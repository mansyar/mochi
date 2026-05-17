# Specification: Phase 0 — Project Foundation (Scaffold & Dev Environment)

## Goal
Create a runnable Python project skeleton with all development tooling configured. No visible output yet — this phase establishes the foundation for all subsequent development.

## Scope
This track covers the full project setup: package management, directory structure, configuration constants, logging, platform abstraction stubs, and a minimal application entry point.

## Modules Created

| Module | Responsibility |
|---|---|
| `pyproject.toml` | Project metadata, dependencies, dev tool configuration (ruff, mypy, pytest, coverage) |
| `src/mochi/__init__.py` | Package marker |
| `src/mochi/__main__.py` | `python -m mochi` entry point (supplements TDD — not in original directory structure) |
| `src/mochi/main.py` | `QApplication` bootstrap |
| `src/mochi/config.py` | All tunable constants (physics, FSM timers, metrics, rendering, polling, items, onboarding) |
| `src/mochi/utils/__init__.py` | Package marker |
| `src/mochi/utils/logger.py` | `setup_logging()` with console + file handlers |
| `src/mochi/utils/platform.py` | OS detection stubs: `get_platform()`, `get_data_dir()`, `is_alt_held()`, `set_click_through()` |
| `assets/sprites/` | Placeholder sprite directory |

## Acceptance Criteria

- [ ] `uv run python -m mochi` launches, logs a startup message, and exits cleanly
- [ ] `uv run pytest` discovers the test directory with zero failures
- [ ] `uv run ruff check src/` — zero lint errors
- [ ] `uv run ruff format --check src/` — zero formatting violations
- [ ] `uv run mypy src/mochi/` — zero type errors
- [ ] All config constants are importable from `mochi.config`
- [ ] `uv.lock` is committed to version control

## Non-Goals
- No cat sprites or rendering
- No FSM or physics engine
- No window polling or environment awareness
- No user interaction (hotkeys, toolbox, drag)
- No pet metrics or persistence
