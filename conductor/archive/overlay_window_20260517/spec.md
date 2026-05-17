# Specification: Track 1.1 — Transparent Overlay Window

## Goal
Create a fullscreen, transparent, always-on-top overlay window that serves as the rendering surface for Mochi. The window covers the primary monitor, is click-through by default (Windows MVP; macOS/Linux stubbed), and renders a green test rectangle to prove the rendering pipeline works.

## Scope
This track delivers the foundational rendering surface. It does NOT include sprites, animation, FSM, or cat behavior — those come in Tracks 1.2 and 1.3.

## Modules Affected

| Module | Change |
|---|---|
| `src/mochi/config.py` | **MODIFY** — Add `SCREEN_BOTTOM_MARGIN_PX` constant for test rectangle positioning |
| `src/mochi/core/canvas.py` | **NEW** — `Canvas(QWidget)` class: frameless, transparent, always-on-top, fullscreen overlay |
| `src/mochi/main.py` | **MODIFY** — Instantiate and show Canvas on launch (in `main()`, not `create_application()`) |
| `tests/test_canvas.py` | **NEW** — Unit tests for Canvas class |
| `tests/test_main.py` | **MODIFY** — Add Canvas mock to existing tests |
| `tests/test_platform.py` | **MODIFY** — Add proper Windows click-through tests with mock widget |

**Unchanged:** `src/mochi/utils/platform.py` — macOS/Linux `set_click_through()` remains no-op stubs per ROADMAP. Full cross-platform click-through is deferred.

## Functional Requirements

### FR1: Canvas Window
- A `Canvas` class extending `QWidget` is created in `src/mochi/core/canvas.py`
- Window flags: `FramelessWindowHint | WindowStaysOnTopHint | Tool`
- Widget attribute: `WA_TranslucentBackground = True`
- Geometry: full dimensions of the **primary monitor** only (single-monitor MVP)
- Screen dimensions obtained via `QScreen.availableGeometry()` (which excludes OS taskbar/dock)
- Window spans exactly the primary screen's available geometry

### FR2: Click-Through Default
- Click-through is **enabled by default** on launch via `platform.set_click_through()`
- **Windows**: `WS_EX_TRANSPARENT` via `ctypes.windll.user32 SetWindowLongW / GetWindowLongW` — full implementation (existing code)
- **macOS**: No-op stub (deferred to a future cross-platform track)
- **Linux X11**: No-op stub (deferred to a future cross-platform track)
- `set_click_through()` call is deferred via `QTimer.singleShot(0, ...)` after `.show()` to ensure the native window handle (`winId()`) is fully realized

### FR3: Test Rectangle Rendering
- `paintEvent()` renders a green rectangle (`#00FF00`, 64×64 px)
- Position: centered horizontally using `QScreen.availableGeometry().width()`, positioned at `availableGeometry().bottom() - SCREEN_BOTTOM_MARGIN_PX - 64`
- The `SCREEN_BOTTOM_MARGIN_PX` constant is defined in `config.py` (default: 48px clearance above taskbar)
- The rectangle is a placeholder that will be replaced by the cat sprite in Track 1.2

### FR4: Wiring into Main
- `main.py` creates the `Canvas` instance inside the `main()` function (after QApplication bootstrap), **not** inside `create_application()` — this keeps existing `create_application()` tests unchanged
- Canvas is shown on launch via `.show()`
- `set_click_through(canvas, True)` is called via `QTimer.singleShot(0, lambda: ...)` to avoid `winId()` race condition
- Logging confirms canvas creation and dimensions at INFO level

## Acceptance Criteria

- [ ] A transparent, always-on-top, fullscreen overlay window covers the primary monitor
- [ ] A green 64×64 rectangle is visible at the bottom center of the screen (above the taskbar/dock)
- [ ] Clicking anywhere on the overlay passes through to underlying windows
- [ ] Click-through works on Windows (macOS/Linux are no-op stubs — not blocking for this track)
- [ ] No flicker or visual artifacts on launch
- [ ] Window follows Qt widget lifecycle — closes cleanly on app exit
- [ ] `uv run ruff check src/` — zero lint errors on new code
- [ ] `uv run mypy src/mochi/` — zero type errors on new code
- [ ] `uv run pytest` — all existing tests + new tests pass (existing tests unaffected by changes)

## Out of Scope
- Cat sprites or animation (Track 1.2)
- FSM or physics engine (Track 1.3)
- Window polling or environment awareness (Phase 2)
- Alt-key detection or click-through toggle logic (Phase 3)
- Adaptive tick rate or animation timer
- Sprite sheet loading
- macOS/Linux click-through implementation (deferred)
