# Implementation Plan: Track 1.1 — Transparent Overlay Window

## Phase: Track 1.1 — Transparent Overlay Window

### Task 0: Add screen-related config constant [9288a00]
- [x] **Sub-task 0.1: Write failing test for config constant (Red)**
    - [x] Add test in `tests/test_config.py` — verify `SCREEN_BOTTOM_MARGIN_PX` exists and is a positive integer
    - [x] Run tests and confirm they pass (constant already existed from Phase 0)
    - [x] *Note: Constant already existed; no Red phase achievable — test passed immediately*
- [x] **Sub-task 0.2: Add `SCREEN_BOTTOM_MARGIN_PX` to config.py (Green)**
    - [x] `SCREEN_BOTTOM_MARGIN_PX: int = 48` already present in `config.py` under `# ── Screen / Canvas ───` section (from Phase 0)
    - [x] Run tests and confirm all pass

### Task 1: Implement Canvas class in `src/mochi/core/canvas.py` [fc57717]
- [x] **Sub-task 1.1: Write failing tests for Canvas (Red)**
    - [x] Create `tests/test_canvas.py` with test class `TestCanvas`
    - [x] Test that Canvas is a QWidget subclass
    - [x] Test that Canvas has `FramelessWindowHint`, `WindowStaysOnTopHint`, and `Tool` flags set
    - [x] Test that `WA_TranslucentBackground` is set
    - [x] Test that Canvas geometry matches primary screen's `availableGeometry()`
    - [x] Test that `paintEvent` draws without raising
    - [x] Pixel grab test added (skipped — requires display)
    - [x] Ran tests — 7 failed as expected (ModuleNotFoundError)
- [x] **Sub-task 1.2: Implement Canvas class (Green)**
    - [x] Create `src/mochi/core/canvas.py` with `Canvas(QWidget)` class
    - [x] Set window flags: `FramelessWindowHint | WindowStaysOnTopHint | Tool`
    - [x] Set attribute: `WA_TranslucentBackground = True`
    - [x] Get primary screen geometry using `QGuiScreen.primaryScreen().availableGeometry()`
    - [x] Set Canvas geometry to full primary screen available geometry
    - [x] Implement `paintEvent()` to draw a green (`#00FF00`) 64x64 rectangle
    - [x] Run tests and confirm all pass
    - [x] Run `uv run ruff check src/` — zero errors
    - [x] Run `uv run mypy src/mochi/` — zero errors

### Task 2: Verify Windows click-through in `platform.py`
- [ ] **Sub-task 2.0: This task scoped to Windows only** — macOS/Linux `set_click_through()` remains no-op stubs per ROADMAP. No new platform implementations in this track.
- [ ] **Sub-task 2.1: Write proper tests for existing Windows click-through (Red)**
    - [ ] Add tests in `tests/test_platform.py`:
        - [ ] Test that `set_click_through(None, True)` does not raise (existing guard — keep)
        - [ ] Test that `set_click_through(None, False)` does not raise (existing guard — keep)
        - [ ] Test that `set_click_through(mock_widget, True)` calls the Windows platform function (mock `_set_click_through_win32`)
        - [ ] Test that `set_click_through(mock_widget, False)` calls the Windows platform function (mock `_set_click_through_win32`)
        - [ ] Test that on non-Windows platforms (mock `sys.platform`), calling `set_click_through` does not crash (no-op path)
    - [ ] Run tests and confirm the new tests fail (Windows path may not be properly mock-testable yet)
- [ ] **Sub-task 2.2: Refactor platform.py for testability (Green)**
    - [ ] No code changes to `set_click_through()` needed — the existing Windows implementation is correct
    - [ ] Ensure the tests from 2.1 pass with proper mocking
    - [ ] Run full test suite and verify all pass
    - [ ] Run `uv run ruff check src/` — zero errors
    - [ ] Run `uv run mypy src/mochi/` — zero errors

### Task 3: Wire Canvas into `main.py`
- [ ] **Sub-task 3.1: Write failing tests for main.py integration (Red)**
    - [ ] Add Canvas mock to existing `test_main.py` — patch `mochi.main.Canvas` so existing tests remain unbroken
    - [ ] Add new test: verify that `main()` instantiates Canvas and calls `.show()`
    - [ ] Add new test: verify that Canvas dimensions are logged at INFO level
    - [ ] Run tests and confirm they fail (no Canvas import in main.py yet)
- [ ] **Sub-task 3.2: Modify main.py to create and show Canvas (Green)**
    - [ ] Import Canvas in `main.py`: `from mochi.core.canvas import Canvas`
    - [ ] Import `QTimer` for deferred click-through setup
    - [ ] In the `main()` function (NOT `create_application()`), instantiate Canvas after QApplication:
        ```python
        canvas = Canvas()
        canvas.show()
        logger.info("Canvas created: %dx%d", canvas.width(), canvas.height())
        QTimer.singleShot(0, lambda: set_click_through(canvas, True))
        ```
    - [ ] Run tests and confirm all pass (existing tests + new tests)
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
