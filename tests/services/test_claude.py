"""Tests for Claude (Anthropic) translation service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.claude import ClaudeService


class TestClaudeService:
    """Tests for ClaudeService class."""

    def test_not_configured_without_key(self) -> None:
        """Test that service is not configured without API key."""
        service = ClaudeService(api_key="")
        assert service.is_configured() is False

    def test_configured_with_key(self) -> None:
        """Test that service is configured with API key."""
        service = ClaudeService(api_key="test_key")
        assert service.api_key == "test_key"

    def test_get_name(self) -> None:
        """Test getting service name."""
        service = ClaudeService(api_key="test_key", model="claude-3-opus-20240229")
        assert "claude-3-opus-20240229" in service.get_name()
        assert "Claude" in service.get_name()

    def test_available_models(self) -> None:
        """Test that available models are defined."""
        assert "claude-3-opus-20240229" in ClaudeService.AVAILABLE_MODELS
        assert "claude-3-sonnet-20240229" in ClaudeService.AVAILABLE_MODELS
        assert "claude-3-haiku-20240307" in ClaudeService.AVAILABLE_MODELS

    def test_translate_without_key(self) -> None:
        """Test translation attempt without API key."""
        service = ClaudeService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "not set" in str(exc_info.value) or "not configured" in str(exc_info.value)

    @patch("app.services.claude.ANTHROPIC_AVAILABLE", True)
    @patch("app.services.claude.Anthropic")
    def test_translate_success(self, mock_anthropic_class: MagicMock) -> None:
        """Test successful translation."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Привет, мир!"
        mock_client.messages.create.return_value = mock_response

        service = ClaudeService(api_key="test_key")
        service._client = mock_client

        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @patch("app.services.claude.ANTHROPIC_AVAILABLE", True)
    @patch("app.services.claude.Anthropic")
    def test_translate_with_auto_detect(self, mock_anthropic_class: MagicMock) -> None:
        """Test translation with auto language detection."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Привет!"
        mock_client.messages.create.return_value = mock_response

        service = ClaudeService(api_key="test_key")
        service._client = mock_client

        result = service.translate("Hello!", "auto", "ru")
        assert result == "Привет!"

    @patch("app.services.claude.ANTHROPIC_AVAILABLE", True)
    @patch("app.services.claude.Anthropic")
    def test_translate_api_error(self, mock_anthropic_class: MagicMock) -> None:
        """Test handling API error."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        service = ClaudeService(api_key="test_key")
        service._client = mock_client

        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Claude API error" in str(exc_info.value)

    @patch("app.services.claude.ANTHROPIC_AVAILABLE", True)
    @patch("app.services.claude.Anthropic")
    def test_translate_empty_response(self, mock_anthropic_class: MagicMock) -> None:
        """Test handling empty response."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = []
        mock_client.messages.create.return_value = mock_response

        service = ClaudeService(api_key="test_key")
        service._client = mock_client

        result = service.translate("Hello", "en", "ru")
        assert result == ""
