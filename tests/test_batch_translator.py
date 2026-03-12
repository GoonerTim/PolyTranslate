"""Tests for the batch folder translation module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core.batch_translator import BatchFileResult, BatchProgress, BatchTranslator


@pytest.fixture
def mock_translator():
    translator = MagicMock()
    translator.translate_parallel.return_value = {"deepl": "Translated text"}
    translator.get_available_services.return_value = ["deepl"]
    return translator


@pytest.fixture
def batch(mock_translator):
    return BatchTranslator(mock_translator)


class TestFindFiles:
    def test_find_rpy_files(self, batch, tmp_path):
        (tmp_path / "script.rpy").write_text("label start:", encoding="utf-8")
        (tmp_path / "other.txt").write_text("hello", encoding="utf-8")
        (tmp_path / "readme.md").write_text("# readme", encoding="utf-8")

        files = batch.find_files(tmp_path)
        assert len(files) == 1
        assert files[0].name == "script.rpy"

    def test_find_custom_extensions(self, batch, tmp_path):
        (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
        (tmp_path / "b.txt").write_text("world", encoding="utf-8")
        (tmp_path / "c.rpy").write_text("label start:", encoding="utf-8")

        files = batch.find_files(tmp_path, extensions={".txt"})
        assert len(files) == 2
        assert all(f.suffix == ".txt" for f in files)

    def test_find_files_recursive(self, batch, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.rpy").write_text("label a:", encoding="utf-8")
        (sub / "b.rpy").write_text("label b:", encoding="utf-8")

        files = batch.find_files(tmp_path, recursive=True)
        assert len(files) == 2

    def test_find_files_non_recursive(self, batch, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.rpy").write_text("label a:", encoding="utf-8")
        (sub / "b.rpy").write_text("label b:", encoding="utf-8")

        files = batch.find_files(tmp_path, recursive=False)
        assert len(files) == 1
        assert files[0].name == "a.rpy"

    def test_find_files_empty_dir(self, batch, tmp_path):
        files = batch.find_files(tmp_path)
        assert files == []

    def test_find_files_nonexistent(self, batch):
        files = batch.find_files(Path("/nonexistent/path"))
        assert files == []

    def test_extensions_without_dot(self, batch, tmp_path):
        (tmp_path / "test.txt").write_text("hello", encoding="utf-8")
        files = batch.find_files(tmp_path, extensions={"txt"})
        assert len(files) == 1


class TestTranslateFile:
    def test_translate_txt_file(self, batch, mock_translator, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello world", encoding="utf-8")

        result = batch.translate_file(
            file_path=f,
            source_lang="en",
            target_lang="ru",
            services=["deepl"],
        )

        assert result.success
        assert result.output_path is not None
        assert result.output_path.name == "test_ru.txt"
        assert result.output_path.exists()

    def test_translate_empty_file(self, batch, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")

        result = batch.translate_file(
            file_path=f,
            source_lang="en",
            target_lang="ru",
            services=["deepl"],
        )

        assert result.success
        assert result.error == "Empty file, skipped"
        assert result.output_path is None

    def test_translate_file_with_output_dir(self, batch, mock_translator, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        f = src / "test.txt"
        f.write_text("Hello", encoding="utf-8")

        result = batch.translate_file(
            file_path=f,
            source_lang="en",
            target_lang="ru",
            services=["deepl"],
            output_dir=out,
            source_dir=src,
        )

        assert result.success
        assert result.output_path is not None
        assert str(out) in str(result.output_path)

    def test_translate_file_preserves_subdirs(self, batch, mock_translator, tmp_path):
        src = tmp_path / "src"
        sub = src / "chapter1"
        sub.mkdir(parents=True)
        out = tmp_path / "out"

        f = sub / "script.txt"
        f.write_text("Hello", encoding="utf-8")

        result = batch.translate_file(
            file_path=f,
            source_lang="en",
            target_lang="ru",
            services=["deepl"],
            output_dir=out,
            source_dir=src,
        )

        assert result.success
        assert result.output_path is not None
        assert "chapter1" in str(result.output_path)

    def test_translate_file_error(self, batch, mock_translator, tmp_path):
        mock_translator.translate_parallel.side_effect = RuntimeError("API error")
        f = tmp_path / "test.txt"
        f.write_text("Hello", encoding="utf-8")

        result = batch.translate_file(
            file_path=f,
            source_lang="en",
            target_lang="ru",
            services=["deepl"],
        )

        assert not result.success
        assert "API error" in result.error

    def test_translate_file_service_error_in_result(self, batch, mock_translator, tmp_path):
        mock_translator.translate_parallel.return_value = {"deepl": "[Error: timeout]"}
        f = tmp_path / "test.txt"
        f.write_text("Hello", encoding="utf-8")

        result = batch.translate_file(
            file_path=f,
            source_lang="en",
            target_lang="ru",
            services=["deepl"],
        )

        assert not result.success
        assert "[Error:" in result.error

    def test_translate_file_specific_service(self, batch, mock_translator, tmp_path):
        mock_translator.translate_parallel.return_value = {
            "deepl": "DeepL result",
            "google": "Google result",
        }
        f = tmp_path / "test.txt"
        f.write_text("Hello", encoding="utf-8")

        result = batch.translate_file(
            file_path=f,
            source_lang="en",
            target_lang="ru",
            services=["deepl", "google"],
            service_name="google",
        )

        assert result.success
        content = result.output_path.read_text(encoding="utf-8")
        assert content == "Google result"


class TestTranslateFolder:
    def test_translate_multiple_files(self, batch, mock_translator, tmp_path):
        (tmp_path / "a.rpy").write_text('e "Hello"', encoding="utf-8")
        (tmp_path / "b.rpy").write_text('e "World"', encoding="utf-8")

        results = batch.translate_folder(
            directory=tmp_path,
            source_lang="en",
            target_lang="ru",
            services=["deepl"],
        )

        assert len(results) == 2
        assert all(r.success for r in results)

    def test_translate_folder_empty(self, batch, tmp_path):
        results = batch.translate_folder(
            directory=tmp_path,
            source_lang="en",
            target_lang="ru",
            services=["deepl"],
        )
        assert results == []

    def test_translate_folder_partial_failure(self, batch, mock_translator, tmp_path):
        (tmp_path / "good.rpy").write_text('e "Hello"', encoding="utf-8")
        (tmp_path / "bad.rpy").write_text('e "World"', encoding="utf-8")

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("Service unavailable")
            return {"deepl": "Translated"}

        mock_translator.translate_parallel.side_effect = side_effect

        results = batch.translate_folder(
            directory=tmp_path,
            source_lang="en",
            target_lang="ru",
            services=["deepl"],
        )

        assert len(results) == 2
        succeeded = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        assert len(succeeded) == 1
        assert len(failed) == 1

    def test_translate_folder_progress_callback(self, batch, mock_translator, tmp_path):
        (tmp_path / "a.rpy").write_text('e "Hello"', encoding="utf-8")
        (tmp_path / "b.rpy").write_text('e "World"', encoding="utf-8")

        progress_calls: list[BatchProgress] = []

        batch.translate_folder(
            directory=tmp_path,
            source_lang="en",
            target_lang="ru",
            services=["deepl"],
            progress_callback=lambda p: progress_calls.append(p),
        )

        # 2 files × 2 calls each (start + completed)
        assert len(progress_calls) == 4
        assert progress_calls[0].current_file_index == 0
        assert progress_calls[0].file_completed is False
        assert progress_calls[1].file_completed is True
        assert progress_calls[2].current_file_index == 1
        assert progress_calls[3].file_completed is True


class TestOutputNaming:
    def test_output_name_with_lang_suffix(self, batch, mock_translator, tmp_path):
        f = tmp_path / "script.rpy"
        f.write_text('e "Hello"', encoding="utf-8")

        result = batch.translate_file(
            file_path=f,
            source_lang="en",
            target_lang="ru",
            services=["deepl"],
        )

        assert result.output_path.name == "script_ru.rpy"

    def test_output_name_txt(self, batch, mock_translator, tmp_path):
        f = tmp_path / "readme.txt"
        f.write_text("Hello world", encoding="utf-8")

        result = batch.translate_file(
            file_path=f,
            source_lang="en",
            target_lang="de",
            services=["deepl"],
        )

        assert result.output_path.name == "readme_de.txt"


class TestBatchFileResult:
    def test_dataclass_defaults(self):
        r = BatchFileResult(source_path=Path("test.txt"))
        assert r.success is False
        assert r.output_path is None
        assert r.error is None
        assert r.services_used == []

    def test_dataclass_with_values(self):
        r = BatchFileResult(
            source_path=Path("test.txt"),
            output_path=Path("test_ru.txt"),
            success=True,
            services_used=["deepl"],
        )
        assert r.success
        assert r.output_path == Path("test_ru.txt")


class TestBatchProgress:
    def test_dataclass(self):
        p = BatchProgress(
            current_file_index=2,
            total_files=10,
            current_file_name="script.rpy",
        )
        assert p.current_file_index == 2
        assert p.total_files == 10
        assert p.file_completed is False
