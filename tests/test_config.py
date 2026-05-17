"""Tests for mochi.config constants."""

from mochi import config


class TestPhysicsConstants:
    """All physics constants must be positive floats."""

    def test_gravity_is_positive_float(self) -> None:
        assert isinstance(config.GRAVITY, float)
        assert config.GRAVITY > 0

    def test_terminal_velocity_is_positive_float(self) -> None:
        assert isinstance(config.TERMINAL_VELOCITY, float)
        assert config.TERMINAL_VELOCITY > 0

    def test_walk_speed_is_positive_float(self) -> None:
        assert isinstance(config.WALK_SPEED, float)
        assert config.WALK_SPEED > 0

    def test_climb_speed_is_positive_float(self) -> None:
        assert isinstance(config.CLIMB_SPEED, float)
        assert config.CLIMB_SPEED > 0

    def test_wall_slide_speed_is_positive_float(self) -> None:
        assert isinstance(config.WALL_SLIDE_SPEED, float)
        assert config.WALL_SLIDE_SPEED > 0


class TestFSMTimerConstants:
    """All FSM timer tuples must be (min, max) with min < max."""

    def test_idle_to_walk_timer(self) -> None:
        lo, hi = config.IDLE_TO_WALK_TIMER
        assert isinstance(lo, float) and isinstance(hi, float)
        assert 0 <= lo < hi

    def test_idle_to_sleep_timer(self) -> None:
        lo, hi = config.IDLE_TO_SLEEP_TIMER
        assert isinstance(lo, float) and isinstance(hi, float)
        assert 0 <= lo < hi

    def test_walk_to_idle_timer(self) -> None:
        lo, hi = config.WALK_TO_IDLE_TIMER
        assert isinstance(lo, float) and isinstance(hi, float)
        assert 0 <= lo < hi

    def test_climb_to_wallslide_timer(self) -> None:
        lo, hi = config.CLIMB_TO_WALLSLIDE_TIMER
        assert isinstance(lo, float) and isinstance(hi, float)
        assert 0 <= lo < hi

    def test_climb_timeout(self) -> None:
        lo, hi = config.CLIMB_TIMEOUT
        assert isinstance(lo, float) and isinstance(hi, float)
        assert 0 <= lo < hi

    def test_wallslide_to_climb_timer(self) -> None:
        lo, hi = config.WALLSLIDE_TO_CLIMB_TIMER
        assert isinstance(lo, float) and isinstance(hi, float)
        assert 0 <= lo < hi

    def test_sleep_duration_timer(self) -> None:
        lo, hi = config.SLEEP_DURATION_TIMER
        assert isinstance(lo, float) and isinstance(hi, float)
        assert 0 <= lo < hi


class TestMetricConstants:
    """All metric constants must be within valid ranges."""

    def test_hunger_decay_per_hour(self) -> None:
        assert 0 < config.HUNGER_DECAY_PER_HOUR < 100

    def test_boredom_decay_per_hour(self) -> None:
        assert 0 < config.BOREDOM_DECAY_PER_HOUR < 100

    def test_affection_decay_per_hour(self) -> None:
        assert 0 < config.AFFECTION_DECAY_PER_HOUR < 100

    def test_low_hunger_speed_penalty(self) -> None:
        assert 0 < config.LOW_HUNGER_SPEED_PENALTY < 1

    def test_boredom_low_threshold(self) -> None:
        assert 0 < config.BOREDOM_LOW_THRESHOLD < 100

    def test_affection_avoidance_threshold(self) -> None:
        assert 0 < config.AFFECTION_AVOIDANCE_THRESHOLD < 100

    def test_happy_zoomie_chance(self) -> None:
        assert 0 < config.HAPPY_ZOOMIE_CHANCE < 1

    def test_max_offline_decay_hours(self) -> None:
        assert config.MAX_OFFLINE_DECAY_HOURS > 0

    def test_state_write_debounce_s(self) -> None:
        assert config.STATE_WRITE_DEBOUNCE_S > 0

    def test_item_approach_timeout_s(self) -> None:
        assert config.ITEM_APPROACH_TIMEOUT_S > 0


class TestAnimationRenderConstants:
    """All animation and render constants must be positive integers."""

    def test_animation_tick_ms(self) -> None:
        assert isinstance(config.ANIMATION_TICK_MS, int)
        assert config.ANIMATION_TICK_MS > 0

    def test_sprite_cell_width(self) -> None:
        assert isinstance(config.SPRITE_CELL_WIDTH, int)
        assert config.SPRITE_CELL_WIDTH > 0

    def test_sprite_cell_height(self) -> None:
        assert isinstance(config.SPRITE_CELL_HEIGHT, int)
        assert config.SPRITE_CELL_HEIGHT > 0

    def test_sprite_scale(self) -> None:
        assert config.SPRITE_SCALE > 0
