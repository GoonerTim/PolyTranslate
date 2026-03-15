"""Tests for Google translation service."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from app.services.google import GoogleService


class TestGoogleService:
    """Tests for GoogleService class."""

    def test_not_configured_without_key(self) -> None:
        service = GoogleService(api_key="")
        assert service.is_configured() is True

    def test_configured_with_key(self) -> None:
        service = GoogleService(api_key="test_key")
        assert service.is_configured() is True

    def test_get_name(self) -> None:
        service = GoogleService(api_key="test_key")
        assert service.get_name() == "Google Translate"

    def test_get_name_free(self) -> None:
        service = GoogleService(api_key="")
        assert service.get_name() == "Google Translate (Free)"

    @respx.mock
    def test_translate_success(self, mock_google_response: dict[str, Any]) -> None:
        respx.post("https://translation.googleapis.com/language/translate/v2").mock(
            return_value=httpx.Response(200, json=mock_google_response)
        )

        service = GoogleService(api_key="test_key")
        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @respx.mock
    def test_translate_with_auto_detect(self, mock_google_response: dict[str, Any]) -> None:
        respx.post("https://translation.googleapis.com/language/translate/v2").mock(
            return_value=httpx.Response(200, json=mock_google_response)
        )

        service = GoogleService(api_key="test_key")
        result = service.translate("Hello, world!", "auto", "ru")
        assert result == "Привет, мир!"

    @respx.mock
    def test_translate_api_error_fallback_to_free(self) -> None:
        respx.post("https://translation.googleapis.com/language/translate/v2").mock(
            return_value=httpx.Response(403, json={"error": {"message": "Invalid API key"}})
        )

        respx.get("https://translate.googleapis.com/translate_a/single").mock(
            return_value=httpx.Response(200, json=[[["Привет", "Hello", None, None]]])
        )

        service = GoogleService(api_key="invalid_key")
        result = service.translate("Hello", "en", "ru")
        assert result == "Привет"

    @respx.mock
    def test_translate_with_free_api(self) -> None:
        respx.get("https://translate.googleapis.com/translate_a/single").mock(
            return_value=httpx.Response(200, json=[[["Привет", "Hello", None, None]]])
        )

        service = GoogleService(api_key="")
        result = service.translate("Hello", "en", "ru")
        assert result == "Привет"

    @respx.mock
    def test_translate_free_api_error(self) -> None:
        respx.get("https://translate.googleapis.com/translate_a/single").mock(
            return_value=httpx.Response(500, json={"error": "Server error"})
        )

        service = GoogleService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Google free API" in str(exc_info.value)

    @respx.mock
    def test_translate_free_api_unexpected_format(self) -> None:
        respx.get("https://translate.googleapis.com/translate_a/single").mock(
            return_value=httpx.Response(200, json={"unexpected": "format"})
        )

        service = GoogleService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "parse" in str(exc_info.value).lower() or "unexpected" in str(exc_info.value).lower()

    @respx.mock
    def test_translate_paid_api_error(self) -> None:
        respx.post("https://translation.googleapis.com/language/translate/v2").mock(
            return_value=httpx.Response(403, json={"error": "forbidden"})
        )

        service = GoogleService(api_key="bad_key")
        service._translate_free = lambda *a: "fallback"  # type: ignore[assignment]
        result = service.translate("Hello", "en", "ru")
        assert result == "fallback"

    @respx.mock
    def test_translate_paid_api_request_exception(self) -> None:
        respx.post("https://translation.googleapis.com/language/translate/v2").mock(
            side_effect=httpx.ConnectError("timeout")
        )

        service = GoogleService(api_key="key")
        with pytest.raises(ValueError, match="Google API request failed"):
            service._translate_with_api_key("Hello", "en", "ru")

    @respx.mock
    def test_translate_free_api_429_retry_then_success(self) -> None:
        route = respx.get("https://translate.googleapis.com/translate_a/single")
        route.side_effect = [
            httpx.Response(429),
            httpx.Response(200, json=[[["Привет", "Hello"]]]),
        ]

        service = GoogleService(api_key="")
        result = service._translate_free("Hello", "en", "ru")
        assert result == "Привет"

    @respx.mock
    def test_translate_free_api_429_exhausted(self) -> None:
        respx.get("https://translate.googleapis.com/translate_a/single").mock(
            return_value=httpx.Response(429)
        )

        service = GoogleService(api_key="")
        with pytest.raises(ValueError, match="rate limit"):
            service._translate_free("Hello", "en", "ru")

    @respx.mock
    def test_translate_free_api_request_error_retry(self) -> None:
        route = respx.get("https://translate.googleapis.com/translate_a/single")
        route.side_effect = [
            httpx.ConnectError("fail"),
            httpx.Response(200, json=[[["Привет", "Hello"]]]),
        ]

        service = GoogleService(api_key="")
        result = service._translate_free("Hello", "en", "ru")
        assert result == "Привет"

    @respx.mock
    def test_translate_free_api_request_error_exhausted(self) -> None:
        respx.get("https://translate.googleapis.com/translate_a/single").mock(
            side_effect=httpx.ConnectError("fail")
        )

        service = GoogleService(api_key="")
        with pytest.raises(ValueError, match="request failed"):
            service._translate_free("Hello", "en", "ru")

    @respx.mock
    def test_translate_free_api_max_retries_exceeded(self) -> None:
        respx.get("https://translate.googleapis.com/translate_a/single").mock(
            return_value=httpx.Response(429)
        )

        service = GoogleService(api_key="")
        with pytest.raises(ValueError):
            service._translate_free("Hello", "en", "ru")
