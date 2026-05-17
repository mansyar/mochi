# Implementation Plan: Track 1.3 — Basic FSM + Walk on Screen Bottom

## Phase 1: Core FSM Engine

> **Goal:** Create the `FSM` class with Idle/Walk states and timer-based transitions, fully tested.

- [ ] Task 1.1: Write FSM tests (test_fsm.py)
    - [ ] Write test: FSM initializes in Idle state
    - [ ] Write test: Idle→Walk transition fires within IDLE_TO_WALK_TIMER range
    - [ ] Write test: Walk→Idle transition fires within WALK_TO_IDLE_TIMER range
    - [ ] Write test: No invalid state transitions (e.g., double-transition guard)
    - [ ] Write test: FSM logs transitions at DEBUG level
    - [ ] Run tests: confirm they fail as expected (Red phase)
- [ ] Task 1.2: Implement FSM class (src/mochi/core/fsm.py)
    - [ ] Create `PetState` enum (Idle, Walk)
    - [ ] Create `FSM` class with `tick(dt: float) -> None` method
    - [ ] Implement timer logic using `IDLE_TO_WALK_TIMER` and `WALK_TO_IDLE_TIMER` from config
    - [ ] Add DEBUG-level logging for state transitions
    - [ ] Run tests: confirm all pass (Green phase)
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Core FSM Engine' (Protocol in workflow.md)

## Phase 2: Core Physics Engine

> **Goal:** Create the `Physics` class with horizontal movement and screen boundary clamping, fully tested.

- [ ] Task 2.1: Write Physics tests (test_physics.py)
    - [ ] Write test: Walk state applies horizontal displacement at WALK_SPEED * dt
    - [ ] Write test: Idle state results in zero movement
    - [ ] Write test: Screen left edge reverses direction (+1 → -1)
    - [ ] Write test: Screen right edge reverses direction (-1 → +1)
    - [ ] Write test: Half-sprite overshoot allowed before reversal
    - [ ] Write test: Cat position never exceeds bounds + overshoot
    - [ ] Run tests: confirm they fail as expected (Red phase)
- [ ] Task 2.2: Implement Physics class (src/mochi/core/physics.py)
    - [ ] Create `Physics` class with `x`, `y`, `direction` (+1/-1) attributes
    - [ ] Implement `update(dt: float, state: PetState, screen_width: int, sprite_width: int) -> None`
    - [ ] Apply `WALK_SPEED * dt * direction` to `x` when in Walk state
    - [ ] Implement screen boundary detection with configurable overshoot
    - [ ] Return edge-hit signal for canvas to handle pause behavior
    - [ ] Run tests: confirm all pass (Green phase)
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Core Physics Engine' (Protocol in workflow.md)

## Phase 3: Canvas Integration & Walk Animation

> **Goal:** Wire FSM + Physics into the Canvas animation loop, implement direction-aware sprite rendering with edge pause behavior.

- [ ] Task 3.1: Update Canvas to load walk sprites
    - [ ] Load `walk` animation key from SpriteSheet in Canvas.__init__
    - [ ] Store `_walk_frames: list[QPixmap]` alongside existing `_idle_frames`
- [ ] Task 3.2: Wire FSM + Physics into animation tick
    - [ ] Create FSM and Physics instances in Canvas.__init__
    - [ ] In `_advance_frame()`: calculate dt, call `fsm.tick(dt)` then `physics.update(...)`
    - [ ] Store `_current_sprite_key: str` to track active animation
    - [ ] On state change, reload frames from cache if animation key changed
    - [ ] Call `self.update()` for repaint
- [ ] Task 3.3: Implement direction-aware sprite rendering
    - [ ] In `paintEvent`, check physics.direction
    - [ ] When direction == -1 (left): use `QPainter.scale(-1, 1)` before drawPixmap
    - [ ] When direction == +1 (right): draw normally
- [ ] Task 3.4: Implement screen edge pause behavior
    - [ ] When physics signals edge-hit, trigger a brief forced-Idle timer (0.5-1s)
    - [ ] After pause completes, reverse direction and resume Walk state
- [ ] Task 3.5: Update `src/mochi/core/__init__.py`
    - [ ] Re-export FSM and Physics for clean imports
- [ ] Task 3.6: Run full test suite and quality gates
    - [ ] Run `uv run pytest` — all 79 existing tests + new tests pass
    - [ ] Run `uv run ruff check src/` — zero lint errors
    - [ ] Run `uv run mypy src/mochi/` — zero type errors
    - [ ] Run `uv run ruff format --check src/` — zero formatting violations
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Canvas Integration & Walk Animation' (Protocol in workflow.md)
