"""OpenAI translation service."""

from __future__ import annotations

from app.config.languages import get_language_name
from app.services.base import TranslationService

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore[misc, assignment]


class OpenAIService(TranslationService):
    """OpenAI GPT translation service."""

    AVAILABLE_MODELS = [
        "gpt-4-turbo-preview",
        "gpt-4",
        "gpt-3.5-turbo",
        "gpt-4o",
        "gpt-4o-mini",
    ]

    def __init__(self, api_key: str = "", model: str = "gpt-3.5-turbo") -> None:
        self.api_key = api_key
        self.model = model
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if not OPENAI_AVAILABLE:
            raise ValueError("OpenAI package is not installed")
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not self.is_configured():
            raise ValueError("OpenAI API key not set")

        source_name = (
            get_language_name(source_lang) if source_lang != "auto" else "the source language"
        )
        target_name = get_language_name(target_lang)

        prompt = f"Translate the following text from {source_name} to {target_name}. Be accurate and preserve meaning:\n\n{text}"

        try:
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
        except Exception as e:
            raise ValueError(f"OpenAI API error: {e}") from e

    def is_configured(self) -> bool:
        return bool(self.api_key) and OPENAI_AVAILABLE

    def get_name(self) -> str:
        return f"OpenAI ({self.model})"
