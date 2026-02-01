"""Tests for the settings module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config.settings import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_settings(self, temp_dir: Path) -> None:
        """Test default settings initialization."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        assert settings.get_theme() == "dark"
        assert settings.get_chunk_size() == 1000
        assert settings.get_max_workers() == 3

    def test_load_settings(self, temp_config: Path) -> None:
        """Test loading settings from file."""
        settings = Settings(temp_config)

        assert settings.get_api_key("deepl") == "test_deepl_key"
        assert settings.get_api_key("yandex") == "test_yandex_key"
        assert settings.get_theme() == "dark"

    def test_save_settings(self, temp_dir: Path) -> None:
        """Test saving settings to file."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set_api_key("deepl", "new_key")
        settings.set_theme("light")
        settings.save()

        # Load again and verify
        settings2 = Settings(config_path)
        assert settings2.get_api_key("deepl") == "new_key"
        assert settings2.get_theme() == "light"

    def test_get_api_keys(self, temp_config: Path) -> None:
        """Test getting all API keys."""
        settings = Settings(temp_config)
        keys = settings.get_api_keys()

        assert isinstance(keys, dict)
        assert "deepl" in keys
        assert keys["deepl"] == "test_deepl_key"

    def test_set_api_key(self, temp_dir: Path) -> None:
        """Test setting an API key."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set_api_key("deepl", "my_key")
        assert settings.get_api_key("deepl") == "my_key"

    def test_theme_validation(self, temp_dir: Path) -> None:
        """Test theme validation."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set_theme("light")
        assert settings.get_theme() == "light"

        settings.set_theme("dark")
        assert settings.get_theme() == "dark"

        with pytest.raises(ValueError):
            settings.set_theme("invalid")

    def test_chunk_size_validation(self, temp_dir: Path) -> None:
        """Test chunk size validation."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set_chunk_size(500)
        assert settings.get_chunk_size() == 500

        settings.set_chunk_size(2000)
        assert settings.get_chunk_size() == 2000

        with pytest.raises(ValueError):
            settings.set_chunk_size(50)  # Too small

        with pytest.raises(ValueError):
            settings.set_chunk_size(10000)  # Too large

    def test_max_workers_validation(self, temp_dir: Path) -> None:
        """Test max workers validation."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set_max_workers(5)
        assert settings.get_max_workers() == 5

        with pytest.raises(ValueError):
            settings.set_max_workers(0)

        with pytest.raises(ValueError):
            settings.set_max_workers(20)

    def test_selected_services(self, temp_dir: Path) -> None:
        """Test selected services management."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set_selected_services(["deepl", "google"])
        assert settings.get_selected_services() == ["deepl", "google"]

    def test_language_settings(self, temp_dir: Path) -> None:
        """Test language settings."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set_source_language("en")
        assert settings.get_source_language() == "en"

        settings.set_target_language("ru")
        assert settings.get_target_language() == "ru"

    def test_reset_to_defaults(self, temp_config: Path) -> None:
        """Test resetting to defaults."""
        settings = Settings(temp_config)

        # Modify settings
        settings.set_theme("light")
        settings.set_chunk_size(500)

        # Reset
        settings.reset_to_defaults()

        assert settings.get_theme() == "dark"
        assert settings.get_chunk_size() == 1000

    def test_to_dict(self, temp_dir: Path) -> None:
        """Test converting settings to dictionary."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        data = settings.to_dict()
        assert isinstance(data, dict)
        assert "api_keys" in data
        assert "theme" in data

    def test_deep_merge(self, temp_dir: Path) -> None:
        """Test that new settings are merged with defaults."""
        config_path = temp_dir / "config.json"

        # Create partial config
        partial_config = {"theme": "light"}
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(partial_config, f)

        settings = Settings(config_path)

        # Should have the custom theme
        assert settings.get_theme() == "light"

        # But also have defaults for missing keys
        assert settings.get_chunk_size() == 1000
        assert settings.get_api_keys() is not None

    def test_load_invalid_json(self, temp_dir: Path) -> None:
        """Test loading settings from invalid JSON."""
        config_path = temp_dir / "config.json"
        # Write invalid JSON
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("{invalid json")

        # Should fall back to defaults
        settings = Settings(config_path)
        assert settings.get_theme() == "dark"
        assert settings.get_chunk_size() == 1000

    def test_save_error_handling(self, temp_dir: Path) -> None:
        """Test save error handling with invalid path."""
        # Use path that cannot be written to
        config_path = temp_dir / "nonexistent" / "subdir" / "config.json"
        settings = Settings(config_path)
        settings.set_theme("light")

        with pytest.raises(ValueError, match="Failed to save settings"):
            settings.save()

    def test_set_method(self, temp_dir: Path) -> None:
        """Test generic set method."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set("custom_key", "custom_value")
        assert settings.get("custom_key") == "custom_value"

    def test_set_api_key_without_existing_keys(self, temp_dir: Path) -> None:
        """Test setting API key when api_keys dict doesn't exist."""
        config_path = temp_dir / "config.json"
        # Create settings without api_keys
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump({"theme": "dark"}, f)

        settings = Settings(config_path)
        settings.set_api_key("deepl", "new_key")
        assert settings.get_api_key("deepl") == "new_key"

    def test_window_geometry(self, temp_dir: Path) -> None:
        """Test window geometry settings."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        # Test default
        assert settings.get_window_geometry() == "1200x800"

        # Test set
        settings.set_window_geometry("1920x1080")
        assert settings.get_window_geometry() == "1920x1080"
