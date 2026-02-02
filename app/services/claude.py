"""Claude (Anthropic) translation service."""

from __future__ import annotations

from app.config.languages import get_language_name
from app.services.base import TranslationService

try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None  # type: ignore[misc, assignment]


class ClaudeService(TranslationService):
    """Anthropic Claude API translation service."""

    AVAILABLE_MODELS = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-2.1",
        "claude-2.0",
        "claude-instant-1.2",
    ]

    def __init__(self, api_key: str = "", model: str = "claude-3-sonnet-20240229") -> None:
        self.api_key = api_key
        self.model = model
        self._client: Anthropic | None = None

    def _get_client(self) -> Anthropic:
        if not ANTHROPIC_AVAILABLE:
            raise ValueError("Anthropic package is not installed")
        if self._client is None:
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not self.is_configured():
            raise ValueError("Anthropic API key not set")

        source_name = (
            get_language_name(source_lang) if source_lang != "auto" else "the source language"
        )
        target_name = get_language_name(target_lang)

        prompt = f"Translate the following text from {source_name} to {target_name}. Be accurate and preserve meaning. Only output the translation, nothing else.\n\nText to translate:\n{text}"

        try:
            client = self._get_client()
            message = client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            if message.content and len(message.content) > 0:
                return message.content[0].text.strip()
            return ""
        except Exception as e:
            raise ValueError(f"Claude API error: {e}") from e

    def is_configured(self) -> bool:
        return bool(self.api_key) and ANTHROPIC_AVAILABLE

    def get_name(self) -> str:
        return f"Claude ({self.model})"
