"""Extended CLI tests for uncovered branches."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.cli import (
    _format_results,
    _get_text,
    _load_settings,
    _progress_callback,
    _resolve_params,
    _resolve_services,
    cmd_cache,
    cmd_config,
    cmd_detect,
    cmd_languages,
    run_cli,
)


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
        args = Namespace(file=str(f), input=None)
        assert _get_text(args) == "hello world"

    def test_get_text_file_not_found(self) -> None:
        args = Namespace(file="/nonexistent/file.txt", input=None)
        with pytest.raises(SystemExit):
            _get_text(args)

    def test_get_text_from_input(self) -> None:
        args = Namespace(file=None, input="direct text")
        assert _get_text(args) == "direct text"

    def test_get_text_no_input_no_stdin(self) -> None:
        args = Namespace(file=None, input=None)
        with patch.object(sys.stdin, "isatty", return_value=True), pytest.raises(SystemExit):
            _get_text(args)

    def test_get_text_from_stdin(self) -> None:
        args = Namespace(file=None, input=None)
        with (
            patch.object(sys.stdin, "isatty", return_value=False),
            patch.object(sys.stdin, "read", return_value="piped text\n"),
        ):
            assert _get_text(args) == "piped text"


class TestResolveParams:
    def test_uses_args_when_provided(self) -> None:
        args = Namespace(source="en", target="de", chunk_size=500, max_workers=5)
        settings = MagicMock()
        result = _resolve_params(args, settings)
        assert result == ("en", "de", 500, 5)

    def test_falls_back_to_settings(self) -> None:
        args = Namespace(source=None, target=None, chunk_size=None, max_workers=None)
        settings = MagicMock()
        settings.get_source_language.return_value = "auto"
        settings.get_target_language.return_value = "ru"
        settings.get_chunk_size.return_value = 1000
        settings.get_max_workers.return_value = 3
        source, target, chunk_size, max_workers = _resolve_params(args, settings)
        assert source == "auto"
        assert target == "ru"


class TestResolveServices:
    def test_all_services(self) -> None:
        args = Namespace(all_services=True, services=None)
        translator = MagicMock()
        translator.get_available_services.return_value = ["deepl", "google"]
        result = _resolve_services(args, translator, MagicMock())
        assert result == ["deepl", "google"]

    def test_specific_services(self) -> None:
        args = Namespace(all_services=False, services=["deepl"])
        translator = MagicMock()
        translator.get_available_services.return_value = ["deepl", "google"]
        result = _resolve_services(args, translator, MagicMock())
        assert result == ["deepl"]

    def test_invalid_service_exits(self) -> None:
        args = Namespace(all_services=False, services=["nonexistent"])
        translator = MagicMock()
        translator.get_available_services.return_value = ["deepl"]
        with pytest.raises(SystemExit):
            _resolve_services(args, translator, MagicMock())

    def test_no_available_services_exits(self) -> None:
        args = Namespace(all_services=False, services=None)
        translator = MagicMock()
        translator.get_available_services.return_value = []
        with pytest.raises(SystemExit):
            _resolve_services(args, translator, MagicMock())

    def test_default_from_settings(self) -> None:
        args = Namespace(all_services=False, services=None)
        translator = MagicMock()
        translator.get_available_services.return_value = ["deepl", "google"]
        settings = MagicMock()
        settings.get_selected_services.return_value = ["google"]
        result = _resolve_services(args, translator, settings)
        assert result == ["google"]

    def test_default_first_available(self) -> None:
        args = Namespace(all_services=False, services=None)
        translator = MagicMock()
        translator.get_available_services.return_value = ["deepl", "google"]
        settings = MagicMock()
        settings.get_selected_services.return_value = ["nonexistent"]
        result = _resolve_services(args, translator, settings)
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
    def test_cmd_languages_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        cmd_languages(Namespace())
        captured = capsys.readouterr()
        assert "en" in captured.out
        assert "English" in captured.out
        assert "auto" not in captured.out


class TestCmdDetect:
    @patch("app.core.language_detector.LanguageDetector.detect", return_value="en")
    def test_detect_success(self, _: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
        args = Namespace(file=None, input="Hello world")
        cmd_detect(args)
        captured = capsys.readouterr()
        assert "en" in captured.out

    @patch("app.core.language_detector.LanguageDetector.detect", return_value=None)
    def test_detect_failure(self, _: MagicMock) -> None:
        args = Namespace(file=None, input="x")
        with pytest.raises(SystemExit):
            cmd_detect(args)


class TestCmdCache:
    def test_cache_no_action(self) -> None:
        args = Namespace(cache_action=None, config=None)
        with pytest.raises(SystemExit):
            cmd_cache(args)

    @patch("app.utils.cache.TranslationCache.__len__", return_value=0)
    def test_cache_export_empty(self, _: MagicMock) -> None:
        args = Namespace(cache_action="export-tmx", output="out.tmx", config=None)
        with pytest.raises(SystemExit):
            cmd_cache(args)

    def test_cache_import_file_not_found(self) -> None:
        args = Namespace(cache_action="import-tmx", input="/nonexistent.tmx", config=None)
        with pytest.raises(SystemExit):
            cmd_cache(args)


class TestCmdConfig:
    def test_config_set_value(self) -> None:
        with patch("app.cli._load_settings") as mock_ls:
            mock_settings = MagicMock()
            mock_ls.return_value = mock_settings
            args = Namespace(set=["target_language", "de"], set_key=None, config=None)
            cmd_config(args)
            mock_settings.set.assert_called_once_with("target_language", "de")
            mock_settings.save.assert_called_once()

    def test_config_set_key(self) -> None:
        with patch("app.cli._load_settings") as mock_ls:
            mock_settings = MagicMock()
            mock_ls.return_value = mock_settings
            args = Namespace(set=None, set_key=["openai", "sk-test"], config=None)
            cmd_config(args)
            mock_settings.set_api_key.assert_called_once_with("openai", "sk-test")

    def test_config_show_default(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("app.cli._load_settings") as mock_ls:
            mock_settings = MagicMock()
            mock_settings.to_dict.return_value = {
                "api_keys": {"openai": "sk-1234567890"},
                "target": "ru",
            }
            mock_ls.return_value = mock_settings
            args = Namespace(set=None, set_key=None, config=None)
            cmd_config(args)
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert "sk-1...7890" in data["api_keys"]["openai"]


class TestRunCLI:
    def test_no_command_shows_help(self) -> None:
        with pytest.raises(SystemExit):
            run_cli([])

    def test_unknown_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Unknown commands fall through to print_help
        run_cli(["languages"])
        captured = capsys.readouterr()
        assert "en" in captured.out
