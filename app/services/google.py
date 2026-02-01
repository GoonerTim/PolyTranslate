from __future__ import annotations

import requests

from app.services.base import TranslationService


class GoogleService(TranslationService):
    API_URL = "https://translation.googleapis.com/language/translate/v2"
    FREE_API_URL = "https://translate.googleapis.com/translate_a/single"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if self.api_key:
            try:
                return self._translate_with_api_key(text, source_lang, target_lang)
            except Exception:
                pass
        return self._translate_free(text, source_lang, target_lang)

    def _translate_with_api_key(self, text: str, source_lang: str, target_lang: str) -> str:
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
        raise ValueError(f"Google API error {response.status_code}: {response.text}")

    def _translate_free(self, text: str, source_lang: str, target_lang: str) -> str:
        params = {
            "client": "gtx",
            "sl": source_lang if source_lang.lower() != "auto" else "auto",
            "tl": target_lang,
            "dt": "t",
            "q": text,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        try:
            response = requests.get(self.FREE_API_URL, params=params, headers=headers, timeout=30)
        except requests.RequestException as e:
            raise ValueError(f"Google free API request failed: {e}") from e

        if response.status_code == 200:
            try:
                result = response.json()
                if result and isinstance(result[0], list):
                    translations = [part[0] for part in result[0] if part and part[0]]
                    return "".join(translations)
                raise ValueError("Unexpected response format from Google free API")
            except (KeyError, IndexError, TypeError) as e:
                raise ValueError(f"Failed to parse Google free API response: {e}") from e
        raise ValueError(f"Google free API HTTP error {response.status_code}: {response.text}")

    def is_configured(self) -> bool:
        return True

    def get_name(self) -> str:
        return "Google Translate" + (" (Free)" if not self.api_key else "")
