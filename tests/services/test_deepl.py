"""Tests for DeepL translation service."""

from __future__ import annotations

from typing import Any

import pytest
import responses

from app.services.deepl import DeepLService


class TestDeepLService:
    """Tests for DeepLService class."""

    def test_configured_without_key(self) -> None:
        """Test that service is always configured (uses free API if no key)."""
        service = DeepLService(api_key="")
        assert service.is_configured() is True

    def test_configured_with_key(self) -> None:
        """Test that service is configured with API key."""
        service = DeepLService(api_key="test_key")
        assert service.is_configured() is True

    def test_get_name_with_key(self) -> None:
        """Test getting service name with API key."""
        service = DeepLService(api_key="test_key")
        assert service.get_name() == "DeepL"

    def test_get_name_without_key(self) -> None:
        """Test getting service name without API key shows (Free) suffix."""
        service = DeepLService(api_key="")
        assert service.get_name() == "DeepL (Free)"

    def test_supported_languages(self) -> None:
        """Test that supported languages are defined."""
        service = DeepLService(api_key="test_key")
        languages = service.get_supported_languages()
        assert "en" in languages
        assert "ru" in languages
        assert "de" in languages

    @responses.activate
    def test_translate_with_api_key_success(self, mock_deepl_response: dict[str, Any]) -> None:
        """Test successful translation with API key."""
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
    def test_translate_free_api_without_key(self) -> None:
        """Test translation using unofficial free API when no API key."""
        free_response = {
            "result": {
                "translations": [
                    {
                        "beams": [
                            {"postprocessed_sentence": "Привет"},
                        ]
                    },
                    {
                        "beams": [
                            {"postprocessed_sentence": "мир!"},
                        ]
                    },
                ]
            }
        }
        responses.add(
            responses.POST,
            "https://www2.deepl.com/jsonrpc",
            json=free_response,
            status=200,
        )

        service = DeepLService(api_key="")
        result = service.translate("Hello world!", "en", "ru")
        assert "Привет" in result
        assert "мир!" in result

    @responses.activate
    def test_translate_fallback_to_free_api(self) -> None:
        """Test automatic fallback from paid API to free API on error."""
        # Paid API fails
        responses.add(
            responses.POST,
            "https://api-free.deepl.com/v2/translate",
            json={"message": "Invalid API key"},
            status=403,
        )
        # Free API succeeds
        free_response = {
            "result": {
                "translations": [
                    {
                        "beams": [
                            {"postprocessed_sentence": "Привет, мир!"},
                        ]
                    }
                ]
            }
        }
        responses.add(
            responses.POST,
            "https://www2.deepl.com/jsonrpc",
            json=free_response,
            status=200,
        )

        service = DeepLService(api_key="invalid_key", is_free_plan=True)
        result = service.translate("Hello, world!", "en", "ru")
        assert "Привет, мир!" in result

    @responses.activate
    def test_translate_quota_exceeded_fallback(self) -> None:
        """Test fallback to free API when quota exceeded."""
        # Paid API quota exceeded
        responses.add(
            responses.POST,
            "https://api-free.deepl.com/v2/translate",
            json={"message": "Quota exceeded"},
            status=456,
        )
        # Free API succeeds
        free_response = {
            "result": {
                "translations": [
                    {
                        "beams": [
                            {"postprocessed_sentence": "Привет"},
                        ]
                    }
                ]
            }
        }
        responses.add(
            responses.POST,
            "https://www2.deepl.com/jsonrpc",
            json=free_response,
            status=200,
        )

        service = DeepLService(api_key="test_key", is_free_plan=True)
        result = service.translate("Hello", "en", "ru")
        assert "Привет" in result

    @responses.activate
    def test_unsupported_target_language_with_free_api(self) -> None:
        """Test handling unsupported target language with free API."""
        service = DeepLService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "xyz")
        assert "does not support" in str(exc_info.value)

    @responses.activate
    def test_free_api_error_handling(self) -> None:
        """Test error handling when free API fails."""
        responses.add(
            responses.POST,
            "https://www2.deepl.com/jsonrpc",
            json={"error": "Server error"},
            status=500,
        )

        service = DeepLService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "HTTP error 500" in str(exc_info.value)

    @responses.activate
    def test_free_api_unexpected_response_format(self) -> None:
        """Test handling unexpected response format from free API."""
        responses.add(
            responses.POST,
            "https://www2.deepl.com/jsonrpc",
            json={"unexpected": "format"},
            status=200,
        )

        service = DeepLService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Unexpected response format" in str(exc_info.value)
