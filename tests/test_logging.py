"""Tests for logging configuration."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from app.utils.logging import setup_logging


@pytest.fixture(autouse=True)
def _reset_logger():
    """Reset the app logger before each test."""
    root = logging.getLogger("app")
    root.handlers.clear()
    root.setLevel(logging.WARNING)
    yield
    root.handlers.clear()
    root.setLevel(logging.WARNING)


class TestSetupLogging:
    def test_creates_file_handler(self, tmp_path: Path) -> None:
        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file)

        root = logging.getLogger("app")
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0], logging.FileHandler)

    def test_creates_console_handler(self, tmp_path: Path) -> None:
        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file, console=True)

        root = logging.getLogger("app")
        assert len(root.handlers) == 2
        handler_types = {type(h) for h in root.handlers}
        assert logging.FileHandler in handler_types
        assert logging.StreamHandler in handler_types

    def test_no_file_handler_when_none(self) -> None:
        setup_logging(log_file=None, console=True)

        root = logging.getLogger("app")
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0], logging.StreamHandler)

    def test_sets_level(self, tmp_path: Path) -> None:
        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file, level=logging.DEBUG)

        root = logging.getLogger("app")
        assert root.level == logging.DEBUG

    def test_idempotent(self, tmp_path: Path) -> None:
        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file)
        setup_logging(log_file=log_file)

        root = logging.getLogger("app")
        assert len(root.handlers) == 1

    def test_writes_to_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file)

        logger = logging.getLogger("app.test")
        logger.info("test message")

        content = log_file.read_text(encoding="utf-8")
        assert "test message" in content
        assert "[INFO]" in content

    def test_console_handler_level_is_warning(self, tmp_path: Path) -> None:
        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file, console=True)

        root = logging.getLogger("app")
        stream_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(stream_handlers) == 1
        assert stream_handlers[0].level == logging.WARNING

    def test_no_handlers_no_file_no_console(self) -> None:
        setup_logging(log_file=None, console=False)

        root = logging.getLogger("app")
        assert len(root.handlers) == 0
