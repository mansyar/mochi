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

from PySide6.QtCore import QObject, QRect, QThread, QTimer, Signal

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
        #: Internal QTimer created in ``run()``.
        self._timer: QTimer | None = None

    def run(self) -> None:
        """Thread entry point: create timer and start event loop."""
        from mochi import config

        self._timer = QTimer()
        self._timer.setInterval(config.WINDOW_POLL_INTERVAL_MS)
        self._timer.timeout.connect(self._poll)
        self._timer.start()
        self.exec()

    def _poll(self) -> None:
        """Execute one poll cycle: query windows, build surfaces, emit."""
        try:
            import pywinctl

            raw = pywinctl.getAllWindows()
            visible = self._get_visible_windows(raw)
            surfaces = self._build_surfaces(visible)
        except Exception:
            logger.warning("Window polling failed; re-emitting cached surfaces", exc_info=True)
            surfaces = list(self._cached_surfaces)

        self._cached_surfaces = surfaces
        self.platforms_updated.emit(surfaces)

    def _build_surfaces(self, windows: list[Any]) -> list[Surface]:
        """Build a list of ``Surface`` objects from filtered windows and screen edges.

        For each visible window, produces ``window_top``, ``window_left``,
        and ``window_right`` surfaces.  Screen edge surfaces (bottom, left,
        right) are always included.

        Parameters
        ----------
        windows : list[Any]
            Filtered list of visible pywinctl windows.

        Returns
        -------
        list[Surface]
            All walkable/grabbable surfaces on the desktop.
        """
        surfaces: list[Surface] = []
        s = self._screen_geo

        # ── Window surfaces ────────────────────────────────────────────
        for w in windows:
            x = getattr(w, "left", 0) or 0
            y = getattr(w, "top", 0) or 0
            ww = getattr(w, "width", 0) or 0
            wh = getattr(w, "height", 0) or 0
            get_handle = getattr(w, "getHandle", None)
            wid: int | None
            if callable(get_handle):
                raw = get_handle()
                wid = None if raw is None else int(raw)
            else:
                wid = None

            surfaces.append(
                Surface(
                    rect=QRect(x, y, ww, 0),
                    surface_type="window_top",
                    window_id=wid,
                )
            )
            surfaces.append(
                Surface(
                    rect=QRect(x, y, 0, wh),
                    surface_type="window_left",
                    window_id=wid,
                )
            )
            surfaces.append(
                Surface(
                    rect=QRect(x + ww, y, 0, wh),
                    surface_type="window_right",
                    window_id=wid,
                )
            )

        # ── Screen edge surfaces ───────────────────────────────────────
        bottom_y = s.bottom()
        surfaces.append(
            Surface(
                rect=QRect(0, bottom_y, s.width(), 0),
                surface_type="screen_bottom",
                window_id=None,
            )
        )
        surfaces.append(
            Surface(
                rect=QRect(0, 0, 0, s.height()),
                surface_type="screen_left",
                window_id=None,
            )
        )
        surfaces.append(
            Surface(
                rect=QRect(s.width(), 0, 0, s.height()),
                surface_type="screen_right",
                window_id=None,
            )
        )

        return surfaces

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
            # pywinctl 0.x: isMinimized is a method; newer versions: property
            is_min_attr = getattr(w, "isMinimized", None)
            if is_min_attr is not None:
                if callable(is_min_attr):
                    if is_min_attr():
                        continue
                elif is_min_attr:
                    continue
            title = getattr(w, "title", "") or ""
            if not title.strip():
                continue
            if title.strip() == "Mochi":
                continue
            result.append(w)
        return result
