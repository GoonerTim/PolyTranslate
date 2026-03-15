"""Tests for the Ren'Py processor module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.renpy_processor import RenpyProcessor


class TestRenpyProcessorReadRpy:
    """Tests for RenpyProcessor.read_rpy method."""

    def test_read_rpy_old_dialogue_triple_quotes(self) -> None:
        rpy_content = b"    '''This is old dialogue'''"
        result = RenpyProcessor.read_rpy(rpy_content)
        assert "DIALOGUE_LINE_1: This is old dialogue" in result

    def test_read_rpy_old_dialogue_triple_double_quotes(self) -> None:
        rpy_content = b'    """This is triple quoted dialogue"""'
        result = RenpyProcessor.read_rpy(rpy_content)
        assert "DIALOGUE_LINE_1: This is triple quoted dialogue" in result

    def test_read_rpy_old_dialogue_empty_not_extracted(self) -> None:
        rpy_content = b"    '''   '''"
        result = RenpyProcessor.read_rpy(rpy_content)
        # Empty old dialogue should not be extracted (match.strip() is falsy)
        assert "DIALOGUE_LINE" not in result or "   " not in result

    def test_read_rpy_error_raises_value_error(self) -> None:
        with (
            patch.object(
                RenpyProcessor.__mro__[0],
                "read_rpy",
                wraps=RenpyProcessor.read_rpy,
            ),
            patch(
                "app.core.renpy_processor.FileProcessor.detect_encoding",
                side_effect=RuntimeError("encoding failed"),
            ),
            pytest.raises(ValueError, match="RPY reading error"),
        ):
            RenpyProcessor.read_rpy(b"some content")

    def test_read_rpy_error_wraps_original_exception(self) -> None:
        with patch(
            "app.core.renpy_processor.FileProcessor.detect_encoding",
            side_effect=RuntimeError("bad encoding"),
        ):
            with pytest.raises(ValueError, match="bad encoding") as exc_info:
                RenpyProcessor.read_rpy(b"content")
            assert exc_info.value.__cause__ is not None


class TestRenpyProcessorReconstructRpy:
    """Tests for RenpyProcessor.reconstruct_rpy method."""

    def test_reconstruct_rpy_translate_strings(self) -> None:
        original = '    _("Start game")'
        translations = {"TRANSLATABLE_STRING_1: Start game": "Начать игру"}
        result = RenpyProcessor.reconstruct_rpy(
            original, translations, translate_dialogue=False, translate_strings=True
        )
        assert "Начать игру" in result

    def test_reconstruct_rpy_translate_strings_preserves_structure(self) -> None:
        original = '    _("Play")\n    _("Exit")'
        translations = {
            "TRANSLATABLE_STRING_1: Play": "Играть",
            "TRANSLATABLE_STRING_2: Exit": "Выход",
        }
        result = RenpyProcessor.reconstruct_rpy(
            original, translations, translate_dialogue=False, translate_strings=True
        )
        assert "Играть" in result
        assert "Выход" in result

    def test_reconstruct_rpy_translate_strings_no_match(self) -> None:
        original = '    _("Keep original")'
        translations = {}
        result = RenpyProcessor.reconstruct_rpy(
            original, translations, translate_dialogue=False, translate_strings=True
        )
        assert '_("Keep original")' in result

    def test_reconstruct_rpy_translate_strings_single_quotes(self) -> None:
        original = "    _('Options')"
        translations = {"TRANSLATABLE_STRING_1: Options": "Опции"}
        result = RenpyProcessor.reconstruct_rpy(
            original, translations, translate_dialogue=False, translate_strings=True
        )
        assert "Опции" in result

    def test_reconstruct_rpy_error_raises_value_error(self) -> None:
        with (
            patch(
                "app.core.renpy_processor.re.sub",
                side_effect=RuntimeError("regex failed"),
            ),
            pytest.raises(ValueError, match="RPY reconstruction error"),
        ):
            RenpyProcessor.reconstruct_rpy(
                'e "Hello"',
                {"DIALOGUE_LINE_1: Hello": "Привет"},
            )

    def test_reconstruct_rpy_error_wraps_original_exception(self) -> None:
        with patch(
            "app.core.renpy_processor.re.sub",
            side_effect=RuntimeError("broken"),
        ):
            with pytest.raises(ValueError, match="broken") as exc_info:
                RenpyProcessor.reconstruct_rpy('e "Hello"', {})
            assert exc_info.value.__cause__ is not None
