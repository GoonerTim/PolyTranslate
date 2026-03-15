"""LocalAI translation service (OpenAI-compatible local server)."""

from __future__ import annotations

from typing import Any

from app.services.llm_base import LLMTranslationService

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore[misc, assignment]


class LocalAIService(LLMTranslationService):
    """LocalAI service using OpenAI-compatible local server."""

    def __init__(
        self,
        base_url: str = "",
        model: str = "default",
        api_key: str = "not-needed",
        timeout: float = 1800.0,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            display_name="LocalAI",
            error_prefix="LocalAI",
            timeout=timeout,
        )
        self.base_url = base_url.rstrip("/")

    def _create_client(self) -> Any:
        return OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=self.timeout)

    def _is_available(self) -> bool:
        return OPENAI_AVAILABLE

    def is_configured(self) -> bool:
        return bool(self.base_url) and OPENAI_AVAILABLE
