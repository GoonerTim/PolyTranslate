"""Tests for DeepL translation service."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from app.services.deepl import DeepLService


class TestDeepLService:
    """Tests for DeepLService class."""

    def test_configured_without_key(self) -> None:
        service = DeepLService(api_key="")
        assert service.is_configured() is True

    def test_configured_with_key(self) -> None:
        service = DeepLService(api_key="test_key")
        assert service.is_configured() is True

    def test_get_name_with_key(self) -> None:
        service = DeepLService(api_key="test_key")
        assert service.get_name() == "DeepL"

    def test_get_name_without_key(self) -> None:
        service = DeepLService(api_key="")
        assert service.get_name() == "DeepL (Free)"

    def test_supported_languages(self) -> None:
        service = DeepLService(api_key="test_key")
        languages = service.get_supported_languages()
        assert "en" in languages
        assert "ru" in languages
        assert "de" in languages

    @respx.mock
    def test_translate_with_api_key_success(self, mock_deepl_response: dict[str, Any]) -> None:
        respx.post("https://api-free.deepl.com/v2/translate").mock(
            return_value=httpx.Response(200, json=mock_deepl_response)
        )

        service = DeepLService(api_key="test_key", is_free_plan=True)
        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @respx.mock
    def test_translate_pro_plan(self, mock_deepl_response: dict[str, Any]) -> None:
        respx.post("https://api.deepl.com/v2/translate").mock(
            return_value=httpx.Response(200, json=mock_deepl_response)
        )

        service = DeepLService(api_key="test_key", is_free_plan=False)
        result = service.translate("Hello, world!", "en", "ru")
        assert result == "Привет, мир!"

    @respx.mock
    def test_translate_free_api_without_key(self) -> None:
        free_response = {
            "result": {
                "translations": [
                    {
                        "beams": [
                            {"postprocessed_sentence": "Привет, мир!"},
                        ]
                    },
                ]
            }
        }
        respx.post("https://www2.deepl.com/jsonrpc").mock(
            return_value=httpx.Response(200, json=free_response)
        )

        service = DeepLService(api_key="")
        result = service.translate("Hello world!", "en", "ru")
        assert "Привет, мир!" in result

    @respx.mock
    def test_translate_free_api_multiple_sentences(self) -> None:
        free_response = {
            "result": {
                "translations": [
                    {
                        "beams": [
                            {"postprocessed_sentence": "Привет мир."},
                        ]
                    },
                    {
                        "beams": [
                            {"postprocessed_sentence": "Как дела?"},
                        ]
                    },
                ]
            }
        }
        respx.post("https://www2.deepl.com/jsonrpc").mock(
            return_value=httpx.Response(200, json=free_response)
        )

        service = DeepLService(api_key="")
        result = service.translate("Hello world. How are you?", "en", "ru")
        assert "Привет мир." in result
        assert "Как дела?" in result
        assert " " in result

    @respx.mock
    def test_translate_fallback_to_free_api(self) -> None:
        respx.post("https://api-free.deepl.com/v2/translate").mock(
            return_value=httpx.Response(403, json={"message": "Invalid API key"})
        )
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
        respx.post("https://www2.deepl.com/jsonrpc").mock(
            return_value=httpx.Response(200, json=free_response)
        )

        service = DeepLService(api_key="invalid_key", is_free_plan=True)
        result = service.translate("Hello, world!", "en", "ru")
        assert "Привет, мир!" in result

    @respx.mock
    def test_translate_quota_exceeded_fallback(self) -> None:
        respx.post("https://api-free.deepl.com/v2/translate").mock(
            return_value=httpx.Response(456, json={"message": "Quota exceeded"})
        )
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
        respx.post("https://www2.deepl.com/jsonrpc").mock(
            return_value=httpx.Response(200, json=free_response)
        )

        service = DeepLService(api_key="test_key", is_free_plan=True)
        result = service.translate("Hello", "en", "ru")
        assert "Привет" in result

    @respx.mock
    def test_unsupported_target_language_with_free_api(self) -> None:
        service = DeepLService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "xyz")
        assert "does not support" in str(exc_info.value)

    @respx.mock
    def test_free_api_error_handling(self) -> None:
        respx.post("https://www2.deepl.com/jsonrpc").mock(
            return_value=httpx.Response(500, json={"error": "Server error"})
        )

        service = DeepLService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "HTTP error 500" in str(exc_info.value)

    @respx.mock
    def test_free_api_unexpected_response_format(self) -> None:
        respx.post("https://www2.deepl.com/jsonrpc").mock(
            return_value=httpx.Response(200, json={"unexpected": "format"})
        )

        service = DeepLService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "Unexpected response format" in str(exc_info.value)

    @respx.mock
    def test_free_api_rate_limit_retry_success(self) -> None:
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
        route = respx.post("https://www2.deepl.com/jsonrpc")
        route.side_effect = [
            httpx.Response(429, json={"code": 429, "message": "Too many requests"}),
            httpx.Response(200, json=free_response),
        ]

        service = DeepLService(api_key="")
        result = service.translate("Hello, world!", "en", "ru")
        assert "Привет, мир!" in result
        assert route.call_count == 2

    @respx.mock
    def test_free_api_rate_limit_max_retries_exceeded(self) -> None:
        respx.post("https://www2.deepl.com/jsonrpc").mock(
            return_value=httpx.Response(429, json={"code": 429, "message": "Too many requests"})
        )

        service = DeepLService(api_key="")
        with pytest.raises(ValueError) as exc_info:
            service.translate("Hello", "en", "ru")
        assert "rate limit exceeded" in str(exc_info.value).lower()
