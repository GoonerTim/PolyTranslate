"""Settings management for the translator application."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Settings:
    """Manages application settings stored in a JSON file."""

    OPENAI_MODELS = [
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
        "gpt-4o",
        "gpt-4o-mini",
        "o3-mini",
        "gpt-4-turbo",
    ]

    CLAUDE_MODELS = [
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
    ]

    GROQ_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
        "mixtral-8x7b-32768",
    ]

    VALIDATORS: dict[str, tuple[type, Any]] = {
        "theme": (str, {"choices": ["dark", "light"]}),
        "chunk_size": (int, {"min": 100, "max": 5000}),
        "max_workers": (int, {"min": 1, "max": 10}),
        "cache_max_size": (int, {"min": 100, "max": 100000}),
        "cache_enabled": (bool, {}),
        "deepl_plan": (str, {"choices": ["free", "pro"]}),
        "renpy_processing_mode": (str, {"choices": ["scenes", "chunks", "full"]}),
        "ai_evaluation_auto": (bool, {}),
    }

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

        self._settings: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    loaded = json.load(f)
                self._settings = self._deep_merge(self.DEFAULT_SETTINGS.copy(), loaded)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load settings from %s: %s", self.config_path, e)
                self._settings = self.DEFAULT_SETTINGS.copy()
        else:
            self._settings = self.DEFAULT_SETTINGS.copy()

    def save(self) -> None:
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
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
        return self._settings.get(key, default)

    def validate(self, key: str, value: Any) -> None:
        """Validate a setting value. Raises ValueError if invalid."""
        if key in self.VALIDATORS:
            expected_type, rules = self.VALIDATORS[key]
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"Invalid type for '{key}': expected {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )
            if "choices" in rules and value not in rules["choices"]:
                raise ValueError(
                    f"Invalid value for '{key}': {value!r}. "
                    f"Must be one of: {', '.join(str(c) for c in rules['choices'])}"
                )
            if "min" in rules and value < rules["min"]:
                raise ValueError(f"Value for '{key}' must be >= {rules['min']}, got {value}")
            if "max" in rules and value > rules["max"]:
                raise ValueError(f"Value for '{key}' must be <= {rules['max']}, got {value}")

        model_lists = {
            "openai_model": self.OPENAI_MODELS,
            "claude_model": self.CLAUDE_MODELS,
            "groq_model": self.GROQ_MODELS,
        }
        if key in model_lists:
            if not isinstance(value, str) or not value:
                raise ValueError(f"Model for '{key}' must be a non-empty string")
            if value not in model_lists[key]:
                allowed = ", ".join(model_lists[key])
                raise ValueError(f"Unknown model for '{key}': {value!r}. Available: {allowed}")

    def set(self, key: str, value: Any) -> None:
        self.validate(key, value)
        self._settings[key] = value

    def get_api_keys(self) -> dict[str, str]:
        return self._settings.get("api_keys", {}).copy()

    def set_api_key(self, service: str, key: str) -> None:
        if "api_keys" not in self._settings:
            self._settings["api_keys"] = {}
        self._settings["api_keys"][service] = key

    def get_api_key(self, service: str) -> str:
        return self._settings.get("api_keys", {}).get(service, "")

    def get_theme(self) -> str:
        return self._settings.get("theme", "dark")

    def set_theme(self, theme: str) -> None:
        self.set("theme", theme)

    def get_chunk_size(self) -> int:
        return self._settings.get("chunk_size", 1000)

    def set_chunk_size(self, size: int) -> None:
        self.set("chunk_size", size)

    def get_max_workers(self) -> int:
        return self._settings.get("max_workers", 3)

    def set_max_workers(self, workers: int) -> None:
        self.set("max_workers", workers)

    def get_selected_services(self) -> list[str]:
        return self._settings.get("selected_services", ["deepl"])

    def set_selected_services(self, services: list[str]) -> None:
        self._settings["selected_services"] = services

    def get_source_language(self) -> str:
        return self._settings.get("source_language", "auto")

    def set_source_language(self, lang: str) -> None:
        self._settings["source_language"] = lang

    def get_target_language(self) -> str:
        return self._settings.get("target_language", "ru")

    def set_target_language(self, lang: str) -> None:
        self._settings["target_language"] = lang

    def get_window_geometry(self) -> str:
        return self._settings.get("window_geometry", "1200x800")

    def set_window_geometry(self, geometry: str) -> None:
        self._settings["window_geometry"] = geometry

    def reset_to_defaults(self) -> None:
        self._settings = self.DEFAULT_SETTINGS.copy()

    def to_dict(self) -> dict[str, Any]:
        return self._settings.copy()
