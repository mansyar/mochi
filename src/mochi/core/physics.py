"""Physics engine for Mochi cat horizontal movement and vertical gravity.

Provides the ``Physics`` class which tracks position (x, y, velocity_y),
direction, and handles frame-rate-independent movement with configurable
overshoot at screen edges.  Supports Walk (horizontal), Fall (gravity),
and Idle/EdgePause (stationary) states via ``PhysicsResult`` signalling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mochi import config
from mochi.core.fsm import PetState

# Tolerance (px) for checking whether the cat is standing on a surface.
_SUPPORT_TOLERANCE = 4.0

# Hard limit to prevent the cat from falling indefinitely.
_FALLBACK_GROUND_Y = 10000


@dataclass
class PhysicsResult:
    """Result of a Physics.update() call.

    Attributes
    ----------
    edge_hit : bool
        ``True`` when Walk state reaches a screen edge.
    surface_lost : bool
        ``True`` when Walk state has no supporting surface below.
    landed : bool
        ``True`` when Fall state lands on a surface.
    """

    edge_hit: bool = False
    surface_lost: bool = False
    landed: bool = False


class Physics:
    """Tracks cat position and handles horizontal and vertical movement.

    The physics object is stateless with respect to the FSM — it receives
    the current state each tick and moves the cat accordingly.

    Parameters
    ----------
    x : float, optional
        Initial horizontal position (default 0).
    y : float, optional
        Initial vertical position (default 0).
    """

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        #: Horizontal position (pixels from left edge of screen).
        self.x: float = x
        #: Vertical position (pixels from top edge of screen).
        self.y: float = y
        #: Vertical velocity (px/s, positive = downward).
        self.velocity_y: float = 0.0
        #: Movement direction (+1 right, -1 left).
        self.direction: int = 1

    def update(
        self,
        dt: float,
        state: PetState,
        screen_width: int,
        sprite_width: int,
        surfaces: Any = None,
    ) -> PhysicsResult:
        """Advance physics by *dt* seconds.

        Parameters
        ----------
        dt : float
            Delta time in seconds since the last tick.
        state : PetState
            Current FSM state (movement only occurs in **Walk** / **Fall**).
        screen_width : int
            Width of the screen / available desktop area in pixels.
        sprite_width : int
            Width of the sprite cell in pixels.
        surfaces : Any, optional
            List of ``Surface`` objects for surface-aware physics (default
            ``None``).  Must be iterable with ``rect`` and ``surface_type``
            attributes when provided.

        Returns
        -------
        PhysicsResult
            Signals for edge-hit, surface-loss, and landing events.
        """
        result = PhysicsResult()
        surfaces_list = surfaces if surfaces is not None else []

        # ── Fall state: gravity acceleration ────────────────────────────
        if state is PetState.Fall:
            # Record position before gravity to detect surface crossing
            pre_fall_y = self.y

            self.velocity_y += config.GRAVITY * dt
            self.velocity_y = min(self.velocity_y, config.TERMINAL_VELOCITY)
            self.y += self.velocity_y * dt

            # Landing detection — check if cat passed through a surface
            result.landed = self._detect_landing(surfaces_list, sprite_width, pre_fall_y=pre_fall_y)

            if result.landed:
                self.velocity_y = 0.0
            else:
                # Hard clamp to prevent infinite fall off the screen
                if self.y >= _FALLBACK_GROUND_Y:
                    self.y = float(_FALLBACK_GROUND_Y)
                    self.velocity_y = 0.0
                    result.landed = True

            return result

        # ── Non-Fall states: reset vertical velocity ────────────────────
        self.velocity_y = 0.0

        # ── Non-Walk states (Idle, EdgePause): no movement ──────────────
        if state is not PetState.Walk:
            return result

        # ── Walk state: horizontal movement + boundary detection ────────
        half = sprite_width / 2.0

        # ── Boundary limits ────────────────────────────────────────────
        edge_trigger_right = screen_width - half
        edge_trigger_left = -half

        # ── Pre-movement check: already past overshoot threshold? ──────
        if self.direction > 0 and self.x > edge_trigger_right:
            result.edge_hit = True
            self.x = edge_trigger_right
        elif self.direction < 0 and self.x < edge_trigger_left:
            result.edge_hit = True
            self.x = edge_trigger_left
        else:
            # ── Apply movement ─────────────────────────────────────────
            self.x += config.WALK_SPEED * dt * self.direction

            # ── Clamp so leading edge does not exceed overshoot ────────
            self.x = max(edge_trigger_left, min(self.x, edge_trigger_right))

            # ── Post-movement check: crossed boundary this tick? ────────
            if (self.direction > 0 and self.x >= edge_trigger_right) or (
                self.direction < 0 and self.x <= edge_trigger_left
            ):
                result.edge_hit = True

        # ── Surface-loss detection (after movement) ─────────────────────
        result.surface_lost = not self._is_supported(surfaces_list, sprite_width)

        return result

    # ── Private helpers ─────────────────────────────────────────────────

    def _is_supported(self, surfaces: list[Any], sprite_width: int) -> bool:
        """Check whether the cat is standing on a supporting surface."""
        if not surfaces:
            return False

        pet_center_x = self.x + sprite_width / 2.0
        pet_bottom = self.y + config.SPRITE_CELL_HEIGHT

        for s in surfaces:
            if not hasattr(s, "surface_type"):
                continue
            if s.surface_type not in ("window_top", "screen_bottom"):
                continue

            surface_top = float(s.rect.y())
            # Vertical support check: pet bottom is at or near surface top
            if (
                abs(pet_bottom - surface_top) <= _SUPPORT_TOLERANCE
                and s.rect.left() - _SUPPORT_TOLERANCE
                <= pet_center_x
                <= s.rect.right() + _SUPPORT_TOLERANCE
            ):
                return True

        return False

    def _detect_landing(
        self, surfaces: list[Any], sprite_width: int, pre_fall_y: float | None = None
    ) -> bool:
        """Detect if the cat has landed on a surface during fall.

        Uses ``pre_fall_y`` (the Y before gravity was applied) to determine
        whether the cat crossed a surface boundary during this tick.

        Returns ``True`` and snaps position if landing is found.
        """
        pet_center_x = self.x + sprite_width / 2.0
        pet_bottom = self.y + config.SPRITE_CELL_HEIGHT
        cat_top = pre_fall_y if pre_fall_y is not None else self.y

        # Priority: check surfaces in order (topmost/z-order first)
        for s in surfaces:
            if not hasattr(s, "surface_type"):
                continue
            if s.surface_type not in ("window_top", "screen_bottom"):
                continue

            surface_top = float(s.rect.y())
            # Cat must have been above the surface at the start of this tick
            if cat_top >= surface_top:
                continue
            # Check vertical: pet bottom >= surface top AND horizontal overlap
            if (
                pet_bottom >= surface_top
                and s.rect.left() - _SUPPORT_TOLERANCE
                <= pet_center_x
                <= s.rect.right() + _SUPPORT_TOLERANCE
            ):
                # Snap to surface
                self.y = surface_top - config.SPRITE_CELL_HEIGHT
                return True

        return False
