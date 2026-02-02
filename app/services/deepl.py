"""DeepL translation service."""

from __future__ import annotations

import re
import threading
import time

import requests

from app.config.languages import DEEPL_LANG_MAP
from app.services.base import TranslationService


class DeepLService(TranslationService):
    """DeepL API translation service."""

    FREE_API_URL = "https://api-free.deepl.com/v2/translate"
    PRO_API_URL = "https://api.deepl.com/v2/translate"
    UNOFFICIAL_API_URL = "https://www2.deepl.com/jsonrpc"

    _last_free_request_time: float = 0
    _free_api_lock = threading.Lock()
    _min_request_interval = 1.0

    def __init__(self, api_key: str = "", is_free_plan: bool = True) -> None:
        self.api_key = api_key
        self.is_free_plan = is_free_plan

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if self.api_key:
            try:
                return self._translate_with_api_key(text, source_lang, target_lang)
            except Exception:
                pass
        return self._translate_free(text, source_lang, target_lang)

    def _translate_with_api_key(self, text: str, source_lang: str, target_lang: str) -> str:
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

    def _translate_free(self, text: str, source_lang: str, target_lang: str) -> str:
        target_lang_deepl = DEEPL_LANG_MAP.get(target_lang.lower())
        if not target_lang_deepl:
            raise ValueError(f"DeepL does not support target language: {target_lang}")

        source_lang_deepl = DEEPL_LANG_MAP.get(source_lang.lower(), "auto")

        sentences = self._split_sentences(text)
        jobs = [{"kind": "default", "raw_en_sentence": sentence} for sentence in sentences]

        timestamp = int(time.time() * 1000)
        i_count = sum(sentence.count("i") for sentence in sentences)
        if i_count > 0:
            timestamp = timestamp + (i_count - timestamp % i_count)

        payload = {
            "jsonrpc": "2.0",
            "method": "LMT_handle_jobs",
            "id": 1,
            "params": {
                "jobs": jobs,
                "lang": {
                    "user_preferred_langs": ["EN", target_lang_deepl],
                    "source_lang_user_selected": source_lang_deepl,
                    "target_lang": target_lang_deepl,
                },
                "priority": 1,
                "timestamp": timestamp,
            },
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        max_retries = 3
        base_delay = 2.0

        for attempt in range(max_retries + 1):
            with self._free_api_lock:
                current_time = time.time()
                time_since_last_request = current_time - DeepLService._last_free_request_time
                if time_since_last_request < self._min_request_interval:
                    time.sleep(self._min_request_interval - time_since_last_request)
                DeepLService._last_free_request_time = time.time()

            try:
                response = requests.post(
                    self.UNOFFICIAL_API_URL, json=payload, headers=headers, timeout=30
                )
            except requests.RequestException as e:
                if attempt == max_retries:
                    raise ValueError(f"DeepL free API request failed: {e}") from e
                time.sleep(base_delay * (2**attempt))
                continue

            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("result") and result["result"].get("translations"):
                        translations = []
                        for translation in result["result"]["translations"]:
                            if translation.get("beams") and len(translation["beams"]) > 0:
                                translated_text = translation["beams"][0].get(
                                    "postprocessed_sentence", ""
                                )
                                translations.append(translated_text)
                        return " ".join(translations)
                    raise ValueError("Unexpected response format from DeepL free API")
                except (KeyError, IndexError, TypeError) as e:
                    raise ValueError(f"Failed to parse DeepL free API response: {e}") from e

            if response.status_code == 429:
                if attempt < max_retries:
                    delay = base_delay * (2**attempt)
                    time.sleep(delay)
                    continue
                raise ValueError(
                    "DeepL free API rate limit exceeded. Please try again later or use an API key."
                )

            raise ValueError(f"DeepL free API HTTP error {response.status_code}: {response.text}")

        raise ValueError("DeepL free API: Maximum retries exceeded")

    def _split_sentences(self, text: str) -> list[str]:
        sentence_pattern = r"[.!?\"':;\u0964]\s+|\n+"
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def is_configured(self) -> bool:
        return True

    def get_name(self) -> str:
        return "DeepL" + (" (Free)" if not self.api_key else "")

    def get_supported_languages(self) -> list[str]:
        return list(DEEPL_LANG_MAP.keys())
