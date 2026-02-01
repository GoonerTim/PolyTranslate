"""Tests for DeepL translation service."""

from __future__ import annotations

from typing import Any

import pytest
import responses

from app.services.deepl import DeepLService


class TestDeepLService:
    """Tests for DeepLService class."""

    def test_not_configured_without_key(self) -> None:
        """Test that service is not configured without API key."""
        service = DeepLService(api_key="")
        assert service.is_configured() is False

    def test_configured_with_key(self) -> None:
        """Test that service is configured with API key."""
        service = DeepLService(api_key="test_key")
        assert service.is_configured() is True

    def test_get_name(self) -> None:
        """Test getting service name."""
        service = DeepLService(api_key="test_key")
        assert service.get_name() == "DeepL"

    def test_supported_languages(self) -> None:
        """Test that supported languages are defined."""
        service = DeepLService(api_key="test_key")
        languages = service.get_supported_languages()
        assert "en" in languages
        assert "ru" in languages
        assert "de" in languages

    @responses.activate
    def test_translate_success(self, mock_deepl_response: dict[str, Any]) -> None:
        """Test successful translation."""
        responses.add(
            responses.POST,
            "https://api-free.deepl.com/v2/translate",
            json=mock_deepl_response,
            status=200,
        )

        service = DeepLService(api_key="test_key", is_free_plan=True)
        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @responses.activate
    def test_translate_pro_plan(self, mock_deepl_response: dict[str, Any]) -> None:
        """Test translation with Pro plan."""
        responses.add(
            responses.POST,
            "https://api.deepl.com/v2/translate",
            json=mock_deepl_response,
            status=200,
        )

        service = DeepLService(api_key="test_key", is_free_plan=False)
        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @responses.activate
    def test_translate_quota_exceeded(self) -> None:
        """Test handling quota exceeded error."""
        responses.add(
            responses.POST,
            "https://api-free.deepl.com/v2/translate",
            json={"message": "Quota exceeded"},
            status=456,
        )

        service = DeepLService(api_key="test_key", is_free_plan=True)
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Quota exceeded" in str(exc_info.value)

    @responses.activate
    def test_translate_invalid_key(self) -> None:
        """Test handling invalid API key."""
        responses.add(
            responses.POST,
            "https://api-free.deepl.com/v2/translate",
            json={"message": "Invalid API key"},
            status=403,
        )

        service = DeepLService(api_key="invalid_key", is_free_plan=True)
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Invalid API key" in str(exc_info.value)

    def test_translate_without_key(self) -> None:
        """Test translation attempt without API key."""
        service = DeepLService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "not set" in str(exc_info.value)

    def test_unsupported_target_language(self) -> None:
        """Test handling unsupported target language."""
        service = DeepLService(api_key="test_key")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "xyz")
        assert "does not support" in str(exc_info.value)
