# Implementation Plan: Track 1.1 — Transparent Overlay Window

## Phase: Track 1.1 — Transparent Overlay Window

### Task 1: Implement Canvas class in `src/mochi/core/canvas.py`
- [ ] **Sub-task 1.1: Write failing tests for Canvas (Red)**
    - [ ] Create `tests/test_canvas.py` with test class `TestCanvas`
    - [ ] Test that Canvas is a QWidget subclass
    - [ ] Test that Canvas has `FramelessWindowHint`, `WindowStaysOnTopHint`, and `Tool` flags set
    - [ ] Test that `WA_TranslucentBackground` is set
    - [ ] Test that Canvas geometry matches primary screen dimensions (via mock QScreen)
    - [ ] Test that `paintEvent` produces a QPainter draw (mock test — verify no errors)
    - [ ] Run tests and confirm they fail as expected (import errors / no Canvas class yet)
- [ ] **Sub-task 1.2: Implement Canvas class (Green)**
    - [ ] Create `src/mochi/core/canvas.py` with `Canvas(QWidget)` class
    - [ ] Set window flags: `FramelessWindowHint | WindowStaysOnTopHint | Tool`
    - [ ] Set attribute: `WA_TranslucentBackground = True`
    - [ ] Get primary screen geometry using `QScreen` / `QGuiScreen.primaryScreen()`
    - [ ] Set Canvas geometry to full primary screen dimensions
    - [ ] Implement `paintEvent()` to draw a green (`#00FF00`) 64×64 rectangle at screen bottom center
    - [ ] Run tests and confirm all pass

### Task 2: Implement full cross-platform click-through in `platform.py`
- [ ] **Sub-task 2.1: Write failing tests for macOS/Linux click-through (Red)**
    - [ ] Add tests in `tests/test_platform.py`:
        - [ ] Test that `set_click_through(window, True)` on a mock widget doesn't raise on any platform
        - [ ] Test that `set_click_through(window, False)` doesn't raise on any platform
    - [ ] Run tests and confirm they fail (or pass as no-op stubs — document current behavior as baseline)
- [ ] **Sub-task 2.2: Implement macOS click-through**
    - [ ] Implement `_set_click_through_macos(window, enabled)` in `platform.py`
    - [ ] Use `objc` bridge to call `NSWindow.setIgnoresMouseEvents_()`
    - [ ] Gate behind `sys.platform == "darwin"` check
- [ ] **Sub-task 2.3: Implement Linux X11 click-through**
    - [ ] Implement `_set_click_through_linux(window, enabled)` in `platform.py`
    - [ ] Use `Xlib` to call `XShapeCombineRectangles` with empty shape mask
    - [ ] Gate behind `sys.platform == "linux"` check
- [ ] **Sub-task 2.4: Update `set_click_through()` dispatch**
    - [ ] Add `"darwin"` and `"linux"` branches to `set_click_through()`
    - [ ] Run full test suite and verify all pass
    - [ ] Run `uv run ruff check src/` — zero errors
    - [ ] Run `uv run mypy src/mochi/` — zero errors

### Task 3: Wire Canvas into `main.py`
- [ ] **Sub-task 3.1: Write failing tests for main.py integration (Red)**
    - [ ] Add test in `tests/test_main.py`: verify that `main.create_application()` + canvas creation doesn't crash
    - [ ] Mock Canvas to verify `.show()` is called
    - [ ] Run tests and confirm they fail (no Canvas import yet)
- [ ] **Sub-task 3.2: Modify main.py to create and show Canvas**
    - [ ] Import Canvas in `main.py`
    - [ ] Instantiate Canvas after QApplication bootstrap in `create_application()` or `main()`
    - [ ] Call `canvas.show()`
    - [ ] Log canvas dimensions at INFO level on creation
    - [ ] Call `platform.set_click_through(canvas, True)` after showing
    - [ ] Run tests and confirm all pass
    - [ ] Run `uv run ruff check src/` — zero errors
    - [ ] Run `uv run mypy src/mochi/` — zero errors

### Task 4: Final verification & code quality
- [ ] Run full test suite: `uv run pytest` — all tests pass
- [ ] Run linter: `uv run ruff check src/` — zero errors
- [ ] Run formatter: `uv run ruff format --check src/` — zero violations
- [ ] Run type checker: `uv run mypy src/mochi/` — zero errors
- [ ] Verify coverage meets requirements

### Task 5: Phase Completion Verification
- [ ] Task: Conductor - User Manual Verification 'Track 1.1 — Transparent Overlay Window' (Protocol in workflow.md)
