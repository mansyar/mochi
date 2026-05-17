# Specification: Track 1.2 — Sprite Loading & Idle Animation

## Overview
Replace the green test rectangle on the Canvas with a looping idle animation of the cat sprite. Implement a `SpriteSheet` loader that slices sprite PNGs into individual frame pixmaps, wire an animation timer into the Canvas paint loop, and render the idle sprite breathing cycle.

## Scope
This track covers:
1. Creating a `SpriteSheet` class in `src/mochi/ui/sprites.py` that loads and slices sprite PNG files
2. Updating `Canvas` to render the idle sprite instead of the green test rectangle
3. Adding a `QTimer`-based animation tick that advances frames
4. Looping the idle breathing animation at the configured tick rate

## Modules Affected
| Module | Change |
|--------|--------|
| `src/mochi/ui/sprites.py` | **New.** Sprite sheet loader: load PNG, slice into frame pixmaps, cache by animation key |
| `src/mochi/core/canvas.py` | **Modified.** Replace green rect paint with sprite rendering; add animation timer |
| *(no change to config.py)* | Frame count derived dynamically from loaded PNG — no new constant needed |

## Functional Requirements

### FR1: SpriteSheet Loader (`sprites.py`)
- `SpriteSheet` class loads a PNG file and slices it into individual frame `QPixmap` objects
- Cell size is defined by `SPRITE_CELL_WIDTH` × `SPRITE_CELL_HEIGHT` (64×64 px)
- Frame list is cached as `list[QPixmap]` per animation key
- **Animation key → filename convention:** keys are lowercase strings; the loader maps `load("idle")` to `IDLE.png` by searching case-insensitively. Multi-word keys use spaces: `load("attack 1")` → `ATTACK 1.png`
- Sprite files that are not multiples of 64px in width/height (e.g., `BOWL.png` at 16×16) are silently skipped — they are item sprites handled in later tracks
- The loader resolves sprite files using an `asset_path()` helper that works in development, PyInstaller (`_MEIPASS`), and Nuitka (`__compiled__`) modes
- **Frame count** is derived dynamically from the loaded PNG: `len(loaded_pixmaps)`. No separate config constant is needed
- Graceful handling: if a PNG fails to load, log a warning and return an empty list. If an animation key has not been loaded, `get_frames()` returns an empty list rather than raising `KeyError`

### FR2: Idle Sprite Rendering
- Canvas renders frame 0 of the idle animation at screen bottom-center (same position as the current green rectangle)
- The sprite is drawn centered in its cell area using `QPainter.drawPixmap()`
- Click-through and transparent overlay behavior remain unchanged

### FR3: Animation Timer
- A `QTimer` fires every `ANIMATION_TICK_MS` (100ms) to advance the frame index
- Frame index wraps to 0 when it exceeds the frame count (looping animation)
- Timer starts on Canvas construction and stops only on hide/shutdown
- Each tick calls `canvas.update()` to trigger `paintEvent`

### FR4: Configuration
- No new config constants needed — frame count is derived from the loaded PNG dimensions
- `ANIMATION_TICK_MS: int = 100` already exists in config.py and controls the timer interval

## Acceptance Criteria
- [ ] `SpriteSheet` loads IDLE.png and produces `QPixmap` frames matching the PNG's width ÷ `SPRITE_CELL_WIDTH` (640÷64 = 10 frames)
- [ ] Canvas renders frame 0 of the idle sprite at screen bottom-center (same position as the green rect)
- [ ] Animation cycles through all idle frames at 100ms intervals, looping continuously
- [ ] No visual flickering or artifacts during animation
- [ ] Green test rectangle is removed (no `QColor("#00FF00")` reference remains)
- [ ] `uv run pytest` — all existing tests pass (59 tests + new tests)
- [ ] `uv run ruff check src/` — zero lint errors
- [ ] `uv run mypy src/mochi/` — zero type errors

## Out of Scope
- Animations for other states (Walk, Sleep, Climb, etc.) — deferred to later tracks
- Sprite mirroring for left/right walking — deferred to Track 1.3
- HiDPI / SPRITE_SCALE logic — deferred
- Any interaction or FSM logic — still a static idle cat
