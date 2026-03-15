"""Tests for SubtitleProcessor edge cases and error paths."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.subtitle_processor import SubtitleProcessor


class TestReadSRT:
    def test_invalid_index_skipped(self) -> None:
        srt_content = (
            b"abc\n00:00:01,000 --> 00:00:04,000\nHello\n\n"
            b"2\n00:00:05,000 --> 00:00:08,000\nWorld\n"
        )
        result = SubtitleProcessor.read_srt(srt_content)
        assert "SRT_2: World" in result
        assert "Hello" not in result

    def test_missing_timecode_separator_skipped(self) -> None:
        srt_content = (
            b"1\n00:00:01,000 00:00:04,000\nHello\n\n2\n00:00:05,000 --> 00:00:08,000\nWorld\n"
        )
        result = SubtitleProcessor.read_srt(srt_content)
        assert "SRT_2: World" in result
        assert "SRT_1" not in result

    def test_no_valid_blocks_returns_original(self) -> None:
        srt_content = b"abc\nno timecode\nsome text\n"
        result = SubtitleProcessor.read_srt(srt_content)
        assert "abc" in result
        assert "no timecode" in result

    def test_error_raises_valueerror(self) -> None:
        with (
            patch(
                "app.core.subtitle_processor.FileProcessor.detect_encoding",
                side_effect=RuntimeError("encoding failure"),
            ),
            pytest.raises(ValueError, match="SRT reading error"),
        ):
            SubtitleProcessor.read_srt(b"data")


class TestReconstructSRT:
    def test_short_block_preserved(self) -> None:
        original = "1\n00:00:01,000 --> 00:00:04,000\nHello\n\nshort line\n\n2\n00:00:05,000 --> 00:00:08,000\nWorld\n"
        translations = {"SRT_2: World": "Мир"}
        result = SubtitleProcessor.reconstruct_srt(original, translations)
        assert "short line" in result
        assert "Мир" in result

    def test_invalid_index_block_preserved(self) -> None:
        original = (
            "abc\n00:00:01,000 --> 00:00:04,000\nHello\n\n2\n00:00:05,000 --> 00:00:08,000\nWorld\n"
        )
        translations = {"SRT_2: World": "Мир"}
        result = SubtitleProcessor.reconstruct_srt(original, translations)
        assert "abc" in result
        assert "Мир" in result

    def test_missing_timecode_block_preserved(self) -> None:
        original = "1\nno arrow here\nHello\n\n2\n00:00:05,000 --> 00:00:08,000\nWorld\n"
        translations = {"SRT_2: World": "Мир"}
        result = SubtitleProcessor.reconstruct_srt(original, translations)
        assert "no arrow here" in result
        assert "Мир" in result

    def test_error_raises_valueerror(self) -> None:
        with (
            patch(
                "app.core.subtitle_processor.re.split",
                side_effect=RuntimeError("regex failure"),
            ),
            pytest.raises(ValueError, match="SRT reconstruction error"),
        ):
            SubtitleProcessor.reconstruct_srt("1\n00:00:00,000 --> 00:00:01,000\nHi\n", {})


class TestReadASS:
    def test_comment_lines_skipped(self) -> None:
        ass_content = (
            b"[Events]\n"
            b"Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            b"Comment: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,This is a comment\n"
            b"Dialogue: 0,0:00:05.00,0:00:08.00,Default,,0,0,0,,Visible text\n"
        )
        result = SubtitleProcessor.read_ass(ass_content)
        assert "ASS_1: Visible text" in result
        assert "This is a comment" not in result

    def test_empty_clean_text_skipped(self) -> None:
        ass_content = (
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            r"Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,{\b1}{\b0}" + "\n"
            "Dialogue: 0,0:00:05.00,0:00:08.00,Default,,0,0,0,,Real text\n"
        ).encode()
        result = SubtitleProcessor.read_ass(ass_content)
        assert "ASS_1: Real text" in result
        assert "ASS_2" not in result

    def test_no_events_section_returns_original(self) -> None:
        ass_content = (
            b"[Script Info]\nTitle: Test\n\n"
            b"[V4+ Styles]\nFormat: Name, Fontname\nStyle: Default,Arial\n"
        )
        result = SubtitleProcessor.read_ass(ass_content)
        assert "[Script Info]" in result
        assert "Title: Test" in result

    def test_section_after_events_exits_events(self) -> None:
        ass_content = (
            b"[Events]\n"
            b"Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            b"Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,Hello\n"
            b"[Fonts]\n"
            b"Dialogue: 0,0:00:05.00,0:00:08.00,Default,,0,0,0,,Should be ignored\n"
        )
        result = SubtitleProcessor.read_ass(ass_content)
        assert "ASS_1: Hello" in result
        assert "Should be ignored" not in result

    def test_error_raises_valueerror(self) -> None:
        with (
            patch(
                "app.core.subtitle_processor.FileProcessor.detect_encoding",
                side_effect=RuntimeError("encoding failure"),
            ),
            pytest.raises(ValueError, match="ASS/SSA reading error"),
        ):
            SubtitleProcessor.read_ass(b"data")


class TestReconstructASS:
    def test_section_after_events_exits_events(self) -> None:
        ass_content = (
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,Hello\n"
            "[Fonts]\n"
            "fontdata: abc\n"
        )
        translations = {"ASS_1: Hello": "Привет"}
        result = SubtitleProcessor.reconstruct_ass(ass_content, translations)
        assert "Привет" in result
        assert "[Fonts]" in result
        assert "fontdata: abc" in result

    def test_error_raises_valueerror(self) -> None:
        with (
            patch(
                "app.core.subtitle_processor.SubtitleProcessor.reconstruct_ass",
                side_effect=ValueError("ASS/SSA reconstruction error: test"),
            ),
            pytest.raises(ValueError, match="ASS/SSA reconstruction error"),
        ):
            SubtitleProcessor.reconstruct_ass("content", {})

    def test_error_from_internal_exception(self) -> None:
        # Pass non-string to trigger an exception inside the try block
        with pytest.raises(ValueError, match="ASS.*reconstruction error"):
            SubtitleProcessor.reconstruct_ass(None, {})  # type: ignore[arg-type]
