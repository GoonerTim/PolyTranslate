"""OpenRouter translation service."""

from __future__ import annotations

from typing import Any

from app.services.llm_base import LLMTranslationService

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore[misc, assignment]


class OpenRouterService(LLMTranslationService):
    """OpenRouter API translation service (OpenAI-compatible)."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str = "",
        model: str = "openai/gpt-4o-mini",
        site_url: str = "",
        site_name: str = "Translator App",
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            display_name="OpenRouter",
            error_prefix="OpenRouter API",
        )
        self.site_url = site_url
        self.site_name = site_name

    def _create_client(self) -> Any:
        return OpenAI(
            base_url=self.BASE_URL,
            api_key=self.api_key,
            default_headers={
                "HTTP-Referer": self.site_url,
                "X-Title": self.site_name,
            },
        )

    def _is_available(self) -> bool:
        return OPENAI_AVAILABLE
