"""LocalAI translation service (OpenAI-compatible local server)."""

from __future__ import annotations

from app.config.languages import get_language_name
from app.services.base import TranslationService

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore[misc, assignment]


class LocalAIService(TranslationService):
    """LocalAI service using OpenAI-compatible local server."""

    def __init__(
        self,
        base_url: str = "",
        model: str = "default",
        api_key: str = "not-needed",
    ) -> None:
        """
        Initialize LocalAI service.

        Args:
            base_url: Base URL of the LocalAI server (e.g., http://localhost:8080/v1).
            model: Model name to use.
            api_key: API key (usually not needed for local servers).
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        """Get or create LocalAI client."""
        if not OPENAI_AVAILABLE:
            raise ValueError("OpenAI package is not installed")
        if self._client is None:
            self._client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )
        return self._client

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using LocalAI."""
        if not self.is_configured():
            raise ValueError("LocalAI server URL not configured")

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
            raise ValueError(f"LocalAI error: {e}") from e

    def is_configured(self) -> bool:
        """Check if the service is configured."""
        return bool(self.base_url) and OPENAI_AVAILABLE

    def get_name(self) -> str:
        """Get the service name."""
        return f"LocalAI ({self.model})"
