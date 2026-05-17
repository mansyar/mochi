"""Platform abstraction stubs for Mochi.

Provides OS-agnostic helpers for detecting the current platform,
resolving OS-appropriate data directories, checking modifier key
state, and toggling click-through on windows.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


def get_platform() -> str:
    """Return the current platform identifier.

    Returns
    -------
    str
        One of ``"win32"``, ``"darwin"``, or ``"linux"``.
    """
    return sys.platform


def get_data_dir() -> Path:
    """Return the OS-appropriate data directory for Mochi.

    Resolves to:

    - **Windows:** ``%APPDATA%\\Mochi``
    - **macOS:** ``~/Library/Application Support/Mochi``
    - **Linux:** ``~/.local/share/mochi``

    The directory is created on the first call.

    Returns
    -------
    Path
        Resolved and existing data directory.
    """
    plat = sys.platform
    if plat == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        data_dir = base / "Mochi"
    elif plat == "darwin":
        data_dir = Path.home() / "Library" / "Application Support" / "Mochi"
    else:
        # Linux / other Unix
        xdg_data = os.environ.get("XDG_DATA_HOME")
        base = Path(xdg_data) if xdg_data else Path.home() / ".local" / "share"
        data_dir = base / "mochi"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def is_alt_held() -> bool:
    """Check whether the Alt key is currently held.

    .. note::

       This is a stub that always returns ``False``. A native-keyboard
       implementation will replace it in a later phase.

    Returns
    -------
    bool
        ``True`` if Alt is held, ``False`` otherwise.
    """
    return False


def set_click_through(window: QWidget | None, enabled: bool) -> None:
    """Enable or disable click-through on the given window.

    On Windows this uses the ``WS_EX_TRANSPARENT`` extended window style
    via ``ctypes``. On macOS and Linux the call is a no-op for now.

    Parameters
    ----------
    window : QWidget or None
        The Qt widget to modify.
    enabled : bool
        ``True`` to enable click-through, ``False`` to disable.
    """
    if window is None:
        return

    plat = sys.platform
    if plat == "win32":
        _set_click_through_win32(window, enabled)
    # macOS and Linux stubs — no-op for MVP


def _set_click_through_win32(window: QWidget, enabled: bool) -> None:
    """Toggle ``WS_EX_TRANSPARENT`` on a Windows window."""
    import ctypes

    gwl_exstyle = -20
    ws_ex_transparent = 0x00000020

    hwnd = int(window.winId())
    user32 = ctypes.windll.user32

    current_style = user32.GetWindowLongW(hwnd, gwl_exstyle)
    new_style = current_style | ws_ex_transparent if enabled else current_style & ~ws_ex_transparent
    user32.SetWindowLongW(hwnd, new_style, gwl_exstyle)
