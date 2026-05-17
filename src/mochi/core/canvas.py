"""Canvas — the transparent overlay rendering surface for Mochi.

Provides a fullscreen, frameless, always-on-top ``QWidget`` that serves
as the drawing surface for the cat sprite, FSM-driven state transitions,
and physics-based movement with environmental effects.
"""

from __future__ import annotations

import logging
import time

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from mochi import config
from mochi.core.environment import EnvironmentPoller, Surface
from mochi.core.fsm import FSM, PetState
from mochi.core.physics import Physics
from mochi.ui.sprites import SpriteSheet

logger = logging.getLogger("mochi.canvas")

#: Composite window flags for the overlay: frameless, always-on-top, tool.
_CANVAS_FLAGS = (
    Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
)

#: Animation tick intervals (ms) per FSM state.
_TICK_INTERVALS: dict[PetState, int] = {
    PetState.Idle: 250,
    PetState.Walk: 100,
    PetState.EdgePause: 250,
}

#: Sprite animation key lookup per FSM state.
_SPRITE_KEYS: dict[PetState, str] = {
    PetState.Idle: "idle",
    PetState.Walk: "walk",
    PetState.EdgePause: "walk",
}


class Canvas(QWidget):
    """Fullscreen transparent overlay window for rendering Mochi.

    The canvas covers the primary monitor's available geometry (excluding
    OS taskbar/dock), is click-through by default, and renders the cat
    sprite with animation driven by the FSM and Physics engines.

    Parameters
    ----------
    parent : QWidget or None
        Optional parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowFlags(_CANVAS_FLAGS)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        screen = QApplication.primaryScreen()
        self._screen_geo: QRect | None = None
        if screen is not None:
            geo = screen.availableGeometry()
            self.setGeometry(geo)
            self._screen_geo = geo

        # ── Sprite sheet loading ──────────────────────────────────────────
        self._spritesheet: SpriteSheet = SpriteSheet("sprites/")
        self._animations: dict[str, list[QPixmap]] = {
            "idle": self._spritesheet.load("idle"),
            "walk": self._spritesheet.load("walk"),
        }
        self._current_frame: int = 0
        self._current_sprite_key: str = "idle"

        # ── FSM & Physics ─────────────────────────────────────────────────
        self._fsm: FSM = FSM()
        bottom_y = self._screen_bottom_y()
        self._physics: Physics = Physics(
            x=(self.width() - config.SPRITE_CELL_WIDTH) // 2,
            y=bottom_y,
        )
        self._last_tick: float = time.monotonic()

        # ── Surface list (from EnvironmentPoller) ──────────────────────────
        self._surfaces: list[Surface] = []

        # ── Environment poller (started lazily in showEvent) ───────────────
        self._poller: EnvironmentPoller | None = None
        if self._screen_geo is not None:
            self._poller = EnvironmentPoller(screen_geo=self._screen_geo)
            self._poller.platforms_updated.connect(self._on_platforms_updated)
            # Note: _poller.start() called in showEvent to avoid thread
            # conflicts during widget construction in tests.

        # ── Animation timer (adaptive rate) ───────────────────────────────
        self._animation_timer: QTimer = QTimer(self)
        self._animation_timer.setInterval(_TICK_INTERVALS[PetState.Idle])
        self._animation_timer.timeout.connect(self._advance_frame)
        self._animation_timer.start()

        logger.info(
            "Canvas created: %dx%d at (%d, %d), frames: idle=%d walk=%d",
            self.width(),
            self.height(),
            self.x(),
            self.y(),
            len(self._animations.get("idle", [])),
            len(self._animations.get("walk", [])),
        )

    # ── Public helpers ──────────────────────────────────────────────────

    @property
    def fsm(self) -> FSM:
        """Expose the FSM instance for testing and external control."""
        return self._fsm

    @property
    def physics(self) -> Physics:
        """Expose the Physics instance for testing and external control."""
        return self._physics

    # ── Public helpers ──────────────────────────────────────────────────

    def showEvent(self, event: object) -> None:  # noqa: N802
        """Start the environment poller when the canvas is first shown."""
        if self._poller is not None and not self._poller.isRunning():
            self._poller.start()
        super().showEvent(event)  # type: ignore[misc]

    def closeEvent(self, event: object) -> None:  # noqa: N802
        """Clean up the poller thread on window close."""
        self._stop_poller()
        super().closeEvent(event)  # type: ignore[misc]

    def _stop_poller(self) -> None:
        """Safely stop and clean up the environment poller thread."""
        if self._poller is not None:
            p = self._poller
            self._poller = None
            p.platforms_updated.disconnect(self._on_platforms_updated)
            p.quit()
            p.wait(2000)
            p.deleteLater()

    def _on_platforms_updated(self, surfaces: list[Surface]) -> None:
        """Store the latest surface list from the environment poller.

        Parameters
        ----------
        surfaces : list[Surface]
            The latest list of walkable surfaces on the desktop.
        """
        self._surfaces = surfaces
        logger.info("Surfaces updated: %d surfaces", len(surfaces))

    # ── Internal ─────────────────────────────────────────────────────────

    def _screen_bottom_y(self) -> int:
        """Return the Y coordinate for the screen-bottom surface."""
        geo = self._screen_geo
        if geo is not None:
            return geo.bottom() - config.SCREEN_BOTTOM_MARGIN_PX - config.SPRITE_CELL_HEIGHT
        return 0

    def _advance_frame(self) -> None:
        """Animation tick: advance FSM, physics, and sprite frame.

        Called by the ``QTimer`` at a state-dependent interval.
        """
        # 1. Compute dt (frame-rate independent)
        now = time.monotonic()
        dt = now - self._last_tick
        self._last_tick = now

        # 2. Tick the FSM (timer-based state transitions)
        self._fsm.tick(dt)
        current_state = self._fsm.current_state

        # 2.5 Sync physics direction from FSM (FSM owns direction reversal)
        # Note: ``x`` is the sprite's **left edge** in both directions
        # (see ``paintEvent``), so no position adjustment is needed on flip.
        self._physics.direction = self._fsm.direction

        # 3. Update physics (horizontal movement)
        geo = self._screen_geo
        screen_width = geo.width() if geo is not None else 1920
        edge_hit = self._physics.update(
            dt,
            current_state,
            screen_width=screen_width,
            sprite_width=config.SPRITE_CELL_WIDTH,
        )

        # 4. Handle edge-hit: transition to EdgePause
        if edge_hit and current_state is PetState.Walk:
            self._fsm.transition_to(PetState.EdgePause)

        # 5. Determine sprite key from state
        new_key = _SPRITE_KEYS.get(current_state, "idle")

        # 6. Swap sprite animation if key changed
        if new_key != self._current_sprite_key:
            self._current_sprite_key = new_key
            self._current_frame = 0

        # 7. Advance frame index
        frames = self._animations.get(self._current_sprite_key, [])
        if not frames and self._current_sprite_key == "walk":
            logger.warning("No walk frames loaded — cat will be invisible during Walk state")
        if frames:
            self._current_frame = (self._current_frame + 1) % len(frames)

        # 8. Adapt timer interval to current state
        self._animation_timer.setInterval(_TICK_INTERVALS.get(current_state, 250))

        # 9. Request repaint
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802
        """Render the current sprite frame, flipped for left direction.

        Parameters
        ----------
        event : QPaintEvent
            The paint event (unused — full window repaint).
        """
        painter = QPainter(self)
        try:
            screen = QApplication.primaryScreen()
            geo = screen.availableGeometry() if screen is not None else self._screen_geo
            if geo is None:
                return

            x = int(self._physics.x)
            y = int(self._physics.y)

            frames = self._animations.get(self._current_sprite_key, [])
            if frames and self._current_frame < len(frames):
                frame = frames[self._current_frame]

                # ``x`` always represents the sprite's **left edge** in canvas
                # coordinates, regardless of direction.  When facing right
                # (dir=+1) we flip horizontally via ``scale(-1, 1)`` and adjust
                # the origin so the flipped sprite still occupies [x, x+w].
                #
                # Without the ``+ 1`` offset, the two branches would differ by
                # one pixel — imperceptible, but this keeps them pixel-identical.
                if self._physics.direction == 1:
                    painter.save()
                    painter.scale(-1.0, 1.0)
                    painter.drawPixmap(-x - frame.width() + 1, y, frame)
                    painter.restore()
                else:
                    painter.drawPixmap(x, y, frame)
        finally:
            painter.end()
