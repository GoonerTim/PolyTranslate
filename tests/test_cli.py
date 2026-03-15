"""Tests for the CLI module."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from app.cli import cli, run_cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestClickCommands:
    """Test that click commands parse arguments correctly."""

    def test_translate_command(self, runner: CliRunner) -> None:
        with patch("app.cli._load_settings") as mock_ls, patch("app.cli.Translator") as mock_t:
            mock_ls.return_value = MagicMock(
                get_source_language=MagicMock(return_value="en"),
                get_target_language=MagicMock(return_value="ru"),
                get_chunk_size=MagicMock(return_value=1000),
                get_max_workers=MagicMock(return_value=3),
                get_selected_services=MagicMock(return_value=["deepl"]),
            )
            mock_translator = MagicMock()
            mock_translator.get_available_services.return_value = ["deepl"]
            mock_translator.translate_parallel.return_value = {"deepl": "Привет"}
            mock_t.return_value = mock_translator

            result = runner.invoke(cli, ["translate", "Hello world", "-t", "ru"])
            assert result.exit_code == 0
            assert "Привет" in result.output

    def test_translate_alias(self, runner: CliRunner) -> None:
        """Aliases work via run_cli."""
        with patch("app.cli._load_settings") as mock_ls, patch("app.cli.Translator") as mock_t:
            mock_ls.return_value = MagicMock(
                get_source_language=MagicMock(return_value="en"),
                get_target_language=MagicMock(return_value="ru"),
                get_chunk_size=MagicMock(return_value=1000),
                get_max_workers=MagicMock(return_value=3),
                get_selected_services=MagicMock(return_value=["deepl"]),
            )
            mock_translator = MagicMock()
            mock_translator.get_available_services.return_value = ["deepl"]
            mock_translator.translate_parallel.return_value = {"deepl": "Привет"}
            mock_t.return_value = mock_translator

            # "t" alias resolved through run_cli
            result = runner.invoke(cli, ["translate", "Hello"])
            assert result.exit_code == 0

    def test_translate_with_file(self, runner: CliRunner, tmp_path) -> None:
        input_file = tmp_path / "test.txt"
        input_file.write_text("Hello world", encoding="utf-8")

        with patch("app.cli._load_settings") as mock_ls, patch("app.cli.Translator") as mock_t:
            mock_ls.return_value = MagicMock(
                get_source_language=MagicMock(return_value="en"),
                get_target_language=MagicMock(return_value="de"),
                get_chunk_size=MagicMock(return_value=1000),
                get_max_workers=MagicMock(return_value=3),
                get_selected_services=MagicMock(return_value=["deepl"]),
            )
            mock_translator = MagicMock()
            mock_translator.get_available_services.return_value = ["deepl"]
            mock_translator.translate_parallel.return_value = {"deepl": "Hallo"}
            mock_t.return_value = mock_translator

            result = runner.invoke(
                cli, ["translate", "--file", str(input_file), "-s", "en", "-t", "de"]
            )
            assert result.exit_code == 0

    def test_translate_all_services(self, runner: CliRunner) -> None:
        with patch("app.cli._load_settings") as mock_ls, patch("app.cli.Translator") as mock_t:
            mock_ls.return_value = MagicMock(
                get_source_language=MagicMock(return_value="en"),
                get_target_language=MagicMock(return_value="ru"),
                get_chunk_size=MagicMock(return_value=1000),
                get_max_workers=MagicMock(return_value=3),
            )
            mock_translator = MagicMock()
            mock_translator.get_available_services.return_value = ["deepl", "google"]
            mock_translator.translate_parallel.return_value = {
                "deepl": "Привет",
                "google": "Привет",
            }
            mock_t.return_value = mock_translator

            result = runner.invoke(cli, ["translate", "Hello", "--all-services"])
            assert result.exit_code == 0
            call_args = mock_translator.translate_parallel.call_args
            assert call_args.kwargs["services"] == ["deepl", "google"]

    def test_translate_specific_services(self, runner: CliRunner) -> None:
        with patch("app.cli._load_settings") as mock_ls, patch("app.cli.Translator") as mock_t:
            mock_ls.return_value = MagicMock(
                get_source_language=MagicMock(return_value="en"),
                get_target_language=MagicMock(return_value="ru"),
                get_chunk_size=MagicMock(return_value=1000),
                get_max_workers=MagicMock(return_value=3),
            )
            mock_translator = MagicMock()
            mock_translator.get_available_services.return_value = ["deepl", "google"]
            mock_translator.translate_parallel.return_value = {
                "deepl": "Привет",
                "google": "Здравствуйте",
            }
            mock_t.return_value = mock_translator

            result = runner.invoke(
                cli, ["translate", "Hello", "--services", "deepl", "--services", "google"]
            )
            assert result.exit_code == 0
            assert "DEEPL" in result.output
            assert "GOOGLE" in result.output

    def test_translate_json_format(self, runner: CliRunner) -> None:
        with patch("app.cli._load_settings") as mock_ls, patch("app.cli.Translator") as mock_t:
            mock_ls.return_value = MagicMock(
                get_source_language=MagicMock(return_value="en"),
                get_target_language=MagicMock(return_value="ru"),
                get_chunk_size=MagicMock(return_value=1000),
                get_max_workers=MagicMock(return_value=3),
                get_selected_services=MagicMock(return_value=["deepl"]),
            )
            mock_translator = MagicMock()
            mock_translator.get_available_services.return_value = ["deepl"]
            mock_translator.translate_parallel.return_value = {"deepl": "Привет"}
            mock_t.return_value = mock_translator

            result = runner.invoke(cli, ["translate", "Hello", "--format", "json"])
            assert result.exit_code == 0
            parsed = json.loads(result.output)
            assert parsed["deepl"] == "Привет"

    def test_translate_output_file(self, runner: CliRunner, tmp_path) -> None:
        out_file = tmp_path / "output.txt"
        with patch("app.cli._load_settings") as mock_ls, patch("app.cli.Translator") as mock_t:
            mock_ls.return_value = MagicMock(
                get_source_language=MagicMock(return_value="en"),
                get_target_language=MagicMock(return_value="ru"),
                get_chunk_size=MagicMock(return_value=1000),
                get_max_workers=MagicMock(return_value=3),
                get_selected_services=MagicMock(return_value=["deepl"]),
            )
            mock_translator = MagicMock()
            mock_translator.get_available_services.return_value = ["deepl"]
            mock_translator.translate_parallel.return_value = {"deepl": "Привет"}
            mock_t.return_value = mock_translator

            result = runner.invoke(cli, ["translate", "Hello", "-o", str(out_file)])
            assert result.exit_code == 0
            assert out_file.read_text(encoding="utf-8") == "Привет"

    def test_services_command(self, runner: CliRunner) -> None:
        with patch("app.cli._load_settings") as mock_ls, patch("app.cli.Translator") as mock_t:
            mock_ls.return_value = MagicMock(
                get_selected_services=MagicMock(return_value=["deepl"]),
            )
            mock_svc = MagicMock()
            mock_svc.get_name.return_value = "DeepL"
            mock_translator = MagicMock()
            mock_translator.services = {"deepl": mock_svc}
            mock_translator.get_available_services.return_value = ["deepl"]
            mock_t.return_value = mock_translator

            result = runner.invoke(cli, ["services"])
            assert result.exit_code == 0
            assert "deepl" in result.output
            assert "DeepL" in result.output

    def test_languages_command(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["languages"])
        assert result.exit_code == 0
        assert "English" in result.output
        assert "Russian" in result.output

    def test_detect_command(self, runner: CliRunner) -> None:
        with patch("app.core.language_detector.LanguageDetector.detect", return_value="en"):
            result = runner.invoke(cli, ["detect", "Hello world"])
            assert result.exit_code == 0
            assert "en" in result.output
            assert "English" in result.output

    def test_detect_failure(self, runner: CliRunner) -> None:
        with patch("app.core.language_detector.LanguageDetector.detect", return_value=None):
            result = runner.invoke(cli, ["detect", "???"])
            assert result.exit_code == 1

    def test_config_show(self, runner: CliRunner) -> None:
        with patch("app.cli._load_settings") as mock_ls:
            settings = MagicMock()
            settings.to_dict.return_value = {
                "api_keys": {"openai": "sk-1234567890abcdef", "deepl": ""},
                "chunk_size": 1000,
            }
            mock_ls.return_value = settings

            result = runner.invoke(cli, ["config"])
            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["api_keys"]["openai"] == "sk-1...cdef"
            assert output["api_keys"]["deepl"] == "(not set)"

    def test_config_set(self, runner: CliRunner) -> None:
        with patch("app.cli._load_settings") as mock_ls:
            settings = MagicMock()
            mock_ls.return_value = settings

            result = runner.invoke(cli, ["config", "--set", "chunk_size", "2000"])
            assert result.exit_code == 0
            settings.set.assert_called_once_with("chunk_size", 2000)
            settings.save.assert_called_once()

    def test_config_set_key(self, runner: CliRunner) -> None:
        with patch("app.cli._load_settings") as mock_ls:
            settings = MagicMock()
            mock_ls.return_value = settings

            result = runner.invoke(cli, ["config", "--set-key", "openai", "sk-test123"])
            assert result.exit_code == 0
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

        run_cli(["translate", "Hello", "--services", "deepl", "--services", "google"])
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


class TestCmdTranslateDirectory:
    @patch("app.cli.BatchTranslator")
    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_translate_directory(
        self, mock_settings, mock_translator_cls, mock_batch_cls, tmp_path, capsys
    ):
        # Create test files
        (tmp_path / "test.rpy").write_text('e "Hello"', encoding="utf-8")

        settings = MagicMock()
        settings.get_source_language.return_value = "en"
        settings.get_target_language.return_value = "ru"
        settings.get_chunk_size.return_value = 1000
        settings.get_max_workers.return_value = 3
        settings.get_selected_services.return_value = ["deepl"]
        mock_settings.return_value = settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl"]
        mock_translator_cls.return_value = mock_translator

        from app.core.batch_translator import BatchFileResult

        mock_batch = MagicMock()
        mock_batch.find_files.return_value = [tmp_path / "test.rpy"]
        mock_batch.translate_folder.return_value = [
            BatchFileResult(
                source_path=tmp_path / "test.rpy",
                output_path=tmp_path / "test_ru.rpy",
                success=True,
                services_used=["deepl"],
            )
        ]
        mock_batch_cls.return_value = mock_batch

        run_cli(["translate", "-d", str(tmp_path), "-t", "ru"])
        captured = capsys.readouterr()
        assert "test_ru.rpy" in captured.out

    def test_directory_not_found(self):
        with pytest.raises(SystemExit) as exc_info:
            run_cli(["translate", "-d", "/nonexistent/folder/xyz"])
        assert exc_info.value.code == 1

    @patch("app.cli.BatchTranslator")
    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_translate_directory_no_files(
        self, mock_settings, mock_translator_cls, mock_batch_cls, tmp_path
    ):
        settings = MagicMock()
        settings.get_source_language.return_value = "en"
        settings.get_target_language.return_value = "ru"
        settings.get_chunk_size.return_value = 1000
        settings.get_max_workers.return_value = 3
        settings.get_selected_services.return_value = ["deepl"]
        mock_settings.return_value = settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl"]
        mock_translator_cls.return_value = mock_translator

        mock_batch = MagicMock()
        mock_batch.find_files.return_value = []
        mock_batch_cls.return_value = mock_batch

        with pytest.raises(SystemExit) as exc_info:
            run_cli(["translate", "-d", str(tmp_path)])
        assert exc_info.value.code == 1

    @patch("app.cli.BatchTranslator")
    @patch("app.cli.Translator")
    @patch("app.cli._load_settings")
    def test_translate_directory_json_output(
        self, mock_settings, mock_translator_cls, mock_batch_cls, tmp_path, capsys
    ):
        (tmp_path / "a.rpy").write_text('e "Hi"', encoding="utf-8")

        settings = MagicMock()
        settings.get_source_language.return_value = "en"
        settings.get_target_language.return_value = "ru"
        settings.get_chunk_size.return_value = 1000
        settings.get_max_workers.return_value = 3
        settings.get_selected_services.return_value = ["deepl"]
        mock_settings.return_value = settings

        mock_translator = MagicMock()
        mock_translator.get_available_services.return_value = ["deepl"]
        mock_translator_cls.return_value = mock_translator

        from app.core.batch_translator import BatchFileResult

        mock_batch = MagicMock()
        mock_batch.find_files.return_value = [tmp_path / "a.rpy"]
        mock_batch.translate_folder.return_value = [
            BatchFileResult(
                source_path=tmp_path / "a.rpy",
                output_path=tmp_path / "a_ru.rpy",
                success=True,
                services_used=["deepl"],
            )
        ]
        mock_batch_cls.return_value = mock_batch

        run_cli(["translate", "-d", str(tmp_path), "-t", "ru", "--format", "json"])
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert len(result) == 1
        assert result[0]["success"] is True


class TestNoCommand:
    def test_no_command_shows_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            run_cli([])
        assert exc_info.value.code == 0
