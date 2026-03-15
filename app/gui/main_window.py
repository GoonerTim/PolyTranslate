from __future__ import annotations

from pathlib import Path
from typing import Any

import customtkinter as ctk

from app.config.languages import get_source_languages, get_target_languages
from app.config.settings import Settings
from app.core.file_processor import FileProcessor
from app.core.renpy_context import RenpyContextExtractor
from app.core.translator import Translator
from app.gui.history_view import TranslationHistory
from app.gui.settings_dialog import SettingsDialog
from app.gui.tabs import (
    ComparisonTabMixin,
    DiffTabMixin,
    EvaluationTabMixin,
    GlossaryTabMixin,
    HistoryTabMixin,
    ResultsTabMixin,
)
from app.gui.widgets.file_drop import FileDropZone
from app.gui.widgets.progress import ProgressBar
from app.gui.workflows import (
    BatchWorkflowMixin,
    EvaluationWorkflowMixin,
    TranslationWorkflowMixin,
)
from app.services.agent_voting import VotingResult
from app.services.ai_evaluator import AIEvaluator, EvaluationResult
from app.utils.glossary import Glossary

try:
    from tkinterdnd2 import TkinterDnD

    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    TkinterDnD = None


class MainWindow(
    ResultsTabMixin,
    ComparisonTabMixin,
    DiffTabMixin,
    EvaluationTabMixin,
    HistoryTabMixin,
    GlossaryTabMixin,
    TranslationWorkflowMixin,
    EvaluationWorkflowMixin,
    BatchWorkflowMixin,
):
    BUILTIN_SERVICES = {
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

        # Merge built-in + plugin services for GUI display
        self.SERVICES = dict(self.BUILTIN_SERVICES)
        for sid, svc in self.translator.services.items():
            if sid not in self.SERVICES:
                self.SERVICES[sid] = svc.get_name()
        self.glossary = Glossary()
        self.history = TranslationHistory()

        self._current_file: str | None = None
        self._current_text: str = ""
        self._original_text: str = ""
        self._translations: dict[str, str] = {}
        self._is_translating: bool = False

        # AI Evaluation storage
        self._evaluations: dict[str, EvaluationResult] = {}
        self._ai_improved_translation: str = ""
        self._best_service: str = ""
        self._ai_evaluator: AIEvaluator | None = None
        self._voting_result: VotingResult | None = None
        self._renpy_context_extractor: RenpyContextExtractor | None = None

        self._create_window()
        self._create_widgets()
        self._apply_settings()

        self._refresh_history()
        self._refresh_glossary()

    # ── Window setup ─────────────────────────────────────────────

    def _create_window(self) -> None:
        if DND_AVAILABLE and TkinterDnD is not None:
            self.root = TkinterDnD.Tk()
        else:
            self.root = ctk.CTk()

        self.root.title("\u2728 PolyTranslate - Modern Translation Suite")
        self.root.geometry(self.settings.get_window_geometry())
        self.root.minsize(1200, 700)

        ctk.set_appearance_mode(self.settings.get_theme())
        ctk.set_default_color_theme("blue")

        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=4)
        self.root.rowconfigure(2, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self) -> None:
        self._create_menu()
        self._create_controls_panel()
        self._create_progress_bar()
        self._create_main_content()
        self._create_status_bar()

    # ── Menu bar ─────────────────────────────────────────────────

    def _create_menu(self) -> None:
        menu_frame = ctk.CTkFrame(self.root, height=50, corner_radius=0)
        menu_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)

        ctk.CTkLabel(
            menu_frame,
            text="\u2728 PolyTranslate",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=15)

        ctk.CTkFrame(menu_frame, width=2, height=30, fg_color=("gray70", "gray30")).pack(
            side="left", padx=10, pady=10
        )

        menu_buttons = [
            ("\U0001f4c2 Open", self._open_file, 110),
            ("\U0001f4c1 Translate Folder", self._translate_folder, 160),
            ("\U0001f4e4 Export", self._export_results, 110),
            ("\u2699\ufe0f Settings", self._open_settings, 110),
            ("\U0001f4dc History", self._open_history, 110),
            ("\U0001f4da Glossary", self._open_glossary, 110),
        ]

        for text, command, width in menu_buttons:
            ctk.CTkButton(
                menu_frame,
                text=text,
                command=command,
                width=width,
                height=35,
                corner_radius=8,
                font=ctk.CTkFont(size=13),
            ).pack(side="left", padx=5)

        theme_icon = "\U0001f319" if self.settings.get_theme() == "light" else "\u2600\ufe0f"
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

    # ── Controls panel (left sidebar) ────────────────────────────

    def _create_controls_panel(self) -> None:
        controls = ctk.CTkScrollableFrame(self.root, corner_radius=0)
        controls.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(0, 0), pady=0)

        content = ctk.CTkFrame(controls, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=10)

        # File drop zone
        self.file_drop = FileDropZone(
            content,
            on_file_drop=self._on_file_selected,
            width=280,
            height=100,
        )
        self.file_drop.pack(pady=(0, 10))

        # Language settings
        self._create_language_card(content)

        # Service checkboxes
        self._create_services_card(content)

        # Action buttons
        self._create_action_buttons(content)

    def _create_language_card(self, parent: ctk.CTkFrame) -> None:
        lang_card = ctk.CTkFrame(parent, corner_radius=12)
        lang_card.pack(fill="x", pady=(0, 10))

        lang_inner = ctk.CTkFrame(lang_card, fg_color="transparent")
        lang_inner.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(
            lang_inner,
            text="\U0001f30d Languages",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(0, 8))

        # Source language
        source_frame = ctk.CTkFrame(lang_inner, fg_color="transparent")
        source_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(source_frame, text="From:", font=ctk.CTkFont(size=11, weight="bold")).pack(
            anchor="w", pady=(0, 3)
        )
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

        ctk.CTkLabel(target_frame, text="To:", font=ctk.CTkFont(size=11, weight="bold")).pack(
            anchor="w", pady=(0, 3)
        )
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

    def _create_services_card(self, parent: ctk.CTkFrame) -> None:
        services_card = ctk.CTkFrame(parent, corner_radius=12)
        services_card.pack(fill="x", pady=(0, 10))

        services_inner = ctk.CTkFrame(services_card, fg_color="transparent")
        services_inner.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(
            services_inner,
            text="\U0001f527 Services",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(0, 8))

        services_grid = ctk.CTkFrame(services_inner, fg_color="transparent")
        services_grid.pack(fill="x")

        self.service_vars: dict[str, ctk.BooleanVar] = {}
        selected = self.settings.get_selected_services()

        service_icons = {
            "deepl": "\U0001f537",
            "yandex": "\U0001f7e3",
            "google": "\U0001f534",
            "openai": "\U0001f916",
            "openrouter": "\U0001f310",
            "chatgpt_proxy": "\U0001f4ac",
            "groq": "\u26a1",
            "claude": "\U0001f3ad",
            "localai": "\U0001f4bb",
        }

        for _idx, (service_id, service_name) in enumerate(self.SERVICES.items()):
            var = ctk.BooleanVar(value=service_id in selected)
            self.service_vars[service_id] = var
            icon = service_icons.get(service_id, "\u2022")

            row_frame = ctk.CTkFrame(services_grid, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            ctk.CTkCheckBox(
                row_frame,
                text=f"{icon} {service_name}",
                variable=var,
                width=120,
                font=ctk.CTkFont(size=11),
                corner_radius=6,
            ).pack(anchor="w", padx=5)

    def _create_action_buttons(self, parent: ctk.CTkFrame) -> None:
        action_frame = ctk.CTkFrame(parent, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 8))

        self.translate_button = ctk.CTkButton(
            action_frame,
            text="\U0001f680 Translate",
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
            text="\U0001f4ca Compare",
            command=self._show_comparison,
            height=38,
            corner_radius=10,
            font=ctk.CTkFont(size=13),
            state="disabled",
        )
        self.compare_button.pack(fill="x", pady=3)

        self.evaluate_button = ctk.CTkButton(
            action_frame,
            text="\U0001f916 Evaluate All",
            command=self._start_evaluation,
            height=38,
            corner_radius=10,
            font=ctk.CTkFont(size=13),
            fg_color=("#9333ea", "#7c3aed"),
            hover_color=("#7c3aed", "#6d28d9"),
            state="disabled",
        )
        self.evaluate_button.pack(fill="x", pady=3)

        self.clear_button = ctk.CTkButton(
            action_frame,
            text="\U0001f5d1\ufe0f Clear",
            command=self._clear_all,
            height=38,
            corner_radius=10,
            font=ctk.CTkFont(size=13),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
        )
        self.clear_button.pack(fill="x", pady=3)

    # ── Progress bar ─────────────────────────────────────────────

    def _create_progress_bar(self) -> None:
        progress_frame = ctk.CTkFrame(self.root, corner_radius=0, height=60)
        progress_frame.grid(row=1, column=1, sticky="ew", padx=0, pady=0)
        progress_frame.grid_propagate(False)

        content = ctk.CTkFrame(progress_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)

        self.progress = ProgressBar(content)
        self.progress.pack(fill="x")

    # ── Main content (tabs) ──────────────────────────────────────

    def _create_main_content(self) -> None:
        content = ctk.CTkFrame(self.root, corner_radius=0)
        content.grid(row=2, column=1, sticky="nsew", padx=0, pady=0)

        inner = ctk.CTkFrame(content, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=(10, 15))

        header_frame = ctk.CTkFrame(inner, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header_frame,
            text="\U0001f4dd Translation Results",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        self.results_tabview = ctk.CTkTabview(
            inner, corner_radius=12, segmented_button_selected_color=("#2563eb", "#1e40af")
        )
        self.results_tabview.pack(fill="both", expand=True)

        tab_names = [
            "\U0001f4dd Results",
            "\U0001f4ca Comparison",
            "\U0001f500 Diff",
            "\U0001f916 AI Evaluation",
            "\U0001f4dc History",
            "\U0001f4da Glossary",
        ]
        for name in tab_names:
            self.results_tabview.add(name)

        # Empty states
        self._create_empty_state(self.results_tabview.tab("\U0001f4dd Results"))
        self._create_empty_ai_eval_state(self.results_tabview.tab("\U0001f916 AI Evaluation"))
        self._create_empty_comparison_state(self.results_tabview.tab("\U0001f4ca Comparison"))
        self._create_empty_diff_state(self.results_tabview.tab("\U0001f500 Diff"))

        # History & Glossary tabs
        self.history_tab = self.results_tabview.tab("\U0001f4dc History")
        self._create_history_content()

        self.glossary_tab = self.results_tabview.tab("\U0001f4da Glossary")
        self._create_glossary_content()

    # ── Empty states ─────────────────────────────────────────────

    def _create_empty_state(self, parent: ctk.CTkFrame) -> None:
        self._create_empty_placeholder(
            parent, "\U0001f4c4", "No translations yet", "Upload a file and start translating!"
        )

    def _create_empty_comparison_state(self, parent: ctk.CTkFrame) -> None:
        self._create_empty_placeholder(
            parent,
            "\U0001f4ca",
            "No translations to compare",
            "Complete a translation to see comparison view",
        )

    def _create_empty_diff_state(self, parent: ctk.CTkFrame) -> None:
        self._create_empty_placeholder(
            parent,
            "\U0001f500",
            "No diff to display",
            "Translate text to see a line-by-line diff with the original.\n"
            "Click \u21a9 on any line to revert it back.",
        )

    def _create_empty_ai_eval_state(self, parent: ctk.CTkFrame) -> None:
        empty_frame = ctk.CTkFrame(parent, fg_color="transparent")
        empty_frame.pack(fill="both", expand=True, padx=40, pady=40)

        ctk.CTkLabel(empty_frame, text="\U0001f916", font=ctk.CTkFont(size=60)).pack(pady=(20, 10))
        ctk.CTkLabel(
            empty_frame,
            text="No AI evaluations yet",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=5)
        ctk.CTkLabel(
            empty_frame,
            text="Translate text and click '\U0001f916 Evaluate All' to get AI-powered ratings",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60"),
        ).pack(pady=5)
        ctk.CTkLabel(
            empty_frame,
            text="Configure AI Evaluator service in Settings > AI Evaluation Settings",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
        ).pack(pady=(15, 5))

    @staticmethod
    def _create_empty_placeholder(
        parent: ctk.CTkFrame, icon: str, title: str, subtitle: str
    ) -> None:
        empty_frame = ctk.CTkFrame(parent, fg_color="transparent")
        empty_frame.pack(fill="both", expand=True, padx=40, pady=40)

        ctk.CTkLabel(empty_frame, text=icon, font=ctk.CTkFont(size=60)).pack(pady=(20, 10))
        ctk.CTkLabel(empty_frame, text=title, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=5)
        ctk.CTkLabel(
            empty_frame,
            text=subtitle,
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60"),
        ).pack(pady=5)

    # ── Status bar ───────────────────────────────────────────────

    def _create_status_bar(self) -> None:
        status_frame = ctk.CTkFrame(self.root, height=35, corner_radius=0)
        status_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=0, pady=0)

        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="\u25cf",
            font=ctk.CTkFont(size=14),
            text_color=("#10b981", "#34d399"),
        )
        self.status_indicator.pack(side="left", padx=(15, 5))

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="\u2728 Ready to translate",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(side="left", padx=5)

    # ── Settings & navigation ────────────────────────────────────

    def _apply_settings(self) -> None:
        self.source_lang_var.set(self.settings.get_source_language())
        self.target_lang_var.set(self.settings.get_target_language())

        selected = self.settings.get_selected_services()
        for service_id, var in self.service_vars.items():
            var.set(service_id in selected)

        agents_config = self.settings.get("agents", [])
        button_text = "\U0001f916 Agent Vote" if agents_config else "\U0001f916 Evaluate All"
        self.evaluate_button.configure(text=button_text)

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
        self.results_tabview.set("\U0001f4dc History")
        self._refresh_history()

    def _on_history_select(self, entry: dict[str, Any]) -> None:
        self._translations = entry.get("translations", {})
        self._original_text = entry.get("source_text", "")
        self._update_results()
        self.results_tabview.set("\U0001f4dd Results")
        self._status("History entry loaded")

    def _open_glossary(self) -> None:
        self.results_tabview.set("\U0001f4da Glossary")
        self._refresh_glossary()

    def _toggle_theme(self) -> None:
        current = self.settings.get_theme()
        new_theme = "light" if current == "dark" else "dark"
        self.settings.set_theme(new_theme)
        self.settings.save()
        ctk.set_appearance_mode(new_theme)
        theme_icon = "\U0001f319" if new_theme == "light" else "\u2600\ufe0f"
        self.theme_button.configure(text=theme_icon)

    def _get_selected_services(self) -> list[str]:
        return [service_id for service_id, var in self.service_vars.items() if var.get()]

    def _show_comparison(self) -> None:
        if self._translations:
            self.results_tabview.set("\U0001f4ca Comparison")

    def _clear_all(self) -> None:
        self._current_file = None
        self._current_text = ""
        self._original_text = ""
        self._translations = {}
        self._evaluations = {}
        self._ai_improved_translation = ""
        self._best_service = ""
        self.file_drop.clear()
        self.progress.reset()
        self.compare_button.configure(state="disabled")
        self.evaluate_button.configure(state="disabled")
        self._update_results()
        self.results_tabview.set("\U0001f4dd Results")
        self._status("Cleared")

    # ── Utilities ────────────────────────────────────────────────

    def _make_textbox_readonly(self, textbox: ctk.CTkTextbox) -> None:
        def on_key(event: Any) -> str:
            if event.state & 0x0004 and event.keysym in ("c", "a", "C", "A"):
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
            return "break"

        textbox._textbox.bind("<Key>", on_key)  # type: ignore[attr-defined]

    def _status(self, message: str) -> None:
        self.status_label.configure(text=message)

    def _on_close(self) -> None:
        self.settings.set_window_geometry(self.root.geometry())
        self.settings.save()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
