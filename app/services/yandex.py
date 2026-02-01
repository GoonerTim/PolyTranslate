from __future__ import annotations

import uuid

import requests

from app.services.base import TranslationService


class YandexService(TranslationService):
    API_URL = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    FREE_API_URL = "https://translate.yandex.net/api/v1/tr.json/translate"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key
        self.uuid = str(uuid.uuid4()).replace("-", "")

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if self.api_key:
            try:
                return self._translate_with_api_key(text, source_lang, target_lang)
            except Exception:
                pass
        return self._translate_free(text, source_lang, target_lang)

    def _translate_with_api_key(self, text: str, source_lang: str, target_lang: str) -> str:
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
        raise ValueError(f"Yandex API error {response.status_code}: {response.text}")

    def _translate_free(self, text: str, source_lang: str, target_lang: str) -> str:
        source_code = source_lang.lower() if source_lang.lower() != "auto" else ""
        target_code = target_lang.lower()
        lang_pair = f"{source_code}-{target_code}" if source_code else target_code

        params = {
            "uuid": self.uuid,
            "srv": "android",
            "lang": lang_pair,
            "reason": "auto",
            "format": "text",
        }
        headers = {
            "User-Agent": "ru.yandex.translate/21.15.4 (Xiaomi Redmi Note 8; Android 11)",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"text": text}

        try:
            response = requests.post(
                self.FREE_API_URL, params=params, data=data, headers=headers, timeout=30
            )
        except requests.RequestException as e:
            raise ValueError(f"Yandex free API request failed: {e}") from e

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                return "\n".join(result.get("text", []))
            raise ValueError(f"Yandex free API error: {result.get('message', 'Unknown error')}")
        raise ValueError(f"Yandex free API HTTP error {response.status_code}: {response.text}")

    def is_configured(self) -> bool:
        return True

    def get_name(self) -> str:
        return "Yandex Translate" + (" (Free)" if not self.api_key else "")
