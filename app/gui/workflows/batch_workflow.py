from __future__ import annotations

import threading
from pathlib import Path

import customtkinter as ctk

from app.core.batch_translator import BatchFileResult, BatchProgress, BatchTranslator
from app.core.file_processor import FileProcessor


class BatchWorkflowMixin:
    def _translate_folder(self) -> None:
        from tkinter import filedialog, messagebox

        if self._is_translating:
            return

        directory = filedialog.askdirectory(title="Select folder to translate")
        if not directory:
            return

        services = self._get_selected_services()
        if not services:
            self._status("No services selected")
            return

        available = self.translator.get_available_services()
        free_services = {"yandex", "google", "chatgpt_proxy"}
        valid_services = [s for s in services if s in available or s in free_services]
        if not valid_services:
            self._status("No configured services selected")
            return

        batch = BatchTranslator(self.translator)
        files = batch.find_files(Path(directory))

        if not files:
            all_ext = {"." + e for e in FileProcessor.SUPPORTED_EXTENSIONS}
            files = batch.find_files(Path(directory), all_ext)

        if not files:
            messagebox.showinfo("No files", f"No translatable files found in:\n{directory}")
            return

        extensions_found = {f.suffix for f in files}
        file_list = "\n".join(f"  {f.name}" for f in files[:10])
        if len(files) > 10:
            file_list += f"\n  ... and {len(files) - 10} more"

        msg = (
            f"Found {len(files)} file(s) ({', '.join(extensions_found)}):\n\n"
            f"{file_list}\n\n"
            f"Target language: {self.target_lang_var.get()}\n"
            f"Services: {', '.join(valid_services)}\n\n"
            f"Continue?"
        )
        if not messagebox.askyesno("Translate Folder", msg):
            return

        self._is_translating = True
        self.translate_button.configure(state="disabled")
        self.progress.reset()

        self.settings.set_source_language(self.source_lang_var.get())
        self.settings.set_target_language(self.target_lang_var.get())
        self.settings.set_selected_services(services)
        self.settings.save()

        thread = threading.Thread(
            target=self._run_folder_translation,
            args=(Path(directory), valid_services, files),
        )
        thread.daemon = True
        thread.start()

    def _run_folder_translation(
        self, directory: Path, services: list[str], files: list[Path]
    ) -> None:
        source_lang = self.source_lang_var.get()
        target_lang = self.target_lang_var.get()

        if source_lang == "auto":
            source_lang = "en"

        batch = BatchTranslator(self.translator)
        total_files = len(files)

        def on_progress(progress: BatchProgress) -> None:
            idx = progress.current_file_index
            overall = (idx + (1.0 if progress.file_completed else 0.5)) / total_files
            status = f"[{idx + 1}/{total_files}] {progress.current_file_name}"
            if progress.file_completed:
                status += " \u2713"
            self.root.after(0, lambda: self.progress.set_progress(overall))
            self.root.after(0, lambda s=status: self.progress.set_status(s))

        try:
            results = batch.translate_folder(
                directory=directory,
                source_lang=source_lang,
                target_lang=target_lang,
                services=services,
                chunk_size=self.settings.get_chunk_size(),
                max_workers=self.settings.get_max_workers(),
                progress_callback=on_progress,
            )
            self.root.after(0, lambda: self._on_folder_translation_complete(results))
        except Exception as e:
            self.root.after(0, lambda err=str(e): self._on_translation_error(err))

    def _on_folder_translation_complete(self, results: list[BatchFileResult]) -> None:
        self._is_translating = False
        self.translate_button.configure(state="normal")
        self.progress.set_progress(1.0)
        self.progress.set_status("Batch complete!")

        succeeded = sum(1 for r in results if r.success and not r.error)
        skipped = sum(1 for r in results if r.success and r.error)
        failed = sum(1 for r in results if not r.success)

        summary = f"Batch: {succeeded} translated, {skipped} skipped, {failed} failed"
        self._status(summary)

        results_tab = self.results_tabview.tab("\U0001f4dd Results")
        for widget in results_tab.winfo_children():
            widget.destroy()

        scroll = ctk.CTkScrollableFrame(results_tab)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        summary_card = ctk.CTkFrame(scroll, corner_radius=12)
        summary_card.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(
            summary_card,
            text="\U0001f4c1 Batch Translation Results",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=15, pady=(15, 5))
        ctk.CTkLabel(
            summary_card,
            text=f"{succeeded} translated  |  {skipped} skipped  |  {failed} failed",
            font=ctk.CTkFont(size=13),
        ).pack(padx=15, pady=(0, 15))

        for r in results:
            color = ("#10b981", "#34d399") if r.success else ("#ef4444", "#dc2626")
            card = ctk.CTkFrame(scroll, corner_radius=10)
            card.pack(fill="x", padx=10, pady=3)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=8)

            icon = "\u2713" if r.success else "\u2717"
            ctk.CTkLabel(
                inner,
                text=icon,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=color,
            ).pack(side="left", padx=(0, 8))

            ctk.CTkLabel(
                inner,
                text=str(r.source_path.name),
                font=ctk.CTkFont(size=12),
            ).pack(side="left")

            if r.output_path:
                ctk.CTkLabel(
                    inner,
                    text=f"\u2192 {r.output_path.name}",
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray60"),
                ).pack(side="left", padx=10)

            if r.error:
                ctk.CTkLabel(
                    inner,
                    text=r.error,
                    font=ctk.CTkFont(size=11),
                    text_color=color,
                ).pack(side="right")

        self.results_tabview.set("\U0001f4dd Results")
