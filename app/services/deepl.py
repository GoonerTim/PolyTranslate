"""DeepL translation service."""

from __future__ import annotations

import requests

from app.config.languages import DEEPL_LANG_MAP
from app.services.base import TranslationService


class DeepLService(TranslationService):
    """DeepL API translation service."""

    FREE_API_URL = "https://api-free.deepl.com/v2/translate"
    PRO_API_URL = "https://api.deepl.com/v2/translate"

    def __init__(self, api_key: str = "", is_free_plan: bool = True) -> None:
        """
        Initialize DeepL service.

        Args:
            api_key: DeepL API key.
            is_free_plan: Whether using the free plan.
        """
        self.api_key = api_key
        self.is_free_plan = is_free_plan

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using DeepL API."""
        if not self.is_configured():
            raise ValueError("DeepL API key not set")

        target_lang_deepl = DEEPL_LANG_MAP.get(target_lang.lower())
        if not target_lang_deepl:
            raise ValueError(f"DeepL does not support target language: {target_lang}")

        source_lang_deepl = DEEPL_LANG_MAP.get(source_lang.lower(), "")

        url = self.FREE_API_URL if self.is_free_plan else self.PRO_API_URL

        params: dict[str, str] = {
            "auth_key": self.api_key,
            "text": text,
            "target_lang": target_lang_deepl,
            "preserve_formatting": "1",
        }

        if source_lang_deepl and source_lang.lower() != "auto":
            params["source_lang"] = source_lang_deepl

        try:
            response = requests.post(url, data=params, timeout=30)
        except requests.RequestException as e:
            raise ValueError(f"DeepL API request failed: {e}") from e

        if response.status_code == 200:
            result = response.json()
            return result["translations"][0]["text"]
        elif response.status_code == 456:
            raise ValueError("DeepL: Quota exceeded for free account")
        elif response.status_code == 403:
            raise ValueError("DeepL: Invalid API key")
        else:
            raise ValueError(f"DeepL API error {response.status_code}: {response.text}")

    def is_configured(self) -> bool:
        """Check if the service is configured."""
        return bool(self.api_key)

    def get_name(self) -> str:
        """Get the service name."""
        return "DeepL"

    def get_supported_languages(self) -> list[str]:
        """Get supported languages."""
        return list(DEEPL_LANG_MAP.keys())
