from __future__ import annotations

import threading
from pathlib import Path


class TranslationWorkflowMixin:
    def _start_translation(self) -> None:
        if self._is_translating:
            return

        if not self._current_text:
            self._status("No file loaded")
            return

        services = self._get_selected_services()
        if not services:
            self._status("No services selected")
            return

        available = self.translator.get_available_services()
        free_services = {"yandex", "google", "chatgpt_proxy"}
        valid_services = [s for s in services if s in available or s in free_services]

        if not valid_services:
            self._status(
                "\u26a0\ufe0f No configured services selected. Check API keys in Settings."
            )
            return

        self._is_translating = True
        self.translate_button.configure(state="disabled")
        self.progress.reset()

        self.settings.set_source_language(self.source_lang_var.get())
        self.settings.set_target_language(self.target_lang_var.get())
        self.settings.set_selected_services(services)
        self.settings.save()

        thread = threading.Thread(target=self._run_translation, args=(valid_services,))
        thread.daemon = True
        thread.start()

    def _run_translation(self, services: list[str]) -> None:
        source_lang = self.source_lang_var.get()
        target_lang = self.target_lang_var.get()

        self._original_text = self._current_text

        if source_lang == "auto":
            detected = self.translator.detect_language(self._current_text[:1000])
            if detected:
                source_lang = detected
                self.root.after(0, lambda: self._status(f"Detected language: {source_lang}"))
            else:
                source_lang = "en"

        def progress_callback(completed: int, total: int) -> None:
            progress = completed / total if total > 0 else 0
            self.root.after(0, lambda: self.progress.set_progress(progress))
            self.root.after(
                0, lambda: self.progress.set_status(f"Translating... {completed}/{total}")
            )

        try:
            self._translations = self.translator.translate_parallel(
                self._current_text,
                source_lang,
                target_lang,
                services,
                chunk_size=self.settings.get_chunk_size(),
                max_workers=self.settings.get_max_workers(),
                progress_callback=progress_callback,
            )

            file_name = Path(self._current_file).name if self._current_file else ""
            self.history.add_entry(
                self._current_text,
                self._translations,
                source_lang,
                target_lang,
                file_name,
            )

            self.root.after(0, self._on_translation_complete)
        except Exception as e:
            self.root.after(0, lambda err=str(e): self._on_translation_error(err))

    def _on_translation_complete(self) -> None:
        self._is_translating = False
        self.translate_button.configure(state="normal")
        self.compare_button.configure(state="normal")
        self.progress.set_progress(1.0)
        self.progress.set_status("Complete!")
        self._status("Translation complete")
        self._update_results()

        evaluator_service = self.settings.get("ai_evaluator_service", "")
        if evaluator_service and len(self._translations) > 0:
            self.evaluate_button.configure(state="normal")

    def _on_translation_error(self, error: str) -> None:
        self._is_translating = False
        self.translate_button.configure(state="normal")
        self.progress.reset()
        self._status(f"Error: {error}")
