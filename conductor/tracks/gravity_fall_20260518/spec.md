# Track 2.2 — Gravity, Falling & Ground Snapping

## Overview

Add vertical physics (gravity) to Mochi's movement system so the cat falls with acceleration when its supporting surface is lost (window moved, closed, or minimized). The cat lands on the nearest window top edge below it, or on the screen bottom as a last resort. A new `Fall` FSM state drives the behavior with an appropriate sprite animation during descent.

## Dependencies

This track builds on:
- **Track 2.1 (Window Polling & Surface Detection):** `EnvironmentPoller` provides the `list[Surface]` of window tops, window sides, and screen edges.
- **Track 1.3 (FSM + Walk on Screen Bottom):** `FSM` and `Physics` classes exist with Idle, Walk, and EdgePause states.

## Modules Affected

- **`core/physics.py`** — Add vertical velocity (`velocity_y`), gravity acceleration, terminal velocity capping, and ground/landing detection.
- **`core/fsm.py`** — Add `Fall` state and its transitions (Walk→Fall, Fall→Idle).
- **`core/canvas.py`** — Wire Fall state into the animation tick: sync Fall sprite key, pass surfaces to physics, handle landing events.
- **`ui/sprites.py`** — Load the `FALL.png` sprite sheet as a cached animation.
- **`config.py`** — Constants already exist: `GRAVITY` (980.0), `TERMINAL_VELOCITY` (600.0). No new config needed.

## Functional Requirements

### 1. Fall State (FSM)
- Add a new `PetState.Fall` singleton.
- **Walk→Fall transition:** When physics detects that no supporting surface exists below the cat (i.e., the window/edge the cat was on has moved, closed, or been minimized), the FSM transitions to Fall.
- **Fall→Idle transition:** When the cat's bottom edge reaches or passes a surface top edge, snap position, zero velocity, transition to Idle.
- Surface ordering for landing: cat lands on the **topmost Z-order** surface below it. (Z-order is approximated by surface list ordering — windows reported first by the OS are assumed topmost.)
- If no window surface exists below, the cat lands on `screen_bottom` as the last-resort ground.
- Random timers are NOT used for Fall transitions — they're purely driven by physics conditions.

### 2. Gravity Physics
- Add `velocity_y: float` to the `Physics` class (initialized to 0.0).
- In `Physics.update()`, when the current state is `Fall`:
  - `velocity_y += GRAVITY * dt` (acceleration: 980 px/s²)
  - Cap: `velocity_y = min(velocity_y, TERMINAL_VELOCITY)` (max: 600 px/s)
  - `self.y += velocity_y * dt`
- In all non-Fall states, `velocity_y` is held at 0.0 (no drift).

### 3. Ground / Landing Detection
- `Physics.update()` receives the `list[Surface]` from the `EnvironmentPoller`.
- For each `Surface` with `surface_type in ("window_top", "screen_bottom")`:
  - Calculate `pet_bottom = physics.y + SPRITE_CELL_HEIGHT`.
  - Calculate `surface_top = surface.rect.top()`.
  - Check horizontal overlap: `pet_center_x` falls within `surface.rect.left()` to `surface.rect.right()`.
  - If `pet_bottom >= surface_top` and horizontal overlap exists:
    - Snap `physics.y = surface_top - SPRITE_CELL_HEIGHT`.
    - Zero `velocity_y`.
    - Return a landing signal to the caller (Canvas).
- **Screen bottom** is always the last surface checked / final fallback.
- Landing priority: from highest Z-order (first in list) to lowest. If multiple surfaces are at the same Y level, the first match (highest Z) wins.

### 4. Fall Animation
- Load `FALL.png` sprite frames in Canvas (expected to exist at `assets/sprites/FALL.png`).
- Add `PetState.Fall` → `"fall"` to `_SPRITE_KEYS` dict.
- Add `PetState.Fall` → appropriate tick interval (e.g., 100ms for 10 FPS during fall).

## Acceptance Criteria

- [ ] `PetState.Fall` exists as a valid FSM state.
- [ ] `Physics` class tracks `velocity_y` and applies gravity acceleration when state is Fall.
- [ ] `velocity_y` is capped at `TERMINAL_VELOCITY` (600 px/s).
- [ ] When the cat walks off a surface (no surface below), it transitions from Walk→Fall.
- [ ] When falling, the cat lands on the topmost window surface below it that has horizontal overlap.
- [ ] If no window surface exists below, the cat lands on screen_bottom.
- [ ] On landing, position snaps to the surface top, velocity_y zeroes, and state transitions to Idle.
- [ ] The Fall sprite animation plays during descent.
- [ ] Cat does not take fall damage — it always lands safely.
- [ ] No random timer governs Fall — transitions are purely physics-driven.

## Non-Functional Requirements

- **Performance:** Gravity calculations add < 0.1% CPU overhead. No measurable impact on existing budget.
- **Frame-rate independence:** All movement and acceleration are scaled by `dt` to behave identically at any frame rate.
- **Error handling:** If the surface list is empty (poller failure), the cat falls through to screen_bottom and lands. No crash, no stuck state.

## Out of Scope

- Climbing / Wall Slide states (Track 2.3).
- Sleep state (Track 2.4).
- Window side climbing during fall (post-MVP).
- Multi-monitor support (post-MVP).
- macOS/Linux platform-specific click-through (deferred).
