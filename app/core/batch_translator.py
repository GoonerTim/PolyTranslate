"""Batch folder translation for translating all files in a directory."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.file_processor import FileProcessor

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.core.translator import Translator


@dataclass
class BatchFileResult:
    source_path: Path
    output_path: Path | None = None
    success: bool = False
    error: str | None = None
    services_used: list[str] = field(default_factory=list)


@dataclass
class BatchProgress:
    current_file_index: int
    total_files: int
    current_file_name: str
    file_completed: bool = False


class BatchTranslator:
    def __init__(self, translator: Translator) -> None:
        self.translator = translator

    def find_files(
        self,
        directory: Path,
        extensions: set[str] | None = None,
        recursive: bool = True,
    ) -> list[Path]:
        if not directory.is_dir():
            return []

        if extensions is None:
            extensions = {".rpy"}

        normalized = {ext if ext.startswith(".") else f".{ext}" for ext in extensions}

        files: list[Path] = []
        pattern = "**/*" if recursive else "*"
        for path in directory.glob(pattern):
            if path.is_file() and path.suffix.lower() in normalized:
                files.append(path)

        return sorted(files)

    def translate_file(
        self,
        file_path: Path,
        source_lang: str,
        target_lang: str,
        services: list[str],
        output_dir: Path | None = None,
        service_name: str | None = None,
        source_dir: Path | None = None,
        chunk_size: int = 1000,
        max_workers: int = 3,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> BatchFileResult:
        result = BatchFileResult(source_path=file_path, services_used=services)

        try:
            text = FileProcessor.process_file(file_path)
            if not text.strip():
                result.success = True
                result.error = "Empty file, skipped"
                return result

            translations = self.translator.translate_parallel(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                services=services,
                chunk_size=chunk_size,
                max_workers=max_workers,
                progress_callback=progress_callback,
            )

            pick = service_name if service_name and service_name in translations else services[0]
            translated_text = translations[pick]

            if translated_text.startswith("[Error:"):
                result.error = translated_text
                return result

            # For .rpy files, reconstruct with original structure
            is_rpy = file_path.suffix.lower() == ".rpy"
            if is_rpy:
                translated_text = self._reconstruct_rpy(file_path, translated_text)

            # Determine output path
            output_path = self._get_output_path(file_path, target_lang, output_dir, source_dir)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(translated_text, encoding="utf-8")

            result.output_path = output_path
            result.success = True

        except Exception as e:
            result.error = str(e)

        return result

    def translate_folder(
        self,
        directory: Path,
        source_lang: str,
        target_lang: str,
        services: list[str],
        extensions: set[str] | None = None,
        output_dir: Path | None = None,
        service_name: str | None = None,
        chunk_size: int = 1000,
        max_workers: int = 3,
        recursive: bool = True,
        progress_callback: Callable[[BatchProgress], None] | None = None,
    ) -> list[BatchFileResult]:
        files = self.find_files(directory, extensions, recursive)
        if not files:
            return []

        results: list[BatchFileResult] = []

        for i, file_path in enumerate(files):
            if progress_callback:
                progress_callback(
                    BatchProgress(
                        current_file_index=i,
                        total_files=len(files),
                        current_file_name=file_path.name,
                    )
                )

            file_result = self.translate_file(
                file_path=file_path,
                source_lang=source_lang,
                target_lang=target_lang,
                services=services,
                output_dir=output_dir,
                service_name=service_name,
                source_dir=directory,
                chunk_size=chunk_size,
                max_workers=max_workers,
            )
            results.append(file_result)

            if progress_callback:
                progress_callback(
                    BatchProgress(
                        current_file_index=i,
                        total_files=len(files),
                        current_file_name=file_path.name,
                        file_completed=True,
                    )
                )

        return results

    def _reconstruct_rpy(self, file_path: Path, translated_text: str) -> str:
        raw = file_path.read_bytes()
        encoding = FileProcessor.detect_encoding(raw)
        original_content = raw.decode(encoding)

        translations_dict: dict[str, str] = {}
        for line in translated_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            match = re.match(
                r"^(DIALOGUE_LINE_\d+|TRANSLATABLE_STRING_\d+|"
                r"CHARACTER_DIALOGUE_\d+_\w+|MENU_OPTION_\d+):\s*(.+)$",
                line,
            )
            if match:
                key_prefix = match.group(1)
                translated_value = match.group(2)
                # Find original value for this key from the extracted text
                original_extracted = FileProcessor.read_rpy(raw)
                for orig_line in original_extracted.split("\n"):
                    if orig_line.startswith(key_prefix + ":"):
                        original_value = orig_line.split(": ", 1)[1] if ": " in orig_line else ""
                        full_key = f"{key_prefix}: {original_value}"
                        translations_dict[full_key] = translated_value
                        break

        return FileProcessor.reconstruct_rpy(original_content, translations_dict)

    def _get_output_path(
        self,
        file_path: Path,
        target_lang: str,
        output_dir: Path | None,
        source_dir: Path | None,
    ) -> Path:
        suffix = f"_{target_lang}{file_path.suffix}"
        new_name = file_path.stem + suffix

        if output_dir:
            if source_dir:
                try:
                    relative = file_path.relative_to(source_dir)
                    return output_dir / relative.parent / new_name
                except ValueError:
                    pass
            return output_dir / new_name

        return file_path.parent / new_name
