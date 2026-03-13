"""Diff view widget — VS Code-style line-by-line diff with revert buttons."""

from __future__ import annotations

import difflib
from collections.abc import Callable
from typing import Any

import customtkinter as ctk


class DiffView(ctk.CTkFrame):
    """Line-by-line diff between original and translated text with per-line revert."""

    # Colors: (light_mode, dark_mode)
    COLOR_REMOVED_BG = ("#fecaca", "#450a0a")
    COLOR_ADDED_BG = ("#bbf7d0", "#052e16")
    COLOR_UNCHANGED_BG = ("transparent", "transparent")
    COLOR_REMOVED_FG = ("#991b1b", "#fca5a5")
    COLOR_ADDED_FG = ("#166534", "#86efac")
    COLOR_LINE_NUM = ("gray50", "gray60")

    def __init__(
        self,
        master: Any,
        on_change: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._original_lines: list[str] = []
        self._translated_lines: list[str] = []
        self._on_change = on_change

        # Header
        self._header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._header_frame.pack(fill="x", padx=5, pady=(5, 0))

        self._service_label = ctk.CTkLabel(
            self._header_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._service_label.pack(side="left", padx=5)

        self._stats_label = ctk.CTkLabel(
            self._header_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        )
        self._stats_label.pack(side="left", padx=10)

        # Legend
        legend = ctk.CTkFrame(self._header_frame, fg_color="transparent")
        legend.pack(side="right", padx=5)

        ctk.CTkLabel(
            legend, text="  removed", font=ctk.CTkFont(size=11),
            text_color=self.COLOR_REMOVED_FG,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            legend, text="  added", font=ctk.CTkFont(size=11),
            text_color=self.COLOR_ADDED_FG,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            legend, text="↩ revert line", font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        ).pack(side="left")

        # Scrollable diff content
        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self._scroll.grid_columnconfigure(1, weight=1)

    def set_diff(
        self,
        original: str,
        translated: str,
        service_name: str = "",
        service_icon: str = "",
    ) -> None:
        self._original_lines = original.splitlines(keepends=True)
        self._translated_lines = translated.splitlines(keepends=True)

        if service_name:
            label = f"{service_icon} {service_name.upper()}" if service_icon else service_name.upper()
            self._service_label.configure(text=label)

        self._render()

    def _render(self) -> None:
        for widget in self._scroll.winfo_children():
            widget.destroy()

        opcodes = difflib.SequenceMatcher(
            None, self._original_lines, self._translated_lines
        ).get_opcodes()

        added = 0
        removed = 0
        unchanged = 0
        row = 0

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                for k in range(i2 - i1):
                    self._add_line(row, i1 + k + 1, self._original_lines[i1 + k], "equal")
                    unchanged += 1
                    row += 1

            elif tag == "delete":
                for k in range(i2 - i1):
                    self._add_line(row, i1 + k + 1, self._original_lines[i1 + k], "delete")
                    removed += 1
                    row += 1

            elif tag == "insert":
                for k in range(j2 - j1):
                    self._add_line(
                        row, j1 + k + 1, self._translated_lines[j1 + k], "insert",
                        revert_idx=j1 + k,
                    )
                    added += 1
                    row += 1

            elif tag == "replace":
                orig_count = i2 - i1
                trans_count = j2 - j1

                for k in range(max(orig_count, trans_count)):
                    if k < orig_count:
                        self._add_line(row, i1 + k + 1, self._original_lines[i1 + k], "delete")
                        removed += 1
                        row += 1
                    if k < trans_count:
                        self._add_line(
                            row, j1 + k + 1, self._translated_lines[j1 + k], "insert",
                            revert_idx=j1 + k,
                            revert_original=self._original_lines[i1 + k] if k < orig_count else None,
                        )
                        added += 1
                        row += 1

        self._stats_label.configure(
            text=f"+{added}  -{removed}  ={unchanged}"
        )

    def _add_line(
        self,
        row: int,
        line_num: int,
        text: str,
        tag: str,
        revert_idx: int | None = None,
        revert_original: str | None = None,
    ) -> None:
        display_text = text.rstrip("\n\r")

        if tag == "delete":
            bg = self.COLOR_REMOVED_BG
            fg = self.COLOR_REMOVED_FG
            prefix = "-"
        elif tag == "insert":
            bg = self.COLOR_ADDED_BG
            fg = self.COLOR_ADDED_FG
            prefix = "+"
        else:
            bg = self.COLOR_UNCHANGED_BG
            fg = ("gray20", "gray80")
            prefix = " "

        line_frame = ctk.CTkFrame(self._scroll, fg_color=bg, corner_radius=0, height=26)
        line_frame.grid(row=row, column=1, sticky="ew", pady=0)
        line_frame.grid_columnconfigure(1, weight=1)

        # Line number
        ctk.CTkLabel(
            line_frame,
            text=f"{line_num:>4}",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=self.COLOR_LINE_NUM,
            width=40,
        ).grid(row=0, column=0, padx=(4, 2))

        # Prefix (+/-)
        ctk.CTkLabel(
            line_frame,
            text=prefix,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=fg,
            width=16,
        ).grid(row=0, column=1, padx=0)

        # Content
        ctk.CTkLabel(
            line_frame,
            text=display_text if display_text else " ",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=fg,
            anchor="w",
        ).grid(row=0, column=2, sticky="w", padx=(4, 0))

        # Revert button for added/replaced lines
        if tag == "insert" and revert_idx is not None:
            revert_btn = ctk.CTkButton(
                line_frame,
                text="↩",
                width=28,
                height=22,
                corner_radius=4,
                font=ctk.CTkFont(size=13),
                fg_color=("gray80", "gray30"),
                hover_color=("gray70", "gray40"),
                text_color=("gray20", "gray80"),
                command=lambda idx=revert_idx, orig=revert_original: self._revert_line(idx, orig),
            )
            revert_btn.grid(row=0, column=3, padx=(4, 4))

    def _revert_line(self, idx: int, original: str | None) -> None:
        if original is not None:
            self._translated_lines[idx] = original
        else:
            del self._translated_lines[idx]

        self._render()

        if self._on_change:
            self._on_change(self.get_translated_text())

    def get_translated_text(self) -> str:
        return "".join(self._translated_lines)
