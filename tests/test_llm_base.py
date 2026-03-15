"""Tests for LLMTranslationService base class."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.services.llm_base import LLMTranslationService


class _DummyLLM(LLMTranslationService):
    """Concrete subclass for testing the abstract base."""

    AVAILABLE_MODELS = ["model-a", "model-b"]

    def __init__(self, api_key: str = "key", model: str = "model-a", available: bool = True):
        super().__init__(
            api_key=api_key, model=model, display_name="Dummy", error_prefix="Dummy API"
        )
        self._available = available

    def _create_client(self) -> Any:
        return MagicMock()

    def _is_available(self) -> bool:
        return self._available


class TestLLMTranslationServiceBase:
    def test_is_configured_true(self) -> None:
        svc = _DummyLLM(api_key="sk-123", available=True)
        assert svc.is_configured() is True

    def test_is_configured_no_key(self) -> None:
        svc = _DummyLLM(api_key="", available=True)
        assert svc.is_configured() is False

    def test_is_configured_not_available(self) -> None:
        svc = _DummyLLM(api_key="sk-123", available=False)
        assert svc.is_configured() is False

    def test_get_name(self) -> None:
        svc = _DummyLLM(model="model-b")
        assert svc.get_name() == "Dummy (model-b)"

    def test_translate_not_configured_raises(self) -> None:
        svc = _DummyLLM(api_key="")
        with pytest.raises(ValueError, match="not configured"):
            svc.translate("hello", "en", "ru")

    def test_translate_success(self) -> None:
        svc = _DummyLLM()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Привет"
        mock_client.chat.completions.create.return_value = mock_response
        svc._client = mock_client

        result = svc.translate("Hello", "en", "ru")
        assert result == "Привет"

    def test_translate_auto_source_lang(self) -> None:
        svc = _DummyLLM()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hola"
        mock_client.chat.completions.create.return_value = mock_response
        svc._client = mock_client

        result = svc.translate("Hello", "auto", "es")
        assert result == "Hola"
        # Verify "the source language" was used in prompt
        call_args = mock_client.chat.completions.create.call_args
        user_msg = call_args[1]["messages"][1]["content"]
        assert "the source language" in user_msg

    def test_translate_wraps_exception(self) -> None:
        svc = _DummyLLM()
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("API down")
        svc._client = mock_client

        with pytest.raises(ValueError, match="Dummy API error"):
            svc.translate("Hello", "en", "ru")

    def test_call_llm_empty_content(self) -> None:
        svc = _DummyLLM()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response
        svc._client = mock_client

        result = svc._call_llm("test prompt")
        assert result == ""

    def test_get_client_not_available_raises(self) -> None:
        svc = _DummyLLM(available=False)
        with pytest.raises(ValueError, match="not installed"):
            svc._get_client()

    def test_get_client_caches_instance(self) -> None:
        svc = _DummyLLM()
        client1 = svc._get_client()
        client2 = svc._get_client()
        assert client1 is client2
