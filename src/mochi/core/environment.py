"""Environment poller and surface detection for Mochi.

Provides the ``Surface`` dataclass representing walkable/grabbable surfaces
on the desktop (window tops, window sides, screen edges), and the
``EnvironmentPoller`` QThread that periodically queries active windows
via PyWinCtl and emits an updated surface list.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QRect, QThread, Signal


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
