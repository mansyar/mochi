# Track 2.2 — Gravity, Falling & Ground Snapping

## Phase 1: FSM — Add Fall State [checkpoint: 48e4459]

**Goal:** Add the `Fall` behavior state to the FSM with correct transitions and defensive timer handling.

- [x] Task: Write FSM tests for Fall state [a5558b5]
    - [x] `test_fsm.py`: `PetState.Fall` exists and is not None
    - [x] `test_fsm.py`: Walk→Fall transition on explicit `transition_to(PetState.Fall)`
    - [x] `test_fsm.py`: Fall→Idle transition on explicit `transition_to(PetState.Idle)`
    - [x] `test_fsm.py`: Fall state is immune to timer-based auto-transition — tick with dt=100s and assert state is still Fall
    - [x] `test_fsm.py`: `_on_timer_expired()` does not raise when state is Fall (defensive no-op)

- [x] Task: Add PetState.Fall to FSM [a5558b5]
    - [x] `fsm.py`: Add `Fall` property to `PetState` class and create singleton
    - [x] `fsm.py`: Add `PetState.Fall` to `_STATE_NAMES` dict
    - [x] `fsm.py`: In `_set_timer_for_state`, set Fall's timer to `float('inf')` (physics-driven, never auto-transitions)
    - [x] `fsm.py`: Add defensive Fall case to `_on_timer_expired()` — log a warning, no state change

- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md) [48e4459]

## Phase 2: Physics — Gravity, Landing, and Surface-Loss Detection [checkpoint: 47013ca]

**Goal:** Implement gravity acceleration, terminal velocity capping, landing detection, and surface-loss detection in the Physics engine. Physics.update() return type changes from `bool` to `PhysicsResult`.

- [x] Task: Write PhysicsResult dataclass [b613110]
    - [x] `physics.py`: Define `PhysicsResult` dataclass with `edge_hit: bool = False`, `surface_lost: bool = False`, `landed: bool = False`
    - [x] Re-export `PhysicsResult` from `mochi.core.__init__`

- [x] Task: Write Physics tests for gravity and landing [b613110]
    - [x] `test_physics.py`: Physics class initializes with `velocity_y == 0.0`
    - [x] `test_physics.py`: In Fall state, `velocity_y` increases by `GRAVITY * dt` each tick
    - [x] `test_physics.py`: `velocity_y` does not exceed `TERMINAL_VELOCITY` after extended fall
    - [x] `test_physics.py`: In non-Fall states (Idle, Walk, EdgePause), `velocity_y` stays 0.0
    - [x] `test_physics.py`: `y` position increases (falls) when velocity_y > 0
    - [x] `test_physics.py`: Landing on a surface below snaps `y` to surface top - SPRITE_CELL_HEIGHT
    - [x] `test_physics.py`: Landing zeroes `velocity_y`
    - [x] `test_physics.py`: Landing on screen_bottom works when no window surfaces exist
    - [x] `test_physics.py`: Landing only triggers when horizontal overlap exists
    - [x] `test_physics.py`: Cat lands on first (topmost/highest Z) surface when multiple surfaces exist
    - [x] `test_physics.py`: No landing if no surface below (cat keeps falling)
    - [x] `test_physics.py`: `update()` returns `PhysicsResult` instance (updated existing tests)
    - [x] `test_physics.py`: `PhysicsResult.surface_lost` is True when Walk state has no supporting surface
    - [x] `test_physics.py`: `PhysicsResult.surface_lost` is False when Walk state is supported
    - [x] `test_physics.py`: `PhysicsResult.landed` is True when Fall state lands on a surface
    - [x] `test_physics.py`: Cat keeps falling without landing when surfaces list is empty
    - [x] `test_physics.py`: `PhysicsResult.edge_hit` still works for Walk state at screen edges

- [x] Task: Implement gravity in Physics [b613110]
    - [x] `physics.py`: Add `velocity_y: float` field initialized to 0.0
    - [x] `physics.py`: In `update()`, add Fall branch with gravity acceleration
    - [x] `physics.py`: In non-Fall states, keep `velocity_y = 0.0`

- [x] Task: Implement landing detection in Physics [b613110]
    - [x] `physics.py`: In Fall branch, iterate surfaces with surface_type in ("window_top", "screen_bottom")
    - [x] `physics.py`: Check pet_bottom >= surface_top AND horizontal overlap
    - [x] `physics.py`: On landing: snap y, zero velocity_y, set result.landed = True
    - [x] `physics.py`: Hard clamp fallback at _FALLBACK_GROUND_Y

- [x] Task: Implement surface-loss detection in Physics (Walk state) [b613110]
    - [x] `physics.py`: After Walk horizontal movement, check if any surface supports the cat
    - [x] `physics.py`: Check pet_bottom near surface_top AND horizontal overlap
    - [x] `physics.py`: If no surface supports, set result.surface_lost = True

- [x] Task: Fix screen_bottom surface Y coordinate in environment.py [b613110]
    - [x] `environment.py`: Changed to actual ground line (without SPRITE_CELL_HEIGHT)
    - [x] `test_environment.py`: Updated expected Y to match new formula

- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md) [47013ca]

## Phase 3: Canvas — Wire Fall into Animation Loop

**Goal:** Integrate Fall state, gravity physics, fall sprite (from JUMP.png middle frame), and landing into the Canvas animation loop with correct tick ordering.

- [~] Task: Write Canvas integration tests for Fall
    - [ ] `test_canvas.py`: `_advance_frame` transitions to Fall when surface is lost (mock surfaces)
    - [ ] `test_canvas.py`: `_advance_frame` transitions to Idle when landing detected
    - [ ] `test_canvas.py`: Fall sprite key is used when state is Fall
    - [ ] `test_canvas.py`: Animation tick interval is correct for Fall state
    - [ ] `test_canvas.py`: Middle frame of JUMP.png used as fall sprite in Canvas init
    - [ ] `test_canvas.py`: Physics receives surfaces list in update() call
    - [ ] `test_canvas.py`: `_advance_frame` does NOT reorder — FSM tick runs AFTER physics update

- [ ] Task: Load fall sprite from JUMP.png middle frame
    - [ ] `canvas.py`: In `__init__`, add `"fall": [self._spritesheet.load("jump")[1]]` to `_animations` (frame index 1 of 3)
    - [ ] Guard against IndexError if jump frames are fewer than 2: fallback to empty list with warning

- [ ] Task: Add Fall sprite key and tick interval mappings
    - [ ] `canvas.py`: Add `PetState.Fall: "fall"` to `_SPRITE_KEYS`
    - [ ] `canvas.py`: Add `PetState.Fall: 100` to `_TICK_INTERVALS` (10 FPS — keeps landing detection responsive)

- [ ] Task: Pass surfaces list to Physics.update()
    - [ ] `canvas.py`: In `_advance_frame()`, pass `self._surfaces` to `self._physics.update(..., surfaces=self._surfaces)`

- [ ] Task: Reorder _advance_frame to prevent race condition
    - [ ] `canvas.py`: Change _advance_frame order to:
        1. Compute dt
        2. Sync physics direction from FSM
        3. Call `physics.update(surfaces=...)` → get `PhysicsResult`
        4. If Walk and `result.surface_lost` → `fsm.transition_to(PetState.Fall)`
        5. If Fall and `result.landed` → `fsm.transition_to(PetState.Idle)`
        6. Call `fsm.tick(dt)` — safe: Fall has inf timer
        7. Handle `result.edge_hit` → `fsm.transition_to(PetState.EdgePause)`
        8. Determine sprite key, advance frame, update timer interval, repaint
    - [ ] Update the existing `edge_hit = physics.update(...)` unpack to use `PhysicsResult`

- [ ] Task: Handle surface-loss and landing signals in Canvas
    - [ ] `canvas.py`: After `physics.update()`, check `result.surface_lost` and transition if Walk
    - [ ] `canvas.py`: After `physics.update()`, check `result.landed` and transition if Fall

- [ ] Task: Run full test suite and verify
    - [ ] Run `uv run pytest` — all tests pass
    - [ ] Run `uv run ruff check src/` — zero lint errors
    - [ ] Run `uv run ruff format --check src/` — zero formatting violations
    - [ ] Run `uv run mypy src/mochi/` — zero type errors

- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
