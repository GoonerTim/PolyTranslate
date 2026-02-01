"""Pytest configuration and fixtures."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_text() -> str:
    """Sample text for translation."""
    return "Hello, world! This is a test sentence. How are you today?"


@pytest.fixture
def sample_text_ru() -> str:
    """Sample Russian text."""
    return "Привет, мир! Это тестовое предложение. Как дела сегодня?"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config(temp_dir: Path) -> Path:
    """Create a temporary config file."""
    config_path = temp_dir / "config.json"
    config = {
        "api_keys": {
            "deepl": "test_deepl_key",
            "yandex": "test_yandex_key",
            "google": "test_google_key",
            "openai": "test_openai_key",
            "groq": "test_groq_key",
        },
        "theme": "dark",
        "chunk_size": 1000,
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f)
    return config_path


@pytest.fixture
def temp_glossary(temp_dir: Path) -> Path:
    """Create a temporary glossary file."""
    glossary_path = temp_dir / "glossary.json"
    glossary = {
        "entries": {
            "Hello": "Привет",
            "world": "мир",
        },
        "case_sensitive": False,
    }
    with open(glossary_path, "w", encoding="utf-8") as f:
        json.dump(glossary, f)
    return glossary_path


@pytest.fixture
def sample_txt_file(temp_dir: Path) -> Path:
    """Create a sample text file."""
    file_path = temp_dir / "sample.txt"
    file_path.write_text("Hello, world!", encoding="utf-8")
    return file_path


@pytest.fixture
def sample_rpy_content() -> bytes:
    """Sample Ren'Py file content."""
    return b"""
# This is a comment
label start:
    e "Hello, how are you?"
    mc "I'm fine, thanks!"

    menu:
        "Good option":
            jump good_ending
        "Bad option":
            jump bad_ending

    $ some_variable = True
    _("Translatable string")
"""


@pytest.fixture
def mock_deepl_response() -> dict[str, Any]:
    """Mock DeepL API response."""
    return {"translations": [{"text": "Привет, мир!"}]}


@pytest.fixture
def mock_yandex_response() -> dict[str, Any]:
    """Mock Yandex API response."""
    return {"translations": [{"text": "Привет, мир!"}]}


@pytest.fixture
def mock_google_response() -> dict[str, Any]:
    """Mock Google API response."""
    return {"data": {"translations": [{"translatedText": "Привет, мир!"}]}}


@pytest.fixture
def mock_chatgpt_proxy_response() -> dict[str, Any]:
    """Mock ChatGPT Proxy response."""
    return {"response": {"translated_text": "Привет, мир!"}}
