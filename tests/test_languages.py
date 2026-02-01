"""Tests for the languages configuration module."""

from __future__ import annotations

from app.config.languages import (
    CHATGPT_PROXY_LANG_MAP,
    DEEPL_LANG_MAP,
    LANGUAGE_NAMES,
    LANGUAGES,
    get_chatgpt_proxy_code,
    get_deepl_code,
    get_language_name,
    get_source_languages,
    get_target_languages,
)


class TestLanguages:
    """Tests for language configuration."""

    def test_languages_dict_structure(self) -> None:
        """Test that LANGUAGES dict has correct structure."""
        assert isinstance(LANGUAGES, dict)
        assert len(LANGUAGES) > 0
        # Check some common languages exist
        assert "en" in LANGUAGES
        assert "ru" in LANGUAGES
        assert "es" in LANGUAGES
        assert "auto" in LANGUAGES

    def test_language_values(self) -> None:
        """Test that language values are strings."""
        for code, name in LANGUAGES.items():
            assert isinstance(code, str)
            assert isinstance(name, str)
            assert len(name) > 0

    def test_get_language_name_existing(self) -> None:
        """Test getting name for existing language."""
        assert get_language_name("en") == "English"
        assert get_language_name("ru") == "Russian"
        assert get_language_name("fr") == "French"

    def test_get_language_name_nonexistent(self) -> None:
        """Test getting name for non-existent language."""
        result = get_language_name("xx")
        assert result == "xx"  # Should return code itself

    def test_get_language_name_uppercase(self) -> None:
        """Test getting name with uppercase code."""
        assert get_language_name("EN") == "English"
        assert get_language_name("RU") == "Russian"

    def test_get_source_languages(self) -> None:
        """Test getting source languages (including auto)."""
        source_langs = get_source_languages()
        assert isinstance(source_langs, dict)
        assert "auto" in source_langs
        assert "en" in source_langs
        # Should be a copy, not the same object
        assert source_langs is not LANGUAGES

    def test_get_target_languages(self) -> None:
        """Test getting target languages (excluding auto)."""
        target_langs = get_target_languages()
        assert isinstance(target_langs, dict)
        assert "auto" not in target_langs
        assert "en" in target_langs
        assert len(target_langs) == len(LANGUAGES) - 1

    def test_get_deepl_code_existing(self) -> None:
        """Test getting DeepL code for existing language."""
        assert get_deepl_code("en") == "EN"
        assert get_deepl_code("ru") == "RU"
        assert get_deepl_code("de") == "DE"

    def test_get_deepl_code_nonexistent(self) -> None:
        """Test getting DeepL code for non-existent language."""
        assert get_deepl_code("xx") is None

    def test_get_deepl_code_uppercase(self) -> None:
        """Test getting DeepL code with uppercase input."""
        assert get_deepl_code("EN") == "EN"
        assert get_deepl_code("RU") == "RU"

    def test_get_chatgpt_proxy_code_existing(self) -> None:
        """Test getting ChatGPT Proxy code for existing language."""
        assert get_chatgpt_proxy_code("en") == "en"
        assert get_chatgpt_proxy_code("ru") == "ru"
        assert get_chatgpt_proxy_code("zh") == "zh-CN"

    def test_get_chatgpt_proxy_code_nonexistent(self) -> None:
        """Test getting ChatGPT Proxy code for non-existent language."""
        assert get_chatgpt_proxy_code("xx") is None

    def test_chatgpt_proxy_chinese_code(self) -> None:
        """Test ChatGPT Proxy Chinese language code."""
        # Base Chinese code maps to simplified
        assert get_chatgpt_proxy_code("zh") == "zh-CN"
        # CHATGPT_PROXY_LANG_MAP has uppercase keys, but function uses .lower()
        # So we verify the mapping exists in the dict
        assert "zh-CN" in CHATGPT_PROXY_LANG_MAP
        assert "zh-TW" in CHATGPT_PROXY_LANG_MAP

    def test_deepl_lang_map_structure(self) -> None:
        """Test DEEPL_LANG_MAP structure."""
        assert isinstance(DEEPL_LANG_MAP, dict)
        assert len(DEEPL_LANG_MAP) > 0
        # All values should be uppercase
        for _code, deepl_code in DEEPL_LANG_MAP.items():
            assert deepl_code.isupper()

    def test_chatgpt_proxy_lang_map_structure(self) -> None:
        """Test CHATGPT_PROXY_LANG_MAP structure."""
        assert isinstance(CHATGPT_PROXY_LANG_MAP, dict)
        assert len(CHATGPT_PROXY_LANG_MAP) > 0

    def test_language_names_structure(self) -> None:
        """Test LANGUAGE_NAMES structure."""
        assert isinstance(LANGUAGE_NAMES, dict)
        assert len(LANGUAGE_NAMES) > 0
        assert "en" in LANGUAGE_NAMES
        assert "ru" in LANGUAGE_NAMES

    def test_common_languages_present(self) -> None:
        """Test that common languages are present."""
        common_languages = ["en", "ru", "es", "fr", "de", "it", "pt", "ja", "zh", "ko"]
        for lang_code in common_languages:
            assert lang_code in LANGUAGES, f"Common language {lang_code} missing"
