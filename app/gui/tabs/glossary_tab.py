from __future__ import annotations

import customtkinter as ctk


class GlossaryTabMixin:
    def _create_glossary_content(self) -> None:
        header_frame = ctk.CTkFrame(self.glossary_tab, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            header_frame,
            text="\U0001f4da Glossary Editor",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        self.glossary_case_var = ctk.BooleanVar(value=self.glossary.is_case_sensitive())
        ctk.CTkCheckBox(
            header_frame,
            text="Case Sensitive",
            variable=self.glossary_case_var,
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=10)

        info_frame = ctk.CTkFrame(self.glossary_tab, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            info_frame,
            text="Define term replacements. Terms will be replaced after translation.",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        ).pack(anchor="w")

        headers_frame = ctk.CTkFrame(self.glossary_tab, fg_color="transparent")
        headers_frame.pack(fill="x", padx=15)

        ctk.CTkLabel(
            headers_frame,
            text="Original Term",
            width=280,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            headers_frame,
            text="Replacement",
            width=280,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=5)

        self.glossary_entries_frame = ctk.CTkScrollableFrame(self.glossary_tab, height=300)
        self.glossary_entries_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.glossary_entry_widgets: list[tuple[ctk.CTkEntry, ctk.CTkEntry]] = []

        button_frame = ctk.CTkFrame(self.glossary_tab, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkButton(
            button_frame,
            text="\u2795 Add Entry",
            command=self._add_glossary_entry,
            width=120,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="\U0001f4be Save",
            command=self._save_glossary,
            width=120,
            height=35,
            corner_radius=8,
            fg_color=("#10b981", "#34d399"),
            hover_color=("#059669", "#10b981"),
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            button_frame,
            text="\U0001f5d1\ufe0f Clear All",
            command=self._clear_glossary,
            width=120,
            height=35,
            corner_radius=8,
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c"),
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=5)

    def _refresh_glossary(self) -> None:
        for widget in self.glossary_entries_frame.winfo_children():
            widget.destroy()

        self.glossary_entry_widgets.clear()
        self.glossary_case_var.set(self.glossary.is_case_sensitive())

        entries = self.glossary.get_all_entries()

        for original, replacement in entries.items():
            self._add_glossary_row(original, replacement)

        if not entries:
            self._add_glossary_row()

    def _add_glossary_entry(self) -> None:
        self._add_glossary_row()

    def _add_glossary_row(self, original: str = "", replacement: str = "") -> None:
        row_frame = ctk.CTkFrame(self.glossary_entries_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=3)

        original_entry = ctk.CTkEntry(
            row_frame,
            width=280,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )
        original_entry.pack(side="left", padx=5)
        if original:
            original_entry.insert(0, original)

        replacement_entry = ctk.CTkEntry(
            row_frame,
            width=280,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )
        replacement_entry.pack(side="left", padx=5)
        if replacement:
            replacement_entry.insert(0, replacement)

        ctk.CTkButton(
            row_frame,
            text="\u2715",
            command=lambda: self._delete_glossary_row(row_frame, original_entry, replacement_entry),
            width=35,
            height=35,
            corner_radius=8,
            fg_color="transparent",
            text_color=("gray50", "gray60"),
            hover_color=("gray70", "gray40"),
            font=ctk.CTkFont(size=14),
        ).pack(side="left", padx=5)

        self.glossary_entry_widgets.append((original_entry, replacement_entry))

    def _delete_glossary_row(
        self,
        row_frame: ctk.CTkFrame,
        original_entry: ctk.CTkEntry,
        replacement_entry: ctk.CTkEntry,
    ) -> None:
        self.glossary_entry_widgets.remove((original_entry, replacement_entry))
        row_frame.destroy()

    def _save_glossary(self) -> None:
        entries: dict[str, str] = {}
        for original_entry, replacement_entry in self.glossary_entry_widgets:
            original = original_entry.get().strip()
            replacement = replacement_entry.get().strip()
            if original and replacement:
                entries[original] = replacement

        self.glossary.set_entries(entries)
        self.glossary.set_case_sensitive(self.glossary_case_var.get())
        self.glossary.save()

        self.translator.glossary = self.glossary
        self._status("Glossary saved \u2713")

    def _clear_glossary(self) -> None:
        for original_entry, _replacement_entry in self.glossary_entry_widgets:
            if hasattr(original_entry, "master"):
                original_entry.master.destroy()  # type: ignore[union-attr]
        self.glossary_entry_widgets.clear()
        self._add_glossary_row()
        self._status("Glossary entries cleared")
