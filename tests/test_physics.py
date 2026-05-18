"""Tests for mochi.core.physics — Horizontal movement, screen boundary logic, gravity & landing."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QRect

from mochi import config
from mochi.core.environment import Surface
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
        result = p.update(dt, PetState.Walk, screen_width=1920, sprite_width=80)

        expected_x = 100.0 + config.WALK_SPEED * dt
        assert p.x == pytest.approx(expected_x, rel=1e-6)
        assert not result.edge_hit, "Should not signal edge hit in middle of screen"

    def test_walk_state_moves_left_when_direction_negative(self) -> None:
        """When direction is -1, x should decrease."""
        from mochi.core.physics import Physics

        p = Physics()
        p.x = 500.0
        p.direction = -1

        dt = 0.5
        result = p.update(dt, PetState.Walk, screen_width=1920, sprite_width=80)

        expected_x = 500.0 - config.WALK_SPEED * dt
        assert p.x == pytest.approx(expected_x, rel=1e-6)
        assert not result.edge_hit

    def test_idle_state_results_in_zero_movement(self) -> None:
        """In Idle state, x should not change."""
        from mochi.core.physics import Physics

        p = Physics()
        p.x = 250.0
        initial_x = p.x

        result = p.update(5.0, PetState.Idle, screen_width=1920, sprite_width=80)

        assert p.x == pytest.approx(initial_x, rel=1e-6)
        assert not result.edge_hit, "Idle should never signal edge hit"

    def test_edge_pause_state_results_in_zero_movement(self) -> None:
        """In EdgePause state, x should not change."""
        from mochi.core.physics import Physics

        p = Physics()
        p.x = 250.0
        initial_x = p.x

        result = p.update(5.0, PetState.EdgePause, screen_width=1920, sprite_width=80)

        assert p.x == pytest.approx(initial_x, rel=1e-6)
        assert not result.edge_hit, "EdgePause should never signal edge hit"

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
            assert not result.edge_hit

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

        result = p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        assert result.edge_hit, "Should signal edge hit at right boundary"

    def test_left_edge_signals_edge_hit(self) -> None:
        """Walking past left edge should signal edge-hit."""
        from mochi.core.physics import Physics

        p = Physics()
        p.direction = -1
        half = self.SPRITE_WIDTH / 2
        p.x = -(half + 1)  # past the left overshoot threshold

        result = p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        assert result.edge_hit, "Should signal edge hit at left boundary"

    def test_half_sprite_overshoot_allowed_before_edge_hit(self) -> None:
        """Cat at overshoot boundary that moves past triggers edge hit and gets clamped."""
        from mochi.core.physics import Physics

        p = Physics()
        p.direction = 1
        half = self.SPRITE_WIDTH / 2
        p.x = self.SCREEN_WIDTH - half  # exactly at overshoot boundary

        result = p.update(0.01, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        # Movement pushes past boundary → edge hit, position clamped back to boundary
        assert result.edge_hit, "Moving past overshoot boundary should signal edge hit"
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

        result = p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        assert result.edge_hit
        assert p.direction == 1, "Physics should NOT reverse direction"

    def test_no_edge_hit_when_within_valid_bounds(self) -> None:
        """Cat in middle of screen should not signal edge hit."""
        from mochi.core.physics import Physics

        p = Physics()
        p.x = self.SCREEN_WIDTH / 2

        result = p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        assert not result.edge_hit

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
        result = p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        assert not result.edge_hit, "Moving away from edge should not signal edge hit"

    def test_edge_hit_on_right_while_moving_left_does_not_trigger(self) -> None:
        """Edge hit should depend on movement direction, not position alone."""
        from mochi.core.physics import Physics

        p = Physics()
        p.direction = -1  # moving left
        p.x = self.SCREEN_WIDTH + self.SPRITE_WIDTH  # far right

        # Moving left from far right — no edge hit since we're moving away from right edge
        result = p.update(1.0, PetState.Walk, self.SCREEN_WIDTH, self.SPRITE_WIDTH)

        assert not result.edge_hit, "Moving left should not trigger right-edge hit"


class TestPhysicsAPI:
    """Test the Physics API surface."""

    def test_update_accepts_surfaces_none(self) -> None:
        """update() should accept surfaces=None (forward-compat with Phase 2)."""
        from mochi.core.physics import Physics, PhysicsResult

        p = Physics()
        # Should not raise
        result = p.update(1.0, PetState.Idle, screen_width=1920, sprite_width=80, surfaces=None)
        assert isinstance(result, PhysicsResult)

    def test_update_returns_physics_result(self) -> None:
        """update() should return a PhysicsResult."""
        from mochi.core.physics import Physics, PhysicsResult

        p = Physics()
        result = p.update(1.0, PetState.Idle, 1920, 80)
        assert isinstance(result, PhysicsResult)


class TestPhysicsGravity:
    """Test gravity acceleration and terminal velocity in Fall state."""

    def test_velocity_y_starts_at_zero(self) -> None:
        """Physics initializes with velocity_y == 0.0."""
        from mochi.core.physics import Physics

        p = Physics()
        assert p.velocity_y == pytest.approx(0.0)

    def test_gravity_accelerates_in_fall_state(self) -> None:
        """In Fall state, velocity_y increases by GRAVITY * dt."""
        from mochi.core.physics import Physics

        p = Physics()
        p.velocity_y = 0.0
        dt = 0.5

        p.update(dt, PetState.Fall, 1920, 80)

        expected = config.GRAVITY * dt
        assert p.velocity_y == pytest.approx(expected, rel=1e-6), (
            f"velocity_y should be {expected}, got {p.velocity_y}"
        )

    def test_terminal_velocity_cap(self) -> None:
        """velocity_y should not exceed TERMINAL_VELOCITY after extended fall."""
        from mochi.core.physics import Physics

        p = Physics()
        p.velocity_y = 0.0
        # Fall for a long time — should cap at terminal velocity
        for _ in range(100):
            p.update(0.1, PetState.Fall, 1920, 80)

        assert p.velocity_y <= config.TERMINAL_VELOCITY + 1e-6, (
            f"velocity_y ({p.velocity_y}) should be capped at {config.TERMINAL_VELOCITY}"
        )
        # Should be at or very near terminal velocity
        assert p.velocity_y == pytest.approx(config.TERMINAL_VELOCITY, rel=0.1)

    def test_velocity_y_zero_in_non_fall_states(self) -> None:
        """In non-Fall states, velocity_y stays 0.0."""
        from mochi.core.physics import Physics

        p = Physics()
        p.velocity_y = 999.0  # set high value

        for state in (PetState.Idle, PetState.Walk, PetState.EdgePause):
            p.velocity_y = 999.0
            p.update(1.0, state, 1920, 80)
            assert p.velocity_y == pytest.approx(0.0), (
                f"velocity_y should be 0.0 in {state}, got {p.velocity_y}"
            )

    def test_y_increases_during_fall(self) -> None:
        """y position increases (falls) when velocity_y > 0."""
        from mochi.core.physics import Physics

        p = Physics()
        p.y = 100.0
        p.velocity_y = 0.0

        p.update(1.0, PetState.Fall, 1920, 80)

        assert p.y > 100.0, f"y ({p.y}) should have increased during fall"

    def test_physics_has_velocity_y_attribute(self) -> None:
        """Physics class must have velocity_y attribute."""
        from mochi.core.physics import Physics

        p = Physics()
        assert hasattr(p, "velocity_y")


class TestPhysicsLanding:
    """Test landing detection when falling onto surfaces."""

    def _make_surface(self, y: int, width: int = 1920, surface_type: str = "window_top") -> Surface:
        return Surface(rect=QRect(0, y, width, 0), surface_type=surface_type, window_id=None)

    def test_land_on_surface_snaps_y(self) -> None:
        """Landing on a surface below snaps y to surface top - SPRITE_CELL_HEIGHT."""
        from mochi.core.physics import Physics

        p = Physics()
        p.y = 200.0  # cat above a surface
        p.velocity_y = 500.0

        surfaces = [self._make_surface(y=500)]
        result = p.update(1.0, PetState.Fall, 1920, 80, surfaces=surfaces)

        assert result.landed, "Should indicate landing"
        expected_y = 500 - config.SPRITE_CELL_HEIGHT  # surface_top - cell_height
        assert p.y == pytest.approx(expected_y, rel=1e-6), f"y ({p.y}) should snap to {expected_y}"

    def test_landing_zeroes_velocity(self) -> None:
        """Landing should zero velocity_y."""
        from mochi.core.physics import Physics

        p = Physics()
        p.y = 200.0
        p.velocity_y = 500.0

        surfaces = [self._make_surface(y=500)]
        p.update(1.0, PetState.Fall, 1920, 80, surfaces=surfaces)

        assert p.velocity_y == pytest.approx(0.0), (
            f"velocity_y ({p.velocity_y}) should be 0 after landing"
        )

    def test_land_on_screen_bottom(self) -> None:
        """Landing on screen_bottom works when no window surfaces exist."""
        from mochi.core.physics import Physics

        p = Physics()
        p.y = 900.0
        p.velocity_y = 500.0

        surfaces = [self._make_surface(y=1000, surface_type="screen_bottom")]
        result = p.update(1.0, PetState.Fall, 1920, 80, surfaces=surfaces)

        assert result.landed, "Should land on screen_bottom"
        expected_y = 1000 - config.SPRITE_CELL_HEIGHT
        assert p.y == pytest.approx(expected_y, rel=1e-6)

    def test_landing_requires_horizontal_overlap(self) -> None:
        """Landing should only trigger when horizontal overlap exists."""
        from mochi.core.physics import Physics

        p = Physics()
        p.x = 2000.0  # far right, outside any surface
        p.y = 200.0
        p.velocity_y = 500.0

        # Surface spans x=0 to x=1920, cat is at x=2000 — no overlap
        surfaces = [self._make_surface(y=500, width=1920)]
        result = p.update(1.0, PetState.Fall, 1920, 80, surfaces=surfaces)

        assert not result.landed, "Should NOT land — no horizontal overlap"

    def test_lands_on_topmost_surface(self) -> None:
        """Cat lands on first (topmost/highest Z) surface when multiple overlap."""
        from mochi.core.physics import Physics

        p = Physics()
        p.y = 200.0
        p.velocity_y = 500.0

        # Two surfaces at different Y — should land on the higher (lower Y value) one
        surfaces = [
            self._make_surface(y=300),  # higher surface — should land here
            self._make_surface(y=500),  # lower surface — should NOT reach
        ]
        result = p.update(1.0, PetState.Fall, 1920, 80, surfaces=surfaces)

        assert result.landed
        expected_y = 300 - config.SPRITE_CELL_HEIGHT
        assert p.y == pytest.approx(expected_y, rel=1e-6), (
            f"y ({p.y}) should snap to topmost surface at {expected_y}"
        )

    def test_no_landing_if_no_surface_below(self) -> None:
        """No landing if no surface below (cat keeps falling)."""
        from mochi.core.physics import Physics

        p = Physics()
        p.y = 100.0
        p.velocity_y = 500.0

        # Surface is above the cat, not below
        surfaces = [self._make_surface(y=50)]
        result = p.update(1.0, PetState.Fall, 1920, 80, surfaces=surfaces)

        assert not result.landed, "Should NOT land — surface is above cat"
        # y should have increased (fell)
        assert p.y > 100.0

    def test_fall_through_without_landing(self) -> None:
        """Without surfaces, the cat keeps falling (no landing)."""
        from mochi.core.physics import Physics

        p = Physics()
        p.y = 100.0
        p.velocity_y = 600.0

        # Empty surfaces list — should keep falling (no landing)
        result = p.update(10.0, PetState.Fall, 1920, 80, surfaces=[])

        # No surfaces to land on, cat keeps falling
        assert not result.landed, "Should NOT land — no surfaces to land on"
        # Y should have increased significantly
        assert p.y > 1000.0, f"y ({p.y}) should be far below starting position"

    def test_result_landed_true_on_landing(self) -> None:
        """PhysicsResult.landed is True when Fall state lands on a surface."""
        from mochi.core.physics import Physics

        p = Physics()
        p.y = 200.0
        p.velocity_y = 500.0

        surfaces = [self._make_surface(y=500)]
        result = p.update(1.0, PetState.Fall, 1920, 80, surfaces=surfaces)

        assert result.landed

    def test_result_edge_hit_still_works_in_walk(self) -> None:
        """PhysicsResult.edge_hit still works for Walk state at screen edges."""
        from mochi.core.physics import Physics

        p = Physics()
        p.direction = 1
        half = 40.0
        p.x = 1920 - half + 1  # past right edge

        result = p.update(1.0, PetState.Walk, 1920, 80)
        assert result.edge_hit


class TestPhysicsSurfaceLoss:
    """Test surface-loss detection in Walk state."""

    def _make_surface(self, y: int, width: int = 1920, surface_type: str = "window_top") -> Surface:
        return Surface(rect=QRect(0, y, width, 0), surface_type=surface_type, window_id=None)

    def test_surface_lost_when_no_support(self) -> None:
        """surface_lost is True when Walk state has no supporting surface."""
        from mochi.core.physics import Physics

        p = Physics()
        p.y = 100.0
        p.x = 500.0

        # No surfaces to support the cat
        result = p.update(1.0, PetState.Walk, 1920, 80, surfaces=[])

        assert result.surface_lost, "Should detect surface loss with no surfaces"

    def test_surface_not_lost_when_supported(self) -> None:
        """surface_lost is False when Walk state is supported."""
        from mochi.core.physics import Physics

        p = Physics()
        p.y = 100.0
        p.x = 500.0

        # Surface right at the cat's bottom edge
        surfaces = [self._make_surface(y=100 + config.SPRITE_CELL_HEIGHT)]
        result = p.update(1.0, PetState.Walk, 1920, 80, surfaces=surfaces)

        assert not result.surface_lost, "Should NOT detect surface loss when supported"

    def test_surface_lost_outside_horizontal_bounds(self) -> None:
        """surface_lost is True when cat walks off a narrow window's horizontal edge."""
        from mochi.core.physics import Physics

        p = Physics()
        p.y = 100.0
        p.x = 1000.0  # cat center at 1040 — outside narrow window (width=200, right=199)

        # Narrow window surface (200px wide)
        surfaces = [self._make_surface(y=100 + config.SPRITE_CELL_HEIGHT, width=200)]
        result = p.update(1.0, PetState.Walk, 1920, 80, surfaces=surfaces)

        assert result.surface_lost, (
            "Should detect surface loss when cat center is past window horizontal edge"
        )
