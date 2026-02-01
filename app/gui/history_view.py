"""History view for viewing past translations."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

if TYPE_CHECKING:
    pass


class TranslationHistory:
    """Manages translation history storage."""

    def __init__(self, history_path: str | Path | None = None) -> None:
        """Initialize history manager."""
        if history_path is None:
            self.history_path = Path("history.json")
        else:
            self.history_path = Path(history_path)

        self._entries: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        """Load history from file."""
        if self.history_path.exists():
            try:
                with open(self.history_path, encoding="utf-8") as f:
                    self._entries = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._entries = []
        else:
            self._entries = []

    def save(self) -> None:
        """Save history to file."""
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def add_entry(
        self,
        source_text: str,
        translations: dict[str, str],
        source_lang: str,
        target_lang: str,
        file_name: str = "",
        evaluations: dict[str, Any] | None = None,
        ai_improved: str = "",
        best_service: str = "",
    ) -> None:
        """Add a new history entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "file_name": file_name,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "source_text": source_text[:500],  # Store preview
            "translations": {k: v[:500] for k, v in translations.items()},
        }

        # Add evaluation data if provided
        if evaluations:
            entry["evaluations"] = evaluations
        if ai_improved:
            entry["ai_improved"] = ai_improved[:500]
        if best_service:
            entry["best_service"] = best_service

        self._entries.insert(0, entry)

        # Keep only last 100 entries
        if len(self._entries) > 100:
            self._entries = self._entries[:100]

        self.save()

    def get_entries(self) -> list[dict[str, Any]]:
        """Get all history entries."""
        return self._entries.copy()

    def clear(self) -> None:
        """Clear all history."""
        self._entries = []
        self.save()

    def delete_entry(self, index: int) -> bool:
        """Delete entry at index."""
        if 0 <= index < len(self._entries):
            del self._entries[index]
            self.save()
            return True
        return False


class HistoryView(ctk.CTkToplevel):
    """Window for viewing translation history."""

    def __init__(
        self,
        master: ctk.CTk,
        history: TranslationHistory,
        on_select: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        """
        Initialize the history view.

        Args:
            master: Parent window.
            history: TranslationHistory instance.
            on_select: Callback when an entry is selected.
        """
        super().__init__(master)

        self.history = history
        self.on_select = on_select

        self.title("Translation History")
        self.geometry("800x600")

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
            text="Translation History",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="Clear All",
            command=self._clear_history,
            width=100,
            fg_color="red",
            hover_color="darkred",
        ).pack(side="right")

        # Scrollable list
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Close button
        ctk.CTkButton(self, text="Close", command=self.destroy, width=100).pack(pady=10)

    def _load_entries(self) -> None:
        """Load history entries into the list."""
        # Clear existing
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        entries = self.history.get_entries()

        if not entries:
            ctk.CTkLabel(
                self.list_frame,
                text="No translation history",
                font=ctk.CTkFont(size=14),
            ).pack(pady=50)
            return

        for idx, entry in enumerate(entries):
            self._create_entry_card(idx, entry)

    def _create_entry_card(self, idx: int, entry: dict[str, Any]) -> None:
        """Create a card for a history entry."""
        card = ctk.CTkFrame(self.list_frame)
        card.pack(fill="x", pady=5, padx=5)

        # Header row
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)

        # Timestamp
        timestamp = entry.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                pass

        ctk.CTkLabel(
            header,
            text=timestamp,
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        ).pack(side="left")

        # Languages
        source_lang = entry.get("source_lang", "?")
        target_lang = entry.get("target_lang", "?")
        ctk.CTkLabel(
            header,
            text=f"{source_lang.upper()} -> {target_lang.upper()}",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left", padx=20)

        # File name
        file_name = entry.get("file_name", "")
        if file_name:
            ctk.CTkLabel(
                header,
                text=file_name,
                font=ctk.CTkFont(size=11),
            ).pack(side="left", padx=10)

        # Delete button
        delete_btn = ctk.CTkButton(
            header,
            text="X",
            command=lambda i=idx: self._delete_entry(i),
            width=30,
            height=25,
            fg_color="transparent",
            text_color=("gray50", "gray60"),
            hover_color=("gray70", "gray40"),
        )
        delete_btn.pack(side="right")

        # Preview text
        source_preview = entry.get("source_text", "")[:100]
        if len(entry.get("source_text", "")) > 100:
            source_preview += "..."

        preview_label = ctk.CTkLabel(
            card,
            text=source_preview,
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
        )
        preview_label.pack(fill="x", padx=10, pady=5)

        # Services used
        services = list(entry.get("translations", {}).keys())
        if services:
            services_text = "Services: " + ", ".join(services)
            ctk.CTkLabel(
                card,
                text=services_text,
                font=ctk.CTkFont(size=10),
                text_color=("gray50", "gray60"),
            ).pack(fill="x", padx=10, pady=(0, 5))

        # Make card clickable
        card.bind("<Button-1>", lambda e, ent=entry: self._select_entry(ent))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, ent=entry: self._select_entry(ent))

    def _select_entry(self, entry: dict[str, Any]) -> None:
        """Handle entry selection."""
        if self.on_select:
            self.on_select(entry)
        self.destroy()

    def _delete_entry(self, index: int) -> None:
        """Delete an entry."""
        self.history.delete_entry(index)
        self._load_entries()

    def _clear_history(self) -> None:
        """Clear all history."""
        self.history.clear()
        self._load_entries()
