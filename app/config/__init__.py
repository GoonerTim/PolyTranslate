"""Configuration management."""

from app.config.languages import LANGUAGES, get_language_name
from app.config.settings import Settings

__all__ = ["Settings", "LANGUAGES", "get_language_name"]
