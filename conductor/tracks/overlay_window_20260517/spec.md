# Specification: Track 1.1 — Transparent Overlay Window

## Goal
Create a fullscreen, transparent, always-on-top overlay window that serves as the rendering surface for Mochi. The window covers the primary monitor, is click-through by default, and renders a green test rectangle to prove the rendering pipeline works.

## Scope
This track delivers the foundational rendering surface. It does NOT include sprites, animation, FSM, or cat behavior — those come in Tracks 1.2 and 1.3.

## Modules Affected

| Module | Change |
|---|---|
| `src/mochi/core/canvas.py` | **NEW** — `Canvas(QWidget)` class: frameless, transparent, always-on-top, fullscreen overlay |
| `src/mochi/utils/platform.py` | **MODIFY** — Extend `set_click_through()` with full macOS and Linux X11 implementations |
| `src/mochi/main.py` | **MODIFY** — Instantiate and show Canvas on launch |
| `tests/test_canvas.py` | **NEW** — Unit tests for Canvas class |
| `tests/test_platform.py` | **MODIFY** — Add tests for new platform click-through implementations |

## Functional Requirements

### FR1: Canvas Window
- A `Canvas` class extending `QWidget` is created in `src/mochi/core/canvas.py`
- Window flags: `FramelessWindowHint | WindowStaysOnTopHint | Tool`
- Widget attribute: `WA_TranslucentBackground = True`
- Geometry: full dimensions of the **primary monitor** only (single-monitor MVP)
- Window spans exactly the primary screen dimensions

### FR2: Click-Through Default
- Click-through is **enabled by default** on launch via `platform.set_click_through()`
- The function must work on all 3 target platforms:
  - **Windows**: `WS_EX_TRANSPARENT` via `ctypes.windll.user32 SetWindowLongW / GetWindowLongW` (already implemented as a stub)
  - **macOS**: `NSWindow.setIgnoresMouseEvents_(True)` via Python `objc` bridge
  - **Linux X11**: `XShapeCombineRectangles` via Python `Xlib` to set an empty input shape mask

### FR3: Test Rectangle Rendering
- `paintEvent()` renders a green rectangle (`#00FF00`, 64×64 px)
- Position: centered horizontally at the screen bottom (Y = screen height - canvas bottom margin, sitting above the taskbar)
- The rectangle is a placeholder that will be replaced by the cat sprite in Track 1.2

### FR4: Wiring into Main
- `main.py` creates the `Canvas` instance after `QApplication` bootstrap
- Canvas is shown on launch via `.show()`
- Logging confirms canvas creation and dimensions at INFO level

## Acceptance Criteria

- [ ] A transparent, always-on-top, fullscreen overlay window covers the primary monitor
- [ ] A green 64×64 rectangle is visible at the bottom center of the screen
- [ ] Clicking anywhere on the overlay passes through to underlying windows
- [ ] Click-through works on all 3 platforms (Windows, macOS, Linux X11)
- [ ] No flicker or visual artifacts on launch
- [ ] Window follows Qt widget lifecycle — closes cleanly on app exit
- [ ] `uv run ruff check src/` — zero lint errors on new code
- [ ] `uv run mypy src/mochi/` — zero type errors on new code
- [ ] `uv run pytest` — all existing tests + new tests pass

## Out of Scope
- Cat sprites or animation (Track 1.2)
- FSM or physics engine (Track 1.3)
- Window polling or environment awareness (Phase 2)
- Alt-key detection or click-through toggle logic (Phase 3)
- Adaptive tick rate or animation timer
- Sprite sheet loading
