"""Tests for Canvas sprite animation — frame advancement and rendering."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QRect, QTimer

from mochi import config


class TestCanvasAnimationTimer:
    """Test that Canvas creates and configures the animation timer."""

    def test_canvas_creates_animation_timer(self, qtbot: object) -> None:
        """Canvas should have a QTimer for animation tick."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        assert hasattr(canvas, "_animation_timer")
        assert isinstance(canvas._animation_timer, QTimer)

    def test_animation_timer_interval_is_100ms(self, qtbot: object) -> None:
        """Animation timer interval should equal ANIMATION_TICK_MS (100ms)."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        assert canvas._animation_timer.interval() == config.ANIMATION_TICK_MS

    def test_animation_timer_is_active_on_construction(self, qtbot: object) -> None:
        """Animation timer should be running after Canvas construction."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        assert canvas._animation_timer.isActive()


class TestCanvasFrameAdvancement:
    """Test that the frame index advances correctly on timer ticks."""

    def test_frame_index_starts_at_zero(self, qtbot: object) -> None:
        """Current frame index should start at 0."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        assert canvas._current_frame == 0

    def test_frame_index_advances_on_tick(self, qtbot: object) -> None:
        """Frame index should advance by 1 after a timer tick."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        # Count initial frames for wrap-around
        frame_count = len(canvas._idle_frames)
        initial = canvas._current_frame
        canvas._advance_frame()
        expected = (initial + 1) % frame_count if frame_count > 0 else 0
        assert canvas._current_frame == expected

    def test_frame_wraps_after_last_frame(self, qtbot: object) -> None:
        """Frame index should wrap to 0 after advancing past the last frame."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        frame_count = len(canvas._idle_frames)
        if frame_count == 0:
            pytest.skip("No idle frames loaded")

        # Advance to the last frame
        for _ in range(frame_count):
            canvas._advance_frame()

        assert canvas._current_frame == 0


class TestCanvasSpriteRendering:
    """Test that Canvas renders the sprite instead of the green rectangle."""

    def test_paint_event_calls_draw_pixmap(self, qtbot: object) -> None:
        """paintEvent should call painter.drawPixmap with the current frame."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        # Patch QPainter.drawPixmap at the class level so it affects the
        # internal QPainter created inside paintEvent.
        with patch("PySide6.QtGui.QPainter.drawPixmap") as mock_draw:
            canvas.paintEvent(MagicMock(rect=MagicMock(return_value=QRect(0, 0, 100, 100))))
            mock_draw.assert_called_once()

    def test_no_green_rect_drawn(self, qtbot: object) -> None:
        """paintEvent should NOT call fillRect with QColor("#00FF00")."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        # Patch QPainter.fillRect at the class level.
        with patch("PySide6.QtGui.QPainter.fillRect") as mock_fill:
            canvas.paintEvent(MagicMock(rect=MagicMock(return_value=QRect(0, 0, 100, 100))))
            mock_fill.assert_not_called()

    def test_canvas_has_idle_frames(self, qtbot: object) -> None:
        """Canvas should load idle frames on construction."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        assert hasattr(canvas, "_idle_frames")
        assert isinstance(canvas._idle_frames, list)
        # At minimum we should have the frames loaded
        assert len(canvas._idle_frames) > 0


class TestGreenRectObsolete:
    """Test that the green rectangle pixel test is marked obsolete."""

    def test_green_rect_test_comment_updated(self) -> None:
        """The skipped green pixel test should reference that it's obsolete."""
        import inspect

        import mochi.core.canvas

        source = inspect.getsource(mochi.core.canvas)
        assert "#00FF00" not in source or "green" not in source, (
            "Green rectangle #00FF00 should be removed from canvas.py"
        )
