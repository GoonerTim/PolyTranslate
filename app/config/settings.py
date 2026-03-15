"""Settings management for the translator application."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.config.schema import (
    CLAUDE_MODELS,
    GROQ_MODELS,
    OPENAI_MODELS,
    ApiKeysSchema,
    SettingsSchema,
)

logger = logging.getLogger(__name__)


class Settings:
    """Manages application settings stored in a JSON file."""

    OPENAI_MODELS = OPENAI_MODELS
    CLAUDE_MODELS = CLAUDE_MODELS
    GROQ_MODELS = GROQ_MODELS

    DEFAULT_SETTINGS: dict[str, Any] = {
        "api_keys": {
            "deepl": "",
            "yandex": "",
            "google": "",
            "openai": "",
            "openrouter": "",
            "groq": "",
            "anthropic": "",
        },
        "deepl_plan": "free",
        "openai_model": "gpt-4o-mini",
        "openrouter_model": "openai/gpt-4o-mini",
        "groq_model": "llama-3.3-70b-versatile",
        "claude_model": "claude-sonnet-4-6",
        "localai_url": "",
        "localai_model": "default",
        "theme": "dark",
        "chunk_size": 1000,
        "max_workers": 3,
        "source_language": "auto",
        "target_language": "ru",
        "selected_services": ["deepl"],
        "window_geometry": "1200x800",
        "ai_evaluator_service": "",
        "ai_evaluator_model": "",
        "ai_evaluation_auto": False,
        "agents": [],
        "renpy_game_folder": "",
        "renpy_processing_mode": "scenes",
        "cache_enabled": True,
        "cache_max_size": 10000,
    }

    def __init__(self, config_path: str | Path | None = None) -> None:
        if config_path is None:
            self.config_path = Path("config.json")
        else:
            self.config_path = Path(config_path)

        self._schema: SettingsSchema = SettingsSchema()
        self.load()

    def load(self) -> None:
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    loaded = json.load(f)
                merged = self._deep_merge(self.DEFAULT_SETTINGS.copy(), loaded)
                self._schema = SettingsSchema.model_validate(merged)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load settings from %s: %s", self.config_path, e)
                self._schema = SettingsSchema()
            except ValidationError as e:
                logger.warning("Invalid settings in %s: %s", self.config_path, e)
                self._schema = SettingsSchema()
        else:
            self._schema = SettingsSchema()

    def save(self) -> None:
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise ValueError(f"Failed to save settings: {e}") from e

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        if hasattr(self._schema, key):
            value = getattr(self._schema, key)
            if isinstance(value, ApiKeysSchema):
                return value.model_dump()
            return value
        # Check pydantic extra fields
        extras = self._schema.model_extra or {}
        if key in extras:
            return extras[key]
        return default

    # Map Pydantic field types to friendly names for error messages
    _FIELD_TYPES: dict[str, tuple[str, type]] = {
        "theme": ("str", str),
        "deepl_plan": ("str", str),
        "renpy_processing_mode": ("str", str),
        "chunk_size": ("int", int),
        "max_workers": ("int", int),
        "cache_max_size": ("int", int),
        "cache_enabled": ("bool", bool),
        "ai_evaluation_auto": ("bool", bool),
    }

    def validate(self, key: str, value: Any) -> None:
        """Validate a setting value. Raises ValueError if invalid."""
        # Pre-check: type mismatch for known fields — produce backward-compatible messages
        if key in self._FIELD_TYPES:
            type_name, expected_type = self._FIELD_TYPES[key]
            if expected_type is bool:
                if not isinstance(value, bool):
                    raise ValueError(
                        f"Invalid type for '{key}': expected {type_name}, "
                        f"got {type(value).__name__}"
                    )
            elif not isinstance(value, expected_type) or isinstance(value, bool):
                raise ValueError(
                    f"Invalid type for '{key}': expected {type_name}, got {type(value).__name__}"
                )

        # Model validation for known model keys — pre-check for backward compat messages
        model_lists = {
            "openai_model": OPENAI_MODELS,
            "claude_model": CLAUDE_MODELS,
            "groq_model": GROQ_MODELS,
        }
        if key in model_lists:
            if not isinstance(value, str) or not value:
                raise ValueError(f"Model for '{key}' must be a non-empty string")
            if value not in model_lists[key]:
                allowed = ", ".join(model_lists[key])
                raise ValueError(f"Unknown model for '{key}': {value!r}. Available: {allowed}")

        try:
            current = self.to_dict()
            current[key] = value
            SettingsSchema.model_validate(current)
        except ValidationError as e:
            # Extract the original ValueError message from Pydantic
            for error in e.errors():
                if error.get("type") == "value_error":
                    msg = str(error.get("msg", ""))
                    # Pydantic prepends "Value error, " — strip it
                    if msg.startswith("Value error, "):
                        msg = msg[len("Value error, ") :]
                    raise ValueError(msg) from e
            raise ValueError(str(e)) from e

    def set(self, key: str, value: Any) -> None:
        self.validate(key, value)
        current = self.to_dict()
        current[key] = value
        self._schema = SettingsSchema.model_validate(current)

    def get_api_keys(self) -> dict[str, str]:
        return self._schema.api_keys.model_dump()

    def set_api_key(self, service: str, key: str) -> None:
        keys = self._schema.api_keys.model_dump()
        keys[service] = key
        self._schema.api_keys = ApiKeysSchema.model_validate(keys)

    def get_api_key(self, service: str) -> str:
        keys = self._schema.api_keys.model_dump()
        return keys.get(service, "")

    def get_theme(self) -> str:
        return self._schema.theme

    def set_theme(self, theme: str) -> None:
        self.set("theme", theme)

    def get_chunk_size(self) -> int:
        return self._schema.chunk_size

    def set_chunk_size(self, size: int) -> None:
        self.set("chunk_size", size)

    def get_max_workers(self) -> int:
        return self._schema.max_workers

    def set_max_workers(self, workers: int) -> None:
        self.set("max_workers", workers)

    def get_selected_services(self) -> list[str]:
        return self._schema.selected_services

    def set_selected_services(self, services: list[str]) -> None:
        self._schema.selected_services = services

    def get_source_language(self) -> str:
        return self._schema.source_language

    def set_source_language(self, lang: str) -> None:
        self._schema.source_language = lang

    def get_target_language(self) -> str:
        return self._schema.target_language

    def set_target_language(self, lang: str) -> None:
        self._schema.target_language = lang

    def get_window_geometry(self) -> str:
        return self._schema.window_geometry

    def set_window_geometry(self, geometry: str) -> None:
        self._schema.window_geometry = geometry

    def reset_to_defaults(self) -> None:
        self._schema = SettingsSchema()

    def to_dict(self) -> dict[str, Any]:
        data = self._schema.model_dump()
        # Merge extra fields into the top-level dict
        if self._schema.model_extra:
            data.update(self._schema.model_extra)
        return data
