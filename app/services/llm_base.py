"""Base class for OpenAI-compatible LLM translation services."""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Any

from app.config.languages import get_language_name
from app.services.base import TranslationService

logger = logging.getLogger(__name__)


class LLMTranslationService(TranslationService):
    """Base for LLM-based translation services (OpenAI-compatible)."""

    AVAILABLE_MODELS: list[str] = []

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
        display_name: str = "",
        error_prefix: str = "",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self._display_name = display_name
        self._error_prefix = error_prefix
        self._client: Any = None

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not self.is_configured():
            raise ValueError(f"{self._error_prefix} not configured")

        source_name = (
            get_language_name(source_lang) if source_lang != "auto" else "the source language"
        )
        target_name = get_language_name(target_lang)

        prompt = (
            f"Translate the following text from {source_name} to {target_name}. "
            f"Be accurate and preserve meaning:\n\n{text}"
        )

        try:
            return self._call_llm(prompt)
        except Exception as e:
            raise ValueError(f"{self._error_prefix} error: {e}") from e

    def _call_llm(self, prompt: str) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional translator. Provide accurate, natural translations. Only output the translation, nothing else.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.3,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""

    def _get_client(self) -> Any:
        if not self._is_available():
            raise ValueError(f"{self._display_name} package is not installed")
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def is_configured(self) -> bool:
        return bool(self.api_key) and self._is_available()

    def get_name(self) -> str:
        return f"{self._display_name} ({self.model})"

    @abstractmethod
    def _create_client(self) -> Any: ...

    @abstractmethod
    def _is_available(self) -> bool: ...
