"""Language detection module."""

from __future__ import annotations

import logging
from collections import OrderedDict

from app.config.languages import LANGUAGES, get_language_name

try:
    from langdetect import detect, detect_langs
    from langdetect.lang_detect_exception import LangDetectException

    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    LangDetectException = Exception  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)

_CACHE_MAX_SIZE = 256
_CACHE_KEY_PREFIX_LEN = 200


class LanguageDetector:
    """Detects the language of text content."""

    SUPPORTED_LANGUAGES = LANGUAGES

    _cache: OrderedDict[str, str | None] = OrderedDict()

    @classmethod
    def detect(cls, text: str) -> str | None:
        if not LANGDETECT_AVAILABLE:
            return None

        if not text or len(text.strip()) < 10:
            return None

        cache_key = text.strip()[:_CACHE_KEY_PREFIX_LEN]
        if cache_key in cls._cache:
            cls._cache.move_to_end(cache_key)
            return cls._cache[cache_key]

        try:
            lang = detect(text)
            if lang == "zh-cn" or lang == "zh-tw":
                result: str | None = lang
            else:
                result = lang
        except LangDetectException:
            result = None
        except Exception as e:
            logger.debug("Language detection failed: %s", e)
            result = None

        cls._cache[cache_key] = result
        if len(cls._cache) > _CACHE_MAX_SIZE:
            cls._cache.popitem(last=False)

        return result

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

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()
