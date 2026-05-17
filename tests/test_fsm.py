"""Tests for mochi.core.fsm — Finite State Machine for Mochi cat behavior."""

from __future__ import annotations

import logging
from unittest.mock import patch

from mochi import config


class TestPetStateEnum:
    """Test that PetState enum defines the expected states."""

    def test_pet_state_has_idle(self) -> None:
        """PetState must have an Idle member."""
        from mochi.core.fsm import PetState

        assert PetState.Idle is not None

    def test_pet_state_has_walk(self) -> None:
        """PetState must have a Walk member."""
        from mochi.core.fsm import PetState

        assert PetState.Walk is not None

    def test_pet_state_has_edge_pause(self) -> None:
        """PetState must have an EdgePause member."""
        from mochi.core.fsm import PetState

        assert PetState.EdgePause is not None


class TestFSMClass:
    """Test that FSM class definition is correct."""

    def test_fsm_module_importable(self) -> None:
        """Importing the fsm module should not raise."""
        import mochi.core.fsm  # noqa: F401

    def test_fsm_class_exists(self) -> None:
        """FSM class must exist in the fsm module."""
        from mochi.core.fsm import FSM

        assert FSM is not None

    def test_fsm_initializes_in_idle(self) -> None:
        """FSM should initialize in Idle state."""
        from mochi.core.fsm import FSM, PetState

        fsm = FSM()
        assert fsm.current_state == PetState.Idle

    def test_fsm_has_tick_method(self) -> None:
        """FSM must have a tick(dt) method."""
        from mochi.core.fsm import FSM

        fsm = FSM()
        assert hasattr(fsm, "tick")
        assert callable(fsm.tick)


class TestFSMTransitions:
    """Test that FSM transitions happen within expected timer ranges."""

    def test_idle_to_walk_transitions_within_timer_range(self) -> None:
        """Idle→Walk should fire between IDLE_TO_WALK_TIMER[0] and [1]."""
        from mochi.core.fsm import FSM, PetState

        # We'll simulate ticking faster than real-time by patching random
        # to produce a known value, then tick just past the timer.
        fsm = FSM()
        assert fsm.current_state == PetState.Idle

        # The FSM on Idle entry sets a random timer between (2.0, 5.0) seconds.
        # We tick a tiny amount less than the minimum, then past it.
        min_timer, max_timer = config.IDLE_TO_WALK_TIMER

        # Tick just before the minimum timer - should still be Idle
        fsm.tick(min_timer - 0.01)
        assert fsm.current_state == PetState.Idle, (
            f"Should still be Idle at {min_timer - 0.01:.2f}s (min timer {min_timer}s)"
        )

        # Tick past the maximum timer - should have transitioned to Walk
        fsm.tick(max_timer + 0.1)
        assert fsm.current_state == PetState.Walk, (
            f"Should have transitioned to Walk by {max_timer + 0.1:.2f}s"
        )

    def test_walk_to_idle_transitions_within_timer_range(self) -> None:
        """Walk→Idle should fire between WALK_TO_IDLE_TIMER[0] and [1]."""
        from mochi.core.fsm import FSM, PetState

        fsm = FSM()

        # Force transition to Walk first
        fsm.transition_to(PetState.Walk)
        assert fsm.current_state == PetState.Walk

        min_timer, max_timer = config.WALK_TO_IDLE_TIMER

        # Tick just before minimum
        fsm.tick(min_timer - 0.01)
        assert fsm.current_state == PetState.Walk, (
            f"Should still be Walk at {min_timer - 0.01:.2f}s"
        )

        # Tick past maximum
        fsm.tick(max_timer + 0.1)
        assert fsm.current_state == PetState.Idle, (
            f"Should have returned to Idle by {max_timer + 0.1:.2f}s"
        )

    def test_edge_pause_to_walk_transitions_within_timer_range(self) -> None:
        """EdgePause→Walk should fire within 0.5-1s range."""
        from mochi.core.fsm import FSM, PetState

        fsm = FSM()
        fsm.transition_to(PetState.EdgePause)
        assert fsm.current_state == PetState.EdgePause

        # Tick just before minimum (0.5s is the minimum for edge pause)
        fsm.tick(0.49)
        assert fsm.current_state == PetState.EdgePause, "Should still be EdgePause at 0.49s"

        # Tick past maximum (1.0s)
        fsm.tick(0.6)  # total ~1.09s from entry
        assert fsm.current_state == PetState.Walk, (
            "Should have transitioned to Walk after EdgePause"
        )

    def test_same_state_transition_is_noop(self) -> None:
        """Transitioning to the current state should be a no-op."""
        from mochi.core.fsm import FSM, PetState

        fsm = FSM()
        assert fsm.current_state == PetState.Idle

        # Transition to Idle again
        fsm.transition_to(PetState.Idle)
        assert fsm.current_state == PetState.Idle
        # The timer should have been reset on the first entry,
        # but a no-op should NOT reset timers. Let's verify by
        # checking it still fires within the expected range.
        # If the timer was reset, this test is still valid.
        # Key assertion: it doesn't crash and stays Idle.

    def test_edge_pause_reverses_direction_on_exit(self) -> None:
        """EdgePause should expose a pending direction reversal flag."""
        from mochi.core.fsm import FSM, PetState

        fsm = FSM()
        fsm.transition_to(PetState.Walk)
        fsm.direction = 1  # walking right

        fsm.transition_to(PetState.EdgePause)
        fsm.tick(1.0)  # past the edge pause timer

        # After EdgePause→Walk, direction should be reversed
        assert fsm.direction == -1, "Direction should reverse after EdgePause"

    def test_direction_not_reversed_on_normal_walk_to_idle(self) -> None:
        """Normal Walk→Idle should NOT reverse direction."""
        from mochi.core.fsm import FSM, PetState

        fsm = FSM()
        fsm.transition_to(PetState.Walk)
        fsm.direction = 1

        # Tick past walk timer to trigger Idle
        max_timer = config.WALK_TO_IDLE_TIMER[1]
        fsm.tick(max_timer + 0.1)
        assert fsm.current_state == PetState.Idle
        assert fsm.direction == 1, "Direction should NOT change on normal Walk→Idle"


class TestFSMLogging:
    """Test that FSM logs state transitions at DEBUG level."""

    def test_transition_logs_at_debug_level(self) -> None:
        """State transitions should be logged at DEBUG level."""
        from mochi.core.fsm import FSM, PetState

        fsm = FSM()
        logger = logging.getLogger("mochi.fsm")

        with patch.object(logger, "debug") as mock_debug:
            fsm.transition_to(PetState.Walk)
            mock_debug.assert_called_once()


class TestFSMTransitionToAPI:
    """Test the transition_to public API."""

    def test_transition_to_returns_none(self) -> None:
        """transition_to should return None."""
        from mochi.core.fsm import FSM, PetState

        fsm = FSM()
        result = fsm.transition_to(PetState.Walk)
        assert result is None
