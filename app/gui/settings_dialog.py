"""Settings dialog for API keys and application configuration."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from app.config.settings import Settings


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog window."""

    def __init__(
        self,
        master: ctk.CTk,
        settings: Settings,
        on_save: Callable[[], None] | None = None,
    ) -> None:
        """
        Initialize the settings dialog.

        Args:
            master: Parent window.
            settings: Settings instance.
            on_save: Callback when settings are saved.
        """
        super().__init__(master)

        self.settings = settings
        self.on_save = on_save

        self.title("Settings")
        self.geometry("500x850")
        self.resizable(False, False)

        # Make modal
        self.transient(master)
        self.grab_set()

        self._create_widgets()
        self._load_settings()

        # Center on parent
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_y() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create the dialog widgets."""
        # Scrollable frame for content
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=460, height=500)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # API Keys Section
        self._create_section_label("API Keys")

        self.api_entries: dict[str, ctk.CTkEntry] = {}
        self.model_vars: dict[str, ctk.StringVar] = {}

        api_services = [
            ("deepl", "DeepL API Key"),
            ("yandex", "Yandex Cloud API Key (Optional - works without key)"),
            ("google", "Google Cloud API Key (Optional - works without key)"),
            ("openai", "OpenAI API Key"),
            ("openrouter", "OpenRouter API Key"),
            ("groq", "Groq API Key"),
            ("anthropic", "Anthropic (Claude) API Key"),
        ]

        for key, label in api_services:
            self._create_api_entry(key, label)

        # Info note about free services
        info_label = ctk.CTkLabel(
            self.scroll_frame,
            text="ℹ️ Yandex and Google work without API keys using their free public APIs",
            font=ctk.CTkFont(size=11),
            text_color=("#2563eb", "#60a5fa"),
        )
        info_label.pack(pady=(5, 10))

        # DeepL Plan
        self._create_section_label("DeepL Settings")

        self.deepl_plan_var = ctk.StringVar(value="free")
        plan_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        plan_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(plan_frame, text="DeepL Plan:").pack(side="left", padx=5)
        ctk.CTkRadioButton(
            plan_frame, text="Free", variable=self.deepl_plan_var, value="free"
        ).pack(side="left", padx=10)
        ctk.CTkRadioButton(plan_frame, text="Pro", variable=self.deepl_plan_var, value="pro").pack(
            side="left", padx=10
        )

        # LocalAI Settings
        self._create_section_label("LocalAI Settings")

        self.localai_url_entry = self._create_labeled_entry(
            "Server URL:", "http://localhost:8080/v1"
        )
        self.localai_model_entry = self._create_labeled_entry("Model:", "default")

        # Model Settings
        self._create_section_label("Model Settings")

        # OpenAI Model
        self._create_model_dropdown(
            "OpenAI Model:",
            "openai_model",
            [
                "gpt-4-turbo-preview",
                "gpt-4",
                "gpt-3.5-turbo",
                "gpt-4o",
                "gpt-4o-mini",
            ],
        )

        # Claude Model
        self._create_model_dropdown(
            "Claude Model:",
            "claude_model",
            [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-2.1",
                "claude-2.0",
                "claude-instant-1.2",
            ],
        )

        # Groq Model
        self._create_model_dropdown(
            "Groq Model:",
            "groq_model",
            [
                "mixtral-8x7b-32768",
                "llama2-70b-4096",
                "gemma-7b-it",
                "llama3-8b-8192",
                "llama3-70b-8192",
            ],
        )

        # OpenRouter Model
        self.openrouter_model_entry = self._create_labeled_entry(
            "OpenRouter Model:", "openai/gpt-3.5-turbo"
        )

        # AI Evaluation Settings
        self._create_section_label("AI Evaluation Settings")

        eval_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        eval_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(eval_frame, text="AI Evaluator Service:", width=150, anchor="w").pack(
            side="left", padx=5
        )
        self.ai_evaluator_service_var = ctk.StringVar(value="")
        self.ai_evaluator_dropdown = ctk.CTkOptionMenu(
            eval_frame,
            variable=self.ai_evaluator_service_var,
            values=["", "openai", "claude", "groq", "localai"],
            width=200,
        )
        self.ai_evaluator_dropdown.pack(side="left", padx=5)

        eval_helper = ctk.CTkLabel(
            self.scroll_frame,
            text="Select which AI service to use for translation evaluation.\nLeave empty to disable AI evaluation feature.",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            justify="left",
        )
        eval_helper.pack(fill="x", padx=10, pady=(2, 5))

        # Processing Settings
        self._create_section_label("Processing Settings")

        # Chunk size
        chunk_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        chunk_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(chunk_frame, text="Chunk Size:").pack(side="left", padx=5)
        self.chunk_size_slider = ctk.CTkSlider(
            chunk_frame, from_=500, to=2000, number_of_steps=15, width=200
        )
        self.chunk_size_slider.pack(side="left", padx=10)
        self.chunk_size_label = ctk.CTkLabel(chunk_frame, text="1000")
        self.chunk_size_label.pack(side="left", padx=5)
        self.chunk_size_slider.configure(
            command=lambda v: self.chunk_size_label.configure(text=str(int(v)))
        )

        # Max workers
        workers_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        workers_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(workers_frame, text="Max Workers:").pack(side="left", padx=5)
        self.max_workers_slider = ctk.CTkSlider(
            workers_frame, from_=1, to=10, number_of_steps=9, width=200
        )
        self.max_workers_slider.pack(side="left", padx=10)
        self.max_workers_label = ctk.CTkLabel(workers_frame, text="3")
        self.max_workers_label.pack(side="left", padx=5)
        self.max_workers_slider.configure(
            command=lambda v: self.max_workers_label.configure(text=str(int(v)))
        )

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, width=100).pack(
            side="right", padx=5
        )

        ctk.CTkButton(button_frame, text="Save", command=self._save_settings, width=100).pack(
            side="right", padx=5
        )

    def _create_section_label(self, text: str) -> None:
        """Create a section label."""
        label = ctk.CTkLabel(
            self.scroll_frame,
            text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        label.pack(fill="x", padx=5, pady=(15, 5))

    def _create_api_entry(self, key: str, label: str) -> None:
        """Create an API key entry field."""
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(fill="x", padx=5, pady=3)

        ctk.CTkLabel(frame, text=label, width=180, anchor="w").pack(side="left", padx=5)
        entry = ctk.CTkEntry(frame, width=250, show="*")
        entry.pack(side="left", padx=5)

        # Toggle visibility button
        show_var = ctk.BooleanVar(value=False)

        def toggle_visibility() -> None:
            if show_var.get():
                entry.configure(show="")
            else:
                entry.configure(show="*")

        toggle_btn = ctk.CTkCheckBox(
            frame, text="Show", variable=show_var, command=toggle_visibility, width=60
        )
        toggle_btn.pack(side="left", padx=5)

        self.api_entries[key] = entry

    def _create_labeled_entry(self, label: str, placeholder: str = "") -> ctk.CTkEntry:
        """Create a labeled entry field."""
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(fill="x", padx=5, pady=3)

        ctk.CTkLabel(frame, text=label, width=100, anchor="w").pack(side="left", padx=5)
        entry = ctk.CTkEntry(frame, width=350, placeholder_text=placeholder)
        entry.pack(side="left", padx=5)

        return entry

    def _create_model_dropdown(self, label: str, key: str, values: list[str]) -> None:
        """Create a model selection dropdown."""
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(fill="x", padx=5, pady=3)

        ctk.CTkLabel(frame, text=label, width=150, anchor="w").pack(side="left", padx=5)
        var = ctk.StringVar(value=values[0])
        dropdown = ctk.CTkOptionMenu(frame, variable=var, values=values, width=300)
        dropdown.pack(side="left", padx=5)

        self.model_vars[key] = var

    def _load_settings(self) -> None:
        """Load current settings into the dialog."""
        api_keys = self.settings.get_api_keys()

        for key, entry in self.api_entries.items():
            value = api_keys.get(key, "")
            if value:
                entry.insert(0, value)

        # DeepL plan
        self.deepl_plan_var.set(self.settings.get("deepl_plan", "free"))

        # LocalAI
        localai_url = self.settings.get("localai_url", "")
        if localai_url:
            self.localai_url_entry.insert(0, localai_url)

        localai_model = self.settings.get("localai_model", "default")
        self.localai_model_entry.insert(0, localai_model)

        # AI Evaluator
        self.ai_evaluator_service_var.set(self.settings.get("ai_evaluator_service", ""))

        # Model settings
        for key, var in self.model_vars.items():
            var.set(self.settings.get(key, var.get()))

        # OpenRouter model (text entry)
        openrouter_model = self.settings.get("openrouter_model", "openai/gpt-3.5-turbo")
        self.openrouter_model_entry.insert(0, openrouter_model)

        # Processing settings
        self.chunk_size_slider.set(self.settings.get_chunk_size())
        self.chunk_size_label.configure(text=str(self.settings.get_chunk_size()))

        self.max_workers_slider.set(self.settings.get_max_workers())
        self.max_workers_label.configure(text=str(self.settings.get_max_workers()))

    def _save_settings(self) -> None:
        """Save settings and close dialog."""
        # API keys
        for key, entry in self.api_entries.items():
            self.settings.set_api_key(key, entry.get())

        # DeepL plan
        self.settings.set("deepl_plan", self.deepl_plan_var.get())

        # LocalAI
        self.settings.set("localai_url", self.localai_url_entry.get())
        self.settings.set("localai_model", self.localai_model_entry.get())

        # AI Evaluator
        self.settings.set("ai_evaluator_service", self.ai_evaluator_service_var.get())

        # Model settings
        for key, var in self.model_vars.items():
            self.settings.set(key, var.get())

        # OpenRouter model (text entry)
        self.settings.set("openrouter_model", self.openrouter_model_entry.get())

        # Processing settings
        self.settings.set_chunk_size(int(self.chunk_size_slider.get()))
        self.settings.set_max_workers(int(self.max_workers_slider.get()))

        # Save to file
        self.settings.save()

        # Callback
        if self.on_save:
            self.on_save()

        self.destroy()
