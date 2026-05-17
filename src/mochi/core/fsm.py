"""Finite State Machine for Mochi cat behavior.

Defines the ``PetState`` enum and the ``FSM`` class which drives
autonomous state transitions (Idle, Walk, EdgePause) using timer-based
logic.  Only screen-bottom walking is implemented in this track —
window / platform awareness is deferred to Phase 2.
"""

from __future__ import annotations

import logging
import random

from mochi import config

logger = logging.getLogger("mochi.fsm")


class PetState:
    """Cat behaviour states for the FSM.

    Each instance represents a unique state.  Equality is by identity
    (``is``), so ``PetState.Idle is PetState.Idle`` is ``True``.
    """

    Idle: PetState  #: Sitting / loafing, subtle breathing animation.
    Walk: PetState  #: Horizontal movement along a surface.
    EdgePause: PetState  #: Brief pause at screen edge before reversing.


# --- Define singleton instances ---
PetState.Idle = PetState()
PetState.Walk = PetState()
PetState.EdgePause = PetState()

# Dict lookup for repr / display.
_STATE_NAMES: dict[PetState, str] = {
    PetState.Idle: "Idle",
    PetState.Walk: "Walk",
    PetState.EdgePause: "EdgePause",
}


class FSM:
    """Timer-driven finite state machine for cat behaviour.

    The FSM manages three states (Idle, Walk, EdgePause) with random-timer
    transitions.  It is driven by a ``tick(dt)`` call from the Canvas
    animation loop.

    Parameters
    ----------
    initial_state : PetState, optional
        Starting state (default ``PetState.Idle``).
    """

    def __init__(self, initial_state: PetState = PetState.Idle) -> None:
        #: Current FSM state.
        self._state: PetState = initial_state
        #: Elapsed time in the current state (seconds).
        self._elapsed: float = 0.0
        #: Timer duration for the current state (seconds).
        self._timer: float = 0.0
        #: Direction the cat faces / moves (+1 right, -1 left).
        self.direction: int = 1

        self._set_timer_for_state(self._state)

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def current_state(self) -> PetState:
        """The current FSM state."""
        return self._state

    # ── Public API ───────────────────────────────────────────────────────

    def tick(self, dt: float) -> None:
        """Advance the FSM by *dt* seconds.

        Should be called once per animation tick from the Canvas loop.

        Parameters
        ----------
        dt : float
            Delta time in seconds since the last tick.
        """
        self._elapsed += dt

        if self._elapsed >= self._timer:
            self._on_timer_expired()

    def transition_to(self, state: PetState) -> None:
        """Transition to a new state.

        If *state* is the same as the current state, the call is a no-op
        (the timer is **not** reset).

        Parameters
        ----------
        state : PetState
            The target state.
        """
        if state is self._state:
            return

        old_name = _STATE_NAMES.get(self._state, str(self._state))
        new_name = _STATE_NAMES.get(state, str(state))
        logger.debug("State transition: %s → %s", old_name, new_name)

        self._state = state
        self._elapsed = 0.0
        self._set_timer_for_state(state)

    # ── Internal helpers ─────────────────────────────────────────────────

    def _set_timer_for_state(self, state: PetState) -> None:
        """Set the timer duration for *state* based on config ranges."""
        if state is PetState.Idle:
            low, high = config.IDLE_TO_WALK_TIMER
        elif state is PetState.Walk:
            low, high = config.WALK_TO_IDLE_TIMER
        elif state is PetState.EdgePause:
            low, high = (0.5, 1.0)
        else:
            low, high = (1.0, 1.0)

        self._timer = random.uniform(low, high)

    def _on_timer_expired(self) -> None:
        """Handle a state timer expiry by transitioning to the next state."""
        if self._state is PetState.Idle:
            self.transition_to(PetState.Walk)
        elif self._state is PetState.Walk:
            self.transition_to(PetState.Idle)
        elif self._state is PetState.EdgePause:
            self.direction *= -1  # reverse direction
            self.transition_to(PetState.Walk)
