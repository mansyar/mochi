"""Logging configuration for Mochi.

Provides a single setup_logging() entry point that configures both
console (stdout) and file handlers with a consistent format.
"""

import logging
import sys
from pathlib import Path

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(debug: bool = False, log_path: str | None = None) -> None:
    """Configure the root logger with console and file handlers.

    Parameters
    ----------
    debug : bool, optional
        If True, set root logger to DEBUG level (default is INFO).
    log_path : str or None, optional
        Path to the log file. If None, defaults to ``mochi.log`` in the
        current working directory.
    """
    level = logging.DEBUG if debug else logging.INFO
    root = logging.getLogger()

    # Prevent duplicate handlers on repeated calls
    root.handlers.clear()
    root.setLevel(level)

    # Console handler (stdout)
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(console_handler)

    # File handler
    resolved_path = Path(log_path) if log_path else Path("mochi.log")
    file_handler = logging.FileHandler(resolved_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(file_handler)
