"""Environment poller and surface detection for Mochi.

Provides the ``Surface`` dataclass representing walkable/grabbable surfaces
on the desktop (window tops, window sides, screen edges), and the
``EnvironmentPoller`` QThread that periodically queries active windows
via PyWinCtl and emits an updated surface list.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRect


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
