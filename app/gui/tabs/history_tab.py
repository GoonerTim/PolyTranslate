from __future__ import annotations

from datetime import datetime
from typing import Any

import customtkinter as ctk


class HistoryTabMixin:
    def _create_history_content(self) -> None:
        header_frame = ctk.CTkFrame(self.history_tab, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            header_frame,
            text="\U0001f4dc Translation History",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="\U0001f5d1\ufe0f Clear All",
            command=self._clear_history,
            width=120,
            height=35,
            corner_radius=8,
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c"),
            font=ctk.CTkFont(size=12),
        ).pack(side="right")

        self.history_list_frame = ctk.CTkScrollableFrame(self.history_tab)
        self.history_list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _refresh_history(self) -> None:
        for widget in self.history_list_frame.winfo_children():
            widget.destroy()

        entries = self.history.get_entries()

        if not entries:
            empty_frame = ctk.CTkFrame(self.history_list_frame, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, padx=40, pady=40)

            ctk.CTkLabel(
                empty_frame,
                text="\U0001f4dc",
                font=ctk.CTkFont(size=60),
            ).pack(pady=(20, 10))

            ctk.CTkLabel(
                empty_frame,
                text="No translation history",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(pady=5)

            ctk.CTkLabel(
                empty_frame,
                text="Your translation history will appear here",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray60"),
            ).pack(pady=5)
            return

        for idx, entry in enumerate(entries):
            self._create_history_card(idx, entry)

    def _create_history_card(self, idx: int, entry: dict[str, Any]) -> None:
        card = ctk.CTkFrame(self.history_list_frame, corner_radius=12)
        card.pack(fill="x", pady=8, padx=5)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=10)

        timestamp = entry.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                pass

        ctk.CTkLabel(
            header,
            text=f"\U0001f552 {timestamp}",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left")

        source_lang = entry.get("source_lang", "?")
        target_lang = entry.get("target_lang", "?")
        ctk.CTkLabel(
            header,
            text=f"{source_lang.upper()} \u2192 {target_lang.upper()}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#2563eb", "#60a5fa"),
        ).pack(side="left", padx=20)

        file_name = entry.get("file_name", "")
        if file_name:
            ctk.CTkLabel(
                header,
                text=f"\U0001f4c4 {file_name}",
                font=ctk.CTkFont(size=11),
            ).pack(side="left", padx=10)

        ctk.CTkButton(
            header,
            text="\u2715",
            command=lambda i=idx: self._delete_history_entry(i),
            width=30,
            height=25,
            corner_radius=6,
            fg_color="transparent",
            text_color=("gray50", "gray60"),
            hover_color=("gray70", "gray40"),
            font=ctk.CTkFont(size=14),
        ).pack(side="right")

        source_preview = entry.get("source_text", "")[:150]
        if len(entry.get("source_text", "")) > 150:
            source_preview += "..."

        ctk.CTkLabel(
            card,
            text=source_preview,
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=15, pady=(0, 5))

        services = list(entry.get("translations", {}).keys())
        if services:
            services_text = "Services: " + ", ".join(s.upper() for s in services)
            ctk.CTkLabel(
                card,
                text=services_text,
                font=ctk.CTkFont(size=10),
                text_color=("gray50", "gray60"),
            ).pack(fill="x", padx=15, pady=(0, 10))

        def select_entry(e: Any = None) -> None:
            self._on_history_select(entry)

        card.bind("<Button-1>", select_entry)
        for child in card.winfo_children():
            if not isinstance(child, ctk.CTkButton):
                child.bind("<Button-1>", select_entry)

    def _delete_history_entry(self, index: int) -> None:
        self.history.delete_entry(index)
        self._refresh_history()
        self._status("History entry deleted")

    def _clear_history(self) -> None:
        self.history.clear()
        self._refresh_history()
        self._status("History cleared")
