"""Tests for ChatGPT Proxy translation service."""

from __future__ import annotations

from typing import Any

import pytest
import responses

from app.services.chatgpt_proxy import ChatGPTProxyService


class TestChatGPTProxyService:
    """Tests for ChatGPTProxyService class."""

    def test_always_configured(self) -> None:
        """Test that service is always configured (no API key needed)."""
        service = ChatGPTProxyService()
        assert service.is_configured() is True

    def test_get_name(self) -> None:
        """Test getting service name."""
        service = ChatGPTProxyService()
        assert service.get_name() == "ChatGPT Proxy"

    def test_supported_languages(self) -> None:
        """Test that supported languages are defined."""
        service = ChatGPTProxyService()
        languages = service.get_supported_languages()
        assert "en" in languages
        assert "ru" in languages
        assert "de" in languages

    @responses.activate
    def test_translate_success(self, mock_chatgpt_proxy_response: dict[str, Any]) -> None:
        """Test successful translation."""
        responses.add(
            responses.POST,
            "https://mtdev.bytequests.com/v1/translation/chat-gpt",
            json=mock_chatgpt_proxy_response,
            status=200,
        )

        service = ChatGPTProxyService()
        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @responses.activate
    def test_translate_with_auto_detect(self, mock_chatgpt_proxy_response: dict[str, Any]) -> None:
        """Test translation with auto language detection."""
        responses.add(
            responses.POST,
            "https://mtdev.bytequests.com/v1/translation/chat-gpt",
            json=mock_chatgpt_proxy_response,
            status=200,
        )

        service = ChatGPTProxyService()
        result = service.translate("Hello, world!", "auto", "ru")
        assert result == "Привет, мир!"

    @responses.activate
    def test_translate_api_error(self) -> None:
        """Test handling API error."""
        responses.add(
            responses.POST,
            "https://mtdev.bytequests.com/v1/translation/chat-gpt",
            json={"error": "Server error"},
            status=500,
        )

        service = ChatGPTProxyService()
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "ChatGPT Proxy error" in str(exc_info.value)

    @responses.activate
    def test_translate_unexpected_response(self) -> None:
        """Test handling unexpected response structure."""
        responses.add(
            responses.POST,
            "https://mtdev.bytequests.com/v1/translation/chat-gpt",
            json={"unexpected": "structure"},
            status=200,
        )

        service = ChatGPTProxyService()
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Unexpected response" in str(exc_info.value)

    def test_unsupported_target_language(self) -> None:
        """Test handling unsupported target language."""
        service = ChatGPTProxyService()
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "xyz")
        assert "does not support" in str(exc_info.value)

    def test_uuid_generation(self) -> None:
        """Test that UUID is generated correctly."""
        service = ChatGPTProxyService()
        uuid1 = service._generate_uuid()
        uuid2 = service._generate_uuid()

        # Should be valid UUIDs
        assert len(uuid1) == 36
        assert uuid1.count("-") == 4

        # Should be unique
        assert uuid1 != uuid2
