"""Pydantic schema for application settings."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Canonical model lists — single source of truth
OPENAI_MODELS = [
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4o",
    "gpt-4o-mini",
    "o3-mini",
    "gpt-4-turbo",
]

CLAUDE_MODELS = [
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
    "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
]

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]


class ApiKeysSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    deepl: str = ""
    yandex: str = ""
    google: str = ""
    openai: str = ""
    openrouter: str = ""
    groq: str = ""
    anthropic: str = ""


class SettingsSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    api_keys: ApiKeysSchema = Field(default_factory=ApiKeysSchema)
    deepl_plan: str = "free"
    openai_model: str = "gpt-4o-mini"
    openrouter_model: str = "openai/gpt-4o-mini"
    groq_model: str = "llama-3.3-70b-versatile"
    claude_model: str = "claude-sonnet-4-6"
    localai_url: str = ""
    localai_model: str = "default"
    theme: str = "dark"
    chunk_size: int = 1000
    max_workers: int = 3
    source_language: str = "auto"
    target_language: str = "ru"
    selected_services: list[str] = Field(default_factory=lambda: ["deepl"])
    window_geometry: str = "1200x800"
    ai_evaluator_service: str = ""
    ai_evaluator_model: str = ""
    ai_evaluation_auto: bool = False
    agents: list[dict[str, Any]] = Field(default_factory=list)
    renpy_game_folder: str = ""
    renpy_processing_mode: str = "scenes"
    cache_enabled: bool = True
    cache_max_size: int = 10000

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError(f"Invalid type for 'theme': expected str, got {type(v).__name__}")
        if v not in ("dark", "light"):
            raise ValueError(f"Invalid value for 'theme': {v!r}. Must be one of: dark, light")
        return v

    @field_validator("deepl_plan")
    @classmethod
    def validate_deepl_plan(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError(f"Invalid type for 'deepl_plan': expected str, got {type(v).__name__}")
        if v not in ("free", "pro"):
            raise ValueError(f"Invalid value for 'deepl_plan': {v!r}. Must be one of: free, pro")
        return v

    @field_validator("renpy_processing_mode")
    @classmethod
    def validate_renpy_processing_mode(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError(
                f"Invalid type for 'renpy_processing_mode': expected str, got {type(v).__name__}"
            )
        if v not in ("scenes", "chunks", "full"):
            raise ValueError(
                f"Invalid value for 'renpy_processing_mode': {v!r}. "
                f"Must be one of: scenes, chunks, full"
            )
        return v

    @field_validator("chunk_size")
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        if not isinstance(v, int) or isinstance(v, bool):
            raise ValueError(f"Invalid type for 'chunk_size': expected int, got {type(v).__name__}")
        if v < 100:
            raise ValueError(f"Value for 'chunk_size' must be >= 100, got {v}")
        if v > 5000:
            raise ValueError(f"Value for 'chunk_size' must be <= 5000, got {v}")
        return v

    @field_validator("max_workers")
    @classmethod
    def validate_max_workers(cls, v: int) -> int:
        if not isinstance(v, int) or isinstance(v, bool):
            raise ValueError(
                f"Invalid type for 'max_workers': expected int, got {type(v).__name__}"
            )
        if v < 1:
            raise ValueError(f"Value for 'max_workers' must be >= 1, got {v}")
        if v > 10:
            raise ValueError(f"Value for 'max_workers' must be <= 10, got {v}")
        return v

    @field_validator("cache_max_size")
    @classmethod
    def validate_cache_max_size(cls, v: int) -> int:
        if not isinstance(v, int) or isinstance(v, bool):
            raise ValueError(
                f"Invalid type for 'cache_max_size': expected int, got {type(v).__name__}"
            )
        if v < 100:
            raise ValueError(f"Value for 'cache_max_size' must be >= 100, got {v}")
        if v > 100000:
            raise ValueError(f"Value for 'cache_max_size' must be <= 100000, got {v}")
        return v

    @field_validator("cache_enabled")
    @classmethod
    def validate_cache_enabled(cls, v: bool) -> bool:
        if not isinstance(v, bool):
            raise ValueError(
                f"Invalid type for 'cache_enabled': expected bool, got {type(v).__name__}"
            )
        return v

    @field_validator("ai_evaluation_auto")
    @classmethod
    def validate_ai_evaluation_auto(cls, v: bool) -> bool:
        if not isinstance(v, bool):
            raise ValueError(
                f"Invalid type for 'ai_evaluation_auto': expected bool, got {type(v).__name__}"
            )
        return v

    @field_validator("openai_model")
    @classmethod
    def validate_openai_model(cls, v: str) -> str:
        if not isinstance(v, str) or not v:
            raise ValueError("Model for 'openai_model' must be a non-empty string")
        if v not in OPENAI_MODELS:
            allowed = ", ".join(OPENAI_MODELS)
            raise ValueError(f"Unknown model for 'openai_model': {v!r}. Available: {allowed}")
        return v

    @field_validator("claude_model")
    @classmethod
    def validate_claude_model(cls, v: str) -> str:
        if not isinstance(v, str) or not v:
            raise ValueError("Model for 'claude_model' must be a non-empty string")
        if v not in CLAUDE_MODELS:
            allowed = ", ".join(CLAUDE_MODELS)
            raise ValueError(f"Unknown model for 'claude_model': {v!r}. Available: {allowed}")
        return v

    @field_validator("groq_model")
    @classmethod
    def validate_groq_model(cls, v: str) -> str:
        if not isinstance(v, str) or not v:
            raise ValueError("Model for 'groq_model' must be a non-empty string")
        if v not in GROQ_MODELS:
            allowed = ", ".join(GROQ_MODELS)
            raise ValueError(f"Unknown model for 'groq_model': {v!r}. Available: {allowed}")
        return v
