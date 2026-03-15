"""Extended CLI tests for uncovered branches."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from app.cli import (
    _format_results,
    _get_text,
    _load_settings,
    _progress_callback,
    _resolve_params,
    _resolve_services,
    cli,
    run_cli,
)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestLoadSettings:
    def test_load_settings_default(self) -> None:
        settings = _load_settings(None)
        assert settings is not None

    def test_load_settings_custom_path(self, tmp_path: Path) -> None:
        cfg = tmp_path / "custom.json"
        cfg.write_text("{}", encoding="utf-8")
        settings = _load_settings(str(cfg))
        assert settings is not None


class TestGetText:
    def test_get_text_from_file(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        assert _get_text(None, str(f)) == "hello world"

    def test_get_text_file_not_found(self) -> None:
        with pytest.raises(SystemExit):
            _get_text(None, "/nonexistent/file.txt")

    def test_get_text_from_input(self) -> None:
        assert _get_text("direct text", None) == "direct text"

    def test_get_text_no_input_no_stdin(self) -> None:
        with patch.object(sys.stdin, "isatty", return_value=True), pytest.raises(SystemExit):
            _get_text(None, None)

    def test_get_text_from_stdin(self) -> None:
        with (
            patch.object(sys.stdin, "isatty", return_value=False),
            patch.object(sys.stdin, "read", return_value="piped text\n"),
        ):
            assert _get_text(None, None) == "piped text"


class TestResolveParams:
    def test_uses_args_when_provided(self) -> None:
        settings = MagicMock()
        result = _resolve_params("en", "de", 500, 5, settings)
        assert result == ("en", "de", 500, 5)

    def test_falls_back_to_settings(self) -> None:
        settings = MagicMock()
        settings.get_source_language.return_value = "auto"
        settings.get_target_language.return_value = "ru"
        settings.get_chunk_size.return_value = 1000
        settings.get_max_workers.return_value = 3
        source, target, chunk_size, max_workers = _resolve_params(None, None, None, None, settings)
        assert source == "auto"
        assert target == "ru"


class TestResolveServices:
    def test_all_services(self) -> None:
        translator = MagicMock()
        translator.get_available_services.return_value = ["deepl", "google"]
        result = _resolve_services(True, None, translator, MagicMock())
        assert result == ["deepl", "google"]

    def test_specific_services(self) -> None:
        translator = MagicMock()
        translator.get_available_services.return_value = ["deepl", "google"]
        result = _resolve_services(False, ("deepl",), translator, MagicMock())
        assert result == ["deepl"]

    def test_invalid_service_exits(self) -> None:
        translator = MagicMock()
        translator.get_available_services.return_value = ["deepl"]
        with pytest.raises(SystemExit):
            _resolve_services(False, ("nonexistent",), translator, MagicMock())

    def test_no_available_services_exits(self) -> None:
        translator = MagicMock()
        translator.get_available_services.return_value = []
        with pytest.raises(SystemExit):
            _resolve_services(False, None, translator, MagicMock())

    def test_default_from_settings(self) -> None:
        translator = MagicMock()
        translator.get_available_services.return_value = ["deepl", "google"]
        settings = MagicMock()
        settings.get_selected_services.return_value = ["google"]
        result = _resolve_services(False, None, translator, settings)
        assert result == ["google"]

    def test_default_first_available(self) -> None:
        translator = MagicMock()
        translator.get_available_services.return_value = ["deepl", "google"]
        settings = MagicMock()
        settings.get_selected_services.return_value = ["nonexistent"]
        result = _resolve_services(False, None, translator, settings)
        assert result == ["deepl"]


class TestFormatResults:
    def test_json_format(self) -> None:
        result = _format_results({"svc": "hello"}, "json")
        parsed = json.loads(result)
        assert parsed["svc"] == "hello"

    def test_text_single_service(self) -> None:
        result = _format_results({"svc": "hello"}, "text")
        assert result == "hello"

    def test_text_multiple_services(self) -> None:
        result = _format_results({"svc1": "a", "svc2": "b"}, "text")
        assert "=== SVC1 ===" in result
        assert "=== SVC2 ===" in result


class TestProgressCallback:
    def test_progress_mid(self, capsys: pytest.CaptureFixture[str]) -> None:
        _progress_callback(5, 10)
        # Output goes to stderr
        captured = capsys.readouterr()
        assert captured.err  # something written to stderr

    def test_progress_complete(self, capsys: pytest.CaptureFixture[str]) -> None:
        _progress_callback(10, 10)
        captured = capsys.readouterr()
        assert "100%" in captured.err


class TestCmdLanguages:
    def test_cmd_languages_output(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["languages"])
        assert result.exit_code == 0
        assert "en" in result.output
        assert "English" in result.output
        assert "auto" not in result.output


class TestCmdDetect:
    def test_detect_success(self, runner: CliRunner) -> None:
        with patch("app.core.language_detector.LanguageDetector.detect", return_value="en"):
            result = runner.invoke(cli, ["detect", "Hello world"])
            assert result.exit_code == 0
            assert "en" in result.output

    def test_detect_failure(self, runner: CliRunner) -> None:
        with patch("app.core.language_detector.LanguageDetector.detect", return_value=None):
            result = runner.invoke(cli, ["detect", "x"])
            assert result.exit_code == 1


class TestCmdCache:
    def test_cache_no_action(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["cache"])
        # Click shows usage error when no subcommand given
        assert result.exit_code in (0, 2)

    @patch("app.utils.cache.TranslationCache.__len__", return_value=0)
    def test_cache_export_empty(self, _: MagicMock, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["cache", "export-tmx", "out.tmx"])
        assert result.exit_code == 1

    def test_cache_import_file_not_found(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["cache", "import-tmx", "/nonexistent.tmx"])
        assert result.exit_code == 1


class TestCmdConfig:
    def test_config_set_value(self, runner: CliRunner) -> None:
        with patch("app.cli._load_settings") as mock_ls:
            mock_settings = MagicMock()
            mock_ls.return_value = mock_settings
            result = runner.invoke(cli, ["config", "--set", "target_language", "de"])
            assert result.exit_code == 0
            mock_settings.set.assert_called_once_with("target_language", "de")
            mock_settings.save.assert_called_once()

    def test_config_set_key(self, runner: CliRunner) -> None:
        with patch("app.cli._load_settings") as mock_ls:
            mock_settings = MagicMock()
            mock_ls.return_value = mock_settings
            result = runner.invoke(cli, ["config", "--set-key", "openai", "sk-test"])
            assert result.exit_code == 0
            mock_settings.set_api_key.assert_called_once_with("openai", "sk-test")

    def test_config_show_default(self, runner: CliRunner) -> None:
        with patch("app.cli._load_settings") as mock_ls:
            mock_settings = MagicMock()
            mock_settings.to_dict.return_value = {
                "api_keys": {"openai": "sk-1234567890"},
                "target": "ru",
            }
            mock_ls.return_value = mock_settings
            result = runner.invoke(cli, ["config"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "sk-1...7890" in data["api_keys"]["openai"]


class TestStreamFlag:
    @patch("app.cli._load_settings")
    @patch("app.cli.Translator")
    def test_stream_single_service(
        self, mock_trans_cls: MagicMock, mock_ls: MagicMock, runner: CliRunner
    ) -> None:
        mock_settings = MagicMock()
        mock_settings.get_source_language.return_value = "en"
        mock_settings.get_target_language.return_value = "ru"
        mock_settings.get_chunk_size.return_value = 1000
        mock_settings.get_max_workers.return_value = 3
        mock_settings.get_selected_services.return_value = ["deepl"]
        mock_ls.return_value = mock_settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl"]
        mock_translator.translate_parallel.return_value = {"deepl": "Привет"}
        mock_trans_cls.return_value = mock_translator

        result = runner.invoke(cli, ["translate", "Hello", "-t", "ru", "--stream"])
        assert result.exit_code == 0
        # on_token should be passed to translate_parallel
        call_kwargs = mock_translator.translate_parallel.call_args[1]
        assert call_kwargs["on_token"] is not None
        assert "deepl" in call_kwargs["on_token"]
        # progress_callback should be None in streaming mode
        assert call_kwargs["progress_callback"] is None

    @patch("app.cli._load_settings")
    @patch("app.cli.Translator")
    def test_stream_multi_service_warns(
        self, mock_trans_cls: MagicMock, mock_ls: MagicMock, runner: CliRunner
    ) -> None:
        mock_settings = MagicMock()
        mock_settings.get_source_language.return_value = "en"
        mock_settings.get_target_language.return_value = "ru"
        mock_settings.get_chunk_size.return_value = 1000
        mock_settings.get_max_workers.return_value = 3
        mock_ls.return_value = mock_settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl", "google"]
        mock_translator.translate_parallel.return_value = {"deepl": "a", "google": "b"}
        mock_trans_cls.return_value = mock_translator

        result = runner.invoke(
            cli, ["translate", "Hello", "-t", "ru", "--stream", "--all-services"]
        )
        assert result.exit_code == 0


class TestRunCLI:
    def test_no_command_shows_help(self) -> None:
        with pytest.raises(SystemExit):
            run_cli([])

    def test_alias_resolution(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Alias 'l' should resolve to 'languages'."""
        run_cli(["l"])
        captured = capsys.readouterr()
        assert "en" in captured.out
