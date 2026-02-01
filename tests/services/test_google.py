"""Tests for Google translation service."""

from __future__ import annotations

from typing import Any

import pytest
import responses

from app.services.google import GoogleService


class TestGoogleService:
    """Tests for GoogleService class."""

    def test_not_configured_without_key(self) -> None:
        """Test that service is always configured (free API available)."""
        service = GoogleService(api_key="")
        assert service.is_configured() is True

    def test_configured_with_key(self) -> None:
        """Test that service is configured with API key."""
        service = GoogleService(api_key="test_key")
        assert service.is_configured() is True

    def test_get_name(self) -> None:
        """Test getting service name."""
        service = GoogleService(api_key="test_key")
        assert service.get_name() == "Google Translate"

    def test_get_name_free(self) -> None:
        """Test getting service name without API key (free mode)."""
        service = GoogleService(api_key="")
        assert service.get_name() == "Google Translate (Free)"

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
    def test_translate_api_error_fallback_to_free(self) -> None:
        """Test handling API error with fallback to free API."""
        # Mock paid API returning error
        responses.add(
            responses.POST,
            "https://translation.googleapis.com/language/translate/v2",
            json={"error": {"message": "Invalid API key"}},
            status=403,
        )

        # Mock free API returning success
        responses.add(
            responses.GET,
            "https://translate.googleapis.com/translate_a/single",
            json=[[["Привет", "Hello", None, None]]],
            status=200,
        )

        service = GoogleService(api_key="invalid_key")
        result = service.translate("Hello", "en", "ru")
        # Should fallback to free API and succeed
        assert result == "Привет"

    @responses.activate
    def test_translate_with_free_api(self) -> None:
        """Test translation using free API without API key."""
        # Mock free API
        responses.add(
            responses.GET,
            "https://translate.googleapis.com/translate_a/single",
            json=[[["Привет", "Hello", None, None]]],
            status=200,
        )

        service = GoogleService(api_key="")
        result = service.translate("Hello", "en", "ru")
        assert result == "Привет"

    @responses.activate
    def test_translate_free_api_error(self) -> None:
        """Test error handling when free API fails."""
        responses.add(
            responses.GET,
            "https://translate.googleapis.com/translate_a/single",
            json={"error": "Server error"},
            status=500,
        )

        service = GoogleService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Google free API" in str(exc_info.value)
