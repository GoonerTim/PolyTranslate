"""File drop zone widget for drag and drop file handling."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    pass

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    TkinterDnD = None
    DND_FILES = None


class FileDropZone(ctk.CTkFrame):
    """A drag and drop zone for files."""

    SUPPORTED_EXTENSIONS = {
        ".txt",
        ".pdf",
        ".docx",
        ".doc",
        ".pptx",
        ".xlsx",
        ".xls",
        ".csv",
        ".html",
        ".htm",
        ".md",
        ".markdown",
        ".rpy",
    }

    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        on_file_drop: Callable[[str], None] | None = None,
        width: int = 400,
        height: int = 150,
        **kwargs: object,
    ) -> None:
        """
        Initialize the file drop zone.

        Args:
            master: Parent widget.
            on_file_drop: Callback when a file is dropped.
            width: Widget width.
            height: Widget height.
        """
        super().__init__(master, width=width, height=height, **kwargs)

        self.on_file_drop = on_file_drop
        self._current_file: str | None = None

        # Configure the frame
        self.configure(
            corner_radius=10,
            border_width=2,
            border_color=("gray70", "gray30"),
        )

        # Create inner content
        self._create_widgets()

        # Setup drag and drop if available
        self._setup_dnd()

    def _create_widgets(self) -> None:
        """Create the widgets inside the drop zone."""
        # Icon label
        self.icon_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=40),
        )
        self.icon_label.pack(pady=(20, 5))

        # Main text
        self.text_label = ctk.CTkLabel(
            self,
            text="Drag & Drop files here",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.text_label.pack(pady=5)

        # Supported formats
        formats = ", ".join(sorted(ext.upper().lstrip(".") for ext in self.SUPPORTED_EXTENSIONS))
        self.formats_label = ctk.CTkLabel(
            self,
            text=f"Supported: {formats}",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
        )
        self.formats_label.pack(pady=5)

        # Browse button
        self.browse_button = ctk.CTkButton(
            self,
            text="Browse Files",
            command=self._browse_files,
            width=120,
        )
        self.browse_button.pack(pady=10)

    def _setup_dnd(self) -> None:
        """Setup drag and drop functionality."""
        if not DND_AVAILABLE:
            return

        # Check if the root is a TkinterDnD.Tk
        root = self.winfo_toplevel()
        if hasattr(root, "drop_target_register"):
            try:
                self.drop_target_register(DND_FILES)
                self.dnd_bind("<<Drop>>", self._on_drop)
                self.dnd_bind("<<DragEnter>>", self._on_drag_enter)
                self.dnd_bind("<<DragLeave>>", self._on_drag_leave)
            except Exception:
                # DnD not properly initialized
                pass

    def _on_drop(self, event: object) -> None:
        """Handle file drop event."""
        if hasattr(event, "data"):
            # Parse the dropped file path
            file_path = str(event.data)  # type: ignore[attr-defined]

            # Handle Windows paths with curly braces
            if file_path.startswith("{") and file_path.endswith("}"):
                file_path = file_path[1:-1]

            # Validate extension
            path = Path(file_path)
            if path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                self._set_file(file_path)
            else:
                self._show_error(f"Unsupported file format: {path.suffix}")

        self._reset_appearance()

    def _on_drag_enter(self, event: object) -> None:
        """Handle drag enter event."""
        self.configure(border_color=("green", "lightgreen"))

    def _on_drag_leave(self, event: object) -> None:
        """Handle drag leave event."""
        self._reset_appearance()

    def _reset_appearance(self) -> None:
        """Reset the appearance to default."""
        self.configure(border_color=("gray70", "gray30"))

    def _browse_files(self) -> None:
        """Open file browser dialog."""
        from tkinter import filedialog

        filetypes = [
            ("All Supported", " ".join(f"*{ext}" for ext in self.SUPPORTED_EXTENSIONS)),
            ("Text files", "*.txt"),
            ("PDF files", "*.pdf"),
            ("Word documents", "*.docx *.doc"),
            ("PowerPoint", "*.pptx"),
            ("Excel files", "*.xlsx *.xls"),
            ("CSV files", "*.csv"),
            ("HTML files", "*.html *.htm"),
            ("Markdown files", "*.md *.markdown"),
            ("Ren'Py files", "*.rpy"),
            ("All files", "*.*"),
        ]

        file_path = filedialog.askopenfilename(filetypes=filetypes)
        if file_path:
            self._set_file(file_path)

    def _set_file(self, file_path: str) -> None:
        """Set the current file and update display."""
        self._current_file = file_path
        path = Path(file_path)

        # Update display
        self.text_label.configure(text=path.name)
        self.formats_label.configure(text=f"Size: {self._format_size(path.stat().st_size)}")

        # Call callback
        if self.on_file_drop:
            self.on_file_drop(file_path)

    def _show_error(self, message: str) -> None:
        """Show an error message."""
        self.text_label.configure(text=message)

    def _format_size(self, size: int) -> str:
        """Format file size in human readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size //= 1024
        return f"{size:.1f} TB"

    def get_file(self) -> str | None:
        """Get the current file path."""
        return self._current_file

    def clear(self) -> None:
        """Clear the current file."""
        self._current_file = None
        self.text_label.configure(text="Drag & Drop files here")
        formats = ", ".join(sorted(ext.upper().lstrip(".") for ext in self.SUPPORTED_EXTENSIONS))
        self.formats_label.configure(text=f"Supported: {formats}")
