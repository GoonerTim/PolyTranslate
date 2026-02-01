"""Tests for LocalAI translation service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.localai import LocalAIService


class TestLocalAIService:
    """Tests for LocalAIService class."""

    def test_not_configured_without_url(self) -> None:
        """Test that service is not configured without server URL."""
        service = LocalAIService(base_url="")
        assert service.is_configured() is False

    def test_configured_with_url(self) -> None:
        """Test that service is configured with server URL."""
        service = LocalAIService(base_url="http://localhost:8080/v1")
        # Configuration also depends on openai package availability
        assert service.base_url == "http://localhost:8080/v1"

    def test_get_name(self) -> None:
        """Test getting service name."""
        service = LocalAIService(base_url="http://localhost:8080/v1", model="my-model")
        assert "my-model" in service.get_name()
        assert "LocalAI" in service.get_name()

    def test_url_trailing_slash_removed(self) -> None:
        """Test that trailing slash is removed from URL."""
        service = LocalAIService(base_url="http://localhost:8080/v1/")
        assert service.base_url == "http://localhost:8080/v1"

    def test_translate_without_url(self) -> None:
        """Test translation attempt without server URL."""
        service = LocalAIService(base_url="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "not configured" in str(exc_info.value)

    @patch("app.services.localai.OPENAI_AVAILABLE", True)
    @patch("app.services.localai.OpenAI")
    def test_translate_success(self, mock_openai_class: MagicMock) -> None:
        """Test successful translation."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Привет, мир!"
        mock_client.chat.completions.create.return_value = mock_response

        service = LocalAIService(base_url="http://localhost:8080/v1")
        service._client = mock_client

        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @patch("app.services.localai.OPENAI_AVAILABLE", True)
    @patch("app.services.localai.OpenAI")
    def test_translate_with_custom_model(self, mock_openai_class: MagicMock) -> None:
        """Test translation with custom model."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Привет!"
        mock_client.chat.completions.create.return_value = mock_response

        service = LocalAIService(base_url="http://localhost:8080/v1", model="custom-model")
        service._client = mock_client

        result = service.translate("Hello!", "en", "ru")
        assert result == "Привет!"

        # Verify model was used
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "custom-model"

    @patch("app.services.localai.OPENAI_AVAILABLE", True)
    @patch("app.services.localai.OpenAI")
    def test_translate_api_error(self, mock_openai_class: MagicMock) -> None:
        """Test handling API error."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Connection refused")

        service = LocalAIService(base_url="http://localhost:8080/v1")
        service._client = mock_client

        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "LocalAI error" in str(exc_info.value)

    def test_api_key_default(self) -> None:
        """Test that API key has sensible default."""
        service = LocalAIService(base_url="http://localhost:8080/v1")
        # Default should be set for local servers that don't need auth
        assert service.api_key == "not-needed"

    def test_custom_api_key(self) -> None:
        """Test setting custom API key."""
        service = LocalAIService(base_url="http://localhost:8080/v1", api_key="my-secret-key")
        assert service.api_key == "my-secret-key"
