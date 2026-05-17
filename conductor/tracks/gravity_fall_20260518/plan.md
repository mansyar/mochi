# Track 2.2 — Gravity, Falling & Ground Snapping

## Phase 1: FSM — Add Fall State

**Goal:** Add the `Fall` behavior state to the FSM with correct transitions.

- [ ] Task: Write FSM tests for Fall state
    - [ ] `test_fsm.py`: `PetState.Fall` exists and is not None
    - [ ] `test_fsm.py`: Walk→Fall transition on explicit `transition_to(PetState.Fall)`
    - [ ] `test_fsm.py`: Fall→Idle transition on explicit `transition_to(PetState.Idle)`
    - [ ] `test_fsm.py`: Fall transitions do NOT use random timers (verify elapsed stays 0 after repeated ticks without external transition)

- [ ] Task: Add PetState.Fall to FSM
    - [ ] `fsm.py`: Add `Fall` property to `PetState` class and create singleton
    - [ ] `fsm.py`: Add `PetState.Fall` to `_STATE_NAMES` dict
    - [ ] `fsm.py`: Add `_set_timer_for_state` handling for Fall (no-op — Fall transitions are physics-driven, not timer-driven)

- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Physics — Vertical Movement & Landing Detection

**Goal:** Implement gravity acceleration, terminal velocity capping, and ground/landing detection in the Physics engine.

- [ ] Task: Write Physics tests for gravity and landing
    - [ ] `test_physics.py`: Physics class initializes with `velocity_y == 0.0`
    - [ ] `test_physics.py`: In Fall state, `velocity_y` increases by `GRAVITY * dt` each tick
    - [ ] `test_physics.py`: `velocity_y` does not exceed `TERMINAL_VELOCITY` after extended fall
    - [ ] `test_physics.py`: In non-Fall states (Idle, Walk, EdgePause), `velocity_y` stays 0.0
    - [ ] `test_physics.py`: `y` position increases (falls) when velocity_y > 0
    - [ ] `test_physics.py`: Landing on a surface below snaps `y` to surface top - SPRITE_CELL_HEIGHT
    - [ ] `test_physics.py`: Landing zeroes `velocity_y`
    - [ ] `test_physics.py`: Landing on screen_bottom works when no window surfaces exist
    - [ ] `test_physics.py`: Landing only triggers when horizontal overlap exists
    - [ ] `test_physics.py`: Cat lands on first (topmost/highest Z) surface when multiple surfaces at same Y exist
    - [ ] `test_physics.py`: No landing if no surface below (cat keeps falling)
    - [ ] `test_physics.py`: `update()` returns a landing indicator (boolean or enum)
    - [ ] `test_physics.py`: `update()` returns surface-loss indicator when Walk state has no supporting surface
    - [ ] `test_physics.py`: Fallback to screen_bottom when surfaces list is empty

- [ ] Task: Implement gravity in Physics.update()
    - [ ] `physics.py`: Add `velocity_y: float` field initialized to 0.0
    - [ ] `physics.py`: In `update()`, when state is Fall, apply gravity:
        - `velocity_y += GRAVITY * dt`
        - `velocity_y = min(velocity_y, TERMINAL_VELOCITY)`
        - `y += velocity_y * dt`
    - [ ] `physics.py`: In non-Fall states, keep `velocity_y = 0.0`

- [ ] Task: Implement landing detection in Physics.update()
    - [ ] `physics.py`: `update()` accepts `list[Surface]` parameter (already exists as `surfaces: Any = None`)
    - [ ] `physics.py`: Iterate surfaces with `surface_type in ("window_top", "screen_bottom")`
    - [ ] `physics.py`: Check `pet_bottom >= surface_top` AND horizontal overlap (`pet_center_x` within surface horizontal bounds)
    - [ ] `physics.py`: On landing: snap `y = surface_top - SPRITE_CELL_HEIGHT`, zero `velocity_y`
    - [ ] `physics.py`: Return landing indicator from `update()`

- [ ] Task: Implement surface-loss detection in Physics.update()
    - [ ] `physics.py`: When state is Walk, check if any surface supports the cat's current position
    - [ ] `physics.py`: Return surface-loss-indicator when no supporting surface found
    - [ ] `physics.py`: Surface-loss check happens BEFORE movement (if currently supported, just check after movement)

- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Canvas — Wire Fall into Animation Loop

**Goal:** Integrate Fall state, gravity physics, FALL sprite, and landing into the Canvas animation loop.

- [ ] Task: Write Canvas integration tests for Fall
    - [ ] `test_canvas.py`: `_advance_frame` transitions to Fall when surface is lost (mock surfaces)
    - [ ] `test_canvas.py`: `_advance_frame` transitions to Idle when landing detected
    - [ ] `test_canvas.py`: Fall sprite key is used when state is Fall
    - [ ] `test_canvas.py`: Animation tick interval is correct for Fall state
    - [ ] `test_canvas.py`: FALL.png sprite loaded in Canvas init
    - [ ] `test_canvas.py`: Physics receives surfaces list in update() call

- [ ] Task: Load FALL.png sprite in Canvas
    - [ ] `canvas.py`: Add `"fall": self._spritesheet.load("fall")` to `_animations` dict

- [ ] Task: Add Fall sprite key and tick interval mappings
    - [ ] `canvas.py`: Add `PetState.Fall: "fall"` to `_SPRITE_KEYS`
    - [ ] `canvas.py`: Add `PetState.Fall: 100` to `_TICK_INTERVALS` (10 FPS during fall)

- [ ] Task: Pass surfaces list to Physics.update()
    - [ ] `canvas.py`: In `_advance_frame()`, pass `self._surfaces` to `self._physics.update(..., surfaces=self._surfaces)`

- [ ] Task: Handle surface-loss signal from physics
    - [ ] `canvas.py`: After `physics.update()`, check surface-loss indicator
    - [ ] `canvas.py`: If surface lost and current state is Walk, `fsm.transition_to(PetState.Fall)`

- [ ] Task: Handle landing signal from physics
    - [ ] `canvas.py`: After `physics.update()`, check landing indicator
    - [ ] `canvas.py`: If landed and current state is Fall, `fsm.transition_to(PetState.Idle)`

- [ ] Task: Run full test suite and verify
    - [ ] Run `uv run pytest` — all tests pass
    - [ ] Run `uv run ruff check src/` — zero lint errors
    - [ ] Run `uv run ruff format --check src/` — zero formatting violations
    - [ ] Run `uv run mypy src/mochi/` — zero type errors

- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
