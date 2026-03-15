"""Extended tests for translator module — covering uncovered lines."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.config.settings import Settings
from app.core.translator import Translator


def _make_settings(**overrides: object) -> Settings:
    """Create a Settings instance with custom values without loading from disk."""
    s = Settings.__new__(Settings)
    s.config_path = MagicMock()
    s.config_path.exists.return_value = False
    s._settings = {"api_keys": {}}
    s._settings.update(overrides)
    return s


class TestTranslatorInitialization:
    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_initialize_openai_service(self, _: MagicMock) -> None:
        settings = _make_settings(api_keys={"openai": "sk-test"}, openai_model="gpt-4o")
        t = Translator(settings)
        assert "openai" in t.services

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_initialize_groq_service(self, _: MagicMock) -> None:
        settings = _make_settings(api_keys={"groq": "gsk-test"})
        t = Translator(settings)
        assert "groq" in t.services

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_initialize_claude_service(self, _: MagicMock) -> None:
        settings = _make_settings(api_keys={"anthropic": "sk-ant-test"})
        t = Translator(settings)
        assert "claude" in t.services

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_initialize_localai_service(self, _: MagicMock) -> None:
        settings = _make_settings(localai_url="http://localhost:8080")
        t = Translator(settings)
        assert "localai" in t.services

    @patch("app.core.translator.discover_plugins")
    def test_plugin_conflict_skipped(self, mock_plugins: MagicMock) -> None:
        plugin = MagicMock()
        plugin.service_id = "deepl"
        plugin.service = MagicMock()
        mock_plugins.return_value = [plugin]
        settings = _make_settings()
        t = Translator(settings)
        assert t.services["deepl"] is not plugin.service


class TestTranslatorTranslate:
    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_translate_service_not_configured(self, _: MagicMock) -> None:
        t = Translator(_make_settings())
        mock_svc = MagicMock()
        mock_svc.is_configured.return_value = False
        t.services["test_svc"] = mock_svc
        with pytest.raises(ValueError, match="not configured"):
            t.translate("hello", "en", "ru", "test_svc")

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_translate_cache_hit(self, _: MagicMock) -> None:
        t = Translator(_make_settings())
        mock_svc = MagicMock()
        mock_svc.is_configured.return_value = True
        t.services["test_svc"] = mock_svc
        t.cache.put("hello", "en", "ru", "test_svc", "привет")
        result = t.translate("hello", "en", "ru", "test_svc")
        assert "привет" in result
        mock_svc.translate.assert_not_called()


class TestTranslateParallel:
    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_translate_parallel_sync_fallback(self, _: MagicMock) -> None:
        import asyncio

        t = Translator(_make_settings())
        mock_svc = MagicMock()
        mock_svc.is_configured.return_value = True
        mock_svc.translate.return_value = "translated"
        t.services["test_svc"] = mock_svc

        async def run_inside_loop() -> dict[str, str]:
            return t.translate_parallel("hello", "en", "ru", ["test_svc"])

        result = asyncio.run(run_inside_loop())
        assert "test_svc" in result

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_translate_parallel_with_progress(self, _: MagicMock) -> None:
        t = Translator(_make_settings())
        mock_svc = MagicMock()
        mock_svc.is_configured.return_value = True
        mock_svc.translate.return_value = "result"
        t.services["svc1"] = mock_svc

        progress_calls: list[tuple[int, int]] = []

        def cb(completed: int, total: int) -> None:
            progress_calls.append((completed, total))

        t.translate_parallel("hello", "en", "ru", ["svc1"], progress_callback=cb)
        assert len(progress_calls) > 0

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_translate_parallel_error_in_service(self, _: MagicMock) -> None:
        t = Translator(_make_settings())
        mock_svc = MagicMock()
        mock_svc.is_configured.return_value = True
        mock_svc.translate.side_effect = RuntimeError("API failure")
        t.services["bad_svc"] = mock_svc
        result = t.translate_parallel("hello", "en", "ru", ["bad_svc"])
        assert "[Error:" in result["bad_svc"]

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_translate_chunk_error_captured(self, _: MagicMock) -> None:
        t = Translator(_make_settings())
        mock_svc = MagicMock()
        mock_svc.is_configured.return_value = True
        mock_svc.translate.side_effect = RuntimeError("boom")
        t.services["bad"] = mock_svc
        result = t.translate_chunk("hello", "en", "ru", ["bad"])
        assert "[Error:" in result["bad"]


class TestTranslatorReload:
    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_reload_services(self, _: MagicMock) -> None:
        t = Translator(_make_settings())
        original_ids = set(t.services.keys())
        t.reload_services()
        assert set(t.services.keys()) == original_ids
