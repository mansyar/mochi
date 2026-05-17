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
| `src/mochi/config.py` | **MODIFY** — Add `WINDOW_POLL_INTERVAL_MS` constant (300ms) |
| `src/mochi/core/canvas.py` | **MODIFY** — Connect `platforms_updated` signal to store surface list |
| `src/mochi/core/__init__.py` | **MODIFY** — Export `Surface` |
| `src/mochi/core/physics.py` | **NO CHANGE** — `surfaces` param already reserved, integration deferred |
| `tests/test_environment.py` | **NEW** — Unit tests for poller filtering, Surface construction, signals |
| `tests/test_config.py` | **MODIFY** — Add validation test for new config constant |
| `tests/test_physics.py` | **NO CHANGE** — Ground detection deferred to Track 2.2 |

## Functional Requirements

### FR1: Surface Dataclass (`environment.py`)
- A `@dataclass` named `Surface` with fields:
  - `rect: QRect` — The bounding rectangle in screen coordinates
  - `surface_type: str` — One of: `"window_top"`, `"screen_bottom"`, `"screen_left"`, `"screen_right"`, `"window_left"`, `"window_right"`
  - `window_id: int | None` — OS window handle (for tracking moves/closes); `None` for screen edges

### FR2: EnvironmentPoller (`environment.py`)
- A class `EnvironmentPoller(QThread)` that:
  - Creates a `QTimer` at `WINDOW_POLL_INTERVAL_MS` (300ms) on the thread's event loop
  - Each tick:
    1. Calls `pywinctl.getAllWindows()` to enumerate all visible OS windows
    2. **Filters** the list: excludes minimized windows, excludes windows with empty titles, excludes the Mochi overlay itself (by window title "Mochi")
    3. **Builds surfaces:** For each window, computes:
       - `window_top` — a horizontal surface at the window's `y()` spanning `x()` to `x() + width()`
       - `window_left` — a vertical surface at the window's `x()` spanning `y()` to `y() + height()`
       - `window_right` — a vertical surface at `x() + width()`
    4. Adds **screen edges** (from primary monitor geometry):
       - `screen_bottom` — bottom of available geometry (above taskbar)
       - `screen_left` / `screen_right` — left and right bezels
    5. Emits `platforms_updated(list[Surface])` signal

### FR3: Signal & Slot Wiring
- `EnvironmentPoller` declares a Qt signal: `platforms_updated = Signal(list)` (using `list[Surface]` at runtime)
- Canvas stores the most recent surface list: `self._surfaces: list[Surface] = []`
- On receiving the signal, Canvas updates its cached surface list and logs a summary line
- No physics behavior change yet — the cat continues walking on screen bottom only

### FR4: Error Handling
- If `pywinctl.getAllWindows()` raises an exception (permission denied, OS error), log a warning with the exception details and emit the previously cached surface list instead
- If no windows are visible, emit a surface list containing only screen edges
- The poller must not crash under any error condition

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
5. `platforms_updated` signal is emitted every 300ms
6. Canvas receives the signal and caches the surface list
7. If `pywinctl.getAllWindows()` raises, the previous surface list is re-emitted and a warning is logged
8. All unit tests pass with >80% coverage for new code
9. Zero lint errors (`ruff check`), zero type errors (`mypy strict`)

## Out of Scope
- Ground snapping / surface landing (→ Track 2.2)
- Gravity and falling physics (→ Track 2.2)
- Window move/close tracking via `window_id` (→ Track 2.2)
- Fullscreen detection (→ Track 5.2)
- macOS/Linux platform-specific poller variants (pywinctl handles cross-platform)
- Physics engine changes
