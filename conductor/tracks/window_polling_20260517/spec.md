# Specification: Track 2.1 — Window Polling & Surface Detection

## Goal
Implement a background poller that queries active application windows via PyWinCtl, filters and normalizes them into a list of `Surface` objects (window tops, window sides, screen edges), and emits them to the main thread via a Qt signal. No physics integration yet — that comes in Track 2.2.

## References
- **ROADMAP.md** — Phase 2, Track 2.1
- **PRD.md** — Section 4.1.2 (Window & Screen Edge Interaction)
- **TDD.md** — Section 5.4 (Collision Detection), Section 5.5 (Environment Poller)

## Modules Affected

| Module | Change |
|---|---|
| `src/mochi/core/environment.py` | **NEW** — `Surface` dataclass + `EnvironmentPoller(QThread)` class |
| `src/mochi/config.py` | **MODIFY** — Change `WINDOW_POLL_INTERVAL_MS` from 200 to 300 |
| `src/mochi/core/canvas.py` | **MODIFY** — Connect `platforms_updated` signal to store surface list |
| `src/mochi/core/__init__.py` | **MODIFY** — Export `Surface` |
| `src/mochi/core/physics.py` | **NO CHANGE** — `surfaces` param already reserved, integration deferred |
| `tests/test_environment.py` | **NEW** — Unit tests for poller filtering, Surface construction, signals |
| `tests/test_config.py` | **MODIFY** — Update existing config constant test (value changed 200→300) |
| `tests/test_physics.py` | **NO CHANGE** — Ground detection deferred to Track 2.2 |

## Design Notes / Deviations from Design Docs

1. **TDD §5.5 vs §6 value mismatch:** TDD §5.5 says 300ms for poll interval, §6 says 200ms. This spec follows §5.5 (300ms) as the more appropriate value — sufficient for surface detection while keeping CPU under 0.5%. The config will be updated from the current 200ms to 300ms.
2. **ROADMAP scope deviation:** The ROADMAP lists "Ground detection in physics" as part of Track 2.1. This track deliberately defers ground snapping → Track 2.2. After Track 2.1 completes, the cat will still walk only on screen bottom — it won't yet react to window surfaces.
3. **Window stacking:** `window_top` surfaces are generated from raw window rectangles without Z-order clipping. If Window A is behind Window B, surfaces for both are emitted. The cat may appear to "walk on air" above a hidden window. Future tracks can improve this with visibility clipping.

## Functional Requirements

### FR1: Surface Dataclass (`environment.py`)
- A `@dataclass` named `Surface` with fields:
  - `rect: QRect` — The bounding rectangle in screen coordinates
  - `surface_type: str` — One of: `"window_top"`, `"screen_bottom"`, `"screen_left"`, `"screen_right"`, `"window_left"`, `"window_right"`
  - `window_id: int | None` — OS window handle (for tracking moves/closes); `None` for screen edges

### FR2: EnvironmentPoller (`environment.py`)
- A class `EnvironmentPoller(QThread)` that:
  - Receives `screen_geo: QRect` at construction time — captured once on the main thread from `QApplication.primaryScreen().availableGeometry()`. **No QScreen/QApplication APIs are called from the worker thread** (Qt GUI objects are not thread-safe).
  - Creates a `QTimer` at `WINDOW_POLL_INTERVAL_MS` (300ms) on the thread's event loop. The thread's `run()` method must call `self.exec()` to drive the event loop — without it the timer will never fire.
  - Each tick:
    1. Calls `pywinctl.getAllWindows()` to enumerate all visible OS windows
    2. **Filters** the list: excludes minimized windows, excludes windows with empty titles, excludes the Mochi overlay itself (by window title "Mochi")
    3. **Builds surfaces:** For each window, computes:
       - `window_top` — a horizontal surface at the window's `y()` spanning `x()` to `x() + width()`
       - `window_left` — a vertical surface at the window's `x()` spanning `y()` to `y() + height()`
       - `window_right` — a vertical surface at `x() + width()`
    4. Adds **screen edges** (from `screen_geo` passed at construction):
       - `screen_bottom` — horizontal surface at Y = `screen_geo.bottom() - SCREEN_BOTTOM_MARGIN_PX - SPRITE_CELL_HEIGHT` (same formula as `Canvas._screen_bottom_y()`)
       - `screen_left` / `screen_right` — vertical bezels at X = 0 and X = `screen_geo.width()`
    5. Emits `platforms_updated(list[Surface])` signal

### FR3: Signal & Slot Wiring
- `EnvironmentPoller` declares a Qt signal: `platforms_updated = Signal(list)` (using `list[Surface]` at runtime)
- Canvas stores the most recent surface list: `self._surfaces: list[Surface] = []`
- On receiving the signal, Canvas updates its cached surface list and logs a summary line
- No physics behavior change yet — the cat continues walking on screen bottom only
- **Important:** The signal crosses thread boundaries — it is emitted from the worker thread and received on the main (GUI) thread. Qt's signal-slot mechanism handles queuing automatically when sender and receiver are in different threads. No mutex or explicit locking is needed.

### FR4: Error Handling
- If `pywinctl.getAllWindows()` raises an exception (permission denied, OS error), log a warning with the exception details and emit the previously cached surface list instead
- If no windows are visible, emit a surface list containing only screen edges
- The poller must not crash under any error condition
- On macOS, `pywinctl` may raise `PermissionError` if Accessibility permission is denied. Log the warning, emit cached list. The app continues with reduced functionality.

### FR5: Performance
- Window enumeration occurs at most every 300ms
- Surface list is rebuilt from scratch each tick (no incremental diff) — simple and correct
- The poller runs on a background `QThread` so it never blocks the main thread's animation loop

## Non-Functional Requirements

| Metric | Target |
|---|---|
| Poller CPU | < 0.5% single core |
| Poll interval | 300ms (±10ms tolerance) |
| Max surface list size | ~150 surfaces (50 windows × 3 surfaces + 3 screen edges) |
| Error resilience | Never crash on bad window data |

## Acceptance Criteria

1. `EnvironmentPoller` enumerates all visible windows and produces a correct `list[Surface]`
2. The Mochi overlay window is excluded from the surface list
3. Minimized and empty-title windows are excluded
4. Screen edge surfaces are always included (even with zero visible windows)
5. `screen_bottom` Y coordinate matches `Canvas._screen_bottom_y()` formula
6. `platforms_updated` signal is emitted every 300ms
7. Canvas receives the signal (cross-thread) and caches the surface list
8. If `pywinctl.getAllWindows()` raises, the previous surface list is re-emitted and a warning is logged
9. Poller thread cleans up properly on Canvas destruction: `quit()` → `wait()` → `deleteLater()`
10. All unit tests pass with >80% coverage for new code
11. Zero lint errors (`ruff check`), zero type errors (`mypy strict`)

## Out of Scope
- Ground snapping / surface landing (→ Track 2.2)
- Gravity and falling physics (→ Track 2.2)
- Window move/close tracking via `window_id` (→ Track 2.2)
- Fullscreen detection (→ Track 5.2; note: the TDD §5.5 includes fullscreen detection in the poller, but it is deferred here to keep this track focused)
- Z-order clipping of overlapping window surfaces (→ future enhancement)
- macOS/Linux platform-specific poller variants (pywinctl handles cross-platform)
- Physics engine changes

## Forward-Compatibility Notes

- **Fullscreen detection (Track 5.2):** The `EnvironmentPoller` class will likely need an additional `fullscreen_changed(bool)` signal added in Track 5.2. Design the class to accept future signal additions.
- **Surface/edge conflict (Track 2.3):** When Track 2.3 adds Climb & WallSlide, the `physics.py` built-in edge detection may conflict with `screen_left`/`screen_right` surfaces from the poller. Track 2.3 will need to reconcile these two systems.
