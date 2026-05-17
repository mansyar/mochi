"""Sprite sheet loader for Mochi cat animations.

Provides a ``SpriteSheet`` class that loads sprite PNG files, slices them
into individual 64x64 frame pixmaps, and caches them by animation key.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap

from mochi import config

logger = logging.getLogger("mochi.sprites")

#: Module-level cache for assets root path (resolved once).
_ASSETS_ROOT: Path | None = None


def asset_path(relative: str) -> Path:
    """Resolve a relative asset path for the current runtime mode.

    Supports three execution modes:

    - **Development:** resolves relative to the project root (``assets/``).
    - **PyInstaller:** resolves relative to ``sys._MEIPASS``.
    - **Nuitka:** resolves relative to the ``__compiled__`` location.

    Parameters
    ----------
    relative : str
        Relative path to an asset file or directory (e.g. ``"sprites/IDLE.png"``).

    Returns
    -------
    Path
        Absolute path to the requested asset.
    """
    global _ASSETS_ROOT

    if _ASSETS_ROOT is not None:
        return _ASSETS_ROOT / relative

    # PyInstaller bundles data into sys._MEIPASS.
    if hasattr(sys, "_MEIPASS") and isinstance(sys._MEIPASS, str):
        _ASSETS_ROOT = Path(sys._MEIPASS, "assets")
    # Nuitka sets __compiled__ when running compiled.
    elif "__compiled__" in globals() or "__compiled__" in locals():
        _ASSETS_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "assets"
    else:
        # Development mode — assume cwd is the project root.
        _ASSETS_ROOT = Path.cwd() / "assets"

    return _ASSETS_ROOT / relative


class SpriteSheet:
    """Loads and caches sprite sheet frame pixmaps by animation key.

    Each animation key maps to a PNG file in the configured asset directory.
    The PNG is sliced into individual 64x64 ``QPixmap`` frames.

    Parameters
    ----------
    asset_dir : str
        Path to the directory containing sprite PNG files, relative
        to the configured assets root.
    """

    _CELL_W: ClassVar[int] = config.SPRITE_CELL_WIDTH  # 80 px (canvas width per frame)
    _CELL_H: ClassVar[int] = config.SPRITE_CELL_HEIGHT  # 64 px

    def __init__(self, asset_dir: str) -> None:
        self._asset_dir: str = asset_dir
        #: Internal cache: animation_key -> list[QPixmap]
        self._cache: dict[str, list[QPixmap]] = {}

    def load(self, animation_key: str) -> list[QPixmap]:
        """Load and slice a sprite sheet by animation key.

        The key is matched case-insensitively to a ``.png`` file in the
        configured asset directory.  Multi-word keys (e.g. ``"attack 1"``)
        are matched directly to filenames like ``"ATTACK 1.png"``.

        Parameters
        ----------
        animation_key : str
            Lowercase animation identifier (e.g. ``"idle"``, ``"attack 1"``).

        Returns
        -------
        list[QPixmap]
            List of individual frame pixmaps, or an empty list if the
            file could not be loaded or its dimensions are not multiples
            of the sprite cell size.
        """
        if animation_key in self._cache:
            return self._cache[animation_key]

        sheet_dir = asset_path(self._asset_dir)

        # Case-insensitive search for the matching .png file.
        target_name = animation_key + ".png"
        matched: Path | None = None
        for child in sheet_dir.iterdir():
            if child.is_file() and child.name.lower() == target_name.lower():
                matched = child
                break

        if matched is None:
            logger.warning("Sprite sheet not found: %s (%s.png)", animation_key, animation_key)
            self._cache[animation_key] = []
            return self._cache[animation_key]

        # Attempt to load the PNG.
        pixmap = QPixmap(str(matched))
        if pixmap.isNull():
            logger.warning("Failed to load sprite sheet: %s", matched)
            self._cache[animation_key] = []
            return self._cache[animation_key]

        w = pixmap.width()
        h = pixmap.height()
        cell_w = self._CELL_W
        cell_h = self._CELL_H

        # Silently skip files whose dimensions are not multiples of cell size.
        if w % cell_w != 0 or h % cell_h != 0:
            logger.warning(
                "Sprite sheet %s has non-conforming dimensions %dx%d (cell %dx%d), skipping",
                matched.name,
                w,
                h,
                cell_w,
                cell_h,
            )
            self._cache[animation_key] = []
            return self._cache[animation_key]

        cols = w // cell_w
        rows = h // cell_h
        frames: list[QPixmap] = []

        for row in range(rows):
            for col in range(cols):
                raw_frame = pixmap.copy(col * cell_w, row * cell_h, cell_w, cell_h)
                centered = self._autocenter_frame(raw_frame)
                frames.append(centered)

        self._cache[animation_key] = frames
        return frames

    @staticmethod
    def _autocenter_frame(frame: QPixmap) -> QPixmap:
        """Center the visible content of a sprite frame within the cell.

        Sprite sheets often have animation frames where the character's
        content (non-transparent pixels) shifts position from frame to
        frame (e.g. a tail flick moving the center of mass).  This method
        detects the content bounding box and re-centers it so the
        animation appears stable — the character stays in place while
        animating.

        Parameters
        ----------
        frame : QPixmap
            The raw sliced frame pixmap (80x64).

        Returns
        -------
        QPixmap
            The centered frame (the original is returned unchanged if
            the content is already within 1 pixel of the center).
        """
        cell_w = SpriteSheet._CELL_W
        cell_h = SpriteSheet._CELL_H
        image = frame.toImage()

        # Scan for non-transparent content bounds.
        min_x, max_x = cell_w, 0
        min_y, max_y = cell_h, 0

        for y in range(cell_h):
            for x in range(cell_w):
                px = image.pixelColor(x, y)
                if px.alpha() > 0:
                    if x < min_x:
                        min_x = x
                    if x > max_x:
                        max_x = x
                    if y < min_y:
                        min_y = y
                    if y > max_y:
                        max_y = y

        # Empty frame — return as-is.
        if max_x == 0:
            return frame

        content_cx = (min_x + max_x) / 2.0
        content_cy = (min_y + max_y) / 2.0
        center_x = (cell_w - 1) / 2.0
        center_y = (cell_h - 1) / 2.0

        offset_x = round(content_cx - center_x)
        offset_y = round(content_cy - center_y)

        # Already centered within 1 px — skip reprocessing.
        if abs(offset_x) <= 1 and abs(offset_y) <= 1:
            return frame

        # Create a new transparent pixmap and draw the content centered.
        centered = QPixmap(cell_w, cell_h)
        centered.fill(Qt.GlobalColor.transparent)

        painter = QPainter(centered)
        try:
            painter.drawPixmap(-offset_x, -offset_y, frame)
        finally:
            painter.end()

        return centered

    def get_frames(self, animation_key: str) -> list[QPixmap]:
        """Return the cached frame list for an animation key.

        Parameters
        ----------
        animation_key : str
            Animation key to look up.

        Returns
        -------
        list[QPixmap]
            Cached frame list, or an empty list if the key has not been
            loaded (does **not** raise ``KeyError``).
        """
        return self._cache.get(animation_key, [])
