"""Environment poller and surface detection for Mochi.

Provides the ``Surface`` dataclass representing walkable/grabbable surfaces
on the desktop (window tops, window sides, screen edges), and the
``EnvironmentPoller`` QThread that periodically queries active windows
via PyWinCtl and emits an updated surface list.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QObject, QRect, QThread, Signal

logger = logging.getLogger("mochi.environment")


@dataclass
class Surface:
    """A walkable or grabbable surface on the desktop.

    Parameters
    ----------
    rect : QRect
        The bounding rectangle in screen coordinates.
    surface_type : str
        One of ``"window_top"``, ``"window_left"``, ``"window_right"``,
        ``"screen_bottom"``, ``"screen_left"``, ``"screen_right"``.
    window_id : int | None
        OS window handle for tracking moves/closes; ``None`` for screen edges.
    """

    rect: QRect
    surface_type: str
    window_id: int | None


class EnvironmentPoller(QThread):
    """Background thread that polls active windows and emits surface lists.

    Runs a ``QTimer`` at ``WINDOW_POLL_INTERVAL_MS`` on its own event loop.
    Each tick, it queries ``pywinctl`` for visible windows, builds a
    ``list[Surface]``, and emits ``platforms_updated`` to the main thread.

    Parameters
    ----------
    screen_geo : QRect
        The primary monitor's available geometry, captured once on the main
        thread (``QScreen.availableGeometry()``).
    parent : QObject or None
        Optional parent QObject.
    """

    #: Emitted on each poll tick with the latest ``list[Surface]``.
    platforms_updated = Signal(list)

    def __init__(self, screen_geo: QRect, parent: QObject | None = None) -> None:
        super().__init__(parent)
        #: Screen geometry captured once on the main thread.
        self._screen_geo: QRect = screen_geo
        #: Cached surface list from the last successful poll (for error fallback).
        self._cached_surfaces: list[Surface] = []

    @staticmethod
    def _get_visible_windows(windows: list[Any]) -> list[Any]:
        """Filter a list of pywinctl windows to only visible, valid ones.

        Excludes minimized windows, windows with empty titles, and the
        Mochi overlay window itself.

        Parameters
        ----------
        windows : list[Any]
            Raw window list from ``pywinctl.getAllWindows()``.

        Returns
        -------
        list[Any]
            Filtered window list with only visible, non-Mochi windows.
        """
        result: list[Any] = []
        for w in windows:
            if getattr(w, "isMinimized", lambda: False)():
                continue
            title = getattr(w, "title", "") or ""
            if not title.strip():
                continue
            if title.strip() == "Mochi":
                continue
            result.append(w)
        return result
