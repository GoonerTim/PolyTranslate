"""Main application window."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from app.config.languages import get_source_languages, get_target_languages
from app.config.settings import Settings
from app.core.file_processor import FileProcessor
from app.core.translator import Translator
from app.gui.comparison_view import ComparisonView
from app.gui.glossary_view import GlossaryView
from app.gui.history_view import HistoryView, TranslationHistory
from app.gui.settings_dialog import SettingsDialog
from app.gui.widgets.file_drop import FileDropZone
from app.gui.widgets.progress import ProgressBar
from app.utils.glossary import Glossary

if TYPE_CHECKING:
    pass

try:
    from tkinterdnd2 import TkinterDnD

    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    TkinterDnD = None


class MainWindow:
    """Main application window."""

    SERVICES = {
        "deepl": "DeepL",
        "yandex": "Yandex",
        "google": "Google",
        "openai": "OpenAI",
        "openrouter": "OpenRouter",
        "chatgpt_proxy": "ChatGPT (Free)",
        "groq": "Groq",
        "claude": "Claude",
        "localai": "LocalAI",
    }

    def __init__(self) -> None:
        """Initialize the main window."""
        self.settings = Settings()
        self.translator = Translator(self.settings)
        self.glossary = Glossary()
        self.history = TranslationHistory()

        self._current_file: str | None = None
        self._current_text: str = ""
        self._translations: dict[str, str] = {}
        self._is_translating: bool = False

        self._create_window()
        self._create_widgets()
        self._apply_settings()

    def _create_window(self) -> None:
        """Create the main window."""
        # Use TkinterDnD if available for drag-drop support
        if DND_AVAILABLE and TkinterDnD is not None:
            self.root = TkinterDnD.Tk()
        else:
            self.root = ctk.CTk()

        self.root.title("Translator")
        self.root.geometry(self.settings.get_window_geometry())
        self.root.minsize(900, 600)

        # Set theme
        ctk.set_appearance_mode(self.settings.get_theme())
        ctk.set_default_color_theme("blue")

        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self) -> None:
        """Create all widgets."""
        self._create_menu()
        self._create_toolbar()
        self._create_main_content()
        self._create_status_bar()

    def _create_menu(self) -> None:
        """Create the menu bar."""
        menu_frame = ctk.CTkFrame(self.root, height=40)
        menu_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # File menu
        ctk.CTkButton(
            menu_frame,
            text="Open File",
            command=self._open_file,
            width=100,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            menu_frame,
            text="Settings",
            command=self._open_settings,
            width=100,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            menu_frame,
            text="History",
            command=self._open_history,
            width=100,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            menu_frame,
            text="Glossary",
            command=self._open_glossary,
            width=100,
        ).pack(side="left", padx=5)

        # Theme toggle
        self.theme_button = ctk.CTkButton(
            menu_frame,
            text="Dark" if self.settings.get_theme() == "light" else "Light",
            command=self._toggle_theme,
            width=80,
        )
        self.theme_button.pack(side="right", padx=5)

    def _create_toolbar(self) -> None:
        """Create the toolbar with language and service selection."""
        toolbar = ctk.CTkFrame(self.root)
        toolbar.grid(row=1, column=0, sticky="new", padx=10, pady=5)

        # File drop zone
        self.file_drop = FileDropZone(
            toolbar,
            on_file_drop=self._on_file_selected,
            width=880,
            height=120,
        )
        self.file_drop.pack(pady=10)

        # Language selection
        lang_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        lang_frame.pack(fill="x", pady=10)

        # Source language
        ctk.CTkLabel(lang_frame, text="Source:").pack(side="left", padx=5)
        source_langs = get_source_languages()
        self.source_lang_var = ctk.StringVar(value=self.settings.get_source_language())
        self.source_lang_menu = ctk.CTkOptionMenu(
            lang_frame,
            variable=self.source_lang_var,
            values=list(source_langs.keys()),
            width=150,
        )
        self.source_lang_menu.pack(side="left", padx=5)

        # Target language
        ctk.CTkLabel(lang_frame, text="Target:").pack(side="left", padx=(20, 5))
        target_langs = get_target_languages()
        self.target_lang_var = ctk.StringVar(value=self.settings.get_target_language())
        self.target_lang_menu = ctk.CTkOptionMenu(
            lang_frame,
            variable=self.target_lang_var,
            values=list(target_langs.keys()),
            width=150,
        )
        self.target_lang_menu.pack(side="left", padx=5)

        # Services selection
        services_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        services_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(services_frame, text="Services:").pack(side="left", padx=5)

        self.service_vars: dict[str, ctk.BooleanVar] = {}
        selected = self.settings.get_selected_services()

        for service_id, service_name in self.SERVICES.items():
            var = ctk.BooleanVar(value=service_id in selected)
            self.service_vars[service_id] = var
            cb = ctk.CTkCheckBox(
                services_frame,
                text=service_name,
                variable=var,
                width=100,
            )
            cb.pack(side="left", padx=5)

        # Action buttons
        action_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        action_frame.pack(fill="x", pady=10)

        self.translate_button = ctk.CTkButton(
            action_frame,
            text="Translate",
            command=self._start_translation,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.translate_button.pack(side="left", padx=5)

        self.compare_button = ctk.CTkButton(
            action_frame,
            text="Compare",
            command=self._show_comparison,
            width=100,
            state="disabled",
        )
        self.compare_button.pack(side="left", padx=5)

        self.clear_button = ctk.CTkButton(
            action_frame,
            text="Clear",
            command=self._clear_all,
            width=100,
        )
        self.clear_button.pack(side="left", padx=5)

        # Progress bar
        self.progress = ProgressBar(toolbar, width=880)
        self.progress.pack(pady=10)

    def _create_main_content(self) -> None:
        """Create the main content area with translation results."""
        content = ctk.CTkFrame(self.root)
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(150, 10))

        # Configure to fill space
        self.root.rowconfigure(1, weight=1)

        # Tabview for results
        self.results_tabview = ctk.CTkTabview(content)
        self.results_tabview.pack(fill="both", expand=True, padx=5, pady=5)

        # Add initial empty tab
        self.results_tabview.add("Results")
        self.result_text = ctk.CTkTextbox(self.results_tabview.tab("Results"), wrap="word")
        self.result_text.pack(fill="both", expand=True)
        self.result_text.insert("1.0", "Translation results will appear here...")
        self.result_text.configure(state="disabled")

    def _create_status_bar(self) -> None:
        """Create the status bar."""
        status_frame = ctk.CTkFrame(self.root, height=30)
        status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=11),
        )
        self.status_label.pack(side="left", padx=10)

    def _apply_settings(self) -> None:
        """Apply settings to the UI."""
        self.source_lang_var.set(self.settings.get_source_language())
        self.target_lang_var.set(self.settings.get_target_language())

        selected = self.settings.get_selected_services()
        for service_id, var in self.service_vars.items():
            var.set(service_id in selected)

    def _on_file_selected(self, file_path: str) -> None:
        """Handle file selection."""
        self._current_file = file_path
        self._status(f"File loaded: {Path(file_path).name}")

        try:
            self._current_text = FileProcessor.process_file(file_path)
            char_count = len(self._current_text)
            word_count = len(self._current_text.split())
            self._status(f"Loaded {char_count:,} characters, {word_count:,} words")
        except Exception as e:
            self._status(f"Error loading file: {e}")
            self._current_text = ""

    def _open_file(self) -> None:
        """Open file browser."""
        self.file_drop._browse_files()

    def _open_settings(self) -> None:
        """Open settings dialog."""
        SettingsDialog(self.root, self.settings, on_save=self._on_settings_saved)

    def _on_settings_saved(self) -> None:
        """Handle settings saved."""
        self.translator.reload_services()
        self._status("Settings saved")

    def _open_history(self) -> None:
        """Open history view."""
        HistoryView(self.root, self.history, on_select=self._on_history_select)

    def _on_history_select(self, entry: dict[str, Any]) -> None:
        """Handle history entry selection."""
        self._translations = entry.get("translations", {})
        self._update_results()

    def _open_glossary(self) -> None:
        """Open glossary editor."""
        GlossaryView(self.root, self.glossary, on_save=self._on_glossary_saved)

    def _on_glossary_saved(self) -> None:
        """Handle glossary saved."""
        self.translator.glossary = self.glossary
        self._status("Glossary saved")

    def _toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        current = self.settings.get_theme()
        new_theme = "light" if current == "dark" else "dark"
        self.settings.set_theme(new_theme)
        self.settings.save()
        ctk.set_appearance_mode(new_theme)
        self.theme_button.configure(text="Dark" if new_theme == "light" else "Light")

    def _get_selected_services(self) -> list[str]:
        """Get list of selected services."""
        return [service_id for service_id, var in self.service_vars.items() if var.get()]

    def _start_translation(self) -> None:
        """Start the translation process."""
        if self._is_translating:
            return

        if not self._current_text:
            self._status("No file loaded")
            return

        services = self._get_selected_services()
        if not services:
            self._status("No services selected")
            return

        # Check which services are available
        available = self.translator.get_available_services()
        valid_services = [s for s in services if s in available or s == "chatgpt_proxy"]

        if not valid_services:
            self._status("No configured services selected. Check API keys in Settings.")
            return

        self._is_translating = True
        self.translate_button.configure(state="disabled")
        self.progress.reset()

        # Save language preferences
        self.settings.set_source_language(self.source_lang_var.get())
        self.settings.set_target_language(self.target_lang_var.get())
        self.settings.set_selected_services(services)
        self.settings.save()

        # Run translation in thread
        thread = threading.Thread(target=self._run_translation, args=(valid_services,))
        thread.daemon = True
        thread.start()

    def _run_translation(self, services: list[str]) -> None:
        """Run translation in background thread."""
        source_lang = self.source_lang_var.get()
        target_lang = self.target_lang_var.get()

        # Auto-detect language if needed
        if source_lang == "auto":
            detected = self.translator.detect_language(self._current_text[:1000])
            if detected:
                source_lang = detected
                self.root.after(0, lambda: self._status(f"Detected language: {source_lang}"))
            else:
                source_lang = "en"  # Default fallback

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

            # Save to history
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
        """Handle translation completion."""
        self._is_translating = False
        self.translate_button.configure(state="normal")
        self.compare_button.configure(state="normal")
        self.progress.set_progress(1.0)
        self.progress.set_status("Complete!")
        self._status("Translation complete")
        self._update_results()

    def _on_translation_error(self, error: str) -> None:
        """Handle translation error."""
        self._is_translating = False
        self.translate_button.configure(state="normal")
        self.progress.reset()
        self._status(f"Error: {error}")

    def _update_results(self) -> None:
        """Update the results tabs."""
        # Remove old tabs
        for tab_name in self.results_tabview._tab_dict.copy():
            self.results_tabview.delete(tab_name)

        if not self._translations:
            self.results_tabview.add("Results")
            text_box = ctk.CTkTextbox(self.results_tabview.tab("Results"), wrap="word")
            text_box.pack(fill="both", expand=True)
            text_box.insert("1.0", "No translations available")
            text_box.configure(state="disabled")
            return

        # Create a tab for each service
        for service, translation in self._translations.items():
            self.results_tabview.add(service.upper())
            tab = self.results_tabview.tab(service.upper())

            # Stats frame
            stats_frame = ctk.CTkFrame(tab, fg_color="transparent", height=30)
            stats_frame.pack(fill="x", padx=5, pady=5)

            char_count = len(translation)
            word_count = len(translation.split())
            ctk.CTkLabel(
                stats_frame,
                text=f"Characters: {char_count:,} | Words: {word_count:,}",
                font=ctk.CTkFont(size=11),
            ).pack(side="left")

            # Save button
            save_btn = ctk.CTkButton(
                stats_frame,
                text="Save",
                command=lambda t=translation, s=service: self._save_translation(t, s),
                width=80,
            )
            save_btn.pack(side="right", padx=5)

            # Copy button
            copy_btn = ctk.CTkButton(
                stats_frame,
                text="Copy",
                command=lambda t=translation: self._copy_to_clipboard(t),
                width=80,
            )
            copy_btn.pack(side="right", padx=5)

            # Text box
            text_box = ctk.CTkTextbox(tab, wrap="word")
            text_box.pack(fill="both", expand=True, padx=5, pady=5)
            text_box.insert("1.0", translation)

    def _save_translation(self, text: str, service: str) -> None:
        """Save translation to file."""
        from tkinter import filedialog

        # Determine extension based on original file
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

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._status("Copied to clipboard")

    def _show_comparison(self) -> None:
        """Show comparison view."""
        if self._translations:
            ComparisonView(self.root, self._translations, self._current_text)

    def _clear_all(self) -> None:
        """Clear all data."""
        self._current_file = None
        self._current_text = ""
        self._translations = {}
        self.file_drop.clear()
        self.progress.reset()
        self.compare_button.configure(state="disabled")
        self._update_results()
        self._status("Cleared")

    def _status(self, message: str) -> None:
        """Update status bar."""
        self.status_label.configure(text=message)

    def _on_close(self) -> None:
        """Handle window close."""
        # Save window geometry
        self.settings.set_window_geometry(self.root.geometry())
        self.settings.save()
        self.root.destroy()

    def run(self) -> None:
        """Run the application."""
        self.root.mainloop()
