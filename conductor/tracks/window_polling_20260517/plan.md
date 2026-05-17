# Implementation Plan: Track 2.1 — Window Polling & Surface Detection

## Phase 1: Surface Dataclass & Config

- [ ] Task: Add `WINDOW_POLL_INTERVAL_MS = 300` config constant to `config.py`
    - [ ] Validation tests for the new constant in `test_config.py`
- [ ] Task: Create `Surface` dataclass in `src/mochi/core/environment.py`
    - [ ] Write tests: `test_environment.py` — Surface has correct fields, types, defaults
    - [ ] Implement `@dataclass` with `rect: QRect`, `surface_type: str`, `window_id: int | None`
- [ ] Task: Update `src/mochi/core/__init__.py` to export `Surface`

## Phase 2: EnvironmentPoller (QThread + Polling Loop)

- [ ] Task: Implement `EnvironmentPoller(QThread)` skeleton
    - [ ] Write tests: `test_environment.py` — class exists, is QThread subclass, has `platforms_updated` signal
    - [ ] Implement class skeleton: `QThread` subclass with `platforms_updated = Signal(list)`
- [ ] Task: Implement window enumeration and filtering
    - [ ] Write tests: filters out minimized, empty-title, and "Mochi"-titled windows; includes visible windows
    - [ ] Implement `_get_visible_windows()` — calls `pywinctl.getAllWindows()`, applies filters
- [ ] Task: Implement surface list builder
    - [ ] Write tests: given mock windows, produces correct `Surface` objects for all 6 types
    - [ ] Implement `_build_surfaces(windows) -> list[Surface]` — window tops, window left/right, screen edges
- [ ] Task: Implement polling loop with QTimer
    - [ ] Write tests: verify signal emission on tick (use mocked pywinctl)
    - [ ] Implement `QTimer` in `_run()` / `_poll()` on the QThread event loop

## Phase 3: Error Handling & Edge Cases

- [ ] Task: Implement error resilience
    - [ ] Write tests: `pywinctl.getAllWindows()` raises → cached list re-emitted, warning logged
    - [ ] Write tests: zero visible windows → only screen edges in surface list
    - [ ] Implement error handling with cached fallback

## Phase 4: Canvas Integration

- [ ] Task: Wire `platforms_updated` signal into Canvas
    - [ ] Write tests: Canvas creates EnvironmentPoller, signal updates `_surfaces` cache
    - [ ] Modify `Canvas.__init__()` to instantiate and start `EnvironmentPoller`
    - [ ] Connect `poller.platforms_updated.connect(self._on_platforms_updated)`
    - [ ] Implement `_on_platforms_updated(surfaces)` — stores list, logs summary
    - [ ] Ensure poller quits on Canvas destruction

## Phase 5: Verification & Cleanup

- [ ] Task: Run full test suite — `uv run pytest` — all existing + new tests pass
- [ ] Task: Run lint/type checks — `uv run ruff check src/` and `uv run mypy src/mochi/` — zero errors
- [ ] Task: Commit all changes with descriptive messages
