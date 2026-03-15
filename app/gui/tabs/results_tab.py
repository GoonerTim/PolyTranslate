from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

if TYPE_CHECKING:
    from app.services.ai_evaluator import EvaluationResult


class ResultsTabMixin:
    SERVICE_ICONS: dict[str, str] = {
        "deepl": "\U0001f537",
        "yandex": "\U0001f7e3",
        "google": "\U0001f534",
        "openai": "\U0001f916",
        "openrouter": "\U0001f310",
        "chatgpt_proxy": "\U0001f4ac",
        "groq": "\u26a1",
        "claude": "\U0001f3ad",
        "localai": "\U0001f4bb",
        "ai_improved": "\u2728",
    }

    def _update_results(self) -> None:
        results_tab = self.results_tabview.tab("\U0001f4dd Results")
        for widget in results_tab.winfo_children():
            widget.destroy()

        if not self._translations:
            self._create_empty_state(results_tab)
            return

        service_tabview = ctk.CTkTabview(results_tab, corner_radius=8)
        service_tabview.pack(fill="both", expand=True, padx=5, pady=5)

        for service, translation in self._translations.items():
            icon = self.SERVICE_ICONS.get(service, "\u2022")
            tab_name = f"{icon} {service.upper()}"
            service_tabview.add(tab_name)
            tab = service_tabview.tab(tab_name)

            self._create_results_service_tab(tab, service, translation)

        self._update_comparison_tab()
        self._update_diff_tab()

    def _create_results_service_tab(
        self, tab: ctk.CTkFrame, service: str, translation: str
    ) -> None:
        # Stats and actions bar
        stats_frame = ctk.CTkFrame(tab, corner_radius=8, height=50)
        stats_frame.pack(fill="x", padx=10, pady=10)

        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(fill="x", padx=15, pady=10)

        char_count = len(translation)
        word_count = len(translation.split())
        ctk.CTkLabel(
            stats_inner,
            text=f"\U0001f4ca {char_count:,} chars  \u2022  {word_count:,} words",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            stats_inner,
            text="\U0001f4cb Copy",
            command=lambda t=translation: self._copy_to_clipboard(t),
            width=100,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            stats_inner,
            text="\U0001f4be Save",
            command=lambda t=translation, s=service: self._save_translation(t, s),
            width=100,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=5)

        # Rating frame if evaluation exists
        if service in self._evaluations and service != "ai_improved":
            self._create_results_rating(tab, service)

        # Editable text box
        text_box = ctk.CTkTextbox(
            tab,
            wrap="word",
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            activate_scrollbars=True,
        )
        text_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        text_box.insert("1.0", translation)
        text_box.configure(state="normal")

        def on_text_change(event: Any = None, svc: str = service, tb: Any = text_box) -> None:
            self._translations[svc] = tb.get("1.0", "end-1c")

        text_box._textbox.bind(
            "<<Modified>>",
            lambda e, tb=text_box: (  # type: ignore[attr-defined]
                on_text_change() if tb._textbox.edit_modified() else None,  # type: ignore[attr-defined]
                tb._textbox.edit_modified(False),  # type: ignore[attr-defined]
            ),
        )

    def _create_results_rating(self, tab: ctk.CTkFrame, service: str) -> None:
        eval_result: EvaluationResult = self._evaluations[service]

        rating_frame = ctk.CTkFrame(
            tab,
            fg_color=self._get_rating_color(eval_result.score),
            corner_radius=8,
        )
        rating_frame.pack(fill="x", padx=10, pady=(0, 10))

        rating_inner = ctk.CTkFrame(rating_frame, fg_color="transparent")
        rating_inner.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            rating_inner,
            text=f"\u2b50 {eval_result.score:.1f}/10",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(
            rating_inner,
            text=eval_result.explanation,
            font=ctk.CTkFont(size=11),
            wraplength=500,
            anchor="w",
            justify="left",
        ).pack(side="left", fill="x", expand=True, padx=(0, 15))

        if service == self._best_service:
            ctk.CTkLabel(
                rating_inner,
                text="\U0001f3c6 BEST",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("#10b981", "#34d399"),
            ).pack(side="right")

    def _save_translation(self, text: str, service: str) -> None:
        from tkinter import filedialog

        ext = ".txt"
        if self._current_file:
            original_ext = Path(self._current_file).suffix
            if original_ext == ".rpy":
                ext = ".rpy"

        default_name = f"translation_{service}{ext}"

        file_path = filedialog.asksaveasfilename(
            defaultextension=ext,
            initialfile=default_name,
            filetypes=[("Text files", "*.txt"), ("Ren'Py files", "*.rpy"), ("All files", "*.*")],
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text)
                self._status(f"Saved to {Path(file_path).name}")
            except Exception as e:
                self._status(f"Error saving: {e}")

    def _export_results(self) -> None:
        from tkinter import filedialog

        if not self._translations or not self._original_text:
            self._status("Nothing to export")
            return

        file_name = Path(self._current_file).name if self._current_file else ""

        file_path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            initialfile=f"export_{file_name or 'translation'}",
            filetypes=[
                ("Word Document", "*.docx"),
                ("PDF Document", "*.pdf"),
                ("XLIFF", "*.xliff"),
                ("XLIFF", "*.xlf"),
            ],
        )

        if not file_path:
            return

        try:
            from app.core.exporter import TranslationExporter

            result_path = TranslationExporter.export(
                original_text=self._original_text,
                translations=self._translations,
                source_lang=self.source_lang_var.get(),
                target_lang=self.target_lang_var.get(),
                output_path=file_path,
                file_name=file_name,
            )
            self._status(f"Exported to {result_path.name}")
        except ImportError as e:
            self._status(f"Export error: {e}")
        except Exception as e:
            self._status(f"Export failed: {e}")

    def _prepare_streaming_tabs(self, services: list[str]) -> None:
        results_tab = self.results_tabview.tab("\U0001f4dd Results")
        for widget in results_tab.winfo_children():
            widget.destroy()

        self._streaming_textboxes: dict[str, ctk.CTkTextbox] = {}

        service_tabview = ctk.CTkTabview(results_tab, corner_radius=8)
        service_tabview.pack(fill="both", expand=True, padx=5, pady=5)

        for svc in services:
            icon = self.SERVICE_ICONS.get(svc, "\u2022")
            tab_name = f"{icon} {svc.upper()}"
            service_tabview.add(tab_name)
            tab = service_tabview.tab(tab_name)

            text_box = ctk.CTkTextbox(tab, wrap="word", corner_radius=8, font=ctk.CTkFont(size=13))
            text_box.pack(fill="both", expand=True, padx=10, pady=10)
            self._streaming_textboxes[svc] = text_box

    def _append_stream_token(self, service: str, token: str) -> None:
        if hasattr(self, "_streaming_textboxes") and service in self._streaming_textboxes:
            tb = self._streaming_textboxes[service]
            tb.insert("end", token)
            tb.see("end")

    def _copy_to_clipboard(self, text: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._status("Copied to clipboard")
