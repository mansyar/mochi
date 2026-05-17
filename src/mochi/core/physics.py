"""Physics engine for Mochi cat horizontal movement and screen-boundary detection.

Provides the ``Physics`` class which tracks position (x, y), direction,
and handles frame-rate-independent movement with configurable overshoot
at screen edges.  Edge events are signalled to the caller (Canvas) via
a boolean return — direction reversal is owned by the FSM, not physics.
"""

from __future__ import annotations

from typing import Any

from mochi import config
from mochi.core.fsm import PetState


class Physics:
    """Tracks cat position and handles horizontal movement.

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
        #: Movement direction (+1 right, -1 left).
        self.direction: int = 1

    def update(
        self,
        dt: float,
        state: PetState,
        screen_width: int,
        sprite_width: int,
        surfaces: Any = None,
    ) -> bool:
        """Advance physics by *dt* seconds.

        Parameters
        ----------
        dt : float
            Delta time in seconds since the last tick.
        state : PetState
            Current FSM state (movement only occurs in ``Walk``).
        screen_width : int
            Width of the screen / available desktop area in pixels.
        sprite_width : int
            Width of the sprite cell in pixels.
        surfaces : Any, optional
            Reserved for Phase 2 window-awareness (default ``None``).

        Returns
        -------
        bool
            ``True`` if the cat has reached or exceeded a screen boundary
            (left or right) while moving in that direction.  The caller
            (Canvas) should handle the edge pause and direction reversal.
            Returns ``False`` otherwise.
        """
        if state is not PetState.Walk:
            return False

        half = sprite_width / 2.0

        # ── Boundary limits ────────────────────────────────────────────
        edge_trigger_right = screen_width - half  # max x for rightward overshoot
        edge_trigger_left = -half  # left edge overshoot bound

        edge_hit = False

        # ── Pre-movement check: already past overshoot threshold? ──────
        if self.direction > 0 and self.x > edge_trigger_right:
            edge_hit = True
            self.x = edge_trigger_right
        elif self.direction < 0 and self.x < edge_trigger_left:
            edge_hit = True
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
                edge_hit = True

        return edge_hit
