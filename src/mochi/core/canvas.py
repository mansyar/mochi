"""Canvas — the transparent overlay rendering surface for Mochi.

Provides a fullscreen, frameless, always-on-top ``QWidget`` that serves
as the drawing surface for the cat sprite and environmental effects.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QApplication, QWidget

from mochi import config

logger = logging.getLogger("mochi.canvas")

#: Composite window flags for the overlay: frameless, always-on-top, tool.
_CANVAS_FLAGS = (
    Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
)


class Canvas(QWidget):
    """Fullscreen transparent overlay window for rendering Mochi.

    The canvas covers the primary monitor's available geometry (excluding
    OS taskbar/dock), is click-through by default, and provides a
    ``paintEvent`` that draws a placeholder green rectangle at the
    bottom-centre of the screen.

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

        logger.info(
            "Canvas created: %dx%d at (%d, %d)",
            self.width(),
            self.height(),
            self.x(),
            self.y(),
        )

    def paintEvent(self, event: object) -> None:  # noqa: N802
        """Paint the placeholder green rectangle on the canvas.

        Draws a 64x64 green rectangle at the bottom-centre of the screen,
        above the OS taskbar/dock.

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

            rect_size = config.SPRITE_CELL_WIDTH  # 64 px
            x = (geo.width() - rect_size) // 2
            y = geo.bottom() - config.SCREEN_BOTTOM_MARGIN_PX - rect_size

            painter.fillRect(QRect(x, y, rect_size, rect_size), QColor("#00FF00"))
        finally:
            painter.end()
