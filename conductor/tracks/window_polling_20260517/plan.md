# Implementation Plan: Track 2.1 — Window Polling & Surface Detection

## Phase 1: Config Update & Surface Dataclass

- [x] Task: Update `WINDOW_POLL_INTERVAL_MS` in `config.py` from 200 → 300 [f404ce1]
    - [x] Add `TestPollingConstants` class in `test_config.py` to validate the constant value and type
- [ ] Task: Create `Surface` dataclass in `src/mochi/core/environment.py`
    - [ ] Write tests: `test_environment.py` — Surface has correct fields (`rect: QRect`, `surface_type: str`, `window_id: int | None`), defaults, and `@dataclass` behavior
    - [ ] Implement `@dataclass` with all three fields
- [ ] Task: Update `src/mochi/core/__init__.py` to export `Surface`

## Phase 2: EnvironmentPoller (QThread + Polling Loop)

- [ ] Task: Implement `EnvironmentPoller(QThread)` skeleton
    - [ ] Write tests: `test_environment.py` — class exists, is `QThread` subclass, has `platforms_updated = Signal(list)`, accepts `screen_geo: QRect` in `__init__`
    - [ ] Implement class skeleton: `QThread` subclass with `platforms_updated = Signal(list)`, store `screen_geo` from constructor
- [ ] Task: Implement window enumeration and filtering
    - [ ] Write tests: filters out minimized windows, empty-title windows, and "Mochi"-titled windows; includes visible windows; uses mocked `pywinctl` to avoid platform dependency
    - [ ] Implement `_get_visible_windows()` — calls `pywinctl.getAllWindows()`, applies filters (minimized, empty title, title "Mochi")
- [ ] Task: Implement surface list builder
    - [ ] Write tests: given mock windows with known rects, produces correct `Surface` objects for all 6 types (`window_top`, `window_left`, `window_right`, `screen_bottom`, `screen_left`, `screen_right`)
    - [ ] Write tests: `screen_bottom` Y coordinate matches `SCREEN_BOTTOM_MARGIN_PX + SPRITE_CELL_HEIGHT` formula (consistent with `Canvas._screen_bottom_y()`)
    - [ ] Implement `_build_surfaces(windows) -> list[Surface]` — window tops, window left/right, screen edges from cached `screen_geo`
- [ ] Task: Implement polling loop with QTimer
    - [ ] Write tests: verify `platforms_updated` signal emission on tick (use mocked `pywinctl` + `QTest.qWait`)
    - [ ] Implement `run()`: create `QTimer`, connect `timeout` → `_poll`, call `self.exec()` to start event loop
    - [ ] Implement `_poll()`: orchestrate `_get_visible_windows()` → `_build_surfaces()` → emit signal

## Phase 3: Error Handling & Edge Cases

- [ ] Task: Implement error resilience
    - [ ] Write tests: `pywinctl.getAllWindows()` raises → cached list re-emitted, warning logged
    - [ ] Write tests: zero visible windows → only screen edges in surface list
    - [ ] Write tests: `pywinctl` not importable (platform unsupported) → graceful degradation
    - [ ] Implement error handling with cached fallback and try/except in `_poll()`

## Phase 4: Canvas Integration

- [ ] Task: Wire `platforms_updated` signal into Canvas
    - [ ] Write tests: Canvas creates `EnvironmentPoller`, signal updates `_surfaces` cache; mocked poller verifies cross-thread signal delivery
    - [ ] Modify `Canvas.__init__()` to instantiate `EnvironmentPoller(screen_geo=self._screen_geo)` and start it
    - [ ] Connect `poller.platforms_updated.connect(self._on_platforms_updated)`
    - [ ] Implement `_on_platforms_updated(surfaces: list[Surface])` — stores list, logs summary at INFO level (e.g., "Surfaces updated: 12 windows, 39 surfaces")
    - [ ] Implement poller teardown: override `Canvas.closeEvent()` or connect to `QApplication.aboutToQuit` to call `self._poller.quit()`, `self._poller.wait(1000)`, `self._poller.deleteLater()` in sequence

## Phase 5: Verification & Cleanup

- [ ] Task: Run full test suite — `uv run pytest` — all existing + new tests pass
- [ ] Task: Run lint/type checks — `uv run ruff check src/` and `uv run mypy src/mochi/` — zero errors
- [ ] Task: Commit all changes with descriptive messages
