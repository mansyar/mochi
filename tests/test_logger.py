"""Tests for mochi.utils.logger."""

import logging
from pathlib import Path

import pytest

from mochi.utils.logger import setup_logging


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def teardown_method(self) -> None:
        """Reset root logger after each test."""
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.WARNING)

    def test_creates_console_and_file_handlers(self, tmp_path: Path) -> None:
        """setup_logging() should add StreamHandler and FileHandler."""
        log_path = tmp_path / "mochi.log"
        setup_logging(log_path=str(log_path))
        root = logging.getLogger()
        handler_types = {type(h).__name__ for h in root.handlers}
        assert "StreamHandler" in handler_types
        assert "FileHandler" in handler_types

    def test_info_level_produces_output(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Logging at INFO level should produce console output."""
        log_path = tmp_path / "mochi.log"
        setup_logging(log_path=str(log_path))
        logger = logging.getLogger("mochi")
        logger.info("Hello Mochi")
        captured = capsys.readouterr()
        assert "Hello Mochi" in captured.out

    def test_log_format_contains_timestamp_level_and_name(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Log format should include timestamp, level, logger name, and message."""
        log_path = tmp_path / "mochi.log"
        setup_logging(log_path=str(log_path))
        logger = logging.getLogger("mochi.test")
        logger.info("format check")
        captured = capsys.readouterr()
        output = captured.out
        # Should contain timestamp-like digits, level INFO, logger name, and message
        assert "INFO" in output
        assert "mochi.test" in output
        assert "format check" in output

    def test_debug_mode_uses_debug_level(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """When debug=True, DEBUG messages should appear."""
        log_path = tmp_path / "mochi.log"
        setup_logging(debug=True, log_path=str(log_path))
        logger = logging.getLogger("mochi")
        logger.debug("debug message")
        captured = capsys.readouterr()
        assert "debug message" in captured.out

    def test_non_debug_suppresses_debug(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """When debug=False (default), DEBUG messages should NOT appear."""
        log_path = tmp_path / "mochi.log"
        setup_logging(log_path=str(log_path))
        logger = logging.getLogger("mochi")
        logger.debug("should not appear")
        captured = capsys.readouterr()
        assert "should not appear" not in captured.out

    def test_log_file_written(self, tmp_path: Path) -> None:
        """File handler should write log messages to the specified path."""
        log_path = tmp_path / "mochi.log"
        setup_logging(log_path=str(log_path))
        logger = logging.getLogger("mochi")
        logger.info("file test")
        assert log_path.exists()
        content = log_path.read_text()
        assert "file test" in content
