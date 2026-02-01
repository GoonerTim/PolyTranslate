from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import customtkinter as ctk

from app.config.languages import get_source_languages, get_target_languages
from app.config.settings import Settings
from app.core.file_processor import FileProcessor
from app.core.translator import Translator
from app.gui.history_view import TranslationHistory
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

        # Load initial content for history and glossary tabs
        self._refresh_history()
        self._refresh_glossary()

    def _create_window(self) -> None:
        if DND_AVAILABLE and TkinterDnD is not None:
            self.root = TkinterDnD.Tk()
        else:
            self.root = ctk.CTk()

        self.root.title("✨ PolyTranslate - Modern Translation Suite")
        self.root.geometry(self.settings.get_window_geometry())
        self.root.minsize(1200, 700)

        ctk.set_appearance_mode(self.settings.get_theme())
        ctk.set_default_color_theme("blue")

        self.root.columnconfigure(0, weight=1)  # Controls panel
        self.root.columnconfigure(1, weight=4)  # Main content area (results)
        self.root.rowconfigure(2, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self) -> None:
        self._create_menu()
        self._create_controls_panel()
        self._create_progress_bar()
        self._create_main_content()
        self._create_status_bar()

    def _create_menu(self) -> None:
        menu_frame = ctk.CTkFrame(self.root, height=50, corner_radius=0)
        menu_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)

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

    def _create_controls_panel(self) -> None:
        controls = ctk.CTkScrollableFrame(self.root, corner_radius=0)
        controls.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(0, 0), pady=0)

        content = ctk.CTkFrame(controls, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=10)

        # File drop zone (compact)
        self.file_drop = FileDropZone(
            content,
            on_file_drop=self._on_file_selected,
            width=280,
            height=100,
        )
        self.file_drop.pack(pady=(0, 10))

        # Language settings in 2 rows
        lang_card = ctk.CTkFrame(content, corner_radius=12)
        lang_card.pack(fill="x", pady=(0, 10))

        lang_inner = ctk.CTkFrame(lang_card, fg_color="transparent")
        lang_inner.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(
            lang_inner,
            text="🌍 Languages",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(0, 8))

        # Source language
        source_frame = ctk.CTkFrame(lang_inner, fg_color="transparent")
        source_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(
            source_frame, text="From:", font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", pady=(0, 3))
        source_langs = get_source_languages()
        self.source_lang_var = ctk.StringVar(value=self.settings.get_source_language())
        self.source_lang_menu = ctk.CTkOptionMenu(
            source_frame,
            variable=self.source_lang_var,
            values=list(source_langs.keys()),
            width=250,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )
        self.source_lang_menu.pack(fill="x")

        # Target language
        target_frame = ctk.CTkFrame(lang_inner, fg_color="transparent")
        target_frame.pack(fill="x")

        ctk.CTkLabel(
            target_frame, text="To:", font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", pady=(0, 3))
        target_langs = get_target_languages()
        self.target_lang_var = ctk.StringVar(value=self.settings.get_target_language())
        self.target_lang_menu = ctk.CTkOptionMenu(
            target_frame,
            variable=self.target_lang_var,
            values=list(target_langs.keys()),
            width=250,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )
        self.target_lang_menu.pack(fill="x")

        # Translation services in 2 columns
        services_card = ctk.CTkFrame(content, corner_radius=12)
        services_card.pack(fill="x", pady=(0, 10))

        services_inner = ctk.CTkFrame(services_card, fg_color="transparent")
        services_inner.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(
            services_inner,
            text="🔧 Services",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(0, 8))

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

        # Create checkboxes in 2-column grid
        services_list = list(self.SERVICES.items())
        for _idx, (service_id, service_name) in enumerate(services_list):
            var = ctk.BooleanVar(value=service_id in selected)
            self.service_vars[service_id] = var
            icon = service_icons.get(service_id, "•")

            row_frame = ctk.CTkFrame(services_grid, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            cb = ctk.CTkCheckBox(
                row_frame,
                text=f"{icon} {service_name}",
                variable=var,
                width=120,
                font=ctk.CTkFont(size=11),
                corner_radius=6,
            )
            cb.pack(anchor="w", padx=5)

        # Action buttons
        action_frame = ctk.CTkFrame(content, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 8))

        self.translate_button = ctk.CTkButton(
            action_frame,
            text="🚀 Translate",
            command=self._start_translation,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#2563eb", "#1e40af"),
            hover_color=("#1d4ed8", "#1e3a8a"),
        )
        self.translate_button.pack(fill="x", pady=3)

        self.compare_button = ctk.CTkButton(
            action_frame,
            text="📊 Compare",
            command=self._show_comparison,
            height=38,
            corner_radius=10,
            font=ctk.CTkFont(size=13),
            state="disabled",
        )
        self.compare_button.pack(fill="x", pady=3)

        self.clear_button = ctk.CTkButton(
            action_frame,
            text="🗑️ Clear",
            command=self._clear_all,
            height=38,
            corner_radius=10,
            font=ctk.CTkFont(size=13),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
        )
        self.clear_button.pack(fill="x", pady=3)

    def _create_progress_bar(self) -> None:
        progress_frame = ctk.CTkFrame(self.root, corner_radius=0, height=60)
        progress_frame.grid(row=1, column=1, sticky="ew", padx=0, pady=0)
        progress_frame.grid_propagate(False)

        content = ctk.CTkFrame(progress_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)

        self.progress = ProgressBar(content)
        self.progress.pack(fill="x")

    def _create_main_content(self) -> None:

        content = ctk.CTkFrame(self.root, corner_radius=0)
        content.grid(row=2, column=1, sticky="nsew", padx=0, pady=0)

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

        # Add all tabs
        self.results_tabview.add("📝 Results")
        self.results_tabview.add("📊 Comparison")
        self.results_tabview.add("📜 History")
        self.results_tabview.add("📚 Glossary")

        # Results tab with initial empty state
        results_tab = self.results_tabview.tab("📝 Results")
        self._create_empty_state(results_tab)

        # Comparison tab with initial empty state
        comparison_tab = self.results_tabview.tab("📊 Comparison")
        self._create_empty_comparison_state(comparison_tab)

        # History tab
        self.history_tab = self.results_tabview.tab("📜 History")
        self._create_history_content()

        # Glossary tab
        self.glossary_tab = self.results_tabview.tab("📚 Glossary")
        self._create_glossary_content()

    def _create_empty_state(self, parent: ctk.CTkFrame) -> None:
        empty_frame = ctk.CTkFrame(parent, fg_color="transparent")
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

    def _create_empty_comparison_state(self, parent: ctk.CTkFrame) -> None:
        empty_frame = ctk.CTkFrame(parent, fg_color="transparent")
        empty_frame.pack(fill="both", expand=True, padx=40, pady=40)

        ctk.CTkLabel(
            empty_frame,
            text="📊",
            font=ctk.CTkFont(size=60),
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            empty_frame,
            text="No translations to compare",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=5)

        ctk.CTkLabel(
            empty_frame,
            text="Complete a translation to see comparison view",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60"),
        ).pack(pady=5)

    def _create_history_content(self) -> None:
        # Header with clear button
        header_frame = ctk.CTkFrame(self.history_tab, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            header_frame,
            text="📜 Translation History",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="🗑️ Clear All",
            command=self._clear_history,
            width=120,
            height=35,
            corner_radius=8,
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c"),
            font=ctk.CTkFont(size=12),
        ).pack(side="right")

        # Scrollable list
        self.history_list_frame = ctk.CTkScrollableFrame(self.history_tab)
        self.history_list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _create_glossary_content(self) -> None:
        # Header
        header_frame = ctk.CTkFrame(self.glossary_tab, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            header_frame,
            text="📚 Glossary Editor",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        # Case sensitivity toggle
        self.glossary_case_var = ctk.BooleanVar(value=self.glossary.is_case_sensitive())
        case_check = ctk.CTkCheckBox(
            header_frame,
            text="Case Sensitive",
            variable=self.glossary_case_var,
            font=ctk.CTkFont(size=12),
        )
        case_check.pack(side="right", padx=10)

        # Info text
        info_frame = ctk.CTkFrame(self.glossary_tab, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            info_frame,
            text="Define term replacements. Terms will be replaced after translation.",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        ).pack(anchor="w")

        # Column headers
        headers_frame = ctk.CTkFrame(self.glossary_tab, fg_color="transparent")
        headers_frame.pack(fill="x", padx=15)

        ctk.CTkLabel(
            headers_frame,
            text="Original Term",
            width=280,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            headers_frame,
            text="Replacement",
            width=280,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=5)

        # Scrollable entries list
        self.glossary_entries_frame = ctk.CTkScrollableFrame(self.glossary_tab, height=300)
        self.glossary_entries_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.glossary_entry_widgets: list[tuple[ctk.CTkEntry, ctk.CTkEntry]] = []

        # Buttons
        button_frame = ctk.CTkFrame(self.glossary_tab, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkButton(
            button_frame,
            text="➕ Add Entry",
            command=self._add_glossary_entry,
            width=120,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="💾 Save",
            command=self._save_glossary,
            width=120,
            height=35,
            corner_radius=8,
            fg_color=("#10b981", "#34d399"),
            hover_color=("#059669", "#10b981"),
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            button_frame,
            text="🗑️ Clear All",
            command=self._clear_glossary,
            width=120,
            height=35,
            corner_radius=8,
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c"),
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=5)

    def _create_status_bar(self) -> None:

        status_frame = ctk.CTkFrame(self.root, height=35, corner_radius=0)
        status_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=0, pady=0)

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

        self.results_tabview.set("📜 History")
        self._refresh_history()

    def _on_history_select(self, entry: dict[str, Any]) -> None:

        self._translations = entry.get("translations", {})
        self._update_results()
        # Switch to results tab to show the loaded translations
        self.results_tabview.set("📝 Results")
        self._status("History entry loaded")

    def _open_glossary(self) -> None:

        self.results_tabview.set("📚 Glossary")
        self._refresh_glossary()


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
        # Clear Results tab content
        results_tab = self.results_tabview.tab("📝 Results")
        for widget in results_tab.winfo_children():
            widget.destroy()

        if not self._translations:
            self._create_empty_state(results_tab)
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

        # Create service tabs inside Results tab
        service_tabview = ctk.CTkTabview(results_tab, corner_radius=8)
        service_tabview.pack(fill="both", expand=True, padx=5, pady=5)

        # Create a tab for each service with modern design
        for service, translation in self._translations.items():
            icon = service_icons.get(service, "•")
            tab_name = f"{icon} {service.upper()}"
            service_tabview.add(tab_name)
            tab = service_tabview.tab(tab_name)

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

            # Text box with nice styling (scrollable and copyable, but read-only)
            text_box = ctk.CTkTextbox(
                tab,
                wrap="word",
                corner_radius=8,
                font=ctk.CTkFont(size=13),
                activate_scrollbars=True,
            )
            text_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            text_box.insert("1.0", translation)
            # Make read-only but keep text selectable for copying
            text_box.configure(state="normal")
            # Prevent editing while allowing selection and copying
            self._make_textbox_readonly(text_box)

        # Update comparison tab
        self._update_comparison_tab()

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

    def _update_comparison_tab(self) -> None:
        # Clear Comparison tab content
        comparison_tab = self.results_tabview.tab("📊 Comparison")
        for widget in comparison_tab.winfo_children():
            widget.destroy()

        if not self._translations:
            self._create_empty_comparison_state(comparison_tab)
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

        # Create scrollable container
        scroll_frame = ctk.CTkScrollableFrame(comparison_tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Calculate grid layout
        num_services = len(self._translations)
        columns = min(3, num_services)

        # Configure grid
        for i in range(columns):
            scroll_frame.grid_columnconfigure(i, weight=1, uniform="col")

        # Create comparison panels
        services = list(self._translations.items())
        for idx, (service, translation) in enumerate(services):
            row = idx // columns
            col = idx % columns

            panel = self._create_comparison_panel(
                scroll_frame, service, translation, service_icons
            )
            panel.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

    def _create_comparison_panel(
        self,
        parent: ctk.CTkFrame,
        service: str,
        text: str,
        service_icons: dict[str, str],
    ) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(parent, corner_radius=12)

        # Service name header with icon
        icon = service_icons.get(service, "•")
        header = ctk.CTkLabel(
            panel,
            text=f"{icon} {service.upper()}",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        header.pack(fill="x", padx=10, pady=(10, 5))

        # Stats
        stats_text = f"📊 {len(text):,} chars  •  {len(text.split()):,} words"
        stats = ctk.CTkLabel(
            panel,
            text=stats_text,
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        )
        stats.pack(fill="x", padx=10, pady=(0, 5))

        # Text area (scrollable and copyable)
        text_box = ctk.CTkTextbox(
            panel,
            wrap="word",
            height=300,
            font=ctk.CTkFont(size=12),
            activate_scrollbars=True,
        )
        text_box.pack(fill="both", expand=True, padx=10, pady=5)
        text_box.insert("1.0", text)
        # Keep normal state to allow text selection and copying
        text_box.configure(state="normal")
        # Prevent editing while allowing selection and copying
        self._make_textbox_readonly(text_box)

        # Copy button
        copy_btn = ctk.CTkButton(
            panel,
            text="📋 Copy",
            command=lambda t=text: self._copy_to_clipboard(t),
            width=100,
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )
        copy_btn.pack(pady=10)

        return panel

    def _show_comparison(self) -> None:

        if self._translations:
            # Switch to comparison tab
            self.results_tabview.set("📊 Comparison")

    def _clear_all(self) -> None:

        self._current_file = None
        self._current_text = ""
        self._translations = {}
        self.file_drop.clear()
        self.progress.reset()
        self.compare_button.configure(state="disabled")
        self._update_results()
        # Switch back to results tab
        self.results_tabview.set("📝 Results")
        self._status("Cleared")

    def _refresh_history(self) -> None:
        # Clear existing
        for widget in self.history_list_frame.winfo_children():
            widget.destroy()

        entries = self.history.get_entries()

        if not entries:
            empty_frame = ctk.CTkFrame(self.history_list_frame, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, padx=40, pady=40)

            ctk.CTkLabel(
                empty_frame,
                text="📜",
                font=ctk.CTkFont(size=60),
            ).pack(pady=(20, 10))

            ctk.CTkLabel(
                empty_frame,
                text="No translation history",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(pady=5)

            ctk.CTkLabel(
                empty_frame,
                text="Your translation history will appear here",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray60"),
            ).pack(pady=5)
            return

        for idx, entry in enumerate(entries):
            self._create_history_card(idx, entry)

    def _create_history_card(self, idx: int, entry: dict[str, Any]) -> None:
        card = ctk.CTkFrame(self.history_list_frame, corner_radius=12)
        card.pack(fill="x", pady=8, padx=5)

        # Header row
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=10)

        # Timestamp
        timestamp = entry.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                pass

        ctk.CTkLabel(
            header,
            text=f"🕒 {timestamp}",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left")

        # Languages
        source_lang = entry.get("source_lang", "?")
        target_lang = entry.get("target_lang", "?")
        ctk.CTkLabel(
            header,
            text=f"{source_lang.upper()} → {target_lang.upper()}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#2563eb", "#60a5fa"),
        ).pack(side="left", padx=20)

        # File name
        file_name = entry.get("file_name", "")
        if file_name:
            ctk.CTkLabel(
                header,
                text=f"📄 {file_name}",
                font=ctk.CTkFont(size=11),
            ).pack(side="left", padx=10)

        # Delete button
        delete_btn = ctk.CTkButton(
            header,
            text="✕",
            command=lambda i=idx: self._delete_history_entry(i),
            width=30,
            height=25,
            corner_radius=6,
            fg_color="transparent",
            text_color=("gray50", "gray60"),
            hover_color=("gray70", "gray40"),
            font=ctk.CTkFont(size=14),
        )
        delete_btn.pack(side="right")

        # Preview text
        source_preview = entry.get("source_text", "")[:150]
        if len(entry.get("source_text", "")) > 150:
            source_preview += "..."

        preview_label = ctk.CTkLabel(
            card,
            text=source_preview,
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
        )
        preview_label.pack(fill="x", padx=15, pady=(0, 5))

        # Services used
        services = list(entry.get("translations", {}).keys())
        if services:
            services_text = "Services: " + ", ".join(s.upper() for s in services)
            ctk.CTkLabel(
                card,
                text=services_text,
                font=ctk.CTkFont(size=10),
                text_color=("gray50", "gray60"),
            ).pack(fill="x", padx=15, pady=(0, 10))

        # Make card clickable
        def select_entry(e: Any = None) -> None:
            self._on_history_select(entry)

        card.bind("<Button-1>", select_entry)
        for child in card.winfo_children():
            if not isinstance(child, ctk.CTkButton):
                child.bind("<Button-1>", select_entry)

    def _delete_history_entry(self, index: int) -> None:
        self.history.delete_entry(index)
        self._refresh_history()
        self._status("History entry deleted")

    def _clear_history(self) -> None:
        self.history.clear()
        self._refresh_history()
        self._status("History cleared")

    def _refresh_glossary(self) -> None:
        # Clear existing
        for widget in self.glossary_entries_frame.winfo_children():
            widget.destroy()

        self.glossary_entry_widgets.clear()
        self.glossary_case_var.set(self.glossary.is_case_sensitive())

        entries = self.glossary.get_all_entries()

        for original, replacement in entries.items():
            self._add_glossary_row(original, replacement)

        # Add one empty row if no entries
        if not entries:
            self._add_glossary_row()

    def _add_glossary_entry(self) -> None:
        self._add_glossary_row()

    def _add_glossary_row(self, original: str = "", replacement: str = "") -> None:
        row_frame = ctk.CTkFrame(self.glossary_entries_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=3)

        original_entry = ctk.CTkEntry(
            row_frame,
            width=280,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )
        original_entry.pack(side="left", padx=5)
        if original:
            original_entry.insert(0, original)

        replacement_entry = ctk.CTkEntry(
            row_frame,
            width=280,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )
        replacement_entry.pack(side="left", padx=5)
        if replacement:
            replacement_entry.insert(0, replacement)

        # Delete button
        delete_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            command=lambda: self._delete_glossary_row(row_frame, original_entry, replacement_entry),
            width=35,
            height=35,
            corner_radius=8,
            fg_color="transparent",
            text_color=("gray50", "gray60"),
            hover_color=("gray70", "gray40"),
            font=ctk.CTkFont(size=14),
        )
        delete_btn.pack(side="left", padx=5)

        self.glossary_entry_widgets.append((original_entry, replacement_entry))

    def _delete_glossary_row(
        self,
        row_frame: ctk.CTkFrame,
        original_entry: ctk.CTkEntry,
        replacement_entry: ctk.CTkEntry,
    ) -> None:
        self.glossary_entry_widgets.remove((original_entry, replacement_entry))
        row_frame.destroy()

    def _save_glossary(self) -> None:
        # Collect entries
        entries: dict[str, str] = {}
        for original_entry, replacement_entry in self.glossary_entry_widgets:
            original = original_entry.get().strip()
            replacement = replacement_entry.get().strip()
            if original and replacement:
                entries[original] = replacement

        # Update glossary
        self.glossary.set_entries(entries)
        self.glossary.set_case_sensitive(self.glossary_case_var.get())
        self.glossary.save()

        # Update translator
        self.translator.glossary = self.glossary
        self._status("Glossary saved ✓")

    def _clear_glossary(self) -> None:
        for original_entry, _replacement_entry in self.glossary_entry_widgets:
            if hasattr(original_entry, 'master'):
                original_entry.master.destroy()  # type: ignore[union-attr]
        self.glossary_entry_widgets.clear()
        self._add_glossary_row()
        self._status("Glossary entries cleared")

    def _make_textbox_readonly(self, textbox: ctk.CTkTextbox) -> None:
        """Make textbox read-only while keeping text selectable and copyable."""
        def on_key(event: Any) -> str:
            # Allow Ctrl+C, Ctrl+A, and navigation keys
            if event.state & 0x0004 and event.keysym in ("c", "a", "C", "A"):  # Ctrl key
                return "continue"
            if event.keysym in (
                "Left",
                "Right",
                "Up",
                "Down",
                "Home",
                "End",
                "Prior",
                "Next",
            ):
                return "continue"
            # Block all other keys
            return "break"

        textbox._textbox.bind("<Key>", on_key)  # type: ignore[attr-defined]

    def _status(self, message: str) -> None:

        self.status_label.configure(text=message)

    def _on_close(self) -> None:

        # Save window geometry
        self.settings.set_window_geometry(self.root.geometry())
        self.settings.save()
        self.root.destroy()

    def run(self) -> None:

        self.root.mainloop()
