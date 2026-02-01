"""Language definitions and mappings."""

from __future__ import annotations

# Main language dictionary with display names
LANGUAGES: dict[str, str] = {
    "auto": "Auto-detect",
    "en": "English",
    "ru": "Russian",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "nl": "Dutch",
    "pl": "Polish",
    "pt": "Portuguese",
    "zh": "Chinese",
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

# DeepL language codes mapping
DEEPL_LANG_MAP: dict[str, str] = {
    "en": "EN",
    "ru": "RU",
    "de": "DE",
    "fr": "FR",
    "es": "ES",
    "it": "IT",
    "nl": "NL",
    "pl": "PL",
    "pt": "PT",
    "zh": "ZH",
    "ja": "JA",
    "ko": "KO",
    "bg": "BG",
    "cs": "CS",
    "da": "DA",
    "el": "EL",
    "et": "ET",
    "fi": "FI",
    "hu": "HU",
    "id": "ID",
    "lt": "LT",
    "lv": "LV",
    "no": "NB",
    "ro": "RO",
    "sk": "SK",
    "sl": "SL",
    "sv": "SV",
    "tr": "TR",
    "uk": "UK",
}

# ChatGPT Proxy language codes
CHATGPT_PROXY_LANG_MAP: dict[str, str] = {
    "af": "af",
    "az": "az",
    "sq": "sq",
    "ar": "ar",
    "hy": "hy",
    "eu": "eu",
    "be": "be",
    "bg": "bg",
    "ca": "ca",
    "zh": "zh-CN",
    "zh-CN": "zh-CN",
    "zh-TW": "zh-TW",
    "hr": "hr",
    "cs": "cs",
    "da": "da",
    "nl": "nl",
    "en": "en",
    "et": "et",
    "fi": "fi",
    "tl": "tl",
    "fr": "fr",
    "gl": "gl",
    "de": "de",
    "el": "el",
    "ht": "ht",
    "iw": "iw",
    "he": "he",
    "hi": "hi",
    "hu": "hu",
    "is": "is",
    "id": "id",
    "it": "it",
    "ga": "ga",
    "ja": "ja",
    "ka": "ka",
    "ko": "ko",
    "lv": "lv",
    "lt": "lt",
    "mk": "mk",
    "ms": "ms",
    "mt": "mt",
    "no": "no",
    "fa": "fa",
    "pl": "pl",
    "pt": "pt",
    "ro": "ro",
    "ru": "ru",
    "sr": "sr",
    "sk": "sk",
    "sl": "sl",
    "es": "es",
    "sw": "sw",
    "sv": "sv",
    "th": "th",
    "tr": "tr",
    "uk": "uk",
    "ur": "ur",
    "vi": "vi",
    "cy": "cy",
    "yi": "yi",
    "eo": "eo",
    "hmn": "hmn",
    "la": "la",
    "lo": "lo",
    "kk": "kk",
    "uz": "uz",
    "si": "si",
    "tg": "tg",
    "te": "te",
    "km": "km",
    "mn": "mn",
    "kn": "kn",
    "ta": "ta",
    "mr": "mr",
    "bn": "bn",
    "tt": "tt",
}

# Human-readable language names for prompts
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "ru": "Russian",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "nl": "Dutch",
    "pl": "Polish",
    "pt": "Portuguese",
    "zh": "Chinese",
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


def get_language_name(code: str) -> str:
    """
    Get the human-readable name for a language code.

    Args:
        code: ISO 639-1 language code.

    Returns:
        The language name or the code if not found.
    """
    return LANGUAGE_NAMES.get(code.lower(), code)


def get_deepl_code(code: str) -> str | None:
    """
    Get the DeepL language code for a standard code.

    Args:
        code: ISO 639-1 language code.

    Returns:
        DeepL language code or None if not supported.
    """
    return DEEPL_LANG_MAP.get(code.lower())


def get_chatgpt_proxy_code(code: str) -> str | None:
    """
    Get the ChatGPT Proxy language code.

    Args:
        code: ISO 639-1 language code.

    Returns:
        ChatGPT Proxy language code or None if not supported.
    """
    return CHATGPT_PROXY_LANG_MAP.get(code.lower())


def get_source_languages() -> dict[str, str]:
    """Get languages available as source (including auto-detect)."""
    return LANGUAGES.copy()


def get_target_languages() -> dict[str, str]:
    """Get languages available as target (excluding auto-detect)."""
    return {k: v for k, v in LANGUAGES.items() if k != "auto"}
