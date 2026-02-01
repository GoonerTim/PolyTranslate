"""Glossary editor view."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from app.utils.glossary import Glossary


class GlossaryView(ctk.CTkToplevel):
    """Window for editing the glossary."""

    def __init__(
        self,
        master: ctk.CTk,
        glossary: Glossary,
        on_save: Callable[[], None] | None = None,
    ) -> None:
        """
        Initialize the glossary view.

        Args:
            master: Parent window.
            glossary: Glossary instance.
            on_save: Callback when glossary is saved.
        """
        super().__init__(master)

        self.glossary = glossary
        self.on_save = on_save

        self.title("Glossary Editor")
        self.geometry("600x500")

        self._entry_widgets: list[tuple[ctk.CTkEntry, ctk.CTkEntry]] = []

        self._create_widgets()
        self._load_entries()

        # Center on parent
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_y() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create the widgets."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header_frame,
            text="Glossary Editor",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left")

        # Case sensitivity toggle
        self.case_sensitive_var = ctk.BooleanVar(value=self.glossary.is_case_sensitive())
        case_check = ctk.CTkCheckBox(
            header_frame,
            text="Case Sensitive",
            variable=self.case_sensitive_var,
        )
        case_check.pack(side="right", padx=10)

        # Info text
        ctk.CTkLabel(
            self,
            text="Define term replacements. Terms will be replaced after translation.",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        ).pack(padx=10, pady=5)

        # Column headers
        headers_frame = ctk.CTkFrame(self, fg_color="transparent")
        headers_frame.pack(fill="x", padx=10)

        ctk.CTkLabel(headers_frame, text="Original Term", width=220, anchor="w").pack(
            side="left", padx=5
        )
        ctk.CTkLabel(headers_frame, text="Replacement", width=220, anchor="w").pack(
            side="left", padx=5
        )

        # Scrollable entries list
        self.entries_frame = ctk.CTkScrollableFrame(self, height=300)
        self.entries_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Add entry button
        add_btn = ctk.CTkButton(self, text="+ Add Entry", command=self._add_empty_entry, width=120)
        add_btn.pack(pady=5)

        # Bottom buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, width=100).pack(
            side="right", padx=5
        )

        ctk.CTkButton(button_frame, text="Save", command=self._save_glossary, width=100).pack(
            side="right", padx=5
        )

        ctk.CTkButton(
            button_frame,
            text="Clear All",
            command=self._clear_all,
            width=100,
            fg_color="red",
            hover_color="darkred",
        ).pack(side="left", padx=5)

    def _load_entries(self) -> None:
        """Load glossary entries into the editor."""
        entries = self.glossary.get_all_entries()

        for original, replacement in entries.items():
            self._add_entry_row(original, replacement)

        # Add one empty row if no entries
        if not entries:
            self._add_empty_entry()

    def _add_entry_row(
        self, original: str = "", replacement: str = ""
    ) -> tuple[ctk.CTkEntry, ctk.CTkEntry]:
        """Add an entry row."""
        row_frame = ctk.CTkFrame(self.entries_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)

        original_entry = ctk.CTkEntry(row_frame, width=220)
        original_entry.pack(side="left", padx=5)
        if original:
            original_entry.insert(0, original)

        replacement_entry = ctk.CTkEntry(row_frame, width=220)
        replacement_entry.pack(side="left", padx=5)
        if replacement:
            replacement_entry.insert(0, replacement)

        # Delete button
        delete_btn = ctk.CTkButton(
            row_frame,
            text="X",
            command=lambda: self._delete_row(row_frame, original_entry, replacement_entry),
            width=30,
            height=28,
            fg_color="transparent",
            text_color=("gray50", "gray60"),
            hover_color=("gray70", "gray40"),
        )
        delete_btn.pack(side="left", padx=5)

        self._entry_widgets.append((original_entry, replacement_entry))
        return original_entry, replacement_entry

    def _add_empty_entry(self) -> None:
        """Add an empty entry row."""
        self._add_entry_row()

    def _delete_row(
        self,
        row_frame: ctk.CTkFrame,
        original_entry: ctk.CTkEntry,
        replacement_entry: ctk.CTkEntry,
    ) -> None:
        """Delete an entry row."""
        self._entry_widgets.remove((original_entry, replacement_entry))
        row_frame.destroy()

    def _save_glossary(self) -> None:
        """Save the glossary and close."""
        # Collect entries
        entries: dict[str, str] = {}
        for original_entry, replacement_entry in self._entry_widgets:
            original = original_entry.get().strip()
            replacement = replacement_entry.get().strip()
            if original and replacement:
                entries[original] = replacement

        # Update glossary
        self.glossary.set_entries(entries)
        self.glossary.set_case_sensitive(self.case_sensitive_var.get())
        self.glossary.save()

        # Callback
        if self.on_save:
            self.on_save()

        self.destroy()

    def _clear_all(self) -> None:
        """Clear all entries."""
        for original_entry, _replacement_entry in self._entry_widgets:
            original_entry.master.destroy()  # type: ignore[union-attr]
        self._entry_widgets.clear()
        self._add_empty_entry()
