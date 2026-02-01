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
        self.geometry("500x600")
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

        api_services = [
            ("deepl", "DeepL API Key"),
            ("yandex", "Yandex Cloud API Key"),
            ("google", "Google Cloud API Key"),
            ("openai", "OpenAI API Key"),
            ("openrouter", "OpenRouter API Key"),
            ("groq", "Groq API Key"),
            ("anthropic", "Anthropic (Claude) API Key"),
        ]

        for key, label in api_services:
            self._create_api_entry(key, label)

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

        # Processing settings
        self.settings.set_chunk_size(int(self.chunk_size_slider.get()))
        self.settings.set_max_workers(int(self.max_workers_slider.get()))

        # Save to file
        self.settings.save()

        # Callback
        if self.on_save:
            self.on_save()

        self.destroy()
