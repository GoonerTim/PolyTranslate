"""DeepL translation service."""

from __future__ import annotations

import logging
import re
import time

import requests

from app.config.languages import DEEPL_LANG_MAP
from app.services.base import TranslationService
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class DeepLService(TranslationService):
    """DeepL API translation service."""

    FREE_API_URL = "https://api-free.deepl.com/v2/translate"
    PRO_API_URL = "https://api.deepl.com/v2/translate"
    UNOFFICIAL_API_URL = "https://www2.deepl.com/jsonrpc"

    _rate_limiter = RateLimiter(min_interval=1.0)

    _SENTENCE_PATTERN = re.compile(r'^\s+|(?:\s*\n)+\s*|[.!?"\x27:;\u0964](?:\s+)|\s+$')

    def __init__(self, api_key: str = "", is_free_plan: bool = True) -> None:
        self.api_key = api_key
        self.is_free_plan = is_free_plan

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if self.api_key:
            try:
                return self._translate_with_api_key(text, source_lang, target_lang)
            except Exception as e:
                logger.warning("DeepL paid API failed, falling back to free: %s", e)
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

    def _parse_text(self, text: str) -> list[dict[str, str | int]]:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        segments: list[dict[str, str | int]] = []
        pos = 0
        for match in self._SENTENCE_PATTERN.finditer(text):
            sep = match.group(0)
            is_punct_sep = bool(re.match(r'[.!?"\x27:;\u0964](?:\s+)', sep))
            if pos < match.start():
                end = match.start() + 1 if is_punct_sep else match.start()
                if pos < end:
                    segments.append({"type": 1, "text": text[pos:end]})
                    pos = end
            sep_text = sep[1:] if is_punct_sep else sep
            segments.append({"type": 0, "text": sep_text})
            pos = match.start() + len(sep)
        if pos < len(text):
            segments.append({"type": 1, "text": text[pos:]})
        return segments

    def _translate_free(self, text: str, source_lang: str, target_lang: str) -> str:
        target_lang_deepl = DEEPL_LANG_MAP.get(target_lang.lower())
        if not target_lang_deepl:
            raise ValueError(f"DeepL does not support target language: {target_lang}")

        source_lang_deepl = DEEPL_LANG_MAP.get(source_lang.lower(), "auto")

        segments = self._parse_text(text)
        sentences = [re.sub(r"\s+", " ", str(seg["text"])) for seg in segments if seg["type"] == 1]

        if not sentences:
            return text

        jobs = [{"kind": "default", "raw_en_sentence": sentence} for sentence in sentences]

        i_count = 1
        for sentence in sentences:
            i_count += sentence.count("i")
        timestamp = int(time.time() * 1000)
        timestamp = timestamp + (i_count - timestamp % i_count)

        payload = {
            "jsonrpc": "2.0",
            "method": "LMT_handle_jobs",
            "id": 2,
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
            "Accept": "*/*",
            "Accept-Language": "en-US;q=0.8,en;q=0.6",
            "Accept-Encoding": "gzip,deflate",
            "Accept-Charset": "utf-8",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        max_retries = 3
        base_delay = 2.0

        for attempt in range(max_retries + 1):
            self._rate_limiter.wait()

            try:
                response = requests.post(
                    self.UNOFFICIAL_API_URL, json=payload, headers=headers, timeout=30
                )
            except requests.RequestException as e:
                if attempt == max_retries:
                    raise ValueError(f"DeepL free API request failed: {e}") from e
                logger.warning(
                    "DeepL free API request error, retry %d/%d: %s", attempt + 1, max_retries, e
                )
                time.sleep(base_delay * (2**attempt))
                continue

            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("result") and result["result"].get("translations"):
                        translated_sentences = []
                        for translation in result["result"]["translations"]:
                            if translation.get("beams") and len(translation["beams"]) > 0:
                                translated_text = translation["beams"][0].get(
                                    "postprocessed_sentence", ""
                                )
                                translated_sentences.append(translated_text)
                            else:
                                translated_sentences.append("")

                        output = []
                        trans_iter = iter(translated_sentences)
                        for seg in segments:
                            if seg["type"] == 0:
                                output.append(str(seg["text"]))
                            else:
                                output.append(next(trans_iter, str(seg["text"])))
                        return "".join(output)
                    raise ValueError("Unexpected response format from DeepL free API")
                except (KeyError, IndexError, TypeError) as e:
                    raise ValueError(f"Failed to parse DeepL free API response: {e}") from e

            if response.status_code == 429:
                if attempt < max_retries:
                    delay = base_delay * (2**attempt)
                    logger.warning(
                        "DeepL rate limited (429), retry %d/%d after %.1fs",
                        attempt + 1,
                        max_retries,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                raise ValueError(
                    "DeepL free API rate limit exceeded. Please try again later or use an API key."
                )

            raise ValueError(f"DeepL free API HTTP error {response.status_code}: {response.text}")

        raise ValueError("DeepL free API: Maximum retries exceeded")

    def is_configured(self) -> bool:
        return True

    def get_name(self) -> str:
        return "DeepL" + (" (Free)" if not self.api_key else "")

    def get_supported_languages(self) -> list[str]:
        return list(DEEPL_LANG_MAP.keys())
