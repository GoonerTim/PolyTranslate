"""Yandex Translate service."""

from __future__ import annotations

import requests

from app.services.base import TranslationService


class YandexService(TranslationService):
    """Yandex Cloud Translate API service."""

    API_URL = "https://translate.api.cloud.yandex.net/translate/v2/translate"

    def __init__(self, api_key: str = "") -> None:
        """
        Initialize Yandex service.

        Args:
            api_key: Yandex Cloud API key.
        """
        self.api_key = api_key

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using Yandex API."""
        if not self.is_configured():
            raise ValueError("Yandex API key not set")

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        data: dict[str, str | list[str]] = {
            "texts": [text],
            "targetLanguageCode": target_lang,
        }

        if source_lang.lower() != "auto":
            data["sourceLanguageCode"] = source_lang

        try:
            response = requests.post(self.API_URL, headers=headers, json=data, timeout=30)
        except requests.RequestException as e:
            raise ValueError(f"Yandex API request failed: {e}") from e

        if response.status_code == 200:
            return response.json()["translations"][0]["text"]
        else:
            raise ValueError(f"Yandex API error {response.status_code}: {response.text}")

    def is_configured(self) -> bool:
        """Check if the service is configured."""
        return bool(self.api_key)

    def get_name(self) -> str:
        """Get the service name."""
        return "Yandex Translate"
