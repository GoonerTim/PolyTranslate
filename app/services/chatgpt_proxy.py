"""ChatGPT Proxy translation service (no API key required)."""

from __future__ import annotations

import uuid

import requests

from app.config.languages import CHATGPT_PROXY_LANG_MAP
from app.services.base import TranslationService


class ChatGPTProxyService(TranslationService):
    """ChatGPT Proxy translation service that doesn't require an API key."""

    API_URL = "https://mtdev.bytequests.com/v1/translation/chat-gpt"

    def __init__(self) -> None:
        pass

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        source_code = CHATGPT_PROXY_LANG_MAP.get(source_lang.lower(), -1)
        target_code = CHATGPT_PROXY_LANG_MAP.get(target_lang.lower())

        if not target_code:
            raise ValueError(f"ChatGPT Proxy does not support target language: {target_lang}")

        data = {
            "text": text,
            "source_language_code": source_code if source_lang.lower() != "auto" else -1,
            "target_language_code": target_code,
            "share_id": str(uuid.uuid4()),
        }

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "content-type": "application/json",
            "sec-ch-ua": '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "Referer": "https://www.machinetranslation.com/",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

        try:
            response = requests.post(self.API_URL, json=data, headers=headers, timeout=30)
        except requests.RequestException as e:
            raise ValueError(f"ChatGPT Proxy request failed: {e}") from e

        if response.status_code == 200:
            result = response.json()
            if "response" in result and "translated_text" in result["response"]:
                return result["response"]["translated_text"]
            raise ValueError(f"Unexpected response structure: {result}")
        else:
            raise ValueError(f"ChatGPT Proxy error {response.status_code}: {response.text}")

    def is_configured(self) -> bool:
        return True

    def get_name(self) -> str:
        return "ChatGPT Proxy"

    def get_supported_languages(self) -> list[str]:
        return list(CHATGPT_PROXY_LANG_MAP.keys())
