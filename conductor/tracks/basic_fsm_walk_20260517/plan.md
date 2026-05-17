# Implementation Plan: Track 1.3 — Basic FSM + Walk on Screen Bottom

## Phase 1: Core FSM Engine

> **Goal:** Create the `FSM` class with Idle/Walk/EdgePause states and timer-based transitions, fully tested.

- [x] Task 1.1: Write FSM tests (test_fsm.py) `869a42b`
    - [x] Write test: FSM initializes in Idle state
    - [x] Write test: Idle→Walk transition fires within IDLE_TO_WALK_TIMER range
    - [x] Write test: Walk→Idle transition fires within WALK_TO_IDLE_TIMER range
    - [x] Write test: EdgePause→Walk transition fires within 0.5-1s range
    - [x] Write test: Same-state transition is a no-op (guard test)
    - [x] Write test: FSM logs transitions at DEBUG level
    - [x] Run tests: confirm they fail as expected (Red phase)
- [x] Task 1.2: Implement FSM class (src/mochi/core/fsm.py) `869a42b`
    - [x] Create `PetState` enum (Idle, Walk, EdgePause)
    - [x] Create `FSM` class with `tick(dt: float) -> None` method
    - [x] Implement timer logic using `IDLE_TO_WALK_TIMER` and `WALK_TO_IDLE_TIMER` from config
    - [x] Implement EdgePause with fixed 0.5-1s timer
    - [x] Add same-state transition guard (no-op on duplicate)
    - [x] Add DEBUG-level logging for state transitions
    - [x] Run tests: confirm all pass (Green phase)
- [~] Task: Conductor - User Manual Verification 'Phase 1: Core FSM Engine' (Protocol in workflow.md)

## Phase 2: Core Physics Engine

> **Goal:** Create the `Physics` class with horizontal movement and screen boundary clamping, fully tested.

- [ ] Task 2.1: Write Physics tests (test_physics.py)
    - [ ] Write test: Walk state applies horizontal displacement at WALK_SPEED * dt
    - [ ] Write test: Idle state results in zero movement
    - [ ] Write test: Screen left edge signals edge-hit (does NOT reverse direction itself)
    - [ ] Write test: Screen right edge signals edge-hit (does NOT reverse direction itself)
    - [ ] Write test: Half-sprite overshoot allowed before edge-hit signal
    - [ ] Write test: Cat position never exceeds bounds + overshoot
    - [ ] Write test: No edge-hit signal when cat is in valid bounds
    - [ ] Run tests: confirm they fail as expected (Red phase)
- [ ] Task 2.2: Implement Physics class (src/mochi/core/physics.py)
    - [ ] Create `Physics` class with `x`, `y`, `direction` (+1/-1) attributes
    - [ ] Implement `update(dt: float, state: PetState, screen_width: int, sprite_width: int, surfaces: Any = None) -> bool`
    - [ ] Apply `WALK_SPEED * dt * direction` to `x` when in Walk state
    - [ ] Implement screen boundary detection with configurable overshoot (half sprite width)
    - [ ] **Return bool**: `True` if edge was hit (canvas handles pause/direction reversal), `False` otherwise. Physics does NOT reverse direction — that's the FSM's job.
    - [ ] API includes `surfaces=None` parameter for forward-compatibility with Phase 2 window awareness
    - [ ] Run tests: confirm all pass (Green phase)
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Core Physics Engine' (Protocol in workflow.md)

## Phase 3: Canvas Integration & Walk Animation

> **Goal:** Wire FSM + Physics into the Canvas animation loop, implement direction-aware sprite rendering with edge pause behavior.

- [ ] Task 3.1: Update Canvas to load walk sprites
    - [ ] Load `walk` animation key from SpriteSheet in Canvas.__init__
    - [ ] Store `_walk_frames: list[QPixmap]` alongside existing `_idle_frames`
- [ ] Task 3.2: Wire FSM + Physics into animation tick
    - [ ] Create FSM and Physics instances in Canvas.__init__
    - [ ] Store `_last_tick: float = time.monotonic()` for dt calculation
    - [ ] In `_advance_frame()`: `now = time.monotonic(); dt = now - self._last_tick; self._last_tick = now`
    - [ ] Call `fsm.tick(dt)` then `edge_hit = physics.update(dt, fsm.current_state, screen_width, sprite_width)`
    - [ ] If edge_hit: call `fsm.transition_to(EdgePause)`, queue direction reversal on EdgePause expiry
    - [ ] Store `_current_sprite_key: str` to track active animation
    - [ ] On state change, reload frames from cache if animation key changed
    - [ ] Call `self.update()` for repaint
- [ ] Task 3.3: Implement direction-aware sprite rendering
    - [ ] In `paintEvent`, check physics.direction
    - [ ] When direction == -1 (left): use `QPainter.scale(-1, 1)` before drawPixmap
    - [ ] When direction == +1 (right): draw normally
- [ ] Task 3.4: Implement screen edge pause behavior via EdgePause state
    - [ ] When physics signals edge-hit, call `fsm.transition_to(EdgePause)` (0.5-1s timer)
    - [ ] When EdgePause timer fires: reverse direction, transition to Walk
    - [ ] EdgePause uses walk sprite frames (cat pauses mid-step — visually seamless)
- [ ] Task 3.5: Implement adaptive tick rate per FSM state
    - [ ] On FSM state transition, update `_animation_timer.setInterval()`:
        - Walk state → 100ms (10 FPS, smooth movement)
        - Idle state → 250ms (4 FPS, lower CPU)
        - EdgePause state → 250ms (same as idle, minimal CPU)
    - [ ] Write test: Canvas timer interval changes on FSM state transition
- [ ] Task 3.6: Update `src/mochi/core/__init__.py`
    - [ ] Re-export FSM and Physics for clean imports
- [ ] Task 3.7: Run full test suite and quality gates
    - [ ] Run `uv run pytest` — all 79 existing tests + new tests pass
    - [ ] Run `uv run ruff check src/` — zero lint errors
    - [ ] Run `uv run mypy src/mochi/` — zero type errors
    - [ ] Run `uv run ruff format --check src/` — zero formatting violations
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Canvas Integration & Walk Animation' (Protocol in workflow.md)
