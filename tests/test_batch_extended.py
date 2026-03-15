"""Extended tests for batch_translator module — covering uncovered lines."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from app.core.batch_translator import BatchFileResult, BatchProgress, BatchTranslator


class TestBatchTranslatorOutputPath:
    def test_output_path_with_output_dir_and_source_dir(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "game"
        src_dir.mkdir()
        sub = src_dir / "scripts"
        sub.mkdir()
        f = sub / "test.rpy"
        f.write_text("content", encoding="utf-8")

        out_dir = tmp_path / "output"
        out_dir.mkdir()

        bt = BatchTranslator(MagicMock())
        result = bt._get_output_path(f, "ru", out_dir, src_dir)
        assert result == out_dir / "scripts" / "test_ru.rpy"

    def test_output_path_relative_to_fails(self, tmp_path: Path) -> None:
        # When file is not relative to source_dir, falls back to output_dir / new_name
        f = Path("/some/other/path/test.rpy")
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        src_dir = tmp_path / "game"

        bt = BatchTranslator(MagicMock())
        result = bt._get_output_path(f, "ru", out_dir, src_dir)
        assert result == out_dir / "test_ru.rpy"

    def test_output_path_no_output_dir(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hi", encoding="utf-8")

        bt = BatchTranslator(MagicMock())
        result = bt._get_output_path(f, "de", None, None)
        assert result == tmp_path / "test_de.txt"


class TestBatchTranslateFile:
    def test_translate_file_empty(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")

        bt = BatchTranslator(MagicMock())
        result = bt.translate_file(f, "en", "ru", ["deepl"])
        assert result.success is True
        assert result.error == "Empty file, skipped"

    def test_translate_file_error_result(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")

        mock_translator = MagicMock()
        mock_translator.translate_parallel.return_value = {"deepl": "[Error: API failed]"}

        bt = BatchTranslator(mock_translator)
        result = bt.translate_file(f, "en", "ru", ["deepl"])
        assert result.success is False
        assert result.error == "[Error: API failed]"

    def test_translate_file_exception(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")

        mock_translator = MagicMock()
        mock_translator.translate_parallel.side_effect = RuntimeError("unexpected")

        bt = BatchTranslator(mock_translator)
        result = bt.translate_file(f, "en", "ru", ["deepl"])
        assert result.success is False
        assert "unexpected" in result.error

    def test_translate_file_success_txt(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")

        mock_translator = MagicMock()
        mock_translator.translate_parallel.return_value = {"deepl": "привет"}

        bt = BatchTranslator(mock_translator)
        result = bt.translate_file(f, "en", "ru", ["deepl"])
        assert result.success is True
        assert result.output_path is not None
        assert result.output_path.exists()
        assert result.output_path.read_text(encoding="utf-8") == "привет"

    def test_translate_file_picks_specified_service(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")

        mock_translator = MagicMock()
        mock_translator.translate_parallel.return_value = {
            "deepl": "via deepl",
            "google": "via google",
        }

        bt = BatchTranslator(mock_translator)
        result = bt.translate_file(f, "en", "ru", ["deepl", "google"], service_name="google")
        assert result.success is True
        content = result.output_path.read_text(encoding="utf-8")
        assert content == "via google"


class TestBatchTranslateFolder:
    def test_translate_folder_empty(self, tmp_path: Path) -> None:
        bt = BatchTranslator(MagicMock())
        results = bt.translate_folder(tmp_path, "en", "ru", ["deepl"])
        assert results == []

    def test_translate_folder_with_progress(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")

        mock_translator = MagicMock()
        mock_translator.translate_parallel.return_value = {"deepl": "привет"}

        progress_calls: list[BatchProgress] = []

        bt = BatchTranslator(mock_translator)
        results = bt.translate_folder(
            tmp_path,
            "en",
            "ru",
            ["deepl"],
            extensions={".txt"},
            progress_callback=progress_calls.append,
        )
        assert len(results) == 1
        # Should have two progress calls per file (start + complete)
        assert len(progress_calls) == 2
        assert progress_calls[0].file_completed is False
        assert progress_calls[1].file_completed is True


class TestBatchFileResultDefaults:
    def test_defaults(self) -> None:
        r = BatchFileResult(source_path=Path("test.txt"))
        assert r.success is False
        assert r.error is None
        assert r.output_path is None
        assert r.services_used == []
