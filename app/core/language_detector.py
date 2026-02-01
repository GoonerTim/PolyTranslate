"""Language detection module."""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from langdetect import detect, detect_langs
    from langdetect.lang_detect_exception import LangDetectException

    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    LangDetectException = Exception  # type: ignore[misc, assignment]

if TYPE_CHECKING:
    pass


class LanguageDetector:
    """Detects the language of text content."""

    # Common language codes
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "ru": "Russian",
        "de": "German",
        "fr": "French",
        "es": "Spanish",
        "it": "Italian",
        "nl": "Dutch",
        "pl": "Polish",
        "pt": "Portuguese",
        "zh-cn": "Chinese (Simplified)",
        "zh-tw": "Chinese (Traditional)",
        "ja": "Japanese",
        "ko": "Korean",
        "ar": "Arabic",
        "tr": "Turkish",
        "uk": "Ukrainian",
        "cs": "Czech",
        "sv": "Swedish",
        "da": "Danish",
        "fi": "Finnish",
        "no": "Norwegian",
        "hu": "Hungarian",
        "el": "Greek",
        "he": "Hebrew",
        "th": "Thai",
        "vi": "Vietnamese",
        "id": "Indonesian",
        "ms": "Malay",
        "ro": "Romanian",
        "bg": "Bulgarian",
        "sk": "Slovak",
        "sl": "Slovenian",
        "hr": "Croatian",
        "sr": "Serbian",
        "lt": "Lithuanian",
        "lv": "Latvian",
        "et": "Estonian",
    }

    @classmethod
    def detect(cls, text: str) -> str | None:
        """
        Detect the language of the given text.

        Args:
            text: The text to analyze.

        Returns:
            The ISO 639-1 language code or None if detection fails.
        """
        if not LANGDETECT_AVAILABLE:
            return None

        if not text or len(text.strip()) < 10:
            return None

        try:
            lang = detect(text)
            # Normalize Chinese language codes
            if lang == "zh-cn" or lang == "zh-tw":
                return lang
            return lang
        except LangDetectException:
            return None
        except Exception:
            return None

    @classmethod
    def detect_with_confidence(cls, text: str) -> list[tuple[str, float]]:
        """
        Detect language with confidence scores.

        Args:
            text: The text to analyze.

        Returns:
            List of (language_code, probability) tuples sorted by probability.
        """
        if not LANGDETECT_AVAILABLE:
            return []

        if not text or len(text.strip()) < 10:
            return []

        try:
            results = detect_langs(text)
            return [(str(r.lang), float(r.prob)) for r in results]
        except LangDetectException:
            return []
        except Exception:
            return []

    @classmethod
    def get_language_name(cls, code: str) -> str:
        """
        Get the human-readable name for a language code.

        Args:
            code: ISO 639-1 language code.

        Returns:
            The language name or the code if not found.
        """
        return cls.SUPPORTED_LANGUAGES.get(code.lower(), code)

    @classmethod
    def is_available(cls) -> bool:
        """Check if language detection is available."""
        return LANGDETECT_AVAILABLE
