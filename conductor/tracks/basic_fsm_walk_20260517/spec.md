# Specification: Track 1.3 — Basic FSM + Walk on Screen Bottom

## Goal
Implement a basic Finite State Machine (FSM) with **Idle** and **Walk** states, and horizontal movement physics so the cat autonomously walks left and right along the screen bottom edge.

## Scope
This track introduces the FSM engine and physics system. The cat idles for a random duration, walks horizontally, reverses direction at screen edges (with a brief pause), and loops indefinitely. Only the screen bottom is used as a surface — window awareness is deferred to Phase 2.

## Modules Created / Modified

| Module | Action | Responsibility |
|---|---|---|
| `src/mochi/core/__init__.py` | Update | Re-export FSM and Physics classes |
| `src/mochi/core/fsm.py` | **Create** | FSM class: State enum (Idle, Walk), `tick(dt)` method, random timer transitions |
| `src/mochi/core/physics.py` | **Create** | `Physics` class: horizontal movement at WALK_SPEED, screen boundary clamping |
| `src/mochi/core/canvas.py` | Modify | Wire FSM + Physics into animation tick: `fsm.tick()` → `physics.update()` → swap sprite key → `update()` |
| `src/mochi/ui/sprites.py` | Modify (minor) | Add `walk_left`/`walk_right` getter (or use direction flip via QPainter in canvas) |
| `tests/test_fsm.py` | **Create** | Idle→Walk, Walk→Idle, timer range validation |
| `tests/test_physics.py` | **Create** | Horizontal movement, screen bounds, edge reversal |

## Design Decisions

1. **Walk Direction:** The single `WALK.png` sprite sheet is flipped horizontally via `QPainter.scale(-1, 1)` when walking left. No separate left/right assets needed.
2. **Screen Edge Behavior:** When the cat reaches a screen edge, it briefly pauses (enters Idle for ~0.5-1s) then reverses direction. This feels more organic than an instant snap.
3. **Boundary Clamping:** The cat is allowed to go partially off-screen — up to half its sprite width beyond the screen edge — before reversing. This prevents abrupt stops.
4. **Module Split:** `fsm.py` handles state transitions only; `physics.py` handles movement. Separate concerns with loose coupling, aligned with future Phase 2 tracks.
5. **Sprite Key Switching:** In Idle state, render `idle` frames. In Walk state, render `walk` frames (flipped for left direction).

## Functional Requirements

### FR1: Finite State Machine
- The FSM shall have two states: `Idle` and `Walk`.
- On entry to Idle, a random timer is set between `IDLE_TO_WALK_TIMER` (2-5s). When it fires, transition to Walk.
- On entry to Walk, a random timer is set between `WALK_TO_IDLE_TIMER` (3-8s). When it fires, transition to Idle.
- Timer values are pulled from `config.py` (`IDLE_TO_WALK_TIMER`, `WALK_TO_IDLE_TIMER`).
- The FSM is driven by a `tick(dt: float)` method called from the Canvas animation timer.

### FR2: Horizontal Movement
- When in Walk state, the cat moves horizontally at `WALK_SPEED` (60 px/s) in its current direction.
- `dt` (delta time in seconds) is calculated from the actual elapsed time since the last tick.
- The `Physics` class manages position (x, y) and direction (+1 = right, -1 = left).

### FR3: Screen Edge Reversal
- The cat reverses direction (+1 → -1 or -1 → +1) when its leading edge reaches a screen boundary.
- Partial off-screen is allowed: reversal triggers when the cat's **outer edge** plus a configurable overshoot (half sprite width) exceeds the boundary.
- On edge hit, the cat briefly transitions to Idle (0.5-1s pause) before moving in the opposite direction.

### FR4: Animation Integration
- **Idle state:** Render 8-frame idle breathing animation from `IDLE.png` (existing behavior).
- **Walk state:** Render walk frames from `WALK.png`, flipped horizontally when walking left (via `QPainter.scale(-1, 1)`).
- The Canvas animation timer (200ms) drives both frame advancement and FSM/physics ticks.

### FR5: Canvas Wire-Up
- Canvas stores a reference to `FSM` and `Physics` instances.
- Each animation tick:
  1. Calculate `dt` from actual elapsed time.
  2. Call `fsm.tick(dt)` — may transition state and set/reset timers.
  3. Call `physics.update(dt, fsm.current_state)` — updates x position if in Walk state.
  4. Determine sprite key based on state + direction.
  5. Update sprite frames if animation key changed.
  6. Call `self.update()` to trigger repaint.

## Non-Functional Requirements

- Physics update should be frame-rate independent (uses `dt`).
- CPU impact during Walk state should be minimal (same 200ms tick rate, just more logic per tick).
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
- [ ] `test_fsm.py`: No invalid state transitions occur.
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
