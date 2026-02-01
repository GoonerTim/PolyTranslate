"""Settings management for the translator application."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Settings:
    """Manages application settings stored in a JSON file."""

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
        "openai_model": "gpt-3.5-turbo",
        "openrouter_model": "openai/gpt-3.5-turbo",
        "groq_model": "mixtral-8x7b-32768",
        "claude_model": "claude-3-sonnet-20240229",
        "localai_url": "",
        "localai_model": "default",
        "theme": "dark",
        "chunk_size": 1000,
        "max_workers": 3,
        "source_language": "auto",
        "target_language": "ru",
        "selected_services": ["deepl"],
        "window_geometry": "1200x800",
    }

    def __init__(self, config_path: str | Path | None = None) -> None:
        """
        Initialize settings.

        Args:
            config_path: Path to the config file. Defaults to config.json in working dir.
        """
        if config_path is None:
            self.config_path = Path("config.json")
        else:
            self.config_path = Path(config_path)

        self._settings: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load settings from the config file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    loaded = json.load(f)
                # Merge with defaults to ensure all keys exist
                self._settings = self._deep_merge(self.DEFAULT_SETTINGS.copy(), loaded)
            except (json.JSONDecodeError, OSError):
                self._settings = self.DEFAULT_SETTINGS.copy()
        else:
            self._settings = self.DEFAULT_SETTINGS.copy()

    def save(self) -> None:
        """Save settings to the config file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise ValueError(f"Failed to save settings: {e}") from e

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.

        Args:
            key: The setting key.
            default: Default value if key doesn't exist.

        Returns:
            The setting value.
        """
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value.

        Args:
            key: The setting key.
            value: The value to set.
        """
        self._settings[key] = value

    def get_api_keys(self) -> dict[str, str]:
        """Get all API keys."""
        return self._settings.get("api_keys", {}).copy()

    def set_api_key(self, service: str, key: str) -> None:
        """
        Set an API key for a service.

        Args:
            service: The service name.
            key: The API key.
        """
        if "api_keys" not in self._settings:
            self._settings["api_keys"] = {}
        self._settings["api_keys"][service] = key

    def get_api_key(self, service: str) -> str:
        """
        Get an API key for a service.

        Args:
            service: The service name.

        Returns:
            The API key or empty string.
        """
        return self._settings.get("api_keys", {}).get(service, "")

    def get_theme(self) -> str:
        """Get the current theme."""
        return self._settings.get("theme", "dark")

    def set_theme(self, theme: str) -> None:
        """Set the theme."""
        if theme not in ("dark", "light"):
            raise ValueError(f"Invalid theme: {theme}")
        self._settings["theme"] = theme

    def get_chunk_size(self) -> int:
        """Get the chunk size for translation."""
        return self._settings.get("chunk_size", 1000)

    def set_chunk_size(self, size: int) -> None:
        """Set the chunk size."""
        if size < 100 or size > 5000:
            raise ValueError("Chunk size must be between 100 and 5000")
        self._settings["chunk_size"] = size

    def get_max_workers(self) -> int:
        """Get the maximum number of parallel workers."""
        return self._settings.get("max_workers", 3)

    def set_max_workers(self, workers: int) -> None:
        """Set the maximum number of workers."""
        if workers < 1 or workers > 10:
            raise ValueError("Workers must be between 1 and 10")
        self._settings["max_workers"] = workers

    def get_selected_services(self) -> list[str]:
        """Get the list of selected translation services."""
        return self._settings.get("selected_services", ["deepl"])

    def set_selected_services(self, services: list[str]) -> None:
        """Set the selected translation services."""
        self._settings["selected_services"] = services

    def get_source_language(self) -> str:
        """Get the source language."""
        return self._settings.get("source_language", "auto")

    def set_source_language(self, lang: str) -> None:
        """Set the source language."""
        self._settings["source_language"] = lang

    def get_target_language(self) -> str:
        """Get the target language."""
        return self._settings.get("target_language", "ru")

    def set_target_language(self, lang: str) -> None:
        """Set the target language."""
        self._settings["target_language"] = lang

    def get_window_geometry(self) -> str:
        """Get the window geometry."""
        return self._settings.get("window_geometry", "1200x800")

    def set_window_geometry(self, geometry: str) -> None:
        """Set the window geometry."""
        self._settings["window_geometry"] = geometry

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self._settings = self.DEFAULT_SETTINGS.copy()

    def to_dict(self) -> dict[str, Any]:
        """Get all settings as a dictionary."""
        return self._settings.copy()
