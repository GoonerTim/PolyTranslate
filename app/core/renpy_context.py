"""Ren'Py game context extractor for translation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RenpyCharacter:
    variable: str
    name: str
    color: str = ""


@dataclass
class RenpyScene:
    label: str
    characters_present: list[str] = field(default_factory=list)
    dialogue_preview: list[str] = field(default_factory=list)


@dataclass
class RenpyContext:
    characters: list[RenpyCharacter] = field(default_factory=list)
    scenes: list[RenpyScene] = field(default_factory=list)
    current_scene: str = ""
    nearby_dialogue: list[str] = field(default_factory=list)


CHARACTER_PATTERN = re.compile(
    r'^\s*define\s+(\w+)\s*=\s*Character\s*\(\s*["\'](.+?)["\'](?:\s*,\s*(.+?))?\s*\)',
    re.MULTILINE,
)
COLOR_PATTERN = re.compile(r'color\s*=\s*["\'](.+?)["\']')
LABEL_PATTERN = re.compile(r"^\s*label\s+(\w+)\s*:", re.MULTILINE)
DIALOGUE_PATTERN = re.compile(r'^\s+(\w+)\s+["\'](.*?)["\']', re.MULTILINE)


class RenpyContextExtractor:
    def __init__(self, game_folder: str) -> None:
        self.game_folder = Path(game_folder)

    def extract_characters(self) -> list[RenpyCharacter]:
        characters: list[RenpyCharacter] = []
        if not self.game_folder.exists():
            return characters

        for rpy_file in self.game_folder.rglob("*.rpy"):
            try:
                content = rpy_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            for match in CHARACTER_PATTERN.finditer(content):
                variable = match.group(1)
                name = match.group(2)
                kwargs = match.group(3) or ""
                color = ""
                color_match = COLOR_PATTERN.search(kwargs)
                if color_match:
                    color = color_match.group(1)
                characters.append(RenpyCharacter(variable=variable, name=name, color=color))

        return characters

    def extract_scenes(self) -> list[RenpyScene]:
        scenes: list[RenpyScene] = []
        if not self.game_folder.exists():
            return scenes

        for rpy_file in self.game_folder.rglob("*.rpy"):
            try:
                content = rpy_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            label_positions = [(m.start(), m.group(1)) for m in LABEL_PATTERN.finditer(content)]

            for i, (pos, label_name) in enumerate(label_positions):
                end_pos = (
                    label_positions[i + 1][0] if i + 1 < len(label_positions) else len(content)
                )
                block = content[pos:end_pos]

                chars_in_scene: list[str] = []
                dialogue_preview: list[str] = []

                for dmatch in DIALOGUE_PATTERN.finditer(block):
                    char_var = dmatch.group(1)
                    dialogue_text = dmatch.group(2)

                    if char_var not in chars_in_scene:
                        chars_in_scene.append(char_var)

                    if len(dialogue_preview) < 5:
                        dialogue_preview.append(f'{char_var}: "{dialogue_text}"')

                scenes.append(
                    RenpyScene(
                        label=label_name,
                        characters_present=chars_in_scene,
                        dialogue_preview=dialogue_preview,
                    )
                )

        return scenes

    def get_context_for_text(
        self, text: str, current_file: str = "", max_tokens: int = 1500
    ) -> str:
        characters = self.extract_characters()
        scenes = self.extract_scenes()

        current_scene = self._detect_current_scene(text, scenes)
        nearby = self._get_nearby_dialogue(text, current_file)

        parts: list[str] = ["== GAME CONTEXT =="]

        if characters:
            char_strs = [f"{c.variable}={c.name}" for c in characters]
            parts.append(f"Characters: {', '.join(char_strs)}")

        if current_scene:
            parts.append(f"Current Scene: {current_scene}")

        if nearby:
            parts.append("Recent dialogue:")
            for line in nearby[:10]:
                parts.append(f"  {line}")

        parts.append("== END CONTEXT ==")

        context = "\n".join(parts)

        # Truncate by approximate token count (4 chars ≈ 1 token)
        max_chars = max_tokens * 4
        if len(context) > max_chars:
            context = context[:max_chars] + "\n== END CONTEXT =="

        return context

    def _detect_current_scene(self, text: str, scenes: list[RenpyScene]) -> str:
        label_match = LABEL_PATTERN.search(text)
        if label_match:
            return label_match.group(1)

        for scene in scenes:
            for preview_line in scene.dialogue_preview:
                dialogue_text = preview_line.split(": ", 1)[-1].strip('"')
                if dialogue_text in text:
                    return scene.label

        return ""

    def _get_nearby_dialogue(self, text: str, current_file: str) -> list[str]:
        if not current_file:
            return []

        file_path = Path(current_file)
        if not file_path.exists():
            return []

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        lines = content.split("\n")
        text_lines = text.split("\n")
        first_line = text_lines[0].strip() if text_lines else ""

        if not first_line:
            return []

        target_idx = -1
        for i, line in enumerate(lines):
            if first_line in line:
                target_idx = i
                break

        if target_idx < 0:
            return []

        nearby: list[str] = []
        start = max(0, target_idx - 5)
        end = min(len(lines), target_idx + len(text_lines) + 5)

        for line in lines[start:end]:
            dmatch = DIALOGUE_PATTERN.match(line)
            if dmatch:
                nearby.append(f'{dmatch.group(1)}: "{dmatch.group(2)}"')

        return nearby
