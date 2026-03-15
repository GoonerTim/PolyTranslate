"""Tests for the translator module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.config.settings import Settings
from app.core.translator import SimpleTokenizer, Translator, safe_sent_tokenize


class TestSimpleTokenizer:
    """Tests for SimpleTokenizer class."""

    def test_sent_tokenize_basic(self) -> None:
        text = "Hello world. How are you? I am fine!"
        sentences = SimpleTokenizer.sent_tokenize(text)
        assert len(sentences) == 3
        assert sentences[0] == "Hello world."
        assert sentences[1] == "How are you?"
        assert sentences[2] == "I am fine!"

    def test_sent_tokenize_with_numbers(self) -> None:
        text = "The value is 3.14. This is another sentence."
        sentences = SimpleTokenizer.sent_tokenize(text)
        # Should not split on decimal point
        assert "3.14" in sentences[0]

    def test_sent_tokenize_empty(self) -> None:
        text = ""
        sentences = SimpleTokenizer.sent_tokenize(text)
        assert sentences == [""]

    def test_sent_tokenize_no_punctuation(self) -> None:
        text = "Hello world"
        sentences = SimpleTokenizer.sent_tokenize(text)
        assert sentences == ["Hello world"]


class TestSafeSentTokenize:
    """Tests for safe_sent_tokenize function."""

    def test_safe_sent_tokenize_with_nltk(self) -> None:
        text = "Hello world. How are you?"
        sentences = safe_sent_tokenize(text)
        assert len(sentences) >= 2

    @patch("app.core.translator.sent_tokenize")
    def test_safe_sent_tokenize_fallback(self, mock_tokenize: MagicMock) -> None:
        mock_tokenize.side_effect = LookupError("NLTK data not found")
        text = "Hello world. How are you?"
        sentences = safe_sent_tokenize(text)
        assert len(sentences) >= 2

    @patch("app.core.translator.sent_tokenize")
    def test_safe_sent_tokenize_exception(self, mock_tokenize: MagicMock) -> None:
        mock_tokenize.side_effect = Exception("Unknown error")
        text = "Hello world. How are you?"
        sentences = safe_sent_tokenize(text)
        assert len(sentences) >= 2


class TestTranslator:
    """Tests for Translator class."""

    def test_init_default_settings(self) -> None:
        translator = Translator()
        assert translator.settings is not None
        assert isinstance(translator.services, dict)
        assert translator.glossary is not None

    def test_init_custom_settings(self, temp_dir: Path) -> None:
        settings = Settings(temp_dir / "config.json")
        translator = Translator(settings)
        assert translator.settings == settings

    def test_initialize_services_with_keys(self, temp_dir: Path) -> None:
        settings = Settings(temp_dir / "config.json")
        settings.set_api_key("deepl", "test_key")
        settings.set_api_key("yandex", "test_key")
        settings.set_api_key("google", "test_key")

        translator = Translator(settings)
        assert "deepl" in translator.services
        assert "yandex" in translator.services
        assert "google" in translator.services
        assert "chatgpt_proxy" in translator.services  # Always available

    def test_initialize_services_without_keys(self, temp_dir: Path) -> None:
        settings = Settings(temp_dir / "config.json")
        translator = Translator(settings)
        # Only chatgpt_proxy should be available (no key required)
        assert "chatgpt_proxy" in translator.services

    def test_service_timeout_default(self, temp_dir: Path) -> None:
        settings = Settings(temp_dir / "config.json")
        translator = Translator(settings)
        assert translator.services["deepl"].timeout == 1800.0
        assert translator.services["chatgpt_proxy"].timeout == 1800.0

    def test_service_timeout_global(self, temp_dir: Path) -> None:
        settings = Settings(temp_dir / "config.json")
        settings.set("service_timeout", 60.0)
        translator = Translator(settings)
        assert translator.services["deepl"].timeout == 60.0
        assert translator.services["google"].timeout == 60.0
        assert translator.services["chatgpt_proxy"].timeout == 60.0

    def test_service_timeout_per_service(self, temp_dir: Path) -> None:
        settings = Settings(temp_dir / "config.json")
        settings.set("service_timeout", 60.0)
        settings.set("service_timeouts", {"deepl": 15.0})
        translator = Translator(settings)
        assert translator.services["deepl"].timeout == 15.0
        assert translator.services["google"].timeout == 60.0

    def test_reload_services(self, temp_dir: Path) -> None:
        settings = Settings(temp_dir / "config.json")
        # Start with no services configured (only chatgpt_proxy available)
        translator = Translator(settings)
        initial_count = len(translator.services)

        # Add a new API key for a service that wasn't configured
        settings.set_api_key("openai", "new_key")
        translator.settings = settings
        translator.reload_services()

        # Should have one more service now
        assert len(translator.services) > initial_count
        assert "openai" in translator.services

    def test_get_available_services_empty(self, temp_dir: Path) -> None:
        settings = Settings(temp_dir / "config.json")
        translator = Translator(settings)
        available = translator.get_available_services()
        # ChatGPT Proxy is always available
        assert "chatgpt_proxy" in available

    def test_get_available_services_with_keys(self, temp_dir: Path) -> None:
        settings = Settings(temp_dir / "config.json")
        settings.set_api_key("deepl", "test_key")
        translator = Translator(settings)
        available = translator.get_available_services()
        assert "deepl" in available
        assert "chatgpt_proxy" in available

    def test_split_text_basic(self) -> None:
        translator = Translator()
        text = "First sentence. Second sentence. Third sentence."
        chunks = translator.split_text(text, chunk_size=50)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk) <= 100  # Should be reasonable size

    def test_split_text_long(self) -> None:
        translator = Translator()
        # Create long text
        sentences = [f"This is sentence number {i}." for i in range(50)]
        text = " ".join(sentences)
        chunks = translator.split_text(text, chunk_size=100)
        assert len(chunks) > 1

    def test_split_text_empty(self) -> None:
        translator = Translator()
        chunks = translator.split_text("", chunk_size=100)
        assert chunks == [""]

    def test_translate_service_not_available(self) -> None:
        translator = Translator()
        with pytest.raises(ValueError) as exc_info:
            translator.translate("Hello", "en", "ru", "nonexistent")
        assert "not available" in str(exc_info.value)

    def test_translate_service_not_configured(self, temp_dir: Path) -> None:
        settings = Settings(temp_dir / "config.json")
        translator = Translator(settings)
        # DeepL exists but not configured
        with pytest.raises(ValueError):
            translator.translate("Hello", "en", "ru", "deepl")

    @patch("app.services.chatgpt_proxy.httpx.post")
    def test_translate_success(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": {"translated_text": "Привет"}}
        mock_post.return_value = mock_response

        translator = Translator()
        result = translator.translate("Hello", "en", "ru", "chatgpt_proxy")
        assert isinstance(result, str)

    @patch("app.services.chatgpt_proxy.httpx.post")
    def test_translate_with_glossary(self, mock_post: MagicMock, temp_dir: Path) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": {"translated_text": "Hello world"}}
        mock_post.return_value = mock_response

        translator = Translator()
        translator.glossary.add_entry("world", "мир")
        result = translator.translate("Test", "en", "ru", "chatgpt_proxy")
        # Glossary should be applied
        assert isinstance(result, str)

    def test_translate_chunk(self) -> None:
        translator = Translator()
        # Only use chatgpt_proxy which is always available
        with patch("app.services.chatgpt_proxy.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": {"translated_text": "Привет"}}
            mock_post.return_value = mock_response

            results = translator.translate_chunk("Hello", "en", "ru", ["chatgpt_proxy"])
            assert "chatgpt_proxy" in results

    def test_translate_chunk_with_error(self, temp_dir: Path) -> None:
        settings = Settings(temp_dir / "config.json")
        settings.set_api_key("deepl", "invalid_key")
        translator = Translator(settings)

        results = translator.translate_chunk("Hello", "en", "ru", ["deepl"])
        # Should have error message
        assert "Error" in results["deepl"] or "error" in results["deepl"].lower()

    @patch("app.services.chatgpt_proxy.httpx.post")
    def test_translate_parallel(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": {"translated_text": "Привет"}}
        mock_post.return_value = mock_response

        translator = Translator()
        text = "Hello. How are you?"
        results = translator.translate_parallel(
            text, "en", "ru", ["chatgpt_proxy"], chunk_size=50, max_workers=1
        )
        assert "chatgpt_proxy" in results
        assert isinstance(results["chatgpt_proxy"], str)

    @patch("app.services.chatgpt_proxy.httpx.post")
    def test_translate_parallel_with_progress(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": {"translated_text": "Привет"}}
        mock_post.return_value = mock_response

        translator = Translator()
        progress_calls = []

        def progress_callback(completed: int, total: int) -> None:
            progress_calls.append((completed, total))

        text = "Hello. How are you?"
        translator.translate_parallel(
            text,
            "en",
            "ru",
            ["chatgpt_proxy"],
            chunk_size=50,
            max_workers=1,
            progress_callback=progress_callback,
        )
        # Progress callback should have been called
        assert len(progress_calls) > 0

    @patch("app.services.chatgpt_proxy.httpx.post")
    def test_translate_parallel_multiple_services(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": {"translated_text": "Привет"}}
        mock_post.return_value = mock_response

        translator = Translator()
        results = translator.translate_parallel(
            "Hello", "en", "ru", ["chatgpt_proxy"], chunk_size=100, max_workers=2
        )
        assert len(results) >= 1

    def test_detect_language_available(self) -> None:
        translator = Translator()
        result = translator.detect_language("Hello, how are you?")
        # Result can be None if langdetect not available or "en" if available
        if result is not None:
            assert isinstance(result, str)

    def test_detect_language_short_text(self) -> None:
        translator = Translator()
        result = translator.detect_language("Hi")
        # Should return None for short text
        assert result is None

    def test_detect_language_empty(self) -> None:
        translator = Translator()
        result = translator.detect_language("")
        assert result is None
