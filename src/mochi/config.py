"""Tunable constants for Mochi.

All physics, FSM timing, pet metrics, rendering, polling, and UX defaults
live here so they can be tuned without touching logic code.
"""

# ── Physics ──────────────────────────────────────────────────────────────
GRAVITY: float = 980.0  # px/s²  — standard desktop gravity
TERMINAL_VELOCITY: float = 600.0  # px/s  — max fall speed
WALK_SPEED: float = 60.0  # px/s  — horizontal walk speed
CLIMB_SPEED: float = 40.0  # px/s  — vertical climb speed
WALL_SLIDE_SPEED: float = 20.0  # px/s  — slow descent on walls

# ── FSM Timer Ranges (min, max in seconds) ──────────────────────────────
IDLE_TO_WALK_TIMER: tuple[float, float] = (2.0, 5.0)
IDLE_TO_SLEEP_TIMER: tuple[float, float] = (15.0, 30.0)
WALK_TO_IDLE_TIMER: tuple[float, float] = (3.0, 8.0)
CLIMB_TO_WALLSLIDE_TIMER: tuple[float, float] = (1.0, 3.0)
CLIMB_TIMEOUT: tuple[float, float] = (10.0, 15.0)
WALLSLIDE_TO_CLIMB_TIMER: tuple[float, float] = (0.5, 2.0)
SLEEP_DURATION_TIMER: tuple[float, float] = (8.0, 15.0)

# ── Pet Metrics ──────────────────────────────────────────────────────────
HUNGER_DECAY_PER_HOUR: float = 8.0
BOREDOM_DECAY_PER_HOUR: float = 6.0
AFFECTION_DECAY_PER_HOUR: float = 4.0
LOW_HUNGER_SPEED_PENALTY: float = 0.5  # speed multiplier when hungry
BOREDOM_LOW_THRESHOLD: float = 30.0  # below this → bored behaviour
AFFECTION_AVOIDANCE_THRESHOLD: float = 20.0  # below this → avoids user
HAPPY_ZOOMIE_CHANCE: float = 0.05  # probability of zoomie per step
MAX_OFFLINE_DECAY_HOURS: float = 48.0
STATE_WRITE_DEBOUNCE_S: float = 2.0
ITEM_APPROACH_TIMEOUT_S: float = 10.0

# ── Animation / Rendering ───────────────────────────────────────────────
ANIMATION_TICK_MS: int = 100  # ms per animation frame tick
SPRITE_CELL_WIDTH: int = 64  # px per sprite cell
SPRITE_CELL_HEIGHT: int = 64  # px per sprite cell
SPRITE_SCALE: float = 1.0  # base scale factor

# ── Window Polling ──────────────────────────────────────────────────────
WINDOW_POLL_INTERVAL_MS: int = 200  # ms between environment scans

# ── Item Cooldowns ──────────────────────────────────────────────────────
FOOD_COOLDOWN_S: float = 30.0
YARN_COOLDOWN_S: float = 20.0
PET_COOLDOWN_S: float = 10.0
BOX_COOLDOWN_S: float = 60.0
BOX_DURATION_S: float = 30.0

# ── Onboarding ──────────────────────────────────────────────────────────
ONBOARDING_DURATION_S: float = 8.0
