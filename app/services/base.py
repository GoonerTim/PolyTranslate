"""Base class for translation services."""

from __future__ import annotations

from abc import ABC, abstractmethod


class TranslationService(ABC):
    """Abstract base class for translation services."""

    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text from source language to target language.

        Args:
            text: The text to translate.
            source_lang: Source language code (ISO 639-1).
            target_lang: Target language code (ISO 639-1).

        Returns:
            The translated text.

        Raises:
            ValueError: If translation fails or service is not configured.
        """
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the service is properly configured.

        Returns:
            True if the service can be used, False otherwise.
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the display name of the service.

        Returns:
            The human-readable name of the service.
        """
        ...

    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported language codes.

        Returns:
            List of ISO 639-1 language codes. Empty list means all languages.
        """
        return []
