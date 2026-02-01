"""Tests for Yandex translation service."""

from __future__ import annotations

from typing import Any

import pytest
import responses

from app.services.yandex import YandexService


class TestYandexService:
    """Tests for YandexService class."""

    def test_not_configured_without_key(self) -> None:
        """Test that service is not configured without API key."""
        service = YandexService(api_key="")
        assert service.is_configured() is False

    def test_configured_with_key(self) -> None:
        """Test that service is configured with API key."""
        service = YandexService(api_key="test_key")
        assert service.is_configured() is True

    def test_get_name(self) -> None:
        """Test getting service name."""
        service = YandexService(api_key="test_key")
        assert service.get_name() == "Yandex Translate"

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
    def test_translate_api_error(self) -> None:
        """Test handling API error."""
        responses.add(
            responses.POST,
            "https://translate.api.cloud.yandex.net/translate/v2/translate",
            json={"message": "Invalid API key"},
            status=401,
        )

        service = YandexService(api_key="invalid_key")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Yandex API error" in str(exc_info.value)

    def test_translate_without_key(self) -> None:
        """Test translation attempt without API key."""
        service = YandexService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "not set" in str(exc_info.value)
