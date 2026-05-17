# Technical Design Document (TDD)

## Desktop Cat Pet — "Mochi"

**Version:** 1.0
**Last Updated:** 2026-05-17
**Status:** Phase 1, Track 1.1 Complete — Active Development

---

## 1. System Architecture & Technology Stack

The application is an asynchronous Python desktop overlay, designed for minimal resource consumption and cross-platform execution (Windows, macOS, Linux X11).

| Component | Technology | Purpose |
|---|---|---|
| **Core UI Engine** | PySide6-Essentials (Qt 6 for Python) | Frameless transparent overlay window, sprite rendering, animation timer, system tray. Essentials variant excludes unused modules (WebEngine, Multimedia) to reduce binary size by ~100 MB |
| **Window Polling** | PyWinCtl | Cross-platform abstraction to query OS window positions, sizes, and states |
| **Monitor Geometry** | PyMonCtl | Cross-platform monitor geometry queries for fullscreen detection and future multi-monitor support (same author as PyWinCtl) |
| **Global Input** | Platform-native APIs via `ctypes` | OS-native global hotkey registration: Win32 `RegisterHotKey`, macOS `RegisterEventHotKey`, X11 `XGrabKey`. No global keyboard hook — only registered hotkeys are intercepted. Zero external dependencies |
| **Packaging (Dev)** | PyInstaller | Fast iteration builds during development |
| **Packaging (Release)** | Nuitka | Compiles Python to C for smaller binaries (30-50 MB vs 50-80 MB), faster startup, and 10-30% better runtime performance |
| **Config/State** | JSON (stdlib) | Lightweight persistence with no external dependencies |

> **Why not pynput?** pynput installs a global keyboard hook that intercepts ALL keystrokes — unnecessary when we only need 2 hotkeys. This triggers antivirus warnings on Windows, requires full Accessibility permissions on macOS, and creates thread-safety hazards with Qt. Platform-native `RegisterHotKey` / `RegisterEventHotKey` / `XGrabKey` avoids all three issues with zero additional dependencies.

### 1.1 Dependency Versions

```toml
[project]
name = "mochi"
version = "1.0.0"
requires-python = ">=3.11"

[project.dependencies]
PySide6-Essentials = ">=6.7,<7.0"
pywinctl = ">=0.4,<1.0"
pymonctl = ">=0.4,<1.0"
# No pynput — global hotkeys use platform-native APIs via ctypes (zero dependency)

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-qt>=4.4",
    "pytest-cov>=6.0",
    "pytest-xdist>=3.5",
    "mypy>=1.13",
    "pyinstaller>=6.0",
]
release = [
    "nuitka>=2.0",
]

# --- Ruff (linter + formatter, replaces flake8 + black + isort) ---
[tool.ruff]
target-version = "py311"
line-length = 100
src = ["src"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort (import sorting)
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # bugbear (common pitfalls)
    "SIM",  # simplify
    "RUF",  # ruff-specific rules
]

[tool.ruff.lint.isort]
known-first-party = ["mochi"]

# --- pytest ---
[tool.pytest.ini_options]
testpaths = ["tests"]
qt_api = "pyside6"
addopts = "--cov=src/mochi --cov-report=term-missing -q"

# --- mypy (type checker) ---
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[[tool.mypy.overrides]]
module = ["pywinctl.*", "pymonctl.*"]
ignore_missing_imports = true

# --- coverage ---
[tool.coverage.run]
source = ["src/mochi"]
omit = ["src/mochi/__main__.py"]
```

### 1.2 Dev Tooling

| Tool | Role | Replaces |
|---|---|---|
| **uv** | Package manager, virtualenv, Python version management | pip + venv + pyenv + pip-tools |
| **Ruff** | Linter + formatter + import sorter (Rust, 10-100x faster) | flake8 + black + isort |
| **mypy** | Static type checker (strict mode) | — |
| **pytest** | Test runner with Qt and coverage plugins | unittest |

> **Why uv?** Written in Rust, `uv` is a single binary that replaces `pip`, `venv`, `pyenv`, and `pip-tools`. It resolves and installs dependencies 10-100x faster, produces a deterministic `uv.lock` lockfile, and manages Python versions directly — no separate pyenv/pyenv-win install needed.

---

## 2. Project Structure

```
mochi/
├── docs/
│   ├── PRD.md
│   └── TDD.md
├── src/
│   └── mochi/
│       ├── __init__.py
│       ├── main.py                # Entry point, QApplication bootstrap
│       ├── config.py              # All tunable constants & defaults
│       ├── models/
│       │   ├── __init__.py
│       │   ├── pet_state.py       # Tamagotchi metrics, JSON serialization
│       │   └── fsm.py            # Finite State Machine engine
│       ├── core/
│       │   ├── __init__.py
│       │   ├── canvas.py          # Main transparent overlay window
│       │   ├── physics.py         # Gravity, collision detection, movement
│       │   ├── environment.py     # PyWinCtl polling, window geometry cache
│       │   └── input_bridge.py    # Platform-native global hotkey → Qt signal bridge
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── toolbox.py         # Floating inventory menu widget
│       │   ├── tray_icon.py       # System tray icon & context menu
│       │   ├── onboarding.py      # First-run tooltip overlay
│       │   └── sprites.py         # Sprite sheet loader & animation cache
│       └── utils/
│           ├── __init__.py
│           ├── logger.py          # Structured logging setup
│           └── platform.py        # OS detection & platform-specific shims
├── assets/
│   └── sprites/
│       └── cat_sheet.png          # Master sprite sheet
├── tests/
│   ├── test_fsm.py
│   ├── test_physics.py
│   └── test_pet_state.py
├── pyproject.toml
└── README.md
```

### Module Responsibility Map

| Module | Responsibility | Depends On |
|---|---|---|
| `main.py` | Bootstrap QApplication, wire all components, start event loop | All modules |
| `config.py` | Expose all tunable constants as module-level variables | None |
| `fsm.py` | State transitions, timer management, behavior decisions | `config`, `pet_state` |
| `pet_state.py` | Metric CRUD, offline decay calculation, JSON read/write | `config` |
| `canvas.py` | Frameless overlay window, paint loop, sprite rendering | `sprites`, `fsm`, `physics` |
| `physics.py` | Gravity, velocity, collision detection against surfaces | `config`, `environment` |
| `environment.py` | PyWinCtl polling thread, PyMonCtl monitor geometry, window rect cache, fullscreen detection | `config` |
| `input_bridge.py` | Platform-native hotkey registration → Qt signal emission | `platform` (for OS detection) |
| `toolbox.py` | Inventory UI widget, item deployment | `pet_state`, `config` |
| `tray_icon.py` | System tray icon, context menu actions | `canvas`, `pet_state` |
| `sprites.py` | Sprite sheet slicing, QPixmap cache, animation frame indexing | `config` |
| `platform.py` | OS detection, platform-specific window flag workarounds, Alt-key state polling, data directory resolution, single-instance enforcement | None |

---

## 3. Thread Architecture

The application uses **2 threads** with strict communication boundaries.

Using platform-native hotkey registration eliminates the dedicated input thread — hotkey events are delivered directly to the Qt event loop via OS message queues (Win32 `WM_HOTKEY`, macOS Carbon events, X11 `KeyPress` events).

```
┌──────────────────────────────────────────────────────────┐
│                  MAIN THREAD (Qt Event Loop)             │
│                                                          │
│  QApplication.exec()                                     │
│  ├── Canvas (paintEvent, sprite rendering)               │
│  ├── Animation Timer (QTimer, 100ms tick)                │
│  ├── FSM (state transitions, evaluated per tick)         │
│  ├── Physics (position updates, evaluated per tick)      │
│  ├── InputBridge (platform-native hotkey listener)       │
│  │     • Hotkeys registered via OS API at startup        │
│  │     • OS delivers hotkey events to Qt message loop    │
│  │     • Emits: toolbox_requested, boss_key_pressed      │
│  ├── Toolbox Widget                                      │
│  ├── Tray Icon                                           │
│  └── Onboarding Tooltip                                  │
│                                                          │
│  RECEIVES signals from background thread:                │
│  • platforms_updated(list[Surface]) → update physics     │
│  • fullscreen_changed(bool) → auto-hide/show             │
└──────────────────────────────────────────────────────────┘
         ▲
         │ Signal
         │
┌────────┴────────────────────────────┐
│ THREAD 2: Environment Poller        │
│                                      │
│ QThread + QTimer (300ms)             │
│ PyWinCtl.getAllWindows()             │
│ PyMonCtl — monitor geometry queries  │
│                                      │
│ Builds list[Surface] of             │
│ walkable/climbable surfaces          │
│                                      │
│ Emits:                               │
│ • platforms_updated(list[Surface])   │
│ • fullscreen_changed(bool)           │
└──────────────────────────────────────┘
```

### 3.1 Thread Safety Rules

1. **No Qt widget calls from background threads.** All UI mutations happen on the main thread via signal-slot connections.
2. **The input bridge** (`input_bridge.py`) uses platform-native hotkey APIs that deliver events directly to the Qt event loop — no background thread needed:

```python
import sys
import ctypes
from PySide6.QtCore import QObject, Signal, QAbstractNativeEventFilter
from PySide6.QtWidgets import QApplication


class InputBridge(QObject):
    """Platform-native global hotkey registration.

    Uses OS APIs to register only the specific hotkeys we need.
    No global keyboard hook, no background thread, no extra dependencies.
    Hotkey events are delivered via the Qt event loop's native message pump.
    """

    toolbox_requested = Signal()
    boss_key_pressed = Signal()

    # Hotkey IDs (arbitrary unique integers)
    _HOTKEY_TOOLBOX = 1
    _HOTKEY_BOSS = 2

    def register(self) -> bool:
        """Register global hotkeys using the current platform's native API."""
        if sys.platform == "win32":
            return self._register_win32()
        elif sys.platform == "darwin":
            return self._register_macos()
        else:
            return self._register_x11()

    def unregister(self) -> None:
        """Unregister all global hotkeys on shutdown."""
        if sys.platform == "win32":
            self._unregister_win32()
        elif sys.platform == "darwin":
            self._unregister_macos()
        else:
            self._unregister_x11()

    # --- Windows: RegisterHotKey + WM_HOTKEY via nativeEventFilter ---

    def _register_win32(self) -> bool:
        """Use Win32 RegisterHotKey. Delivers WM_HOTKEY (0x0312) to the
        application message queue — processed by Qt's event loop."""
        user32 = ctypes.windll.user32
        MOD_CTRL_SHIFT = 0x0002 | 0x0004  # MOD_CONTROL | MOD_SHIFT
        # Ctrl+Shift+P (0x50) for toolbox
        ok1 = user32.RegisterHotKey(None, self._HOTKEY_TOOLBOX, MOD_CTRL_SHIFT, 0x50)
        # Ctrl+Shift+H (0x48) for boss key
        ok2 = user32.RegisterHotKey(None, self._HOTKEY_BOSS, MOD_CTRL_SHIFT, 0x48)
        # Install native event filter to catch WM_HOTKEY messages
        self._win_filter = self._WinHotkeyFilter(self)
        QApplication.instance().installNativeEventFilter(self._win_filter)
        return bool(ok1 and ok2)

    def _unregister_win32(self) -> None:
        user32 = ctypes.windll.user32
        user32.UnregisterHotKey(None, self._HOTKEY_TOOLBOX)
        user32.UnregisterHotKey(None, self._HOTKEY_BOSS)

    class _WinHotkeyFilter(QAbstractNativeEventFilter):
        WM_HOTKEY = 0x0312

        def __init__(self, bridge: "InputBridge"):
            super().__init__()
            self._bridge = bridge

        def nativeEventFilter(self, event_type, message):
            # On Windows, message is a MSG struct pointer
            if event_type == b"windows_generic_MSG":
                import ctypes.wintypes
                msg = ctypes.wintypes.MSG.from_address(int(message))
                if msg.message == self.WM_HOTKEY:
                    if msg.wParam == self._bridge._HOTKEY_TOOLBOX:
                        self._bridge.toolbox_requested.emit()
                        return True, 0
                    elif msg.wParam == self._bridge._HOTKEY_BOSS:
                        self._bridge.boss_key_pressed.emit()
                        return True, 0
            return False, 0

    # --- macOS / Linux stubs (same pattern, different API) ---

    def _register_macos(self) -> bool:
        """Use Carbon RegisterEventHotKey via pyobjc (already a PyWinCtl dep)."""
        # Implementation uses Carbon.CarbonEvt.RegisterEventHotKey
        # Hotkey events delivered via Carbon event loop → Qt integration
        ...

    def _unregister_macos(self) -> None: ...

    def _register_x11(self) -> bool:
        """Use Xlib XGrabKey via python-xlib (already a PyWinCtl dep)."""
        # Implementation uses Xlib.display.Display().grab_key()
        # Key events delivered via X11 event queue → Qt integration
        ...

    def _unregister_x11(self) -> None: ...
```

> **Key advantage:** On Windows, `RegisterHotKey` delivers `WM_HOTKEY` messages through the standard Win32 message queue, which Qt's event loop already processes. This means hotkey handling runs entirely on the main thread — no signal bridge, no thread-safety concerns, no background thread.

3. **The environment poller** runs on a `QThread` and emits a signal with the updated surface list. The main thread copies the list; the poller never mutates shared state directly.

---

## 4. Data Architecture & Persistence

### 4.1 State File: `pet_state.json`

Located in the platform-appropriate application data directory:

| Platform | Path |
|---|---|
| **Windows** | `%APPDATA%\Mochi\pet_state.json` |
| **macOS** | `~/Library/Application Support/Mochi/pet_state.json` |
| **Linux** | `~/.local/share/mochi/pet_state.json` (XDG spec) |

The `platform.py` module provides a `get_data_dir() -> Path` function that resolves the correct path per OS. The directory is created on first launch if it does not exist.

State is persisted with **write debouncing** — changes are buffered in memory and flushed to disk at most once every 5 seconds via a `QTimer`. An immediate flush also occurs on `QApplication.aboutToQuit` to ensure no data loss on shutdown.

```json
{
  "version": 1,
  "profile": {
    "name": "Mochi"
  },
  "metrics": {
    "hunger": 75,
    "boredom": 60,
    "affection": 85
  },
  "position": {
    "x": 540,
    "y": 320
  },
  "fsm_state": "idle",
  "last_exit_epoch": 1747440000,
  "first_run_completed": true
}
```

### 4.2 Offline Metric Decay

On startup, the engine calculates elapsed time:

```
Δt = t_current − t_last_saved  (in seconds)
hours_elapsed = min(Δt / 3600, MAX_OFFLINE_DECAY_HOURS)  # Capped at 48h
```

Decay is applied per metric using rates from `config.py`:

| Metric | Decay Per Hour | Formula |
|---|---|---|
| Hunger | −5 | `max(0, hunger - 5 × hours_elapsed)` |
| Boredom | −8 | `max(0, boredom - 8 × hours_elapsed)` |
| Affection | −2 | `max(0, affection - 2 × hours_elapsed)` |

### 4.3 Corruption Recovery

If `pet_state.json` fails to parse (malformed JSON, missing keys, wrong types):
1. Log a warning with the parse error.
2. Rename the corrupt file to `pet_state.json.bak`.
3. Initialize with default values (all metrics at 50, position at screen bottom center, `first_run_completed = false`).

---

## 5. Core Subsystem Designs

### 5.1 Canvas Window (`canvas.py`)

The rendering container is a borderless, always-on-top, transparent Qt window spanning the full screen.

| Property | Value |
|---|---|
| **Window Flags** | `FramelessWindowHint \| WindowStaysOnTopHint \| Tool` |
| **Widget Attribute** | `WA_TranslucentBackground = True` |
| **Geometry** | Full primary screen dimensions |
| **Click-Through** | Enabled by default (see §5.2) |

The canvas runs a `QTimer` with an **adaptive tick rate** based on the current FSM state:

| State | Tick Interval | Rationale |
|---|---|---|
| Walk, Climb, Fall, Grabbed, Wall Slide | 100ms (10 FPS) | Active motion requires smooth animation |
| Idle (Loaf) | 250ms (4 FPS) | Subtle breathing animation, low CPU |
| Sleep | 500ms (2 FPS) | Minimal breathing animation, lowest CPU |
| Boss-Key hidden | Timer stopped | Zero CPU. Timer resumes on restore |

Each tick:
1. Ticks the FSM (evaluate transitions).
2. Ticks the physics engine (apply gravity/velocity, detect collisions).
3. Advances the animation frame index.
4. Calls `update()` to trigger `paintEvent()`.

The timer interval is updated whenever the FSM transitions to a new state.

`paintEvent()` renders:
- The cat sprite at its current position.
- Any deployed items (food dish, yarn ball, cardboard box).
- The onboarding tooltip (if first run, first 8 seconds).

### 5.2 Click-Through & Interaction Toggle

**Default mode:** `WindowTransparentForInput` is active. All mouse events pass through to underlying windows.

**Interaction mode:** When the user holds `Alt`, click-through is disabled so the user can click and drag the cat.

**Platform-specific implementation to avoid flicker:**

| Platform | Strategy |
|---|---|
| **Windows** | Use `ctypes.windll.user32` to toggle `WS_EX_TRANSPARENT` via `SetWindowLongW` / `GetWindowLongW` on the native HWND. No window re-creation needed, no `pywin32` dependency |
| **macOS** | Use `NSWindow.setIgnoresMouseEvents_()` via `objc` bridge. Native, no flicker |
| **Linux X11** | Use `Xlib` input shape mask via `XShapeCombineRectangles`. Toggle between empty mask (click-through) and full mask (interactive) |

The `platform.py` module provides a unified interface:

```python
def set_click_through(window: QWidget, enabled: bool) -> None:
    """Platform-specific click-through toggle. No window re-creation."""
    ...
```

**Alt-key detection:** Since the overlay is click-through, it receives no input events. Alt-key state is polled using **platform-native APIs** on each animation tick, regardless of window focus:

```python
# In platform.py
def is_alt_held() -> bool:
    """Check if Alt key is currently held, regardless of window focus."""
    if sys.platform == "win32":
        # GetAsyncKeyState returns key state independent of focus
        return bool(ctypes.windll.user32.GetAsyncKeyState(0x12) & 0x8000)  # VK_MENU
    elif sys.platform == "darwin":
        # CGEventSourceFlagsState reads global modifier state
        import Quartz
        flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateCombinedSessionState)
        return bool(flags & Quartz.kCGEventFlagMaskAlternate)
    else:
        # X11: XQueryKeymap via python-xlib
        ...
```

When Alt is detected as held, `set_click_through(window, False)` is called. When released, it reverts to `True`.

**Toolbox mode:** When the toolbox hotkey is pressed, click-through is disabled to allow the user to interact with toolbox buttons. Click-through is re-enabled when the toolbox is dismissed (click outside, Escape, or hotkey toggle). The dismiss-click is consumed by the overlay and not forwarded to underlying windows.

### 5.3 Animation Engine (`sprites.py`)

The sprite sheet uses **80×64 pixel bounding boxes** containing **32×32 pixel cat frames** (centered, with padding for animation overshoot like tails and ears).

**Boot-time loading:**
1. Load the master sprite sheet PNG into a single `QPixmap`.
2. Slice individual frames using `QPixmap.copy(QRect(...))`.
3. Cache all frames into a `dict[str, list[QPixmap]]` keyed by state name.

```python
SPRITE_MAP: dict[str, list[QPixmap]] = {
    "idle":       [...],  # 4 frames (breathing cycle)
    "walk_right": [...],  # 6 frames
    "walk_left":  [...],  # 6 frames (mirrored)
    "fall":       [...],  # 2 frames
    "climb":      [...],  # 4 frames
    "wall_slide": [...],  # 2 frames
    "sleep":      [...],  # 4 frames (breathing + zzz)
    "grabbed":    [...],  # 2 frames
    "eat":        [...],  # 4 frames
    "play":       [...],  # 4 frames
    "pet":        [...],  # 3 frames
}
```

**Frame advancement:** Each animation timer tick increments the frame index. When the index exceeds the frame count for the current state, it wraps to 0 (looping animation).

### 5.4 Physics & Collision (`physics.py`)

The physics engine operates in **logical pixel coordinates** and runs every 100ms tick.

#### Gravity Model

```python
# During Fall state, each tick:
dt = 0.1  # 100ms in seconds
velocity_y += GRAVITY * dt          # Accelerate
velocity_y = min(velocity_y, TERMINAL_VELOCITY)  # Cap
position_y += velocity_y * dt       # Move
```

#### Collision Detection

Runs after every position update:

1. **Ground check:** If `pet_bottom >= surface_top` for any surface in the platform list, snap `pet_bottom = surface_top`, zero vertical velocity, transition to Idle.
2. **Lateral check:** If `pet_right >= surface_left` or `pet_left <= surface_right` for any vertical surface, transition to Climb.
3. **Screen bounds:** Clamp position within screen boundaries. Screen bottom = ground of last resort.

#### Surface Data Structure

```python
@dataclass
class Surface:
    rect: QRect            # Bounding rectangle
    surface_type: str      # "window_top", "screen_bottom", "screen_left", "screen_right", "window_left", "window_right"
    window_id: int | None  # OS window handle (for tracking moves/closes)
```

### 5.5 Environment Poller (`environment.py`)

Runs on a dedicated `QThread` with a 300ms `QTimer`.

**Each tick:**
1. Call `pywinctl.getAllWindows()`.
2. Filter: exclude minimized, exclude the Mochi overlay itself, exclude windows with empty titles.
3. Detect fullscreen: use `pymonctl` to get the primary monitor geometry, then check if any window's geometry matches the full screen dimensions. Emit `fullscreen_changed(True)` when detected.
4. Build a `list[Surface]` from window rects and screen edges.
5. Emit `platforms_updated(list[Surface])`.

**Error handling:** If `getAllWindows()` throws (permission denied, OS error), log the error and emit the previously cached surface list. Do not crash.

**Performance note:** On systems with 50+ windows, the poller filters by visibility and excludes known non-interactive windows (e.g., Desktop, DWM overlays on Windows). The surface list is kept lean.

---

## 6. Configuration Constants (`config.py`)

All tunable values live in a single module. No magic numbers in business logic.

```python
# Physics
GRAVITY: float = 980.0          # px/s²
TERMINAL_VELOCITY: float = 600.0  # px/s
WALK_SPEED: float = 60.0        # px/s
CLIMB_SPEED: float = 40.0       # px/s
WALL_SLIDE_SPEED: float = 20.0  # px/s

# FSM Timers (seconds) — (min, max) for random uniform
IDLE_TO_WALK_TIMER: tuple[float, float] = (2.0, 5.0)
IDLE_TO_SLEEP_TIMER: tuple[float, float] = (15.0, 30.0)
WALK_TO_IDLE_TIMER: tuple[float, float] = (3.0, 8.0)
CLIMB_TO_WALLSLIDE_TIMER: tuple[float, float] = (1.0, 3.0)
CLIMB_TIMEOUT: tuple[float, float] = (10.0, 15.0)
WALLSLIDE_TO_CLIMB_TIMER: tuple[float, float] = (0.5, 2.0)
SLEEP_DURATION_TIMER: tuple[float, float] = (8.0, 15.0)

# Metrics
HUNGER_DECAY_PER_HOUR: float = 8.0
BOREDOM_DECAY_PER_HOUR: float = 6.0
AFFECTION_DECAY_PER_HOUR: float = 4.0
LOW_HUNGER_SPEED_PENALTY: float = 0.5    # 50% speed reduction
BOREDOM_LOW_THRESHOLD: float = 30.0
AFFECTION_AVOIDANCE_THRESHOLD: float = 20.0
HAPPY_ZOOMIE_CHANCE: float = 0.05        # 5%
MAX_OFFLINE_DECAY_HOURS: float = 48.0    # Cap offline decay
STATE_WRITE_DEBOUNCE_S: float = 5.0      # Min interval between disk writes
ITEM_APPROACH_TIMEOUT_S: float = 10.0    # Cancel approach after this

# Rendering
ANIMATION_TICK_MS: int = 100             # 10 FPS
SPRITE_CELL_WIDTH: int = 64
SPRITE_CELL_HEIGHT: int = 64
SPRITE_SCALE: float = 1.0               # Base scale (HiDPI via 2× sprite sheet)

# Polling
WINDOW_POLL_INTERVAL_MS: int = 200

# Items
FOOD_COOLDOWN_S: float = 30.0
YARN_COOLDOWN_S: float = 20.0
PET_COOLDOWN_S: float = 10.0
BOX_COOLDOWN_S: float = 60.0
BOX_DURATION_S: float = 30.0

# Onboarding
ONBOARDING_DURATION_S: float = 8.0
```

---

## 7. Error Handling & Logging

### 7.1 Logging Strategy

Use Python's `logging` module with structured output.

```python
# logger.py
import logging
import sys
from pathlib import Path

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(debug: bool = False, log_path: str | None = None) -> None:
    """Configure the root logger with console and file handlers.

    Parameters
    ----------
    debug : bool, optional
        If True, set root logger to DEBUG level (default is INFO).
    log_path : str or None, optional
        Path to the log file. If None, defaults to ``mochi.log`` in the
        current working directory.
    """
    level = logging.DEBUG if debug else logging.INFO
    root = logging.getLogger()

    # Prevent duplicate handlers on repeated calls
    root.handlers.clear()
    root.setLevel(level)

    # Console handler (stdout)
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(console_handler)

    # File handler
    resolved_path = Path(log_path) if log_path else Path("mochi.log")
    file_handler = logging.FileHandler(resolved_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(file_handler)
```

Each module creates its own logger: `logger = logging.getLogger(__name__)`.

### 7.2 Error Handling by Component

| Component | Failure Mode | Recovery |
|---|---|---|
| `pet_state.py` | JSON parse error | Backup corrupt file, reset to defaults |
| `environment.py` | PyWinCtl exception | Log warning, use cached surface list |
| `input_bridge.py` | `RegisterHotKey` / `RegisterEventHotKey` / `XGrabKey` returns failure (hotkey already claimed by another app) | Log error with conflicting hotkey name, show tray notification suggesting the user close the conflicting app or remap hotkeys (post-MVP) |
| `canvas.py` | Sprite sheet missing | Log fatal, show error dialog, exit |
| `platform.py` | Click-through API unavailable (`ctypes` call fails) | Fall back to Qt `setWindowFlags` toggle (with flicker) |
| macOS | Accessibility permission denied (required for PyWinCtl window polling) | Show one-time dialog explaining the requirement with a button to open System Settings > Privacy > Accessibility |

---

## 8. Testing Strategy

### 8.1 Unit Tests (No GUI Required)

Run with `uv run pytest`. Coverage reported via `pytest-cov`.

| Module | Test Focus |
|---|---|
| `test_config.py` | All config constants are typed correctly, positive values, valid ranges |
| `test_logger.py` | Logging setup creates correct handlers, respects debug flag, file/console output |
| `test_platform.py` | OS detection, data directory resolution (Windows/macOS/Linux), Alt-key stub, click-through toggle with platform mocking |
| `test_main.py` | QApplication bootstrap, org/app name, logging initialization |
| `test_canvas.py` | Canvas is QWidget subclass, correct window flags, translucent background, geometry matches primary screen, paintEvent doesn't raise |
| `test_fsm.py` | (Planned) All state transitions fire correctly given triggers. Timer boundaries work |
| `test_physics.py` | (Planned) Gravity acceleration, terminal velocity capping, collision detection against mock surfaces |
| `test_pet_state.py` | (Planned) Metric decay calculation, JSON round-trip, corruption recovery, boundary clamping (0–100) |

### 8.2 Integration Tests (pytest-qt)

Use `pytest-qt`'s `qtbot` fixture for Qt widget and signal testing. Set `qt_api = "pyside6"` in `pyproject.toml`.

```python
# Example: test that Canvas widget has correct properties
def test_window_flags_set(qtbot):
    canvas = Canvas()
    qtbot.addWidget(canvas)
    flags = canvas.windowFlags()
    assert flags & Qt.FramelessWindowHint
```

- **Canvas widget (implemented):** `test_canvas.py` — Window flags, translucent background, geometry, paint event.
- **Main integration (implemented):** `test_main.py` — Canvas instantiation, `.show()` call, dimension logging, timer-based click-through setup.
- **Click-through (implemented):** `test_platform.py` — Windows enable/disable via win32 helper, macOS/Linux no-op paths.
- **Sprite loading (planned):** Verify all expected animation keys exist after sheet slicing.
- **Hotkey bridge (planned):** Verify `InputBridge.register()` succeeds on each platform.
- **Signal flow (planned):** Verify `EnvironmentPoller` → `platforms_updated` signal.

### 8.3 Manual QA Checklist

- [ ] Cat walks on top of VS Code, browser, file explorer windows
- [ ] Moving a window out from under the cat causes a fall
- [ ] Cat lands on the next window below, or on screen bottom
- [ ] Climbing a screen edge transitions to walking at the top
- [ ] Toolbox opens at cursor, items work, cooldowns enforce
- [ ] Boss Key hides everything, second press restores
- [ ] Quit from tray saves state; relaunch restores position
- [ ] After 2+ hours offline, metrics have decayed on next launch
- [ ] Alt+click drag picks up and drops the cat
- [ ] Fullscreen app (e.g., a game) auto-hides the cat

---

## 9. Build & Distribution

### 9.1 Development Setup

```bash
# Install uv (one-time, if not already installed)
# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone <repo-url> && cd mochi
uv sync --extra dev          # Creates .venv, installs all deps + dev tools

# Run in development
uv run python -m mochi
# or
uv run python src/mochi/main.py

# Linting & formatting
uv run ruff check src/        # Lint
uv run ruff format src/       # Format
uv run ruff check --fix src/  # Lint + auto-fix

# Type checking
uv run mypy src/mochi/

# Testing
uv run pytest                 # Run tests with coverage
uv run pytest -n auto         # Run tests in parallel (pytest-xdist)
```

### 9.2 Development Builds (PyInstaller)

Used during development for fast iteration. Not optimized for size or performance.

```bash
pyinstaller --onefile --windowed \
  --add-data "assets/sprites:assets/sprites" \
  --exclude-module PySide6.QtWebEngine \
  --exclude-module PySide6.QtMultimedia \
  --exclude-module PySide6.QtNetwork \
  --name Mochi \
  src/mochi/main.py
```

| Flag | Purpose |
|---|---|
| `--onefile` | Single executable distribution |
| `--windowed` | No console window on launch (Windows/macOS) |
| `--add-data` | Bundle sprite assets into the binary |
| `--exclude-module` | Strip unused Qt modules to reduce size |

### 9.3 Release Builds (Nuitka)

Used for production distribution. Compiles Python to C for smaller binaries, faster startup, and better runtime performance.

```bash
python -m nuitka \
  --onefile \
  --windows-disable-console \
  --include-data-dir=assets/sprites=assets/sprites \
  --enable-plugin=pyside6 \
  --output-filename=Mochi \
  src/mochi/main.py
```

| Advantage | Detail |
|---|---|
| **Binary size** | 30-50% smaller than PyInstaller (compiled C, no bundled interpreter) |
| **Startup time** | Faster cold start — no temp extraction needed (unlike PyInstaller `--onefile`) |
| **Runtime performance** | 10-30% faster — Python bytecode compiled to native machine code |
| **Code protection** | Source code not easily recoverable (compiled binary vs. bundled `.pyc`) |

> **Trade-off:** Nuitka builds are 10-100x slower than PyInstaller. Use PyInstaller during development, Nuitka for release.

### 9.4 Asset Path Resolution

Works for both dev, PyInstaller, and Nuitka builds:

```python
import sys
from pathlib import Path

def asset_path(relative: str) -> Path:
    """Resolve asset path for dev, PyInstaller, and Nuitka builds."""
    # PyInstaller extracts to _MEIPASS
    if getattr(sys, '_MEIPASS', None):
        return Path(sys._MEIPASS) / relative
    # Nuitka uses __compiled__ marker; assets are alongside the binary
    if "__compiled__" in dir():
        return Path(sys.argv[0]).parent / relative
    # Development: relative to source tree
    return Path(__file__).parent.parent.parent / relative
```

### 9.5 Target Binaries

| Platform | Output | Size Target (Nuitka) | Size Target (PyInstaller) |
|---|---|---|---|
| Windows x64 | `Mochi.exe` | < 25 MB | < 45 MB |
| macOS ARM64 | `Mochi.app` (bundled) | < 30 MB | < 50 MB |
| Linux x64 | `Mochi` (ELF binary) | < 25 MB | < 45 MB |