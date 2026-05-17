"""Canvas — the transparent overlay rendering surface for Mochi.

Provides a fullscreen, frameless, always-on-top ``QWidget`` that serves
as the drawing surface for the cat sprite and environmental effects.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from mochi import config
from mochi.ui.sprites import SpriteSheet

logger = logging.getLogger("mochi.canvas")

#: Composite window flags for the overlay: frameless, always-on-top, tool.
_CANVAS_FLAGS = (
    Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
)


class Canvas(QWidget):
    """Fullscreen transparent overlay window for rendering Mochi.

    The canvas covers the primary monitor's available geometry (excluding
    OS taskbar/dock), is click-through by default, and renders the cat
    sprite with a looping idle animation driven by a ``QTimer``.

    Parameters
    ----------
    parent : QWidget or None
        Optional parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowFlags(_CANVAS_FLAGS)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        screen = QApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
            self.setGeometry(geo)

        # ── Sprite sheet loading ──────────────────────────────────────────
        self._spritesheet: SpriteSheet = SpriteSheet("sprites/")
        self._idle_frames: list[QPixmap] = self._spritesheet.load("idle")
        self._current_frame: int = 0

        # ── Animation timer ───────────────────────────────────────────────
        self._animation_timer: QTimer = QTimer(self)
        self._animation_timer.setInterval(config.ANIMATION_TICK_MS)
        self._animation_timer.timeout.connect(self._advance_frame)
        self._animation_timer.start()

        logger.info(
            "Canvas created: %dx%d at (%d, %d), idle frames: %d",
            self.width(),
            self.height(),
            self.x(),
            self.y(),
            len(self._idle_frames),
        )

    def _advance_frame(self) -> None:
        """Advance the animation frame index, wrapping to 0 at the end."""
        if self._idle_frames:
            self._current_frame = (self._current_frame + 1) % len(self._idle_frames)
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802
        """Render the current idle sprite frame on the canvas.

        Draws the current animation frame at the bottom-centre of the
        screen, above the OS taskbar/dock.

        Parameters
        ----------
        event : QPaintEvent
            The paint event (unused — full window repaint).
        """
        painter = QPainter(self)
        try:
            screen = QApplication.primaryScreen()
            if screen is None:
                return
            geo = screen.availableGeometry()

            cell_w = config.SPRITE_CELL_WIDTH  # 80 px (frame canvas width)
            cell_h = config.SPRITE_CELL_HEIGHT  # 64 px
            x = (geo.width() - cell_w) // 2
            y = geo.bottom() - config.SCREEN_BOTTOM_MARGIN_PX - cell_h

            if self._idle_frames and self._current_frame < len(self._idle_frames):
                frame = self._idle_frames[self._current_frame]
                painter.drawPixmap(x, y, frame)
        finally:
            painter.end()
