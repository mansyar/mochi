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
    PetState.Fall: 100,
}

#: Sprite animation key lookup per FSM state.
_SPRITE_KEYS: dict[PetState, str] = {
    PetState.Idle: "idle",
    PetState.Walk: "walk",
    PetState.EdgePause: "walk",
    PetState.Fall: "fall",
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

        # Load fall sprite from JUMP.png middle frame (index 1)
        jump_frames = self._spritesheet.load("jump")
        if len(jump_frames) >= 2:
            fall_frames: list[QPixmap] = [jump_frames[1]]
        else:
            logger.warning("JUMP.png has fewer than 2 frames — fall sprite unavailable")
            fall_frames = []

        self._animations: dict[str, list[QPixmap]] = {
            "idle": self._spritesheet.load("idle"),
            "walk": self._spritesheet.load("walk"),
            "fall": fall_frames,
        }
        self._current_frame: int = 0
        self._current_sprite_key: str = "idle"

        # ── FSM & Physics ─────────────────────────────────────────────────
        self._fsm: FSM = FSM()
        # Compute ground offset from sprite content bounds (before Physics)
        self._ground_offset: float = self._compute_ground_offset()
        bottom_y = self._screen_bottom_y()

        self._physics: Physics = Physics(
            x=(self.width() - config.SPRITE_CELL_WIDTH) // 2,
            y=bottom_y,
            ground_offset=self._ground_offset,
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
            "Canvas created: %dx%d at (%d, %d), frames: idle=%d walk=%d fall=%d",
            self.width(),
            self.height(),
            self.x(),
            self.y(),
            len(self._animations.get("idle", [])),
            len(self._animations.get("walk", [])),
            len(self._animations.get("fall", [])),
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
        super().showEvent(event)  # type: ignore[arg-type]

    def closeEvent(self, event: object) -> None:  # noqa: N802
        """Clean up the poller thread on window close."""
        self._stop_poller()
        super().closeEvent(event)  # type: ignore[arg-type]

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
        offset = (
            int(self._ground_offset)
            if hasattr(self, "_ground_offset")
            else config.SPRITE_CELL_HEIGHT
        )
        if geo is not None:
            return geo.bottom() - offset
        return 0

    def _compute_ground_offset(self) -> float:
        """Compute the ground contact offset from sprite content bounds.

        Scans idle and walk frames for the maximum content-bottom pixel
        position within the cell.  This accounts for transparent padding
        below the cat's feet due to sprite auto-centering.

        Returns
        -------
        float
            Distance from ``self.y`` to the cat's ground contact point.
            Falls back to ``SPRITE_CELL_HEIGHT`` if no frames are loaded.
        """
        cell_h = config.SPRITE_CELL_HEIGHT
        max_content_bottom = 0

        for key in ("idle", "walk"):
            frames = self._animations.get(key, [])
            for frame in frames:
                img = frame.toImage()
                for y in range(cell_h):
                    for x in range(frame.width()):
                        if img.pixelColor(x, y).alpha() > 0 and y > max_content_bottom:
                            max_content_bottom = y

        if max_content_bottom == 0:
            # No content found — fall back to full cell height
            return float(cell_h)

        # Ground contact is one pixel below the bottommost content pixel
        return float(max_content_bottom + 1)

    def _advance_frame(self) -> None:
        """Animation tick: advance physics, FSM, and sprite frame.

        Called by the ``QTimer`` at a state-dependent interval.

        **Critical ordering:** physics runs BEFORE the FSM tick to prevent
        Walk→Idle timer transitions from masking surface-loss detection.
        Fall state has ``float('inf')`` timer so it never auto-transitions
        via the timer — transitions are purely physics-driven.
        """
        # 1. Compute dt (frame-rate independent)
        now = time.monotonic()
        dt = now - self._last_tick
        self._last_tick = now

        # 2. Sync physics direction from FSM (FSM owns direction reversal)
        # Note: ``x`` is the sprite's **left edge** in both directions
        # (see ``paintEvent``), so no position adjustment is needed on flip.
        current_state = self._fsm.current_state
        self._physics.direction = self._fsm.direction

        # 3. Update physics with surface awareness
        geo = self._screen_geo
        screen_width = geo.width() if geo is not None else 1920
        result = self._physics.update(
            dt,
            current_state,
            screen_width=screen_width,
            sprite_width=config.SPRITE_CELL_WIDTH,
            surfaces=self._surfaces,
        )

        # 4. Handle surface-loss: Walk → Fall
        if result.surface_lost and current_state is PetState.Walk:
            self._fsm.transition_to(PetState.Fall)
            current_state = self._fsm.current_state

        # 5. Handle landing: Fall → Idle
        if result.landed and current_state is PetState.Fall:
            self._fsm.transition_to(PetState.Idle)
            current_state = self._fsm.current_state

        # 6. Tick the FSM (timer-based state transitions)
        # Safe: Fall has inf timer, won't auto-transition.
        self._fsm.tick(dt)
        current_state = self._fsm.current_state

        # 7. Handle edge-hit: transition to EdgePause
        if result.edge_hit and current_state is PetState.Walk:
            self._fsm.transition_to(PetState.EdgePause)
            current_state = self._fsm.current_state

        # 8. Determine sprite key from state
        new_key = _SPRITE_KEYS.get(current_state, "idle")

        # 9. Swap sprite animation if key changed
        if new_key != self._current_sprite_key:
            self._current_sprite_key = new_key
            self._current_frame = 0

        # 10. Advance frame index
        frames = self._animations.get(self._current_sprite_key, [])
        if not frames and self._current_sprite_key in ("walk", "fall"):
            logger.warning(
                "No %s frames loaded — cat will be invisible during %s state",
                self._current_sprite_key,
                current_state,
            )
        if frames:
            self._current_frame = (self._current_frame + 1) % len(frames)

        # 11. Adapt timer interval to current state
        self._animation_timer.setInterval(_TICK_INTERVALS.get(current_state, 250))

        # 12. Request repaint
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
