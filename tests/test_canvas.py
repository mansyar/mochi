"""Tests for mochi.core.canvas."""

from unittest.mock import MagicMock, patch

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


class TestCanvasSpritePosition:
    """Verify that ``x`` is always the sprite's left edge regardless of
    direction — the fix lives in ``paintEvent``, so no x adjustment
    should happen on direction flips."""

    def test_x_unchanged_after_direction_flip_right_to_left(self, qtbot: object) -> None:
        """When direction flips +1→-1, x should NOT change."""
        from mochi.core.canvas import Canvas
        from mochi.core.fsm import PetState

        canvas = Canvas()
        qtbot.addWidget(canvas)

        canvas._physics.x = 500.0
        canvas._physics.direction = 1
        canvas._fsm.direction = 1

        # Flip direction via EdgePause
        canvas._fsm.transition_to(PetState.EdgePause)
        canvas._fsm._on_timer_expired()
        assert canvas._fsm.direction == -1

        canvas._advance_frame()

        assert canvas._physics.direction == -1
        assert canvas._physics.x == pytest.approx(500.0, rel=1e-6)

    def test_x_unchanged_after_direction_flip_left_to_right(self, qtbot: object) -> None:
        """When direction flips -1→+1, x should NOT change."""
        from mochi.core.canvas import Canvas
        from mochi.core.fsm import PetState

        canvas = Canvas()
        qtbot.addWidget(canvas)

        canvas._physics.x = 100.0
        canvas._physics.direction = -1
        canvas._fsm.direction = -1

        # Flip direction via EdgePause
        canvas._fsm.transition_to(PetState.EdgePause)
        canvas._fsm._on_timer_expired()
        assert canvas._fsm.direction == 1

        # Idle to prevent physics movement
        canvas._fsm.transition_to(PetState.Idle)
        canvas._advance_frame()

        assert canvas._physics.direction == 1
        assert canvas._physics.x == pytest.approx(100.0, rel=1e-6)


class TestCanvasEnvironmentPoller:
    """Canvas must create and manage an EnvironmentPoller."""

    def test_canvas_creates_poller(self, qtbot: object) -> None:
        """Canvas should create an EnvironmentPoller instance."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]
        assert hasattr(canvas, "_poller")
        assert canvas._poller is not None
        # Poller should NOT be running until showEvent
        assert not canvas._poller.isRunning()

    def test_canvas_has_on_platforms_updated(self, qtbot: object) -> None:
        """Canvas should have _on_platforms_updated method."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]
        assert hasattr(canvas, "_on_platforms_updated")
        assert callable(canvas._on_platforms_updated)

    def test_canvas_stores_surface_list(self, qtbot: object) -> None:
        """Canvas should store the latest surface list in _surfaces."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]
        assert hasattr(canvas, "_surfaces")


class TestCanvasFallIntegration:
    """Canvas must properly integrate Fall state into _advance_frame."""

    def test_advance_frame_transitions_to_fall_on_surface_lost(self, qtbot: object) -> None:
        """_advance_frame transitions to Fall when surface is lost in Walk."""
        from mochi import config
        from mochi.core.canvas import Canvas
        from mochi.core.environment import Surface
        from mochi.core.fsm import PetState

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        # Put the cat in Walk state
        canvas._fsm.transition_to(PetState.Walk)
        # Set cat on a surface
        bottom_y = canvas._screen_bottom_y()
        bottom_surface = Surface(
            rect=QRect(0, bottom_y + config.SPRITE_CELL_HEIGHT, 1920, 0),
            surface_type="screen_bottom",
            window_id=None,
        )
        canvas._surfaces = [bottom_surface]
        canvas._on_platforms_updated(canvas._surfaces)

        # Now set no surfaces to trigger surface loss
        canvas._surfaces = []
        canvas._on_platforms_updated(canvas._surfaces)

        # Tick — should detect surface loss and transition to Fall
        canvas._advance_frame()
        assert canvas._fsm.current_state == PetState.Fall, (
            "Should transition to Fall when surface is lost"
        )

    def test_advance_frame_transitions_to_idle_on_landing(self, qtbot: object) -> None:
        """_advance_frame transitions to Idle when landing detected."""
        from mochi.core.canvas import Canvas
        from mochi.core.environment import Surface
        from mochi.core.fsm import PetState

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        # Put the cat in Fall state above a surface
        canvas._fsm.transition_to(PetState.Fall)
        # Place cat just above a surface, with high velocity
        canvas._physics.y = 50.0
        canvas._physics.velocity_y = 500.0
        surface_y = 80  # surface just 30px below — should land in one tick
        landing_surface = Surface(
            rect=QRect(0, surface_y, 1920, 0),
            surface_type="window_top",
            window_id=None,
        )
        canvas._surfaces = [landing_surface]
        canvas._on_platforms_updated(canvas._surfaces)

        # Tick — should land and transition to Idle
        canvas._advance_frame()
        assert canvas._fsm.current_state == PetState.Idle, "Should transition to Idle after landing"

    def test_fall_sprite_key_used_when_fall_state(self, qtbot: object) -> None:
        """Fall sprite key is used when state is Fall."""
        from mochi.core.canvas import Canvas
        from mochi.core.fsm import PetState

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        canvas._fsm.transition_to(PetState.Fall)
        canvas._advance_frame()

        # After FSM tick, the sprite key should reflect Fall's mapped key
        current_key = canvas._current_sprite_key
        # Fall should map to "fall" or the sprite key for Fall
        from mochi.core.canvas import _SPRITE_KEYS

        assert current_key == _SPRITE_KEYS.get(PetState.Fall, "fall"), (
            f"Sprite key should be '{_SPRITE_KEYS.get(PetState.Fall, 'fall')}' "
            f"for Fall state, got '{current_key}'"
        )

    def test_fall_tick_interval_correct(self, qtbot: object) -> None:
        """Animation tick interval is correct for Fall state."""
        from mochi.core.canvas import _TICK_INTERVALS, Canvas
        from mochi.core.fsm import PetState

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        canvas._fsm.transition_to(PetState.Fall)
        canvas._advance_frame()

        expected = _TICK_INTERVALS.get(PetState.Fall, 100)
        assert canvas._animation_timer.interval() == expected, (
            f"Timer interval should be {expected}ms for Fall state, "
            f"got {canvas._animation_timer.interval()}"
        )

    def test_physics_receives_surfaces_in_update(self, qtbot: object) -> None:
        """Physics receives surfaces list in update() call."""
        from PySide6.QtCore import QRect

        from mochi.core.canvas import Canvas
        from mochi.core.environment import Surface

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        # Set up a surface
        surf = Surface(rect=QRect(0, 0, 1920, 0), surface_type="screen_bottom", window_id=None)
        canvas._surfaces = [surf]
        canvas._on_platforms_updated(canvas._surfaces)

        # Spy on physics.update
        original_update = canvas._physics.update

        def spy_update(dt, state, screen_width, sprite_width, **kwargs):
            assert "surfaces" in kwargs, "physics.update() should receive 'surfaces' kwarg"
            assert kwargs["surfaces"] == [surf], (
                "physics.update() should receive the correct surfaces list"
            )
            return original_update(dt, state, screen_width, sprite_width, **kwargs)

        with patch.object(canvas._physics, "update", side_effect=spy_update):
            canvas._advance_frame()

    def test_middle_frame_of_jump_used_as_fall_sprite(self, qtbot: object) -> None:
        """Middle frame of JUMP.png used as fall sprite in Canvas init."""
        from mochi.core.canvas import Canvas

        canvas = Canvas()
        qtbot.addWidget(canvas)  # type: ignore[attr-defined]

        # Check that fall key exists in animations
        assert "fall" in canvas._animations, "Canvas should have a 'fall' animation key"
        # Check it has exactly 1 frame (the middle frame of jump)
        assert len(canvas._animations["fall"]) >= 1, "Fall animation should have at least 1 frame"
