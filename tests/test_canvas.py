"""Tests for mochi.core.canvas."""

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget


class TestCanvasClass:
    """Test that Canvas class definition is correct (no QApp needed)."""

    def test_canvas_module_importable(self) -> None:
        """Importing the module should not raise."""
        import mochi.core.canvas  # noqa: F401

    def test_canvas_is_qwidget_subclass(self) -> None:
        """Canvas must inherit from QWidget."""
        from mochi.core.canvas import Canvas

        assert issubclass(Canvas, QWidget)


class TestCanvasWidget:
    """Test Canvas widget instance properties (requires QApp via qtbot)."""

    def test_window_flags_set(self, qtbot: object) -> None:
        """Canvas should have FramelessWindowHint, WindowStaysOnTopHint, and Tool."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        flags = canvas.windowFlags()
        assert flags & Qt.FramelessWindowHint
        assert flags & Qt.WindowStaysOnTopHint
        assert flags & Qt.Tool

    def test_translucent_background_set(self, qtbot: object) -> None:
        """Canvas should have WA_TranslucentBackground attribute set."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        assert canvas.testAttribute(Qt.WA_TranslucentBackground)

    def test_geometry_matches_primary_screen(self, qtbot: object) -> None:
        """Canvas geometry should match primary screen availableGeometry."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        screen = canvas.screen()
        assert screen is not None
        expected_geo = screen.availableGeometry()
        actual_geo = canvas.geometry()

        assert actual_geo == expected_geo

    def test_paint_event_does_not_raise(self, qtbot: object) -> None:
        """Calling paintEvent with a mock QPainter should not raise."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        # Use a real QPainter backed by the canvas to avoid segfaults
        painter = QPainter(canvas)
        try:
            # Should not raise
            canvas.paintEvent(MagicMock(rect=MagicMock(return_value=QRect(0, 0, 100, 100))))
        finally:
            painter.end()

    @pytest.mark.skipif(True, reason="OBSOLETE: green rect replaced by sprite")
    def test_green_pixel_at_bottom_center(self, qtbot: object) -> None:
        """OBSOLETE — sprite rendering replaces the green rectangle."""
        from mochi import config
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        screen = canvas.screen()
        assert screen is not None
        geo = screen.availableGeometry()

        expected_x = (geo.width() - 64) // 2
        expected_y = geo.bottom() - config.SCREEN_BOTTOM_MARGIN_PX - 64

        pixmap = canvas.grab(QRect(expected_x, expected_y, 64, 64))
        center_pixel = pixmap.toImage().pixelColor(32, 32)

        assert center_pixel.name() == "#00ff00"
