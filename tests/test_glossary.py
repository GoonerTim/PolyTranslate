"""Tests for the glossary module."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.utils.glossary import Glossary


class TestGlossary:
    """Tests for Glossary class."""

    def test_empty_glossary(self, temp_dir: Path) -> None:
        """Test empty glossary initialization."""
        glossary_path = temp_dir / "glossary.json"
        glossary = Glossary(glossary_path)

        assert len(glossary) == 0
        assert glossary.get_all_entries() == {}

    def test_load_glossary(self, temp_glossary: Path) -> None:
        """Test loading glossary from file."""
        glossary = Glossary(temp_glossary)

        assert len(glossary) == 2
        assert glossary.get_entry("Hello") == "Привет"
        assert glossary.get_entry("world") == "мир"

    def test_add_entry(self, temp_dir: Path) -> None:
        """Test adding glossary entry."""
        glossary_path = temp_dir / "glossary.json"
        glossary = Glossary(glossary_path)

        glossary.add_entry("test", "тест")
        assert glossary.get_entry("test") == "тест"

    def test_add_entry_validation(self, temp_dir: Path) -> None:
        """Test entry validation."""
        glossary_path = temp_dir / "glossary.json"
        glossary = Glossary(glossary_path)

        with pytest.raises(ValueError):
            glossary.add_entry("", "value")

        with pytest.raises(ValueError):
            glossary.add_entry("key", "")

    def test_remove_entry(self, temp_glossary: Path) -> None:
        """Test removing glossary entry."""
        glossary = Glossary(temp_glossary)

        assert glossary.remove_entry("Hello") is True
        assert glossary.get_entry("Hello") is None
        assert len(glossary) == 1

    def test_remove_nonexistent_entry(self, temp_glossary: Path) -> None:
        """Test removing nonexistent entry."""
        glossary = Glossary(temp_glossary)
        assert glossary.remove_entry("nonexistent") is False

    def test_save_glossary(self, temp_dir: Path) -> None:
        """Test saving glossary to file."""
        glossary_path = temp_dir / "glossary.json"
        glossary = Glossary(glossary_path)

        glossary.add_entry("key1", "value1")
        glossary.add_entry("key2", "value2")
        glossary.save()

        # Load again and verify
        glossary2 = Glossary(glossary_path)
        assert glossary2.get_entry("key1") == "value1"
        assert glossary2.get_entry("key2") == "value2"

    def test_apply_replacements(self, temp_glossary: Path) -> None:
        """Test applying glossary replacements."""
        glossary = Glossary(temp_glossary)

        text = "Hello, world!"
        result = glossary.apply(text)
        assert result == "Привет, мир!"

    def test_apply_case_insensitive(self, temp_glossary: Path) -> None:
        """Test case-insensitive replacements."""
        glossary = Glossary(temp_glossary)
        glossary.set_case_sensitive(False)

        text = "HELLO, WORLD!"
        result = glossary.apply(text)
        assert "Привет" in result
        assert "мир" in result

    def test_apply_case_sensitive(self, temp_dir: Path) -> None:
        """Test case-sensitive replacements."""
        glossary_path = temp_dir / "glossary.json"
        glossary = Glossary(glossary_path)
        glossary.add_entry("Hello", "Привет")
        glossary.set_case_sensitive(True)

        text = "HELLO, world!"
        result = glossary.apply(text)
        # HELLO should not be replaced
        assert "HELLO" in result

    def test_apply_empty_glossary(self, temp_dir: Path) -> None:
        """Test applying empty glossary."""
        glossary_path = temp_dir / "glossary.json"
        glossary = Glossary(glossary_path)

        text = "Hello, world!"
        result = glossary.apply(text)
        assert result == text

    def test_clear_glossary(self, temp_glossary: Path) -> None:
        """Test clearing glossary."""
        glossary = Glossary(temp_glossary)
        assert len(glossary) > 0

        glossary.clear()
        assert len(glossary) == 0

    def test_set_entries(self, temp_dir: Path) -> None:
        """Test setting all entries at once."""
        glossary_path = temp_dir / "glossary.json"
        glossary = Glossary(glossary_path)

        entries = {"a": "b", "c": "d"}
        glossary.set_entries(entries)

        assert glossary.get_entry("a") == "b"
        assert glossary.get_entry("c") == "d"
        assert len(glossary) == 2

    def test_import_export(self, temp_dir: Path) -> None:
        """Test import/export functionality."""
        glossary_path = temp_dir / "glossary.json"
        glossary = Glossary(glossary_path)

        # Import
        data = {"x": "y", "": "empty"}  # Empty key should be skipped
        count = glossary.import_from_dict(data)
        assert count == 1

        # Export
        exported = glossary.export_to_dict()
        assert exported == {"x": "y"}

    def test_contains(self, temp_glossary: Path) -> None:
        """Test __contains__ method."""
        glossary = Glossary(temp_glossary)

        assert "Hello" in glossary
        assert "nonexistent" not in glossary

    def test_longest_match_first(self, temp_dir: Path) -> None:
        """Test that longer matches are replaced first."""
        glossary_path = temp_dir / "glossary.json"
        glossary = Glossary(glossary_path)

        glossary.add_entry("test", "X")
        glossary.add_entry("testing", "Y")

        text = "testing"
        result = glossary.apply(text)
        # "testing" should be replaced, not "test"
        assert result == "Y"
