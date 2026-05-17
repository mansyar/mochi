# Implementation Plan: Track 2.1 — Window Polling & Surface Detection

## Phase 1: Config Update & Surface Dataclass

- [x] Task: Update `WINDOW_POLL_INTERVAL_MS` in `config.py` from 200 → 300 [f404ce1]
    - [x] Add `TestPollingConstants` class in `test_config.py` to validate the constant value and type
- [x] Task: Create `Surface` dataclass in `src/mochi/core/environment.py` [8db926e]
    - [x] Write tests: `test_environment.py` — Surface has correct fields (`rect: QRect`, `surface_type: str`, `window_id: int | None`), defaults, and `@dataclass` behavior
    - [x] Implement `@dataclass` with all three fields
- [x] Task: Update `src/mochi/core/__init__.py` to export `Surface` [fe93478]

## Phase 2: EnvironmentPoller (QThread + Polling Loop)

- [x] Task: Implement `EnvironmentPoller(QThread)` skeleton [b50b9c0]
    - [x] Write tests: `test_environment.py` — class exists, is `QThread` subclass, has `platforms_updated = Signal(list)`, accepts `screen_geo: QRect` in `__init__`
    - [x] Implement class skeleton: `QThread` subclass with `platforms_updated = Signal(list)`, store `screen_geo` from constructor
- [x] Task: Implement window enumeration and filtering [5ce01d3]
    - [x] Write tests: filters out minimized windows, empty-title windows, and "Mochi"-titled windows; includes visible windows; uses mocked `pywinctl` to avoid platform dependency
    - [x] Implement `_get_visible_windows()` — calls `pywinctl.getAllWindows()`, applies filters (minimized, empty title, title "Mochi")
- [x] Task: Implement surface list builder [b6ad5fe]
    - [x] Write tests: given mock windows with known rects, produces correct `Surface` objects for all 6 types (`window_top`, `window_left`, `window_right`, `screen_bottom`, `screen_left`, `screen_right`)
    - [x] Write tests: `screen_bottom` Y coordinate matches `SCREEN_BOTTOM_MARGIN_PX + SPRITE_CELL_HEIGHT` formula (consistent with `Canvas._screen_bottom_y()`)
    - [x] Implement `_build_surfaces(windows) -> list[Surface]` — window tops, window left/right, screen edges from cached `screen_geo`
- [x] Task: Implement polling loop with QTimer [3734ffd]
    - [x] Write tests: verify `platforms_updated` signal emission on tick (use mocked `pywinctl` + `QTest.qWait`)
    - [x] Implement `run()`: create `QTimer`, connect `timeout` → `_poll`, call `self.exec()` to start event loop
    - [x] Implement `_poll()`: orchestrate `_get_visible_windows()` → `_build_surfaces()` → emit signal

## Phase 3: Error Handling & Edge Cases

- [x] Task: Implement error resilience [9eb82a5]
    - [x] Write tests: `pywinctl.getAllWindows()` raises → cached list re-emitted, warning logged
    - [x] Write tests: zero visible windows → only screen edges in surface list (covered by TestSurfaceListBuilder)
    - [x] Write tests: `pywinctl` not importable (platform unsupported) → graceful degradation (covered by generic Exception handler)
    - [x] Implement error handling with cached fallback and try/except in `_poll()`

## Phase 4: Canvas Integration

- [x] Task: Wire `platforms_updated` signal into Canvas [656e015]
    - [x] Write tests: Canvas creates `EnvironmentPoller`, signal updates `_surfaces` cache; mocked poller verifies cross-thread signal delivery
    - [x] Modify `Canvas.__init__()` to instantiate `EnvironmentPoller(screen_geo=self._screen_geo)` (started lazily in `showEvent()` for test compatibility)
    - [x] Connect `poller.platforms_updated.connect(self._on_platforms_updated)`
    - [x] Implement `_on_platforms_updated(surfaces: list[Surface])` — stores list, logs summary at INFO level
    - [x] Implement poller teardown: `closeEvent()` → `_stop_poller()` → `quit()`, `wait(2000)`, `deleteLater()`

## Phase 5: Verification & Cleanup

- [x] Task: Run full test suite — `uv run pytest` — all 153 pass, 1 skip [0a81910]
- [x] Task: Run lint/type checks — `uv run ruff check src/` and `uv run mypy src/mochi/` — zero errors
- [x] Task: Commit all changes with descriptive messages

## Phase: Review Fixes
- [x] Task: Apply review suggestions — fix no-op test to add real assertions [a921e62]
