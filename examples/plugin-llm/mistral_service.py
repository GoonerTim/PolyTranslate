"""Example AI plugin for PolyTranslate — Mistral translation service.

Demonstrates how to add an LLM-based translation service as a plugin.
Mistral exposes an OpenAI-compatible API, so we inherit from
``LLMTranslationService`` and only implement two methods.

Setup:
    1. Get an API key at https://console.mistral.ai/
    2. In PolyTranslate config.json, add: "api_keys": { "mistral": "your-key" }
    3. Install:  pip install -e examples/plugin-llm/
    4. Run PolyTranslate — "Mistral (mistral-large-latest)" appears automatically.

Streaming, prompt construction, and error handling are all inherited from
LLMTranslationService — no extra code needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.llm_base import LLMTranslationService

if TYPE_CHECKING:
    from app.config.settings import Settings

try:
    from openai import OpenAI

    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False
    OpenAI = None  # type: ignore[misc, assignment]

MISTRAL_BASE_URL = "https://api.mistral.ai/v1"

AVAILABLE_MODELS = [
    "mistral-large-latest",
    "mistral-medium-latest",
    "mistral-small-latest",
    "open-mistral-nemo",
]


class MistralTranslationService(LLMTranslationService):
    """Mistral AI translation via OpenAI-compatible endpoint."""

    AVAILABLE_MODELS = AVAILABLE_MODELS

    def __init__(self, settings: Settings) -> None:
        # Plugin constructors always receive a Settings instance.
        # Read the API key from config.json -> api_keys -> mistral.
        api_key = settings.get_api_key("mistral") or ""

        # Read timeout: per-service override ("mistral") or global default.
        timeouts = settings.get("service_timeouts", {})
        timeout = float(timeouts.get("mistral", settings.get("service_timeout", 1800.0)))

        super().__init__(
            api_key=api_key,
            model="mistral-large-latest",
            display_name="Mistral",
            error_prefix="Mistral API",
            timeout=timeout,
        )

    def _create_client(self) -> Any:
        return OpenAI(api_key=self.api_key, base_url=MISTRAL_BASE_URL, timeout=self.timeout)

    def _is_available(self) -> bool:
        return _AVAILABLE
