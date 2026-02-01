from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

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

try:
    from tkinterdnd2 import TkinterDnD

    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    TkinterDnD = None


class MainWindow:
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
        if DND_AVAILABLE and TkinterDnD is not None:
            self.root = TkinterDnD.Tk()
        else:
            self.root = ctk.CTk()

        self.root.title("✨ PolyTranslate - Modern Translation Suite")
        self.root.geometry(self.settings.get_window_geometry())
        self.root.minsize(1000, 700)

        ctk.set_appearance_mode(self.settings.get_theme())
        ctk.set_default_color_theme("blue")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self) -> None:
        self._create_menu()
        self._create_toolbar()
        self._create_main_content()
        self._create_status_bar()

    def _create_menu(self) -> None:
        menu_frame = ctk.CTkFrame(self.root, height=50, corner_radius=0)
        menu_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        # Logo/Title
        title_label = ctk.CTkLabel(
            menu_frame,
            text="✨ PolyTranslate",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title_label.pack(side="left", padx=15)

        # Separator
        separator = ctk.CTkFrame(menu_frame, width=2, height=30, fg_color=("gray70", "gray30"))
        separator.pack(side="left", padx=10, pady=10)

        # File menu with icons
        ctk.CTkButton(
            menu_frame,
            text="📂 Open",
            command=self._open_file,
            width=110,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            menu_frame,
            text="⚙️ Settings",
            command=self._open_settings,
            width=110,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            menu_frame,
            text="📜 History",
            command=self._open_history,
            width=110,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            menu_frame,
            text="📚 Glossary",
            command=self._open_glossary,
            width=110,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=5)

        # Theme toggle with icon
        theme_icon = "🌙" if self.settings.get_theme() == "light" else "☀️"
        self.theme_button = ctk.CTkButton(
            menu_frame,
            text=theme_icon,
            command=self._toggle_theme,
            width=45,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=18),
        )
        self.theme_button.pack(side="right", padx=15)

    def _create_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(self.root, corner_radius=0)
        toolbar.grid(row=1, column=0, sticky="new", padx=0, pady=0)

        content = ctk.CTkFrame(toolbar, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)

        self.file_drop = FileDropZone(
            content,
            on_file_drop=self._on_file_selected,
            width=960,
            height=140,
        )
        self.file_drop.pack(pady=(0, 15))

        lang_card = ctk.CTkFrame(content, corner_radius=12)
        lang_card.pack(fill="x", pady=(0, 15))

        lang_inner = ctk.CTkFrame(lang_card, fg_color="transparent")
        lang_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            lang_inner,
            text="🌍 Language Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))

        lang_options = ctk.CTkFrame(lang_inner, fg_color="transparent")
        lang_options.pack(fill="x")

        source_frame = ctk.CTkFrame(lang_options, fg_color="transparent")
        source_frame.pack(side="left", padx=(0, 30))

        ctk.CTkLabel(
            source_frame, text="From:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        source_langs = get_source_languages()
        self.source_lang_var = ctk.StringVar(value=self.settings.get_source_language())
        self.source_lang_menu = ctk.CTkOptionMenu(
            source_frame,
            variable=self.source_lang_var,
            values=list(source_langs.keys()),
            width=180,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
        )
        self.source_lang_menu.pack()

        ctk.CTkLabel(lang_options, text="→", font=ctk.CTkFont(size=24)).pack(
            side="left", padx=10
        )

        target_frame = ctk.CTkFrame(lang_options, fg_color="transparent")
        target_frame.pack(side="left", padx=(30, 0))

        ctk.CTkLabel(
            target_frame, text="To:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        target_langs = get_target_languages()
        self.target_lang_var = ctk.StringVar(value=self.settings.get_target_language())
        self.target_lang_menu = ctk.CTkOptionMenu(
            target_frame,
            variable=self.target_lang_var,
            values=list(target_langs.keys()),
            width=180,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
        )
        self.target_lang_menu.pack()

        services_card = ctk.CTkFrame(content, corner_radius=12)
        services_card.pack(fill="x", pady=(0, 15))

        services_inner = ctk.CTkFrame(services_card, fg_color="transparent")
        services_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            services_inner,
            text="🔧 Translation Services",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))

        services_grid = ctk.CTkFrame(services_inner, fg_color="transparent")
        services_grid.pack(fill="x")

        self.service_vars: dict[str, ctk.BooleanVar] = {}
        selected = self.settings.get_selected_services()

        service_icons = {
            "deepl": "🔷",
            "yandex": "🟣",
            "google": "🔴",
            "openai": "🤖",
            "openrouter": "🌐",
            "chatgpt_proxy": "💬",
            "groq": "⚡",
            "claude": "🎭",
            "localai": "💻",
        }

        for service_id, service_name in self.SERVICES.items():
            var = ctk.BooleanVar(value=service_id in selected)
            self.service_vars[service_id] = var
            icon = service_icons.get(service_id, "•")
            cb = ctk.CTkCheckBox(
                services_grid,
                text=f"{icon} {service_name}",
                variable=var,
                width=120,
                font=ctk.CTkFont(size=12),
                corner_radius=6,
            )
            cb.pack(side="left", padx=8, pady=5)

        action_frame = ctk.CTkFrame(content, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 10))

        self.translate_button = ctk.CTkButton(
            action_frame,
            text="🚀 Translate Now",
            command=self._start_translation,
            width=200,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=("#2563eb", "#1e40af"),
            hover_color=("#1d4ed8", "#1e3a8a"),
        )
        self.translate_button.pack(side="left", padx=5)

        self.compare_button = ctk.CTkButton(
            action_frame,
            text="📊 Compare Results",
            command=self._show_comparison,
            width=150,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=14),
            state="disabled",
        )
        self.compare_button.pack(side="left", padx=5)

        self.clear_button = ctk.CTkButton(
            action_frame,
            text="🗑️ Clear",
            command=self._clear_all,
            width=120,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=14),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
        )
        self.clear_button.pack(side="left", padx=5)

        self.progress = ProgressBar(content, width=960)
        self.progress.pack(pady=(10, 0))

    def _create_main_content(self) -> None:

        content = ctk.CTkFrame(self.root, corner_radius=0)
        content.grid(row=2, column=0, sticky="nsew", padx=0, pady=(0, 0))

        # Inner container with padding
        inner = ctk.CTkFrame(content, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=(10, 15))

        # Results header
        header_frame = ctk.CTkFrame(inner, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header_frame,
            text="📝 Translation Results",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        # Tabview for results with modern styling
        self.results_tabview = ctk.CTkTabview(
            inner, corner_radius=12, segmented_button_selected_color=("#2563eb", "#1e40af")
        )
        self.results_tabview.pack(fill="both", expand=True)

        # Add initial empty tab
        self.results_tabview.add("Results")
        tab = self.results_tabview.tab("Results")

        # Initial empty state
        empty_frame = ctk.CTkFrame(tab, fg_color="transparent")
        empty_frame.pack(fill="both", expand=True, padx=40, pady=40)

        ctk.CTkLabel(
            empty_frame,
            text="📄",
            font=ctk.CTkFont(size=60),
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            empty_frame,
            text="No translations yet",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=5)

        ctk.CTkLabel(
            empty_frame,
            text="Upload a file and start translating!",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60"),
        ).pack(pady=5)

    def _create_status_bar(self) -> None:

        status_frame = ctk.CTkFrame(self.root, height=35, corner_radius=0)
        status_frame.grid(row=3, column=0, sticky="ew", padx=0, pady=0)

        # Status indicator
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="●",
            font=ctk.CTkFont(size=14),
            text_color=("#10b981", "#34d399"),
        )
        self.status_indicator.pack(side="left", padx=(15, 5))

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="✨ Ready to translate",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(side="left", padx=5)

    def _apply_settings(self) -> None:

        self.source_lang_var.set(self.settings.get_source_language())
        self.target_lang_var.set(self.settings.get_target_language())

        selected = self.settings.get_selected_services()
        for service_id, var in self.service_vars.items():
            var.set(service_id in selected)

    def _on_file_selected(self, file_path: str) -> None:

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

        self.file_drop._browse_files()

    def _open_settings(self) -> None:

        SettingsDialog(self.root, self.settings, on_save=self._on_settings_saved)

    def _on_settings_saved(self) -> None:

        self.translator.reload_services()
        self._status("Settings saved")

    def _open_history(self) -> None:

        HistoryView(self.root, self.history, on_select=self._on_history_select)

    def _on_history_select(self, entry: dict[str, Any]) -> None:

        self._translations = entry.get("translations", {})
        self._update_results()

    def _open_glossary(self) -> None:

        GlossaryView(self.root, self.glossary, on_save=self._on_glossary_saved)

    def _on_glossary_saved(self) -> None:

        self.translator.glossary = self.glossary
        self._status("Glossary saved")

    def _toggle_theme(self) -> None:

        current = self.settings.get_theme()
        new_theme = "light" if current == "dark" else "dark"
        self.settings.set_theme(new_theme)
        self.settings.save()
        ctk.set_appearance_mode(new_theme)
        theme_icon = "🌙" if new_theme == "light" else "☀️"
        self.theme_button.configure(text=theme_icon)

    def _get_selected_services(self) -> list[str]:

        return [service_id for service_id, var in self.service_vars.items() if var.get()]

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

        # Check which services are available
        available = self.translator.get_available_services()
        # Yandex and Google now work without API keys (free mode)
        free_services = {"yandex", "google", "chatgpt_proxy"}
        valid_services = [s for s in services if s in available or s in free_services]

        if not valid_services:
            self._status("⚠️ No configured services selected. Check API keys in Settings.")
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

        self._is_translating = False
        self.translate_button.configure(state="normal")
        self.compare_button.configure(state="normal")
        self.progress.set_progress(1.0)
        self.progress.set_status("Complete!")
        self._status("Translation complete")
        self._update_results()

    def _on_translation_error(self, error: str) -> None:

        self._is_translating = False
        self.translate_button.configure(state="normal")
        self.progress.reset()
        self._status(f"Error: {error}")

    def _update_results(self) -> None:

        # Remove old tabs
        for tab_name in self.results_tabview._tab_dict.copy():
            self.results_tabview.delete(tab_name)

        if not self._translations:
            self.results_tabview.add("Results")
            tab = self.results_tabview.tab("Results")

            # Empty state with nice design
            empty_frame = ctk.CTkFrame(tab, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, padx=40, pady=40)

            ctk.CTkLabel(
                empty_frame,
                text="📄",
                font=ctk.CTkFont(size=60),
            ).pack(pady=(20, 10))

            ctk.CTkLabel(
                empty_frame,
                text="No translations yet",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(pady=5)

            ctk.CTkLabel(
                empty_frame,
                text="Upload a file and start translating!",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray60"),
            ).pack(pady=5)
            return

        # Service icons
        service_icons = {
            "deepl": "🔷",
            "yandex": "🟣",
            "google": "🔴",
            "openai": "🤖",
            "openrouter": "🌐",
            "chatgpt_proxy": "💬",
            "groq": "⚡",
            "claude": "🎭",
            "localai": "💻",
        }

        # Create a tab for each service with modern design
        for service, translation in self._translations.items():
            icon = service_icons.get(service, "•")
            tab_name = f"{icon} {service.upper()}"
            self.results_tabview.add(tab_name)
            tab = self.results_tabview.tab(tab_name)

            # Stats and actions bar
            stats_frame = ctk.CTkFrame(tab, corner_radius=8, height=50)
            stats_frame.pack(fill="x", padx=10, pady=10)

            stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
            stats_inner.pack(fill="x", padx=15, pady=10)

            # Stats
            char_count = len(translation)
            word_count = len(translation.split())
            ctk.CTkLabel(
                stats_inner,
                text=f"📊 {char_count:,} chars  •  {word_count:,} words",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="left")

            # Action buttons
            copy_btn = ctk.CTkButton(
                stats_inner,
                text="📋 Copy",
                command=lambda t=translation: self._copy_to_clipboard(t),
                width=100,
                height=32,
                corner_radius=8,
                font=ctk.CTkFont(size=12),
            )
            copy_btn.pack(side="right", padx=5)

            save_btn = ctk.CTkButton(
                stats_inner,
                text="💾 Save",
                command=lambda t=translation, s=service: self._save_translation(t, s),
                width=100,
                height=32,
                corner_radius=8,
                font=ctk.CTkFont(size=12),
            )
            save_btn.pack(side="right", padx=5)

            # Text box with nice styling
            text_box = ctk.CTkTextbox(
                tab,
                wrap="word",
                corner_radius=8,
                font=ctk.CTkFont(size=13),
            )
            text_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            text_box.insert("1.0", translation)

    def _save_translation(self, text: str, service: str) -> None:

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

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._status("Copied to clipboard")

    def _show_comparison(self) -> None:

        if self._translations:
            ComparisonView(self.root, self._translations, self._current_text)

    def _clear_all(self) -> None:

        self._current_file = None
        self._current_text = ""
        self._translations = {}
        self.file_drop.clear()
        self.progress.reset()
        self.compare_button.configure(state="disabled")
        self._update_results()
        self._status("Cleared")

    def _status(self, message: str) -> None:

        self.status_label.configure(text=message)

    def _on_close(self) -> None:

        # Save window geometry
        self.settings.set_window_geometry(self.root.geometry())
        self.settings.save()
        self.root.destroy()

    def run(self) -> None:

        self.root.mainloop()
