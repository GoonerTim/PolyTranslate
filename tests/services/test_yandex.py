"""Tests for Yandex translation service."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from app.services.yandex import YandexService


class TestYandexService:
    """Tests for YandexService class."""

    def test_not_configured_without_key(self) -> None:
        service = YandexService(api_key="")
        assert service.is_configured() is True

    def test_configured_with_key(self) -> None:
        service = YandexService(api_key="test_key")
        assert service.is_configured() is True

    def test_get_name(self) -> None:
        service = YandexService(api_key="test_key")
        assert service.get_name() == "Yandex Translate"

    def test_get_name_free(self) -> None:
        service = YandexService(api_key="")
        assert service.get_name() == "Yandex Translate (Free)"

    @respx.mock
    def test_translate_success(self, mock_yandex_response: dict[str, Any]) -> None:
        respx.post("https://translate.api.cloud.yandex.net/translate/v2/translate").mock(
            return_value=httpx.Response(200, json=mock_yandex_response)
        )

        service = YandexService(api_key="test_key")
        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @respx.mock
    def test_translate_with_auto_detect(self, mock_yandex_response: dict[str, Any]) -> None:
        respx.post("https://translate.api.cloud.yandex.net/translate/v2/translate").mock(
            return_value=httpx.Response(200, json=mock_yandex_response)
        )

        service = YandexService(api_key="test_key")
        result = service.translate("Hello, world!", "auto", "ru")
        assert result == "Привет, мир!"

    @respx.mock
    def test_translate_api_error_fallback_to_free(self) -> None:
        respx.post("https://translate.api.cloud.yandex.net/translate/v2/translate").mock(
            return_value=httpx.Response(401, json={"message": "Invalid API key"})
        )

        respx.post("https://translate.yandex.net/api/v1/tr.json/translate").mock(
            return_value=httpx.Response(200, json={"code": 200, "text": ["Привет"]})
        )

        service = YandexService(api_key="invalid_key")
        result = service.translate("Hello", "en", "ru")
        assert result == "Привет"

    @respx.mock
    def test_translate_with_free_api(self) -> None:
        respx.post("https://translate.yandex.net/api/v1/tr.json/translate").mock(
            return_value=httpx.Response(200, json={"code": 200, "text": ["Привет"]})
        )

        service = YandexService(api_key="")
        result = service.translate("Hello", "en", "ru")
        assert result == "Привет"

    @respx.mock
    def test_translate_free_api_error(self) -> None:
        respx.post("https://translate.yandex.net/api/v1/tr.json/translate").mock(
            return_value=httpx.Response(200, json={"code": 500, "message": "Server error"})
        )

        service = YandexService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Yandex free API error" in str(exc_info.value)

    @respx.mock
    def test_translate_paid_api_error(self) -> None:
        respx.post("https://translate.api.cloud.yandex.net/translate/v2/translate").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )

        service = YandexService(api_key="bad_key")
        with pytest.raises(ValueError, match="Yandex API error"):
            service._translate_with_api_key("Hello", "en", "ru")

    @respx.mock
    def test_translate_paid_api_request_exception(self) -> None:
        respx.post("https://translate.api.cloud.yandex.net/translate/v2/translate").mock(
            side_effect=httpx.ConnectError("timeout")
        )

        service = YandexService(api_key="key")
        with pytest.raises(ValueError, match="Yandex API request failed"):
            service._translate_with_api_key("Hello", "en", "ru")

    @respx.mock
    def test_translate_free_api_429_retry_then_success(self) -> None:
        route = respx.post("https://translate.yandex.net/api/v1/tr.json/translate")
        route.side_effect = [
            httpx.Response(429),
            httpx.Response(200, json={"code": 200, "text": ["Привет"]}),
        ]

        service = YandexService(api_key="")
        result = service._translate_free("Hello", "en", "ru")
        assert result == "Привет"

    @respx.mock
    def test_translate_free_api_429_exhausted(self) -> None:
        respx.post("https://translate.yandex.net/api/v1/tr.json/translate").mock(
            return_value=httpx.Response(429)
        )

        service = YandexService(api_key="")
        with pytest.raises(ValueError, match="rate limit"):
            service._translate_free("Hello", "en", "ru")

    @respx.mock
    def test_translate_free_api_request_error_retry(self) -> None:
        route = respx.post("https://translate.yandex.net/api/v1/tr.json/translate")
        route.side_effect = [
            httpx.ConnectError("fail"),
            httpx.Response(200, json={"code": 200, "text": ["Привет"]}),
        ]

        service = YandexService(api_key="")
        result = service._translate_free("Hello", "en", "ru")
        assert result == "Привет"

    @respx.mock
    def test_translate_free_api_request_error_exhausted(self) -> None:
        respx.post("https://translate.yandex.net/api/v1/tr.json/translate").mock(
            side_effect=httpx.ConnectError("fail")
        )

        service = YandexService(api_key="")
        with pytest.raises(ValueError, match="request failed"):
            service._translate_free("Hello", "en", "ru")

    @respx.mock
    def test_translate_free_api_http_error(self) -> None:
        respx.post("https://translate.yandex.net/api/v1/tr.json/translate").mock(
            return_value=httpx.Response(500, text="Internal error")
        )

        service = YandexService(api_key="")
        with pytest.raises(ValueError, match="HTTP error"):
            service._translate_free("Hello", "en", "ru")
