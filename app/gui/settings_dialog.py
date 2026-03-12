"""Settings dialog for API keys and application configuration."""

from __future__ import annotations

from collections.abc import Callable
from tkinter import filedialog
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

if TYPE_CHECKING:
    from app.config.settings import Settings


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog window."""

    AGENT_TYPES = ["localai", "openai", "claude", "groq"]

    def __init__(
        self,
        master: ctk.CTk,
        settings: Settings,
        on_save: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)

        self.settings = settings
        self.on_save = on_save

        self.title("Settings")
        self.geometry("550x1050")
        self.resizable(False, False)

        # Make modal
        self.transient(master)
        self.grab_set()

        self._agent_rows: list[dict[str, Any]] = []

        self._create_widgets()
        self._load_settings()

        # Center on parent
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_y() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self) -> None:
        # Scrollable frame for content
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=510, height=600)
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

        # AI Agents Section
        self._create_section_label("AI Agents (Multi-Agent Voting)")

        agents_helper = ctk.CTkLabel(
            self.scroll_frame,
            text="Add multiple AI agents for voting-based evaluation.\nOverrides single AI Evaluator when agents are configured.",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            justify="left",
        )
        agents_helper.pack(fill="x", padx=10, pady=(2, 5))

        self._agents_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self._agents_container.pack(fill="x", padx=5, pady=5)

        add_agent_btn = ctk.CTkButton(
            self.scroll_frame,
            text="+ Add Agent",
            command=self._add_agent_row,
            width=120,
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color=("#10b981", "#065f46"),
            hover_color=("#059669", "#047857"),
        )
        add_agent_btn.pack(pady=(5, 10))

        # Ren'Py Settings
        self._create_section_label("Ren'Py Settings")

        renpy_folder_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        renpy_folder_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(renpy_folder_frame, text="Game Folder:", width=100, anchor="w").pack(
            side="left", padx=5
        )
        self.renpy_folder_entry = ctk.CTkEntry(
            renpy_folder_frame, width=280, placeholder_text="Path to Ren'Py game folder"
        )
        self.renpy_folder_entry.pack(side="left", padx=5)

        ctk.CTkButton(
            renpy_folder_frame,
            text="Browse",
            command=self._browse_renpy_folder,
            width=70,
            height=28,
            corner_radius=6,
        ).pack(side="left", padx=5)

        renpy_mode_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        renpy_mode_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(renpy_mode_frame, text="Processing Mode:", width=120, anchor="w").pack(
            side="left", padx=5
        )
        self.renpy_mode_var = ctk.StringVar(value="scenes")
        self.renpy_mode_dropdown = ctk.CTkOptionMenu(
            renpy_mode_frame,
            variable=self.renpy_mode_var,
            values=["scenes", "chunks", "full"],
            width=200,
        )
        self.renpy_mode_dropdown.pack(side="left", padx=5)

        renpy_mode_helper = ctk.CTkLabel(
            self.scroll_frame,
            text="scenes = split by labels (recommended), chunks = standard chunking, full = entire file",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            justify="left",
        )
        renpy_mode_helper.pack(fill="x", padx=10, pady=(2, 5))

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
        label = ctk.CTkLabel(
            self.scroll_frame,
            text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        label.pack(fill="x", padx=5, pady=(15, 5))

    def _create_api_entry(self, key: str, label: str) -> None:
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
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(fill="x", padx=5, pady=3)

        ctk.CTkLabel(frame, text=label, width=100, anchor="w").pack(side="left", padx=5)
        entry = ctk.CTkEntry(frame, width=350, placeholder_text=placeholder)
        entry.pack(side="left", padx=5)

        return entry

    def _create_model_dropdown(self, label: str, key: str, values: list[str]) -> None:
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(fill="x", padx=5, pady=3)

        ctk.CTkLabel(frame, text=label, width=150, anchor="w").pack(side="left", padx=5)
        var = ctk.StringVar(value=values[0])
        dropdown = ctk.CTkOptionMenu(frame, variable=var, values=values, width=300)
        dropdown.pack(side="left", padx=5)

        self.model_vars[key] = var

    def _add_agent_row(
        self,
        name: str = "",
        agent_type: str = "localai",
        url: str = "",
        model: str = "",
        api_key: str = "not-needed",
        weight: float = 1.0,
    ) -> None:
        row_frame = ctk.CTkFrame(self._agents_container, corner_radius=8)
        row_frame.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(row_frame, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=6)

        # Row 1: Name + Type + Remove
        r1 = ctk.CTkFrame(inner, fg_color="transparent")
        r1.pack(fill="x", pady=2)

        name_entry = ctk.CTkEntry(r1, width=150, placeholder_text="Agent Name")
        name_entry.pack(side="left", padx=2)
        if name:
            name_entry.insert(0, name)

        type_var = ctk.StringVar(value=agent_type)
        type_menu = ctk.CTkOptionMenu(
            r1,
            variable=type_var,
            values=self.AGENT_TYPES,
            width=100,
            command=lambda v: self._on_agent_type_change(row_data),
        )
        type_menu.pack(side="left", padx=2)

        remove_btn = ctk.CTkButton(
            r1,
            text="X",
            width=30,
            height=28,
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c"),
            command=lambda: self._remove_agent_row(row_data),
        )
        remove_btn.pack(side="right", padx=2)

        # Row 2: URL + Model + API Key
        r2 = ctk.CTkFrame(inner, fg_color="transparent")
        r2.pack(fill="x", pady=2)

        url_entry = ctk.CTkEntry(r2, width=180, placeholder_text="Server URL (LocalAI)")
        url_entry.pack(side="left", padx=2)
        if url:
            url_entry.insert(0, url)

        model_entry = ctk.CTkEntry(r2, width=120, placeholder_text="Model")
        model_entry.pack(side="left", padx=2)
        if model:
            model_entry.insert(0, model)

        key_entry = ctk.CTkEntry(r2, width=120, placeholder_text="API Key", show="*")
        key_entry.pack(side="left", padx=2)
        if api_key:
            key_entry.insert(0, api_key)

        # Row 3: Weight slider
        r3 = ctk.CTkFrame(inner, fg_color="transparent")
        r3.pack(fill="x", pady=2)

        ctk.CTkLabel(r3, text="Weight:", font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
        weight_slider = ctk.CTkSlider(r3, from_=0.5, to=2.0, number_of_steps=6, width=150)
        weight_slider.set(weight)
        weight_slider.pack(side="left", padx=2)
        weight_label = ctk.CTkLabel(r3, text=f"{weight:.1f}", font=ctk.CTkFont(size=11))
        weight_label.pack(side="left", padx=2)
        weight_slider.configure(command=lambda v: weight_label.configure(text=f"{v:.1f}"))

        row_data: dict[str, Any] = {
            "frame": row_frame,
            "name": name_entry,
            "type": type_var,
            "url": url_entry,
            "model": model_entry,
            "api_key": key_entry,
            "weight": weight_slider,
        }

        # Show/hide URL based on type
        if agent_type != "localai":
            url_entry.configure(state="disabled")

        self._agent_rows.append(row_data)

    def _on_agent_type_change(self, row_data: dict[str, Any]) -> None:
        if row_data["type"].get() == "localai":
            row_data["url"].configure(state="normal")
        else:
            row_data["url"].configure(state="disabled")

    def _remove_agent_row(self, row_data: dict[str, Any]) -> None:
        row_data["frame"].destroy()
        if row_data in self._agent_rows:
            self._agent_rows.remove(row_data)

    def _browse_renpy_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select Ren'Py Game Folder")
        if folder:
            self.renpy_folder_entry.delete(0, "end")
            self.renpy_folder_entry.insert(0, folder)

    def _load_settings(self) -> None:
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

        # Agents
        agents = self.settings.get("agents", [])
        for agent_data in agents:
            self._add_agent_row(
                name=agent_data.get("name", ""),
                agent_type=agent_data.get("agent_type", "localai"),
                url=agent_data.get("base_url", ""),
                model=agent_data.get("model", ""),
                api_key=agent_data.get("api_key", "not-needed"),
                weight=agent_data.get("weight", 1.0),
            )

        # Ren'Py settings
        renpy_folder = self.settings.get("renpy_game_folder", "")
        if renpy_folder:
            self.renpy_folder_entry.insert(0, renpy_folder)

        self.renpy_mode_var.set(self.settings.get("renpy_processing_mode", "scenes"))

        # Processing settings
        self.chunk_size_slider.set(self.settings.get_chunk_size())
        self.chunk_size_label.configure(text=str(self.settings.get_chunk_size()))

        self.max_workers_slider.set(self.settings.get_max_workers())
        self.max_workers_label.configure(text=str(self.settings.get_max_workers()))

    def _save_settings(self) -> None:
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

        # Agents
        agents = []
        for row in self._agent_rows:
            agents.append(
                {
                    "name": row["name"].get(),
                    "agent_type": row["type"].get(),
                    "base_url": row["url"].get(),
                    "model": row["model"].get(),
                    "api_key": row["api_key"].get(),
                    "weight": round(row["weight"].get(), 1),
                }
            )
        self.settings.set("agents", agents)

        # Ren'Py settings
        self.settings.set("renpy_game_folder", self.renpy_folder_entry.get())
        self.settings.set("renpy_processing_mode", self.renpy_mode_var.get())

        # Processing settings
        self.settings.set_chunk_size(int(self.chunk_size_slider.get()))
        self.settings.set_max_workers(int(self.max_workers_slider.get()))

        # Save to file
        self.settings.save()

        # Callback
        if self.on_save:
            self.on_save()

        self.destroy()
