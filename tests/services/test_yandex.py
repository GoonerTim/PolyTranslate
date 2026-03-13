"""Tests for Yandex translation service."""

from __future__ import annotations

from typing import Any

import pytest
import requests
import responses

from app.services.yandex import YandexService


class TestYandexService:
    """Tests for YandexService class."""

    def test_not_configured_without_key(self) -> None:
        """Test that service is always configured (free API available)."""
        service = YandexService(api_key="")
        assert service.is_configured() is True

    def test_configured_with_key(self) -> None:
        """Test that service is configured with API key."""
        service = YandexService(api_key="test_key")
        assert service.is_configured() is True

    def test_get_name(self) -> None:
        """Test getting service name."""
        service = YandexService(api_key="test_key")
        assert service.get_name() == "Yandex Translate"

    def test_get_name_free(self) -> None:
        """Test getting service name without API key (free mode)."""
        service = YandexService(api_key="")
        assert service.get_name() == "Yandex Translate (Free)"

    @responses.activate
    def test_translate_success(self, mock_yandex_response: dict[str, Any]) -> None:
        """Test successful translation."""
        responses.add(
            responses.POST,
            "https://translate.api.cloud.yandex.net/translate/v2/translate",
            json=mock_yandex_response,
            status=200,
        )

        service = YandexService(api_key="test_key")
        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @responses.activate
    def test_translate_with_auto_detect(self, mock_yandex_response: dict[str, Any]) -> None:
        """Test translation with auto language detection."""
        responses.add(
            responses.POST,
            "https://translate.api.cloud.yandex.net/translate/v2/translate",
            json=mock_yandex_response,
            status=200,
        )

        service = YandexService(api_key="test_key")
        result = service.translate("Hello, world!", "auto", "ru")
        assert result == "Привет, мир!"

        # Verify that sourceLanguageCode was not sent for auto
        request_body = responses.calls[0].request.body
        assert request_body is not None

    @responses.activate
    def test_translate_api_error_fallback_to_free(self) -> None:
        """Test handling API error with fallback to free API."""
        # Mock paid API returning error
        responses.add(
            responses.POST,
            "https://translate.api.cloud.yandex.net/translate/v2/translate",
            json={"message": "Invalid API key"},
            status=401,
        )

        # Mock free API returning success
        responses.add(
            responses.POST,
            "https://translate.yandex.net/api/v1/tr.json/translate",
            json={"code": 200, "text": ["Привет"]},
            status=200,
        )

        service = YandexService(api_key="invalid_key")
        result = service.translate("Hello", "en", "ru")
        # Should fallback to free API and succeed
        assert result == "Привет"

    @responses.activate
    def test_translate_with_free_api(self) -> None:
        """Test translation using free API without API key."""
        # Mock free API
        responses.add(
            responses.POST,
            "https://translate.yandex.net/api/v1/tr.json/translate",
            json={"code": 200, "text": ["Привет"]},
            status=200,
        )

        service = YandexService(api_key="")
        result = service.translate("Hello", "en", "ru")
        assert result == "Привет"

    @responses.activate
    def test_translate_free_api_error(self) -> None:
        """Test error handling when free API fails."""
        responses.add(
            responses.POST,
            "https://translate.yandex.net/api/v1/tr.json/translate",
            json={"code": 500, "message": "Server error"},
            status=200,
        )

        service = YandexService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Yandex free API error" in str(exc_info.value)

    @responses.activate
    def test_translate_paid_api_error(self) -> None:
        responses.add(
            responses.POST,
            "https://translate.api.cloud.yandex.net/translate/v2/translate",
            json={"message": "Unauthorized"},
            status=401,
        )

        service = YandexService(api_key="bad_key")
        with pytest.raises(ValueError, match="Yandex API error"):
            service._translate_with_api_key("Hello", "en", "ru")

    @responses.activate
    def test_translate_paid_api_request_exception(self) -> None:
        responses.add(
            responses.POST,
            "https://translate.api.cloud.yandex.net/translate/v2/translate",
            body=requests.ConnectionError("timeout"),
        )

        service = YandexService(api_key="key")
        with pytest.raises(ValueError, match="Yandex API request failed"):
            service._translate_with_api_key("Hello", "en", "ru")

    @responses.activate
    def test_translate_free_api_429_retry_then_success(self) -> None:
        responses.add(
            responses.POST,
            "https://translate.yandex.net/api/v1/tr.json/translate",
            status=429,
        )
        responses.add(
            responses.POST,
            "https://translate.yandex.net/api/v1/tr.json/translate",
            json={"code": 200, "text": ["Привет"]},
            status=200,
        )

        service = YandexService(api_key="")
        result = service._translate_free("Hello", "en", "ru")
        assert result == "Привет"

    @responses.activate
    def test_translate_free_api_429_exhausted(self) -> None:
        for _ in range(4):
            responses.add(
                responses.POST,
                "https://translate.yandex.net/api/v1/tr.json/translate",
                status=429,
            )

        service = YandexService(api_key="")
        with pytest.raises(ValueError, match="rate limit"):
            service._translate_free("Hello", "en", "ru")

    @responses.activate
    def test_translate_free_api_request_error_retry(self) -> None:
        responses.add(
            responses.POST,
            "https://translate.yandex.net/api/v1/tr.json/translate",
            body=requests.ConnectionError("fail"),
        )
        responses.add(
            responses.POST,
            "https://translate.yandex.net/api/v1/tr.json/translate",
            json={"code": 200, "text": ["Привет"]},
            status=200,
        )

        service = YandexService(api_key="")
        result = service._translate_free("Hello", "en", "ru")
        assert result == "Привет"

    @responses.activate
    def test_translate_free_api_request_error_exhausted(self) -> None:
        for _ in range(4):
            responses.add(
                responses.POST,
                "https://translate.yandex.net/api/v1/tr.json/translate",
                body=requests.ConnectionError("fail"),
            )

        service = YandexService(api_key="")
        with pytest.raises(ValueError, match="request failed"):
            service._translate_free("Hello", "en", "ru")

    @responses.activate
    def test_translate_free_api_http_error(self) -> None:
        responses.add(
            responses.POST,
            "https://translate.yandex.net/api/v1/tr.json/translate",
            status=500,
            body="Internal error",
        )

        service = YandexService(api_key="")
        with pytest.raises(ValueError, match="HTTP error"):
            service._translate_free("Hello", "en", "ru")
