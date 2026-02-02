#!/usr/bin/env python3
"""Entry point for the Translator desktop application."""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def download_nltk_resources() -> None:
    import contextlib

    try:
        import nltk

        resources = ["punkt", "punkt_tab"]
        for resource in resources:
            with contextlib.suppress(Exception):
                nltk.download(resource, quiet=True)
    except ImportError:
        pass


def main() -> None:
    download_nltk_resources()

    from app.gui.main_window import MainWindow

    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
