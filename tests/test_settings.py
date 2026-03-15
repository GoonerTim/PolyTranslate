"""Tests for the settings module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config.settings import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_settings(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        assert settings.get_theme() == "dark"
        assert settings.get_chunk_size() == 1000
        assert settings.get_max_workers() == 3

    def test_load_settings(self, temp_config: Path) -> None:
        settings = Settings(temp_config)

        assert settings.get_api_key("deepl") == "test_deepl_key"
        assert settings.get_api_key("yandex") == "test_yandex_key"
        assert settings.get_theme() == "dark"

    def test_save_settings(self, temp_dir: Path) -> None:
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
        settings = Settings(temp_config)
        keys = settings.get_api_keys()

        assert isinstance(keys, dict)
        assert "deepl" in keys
        assert keys["deepl"] == "test_deepl_key"

    def test_set_api_key(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set_api_key("deepl", "my_key")
        assert settings.get_api_key("deepl") == "my_key"

    def test_theme_validation(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set_theme("light")
        assert settings.get_theme() == "light"

        settings.set_theme("dark")
        assert settings.get_theme() == "dark"

        with pytest.raises(ValueError):
            settings.set_theme("invalid")

    def test_chunk_size_validation(self, temp_dir: Path) -> None:
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
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set_max_workers(5)
        assert settings.get_max_workers() == 5

        with pytest.raises(ValueError):
            settings.set_max_workers(0)

        with pytest.raises(ValueError):
            settings.set_max_workers(20)

    def test_selected_services(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set_selected_services(["deepl", "google"])
        assert settings.get_selected_services() == ["deepl", "google"]

    def test_language_settings(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set_source_language("en")
        assert settings.get_source_language() == "en"

        settings.set_target_language("ru")
        assert settings.get_target_language() == "ru"

    def test_reset_to_defaults(self, temp_config: Path) -> None:
        settings = Settings(temp_config)

        # Modify settings
        settings.set_theme("light")
        settings.set_chunk_size(500)

        # Reset
        settings.reset_to_defaults()

        assert settings.get_theme() == "dark"
        assert settings.get_chunk_size() == 1000

    def test_to_dict(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        data = settings.to_dict()
        assert isinstance(data, dict)
        assert "api_keys" in data
        assert "theme" in data

    def test_deep_merge(self, temp_dir: Path) -> None:
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
        config_path = temp_dir / "config.json"
        # Write invalid JSON
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("{invalid json")

        # Should fall back to defaults
        settings = Settings(config_path)
        assert settings.get_theme() == "dark"
        assert settings.get_chunk_size() == 1000

    def test_save_error_handling(self, temp_dir: Path) -> None:
        # Use path that cannot be written to
        config_path = temp_dir / "nonexistent" / "subdir" / "config.json"
        settings = Settings(config_path)
        settings.set_theme("light")

        with pytest.raises(ValueError, match="Failed to save settings"):
            settings.save()

    def test_set_method(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        settings.set("custom_key", "custom_value")
        assert settings.get("custom_key") == "custom_value"

    def test_set_api_key_without_existing_keys(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        # Create settings without api_keys
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump({"theme": "dark"}, f)

        settings = Settings(config_path)
        settings.set_api_key("deepl", "new_key")
        assert settings.get_api_key("deepl") == "new_key"

    def test_window_geometry(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        # Test default
        assert settings.get_window_geometry() == "1200x800"

        # Test set
        settings.set_window_geometry("1920x1080")
        assert settings.get_window_geometry() == "1920x1080"

    def test_agents_default(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        assert settings.get("agents") == []

    def test_renpy_game_folder_default(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        assert settings.get("renpy_game_folder") == ""

    def test_renpy_processing_mode_default(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        assert settings.get("renpy_processing_mode") == "scenes"

    def test_agents_save_and_load(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        agents = [
            {
                "name": "Mistral 7B",
                "base_url": "http://localhost:1234/v1",
                "model": "mistral-7b",
                "api_key": "not-needed",
                "agent_type": "localai",
                "weight": 1.5,
            }
        ]
        settings.set("agents", agents)
        settings.save()

        settings2 = Settings(config_path)
        loaded_agents = settings2.get("agents")
        assert len(loaded_agents) == 1
        assert loaded_agents[0]["name"] == "Mistral 7B"
        assert loaded_agents[0]["weight"] == 1.5

    def test_default_models_updated(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)

        assert settings.get("openai_model") == "gpt-4o-mini"
        assert settings.get("claude_model") == "claude-sonnet-4-6"
        assert settings.get("groq_model") == "llama-3.3-70b-versatile"
        assert settings.get("openrouter_model") == "openai/gpt-4o-mini"


class TestSettingsValidation:
    """Tests for settings validation."""

    def test_validate_theme_valid(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("theme", "light")
        assert settings.get("theme") == "light"

    def test_validate_theme_invalid(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="Invalid value for 'theme'"):
            settings.set("theme", "blue")

    def test_validate_theme_wrong_type(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="Invalid type for 'theme'"):
            settings.set("theme", 123)

    def test_validate_chunk_size_range(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="must be >= 100"):
            settings.set("chunk_size", 50)
        with pytest.raises(ValueError, match="must be <= 5000"):
            settings.set("chunk_size", 10000)

    def test_validate_max_workers_range(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="must be >= 1"):
            settings.set("max_workers", 0)
        with pytest.raises(ValueError, match="must be <= 10"):
            settings.set("max_workers", 20)

    def test_validate_cache_max_size(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("cache_max_size", 5000)
        assert settings.get("cache_max_size") == 5000
        with pytest.raises(ValueError):
            settings.set("cache_max_size", 50)

    def test_validate_cache_enabled(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("cache_enabled", False)
        assert settings.get("cache_enabled") is False
        with pytest.raises(ValueError, match="Invalid type"):
            settings.set("cache_enabled", "yes")

    def test_validate_deepl_plan(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("deepl_plan", "pro")
        assert settings.get("deepl_plan") == "pro"
        with pytest.raises(ValueError, match="Invalid value"):
            settings.set("deepl_plan", "enterprise")

    def test_validate_renpy_processing_mode(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("renpy_processing_mode", "chunks")
        assert settings.get("renpy_processing_mode") == "chunks"
        with pytest.raises(ValueError, match="Invalid value"):
            settings.set("renpy_processing_mode", "invalid")

    def test_validate_openai_model_valid(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("openai_model", "gpt-4o")
        assert settings.get("openai_model") == "gpt-4o"

    def test_validate_openai_model_invalid(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="Unknown model"):
            settings.set("openai_model", "gpt-2")

    def test_validate_claude_model_valid(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("claude_model", "claude-sonnet-4-6")
        assert settings.get("claude_model") == "claude-sonnet-4-6"

    def test_validate_claude_model_invalid(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="Unknown model"):
            settings.set("claude_model", "claude-2.0")

    def test_validate_groq_model_valid(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("groq_model", "llama-3.3-70b-versatile")
        assert settings.get("groq_model") == "llama-3.3-70b-versatile"

    def test_validate_groq_model_invalid(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="Unknown model"):
            settings.set("groq_model", "llama2-70b-4096")

    def test_validate_model_empty_string(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="non-empty string"):
            settings.set("openai_model", "")

    def test_validate_model_wrong_type(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="non-empty string"):
            settings.set("claude_model", 123)

    def test_unknown_key_no_validation(self, temp_dir: Path) -> None:
        """Unknown keys pass through without validation."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("custom_key", "any_value")
        assert settings.get("custom_key") == "any_value"

    def test_openrouter_model_no_validation(self, temp_dir: Path) -> None:
        """OpenRouter model is free-form (any provider/model combo)."""
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("openrouter_model", "anthropic/claude-3-opus")
        assert settings.get("openrouter_model") == "anthropic/claude-3-opus"

    def test_service_timeout_default(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        assert settings.get("service_timeout") == 1800.0

    def test_service_timeout_set_valid(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("service_timeout", 60.0)
        assert settings.get("service_timeout") == 60.0

    def test_service_timeout_set_int(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("service_timeout", 45)
        assert settings.get("service_timeout") == 45.0

    def test_service_timeout_too_low(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="must be >= 5"):
            settings.set("service_timeout", 2.0)

    def test_service_timeout_too_high(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="must be <= 3600"):
            settings.set("service_timeout", 5000.0)

    def test_service_timeout_wrong_type(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="expected float"):
            settings.set("service_timeout", "fast")

    def test_service_timeouts_default(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        assert settings.get("service_timeouts") == {}

    def test_service_timeouts_set_valid(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("service_timeouts", {"deepl": 10.0, "openai": 3600})
        result = settings.get("service_timeouts")
        assert result["deepl"] == 10.0
        assert result["openai"] == 3600.0

    def test_service_timeouts_invalid_value_too_low(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="Timeout for service"):
            settings.set("service_timeouts", {"deepl": 1.0})

    def test_service_timeouts_invalid_value_too_high(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        with pytest.raises(ValueError, match="Timeout for service"):
            settings.set("service_timeouts", {"openai": 7200.0})

    def test_service_timeouts_persist(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        settings = Settings(config_path)
        settings.set("service_timeout", 60.0)
        settings.set("service_timeouts", {"deepl": 15.0})
        settings.save()

        settings2 = Settings(config_path)
        assert settings2.get("service_timeout") == 60.0
        assert settings2.get("service_timeouts") == {"deepl": 15.0}

    def test_model_lists_on_settings_class(self) -> None:
        """Model lists are accessible as class attributes."""
        assert "gpt-4o" in Settings.OPENAI_MODELS
        assert "claude-sonnet-4-6" in Settings.CLAUDE_MODELS
        assert "llama-3.3-70b-versatile" in Settings.GROQ_MODELS
