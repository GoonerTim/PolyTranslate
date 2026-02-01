"""OpenRouter translation service."""

from __future__ import annotations

from app.config.languages import get_language_name
from app.services.base import TranslationService

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore[misc, assignment]


class OpenRouterService(TranslationService):
    """OpenRouter API translation service (OpenAI-compatible)."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str = "",
        model: str = "openai/gpt-3.5-turbo",
        site_url: str = "",
        site_name: str = "Translator App",
    ) -> None:
        """
        Initialize OpenRouter service.

        Args:
            api_key: OpenRouter API key.
            model: Model to use for translation.
            site_url: Your site URL (for rankings).
            site_name: Your site name (for rankings).
        """
        self.api_key = api_key
        self.model = model
        self.site_url = site_url
        self.site_name = site_name
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        """Get or create OpenRouter client."""
        if not OPENAI_AVAILABLE:
            raise ValueError("OpenAI package is not installed")
        if self._client is None:
            self._client = OpenAI(
                base_url=self.BASE_URL,
                api_key=self.api_key,
                default_headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
            )
        return self._client

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using OpenRouter API."""
        if not self.is_configured():
            raise ValueError("OpenRouter API key not set")

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
            raise ValueError(f"OpenRouter API error: {e}") from e

    def is_configured(self) -> bool:
        """Check if the service is configured."""
        return bool(self.api_key) and OPENAI_AVAILABLE

    def get_name(self) -> str:
        """Get the service name."""
        return f"OpenRouter ({self.model})"
