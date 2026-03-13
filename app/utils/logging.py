"""Logging configuration for PolyTranslate."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(
    log_file: str | Path | None = "polytranslate.log",
    level: int = logging.INFO,
    console: bool = False,
) -> None:
    root = logging.getLogger("app")
    root.setLevel(level)

    if root.handlers:
        return

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)
