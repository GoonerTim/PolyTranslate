"""Comparison view for comparing translations from different services."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    pass


class ComparisonView(ctk.CTkToplevel):
    """Window for comparing translations from different services."""

    def __init__(
        self,
        master: ctk.CTk,
        translations: dict[str, str],
        original_text: str = "",
    ) -> None:
        """
        Initialize the comparison view.

        Args:
            master: Parent window.
            translations: Dictionary of service_name -> translated_text.
            original_text: The original source text.
        """
        super().__init__(master)

        self.translations = translations
        self.original_text = original_text

        self.title("Translation Comparison")
        self.geometry("1000x700")

        self._create_widgets()

        # Center on parent
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_y() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create the widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Translation Comparison",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        header.pack(pady=10)

        # Main content frame
        content = ctk.CTkFrame(self)
        content.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure grid
        num_services = len(self.translations)
        if num_services == 0:
            ctk.CTkLabel(content, text="No translations to compare").pack(pady=50)
            return

        # Calculate columns
        columns = min(3, num_services)
        rows = (num_services + columns - 1) // columns

        for i in range(columns):
            content.columnconfigure(i, weight=1)

        for i in range(rows):
            content.rowconfigure(i, weight=1)

        # Create comparison panels
        services = list(self.translations.keys())
        for idx, service in enumerate(services):
            row = idx // columns
            col = idx % columns

            panel = self._create_panel(content, service, self.translations[service])
            panel.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # Close button
        close_btn = ctk.CTkButton(self, text="Close", command=self.destroy, width=100)
        close_btn.pack(pady=10)

    def _create_panel(self, parent: ctk.CTkFrame, service: str, text: str) -> ctk.CTkFrame:
        """Create a panel for a single translation."""
        panel = ctk.CTkFrame(parent)

        # Service name header
        header = ctk.CTkLabel(
            panel,
            text=service.upper(),
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        header.pack(fill="x", padx=5, pady=5)

        # Stats
        stats_text = f"Characters: {len(text)} | Words: {len(text.split())}"
        stats = ctk.CTkLabel(
            panel,
            text=stats_text,
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
        )
        stats.pack(fill="x", padx=5)

        # Text area
        text_box = ctk.CTkTextbox(panel, wrap="word")
        text_box.pack(fill="both", expand=True, padx=5, pady=5)
        text_box.insert("1.0", text)
        text_box.configure(state="disabled")

        # Copy button
        def copy_to_clipboard() -> None:
            self.clipboard_clear()
            self.clipboard_append(text)

        copy_btn = ctk.CTkButton(panel, text="Copy", command=copy_to_clipboard, width=80, height=25)
        copy_btn.pack(pady=5)

        return panel


class ComparisonPanel(ctk.CTkFrame):
    """A panel showing side-by-side comparison of two translations."""

    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        left_title: str,
        left_text: str,
        right_title: str,
        right_text: str,
        **kwargs: object,
    ) -> None:
        """
        Initialize comparison panel.

        Args:
            master: Parent widget.
            left_title: Title for left side.
            left_text: Text for left side.
            right_title: Title for right side.
            right_text: Text for right side.
        """
        super().__init__(master, **kwargs)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # Left header
        left_header = ctk.CTkLabel(self, text=left_title, font=ctk.CTkFont(weight="bold"))
        left_header.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Right header
        right_header = ctk.CTkLabel(self, text=right_title, font=ctk.CTkFont(weight="bold"))
        right_header.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Left text
        self.left_text = ctk.CTkTextbox(self, wrap="word")
        self.left_text.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.left_text.insert("1.0", left_text)
        self.left_text.configure(state="disabled")

        # Right text
        self.right_text = ctk.CTkTextbox(self, wrap="word")
        self.right_text.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        self.right_text.insert("1.0", right_text)
        self.right_text.configure(state="disabled")
