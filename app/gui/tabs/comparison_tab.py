from __future__ import annotations

from typing import Any

import customtkinter as ctk

from app.gui.tabs.results_tab import ResultsTabMixin


class ComparisonTabMixin:
    def _update_comparison_tab(self) -> None:
        comparison_tab = self.results_tabview.tab("\U0001f4ca Comparison")
        for widget in comparison_tab.winfo_children():
            widget.destroy()

        if not self._translations:
            self._create_empty_comparison_state(comparison_tab)
            return

        scroll_frame = ctk.CTkScrollableFrame(comparison_tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        num_services = len(self._translations) + (1 if self._original_text else 0)
        columns = min(3, num_services)

        for i in range(columns):
            scroll_frame.grid_columnconfigure(i, weight=1, uniform="col")

        idx = 0
        if self._original_text:
            panel = self._create_comparison_panel(
                scroll_frame, "original", self._original_text, is_original=True
            )
            panel.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
            idx = 1

        for service, translation in self._translations.items():
            row = idx // columns
            col = idx % columns

            panel = self._create_comparison_panel(scroll_frame, service, translation)
            panel.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            idx += 1

    def _create_comparison_panel(
        self,
        parent: ctk.CTkFrame,
        service: str,
        text: str,
        is_original: bool = False,
    ) -> ctk.CTkFrame:
        if service == self._best_service and not is_original and service != "ai_improved":
            panel = ctk.CTkFrame(
                parent, corner_radius=12, border_width=3, border_color=("#10b981", "#34d399")
            )
        else:
            panel = ctk.CTkFrame(parent, corner_radius=12)

        if is_original:
            icon = "\U0001f4c4"
            display_name = "ORIGINAL"
            fg_color = ("#10b981", "#34d399")
        else:
            icon = ResultsTabMixin.SERVICE_ICONS.get(service, "\u2022")
            display_name = service.upper()
            fg_color = ("#2563eb", "#1e40af")

        header_frame = ctk.CTkFrame(panel, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header_frame,
            text=f"{icon} {display_name}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=fg_color,
        ).pack(side="left", anchor="w")

        if service in self._evaluations and not is_original and service != "ai_improved":
            eval_result = self._evaluations[service]

            ctk.CTkLabel(
                header_frame,
                text=f"\u2b50 {eval_result.score:.1f}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self._get_score_text_color(eval_result.score),
            ).pack(side="right", padx=10)

            if service == self._best_service:
                ctk.CTkLabel(
                    header_frame,
                    text="\U0001f3c6",
                    font=ctk.CTkFont(size=14),
                ).pack(side="right", padx=5)

        stats_text = f"\U0001f4ca {len(text):,} chars  \u2022  {len(text.split()):,} words"
        ctk.CTkLabel(
            panel,
            text=stats_text,
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        ).pack(fill="x", padx=10, pady=(0, 5))

        text_box = ctk.CTkTextbox(
            panel,
            wrap="word",
            height=300,
            font=ctk.CTkFont(size=12),
            activate_scrollbars=True,
        )
        text_box.pack(fill="both", expand=True, padx=10, pady=5)
        text_box.insert("1.0", text)

        if is_original:
            text_box.configure(state="disabled")
        else:
            text_box.configure(state="normal")

            def on_text_change(event: Any = None) -> None:
                self._translations[service] = text_box.get("1.0", "end-1c")

            text_box._textbox.bind(
                "<<Modified>>",
                lambda e: (  # type: ignore[attr-defined]
                    on_text_change() if text_box._textbox.edit_modified() else None,  # type: ignore[attr-defined]
                    text_box._textbox.edit_modified(False),  # type: ignore[attr-defined]
                ),
            )

        ctk.CTkButton(
            panel,
            text="\U0001f4cb Copy",
            command=lambda: self._copy_to_clipboard(text_box.get("1.0", "end-1c")),
            width=100,
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        ).pack(pady=10)

        return panel
