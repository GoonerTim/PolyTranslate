"""Tests for Google translation service."""

from __future__ import annotations

from typing import Any

import pytest
import responses

from app.services.google import GoogleService


class TestGoogleService:
    """Tests for GoogleService class."""

    def test_not_configured_without_key(self) -> None:
        """Test that service is not configured without API key."""
        service = GoogleService(api_key="")
        assert service.is_configured() is False

    def test_configured_with_key(self) -> None:
        """Test that service is configured with API key."""
        service = GoogleService(api_key="test_key")
        assert service.is_configured() is True

    def test_get_name(self) -> None:
        """Test getting service name."""
        service = GoogleService(api_key="test_key")
        assert service.get_name() == "Google Translate"

    @responses.activate
    def test_translate_success(self, mock_google_response: dict[str, Any]) -> None:
        """Test successful translation."""
        responses.add(
            responses.POST,
            "https://translation.googleapis.com/language/translate/v2",
            json=mock_google_response,
            status=200,
        )

        service = GoogleService(api_key="test_key")
        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @responses.activate
    def test_translate_with_auto_detect(self, mock_google_response: dict[str, Any]) -> None:
        """Test translation with auto language detection."""
        responses.add(
            responses.POST,
            "https://translation.googleapis.com/language/translate/v2",
            json=mock_google_response,
            status=200,
        )

        service = GoogleService(api_key="test_key")
        result = service.translate("Hello, world!", "auto", "ru")
        assert result == "Привет, мир!"

    @responses.activate
    def test_translate_api_error(self) -> None:
        """Test handling API error."""
        responses.add(
            responses.POST,
            "https://translation.googleapis.com/language/translate/v2",
            json={"error": {"message": "Invalid API key"}},
            status=403,
        )

        service = GoogleService(api_key="invalid_key")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Google API error" in str(exc_info.value)

    def test_translate_without_key(self) -> None:
        """Test translation attempt without API key."""
        service = GoogleService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "not set" in str(exc_info.value)
