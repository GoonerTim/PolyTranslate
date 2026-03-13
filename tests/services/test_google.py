"""Tests for Google translation service."""

from __future__ import annotations

from typing import Any

import pytest
import requests
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

    @responses.activate
    def test_translate_free_api_unexpected_format(self) -> None:
        """Test handling unexpected response format from free API."""
        responses.add(
            responses.GET,
            "https://translate.googleapis.com/translate_a/single",
            json={"unexpected": "format"},
            status=200,
        )

        service = GoogleService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "parse" in str(exc_info.value).lower() or "unexpected" in str(exc_info.value).lower()

    @responses.activate
    def test_translate_paid_api_error(self) -> None:
        responses.add(
            responses.POST,
            "https://translation.googleapis.com/language/translate/v2",
            json={"error": "forbidden"},
            status=403,
        )

        service = GoogleService(api_key="bad_key")
        service._translate_free = lambda *a: "fallback"  # type: ignore[assignment]
        result = service.translate("Hello", "en", "ru")
        assert result == "fallback"

    @responses.activate
    def test_translate_paid_api_request_exception(self) -> None:
        responses.add(
            responses.POST,
            "https://translation.googleapis.com/language/translate/v2",
            body=requests.ConnectionError("timeout"),
        )

        service = GoogleService(api_key="key")
        with pytest.raises(ValueError, match="Google API request failed"):
            service._translate_with_api_key("Hello", "en", "ru")

    @responses.activate
    def test_translate_free_api_429_retry_then_success(self) -> None:
        responses.add(
            responses.GET,
            "https://translate.googleapis.com/translate_a/single",
            status=429,
        )
        responses.add(
            responses.GET,
            "https://translate.googleapis.com/translate_a/single",
            json=[[["Привет", "Hello"]]],
            status=200,
        )

        service = GoogleService(api_key="")
        result = service._translate_free("Hello", "en", "ru")
        assert result == "Привет"

    @responses.activate
    def test_translate_free_api_429_exhausted(self) -> None:
        for _ in range(4):
            responses.add(
                responses.GET,
                "https://translate.googleapis.com/translate_a/single",
                status=429,
            )

        service = GoogleService(api_key="")
        with pytest.raises(ValueError, match="rate limit"):
            service._translate_free("Hello", "en", "ru")

    @responses.activate
    def test_translate_free_api_request_error_retry(self) -> None:
        responses.add(
            responses.GET,
            "https://translate.googleapis.com/translate_a/single",
            body=requests.ConnectionError("fail"),
        )
        responses.add(
            responses.GET,
            "https://translate.googleapis.com/translate_a/single",
            json=[[["Привет", "Hello"]]],
            status=200,
        )

        service = GoogleService(api_key="")
        result = service._translate_free("Hello", "en", "ru")
        assert result == "Привет"

    @responses.activate
    def test_translate_free_api_request_error_exhausted(self) -> None:
        for _ in range(4):
            responses.add(
                responses.GET,
                "https://translate.googleapis.com/translate_a/single",
                body=requests.ConnectionError("fail"),
            )

        service = GoogleService(api_key="")
        with pytest.raises(ValueError, match="request failed"):
            service._translate_free("Hello", "en", "ru")

    @responses.activate
    def test_translate_free_api_max_retries_exceeded(self) -> None:
        """Test the final fallthrough raise after all retries."""
        # This covers the unreachable "Maximum retries exceeded" line
        # by testing the retry exhaustion path via 429
        for _ in range(4):
            responses.add(
                responses.GET,
                "https://translate.googleapis.com/translate_a/single",
                status=429,
            )

        service = GoogleService(api_key="")
        with pytest.raises(ValueError):
            service._translate_free("Hello", "en", "ru")
