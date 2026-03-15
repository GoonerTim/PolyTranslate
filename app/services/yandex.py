from __future__ import annotations

import logging
import uuid

import httpx

from app.services.base import TranslationService
from app.utils.rate_limiter import RateLimiter, retry_with_backoff

logger = logging.getLogger(__name__)


class YandexService(TranslationService):
    API_URL = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    FREE_API_URL = "https://translate.yandex.net/api/v1/tr.json/translate"
    _rate_limiter = RateLimiter(min_interval=0.5)

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key
        self.uuid = str(uuid.uuid4()).replace("-", "")

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if self.api_key:
            try:
                return self._translate_with_api_key(text, source_lang, target_lang)
            except Exception as e:
                logger.warning("Yandex paid API failed, falling back to free: %s", e)
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
            response = httpx.post(self.API_URL, headers=headers, json=data, timeout=30.0)
        except httpx.RequestError as e:
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

        response = retry_with_backoff(
            self._rate_limiter,
            lambda: httpx.post(
                self.FREE_API_URL, params=params, data=data, headers=headers, timeout=30.0
            ),
            "Yandex free API",
        )

        if response.status_code != 200:
            raise ValueError(f"Yandex free API HTTP error {response.status_code}: {response.text}")

        result = response.json()
        if result.get("code") == 200:
            return "\n".join(result.get("text", []))
        raise ValueError(f"Yandex free API error: {result.get('message', 'Unknown error')}")

    def is_configured(self) -> bool:
        return True

    def get_name(self) -> str:
        return "Yandex Translate" + (" (Free)" if not self.api_key else "")
