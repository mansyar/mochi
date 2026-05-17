# Implementation Plan: Track 1.2 — Sprite Loading & Idle Animation

## Phase 1: Sprite Sheet Loading

### Task 1.1: Write tests for SpriteSheet loader (Red Phase)
- [x] Create `tests/test_sprites.py`
- [x] Test: `SpriteSheet` class exists and is instantiable
- [x] Test: `load("idle")` loads IDLE.png and returns `list[QPixmap]` with 10 frames (640÷64)
- [x] Test: each frame pixmap has size 64×64
- [x] Test: loading a non-existent file logs a warning and returns empty list
- [x] Test: `get_frames("idle")` returns the cached frame list
- [x] Test: `get_frames("nonexistent")` returns empty list (consistent with `load()`)
- [x] Test: BOWL.png (16×16) is silently skipped by the loader
- [x] Run tests and confirm they fail (Red Phase)

### Task 1.2: Implement SpriteSheet class (Green Phase)
- [x] Create `src/mochi/ui/sprites.py`
- [x] Implement `asset_path(relative: str) -> Path` helper supporting dev, PyInstaller, and Nuitka modes
- [x] Implement `SpriteSheet.__init__(asset_dir: str)` — store reference to asset directory
- [x] Implement `load(animation_key: str) -> list[QPixmap]`:
    - [x] Map key to filename: lowercase key → case-insensitive search for matching `.png` (e.g., `"idle"` → `IDLE.png`, `"attack 1"` → `ATTACK 1.png`)
    - [x] Load PNG via `QPixmap(str(path))`
    - [x] Validate PNG dimensions are multiples of `SPRITE_CELL_WIDTH`/`SPRITE_CELL_HEIGHT`; skip non-conforming files (e.g., BOWL.png)
    - [x] Slice PNG into individual 64×64 frame pixmaps using `QPixmap.copy()`
    - [x] Cache result internally, return `list[QPixmap]`
    - [x] If PNG not found or fails to load: log warning, cache and return empty list
- [x] Implement `get_frames(animation_key: str) -> list[QPixmap]` — return cached frame list (empty list if not loaded)
- [x] Run tests and confirm they pass (Green Phase)

### Task 1.3: Quality gate — lint, format, type-check sprites module
- [x] `uv run ruff check src/mochi/ui/sprites.py` — zero errors
- [x] `uv run mypy src/mochi/ui/sprites.py` — zero errors
- [x] `uv run pytest tests/test_sprites.py` — all tests pass`[f58918c]`

## Phase 2: Idle Sprite Rendering & Animation

### Task 2.1: Write tests for Canvas sprite rendering and animation (Red Phase)
- [x] Create `tests/test_animation.py` for Canvas timer and frame advancement tests:
    - [x] Test: Canvas creates a `QTimer` for animation tick
    - [x] Test: Animation timer interval equals `ANIMATION_TICK_MS` (100ms)
    - [x] Test: Frame index advances by 1 on each tick, wraps to 0 after `len(idle_frames)`-1
    - [x] Test: `paintEvent` calls `painter.drawPixmap` with the correct current frame
    - [x] Test: Green rectangle is no longer drawn (no `QColor("#00FF00")` or `fillRect` with that color)
- [x] Update skipped `test_green_pixel_at_bottom_center`: update comment to indicate the test is obsolete (sprite replaces green rect); optionally remove or keep skipped
- [x] Run tests and confirm they fail (Red Phase)

### Task 2.2: Wire Canvas with SpriteSheet and animation timer (Green Phase)
- [x] In `Canvas.__init__()`:
    - [x] Instantiate `SpriteSheet` pointing to `assets/sprites/`
    - [x] Call `spritesheet.load("idle")` to cache idle frames
    - [x] Create `QTimer` set to `ANIMATION_TICK_MS` interval
    - [x] Connect timer timeout to slot that advances `_current_frame` and calls `update()`
    - [x] Start the timer
- [x] Add instance variables: `_spritesheet: SpriteSheet`, `_current_frame: int`, `_idle_frames: list[QPixmap]`
- [x] In `paintEvent()`:
    - [x] Replace green `fillRect` with `painter.drawPixmap()` using current idle frame
    - [x] Position: screen bottom-center (same X/Y formula as green rect)
- [x] Remove `QColor("#00FF00")` import/usage from `canvas.py` (no longer needed)
- [x] Remove `QColor` import if no longer used; remove `QRect` import if no longer used
- [x] Run tests and confirm they pass (Green Phase)

### Task 2.3: Quality gate — full verification
- [x] `uv run ruff check src/` — zero errors
- [x] `uv run ruff format --check src/` — zero violations
- [x] `uv run mypy src/mochi/` — zero errors
- [x] `uv run pytest` — all tests pass, coverage ≥ 80%`[76c73b6]`

## Phase 3: Phase Completion Verification [checkpoint: 0083bec]

### Task 3.1: Conductor - User Manual Verification 'Track 1.2: Sprite Loading & Idle Animation' (Protocol in workflow.md)
- [x] Run automated test suite
- [x] Present manual verification steps to user
- [x] Await user confirmation
- [x] Create checkpoint commit with git notes
- [x] Mark phase complete in plan
