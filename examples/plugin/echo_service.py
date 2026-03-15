"""Minimal example plugin for PolyTranslate.

This service simply returns the input text prefixed with the target language code.
It requires no API key and is always configured — useful as a starting point for
writing real plugins or for testing the plugin system.

Install in development mode from this directory:

    pip install -e examples/plugin/

Then run PolyTranslate — the "Echo (example)" service will appear automatically.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.base import TranslationService

if TYPE_CHECKING:
    from app.config.settings import Settings


class EchoTranslationService(TranslationService):
    """Echoes text back with a language tag — demonstrates the plugin interface."""

    def __init__(self, settings: Settings) -> None:
        # Plugins receive the application Settings instance.
        # Use it to read API keys or custom config values:
        #   self.api_key = settings.get_api_key("my_service")
        self._settings = settings

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return f"[{target_lang}] {text}"

    def is_configured(self) -> bool:
        return True

    def get_name(self) -> str:
        return "Echo (example)"
