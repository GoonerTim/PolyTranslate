"""Tests for OpenRouter translation service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.openrouter import OpenRouterService


class TestOpenRouterService:
    """Tests for OpenRouterService class."""

    def test_not_configured_without_key(self) -> None:
        """Test that service is not configured without API key."""
        service = OpenRouterService(api_key="")
        assert service.is_configured() is False

    def test_configured_with_key(self) -> None:
        """Test that service is configured with API key."""
        service = OpenRouterService(api_key="test_key")
        assert service.api_key == "test_key"

    def test_get_name(self) -> None:
        """Test getting service name."""
        service = OpenRouterService(api_key="test_key", model="anthropic/claude-3-opus")
        assert "anthropic/claude-3-opus" in service.get_name()
        assert "OpenRouter" in service.get_name()

    def test_base_url(self) -> None:
        """Test that correct base URL is used."""
        service = OpenRouterService(api_key="test_key")
        assert service.BASE_URL == "https://openrouter.ai/api/v1"

    def test_translate_without_key(self) -> None:
        """Test translation attempt without API key."""
        service = OpenRouterService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "not set" in str(exc_info.value) or "not configured" in str(exc_info.value)

    @patch("app.services.openrouter.OPENAI_AVAILABLE", True)
    @patch("app.services.openrouter.OpenAI")
    def test_translate_success(self, mock_openai_class: MagicMock) -> None:
        """Test successful translation."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Привет, мир!"
        mock_client.chat.completions.create.return_value = mock_response

        service = OpenRouterService(api_key="test_key")
        service._client = mock_client

        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @patch("app.services.openrouter.OPENAI_AVAILABLE", True)
    @patch("app.services.openrouter.OpenAI")
    def test_site_headers(self, mock_openai_class: MagicMock) -> None:
        """Test that site headers are set correctly."""
        service = OpenRouterService(
            api_key="test_key",
            site_url="https://example.com",
            site_name="My App",
        )

        assert service.site_url == "https://example.com"
        assert service.site_name == "My App"
