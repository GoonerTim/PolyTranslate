"""Groq translation service."""

from __future__ import annotations

from typing import Any

from app.services.llm_base import LLMTranslationService

try:
    from groq import Groq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None  # type: ignore[misc, assignment]


class GroqService(LLMTranslationService):
    """Groq API translation service."""

    AVAILABLE_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
        "mixtral-8x7b-32768",
    ]

    def __init__(
        self, api_key: str = "", model: str = "llama-3.3-70b-versatile", timeout: float = 1800.0
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            display_name="Groq",
            error_prefix="Groq API",
            timeout=timeout,
        )

    def _create_client(self) -> Any:
        return Groq(api_key=self.api_key, timeout=self.timeout)

    def _is_available(self) -> bool:
        return GROQ_AVAILABLE
