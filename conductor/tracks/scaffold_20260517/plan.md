# Implementation Plan: Phase 0 — Project Foundation (Scaffold & Dev Environment)

## Phase 0: Project Foundation

### Task 0.1: Initialize pyproject.toml and install dependencies `4bf3da6`
- [x] Create `pyproject.toml` with project name "mochi", version "1.0.0", Python >= 3.11
- [x] Add runtime dependencies: PySide6-Essentials >= 6.7, < 7.0; pywinctl >= 0.4, < 1.0; pymonctl >= 0.4, < 1.0
- [x] Add dev dependencies: pytest >= 8.0, pytest-qt >= 4.4, pytest-cov >= 6.0, pytest-xdist >= 3.5, mypy >= 1.13, ruff >= 0.9.0, PyInstaller >= 6.0
- [x] Add release dependencies: Nuitka >= 2.0
- [x] Configure Ruff lint: target-version py311, line-length 100, src = ["src"], select = [E, W, F, I, N, UP, B, SIM, RUF], isort known-first-party = ["mochi"]
- [x] Configure Ruff format: line-length 100 (inherits from parent), docstring-code-format = true
- [x] Configure mypy: strict mode, python_version 3.11, ignore missing imports for pywinctl and pymonctl
- [x] Configure pytest: testpaths = ["tests"], qt_api = "pyside6", addopts with coverage
- [x] Configure coverage: source = ["src/mochi"], omit __main__.py
- [x] Run `uv sync --extra dev` to create .venv and install all dependencies
- [x] Verify: `uv.lock` is generated and committed to version control

### Task 0.2: Create project directory structure `0eab6b3`
- [x] Create directories: `src/mochi/`, `src/mochi/models/`, `src/mochi/core/`, `src/mochi/ui/`, `src/mochi/utils/`, `tests/`, `assets/sprites/`
- [x] Create `__init__.py` in each Python package directory (src/mochi, models, core, ui, utils)
- [x] Create empty `tests/__init__.py` for pytest discovery
- [x] Create placeholder `assets/sprites/.gitkeep` to preserve the directory
- [x] Create `src/mochi/__main__.py` as a minimal `python -m mochi` entry point (stub that imports `main` — will be completed in Task 0.10)
- [x] Verify: `uv run python -c "import mochi"` succeeds with no errors

### Task 0.3: Write tests for config.py `4b76d86`
- [x] Write `tests/test_config.py`:
    - [x] Test that all physics constants are positive floats
    - [x] Test that all FSM timer tuples are (min, max) with min < max
    - [x] Test that all metric constants are within valid ranges
    - [x] Test that animation/render constants are positive integers
- [x] Run tests and confirm they fail (no implementation yet) — **Red Phase**

### Task 0.4: Implement config.py `3a2373d`
- [x] Create `src/mochi/config.py` with all physics constants (GRAVITY, TERMINAL_VELOCITY, WALK_SPEED, CLIMB_SPEED, WALL_SLIDE_SPEED)
- [x] Add all FSM timer constants (IDLE_TO_WALK_TIMER, IDLE_TO_SLEEP_TIMER, WALK_TO_IDLE_TIMER, CLIMB_TO_WALLSLIDE_TIMER, CLIMB_TIMEOUT, WALLSLIDE_TO_CLIMB_TIMER, SLEEP_DURATION_TIMER)
- [x] Add all metric constants (HUNGER_DECAY_PER_HOUR, BOREDOM_DECAY_PER_HOUR, AFFECTION_DECAY_PER_HOUR, LOW_HUNGER_SPEED_PENALTY, BOREDOM_LOW_THRESHOLD, AFFECTION_AVOIDANCE_THRESHOLD, HAPPY_ZOOMIE_CHANCE, MAX_OFFLINE_DECAY_HOURS, STATE_WRITE_DEBOUNCE_S, ITEM_APPROACH_TIMEOUT_S)
- [x] Add rendering constants (ANIMATION_TICK_MS, SPRITE_CELL_WIDTH, SPRITE_CELL_HEIGHT, SPRITE_SCALE)
- [x] Add polling constant (WINDOW_POLL_INTERVAL_MS)
- [x] Add item constants (FOOD_COOLDOWN_S, YARN_COOLDOWN_S, PET_COOLDOWN_S, BOX_COOLDOWN_S, BOX_DURATION_S)
- [x] Add onboarding constant (ONBOARDING_DURATION_S)
- [x] Run tests and confirm they pass — **Green Phase**
- [x] Run `uv run ruff check src/` — zero lint errors
- [x] Run `uv run mypy src/mochi/` — zero type errors (pending main.py)

### Task 0.5: Write tests for logger.py `23b6c1c`
- [x] Write `tests/test_logger.py`:
    - [x] Test that `setup_logging()` creates both console and file handlers
    - [x] Test that logging at INFO level produces output
    - [x] Test that log format matches expected pattern
    - [x] Test that debug=True enables DEBUG output
    - [x] Test that debug=False (default) suppresses DEBUG
    - [x] Test that log file is actually written
- [x] Run tests and confirm they fail — **Red Phase**

### Task 0.6: Implement logger.py `ac65c63`
- [x] Create `src/mochi/utils/logger.py` with `setup_logging(debug: bool = False) -> None` function
- [x] Configure logging with timestamp, level, name, message format
- [x] Add StreamHandler (stdout) and FileHandler ("mochi.log")
- [x] Use DEBUG level when debug=True, INFO otherwise
- [x] Run tests and confirm they pass — **Green Phase**
- [x] Run `uv run ruff check src/` — zero lint errors
- [x] Run `uv run mypy src/mochi/` — zero type errors (pending main.py)

### Task 0.7: Write tests for platform.py `b43cc34`
- [x] Write `tests/test_platform.py`:
    - [x] Test that `get_platform()` returns one of "win32", "darwin", "linux" (based on sys.platform)
    - [x] Test that `get_data_dir()` returns a Path object
    - [x] Test that `is_alt_held()` returns a boolean
    - [x] Test that `set_click_through()` accepts a QWidget and bool without raising
- [x] Run tests and confirm they fail — **Red Phase**

### Task 0.8: Implement platform.py stubs `99bfbc2`
- [x] Create `src/mochi/utils/platform.py`:
    - [x] Implement `get_platform() -> str` returning sys.platform
    - [x] Implement `get_data_dir() -> Path` resolving OS-appropriate data directory with fallback (`%APPDATA%/Mochi`, `~/Library/Application Support/Mochi`, or `~/.local/share/mochi`), creating it via `mkdir(parents=True, exist_ok=True)` on first call
    - [x] Implement `is_alt_held() -> bool` returning False as default stub
    - [x] Implement `set_click_through(window: "QWidget", enabled: bool) -> None` with platform-specific branching (win32 stub with ctypes placeholder for `WS_EX_TRANSPARENT`, darwin/linux no-op stubs). Used `from __future__ import annotations` + TYPE_CHECKING to avoid forward-import issues
- [x] Run tests and confirm they pass — **Green Phase**
- [x] Run `uv run ruff check src/` — zero lint errors
- [x] Run `uv run mypy src/mochi/` — zero type errors (pending main.py)

### Task 0.9: Write tests for main.py and __main__.py
- [ ] Write `tests/test_main.py`:
    - [ ] Test that main module's `create_application()` returns a QApplication instance
    - [ ] Test that application name is set to "Mochi"
    - [ ] Test that logging is initialized on startup
- [ ] Write `tests/test_entry.py`:
    - [ ] Test that `__main__.py` has the `if __name__ == '__main__':` guard pattern
    - [ ] Test that `__main__.py` imports the `main` module
- [ ] Run tests and confirm they fail — **Red Phase**

### Task 0.10: Implement main.py
- [ ] Create `src/mochi/main.py`:
    - [ ] Import QApplication from PySide6.QtWidgets
    - [ ] Set organization and application names
    - [ ] Call setup_logging()
    - [ ] Create QApplication instance
    - [ ] Log "Mochi started" message
    - [ ] Wire `__main__.py` to call main entry point via `main.main()` from `if __name__ == '__main__':` guard
- [ ] Run tests and confirm they pass — **Green Phase**
- [ ] Verify: `uv run python -m mochi` launches and logs startup message
- [ ] Run `uv run ruff check src/` — zero lint errors
- [ ] Run `uv run mypy src/mochi/` — zero type errors

### Task 0.11: Final tooling verification
- [ ] Run full test suite: `uv run pytest` — all tests pass
- [ ] Run linter: `uv run ruff check src/` — zero errors
- [ ] Run formatter check: `uv run ruff format --check src/` — zero formatting violations
- [ ] Run type checker: `uv run mypy src/mochi/` — zero errors
- [ ] Verify all config constants importable: `uv run python -c "from mochi.config import *"` — no errors
- [ ] Verify application launches: `uv run python -m mochi` — logs startup and exits cleanly
- [ ] Verify `uv.lock` is committed to version control

### Task 0.12: Phase Completion Verification
- [ ] Task: Conductor - User Manual Verification 'Phase 0: Project Foundation' (Protocol in workflow.md)
    - [ ] Run automated tests per Phase Completion Protocol
    - [ ] Present manual verification plan to user
    - [ ] Create checkpoint commit with auditable git notes
