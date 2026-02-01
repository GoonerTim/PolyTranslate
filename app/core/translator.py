"""Main translator orchestration module."""

from __future__ import annotations

import concurrent.futures
from typing import TYPE_CHECKING

from nltk.tokenize import sent_tokenize

from app.config.settings import Settings
from app.core.language_detector import LanguageDetector
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
from app.utils.glossary import Glossary

if TYPE_CHECKING:
    from collections.abc import Callable


class SimpleTokenizer:
    """Fallback tokenizer when NLTK is not available."""

    @staticmethod
    def sent_tokenize(text: str) -> list[str]:
        """Simple sentence tokenizer."""
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
    """Safe sentence tokenizer with fallback."""
    try:
        return sent_tokenize(text)
    except LookupError:
        return SimpleTokenizer.sent_tokenize(text)
    except Exception:
        return SimpleTokenizer.sent_tokenize(text)


class Translator:
    """Main translator class that orchestrates translation services."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the translator with settings."""
        self.settings = settings or Settings()
        self.services: dict[str, TranslationService] = {}
        self.glossary = Glossary()
        self.language_detector = LanguageDetector()
        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize all translation services."""
        api_keys = self.settings.get_api_keys()

        # DeepL
        if api_keys.get("deepl"):
            self.services["deepl"] = DeepLService(
                api_key=api_keys["deepl"],
                is_free_plan=self.settings.get("deepl_plan", "free") == "free",
            )

        # Yandex (always available - uses free API if no key)
        self.services["yandex"] = YandexService(api_key=api_keys.get("yandex", ""))

        # Google (always available - uses free API if no key)
        self.services["google"] = GoogleService(api_key=api_keys.get("google", ""))

        # OpenAI
        if api_keys.get("openai"):
            self.services["openai"] = OpenAIService(
                api_key=api_keys["openai"],
                model=self.settings.get("openai_model", "gpt-3.5-turbo"),
            )

        # OpenRouter
        if api_keys.get("openrouter"):
            self.services["openrouter"] = OpenRouterService(
                api_key=api_keys["openrouter"],
                model=self.settings.get("openrouter_model", "openai/gpt-3.5-turbo"),
            )

        # ChatGPT Proxy (no API key needed)
        self.services["chatgpt_proxy"] = ChatGPTProxyService()

        # Groq
        if api_keys.get("groq"):
            self.services["groq"] = GroqService(
                api_key=api_keys["groq"],
                model=self.settings.get("groq_model", "mixtral-8x7b-32768"),
            )

        # Claude
        if api_keys.get("anthropic"):
            self.services["claude"] = ClaudeService(
                api_key=api_keys["anthropic"],
                model=self.settings.get("claude_model", "claude-3-sonnet-20240229"),
            )

        # LocalAI
        localai_url = self.settings.get("localai_url")
        if localai_url:
            self.services["localai"] = LocalAIService(
                base_url=localai_url,
                model=self.settings.get("localai_model", "default"),
            )

    def reload_services(self) -> None:
        """Reload services with updated settings."""
        self.services.clear()
        self._initialize_services()

    def get_available_services(self) -> list[str]:
        """Get list of available (configured) services."""
        return [name for name, service in self.services.items() if service.is_configured()]

    def split_text(self, text: str, chunk_size: int = 1000) -> list[str]:
        """Split text into chunks for translation."""
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
    ) -> str:
        """
        Translate text using a specific service.

        Args:
            text: Text to translate.
            source_lang: Source language code.
            target_lang: Target language code.
            service_name: Name of the translation service to use.

        Returns:
            Translated text.

        Raises:
            ValueError: If the service is not available.
        """
        service = self.services.get(service_name)
        if service is None:
            raise ValueError(f"Service '{service_name}' is not available")

        if not service.is_configured():
            raise ValueError(f"Service '{service_name}' is not configured")

        # Translate
        translated = service.translate(text, source_lang, target_lang)

        # Apply glossary
        translated = self.glossary.apply(translated)

        return translated

    def translate_chunk(
        self,
        chunk: str,
        source_lang: str,
        target_lang: str,
        services: list[str],
    ) -> dict[str, str]:
        """Translate a single chunk using multiple services."""
        results: dict[str, str] = {}

        for service_name in services:
            try:
                results[service_name] = self.translate(
                    chunk, source_lang, target_lang, service_name
                )
            except Exception as e:
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
    ) -> dict[str, str]:
        """
        Translate text using multiple services in parallel.

        Args:
            text: Text to translate.
            source_lang: Source language code.
            target_lang: Target language code.
            services: List of service names to use.
            chunk_size: Maximum chunk size.
            max_workers: Maximum number of parallel workers.
            progress_callback: Optional callback for progress updates.

        Returns:
            Dictionary mapping service names to translated text.
        """
        chunks = self.split_text(text, chunk_size)
        total_tasks = len(chunks) * len(services)
        completed = 0

        # Store results per service
        all_results: dict[str, list[str]] = {service: [] for service in services}

        def translate_task(chunk: str, chunk_idx: int, service_name: str) -> tuple[int, str, str]:
            """Task for translating a single chunk with a single service."""
            try:
                result = self.translate(chunk, source_lang, target_lang, service_name)
            except Exception as e:
                result = f"[Error: {e}]"
            return chunk_idx, service_name, result

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for chunk_idx, chunk in enumerate(chunks):
                for service_name in services:
                    future = executor.submit(translate_task, chunk, chunk_idx, service_name)
                    futures.append(future)

            # Collect results
            chunk_results: dict[str, dict[int, str]] = {service: {} for service in services}

            for future in concurrent.futures.as_completed(futures):
                chunk_idx, service_name, result = future.result()
                chunk_results[service_name][chunk_idx] = result
                completed += 1
                if progress_callback:
                    progress_callback(completed, total_tasks)

        # Combine chunks for each service
        for service_name in services:
            ordered_chunks = [chunk_results[service_name][i] for i in range(len(chunks))]
            all_results[service_name] = ordered_chunks

        # Join chunks
        final_results = {service: " ".join(chunks) for service, chunks in all_results.items()}

        # Apply glossary to final results
        for service in final_results:
            final_results[service] = self.glossary.apply(final_results[service])

        return final_results

    def detect_language(self, text: str) -> str | None:
        """Detect the language of text."""
        return self.language_detector.detect(text)
