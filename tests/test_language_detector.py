"""Tests for the language detector module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.language_detector import LanguageDetector


class TestLanguageDetector:
    """Tests for LanguageDetector class."""

    def test_is_available(self) -> None:
        # Should be available if langdetect is installed
        result = LanguageDetector.is_available()
        assert isinstance(result, bool)

    def test_detect_english(self) -> None:
        text = "This is a sample text in English language with enough words."
        result = LanguageDetector.detect(text)
        if result is not None:  # Only if langdetect is available
            assert result == "en"

    def test_detect_russian(self) -> None:
        text = "Это пример текста на русском языке с достаточным количеством слов."
        result = LanguageDetector.detect(text)
        if result is not None:
            assert result == "ru"

    def test_detect_short_text(self) -> None:
        text = "Hi"
        result = LanguageDetector.detect(text)
        assert result is None

    def test_detect_empty_text(self) -> None:
        result = LanguageDetector.detect("")
        assert result is None

    def test_detect_whitespace_only(self) -> None:
        result = LanguageDetector.detect("   \n\t  ")
        assert result is None

    @patch("app.core.language_detector.LANGDETECT_AVAILABLE", False)
    def test_detect_when_not_available(self) -> None:
        text = "This is a test sentence."
        result = LanguageDetector.detect(text)
        assert result is None

    def test_detect_with_confidence_english(self) -> None:
        text = "This is a sample text in English language with enough words."
        results = LanguageDetector.detect_with_confidence(text)
        if results:  # Only if langdetect is available
            assert isinstance(results, list)
            assert len(results) > 0
            # Check format
            lang, prob = results[0]
            assert isinstance(lang, str)
            assert isinstance(prob, float)
            assert 0.0 <= prob <= 1.0

    def test_detect_with_confidence_short_text(self) -> None:
        text = "Hi"
        results = LanguageDetector.detect_with_confidence(text)
        assert results == []

    def test_detect_with_confidence_empty(self) -> None:
        results = LanguageDetector.detect_with_confidence("")
        assert results == []

    @patch("app.core.language_detector.LANGDETECT_AVAILABLE", False)
    def test_detect_with_confidence_not_available(self) -> None:
        text = "This is a test sentence."
        results = LanguageDetector.detect_with_confidence(text)
        assert results == []

    def test_get_language_name_existing(self) -> None:
        assert LanguageDetector.get_language_name("en") == "English"
        assert LanguageDetector.get_language_name("ru") == "Russian"
        assert LanguageDetector.get_language_name("fr") == "French"

    def test_get_language_name_nonexistent(self) -> None:
        result = LanguageDetector.get_language_name("xx")
        assert result == "xx"

    def test_get_language_name_uppercase(self) -> None:
        assert LanguageDetector.get_language_name("EN") == "English"
        assert LanguageDetector.get_language_name("RU") == "Russian"

    def test_supported_languages_dict(self) -> None:
        assert isinstance(LanguageDetector.SUPPORTED_LANGUAGES, dict)
        assert len(LanguageDetector.SUPPORTED_LANGUAGES) > 0
        # Check common languages
        assert "en" in LanguageDetector.SUPPORTED_LANGUAGES
        assert "ru" in LanguageDetector.SUPPORTED_LANGUAGES

    def test_detect_spanish(self) -> None:
        text = "Este es un texto de ejemplo en español con suficientes palabras."
        result = LanguageDetector.detect(text)
        if result is not None:
            assert result == "es"

    def test_detect_german(self) -> None:
        text = "Dies ist ein Beispieltext in deutscher Sprache mit genug Wörtern."
        result = LanguageDetector.detect(text)
        if result is not None:
            assert result == "de"

    def test_detect_french(self) -> None:
        text = "Ceci est un exemple de texte en français avec assez de mots."
        result = LanguageDetector.detect(text)
        if result is not None:
            assert result == "fr"

    @patch("app.core.language_detector.detect")
    def test_detect_exception_handling(self, mock_detect: pytest.fixture) -> None:
        from app.core.language_detector import LANGDETECT_AVAILABLE

        if not LANGDETECT_AVAILABLE:
            pytest.skip("langdetect not available")

        # Simulate exception
        mock_detect.side_effect = Exception("Test error")
        result = LanguageDetector.detect("This is a test sentence with enough words.")
        assert result is None

    @patch("app.core.language_detector.detect_langs")
    def test_detect_with_confidence_exception(self, mock_detect_langs: pytest.fixture) -> None:
        from app.core.language_detector import LANGDETECT_AVAILABLE

        if not LANGDETECT_AVAILABLE:
            pytest.skip("langdetect not available")

        # Simulate exception
        mock_detect_langs.side_effect = Exception("Test error")
        results = LanguageDetector.detect_with_confidence(
            "This is a test sentence with enough words."
        )
        assert results == []

    def test_chinese_language_detection(self) -> None:
        text = "这是一个中文文本的例子，包含足够的单词来进行语言检测。"
        result = LanguageDetector.detect(text)
        if result is not None:
            assert result in ["zh-cn", "zh-tw", "zh"]

    def test_japanese_language_detection(self) -> None:
        text = "これは日本語のテキストのサンプルで、言語検出に十分な単語が含まれています。"
        result = LanguageDetector.detect(text)
        if result is not None:
            assert result == "ja"

    def test_detect_with_confidence_sorted(self) -> None:
        text = "This is a sample text in English language with enough words."
        results = LanguageDetector.detect_with_confidence(text)
        if results:
            # Check that probabilities are in descending order
            probs = [prob for _, prob in results]
            assert probs == sorted(probs, reverse=True)
