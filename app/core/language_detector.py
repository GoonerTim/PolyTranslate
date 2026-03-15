"""Language detection module."""

from __future__ import annotations

import logging

from app.config.languages import LANGUAGES, get_language_name

try:
    from langdetect import detect, detect_langs
    from langdetect.lang_detect_exception import LangDetectException

    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    LangDetectException = Exception  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detects the language of text content."""

    SUPPORTED_LANGUAGES = LANGUAGES

    @classmethod
    def detect(cls, text: str) -> str | None:
        if not LANGDETECT_AVAILABLE:
            return None

        if not text or len(text.strip()) < 10:
            return None

        try:
            lang = detect(text)
            if lang == "zh-cn" or lang == "zh-tw":
                return lang
            return lang
        except LangDetectException:
            return None
        except Exception as e:
            logger.debug("Language detection failed: %s", e)
            return None

    @classmethod
    def detect_with_confidence(cls, text: str) -> list[tuple[str, float]]:
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
        return get_language_name(code)

    @classmethod
    def is_available(cls) -> bool:
        return LANGDETECT_AVAILABLE
