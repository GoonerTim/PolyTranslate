"""Groq translation service."""

from __future__ import annotations

from app.config.languages import get_language_name
from app.services.base import TranslationService

try:
    from groq import Groq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None  # type: ignore[misc, assignment]


class GroqService(TranslationService):
    """Groq API translation service."""

    AVAILABLE_MODELS = [
        "mixtral-8x7b-32768",
        "llama2-70b-4096",
        "gemma-7b-it",
        "llama3-8b-8192",
        "llama3-70b-8192",
    ]

    def __init__(self, api_key: str = "", model: str = "mixtral-8x7b-32768") -> None:
        """
        Initialize Groq service.

        Args:
            api_key: Groq API key.
            model: Model to use for translation.
        """
        self.api_key = api_key
        self.model = model
        self._client: Groq | None = None

    def _get_client(self) -> Groq:
        """Get or create Groq client."""
        if not GROQ_AVAILABLE:
            raise ValueError("Groq package is not installed")
        if self._client is None:
            self._client = Groq(api_key=self.api_key)
        return self._client

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using Groq API."""
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
        """Check if the service is configured."""
        return bool(self.api_key) and GROQ_AVAILABLE

    def get_name(self) -> str:
        """Get the service name."""
        return f"Groq ({self.model})"
