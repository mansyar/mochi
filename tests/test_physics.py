"""Tests for mochi.core.physics — Horizontal movement & screen boundary logic."""

from __future__ import annotations

import pytest

from mochi import config
from mochi.core.fsm import PetState


class TestPhysicsClass:
    """Test that Physics class definition is correct."""

    def test_physics_module_importable(self) -> None:
        """Importing the physics module should not raise."""
        import mochi.core.physics  # noqa: F401

    def test_physics_class_exists(self) -> None:
        """Physics class must exist in the physics module."""
        from mochi.core.physics import Physics

        assert Physics is not None

    def test_physics_initializes_at_origin(self) -> None:
        """Physics should initialize at (0, 0) by default."""
        from mochi.core.physics import Physics

        p = Physics()
        assert p.x == 0
        assert p.y == 0

    def test_physics_initial_direction_is_right(self) -> None:
        """Physics should initialize with direction +1 (right)."""
        from mochi.core.physics import Physics

        p = Physics()
        assert p.direction == 1

    def test_physics_has_update_method(self) -> None:
        """Physics must have an update method."""
        from mochi.core.physics import Physics

        p = Physics()
        assert hasattr(p, "update")
        assert callable(p.update)


class TestPhysicsMovement:
    """Test horizontal movement at WALK_SPEED."""

    def test_walk_state_applies_horizontal_displacement(self) -> None:
        """In Walk state, x should increase by WALK_SPEED * dt."""
        from mochi.core.physics import Physics

        p = Physics()
        p.x = 100.0

        dt = 1.0
        edge_hit = p.update(dt, PetState.Walk, screen_width=1920, sprite_width=80)

        expected_x = 100.0 + config.WALK_SPEED * dt
        assert p.x == pytest.approx(expected_x, rel=1e-6)
        assert not edge_hit, "Should not signal edge hit in middle of screen"

    def test_walk_state_moves_left_when_direction_negative(self) -> None:
        """When direction is -1, x should decrease."""
        from mochi.core.physics import Physics

        p = Physics()
        p.x = 500.0
        p.direction = -1

        dt = 0.5
        edge_hit = p.update(dt, PetState.Walk, screen_width=1920, sprite_width=80)

        expected_x = 500.0 - config.WALK_SPEED * dt
        assert p.x == pytest.approx(expected_x, rel=1e-6)
        assert not edge_hit

    def test_idle_state_results_in_zero_movement(self) -> None:
        """In Idle state, x should not change."""
        from mochi.core.physics import Physics

        p = Physics()
        p.x = 250.0
        initial_x = p.x

        edge_hit = p.update(5.0, PetState.Idle, screen_width=1920, sprite_width=80)

        assert p.x == pytest.approx(initial_x, rel=1e-6)
        assert not edge_hit, "Idle should never signal edge hit"

    def test_edge_pause_state_results_in_zero_movement(self) -> None:
        """In EdgePause state, x should not change."""
        from mochi.core.physics import Physics

        p = Physics()
        p.x = 250.0
        initial_x = p.x

        edge_hit = p.update(5.0, PetState.EdgePause, screen_width=1920, sprite_width=80)

        assert p.x == pytest.approx(initial_x, rel=1e-6)
        assert not edge_hit, "EdgePause should never signal edge hit"

    def test_movement_matches_expected_displacement_over_multiple_ticks(self) -> None:
        """Multiple ticks should produce cumulative displacement."""
        from mochi.core.physics import Physics

        p = Physics()
        p.x = 0.0

        total_dt = 0.0
        for _ in range(10):
            result = p.update(0.1, PetState.Walk, screen_width=1920, sprite_width=80)
            total_dt += 0.1
            # Should not hit edge when starting from 0 and moving right
            assert not result

        expected_x = config.WALK_SPEED * total_dt
        assert p.x == pytest.approx(expected_x, rel=1e-6)


class TestPhysicsScreenBounds:
    """Test screen boundary detection with half-sprite overshoot."""

    SPRITE_WIDTH = 80
    SCREEN_WIDTH = 1920

    def test_right_edge_signals_edge_hit(self) -> None:
        """Walking past right edge should signal edge-hit."""
        from mochi.core.physics import Physics

        p = Physics()
        p.direction = 1
        # Place near the right edge: screen_width - half_sprite + small offset
        half = self.SPRITE_WIDTH / 2
        p.x = self.SCREEN_WIDTH - half + 1  # just past overshoot threshold

        edge_hit = p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        assert edge_hit, "Should signal edge hit at right boundary"

    def test_left_edge_signals_edge_hit(self) -> None:
        """Walking past left edge should signal edge-hit."""
        from mochi.core.physics import Physics

        p = Physics()
        p.direction = -1
        half = self.SPRITE_WIDTH / 2
        p.x = -(half + 1)  # past the left overshoot threshold

        edge_hit = p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        assert edge_hit, "Should signal edge hit at left boundary"

    def test_half_sprite_overshoot_allowed_before_edge_hit(self) -> None:
        """Cat at overshoot boundary that moves past triggers edge hit and gets clamped."""
        from mochi.core.physics import Physics

        p = Physics()
        p.direction = 1
        half = self.SPRITE_WIDTH / 2
        p.x = self.SCREEN_WIDTH - half  # exactly at overshoot boundary

        edge_hit = p.update(0.01, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        # Movement pushes past boundary → edge hit, position clamped back to boundary
        assert edge_hit, "Moving past overshoot boundary should signal edge hit"
        assert p.x == pytest.approx(self.SCREEN_WIDTH - half, rel=1e-6), (
            "Position should be clamped to overshoot boundary"
        )

    def test_physics_does_not_reverse_direction_on_edge_hit(self) -> None:
        """Physics should signal edge-hit but NOT reverse direction."""
        from mochi.core.physics import Physics

        p = Physics()
        p.direction = 1
        half = self.SPRITE_WIDTH / 2
        p.x = self.SCREEN_WIDTH - half + 10  # past right edge

        edge_hit = p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        assert edge_hit
        assert p.direction == 1, "Physics should NOT reverse direction"

    def test_no_edge_hit_when_within_valid_bounds(self) -> None:
        """Cat in middle of screen should not signal edge hit."""
        from mochi.core.physics import Physics

        p = Physics()
        p.x = self.SCREEN_WIDTH / 2

        edge_hit = p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        assert not edge_hit

    def test_clamps_position_at_extreme_right(self) -> None:
        """Cat position should be clamped to overshoot boundary at right edge."""
        from mochi.core.physics import Physics

        p = Physics()
        p.direction = 1
        p.x = 99999.0  # way past right edge

        p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        expected = self.SCREEN_WIDTH - self.SPRITE_WIDTH / 2
        assert p.x == pytest.approx(expected, rel=1e-6), (
            f"x ({p.x}) should be clamped to {expected}"
        )

    def test_clamps_position_at_extreme_left(self) -> None:
        """Cat position should not exceed -(half_sprite)."""
        from mochi.core.physics import Physics

        p = Physics()
        p.direction = -1
        p.x = -99999.0  # way past left edge

        p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        min_allowed = -(self.SPRITE_WIDTH / 2)
        assert p.x >= min_allowed, f"x ({p.x}) should not be less than {min_allowed}"

    def test_update_returns_false_when_already_at_edge_and_moving_away(self) -> None:
        """If cat is at edge but moving away, no edge hit."""
        from mochi.core.physics import Physics

        p = Physics()
        p.direction = -1  # moving left (away from right edge)
        half = self.SPRITE_WIDTH / 2
        p.x = self.SCREEN_WIDTH - half + 10  # past right edge

        # Moving left = towards screen center, should not signal edge hit
        edge_hit = p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        assert not edge_hit, "Moving away from edge should not signal edge hit"

    def test_edge_hit_on_right_while_moving_left_does_not_trigger(self) -> None:
        """Edge hit should depend on movement direction, not position alone."""
        from mochi.core.physics import Physics

        p = Physics()
        p.direction = -1  # moving left
        p.x = self.SCREEN_WIDTH + self.SPRITE_WIDTH  # far right

        # Moving left from far right — no edge hit since we're moving away from right edge
        edge_hit = p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        assert not edge_hit, "Moving left should not trigger right-edge hit"


class TestPhysicsAPI:
    """Test the Physics API surface."""

    def test_update_accepts_surfaces_none(self) -> None:
        """update() should accept surfaces=None (forward-compat with Phase 2)."""
        from mochi.core.physics import Physics

        p = Physics()
        # Should not raise
        result = p.update(1.0, PetState.Idle, screen_width=1920, sprite_width=80, surfaces=None)
        assert isinstance(result, bool)

    def test_update_returns_bool(self) -> None:
        """update() should return a bool."""
        from mochi.core.physics import Physics

        p = Physics()
        result = p.update(1.0, PetState.Idle, 1920, 80)
        assert isinstance(result, bool)
