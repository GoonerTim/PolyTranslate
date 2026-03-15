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
    from app.config.schema import SettingsSchema

    data: dict[str, object] = {"api_keys": {}}
    data.update(overrides)
    s._schema = SettingsSchema.model_validate(data)
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


class TestChunkDeduplication:
    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_duplicate_chunks_translated_once(self, _: MagicMock) -> None:
        """Identical chunks should only call the service once."""
        t = Translator(_make_settings())
        mock_svc = MagicMock()
        mock_svc.is_configured.return_value = True
        mock_svc.translate.return_value = "translated"
        t.services["svc"] = mock_svc

        # Force split_text to return duplicates
        with patch.object(t, "split_text", return_value=["hello", "hello", "hello"]):
            result = t.translate_parallel("hello hello hello", "en", "ru", ["svc"])

        # Service should be called only once for the unique chunk
        assert mock_svc.translate.call_count == 1
        # Result should still have 3 chunks joined
        assert result["svc"] == "translated translated translated"

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_duplicate_chunks_sync_fallback(self, _: MagicMock) -> None:
        """Deduplication also works in sync fallback."""
        import asyncio

        t = Translator(_make_settings())
        mock_svc = MagicMock()
        mock_svc.is_configured.return_value = True
        mock_svc.translate.return_value = "result"
        t.services["svc"] = mock_svc

        with patch.object(t, "split_text", return_value=["a", "b", "a", "b", "a"]):

            async def run_inside_loop() -> dict[str, str]:
                return t.translate_parallel("a b a b a", "en", "ru", ["svc"])

            result = asyncio.run(run_inside_loop())

        # Only 2 unique chunks: "a" and "b"
        assert mock_svc.translate.call_count == 2
        assert result["svc"] == "result result result result result"

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_no_duplicates_all_translated(self, _: MagicMock) -> None:
        """When all chunks are unique, all are translated."""
        t = Translator(_make_settings())
        mock_svc = MagicMock()
        mock_svc.is_configured.return_value = True
        mock_svc.translate.side_effect = lambda text, *a: f"t_{text}"
        t.services["svc"] = mock_svc

        with patch.object(t, "split_text", return_value=["a", "b", "c"]):
            result = t.translate_parallel("a b c", "en", "ru", ["svc"])

        assert mock_svc.translate.call_count == 3
        assert result["svc"] == "t_a t_b t_c"

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_dedup_progress_reports_unique_count(self, _: MagicMock) -> None:
        """Progress callback total should reflect unique tasks, not original."""
        t = Translator(_make_settings())
        mock_svc = MagicMock()
        mock_svc.is_configured.return_value = True
        mock_svc.translate.return_value = "ok"
        t.services["svc"] = mock_svc

        progress_calls: list[tuple[int, int]] = []

        def cb(completed: int, total: int) -> None:
            progress_calls.append((completed, total))

        with patch.object(t, "split_text", return_value=["x", "x", "x"]):
            t.translate_parallel("x x x", "en", "ru", ["svc"], progress_callback=cb)

        # Only 1 unique chunk * 1 service = 1 total task
        assert all(total == 1 for _, total in progress_calls)


class TestStreamingTranslation:
    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_translate_stream_with_llm_service(self, _: MagicMock) -> None:
        """LLM service gets streaming callback when on_token provided."""
        from app.services.llm_base import LLMTranslationService

        t = Translator(_make_settings())
        mock_svc = MagicMock(spec=LLMTranslationService)
        mock_svc.is_configured.return_value = True
        mock_svc.supports_streaming.return_value = True
        mock_svc.translate_stream.return_value = "streamed result"
        t.services["llm_svc"] = mock_svc

        tokens: list[str] = []
        result = t.translate("hello", "en", "ru", "llm_svc", on_token=tokens.append)
        assert result == "streamed result"
        mock_svc.translate_stream.assert_called_once()

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_translate_stream_cache_hit_emits_full(self, _: MagicMock) -> None:
        """On cache hit, on_token receives the full cached result."""
        t = Translator(_make_settings())
        mock_svc = MagicMock()
        mock_svc.is_configured.return_value = True
        t.services["svc"] = mock_svc
        t.cache.put("hello", "en", "ru", "svc", "cached")

        tokens: list[str] = []
        result = t.translate("hello", "en", "ru", "svc", on_token=tokens.append)
        assert "cached" in result
        assert len(tokens) == 1
        mock_svc.translate.assert_not_called()

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_translate_stream_non_llm_emits_full(self, _: MagicMock) -> None:
        """Non-LLM service emits full result as single token."""
        t = Translator(_make_settings())
        mock_svc = MagicMock()  # not an LLMTranslationService
        mock_svc.is_configured.return_value = True
        mock_svc.translate.return_value = "full result"
        t.services["basic"] = mock_svc

        tokens: list[str] = []
        result = t.translate("hello", "en", "ru", "basic", on_token=tokens.append)
        assert result == "full result"
        assert tokens == ["full result"]

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_translate_no_callback_works(self, _: MagicMock) -> None:
        """Without on_token, translate works as before."""
        t = Translator(_make_settings())
        mock_svc = MagicMock()
        mock_svc.is_configured.return_value = True
        mock_svc.translate.return_value = "result"
        t.services["svc"] = mock_svc

        result = t.translate("hello", "en", "ru", "svc")
        assert result == "result"

    @patch("app.core.translator.discover_plugins", return_value=[])
    def test_translate_parallel_with_on_token(self, _: MagicMock) -> None:
        """translate_parallel passes per-service callbacks through."""
        from app.services.llm_base import LLMTranslationService

        t = Translator(_make_settings())
        mock_svc = MagicMock(spec=LLMTranslationService)
        mock_svc.is_configured.return_value = True
        mock_svc.supports_streaming.return_value = True
        mock_svc.translate_stream.return_value = "streamed"
        t.services["llm"] = mock_svc

        tokens: list[str] = []
        result = t.translate_parallel(
            "hello",
            "en",
            "ru",
            ["llm"],
            on_token={"llm": tokens.append},
        )
        assert "llm" in result
        mock_svc.translate_stream.assert_called_once()
