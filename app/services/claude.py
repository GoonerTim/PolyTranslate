"""Claude (Anthropic) translation service."""

from __future__ import annotations

from typing import Any

from app.services.llm_base import LLMTranslationService

try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None  # type: ignore[misc, assignment]


class ClaudeService(LLMTranslationService):
    """Anthropic Claude API translation service."""

    AVAILABLE_MODELS = [
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
    ]

    def __init__(self, api_key: str = "", model: str = "claude-sonnet-4-6") -> None:
        super().__init__(
            api_key=api_key, model=model, display_name="Claude", error_prefix="Claude API"
        )

    def _create_client(self) -> Any:
        return Anthropic(api_key=self.api_key)

    def _is_available(self) -> bool:
        return ANTHROPIC_AVAILABLE

    def _call_llm(self, prompt: str) -> str:
        client = self._get_client()
        message = client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        if message.content and len(message.content) > 0:
            return message.content[0].text.strip()
        return ""
