"""Tests for DiffView diff logic (no GUI required)."""

from __future__ import annotations

import difflib


class TestDiffLogic:
    """Test the diff algorithm used by DiffView."""

    def test_identical_texts_no_changes(self):
        original = "Hello\nWorld\n"
        translated = "Hello\nWorld\n"
        orig_lines = original.splitlines(keepends=True)
        trans_lines = translated.splitlines(keepends=True)
        opcodes = difflib.SequenceMatcher(None, orig_lines, trans_lines).get_opcodes()
        tags = [tag for tag, *_ in opcodes]
        assert tags == ["equal"]

    def test_full_replacement(self):
        original = "Hello\n"
        translated = "Привет\n"
        orig_lines = original.splitlines(keepends=True)
        trans_lines = translated.splitlines(keepends=True)
        opcodes = difflib.SequenceMatcher(None, orig_lines, trans_lines).get_opcodes()
        tags = [tag for tag, *_ in opcodes]
        assert "replace" in tags

    def test_added_lines(self):
        original = "Line1\n"
        translated = "Line1\nLine2\n"
        orig_lines = original.splitlines(keepends=True)
        trans_lines = translated.splitlines(keepends=True)
        opcodes = difflib.SequenceMatcher(None, orig_lines, trans_lines).get_opcodes()
        tags = [tag for tag, *_ in opcodes]
        assert "equal" in tags
        assert "insert" in tags

    def test_deleted_lines(self):
        original = "Line1\nLine2\n"
        translated = "Line1\n"
        orig_lines = original.splitlines(keepends=True)
        trans_lines = translated.splitlines(keepends=True)
        opcodes = difflib.SequenceMatcher(None, orig_lines, trans_lines).get_opcodes()
        tags = [tag for tag, *_ in opcodes]
        assert "delete" in tags

    def test_mixed_changes(self):
        original = "Line1\nLine2\nLine3\n"
        translated = "Line1\nChanged\nLine3\nNew\n"
        orig_lines = original.splitlines(keepends=True)
        trans_lines = translated.splitlines(keepends=True)
        opcodes = difflib.SequenceMatcher(None, orig_lines, trans_lines).get_opcodes()
        tags = [tag for tag, *_ in opcodes]
        assert "equal" in tags
        assert len(opcodes) > 1

    def test_revert_line_replace(self):
        """Simulate reverting a translated line back to original."""
        original_lines = ["Hello\n", "World\n"]
        translated_lines = ["Привет\n", "Мир\n"]

        # Revert line 0 back to original
        translated_lines[0] = original_lines[0]

        assert translated_lines == ["Hello\n", "Мир\n"]
        result = "".join(translated_lines)
        assert result == "Hello\nМир\n"

    def test_revert_line_delete(self):
        """Simulate reverting an inserted line by deleting it."""
        translated_lines = ["Line1\n", "Extra\n", "Line2\n"]

        # Remove the inserted line at index 1
        del translated_lines[1]

        assert "".join(translated_lines) == "Line1\nLine2\n"

    def test_empty_original(self):
        original = ""
        translated = "Something\n"
        orig_lines = original.splitlines(keepends=True)
        trans_lines = translated.splitlines(keepends=True)
        opcodes = difflib.SequenceMatcher(None, orig_lines, trans_lines).get_opcodes()
        tags = [tag for tag, *_ in opcodes]
        assert "insert" in tags

    def test_empty_translation(self):
        original = "Something\n"
        translated = ""
        orig_lines = original.splitlines(keepends=True)
        trans_lines = translated.splitlines(keepends=True)
        opcodes = difflib.SequenceMatcher(None, orig_lines, trans_lines).get_opcodes()
        tags = [tag for tag, *_ in opcodes]
        assert "delete" in tags

    def test_multiline_paragraph(self):
        original = "First sentence.\nSecond sentence.\nThird sentence.\n"
        translated = "Первое предложение.\nSecond sentence.\nТретье предложение.\n"
        orig_lines = original.splitlines(keepends=True)
        trans_lines = translated.splitlines(keepends=True)
        opcodes = difflib.SequenceMatcher(None, orig_lines, trans_lines).get_opcodes()

        # Middle line should be equal
        equal_ranges = [(i1, i2) for tag, i1, i2, j1, j2 in opcodes if tag == "equal"]
        equal_lines = []
        for i1, i2 in equal_ranges:
            equal_lines.extend(orig_lines[i1:i2])
        assert "Second sentence.\n" in equal_lines
