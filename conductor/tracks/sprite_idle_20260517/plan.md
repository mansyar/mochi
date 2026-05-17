# Implementation Plan: Track 1.2 — Sprite Loading & Idle Animation

## Phase 1: Sprite Sheet Loading

### Task 1.1: Add config constant for idle frame count
- [ ] Write test: `test_config.py` — verify `IDLE_FRAME_COUNT == 10` (matches IDLE.png: 640×64 / 64 = 10)
- [ ] Add `IDLE_FRAME_COUNT: int = 10` to `src/mochi/config.py`
- [ ] Run tests: confirm new config test passes

### Task 1.2: Write tests for SpriteSheet loader (Red Phase)
- [ ] Create `tests/test_sprites.py`
- [ ] Test: `SpriteSheet` class exists and is instantiable
- [ ] Test: `load()` loads IDLE.png and returns `list[QPixmap]` with exactly 10 frames
- [ ] Test: each frame pixmap has size 64×64
- [ ] Test: loading a non-existent file logs a warning and returns empty list
- [ ] Test: `get_frames("idle")` returns the cached frame list
- [ ] Test: `get_frames("nonexistent")` raises `KeyError`
- [ ] Run tests and confirm they fail (Red Phase)

### Task 1.3: Implement SpriteSheet class (Green Phase)
- [ ] Create `src/mochi/ui/sprites.py`
- [ ] Implement `SpriteSheet.__init__()` — store reference to asset directory
- [ ] Implement `load(animation_key: str) -> list[QPixmap]` — load PNG, slice into 64×64 cells, return list
- [ ] Implement `get_frames(animation_key: str) -> list[QPixmap]` — return cached frame list
- [ ] Implement asset path resolution relative to project root
- [ ] Handle missing PNG files: log warning, return empty list
- [ ] Run tests and confirm they pass (Green Phase)

### Task 1.4: Quality gate — lint, format, type-check sprites module
- [ ] `uv run ruff check src/mochi/ui/sprites.py` — zero errors
- [ ] `uv run mypy src/mochi/ui/sprites.py` — zero errors
- [ ] `uv run pytest tests/test_sprites.py` — all tests pass

## Phase 2: Idle Sprite Rendering & Animation

### Task 2.1: Write tests for Canvas sprite rendering and animation
- [ ] Add tests to `tests/test_canvas.py` or create `tests/test_animation.py`:
    - [ ] Test: Canvas creates a `QTimer` for animation tick
    - [ ] Test: Animation timer interval equals `ANIMATION_TICK_MS` (100ms)
    - [ ] Test: Frame index advances by 1 on each tick, wraps to 0 after `IDLE_FRAME_COUNT`-1
    - [ ] Test: `paintEvent` calls `painter.drawPixmap` with the correct current frame
    - [ ] Test: Green rectangle is no longer drawn (no `QColor("#00FF00")` or `fillRect` with that color)
- [ ] Run tests and confirm they fail (Red Phase)

### Task 2.2: Wire Canvas with SpriteSheet and animation timer
- [ ] In `Canvas.__init__()`:
    - [ ] Instantiate `SpriteSheet` pointing to `assets/sprites/`
    - [ ] Call `spritesheet.load("idle")` to cache idle frames
    - [ ] Create `QTimer` set to `ANIMATION_TICK_MS` interval
    - [ ] Connect timer timeout to slot that advances frame and calls `update()`
    - [ ] Start the timer
- [ ] Add instance variables: `_spritesheet: SpriteSheet`, `_current_frame: int`, `_idle_frames: list[QPixmap]`
- [ ] In `paintEvent()`:
    - [ ] Replace green `fillRect` with `painter.drawPixmap()` using current idle frame
    - [ ] Position: screen bottom-center (same X/Y formula as green rect)
- [ ] Run tests and confirm they pass (Green Phase)

### Task 2.3: Remove green test rectangle code
- [ ] Remove `QColor("#00FF00")` import/usage from `canvas.py`
- [ ] Remove `QColor` import if no longer used (keep `QPainter`)
- [ ] Verify: no `#00FF00` reference remains in source
- [ ] Run full test suite — confirm all tests pass

### Task 2.4: Quality gate — full verification
- [ ] `uv run ruff check src/` — zero errors
- [ ] `uv run ruff format --check src/` — zero violations
- [ ] `uv run mypy src/mochi/` — zero errors
- [ ] `uv run pytest` — all tests pass, coverage ≥ 80%

## Phase 3: Phase Completion Verification

### Task 3.1: Conductor - User Manual Verification 'Phase 1: Sprite Loading & Idle Animation' (Protocol in workflow.md)
- [ ] Run automated test suite
- [ ] Present manual verification steps to user
- [ ] Await user confirmation
- [ ] Create checkpoint commit with git notes
- [ ] Mark phase complete in plan
