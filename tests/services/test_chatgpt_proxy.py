"""Tests for ChatGPT Proxy translation service."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from app.services.chatgpt_proxy import ChatGPTProxyService


class TestChatGPTProxyService:
    """Tests for ChatGPTProxyService class."""

    def test_always_configured(self) -> None:
        service = ChatGPTProxyService()
        assert service.is_configured() is True

    def test_get_name(self) -> None:
        service = ChatGPTProxyService()
        assert service.get_name() == "ChatGPT Proxy"

    def test_supported_languages(self) -> None:
        service = ChatGPTProxyService()
        languages = service.get_supported_languages()
        assert "en" in languages
        assert "ru" in languages
        assert "de" in languages

    @respx.mock
    def test_translate_success(self, mock_chatgpt_proxy_response: dict[str, Any]) -> None:
        respx.post("https://mtdev.bytequests.com/v1/translation/chat-gpt").mock(
            return_value=httpx.Response(200, json=mock_chatgpt_proxy_response)
        )

        service = ChatGPTProxyService()
        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @respx.mock
    def test_translate_with_auto_detect(self, mock_chatgpt_proxy_response: dict[str, Any]) -> None:
        respx.post("https://mtdev.bytequests.com/v1/translation/chat-gpt").mock(
            return_value=httpx.Response(200, json=mock_chatgpt_proxy_response)
        )

        service = ChatGPTProxyService()
        result = service.translate("Hello, world!", "auto", "ru")
        assert result == "Привет, мир!"

    @respx.mock
    def test_translate_api_error(self) -> None:
        respx.post("https://mtdev.bytequests.com/v1/translation/chat-gpt").mock(
            return_value=httpx.Response(500, json={"error": "Server error"})
        )

        service = ChatGPTProxyService()
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "ChatGPT Proxy error" in str(exc_info.value)

    @respx.mock
    def test_translate_unexpected_response(self) -> None:
        respx.post("https://mtdev.bytequests.com/v1/translation/chat-gpt").mock(
            return_value=httpx.Response(200, json={"unexpected": "structure"})
        )

        service = ChatGPTProxyService()
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Unexpected response" in str(exc_info.value)

    def test_unsupported_target_language(self) -> None:
        service = ChatGPTProxyService()
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "xyz")
        assert "does not support" in str(exc_info.value)
