"""Ren'Py file processors."""

from __future__ import annotations

import re

from app.core.file_processor import FileProcessor


class RenpyProcessor:
    """Handles reading and reconstruction of Ren'Py (.rpy) files."""

    @staticmethod
    def read_rpy(
        file_content: bytes,
        translate_dialogue: bool = True,
        translate_strings: bool = True,
        preserve_code: bool = True,
    ) -> str:
        try:
            encoding = FileProcessor.detect_encoding(file_content)
            rpy_content = file_content.decode(encoding)

            patterns = {
                "dialogue": r'^\s*[^#\n]*["\'](.*?)["\']',
                "old_dialogue": r'^\s*[^#\n]*["\']{3}(.*?)["\']{3}',
                "string_translations": r'^\s*_\(["\'](.*?)["\']\)',
                "character_dialogue": r'^\s*(\w+)\s*["\'](.*?)["\']',
                "menu_options": r'^\s*["\'](.*?)["\']:',
            }

            extracted_text: list[str] = []
            lines = rpy_content.split("\n")

            for line_num, line in enumerate(lines, 1):
                line = line.rstrip()

                if line.strip().startswith("#"):
                    continue

                if translate_dialogue:
                    dialogue_matches = re.findall(patterns["dialogue"], line)
                    for match in dialogue_matches:
                        if match.strip() and len(match.strip()) > 1:
                            extracted_text.append(f"DIALOGUE_LINE_{line_num}: {match}")

                    old_dialogue_matches = re.findall(patterns["old_dialogue"], line, re.DOTALL)
                    for match in old_dialogue_matches:
                        if match.strip():
                            extracted_text.append(f"DIALOGUE_LINE_{line_num}: {match}")

                if translate_strings:
                    string_matches = re.findall(patterns["string_translations"], line)
                    for match in string_matches:
                        if match.strip():
                            extracted_text.append(f"TRANSLATABLE_STRING_{line_num}: {match}")

                if translate_dialogue:
                    char_matches = re.findall(patterns["character_dialogue"], line)
                    for char, dialogue in char_matches:
                        if dialogue.strip():
                            extracted_text.append(
                                f"CHARACTER_DIALOGUE_{line_num}_{char}: {dialogue}"
                            )

                    menu_matches = re.findall(patterns["menu_options"], line)
                    for match in menu_matches:
                        if match.strip():
                            extracted_text.append(f"MENU_OPTION_{line_num}: {match}")

            if not extracted_text:
                return rpy_content

            return "\n".join(extracted_text)

        except Exception as e:
            raise ValueError(f"RPY reading error: {e}") from e

    @staticmethod
    def reconstruct_rpy(
        original_content: str,
        translations: dict[str, str],
        translate_dialogue: bool = True,
        translate_strings: bool = True,
    ) -> str:
        try:
            lines = original_content.split("\n")
            translated_lines: list[str] = []

            for line_num, line in enumerate(lines, 1):
                current_line = line

                if translate_dialogue:
                    dialogue_pattern = r'^(\s*[^#\n]*)(["\'])(.*?)(["\'])'

                    def replace_dialogue(match: re.Match[str], num: int = line_num) -> str:
                        prefix = match.group(1)
                        start_quote = match.group(2)
                        content = match.group(3)
                        end_quote = match.group(4)

                        key = f"DIALOGUE_LINE_{num}: {content}"
                        if key in translations:
                            return f"{prefix}{start_quote}{translations[key]}{end_quote}"
                        return match.group(0)

                    current_line = re.sub(dialogue_pattern, replace_dialogue, current_line)

                if translate_strings:
                    string_pattern = r'^(\s*_\()(["\'])(.*?)(["\']\))'

                    def replace_string(match: re.Match[str], num: int = line_num) -> str:
                        prefix = match.group(1)
                        start_quote = match.group(2)
                        content = match.group(3)
                        end_quote = match.group(4)

                        key = f"TRANSLATABLE_STRING_{num}: {content}"
                        if key in translations:
                            return f"{prefix}{start_quote}{translations[key]}{end_quote})"
                        return match.group(0)

                    current_line = re.sub(string_pattern, replace_string, current_line)

                translated_lines.append(current_line)

            return "\n".join(translated_lines)

        except Exception as e:
            raise ValueError(f"RPY reconstruction error: {e}") from e

    @staticmethod
    def split_rpy_by_scenes(content: str) -> list[tuple[str, str]]:
        label_pattern = re.compile(r"^\s*label\s+(\w+)\s*:", re.MULTILINE)
        matches = list(label_pattern.finditer(content))

        if not matches:
            return [("_full", content)]

        scenes: list[tuple[str, str]] = []

        if matches[0].start() > 0:
            preamble = content[: matches[0].start()].strip()
            if preamble:
                scenes.append(("_preamble", preamble))

        for i, match in enumerate(matches):
            label_name = match.group(1)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            scene_content = content[start:end].rstrip()
            scenes.append((label_name, scene_content))

        return scenes
