"""Subtitle file processors (SRT, ASS/SSA)."""

from __future__ import annotations

import re

from app.core.file_processor import FileProcessor


class SubtitleProcessor:
    """Handles reading and reconstruction of subtitle formats."""

    @staticmethod
    def read_srt(file_content: bytes) -> str:
        try:
            encoding = FileProcessor.detect_encoding(file_content)
            srt_content = file_content.decode(encoding)

            extracted_text: list[str] = []
            blocks = re.split(r"\n\s*\n", srt_content.strip())

            for block in blocks:
                lines = block.strip().split("\n")
                if len(lines) < 3:
                    continue

                try:
                    index = int(lines[0].strip())
                except ValueError:
                    continue

                timecode = lines[1].strip()
                if "-->" not in timecode:
                    continue

                text = "\n".join(lines[2:])
                if text.strip():
                    extracted_text.append(f"SRT_{index}: {text}")

            if not extracted_text:
                return srt_content

            return "\n".join(extracted_text)
        except Exception as e:
            raise ValueError(f"SRT reading error: {e}") from e

    @staticmethod
    def reconstruct_srt(original_content: str, translations: dict[str, str]) -> str:
        try:
            blocks = re.split(r"\n\s*\n", original_content.strip())
            result_blocks: list[str] = []

            for block in blocks:
                lines = block.strip().split("\n")
                if len(lines) < 3:
                    result_blocks.append(block)
                    continue

                try:
                    index = int(lines[0].strip())
                except ValueError:
                    result_blocks.append(block)
                    continue

                timecode = lines[1].strip()
                if "-->" not in timecode:
                    result_blocks.append(block)
                    continue

                text = "\n".join(lines[2:])
                key = f"SRT_{index}: {text}"
                translated = translations.get(key, text)

                result_blocks.append(f"{index}\n{timecode}\n{translated}")

            return "\n\n".join(result_blocks) + "\n"
        except Exception as e:
            raise ValueError(f"SRT reconstruction error: {e}") from e

    @staticmethod
    def read_ass(file_content: bytes) -> str:
        try:
            encoding = FileProcessor.detect_encoding(file_content)
            ass_content = file_content.decode(encoding)

            extracted_text: list[str] = []
            in_events = False
            format_fields: list[str] = []
            dialogue_idx = 0

            for line in ass_content.split("\n"):
                line = line.rstrip()

                if line.strip().lower() == "[events]":
                    in_events = True
                    continue
                elif line.strip().startswith("[") and in_events:
                    in_events = False
                    continue

                if not in_events:
                    continue

                if line.strip().lower().startswith("format:"):
                    format_fields = [f.strip().lower() for f in line.split(":", 1)[1].split(",")]
                    continue

                if line.strip().startswith("Dialogue:") or line.strip().startswith("Comment:"):
                    prefix, _, data = line.partition(":")
                    text_index = len(format_fields) - 1 if format_fields else 9

                    parts = data.split(",", text_index)
                    if len(parts) > text_index:
                        text = parts[text_index].strip()
                        clean_text = re.sub(r"\{[^}]*\}", "", text)
                        if clean_text.strip() and prefix.strip() == "Dialogue":
                            dialogue_idx += 1
                            extracted_text.append(f"ASS_{dialogue_idx}: {text}")

            if not extracted_text:
                return ass_content

            return "\n".join(extracted_text)
        except Exception as e:
            raise ValueError(f"ASS/SSA reading error: {e}") from e

    @staticmethod
    def reconstruct_ass(original_content: str, translations: dict[str, str]) -> str:
        try:
            lines = original_content.split("\n")
            result_lines: list[str] = []
            in_events = False
            format_fields: list[str] = []
            dialogue_idx = 0

            for line in lines:
                stripped = line.rstrip()

                if stripped.strip().lower() == "[events]":
                    in_events = True
                    result_lines.append(stripped)
                    continue
                elif stripped.strip().startswith("[") and in_events:
                    in_events = False
                    result_lines.append(stripped)
                    continue

                if not in_events:
                    result_lines.append(stripped)
                    continue

                if stripped.strip().lower().startswith("format:"):
                    format_fields = [
                        f.strip().lower() for f in stripped.split(":", 1)[1].split(",")
                    ]
                    result_lines.append(stripped)
                    continue

                if stripped.strip().startswith("Dialogue:"):
                    prefix, _, data = stripped.partition(":")
                    text_index = len(format_fields) - 1 if format_fields else 9

                    parts = data.split(",", text_index)
                    if len(parts) > text_index:
                        text = parts[text_index].strip()
                        dialogue_idx += 1
                        key = f"ASS_{dialogue_idx}: {text}"
                        if key in translations:
                            parts[text_index] = translations[key]
                        result_lines.append(f"{prefix}:{','.join(parts)}")
                        continue

                result_lines.append(stripped)

            return "\n".join(result_lines)
        except Exception as e:
            raise ValueError(f"ASS/SSA reconstruction error: {e}") from e
