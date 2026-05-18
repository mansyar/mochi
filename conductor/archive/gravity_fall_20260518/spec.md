# Track 2.2 — Gravity, Falling & Ground Snapping

## Overview

Add vertical physics (gravity) to Mochi's movement system so the cat falls with acceleration when its supporting surface is lost (window moved, closed, or minimized). The cat lands on the nearest window top edge below it, or on the screen bottom as a last resort. A new `Fall` FSM state drives the behavior with a static falling sprite during descent.

## Dependencies

This track builds on:
- **Track 2.1 (Window Polling & Surface Detection):** `EnvironmentPoller` provides the `list[Surface]` of window tops, window sides, and screen edges.
- **Track 1.3 (FSM + Walk on Screen Bottom):** `FSM` and `Physics` classes exist with Idle, Walk, and EdgePause states.

## Modules Affected

- **`core/physics.py`** — Add `velocity_y`, gravity acceleration, terminal velocity capping, landing detection, surface-loss detection. **Return type changes** from `bool` to a richer result type (`PhysicsResult` dataclass with `edge_hit`, `surface_lost`, `landed` booleans).
- **`core/fsm.py`** — Add `Fall` state and its transitions (Walk→Fall, Fall→Idle). Set Fall timer to `inf` since transitions are physics-driven. Add defensive Fall case to `_on_timer_expired`.
- **`core/canvas.py`** — Wire Fall state into the animation tick: pass surfaces to physics, reorder the tick loop so physics runs before FSM tick, handle surface-loss and landing signals, load fall sprite, update `_TICK_INTERVALS` and `_SPRITE_KEYS`.
- **`core/environment.py`** — Fix screen_bottom surface Y-coordinate to represent the actual ground line (not the cat-walking line), for consistency with window_top surfaces.
- **`config.py`** — Constants already exist: `GRAVITY` (980.0), `TERMINAL_VELOCITY` (600.0). No new config needed.

## Functional Requirements

### 1. Fall State (FSM)
- Add a new `PetState.Fall` singleton.
- **Walk→Fall transition:** When physics detects that no supporting surface exists below the cat after movement (i.e., the window/edge the cat was on has moved, closed, or been minimized), the FSM transitions to Fall.
- **Fall→Idle transition:** When the cat's bottom edge reaches or passes a surface top edge, snap position, zero velocity, transition to Idle.
- Surface ordering for landing: cat lands on the **topmost Z-order** surface below it. (Z-order is approximated by surface list ordering — windows reported first by the OS are assumed topmost.)
- If no window surface exists below, the cat lands on `screen_bottom` as the last-resort ground.
- Random timers are NOT used for Fall transitions — they're purely physics-driven. The Fall timer is set to `float('inf')` so `tick()` never auto-transitions out of Fall.
- A defensive Fall case is added to `_on_timer_expired()` (logs a warning and is a no-op) to prevent future bugs if the timer logic changes.

### 2. Gravity Physics
- Add `velocity_y: float` to the `Physics` class (initialized to 0.0).
- In `Physics.update()`, when the current state is `Fall`:
  - `velocity_y += GRAVITY * dt` (acceleration: 980 px/s²)
  - Cap: `velocity_y = min(velocity_y, TERMINAL_VELOCITY)` (max: 600 px/s)
  - `self.y += velocity_y * dt`
- In all non-Fall states, `velocity_y` is held at 0.0 (no drift).

### 3. Physics Return Type: `PhysicsResult`
The `Physics.update()` return type changes from `bool` to a `PhysicsResult` dataclass:

```python
@dataclass
class PhysicsResult:
    edge_hit: bool = False       # Walk: reached screen edge
    surface_lost: bool = False   # Walk: no supporting surface below
    landed: bool = False         # Fall: landed on a surface
```

- **Walk state:** Returns `(edge_hit, surface_lost, landed=False)`. Only one of `edge_hit` or `surface_lost` can be `True` per tick.
- **Fall state:** Returns `(edge_hit=False, surface_lost=False, landed)` where `landed=True` when a surface is intersected.
- **Idle/EdgePause:** Returns all `False`.

### 4. Surface-Loss Detection (Walk State)
- Runs **AFTER** horizontal movement in `Physics.update()`.
- After applying `x += WALK_SPEED * dt * direction`, check if the cat's bottom edge (`y + SPRITE_CELL_HEIGHT`) is within the Y range of any surface in the list with `surface_type in ("window_top", "screen_bottom")`.
- Check both vertical alignment (`pet_bottom >= surface_top - tolerance`) AND horizontal overlap (`pet_center_x` within surface horizontal bounds).
- If NO surface supports the cat → `surface_lost = True`.

### 5. Ground / Landing Detection (Fall State)
- For each `Surface` with `surface_type in ("window_top", "screen_bottom")`:
  - Calculate `pet_bottom = physics.y + SPRITE_CELL_HEIGHT`.
  - Calculate `surface_top = surface.rect.top()`.
  - Check horizontal overlap: `pet_center_x` falls within `surface.rect.left()` to `surface.rect.right()`.
  - If `pet_bottom >= surface_top` and horizontal overlap exists:
    - Snap `physics.y = surface_top - SPRITE_CELL_HEIGHT`.
    - Zero `velocity_y`.
    - Set `landed = True`.
- Landing priority: iterate surfaces in order (highest Z-order first). Last surface checked is `screen_bottom`.
- If surface list is empty (poller failure), the cat falls through to screen_bottom Y and lands via hard clamp.

### 6. Screen Bottom Surface Fix
The `EnvironmentPoller._build_surfaces()` currently defines the screen_bottom surface rect at `y = screen.bottom() - SCREEN_BOTTOM_MARGIN_PX - SPRITE_CELL_HEIGHT`. This is inconsistent with window_top surfaces (which use the actual edge Y). The fix:
- `_build_surfaces()`: screen_bottom rect changes to `y = screen.bottom() - SCREEN_BOTTOM_MARGIN_PX` (the actual ground line).
- `Canvas._screen_bottom_y()` remains `screen.bottom() - SCREEN_BOTTOM_MARGIN_PX - SPRITE_CELL_HEIGHT` (where the cat's top sits when standing on the ground).
- `test_environment.py::test_screen_bottom_surface` updated to match the new expected Y.

### 7. Animation Tick Loop Reordering
The `Canvas._advance_frame()` must reorder operations to prevent the FSM timer from firing Walk→Idle before surface-loss is detected:

```
1. Compute dt
2. Sync physics direction from FSM
3. physics.update(dt, current_state, screen_width, sprite_width, surfaces)
4. If Walk and surface_lost → fsm.transition_to(Fall)
5. If Fall and landed → fsm.transition_to(Idle)
6. fsm.tick(dt)  ← safe: Fall has inf timer, won't auto-transition
7. Handle edge_hit → fsm.transition_to(EdgePause)
8. Determine sprite key, advance frame, update timer interval
9. Repaint
```

### 8. Fall Animation
- No `FALL.png` exists in the sprite assets. The **middle frame** (index 1, 0-indexed) of `JUMP.png` (240×64 px, 3 frames at 80×64 each) serves as the falling sprite.
- In `Canvas.__init__`, load `"jump"` animation and extract `frames[1]` as a single-frame list for the `"fall"` key.
- Add `PetState.Fall` → `"fall"` to `_SPRITE_KEYS`.
- Add `PetState.Fall` → `100` ms tick interval to `_TICK_INTERVALS` (10 FPS — single static frame, but keeps consistent update rate for landing detection).

## Acceptance Criteria

- [ ] `PetState.Fall` exists as a valid FSM state with `float('inf')` timer.
- [ ] `Physics` class tracks `velocity_y` and applies gravity acceleration when state is Fall.
- [ ] `velocity_y` is capped at `TERMINAL_VELOCITY` (600 px/s).
- [ ] When the cat walks off a surface (no surface below), it transitions from Walk→Fall.
- [ ] When falling, the cat lands on the topmost window surface below it that has horizontal overlap.
- [ ] If no window surface exists below, the cat lands on screen_bottom.
- [ ] On landing, position snaps to the surface top, velocity_y zeroes, and state transitions to Idle.
- [ ] The middle frame of JUMP.png is displayed as the fall sprite during descent.
- [ ] Cat does not take fall damage — it always lands safely.
- [ ] No random timer governs Fall — transitions are purely physics-driven.
- [ ] `Physics.update()` returns `PhysicsResult` (not bare `bool`). Existing `test_update_returns_bool` updated to check `isinstance(result, PhysicsResult)`.
- [ ] `Physics.update()` does NOT early-return-forbidden for Fall state — gravity is applied.
- [ ] `_advance_frame()` runs physics before FSM tick to prevent Walk→Idle masking surface-loss.
- [ ] `_on_timer_expired()` has a defensive Fall case (warning log, no-op).
- [ ] screen_bottom surface uses correct Y coordinate consistent with window_top surfaces.
- [ ] `EnvironmentPoller._build_surfaces()` and `Canvas._screen_bottom_y()` are consistent after the screen bottom Y fix.

## Non-Functional Requirements

- **Performance:** Gravity calculations add < 0.1% CPU overhead. No measurable impact on existing budget.
- **Frame-rate independence:** All movement and acceleration are scaled by `dt` to behave identically at any frame rate.
- **Error handling:** If the surface list is empty (poller failure), the cat falls through to screen_bottom and lands. No crash, no stuck state.

## Out of Scope

- Climbing / Wall Slide states (Track 2.3). Note: PRD lists Fall→Climb ("lateral edge contact during descent") — this is deferred to Track 2.3's climbing implementation.
- Sleep state (Track 2.4).
- Window side climbing during fall (post-MVP).
- Multi-monitor support (post-MVP).
- macOS/Linux platform-specific click-through (deferred).
