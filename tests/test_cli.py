"""Tests for the CLI module."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.cli import create_parser, run_cli


class TestCreateParser:
    def test_parser_created(self):
        parser = create_parser()
        assert parser is not None

    def test_translate_command(self):
        parser = create_parser()
        args = parser.parse_args(["translate", "Hello world", "-t", "ru"])
        assert args.command == "translate"
        assert args.input == "Hello world"
        assert args.target == "ru"

    def test_translate_alias(self):
        parser = create_parser()
        args = parser.parse_args(["t", "Hello"])
        assert args.command == "t"

    def test_translate_with_file(self):
        parser = create_parser()
        args = parser.parse_args(["translate", "--file", "test.txt", "-s", "en", "-t", "de"])
        assert args.file == "test.txt"
        assert args.source == "en"
        assert args.target == "de"

    def test_translate_all_services(self):
        parser = create_parser()
        args = parser.parse_args(["translate", "Hello", "--all-services"])
        assert args.all_services is True

    def test_translate_specific_services(self):
        parser = create_parser()
        args = parser.parse_args(["translate", "Hello", "--services", "deepl", "google"])
        assert args.services == ["deepl", "google"]

    def test_translate_json_format(self):
        parser = create_parser()
        args = parser.parse_args(["translate", "Hello", "--format", "json"])
        assert args.format == "json"

    def test_translate_output_file(self):
        parser = create_parser()
        args = parser.parse_args(["translate", "Hello", "-o", "out.txt"])
        assert args.output == "out.txt"

    def test_services_command(self):
        parser = create_parser()
        args = parser.parse_args(["services"])
        assert args.command == "services"

    def test_languages_command(self):
        parser = create_parser()
        args = parser.parse_args(["languages"])
        assert args.command == "languages"

    def test_detect_command(self):
        parser = create_parser()
        args = parser.parse_args(["detect", "Hello world"])
        assert args.command == "detect"
        assert args.input == "Hello world"

    def test_config_command_show(self):
        parser = create_parser()
        args = parser.parse_args(["config", "--show"])
        assert args.command == "config"
        assert args.show is True

    def test_config_set(self):
        parser = create_parser()
        args = parser.parse_args(["config", "--set", "chunk_size", "2000"])
        assert args.set == ["chunk_size", "2000"]

    def test_config_set_key(self):
        parser = create_parser()
        args = parser.parse_args(["config", "--set-key", "openai", "sk-test"])
        assert args.set_key == ["openai", "sk-test"]


class TestCmdLanguages:
    def test_list_languages(self, capsys):
        run_cli(["languages"])
        captured = capsys.readouterr()
        assert "English" in captured.out
        assert "Russian" in captured.out
        assert "auto" not in captured.out


class TestCmdServices:
    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_list_services(self, mock_settings, mock_translator_cls, capsys):
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.get_selected_services.return_value = ["deepl"]

        mock_svc = MagicMock()
        mock_svc.get_name.return_value = "DeepL"
        mock_translator = MagicMock()
        mock_translator.services = {"deepl": mock_svc}
        mock_translator.get_available_services.return_value = ["deepl"]
        mock_translator_cls.return_value = mock_translator

        run_cli(["services"])
        captured = capsys.readouterr()
        assert "deepl" in captured.out
        assert "DeepL" in captured.out


class TestCmdDetect:
    @patch("app.core.language_detector.LanguageDetector")
    def test_detect_language(self, mock_detector_cls, capsys):
        mock_detector = MagicMock()
        mock_detector.detect.return_value = "en"
        mock_detector_cls.return_value = mock_detector

        run_cli(["detect", "Hello world"])
        captured = capsys.readouterr()
        assert "en" in captured.out
        assert "English" in captured.out

    @patch("app.core.language_detector.LanguageDetector")
    def test_detect_failure(self, mock_detector_cls):
        mock_detector = MagicMock()
        mock_detector.detect.return_value = None
        mock_detector_cls.return_value = mock_detector

        with pytest.raises(SystemExit) as exc_info:
            run_cli(["detect", "???"])
        assert exc_info.value.code == 1


class TestCmdConfig:
    @patch("app.cli._load_settings")
    def test_show_config(self, mock_settings, capsys):
        settings = MagicMock()
        settings.to_dict.return_value = {
            "api_keys": {"openai": "sk-1234567890abcdef", "deepl": ""},
            "chunk_size": 1000,
        }
        mock_settings.return_value = settings

        run_cli(["config"])
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["api_keys"]["openai"] == "sk-1...cdef"
        assert output["api_keys"]["deepl"] == "(not set)"

    @patch("app.cli._load_settings")
    def test_set_config(self, mock_settings, capsys):
        settings = MagicMock()
        mock_settings.return_value = settings

        run_cli(["config", "--set", "chunk_size", "2000"])
        settings.set.assert_called_once_with("chunk_size", 2000)
        settings.save.assert_called_once()

    @patch("app.cli._load_settings")
    def test_set_api_key(self, mock_settings, capsys):
        settings = MagicMock()
        mock_settings.return_value = settings

        run_cli(["config", "--set-key", "openai", "sk-test123"])
        settings.set_api_key.assert_called_once_with("openai", "sk-test123")
        settings.save.assert_called_once()


class TestCmdTranslate:
    @patch("app.cli._progress_callback")
    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_translate_text(self, mock_settings, mock_translator_cls, mock_progress, capsys):
        settings = MagicMock()
        settings.get_source_language.return_value = "en"
        settings.get_target_language.return_value = "ru"
        settings.get_chunk_size.return_value = 1000
        settings.get_max_workers.return_value = 3
        settings.get_selected_services.return_value = ["deepl"]
        mock_settings.return_value = settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl", "google"]
        mock_translator.translate_parallel.return_value = {"deepl": "Привет мир"}
        mock_translator_cls.return_value = mock_translator

        run_cli(["translate", "Hello world", "-t", "ru"])
        captured = capsys.readouterr()
        assert "Привет мир" in captured.out

    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_translate_multiple_services(self, mock_settings, mock_translator_cls, capsys):
        settings = MagicMock()
        settings.get_source_language.return_value = "en"
        settings.get_target_language.return_value = "ru"
        settings.get_chunk_size.return_value = 1000
        settings.get_max_workers.return_value = 3
        settings.get_selected_services.return_value = ["deepl"]
        mock_settings.return_value = settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl", "google"]
        mock_translator.translate_parallel.return_value = {
            "deepl": "Привет",
            "google": "Здравствуйте",
        }
        mock_translator_cls.return_value = mock_translator

        run_cli(["translate", "Hello", "--services", "deepl", "google"])
        captured = capsys.readouterr()
        assert "DEEPL" in captured.out
        assert "GOOGLE" in captured.out

    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_translate_json_output(self, mock_settings, mock_translator_cls, capsys):
        settings = MagicMock()
        settings.get_source_language.return_value = "en"
        settings.get_target_language.return_value = "ru"
        settings.get_chunk_size.return_value = 1000
        settings.get_max_workers.return_value = 3
        settings.get_selected_services.return_value = ["deepl"]
        mock_settings.return_value = settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl"]
        mock_translator.translate_parallel.return_value = {"deepl": "Привет"}
        mock_translator_cls.return_value = mock_translator

        run_cli(["translate", "Hello", "--format", "json"])
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["deepl"] == "Привет"

    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_translate_to_file(self, mock_settings, mock_translator_cls, tmp_path):
        settings = MagicMock()
        settings.get_source_language.return_value = "en"
        settings.get_target_language.return_value = "ru"
        settings.get_chunk_size.return_value = 1000
        settings.get_max_workers.return_value = 3
        settings.get_selected_services.return_value = ["deepl"]
        mock_settings.return_value = settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl"]
        mock_translator.translate_parallel.return_value = {"deepl": "Привет"}
        mock_translator_cls.return_value = mock_translator

        out_file = tmp_path / "output.txt"
        run_cli(["translate", "Hello", "-o", str(out_file)])
        assert out_file.read_text(encoding="utf-8") == "Привет"

    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_translate_no_services_error(self, mock_settings, mock_translator_cls):
        settings = MagicMock()
        mock_settings.return_value = settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = []
        mock_translator_cls.return_value = mock_translator

        with pytest.raises(SystemExit) as exc_info:
            run_cli(["translate", "Hello"])
        assert exc_info.value.code == 1

    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_translate_invalid_service(self, mock_settings, mock_translator_cls):
        settings = MagicMock()
        mock_settings.return_value = settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl"]
        mock_translator_cls.return_value = mock_translator

        with pytest.raises(SystemExit) as exc_info:
            run_cli(["translate", "Hello", "--services", "nonexistent"])
        assert exc_info.value.code == 1

    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_translate_from_file(self, mock_settings, mock_translator_cls, tmp_path, capsys):
        settings = MagicMock()
        settings.get_source_language.return_value = "en"
        settings.get_target_language.return_value = "ru"
        settings.get_chunk_size.return_value = 1000
        settings.get_max_workers.return_value = 3
        settings.get_selected_services.return_value = ["deepl"]
        mock_settings.return_value = settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl"]
        mock_translator.translate_parallel.return_value = {"deepl": "Привет"}
        mock_translator_cls.return_value = mock_translator

        input_file = tmp_path / "input.txt"
        input_file.write_text("Hello world", encoding="utf-8")

        run_cli(["translate", "--file", str(input_file)])
        captured = capsys.readouterr()
        assert "Привет" in captured.out

    def test_translate_file_not_found(self):
        with pytest.raises(SystemExit) as exc_info:
            run_cli(["translate", "--file", "/nonexistent/file.txt"])
        assert exc_info.value.code == 1

    def test_translate_no_input(self):
        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = True
        with patch("sys.stdin", mock_stdin):
            with pytest.raises(SystemExit) as exc_info:
                run_cli(["translate"])
            assert exc_info.value.code == 1

    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_translate_auto_detect(self, mock_settings, mock_translator_cls, capsys):
        settings = MagicMock()
        settings.get_source_language.return_value = "auto"
        settings.get_target_language.return_value = "ru"
        settings.get_chunk_size.return_value = 1000
        settings.get_max_workers.return_value = 3
        settings.get_selected_services.return_value = ["deepl"]
        mock_settings.return_value = settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl"]
        mock_translator.detect_language.return_value = "en"
        mock_translator.translate_parallel.return_value = {"deepl": "Привет"}
        mock_translator_cls.return_value = mock_translator

        run_cli(["translate", "Hello world"])
        captured = capsys.readouterr()
        assert "Detected language" in captured.err

    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_translate_all_services_flag(self, mock_settings, mock_translator_cls, capsys):
        settings = MagicMock()
        settings.get_source_language.return_value = "en"
        settings.get_target_language.return_value = "ru"
        settings.get_chunk_size.return_value = 1000
        settings.get_max_workers.return_value = 3
        mock_settings.return_value = settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl", "google"]
        mock_translator.translate_parallel.return_value = {
            "deepl": "Привет",
            "google": "Привет",
        }
        mock_translator_cls.return_value = mock_translator

        run_cli(["translate", "Hello", "--all-services"])
        mock_translator.translate_parallel.assert_called_once()
        call_args = mock_translator.translate_parallel.call_args
        assert call_args.kwargs["services"] == ["deepl", "google"]


class TestNoCommand:
    def test_no_command_shows_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            run_cli([])
        assert exc_info.value.code == 0
