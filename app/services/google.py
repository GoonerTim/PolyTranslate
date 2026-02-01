"""Google Translate service."""

from __future__ import annotations

import requests

from app.services.base import TranslationService


class GoogleService(TranslationService):
    """Google Cloud Translation API service."""

    API_URL = "https://translation.googleapis.com/language/translate/v2"

    def __init__(self, api_key: str = "") -> None:
        """
        Initialize Google service.

        Args:
            api_key: Google Cloud API key.
        """
        self.api_key = api_key

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using Google API."""
        if not self.is_configured():
            raise ValueError("Google API key not set")

        params: dict[str, str] = {
            "q": text,
            "target": target_lang,
            "format": "text",
            "key": self.api_key,
        }

        if source_lang.lower() != "auto":
            params["source"] = source_lang

        try:
            response = requests.post(self.API_URL, params=params, timeout=30)
        except requests.RequestException as e:
            raise ValueError(f"Google API request failed: {e}") from e

        if response.status_code == 200:
            return response.json()["data"]["translations"][0]["translatedText"]
        else:
            raise ValueError(f"Google API error {response.status_code}: {response.text}")

    def is_configured(self) -> bool:
        """Check if the service is configured."""
        return bool(self.api_key)

    def get_name(self) -> str:
        """Get the service name."""
        return "Google Translate"
