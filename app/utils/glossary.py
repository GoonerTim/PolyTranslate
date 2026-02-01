"""Glossary management for custom term translations."""

from __future__ import annotations

import json
import re
from pathlib import Path


class Glossary:
    """Manages a glossary of terms for post-translation replacement."""

    def __init__(self, glossary_path: str | Path | None = None) -> None:
        """
        Initialize the glossary.

        Args:
            glossary_path: Path to the glossary JSON file.
        """
        if glossary_path is None:
            self.glossary_path = Path("glossary.json")
        else:
            self.glossary_path = Path(glossary_path)

        self._entries: dict[str, str] = {}
        self._case_sensitive: bool = False
        self.load()

    def load(self) -> None:
        """Load glossary from file."""
        if self.glossary_path.exists():
            try:
                with open(self.glossary_path, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._entries = data.get("entries", {})
                        self._case_sensitive = data.get("case_sensitive", False)
                    else:
                        # Legacy format: direct dict of entries
                        self._entries = data
            except (json.JSONDecodeError, OSError):
                self._entries = {}
        else:
            self._entries = {}

    def save(self) -> None:
        """Save glossary to file."""
        data = {
            "entries": self._entries,
            "case_sensitive": self._case_sensitive,
        }
        try:
            with open(self.glossary_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise ValueError(f"Failed to save glossary: {e}") from e

    def add_entry(self, original: str, replacement: str) -> None:
        """
        Add or update a glossary entry.

        Args:
            original: The original term to match.
            replacement: The replacement term.
        """
        if not original or not replacement:
            raise ValueError("Both original and replacement must be non-empty")
        self._entries[original] = replacement

    def remove_entry(self, original: str) -> bool:
        """
        Remove a glossary entry.

        Args:
            original: The original term to remove.

        Returns:
            True if the entry was removed, False if it didn't exist.
        """
        if original in self._entries:
            del self._entries[original]
            return True
        return False

    def get_entry(self, original: str) -> str | None:
        """
        Get a glossary entry.

        Args:
            original: The original term.

        Returns:
            The replacement term or None if not found.
        """
        return self._entries.get(original)

    def get_all_entries(self) -> dict[str, str]:
        """Get all glossary entries."""
        return self._entries.copy()

    def set_entries(self, entries: dict[str, str]) -> None:
        """
        Set all glossary entries at once.

        Args:
            entries: Dictionary of original -> replacement terms.
        """
        self._entries = entries.copy()

    def clear(self) -> None:
        """Clear all glossary entries."""
        self._entries.clear()

    def apply(self, text: str) -> str:
        """
        Apply glossary replacements to text.

        Args:
            text: The text to process.

        Returns:
            Text with glossary terms replaced.
        """
        if not self._entries:
            return text

        result = text

        # Sort entries by length (longest first) to avoid partial replacements
        sorted_entries = sorted(self._entries.items(), key=lambda x: len(x[0]), reverse=True)

        for original, replacement in sorted_entries:
            if self._case_sensitive:
                result = result.replace(original, replacement)
            else:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(original), re.IGNORECASE)
                result = pattern.sub(replacement, result)

        return result

    def is_case_sensitive(self) -> bool:
        """Check if glossary matching is case-sensitive."""
        return self._case_sensitive

    def set_case_sensitive(self, value: bool) -> None:
        """Set whether glossary matching is case-sensitive."""
        self._case_sensitive = value

    def import_from_dict(self, data: dict[str, str]) -> int:
        """
        Import entries from a dictionary.

        Args:
            data: Dictionary of entries to import.

        Returns:
            Number of entries imported.
        """
        count = 0
        for original, replacement in data.items():
            if original and replacement:
                self._entries[original] = replacement
                count += 1
        return count

    def export_to_dict(self) -> dict[str, str]:
        """Export entries to a dictionary."""
        return self._entries.copy()

    def __len__(self) -> int:
        """Get the number of entries."""
        return len(self._entries)

    def __contains__(self, item: str) -> bool:
        """Check if a term exists in the glossary."""
        return item in self._entries
