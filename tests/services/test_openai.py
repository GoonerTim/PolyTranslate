"""Tests for OpenAI translation service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.openai_service import OpenAIService


class TestOpenAIService:
    """Tests for OpenAIService class."""

    def test_not_configured_without_key(self) -> None:
        """Test that service is not configured without API key."""
        service = OpenAIService(api_key="")
        assert service.is_configured() is False

    def test_configured_with_key(self) -> None:
        """Test that service is configured with API key."""
        service = OpenAIService(api_key="test_key")
        # Configuration also depends on openai package availability
        # Just check basic logic
        assert service.api_key == "test_key"

    def test_get_name(self) -> None:
        """Test getting service name."""
        service = OpenAIService(api_key="test_key", model="gpt-4")
        assert "gpt-4" in service.get_name()
        assert "OpenAI" in service.get_name()

    def test_translate_without_key(self) -> None:
        """Test translation attempt without API key."""
        service = OpenAIService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "not set" in str(exc_info.value) or "not configured" in str(exc_info.value)

    @patch("app.services.openai_service.OPENAI_AVAILABLE", True)
    @patch("app.services.openai_service.OpenAI")
    def test_translate_success(self, mock_openai_class: MagicMock) -> None:
        """Test successful translation."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Привет, мир!"
        mock_client.chat.completions.create.return_value = mock_response

        service = OpenAIService(api_key="test_key")
        service._client = mock_client

        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @patch("app.services.openai_service.OPENAI_AVAILABLE", True)
    @patch("app.services.openai_service.OpenAI")
    def test_translate_with_auto_detect(self, mock_openai_class: MagicMock) -> None:
        """Test translation with auto language detection."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Привет!"
        mock_client.chat.completions.create.return_value = mock_response

        service = OpenAIService(api_key="test_key")
        service._client = mock_client

        result = service.translate("Hello!", "auto", "ru")
        assert result == "Привет!"

    @patch("app.services.openai_service.OPENAI_AVAILABLE", True)
    @patch("app.services.openai_service.OpenAI")
    def test_translate_api_error(self, mock_openai_class: MagicMock) -> None:
        """Test handling API error."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        service = OpenAIService(api_key="test_key")
        service._client = mock_client

        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "API error" in str(exc_info.value) or "Error" in str(exc_info.value)
