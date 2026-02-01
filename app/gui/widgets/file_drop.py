from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk

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

        # Configure the frame with modern styling
        self.configure(
            corner_radius=15,
            border_width=3,
            border_color=("#e5e7eb", "#374151"),
        )
        self._create_widgets()
        self._setup_dnd()

    def _create_widgets(self) -> None:
        self.icon_label = ctk.CTkLabel(
            self,
            text="📎",
            font=ctk.CTkFont(size=50),
        )
        self.icon_label.pack(pady=(25, 5))

        self.text_label = ctk.CTkLabel(
            self,
            text="✨ Drag & Drop files here",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.text_label.pack(pady=5)

        self.subtitle_label = ctk.CTkLabel(
            self,
            text="or click the button below to browse",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60"),
        )
        self.subtitle_label.pack(pady=2)

        formats_short = "TXT, PDF, DOCX, PPTX, XLSX, CSV, HTML, MD, Ren'Py"
        self.formats_label = ctk.CTkLabel(
            self,
            text=f"📋 {formats_short}",
            font=ctk.CTkFont(size=11),
            text_color=("#2563eb", "#60a5fa"),
        )
        self.formats_label.pack(pady=5)

        self.browse_button = ctk.CTkButton(
            self,
            text="📂 Browse Files",
            command=self._browse_files,
            width=140,
            height=38,
            corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#2563eb", "#1e40af"),
            hover_color=("#1d4ed8", "#1e3a8a"),
        )
        self.browse_button.pack(pady=12)

    def _setup_dnd(self) -> None:
        if not DND_AVAILABLE:
            return

        root = self.winfo_toplevel()
        if hasattr(root, "drop_target_register"):
            try:
                self.drop_target_register(DND_FILES)
                self.dnd_bind("<<Drop>>", self._on_drop)
                self.dnd_bind("<<DragEnter>>", self._on_drag_enter)
                self.dnd_bind("<<DragLeave>>", self._on_drag_leave)
            except Exception:
                pass

    def _on_drop(self, event: object) -> None:
        if hasattr(event, "data"):
            file_path = str(event.data)  # type: ignore[attr-defined]

            if file_path.startswith("{") and file_path.endswith("}"):
                file_path = file_path[1:-1]

            path = Path(file_path)
            if path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                self._set_file(file_path)
            else:
                self._show_error(f"Unsupported file format: {path.suffix}")

        self._reset_appearance()

    def _on_drag_enter(self, event: object) -> None:
        self.configure(border_color=("#10b981", "#34d399"), fg_color=("#d1fae5", "#064e3b"))
        self.icon_label.configure(text="⬇️")

    def _on_drag_leave(self, event: object) -> None:
        self._reset_appearance()

    def _reset_appearance(self) -> None:
        self.configure(border_color=("#e5e7eb", "#374151"), fg_color=("gray86", "gray17"))
        self.icon_label.configure(text="📎")

    def _browse_files(self) -> None:
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
        self._current_file = file_path
        path = Path(file_path)

        self.configure(border_color=("#10b981", "#34d399"))
        self.icon_label.configure(text="✅")
        self.text_label.configure(text=f"📄 {path.name}")
        self.subtitle_label.configure(text="File loaded successfully!")
        size_text = self._format_size(path.stat().st_size)
        self.formats_label.configure(text=f"💾 Size: {size_text}")

        if self.on_file_drop:
            self.on_file_drop(file_path)

    def _show_error(self, message: str) -> None:
        self.configure(border_color=("#ef4444", "#dc2626"))
        self.icon_label.configure(text="❌")
        self.text_label.configure(text=message)
        self.subtitle_label.configure(text="Please try another file")

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size //= 1024
        return f"{size:.1f} TB"

    def get_file(self) -> str | None:
        return self._current_file

    def clear(self) -> None:
        self._current_file = None
        self._reset_appearance()
        self.text_label.configure(text="✨ Drag & Drop files here")
        self.subtitle_label.configure(text="or click the button below to browse")
        formats_short = "TXT, PDF, DOCX, PPTX, XLSX, CSV, HTML, MD, Ren'Py"
        self.formats_label.configure(text=f"📋 {formats_short}")
