"""Main translator orchestration module."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from nltk.tokenize import sent_tokenize

from app.config.settings import Settings
from app.core.language_detector import LanguageDetector
from app.core.plugin_loader import discover_plugins
from app.services import (
    ChatGPTProxyService,
    ClaudeService,
    DeepLService,
    GoogleService,
    GroqService,
    LocalAIService,
    OpenAIService,
    OpenRouterService,
    TranslationService,
    YandexService,
)
from app.services.llm_base import LLMTranslationService
from app.utils.cache import TranslationCache
from app.utils.glossary import Glossary

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class SimpleTokenizer:
    @staticmethod
    def sent_tokenize(text: str) -> list[str]:
        sentences: list[str] = []
        current_sentence = ""

        for char in text:
            current_sentence += char
            if char in ".!?" and len(current_sentence) > 1 and not current_sentence[-2].isdigit():
                sentences.append(current_sentence.strip())
                current_sentence = ""

        if current_sentence.strip():
            sentences.append(current_sentence.strip())

        if not sentences:
            sentences = [text]

        return sentences


def safe_sent_tokenize(text: str) -> list[str]:
    try:
        return sent_tokenize(text)
    except LookupError:
        return SimpleTokenizer.sent_tokenize(text)
    except Exception:
        return SimpleTokenizer.sent_tokenize(text)


class Translator:
    """Main translator class that orchestrates translation services."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.services: dict[str, TranslationService] = {}
        self.glossary = Glossary()
        self.language_detector = LanguageDetector()
        self.cache = TranslationCache(
            enabled=self.settings.get("cache_enabled", True),
            max_size=self.settings.get("cache_max_size", 10000),
        )
        self._initialize_services()
        logger.info("Translator initialized with %d services", len(self.services))

    def _initialize_services(self) -> None:
        api_keys = self.settings.get_api_keys()

        self.services["deepl"] = DeepLService(
            api_key=api_keys.get("deepl", ""),
            is_free_plan=self.settings.get("deepl_plan", "free") == "free",
        )

        self.services["yandex"] = YandexService(api_key=api_keys.get("yandex", ""))

        self.services["google"] = GoogleService(api_key=api_keys.get("google", ""))

        if api_keys.get("openai"):
            self.services["openai"] = OpenAIService(
                api_key=api_keys["openai"],
                model=self.settings.get("openai_model", "gpt-4o-mini"),
            )

        if api_keys.get("openrouter"):
            self.services["openrouter"] = OpenRouterService(
                api_key=api_keys["openrouter"],
                model=self.settings.get("openrouter_model", "openai/gpt-4o-mini"),
            )

        self.services["chatgpt_proxy"] = ChatGPTProxyService()

        if api_keys.get("groq"):
            self.services["groq"] = GroqService(
                api_key=api_keys["groq"],
                model=self.settings.get("groq_model", "llama-3.3-70b-versatile"),
            )

        if api_keys.get("anthropic"):
            self.services["claude"] = ClaudeService(
                api_key=api_keys["anthropic"],
                model=self.settings.get("claude_model", "claude-sonnet-4-6"),
            )

        localai_url = self.settings.get("localai_url")
        if localai_url:
            self.services["localai"] = LocalAIService(
                base_url=localai_url,
                model=self.settings.get("localai_model", "default"),
            )

        # Load plugin services
        for plugin in discover_plugins(self.settings):
            if plugin.service_id in self.services:
                logger.warning(
                    "Plugin '%s' conflicts with built-in service — skipped",
                    plugin.service_id,
                )
                continue
            self.services[plugin.service_id] = plugin.service

    def reload_services(self) -> None:
        self.services.clear()
        self._initialize_services()

    def get_available_services(self) -> list[str]:
        return [name for name, service in self.services.items() if service.is_configured()]

    def split_text(self, text: str, chunk_size: int = 1000) -> list[str]:
        sentences = safe_sent_tokenize(text)
        chunks: list[str] = []
        current_chunk = ""

        for sent in sentences:
            if len(current_chunk + sent) <= chunk_size:
                current_chunk += " " + sent if current_chunk else sent
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sent

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        service_name: str,
        on_token: Callable[[str], None] | None = None,
    ) -> str:
        service = self.services.get(service_name)
        if service is None:
            raise ValueError(f"Service '{service_name}' is not available")

        if not service.is_configured():
            raise ValueError(f"Service '{service_name}' is not configured")

        cached = self.cache.get(text, source_lang, target_lang, service_name)
        if cached is not None:
            logger.debug("Cache hit for %s (%s→%s)", service_name, source_lang, target_lang)
            result = self.glossary.apply(cached)
            if on_token:
                on_token(result)
            return result

        if on_token and isinstance(service, LLMTranslationService) and service.supports_streaming():
            translated = service.translate_stream(text, source_lang, target_lang, on_token)
        else:
            translated = service.translate(text, source_lang, target_lang)
            if on_token:
                on_token(translated)

        self.cache.put(text, source_lang, target_lang, service_name, translated)
        return self.glossary.apply(translated)

    def translate_chunk(
        self,
        chunk: str,
        source_lang: str,
        target_lang: str,
        services: list[str],
    ) -> dict[str, str]:
        results: dict[str, str] = {}

        for service_name in services:
            try:
                results[service_name] = self.translate(
                    chunk, source_lang, target_lang, service_name
                )
            except Exception as e:
                logger.error("Translation failed for service %s: %s", service_name, e)
                results[service_name] = f"[Error: {e}]"

        return results

    def translate_parallel(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        services: list[str],
        chunk_size: int = 1000,
        max_workers: int = 3,
        progress_callback: Callable[[int, int], None] | None = None,
        on_token: dict[str, Callable[[str], None]] | None = None,
    ) -> dict[str, str]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return self._translate_parallel_sync(
                text, source_lang, target_lang, services, chunk_size, progress_callback, on_token
            )

        return asyncio.run(
            self._translate_parallel_async(
                text,
                source_lang,
                target_lang,
                services,
                chunk_size,
                max_workers,
                progress_callback,
                on_token,
            )
        )

    async def _translate_parallel_async(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        services: list[str],
        chunk_size: int,
        max_workers: int,
        progress_callback: Callable[[int, int], None] | None = None,
        on_token: dict[str, Callable[[str], None]] | None = None,
    ) -> dict[str, str]:
        chunks = self.split_text(text, chunk_size)

        # Deduplicate chunks: translate each unique chunk only once per service
        unique_chunks = list(dict.fromkeys(chunks))
        total_tasks = len(unique_chunks) * len(services)
        completed = 0
        deduped = len(chunks) - len(unique_chunks)
        logger.info(
            "Starting async parallel translation: %d chunks (%d unique, %d deduplicated), "
            "%d services",
            len(chunks),
            len(unique_chunks),
            deduped,
            len(services),
        )

        semaphore = asyncio.Semaphore(max_workers)
        unique_results: dict[str, dict[str, str]] = {service: {} for service in services}

        async def translate_task(chunk: str, service_name: str) -> None:
            nonlocal completed
            async with semaphore:
                try:
                    token_cb = on_token.get(service_name) if on_token else None
                    result = await asyncio.to_thread(
                        self.translate,
                        chunk,
                        source_lang,
                        target_lang,
                        service_name,
                        token_cb,
                    )
                except Exception as e:
                    logger.error("Chunk failed for %s: %s", service_name, e)
                    result = f"[Error: {e}]"
                unique_results[service_name][chunk] = result
                completed += 1
                if progress_callback:
                    progress_callback(completed, total_tasks)

        tasks = []
        for chunk in unique_chunks:
            for service_name in services:
                tasks.append(translate_task(chunk, service_name))

        await asyncio.gather(*tasks)

        # Map unique results back to original chunk order
        final_results: dict[str, str] = {}
        for service_name in services:
            ordered = [unique_results[service_name][chunk] for chunk in chunks]
            final_results[service_name] = " ".join(ordered)

        for service in final_results:
            final_results[service] = self.glossary.apply(final_results[service])

        self.cache.save()
        return final_results

    def _translate_parallel_sync(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        services: list[str],
        chunk_size: int,
        progress_callback: Callable[[int, int], None] | None = None,
        on_token: dict[str, Callable[[str], None]] | None = None,
    ) -> dict[str, str]:
        """Synchronous fallback when already inside an event loop."""
        chunks = self.split_text(text, chunk_size)

        # Deduplicate chunks: translate each unique chunk only once per service
        unique_chunks = list(dict.fromkeys(chunks))
        total_tasks = len(unique_chunks) * len(services)
        completed = 0

        unique_results: dict[str, dict[str, str]] = {service: {} for service in services}

        for chunk in unique_chunks:
            for service_name in services:
                try:
                    token_cb = on_token.get(service_name) if on_token else None
                    result = self.translate(chunk, source_lang, target_lang, service_name, token_cb)
                except Exception as e:
                    result = f"[Error: {e}]"
                unique_results[service_name][chunk] = result
                completed += 1
                if progress_callback:
                    progress_callback(completed, total_tasks)

        # Map unique results back to original chunk order
        final_results: dict[str, str] = {}
        for service_name in services:
            ordered = [unique_results[service_name][chunk] for chunk in chunks]
            final_results[service_name] = " ".join(ordered)

        for service in final_results:
            final_results[service] = self.glossary.apply(final_results[service])

        self.cache.save()
        return final_results

    def detect_language(self, text: str) -> str | None:
        return self.language_detector.detect(text)
