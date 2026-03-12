"""Tests for Ren'Py context extractor."""

from __future__ import annotations

from pathlib import Path

from app.core.renpy_context import RenpyCharacter, RenpyContext, RenpyContextExtractor, RenpyScene


class TestRenpyCharacter:
    def test_create(self) -> None:
        char = RenpyCharacter(variable="e", name="Eileen", color="#c8ffc8")
        assert char.variable == "e"
        assert char.name == "Eileen"
        assert char.color == "#c8ffc8"

    def test_default_color(self) -> None:
        char = RenpyCharacter(variable="mc", name="Main Character")
        assert char.color == ""


class TestRenpyScene:
    def test_create(self) -> None:
        scene = RenpyScene(label="start", characters_present=["e", "mc"])
        assert scene.label == "start"
        assert scene.characters_present == ["e", "mc"]


class TestRenpyContext:
    def test_create(self) -> None:
        ctx = RenpyContext()
        assert ctx.characters == []
        assert ctx.scenes == []
        assert ctx.current_scene == ""
        assert ctx.nearby_dialogue == []


class TestRenpyContextExtractor:
    def test_extract_characters(self, temp_dir: Path) -> None:
        rpy_file = temp_dir / "script.rpy"
        rpy_file.write_text(
            'define e = Character("Eileen", color="#c8ffc8")\n'
            'define mc = Character("Main Character")\n',
            encoding="utf-8",
        )

        extractor = RenpyContextExtractor(str(temp_dir))
        characters = extractor.extract_characters()

        assert len(characters) == 2
        assert characters[0].variable == "e"
        assert characters[0].name == "Eileen"
        assert characters[0].color == "#c8ffc8"
        assert characters[1].variable == "mc"
        assert characters[1].name == "Main Character"

    def test_extract_characters_with_color(self, temp_dir: Path) -> None:
        rpy_file = temp_dir / "chars.rpy"
        rpy_file.write_text(
            'define s = Character("Sylvie", color="#ff0000", what_color="#ffffff")\n',
            encoding="utf-8",
        )

        extractor = RenpyContextExtractor(str(temp_dir))
        characters = extractor.extract_characters()

        assert len(characters) == 1
        assert characters[0].variable == "s"
        assert characters[0].name == "Sylvie"
        assert characters[0].color == "#ff0000"

    def test_extract_scenes(self, temp_dir: Path) -> None:
        rpy_file = temp_dir / "script.rpy"
        rpy_file.write_text(
            "label start:\n"
            '    e "Hello!"\n'
            '    mc "Hi there!"\n'
            "\n"
            "label chapter1:\n"
            '    e "Welcome to chapter 1"\n',
            encoding="utf-8",
        )

        extractor = RenpyContextExtractor(str(temp_dir))
        scenes = extractor.extract_scenes()

        assert len(scenes) == 2
        assert scenes[0].label == "start"
        assert scenes[1].label == "chapter1"

    def test_scene_characters(self, temp_dir: Path) -> None:
        rpy_file = temp_dir / "script.rpy"
        rpy_file.write_text(
            'label start:\n    e "Hello!"\n    mc "Hi there!"\n    e "How are you?"\n',
            encoding="utf-8",
        )

        extractor = RenpyContextExtractor(str(temp_dir))
        scenes = extractor.extract_scenes()

        assert len(scenes) == 1
        assert "e" in scenes[0].characters_present
        assert "mc" in scenes[0].characters_present

    def test_context_string_format(self, temp_dir: Path) -> None:
        rpy_file = temp_dir / "script.rpy"
        rpy_file.write_text(
            'define e = Character("Eileen")\nlabel start:\n    e "Hello!"\n',
            encoding="utf-8",
        )

        extractor = RenpyContextExtractor(str(temp_dir))
        context = extractor.get_context_for_text('e "Hello!"', str(rpy_file))

        assert "== GAME CONTEXT ==" in context
        assert "== END CONTEXT ==" in context
        assert "Characters:" in context
        assert "e=Eileen" in context

    def test_context_truncation(self, temp_dir: Path) -> None:
        rpy_file = temp_dir / "script.rpy"
        # Create lots of characters
        lines = [f'define c{i} = Character("Character{i}")' for i in range(100)]
        lines.append("label start:")
        lines.append('    c0 "Hello"')
        rpy_file.write_text("\n".join(lines), encoding="utf-8")

        extractor = RenpyContextExtractor(str(temp_dir))
        context = extractor.get_context_for_text("test", "", max_tokens=50)

        # 50 tokens * 4 chars = 200 chars max
        assert len(context) <= 250  # Allow some overhead for the closing tag

    def test_empty_folder(self, temp_dir: Path) -> None:
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        extractor = RenpyContextExtractor(str(empty_dir))
        characters = extractor.extract_characters()
        scenes = extractor.extract_scenes()

        assert characters == []
        assert scenes == []

    def test_nonexistent_folder(self) -> None:
        extractor = RenpyContextExtractor("/nonexistent/path")
        characters = extractor.extract_characters()
        scenes = extractor.extract_scenes()

        assert characters == []
        assert scenes == []

    def test_dialogue_preview_limit(self, temp_dir: Path) -> None:
        rpy_file = temp_dir / "script.rpy"
        lines = ["label start:"]
        for i in range(10):
            lines.append(f'    e "Line {i}"')
        rpy_file.write_text("\n".join(lines), encoding="utf-8")

        extractor = RenpyContextExtractor(str(temp_dir))
        scenes = extractor.extract_scenes()

        assert len(scenes) == 1
        assert len(scenes[0].dialogue_preview) == 5  # max 5
