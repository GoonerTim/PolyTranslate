"""Tests for Groq translation service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.groq_service import GroqService


class TestGroqService:
    """Tests for GroqService class."""

    def test_not_configured_without_key(self) -> None:
        """Test that service is not configured without API key."""
        service = GroqService(api_key="")
        assert service.is_configured() is False

    def test_configured_with_key(self) -> None:
        """Test that service is configured with API key."""
        service = GroqService(api_key="test_key")
        assert service.api_key == "test_key"

    def test_get_name(self) -> None:
        """Test getting service name."""
        service = GroqService(api_key="test_key", model="llama3-70b-8192")
        assert "llama3-70b-8192" in service.get_name()
        assert "Groq" in service.get_name()

    def test_available_models(self) -> None:
        """Test that available models are defined."""
        assert "mixtral-8x7b-32768" in GroqService.AVAILABLE_MODELS
        assert "llama3-70b-8192" in GroqService.AVAILABLE_MODELS

    def test_translate_without_key(self) -> None:
        """Test translation attempt without API key."""
        service = GroqService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "not set" in str(exc_info.value) or "not configured" in str(exc_info.value)

    @patch("app.services.groq_service.GROQ_AVAILABLE", True)
    @patch("app.services.groq_service.Groq")
    def test_translate_success(self, mock_groq_class: MagicMock) -> None:
        """Test successful translation."""
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Привет, мир!"
        mock_client.chat.completions.create.return_value = mock_response

        service = GroqService(api_key="test_key")
        service._client = mock_client

        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @patch("app.services.groq_service.GROQ_AVAILABLE", True)
    @patch("app.services.groq_service.Groq")
    def test_translate_with_auto_detect(self, mock_groq_class: MagicMock) -> None:
        """Test translation with auto language detection."""
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Привет!"
        mock_client.chat.completions.create.return_value = mock_response

        service = GroqService(api_key="test_key")
        service._client = mock_client

        result = service.translate("Hello!", "auto", "ru")
        assert result == "Привет!"

    @patch("app.services.groq_service.GROQ_AVAILABLE", True)
    @patch("app.services.groq_service.Groq")
    def test_translate_api_error(self, mock_groq_class: MagicMock) -> None:
        """Test handling API error."""
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        service = GroqService(api_key="test_key")
        service._client = mock_client

        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Groq API error" in str(exc_info.value)
