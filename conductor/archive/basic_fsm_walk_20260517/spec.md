# Specification: Track 1.3 — Basic FSM + Walk on Screen Bottom

## Goal
Implement a basic Finite State Machine (FSM) with **Idle**, **Walk**, and **EdgePause** states, and horizontal movement physics so the cat autonomously walks left and right along the screen bottom edge.

## Scope
This track introduces the FSM engine and physics system. The cat idles for a random duration, walks horizontally, reverses direction at screen edges (with a brief pause), and loops indefinitely. Only the screen bottom is used as a surface — window awareness is deferred to Phase 2.

## Modules Created / Modified

| Module | Action | Responsibility |
|---|---|---|
| `src/mochi/core/__init__.py` | Update | Re-export FSM and Physics classes |
| `src/mochi/core/fsm.py` | **Create** | FSM class: State enum (Idle, Walk, EdgePause), `tick(dt)` method, random timer transitions |
| `src/mochi/core/physics.py` | **Create** | `Physics` class: horizontal movement at WALK_SPEED, screen boundary clamping |
| `src/mochi/core/canvas.py` | Modify | Wire FSM + Physics into animation tick: `fsm.tick()` → `physics.update()` → swap sprite key → `update()` |
| *(no change to sprites.py)* | — | Direction flip handled entirely in canvas.py's paintEvent via QPainter.scale(-1, 1). The existing SpriteSheet.load("walk") works as-is. |
| `tests/test_fsm.py` | **Create** | Idle→Walk, Walk→Idle, timer range validation |
| `tests/test_physics.py` | **Create** | Horizontal movement, screen bounds, edge reversal |

## Design Decisions

1. **Walk Direction:** The single `WALK.png` sprite sheet is flipped horizontally via `QPainter.scale(-1, 1)` when walking left. No separate left/right assets needed.
2. **Screen Edge Behavior:** When the cat reaches a screen edge, it briefly pauses via a dedicated **EdgePause** state (fixed 0.5-1s timer) then reverses direction and transitions back to Walk. Using a separate state avoids conflicting with Idle's 2-5s timer range.
3. **Boundary Clamping:** The cat is allowed to go partially off-screen — up to half its sprite width beyond the screen edge — before reversing. This prevents abrupt stops.
4. **Module Split:** `fsm.py` handles state transitions only; `physics.py` handles movement. Separate concerns with loose coupling, aligned with future Phase 2 tracks.
5. **Sprite Key Switching:** In Idle state, render `idle` frames. In Walk/EdgePause state, render `walk` frames (flipped for left direction). EdgePause uses the walk sprite (cat pauses mid-step — no separate sprite needed).
6. **Adaptive Tick Rate (future-ready):** The TDD specifies an adaptive tick rate (Walk: 100ms, Idle: 250ms). This track starts with a fixed 200ms tick for simplicity, but the QTimer interval will be adjusted per state in a sub-task to align with the TDD spec. This avoids refactoring in a later track.
7. **FSM Location:** The FSM is placed in `src/mochi/core/` alongside Physics and Canvas (not `src/mochi/models/` as originally outlined in the TDD). This keeps all tightly-coupled tick-loop components together. The deviation is documented here for traceability.
8. **dt Calculation:** Each tick, `dt` is computed as `time.monotonic() - last_tick_time`. This provides frame-rate-independent physics regardless of timer jitter.

## Functional Requirements

### FR1: Finite State Machine
- The FSM shall have three states: `Idle`, `Walk`, and `EdgePause`.
- On entry to Idle, a random timer is set between `IDLE_TO_WALK_TIMER` (2-5s). When it fires, transition to Walk.
- On entry to Walk, a random timer is set between `WALK_TO_IDLE_TIMER` (3-8s). When it fires, transition to Idle.
- Transitioning to the same state is a no-op (guard against duplicate entry).
- **EdgePause** is a transient state: on entry, a fixed 0.5-1s timer is set. When it fires, direction is reversed and the FSM transitions to Walk.
- Timer values are pulled from `config.py` (`IDLE_TO_WALK_TIMER`, `WALK_TO_IDLE_TIMER`).
- The FSM is driven by a `tick(dt: float)` method called from the Canvas animation timer.

### FR2: Horizontal Movement
- When in Walk state, the cat moves horizontally at `WALK_SPEED` (60 px/s) in its current direction.
- `dt` (delta time in seconds) is calculated as `time.monotonic() - last_tick_time` at the start of each `_advance_frame()` call.
- The `Physics` class manages position (x, y) and direction (+1 = right, -1 = left).
- The Physics API is designed for forward-compatibility: `update(dt, state, screen_width, sprite_width, surfaces=None)` where `surfaces` will carry window/platform data in Phase 2. For this track, `surfaces` is omitted and only screen-bottom behavior applies.

### FR3: Screen Edge Reversal
- The cat reverses direction (+1 → -1 or -1 → +1) when its leading edge reaches a screen boundary.
- Partial off-screen is allowed: reversal triggers when the cat's **outer edge** plus a configurable overshoot (half sprite width) exceeds the boundary.
- On edge hit, physics signals an edge event. The canvas triggers FSM to transition to **EdgePause** state (fixed 0.5-1s timer). When EdgePause completes, direction is reversed and FSM transitions to Walk.
- Physics does NOT reverse direction itself — it only signals the edge hit. The FSM owns the direction reversal logic.

### FR4: Animation Integration
- **Idle state:** Render 8-frame idle breathing animation from `IDLE.png` (existing behavior).
- **Walk state:** Render walk frames from `WALK.png`, flipped horizontally when walking left (via `QPainter.scale(-1, 1)`).
- The Canvas animation timer uses an **adaptive tick rate**: 100ms (10 FPS) during Walk state, 250ms (4 FPS) during Idle/EdgePause. This matches the TDD spec for smooth walking animation and reduced CPU during idle.

### FR5: Canvas Wire-Up
- Canvas stores a reference to `FSM` and `Physics` instances.
- Each animation tick:
  1. Capture `dt = time.monotonic() - last_tick_time`, update `last_tick_time`.
  2. Call `fsm.tick(dt)` — may transition state and set/reset timers.
  3. Call `physics.update(dt, fsm.current_state, screen_width, sprite_width)` — updates x position if in Walk state.
  4. If FSM state changed: adjust `_animation_timer` interval (100ms Walk / 250ms Idle/EdgePause).
  5. If physics signals edge-hit: call `fsm.transition_to(EdgePause)`, queue direction reversal on timer expiry.
  6. Determine sprite key based on state + direction.
  7. Update sprite frames if animation key changed.
  8. Call `self.update()` to trigger repaint.

## Non-Functional Requirements

- Physics update should be frame-rate independent (uses `dt`).
- CPU impact during Walk state should be minimal (100ms tick rate, just more logic per tick). During Idle/EdgePause the 250ms tick rate reduces CPU.
- No new dependencies beyond existing tech stack (PySide6-Essentials, Python stdlib).

## Acceptance Criteria

- [ ] Cat starts in Idle state, displaying the idle breathing animation.
- [ ] Within 2-5 seconds, cat transitions to Walk state and moves horizontally.
- [ ] While walking, the walk animation plays (flipped for left direction).
- [ ] After 3-8 seconds of walking, cat transitions back to Idle.
- [ ] At screen edges, cat pauses briefly then reverses direction.
- [ ] Cat's position is bounded by screen width (allowing half-sprite overshoot).
- [ ] All FSM state transitions are logged at DEBUG level.

## Acceptance Criteria (Tests)

- [ ] `test_fsm.py`: Idle→Walk transition fires within timer range.
- [ ] `test_fsm.py`: Walk→Idle transition fires within timer range.
- [ ] `test_fsm.py`: Same-state transition is a no-op (guard test).
- [ ] `test_physics.py`: Horizontal movement at WALK_SPEED matches expected displacement.
- [ ] `test_physics.py`: Screen bounds clamp position correctly.
- [ ] `uv run ruff check src/` — zero lint errors on new code.
- [ ] `uv run mypy src/mochi/` — zero type errors.

## Out of Scope

- No window/platform awareness (deferred to Phase 2).
- No climb, fall, wall slide, or sleep states (deferred to subsequent tracks).
- No Tamagotchi metrics or item interactions (deferred to Phase 4).
- No drag interaction or click-through toggling (deferred to Phase 3).
- No animation blending or easing between states (instant sprite swaps only).
