"""Groq translation service."""

from __future__ import annotations

import logging

from app.config.languages import get_language_name
from app.services.base import TranslationService

logger = logging.getLogger(__name__)

try:
    from groq import Groq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None  # type: ignore[misc, assignment]


class GroqService(TranslationService):
    """Groq API translation service."""

    AVAILABLE_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
        "mixtral-8x7b-32768",
    ]

    def __init__(self, api_key: str = "", model: str = "llama-3.3-70b-versatile") -> None:
        self.api_key = api_key
        self.model = model
        self._client: Groq | None = None

    def _get_client(self) -> Groq:
        if not GROQ_AVAILABLE:
            raise ValueError("Groq package is not installed")
        if self._client is None:
            self._client = Groq(api_key=self.api_key)
        return self._client

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not self.is_configured():
            raise ValueError("Groq API key not set")

        source_name = (
            get_language_name(source_lang) if source_lang != "auto" else "the source language"
        )
        target_name = get_language_name(target_lang)

        prompt = f"""Translate the following text from {source_name} to {target_name}.
Provide an accurate and natural translation:

{text}

Translation:"""

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Provide accurate, fluent translations that preserve the original meaning. Only output the translation, nothing else.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=2000,
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception as e:
            raise ValueError(f"Groq API error: {e}") from e

    def is_configured(self) -> bool:
        return bool(self.api_key) and GROQ_AVAILABLE

    def get_name(self) -> str:
        return f"Groq ({self.model})"
