"""OpenAI translation service."""

from __future__ import annotations

from typing import Any

from app.services.llm_base import LLMTranslationService

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore[misc, assignment]


class OpenAIService(LLMTranslationService):
    """OpenAI GPT translation service."""

    AVAILABLE_MODELS = [
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
        "gpt-4o",
        "gpt-4o-mini",
        "o3-mini",
        "gpt-4-turbo",
    ]

    def __init__(
        self, api_key: str = "", model: str = "gpt-4o-mini", timeout: float = 1800.0
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            display_name="OpenAI",
            error_prefix="OpenAI API",
            timeout=timeout,
        )

    def _create_client(self) -> Any:
        return OpenAI(api_key=self.api_key, timeout=self.timeout)

    def _is_available(self) -> bool:
        return OPENAI_AVAILABLE
