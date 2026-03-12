"""Tests for Ren'Py scene splitting in FileProcessor."""

from __future__ import annotations

from app.core.file_processor import FileProcessor


class TestSplitRpyByScenes:
    def test_split_rpy_by_scenes(self) -> None:
        content = (
            "label start:\n"
            '    e "Hello!"\n'
            '    mc "Hi!"\n'
            "\n"
            "label chapter1:\n"
            '    e "Welcome"\n'
            "\n"
            "label chapter2:\n"
            '    mc "Goodbye"\n'
        )

        scenes = FileProcessor.split_rpy_by_scenes(content)

        assert len(scenes) == 3
        assert scenes[0][0] == "start"
        assert 'e "Hello!"' in scenes[0][1]
        assert scenes[1][0] == "chapter1"
        assert 'e "Welcome"' in scenes[1][1]
        assert scenes[2][0] == "chapter2"
        assert 'mc "Goodbye"' in scenes[2][1]

    def test_split_no_labels(self) -> None:
        content = 'e "Hello!"\nmc "Hi!"\n'

        scenes = FileProcessor.split_rpy_by_scenes(content)

        assert len(scenes) == 1
        assert scenes[0][0] == "_full"
        assert scenes[0][1] == content

    def test_split_single_label(self) -> None:
        content = 'label start:\n    e "Hello!"\n    mc "Hi!"\n'

        scenes = FileProcessor.split_rpy_by_scenes(content)

        assert len(scenes) == 1
        assert scenes[0][0] == "start"
        assert 'e "Hello!"' in scenes[0][1]

    def test_split_with_preamble(self) -> None:
        content = 'define e = Character("Eileen")\n\nlabel start:\n    e "Hello!"\n'

        scenes = FileProcessor.split_rpy_by_scenes(content)

        assert len(scenes) == 2
        assert scenes[0][0] == "_preamble"
        assert "define" in scenes[0][1]
        assert scenes[1][0] == "start"

    def test_split_empty_content(self) -> None:
        scenes = FileProcessor.split_rpy_by_scenes("")
        assert len(scenes) == 1
        assert scenes[0][0] == "_full"

    def test_scene_content_boundaries(self) -> None:
        content = 'label scene1:\n    e "Line 1"\n    e "Line 2"\nlabel scene2:\n    mc "Line 3"\n'

        scenes = FileProcessor.split_rpy_by_scenes(content)

        assert len(scenes) == 2
        # scene1 should NOT contain scene2's content
        assert "Line 3" not in scenes[0][1]
        # scene2 should NOT contain scene1's content
        assert "Line 1" not in scenes[1][1]
