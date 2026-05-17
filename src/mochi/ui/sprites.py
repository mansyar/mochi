"""Sprite sheet loader for Mochi cat animations.

Provides a ``SpriteSheet`` class that loads sprite PNG files, slices them
into individual 64x64 frame pixmaps, and caches them by animation key.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import ClassVar

from PySide6.QtGui import QPixmap

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

    _CELL_SIZE: ClassVar[int] = config.SPRITE_CELL_WIDTH  # 64 px

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
        cell = self._CELL_SIZE

        # Silently skip files whose dimensions are not multiples of cell size.
        if w % cell != 0 or h % cell != 0:
            logger.warning(
                "Sprite sheet %s has non-conforming dimensions %dx%d (cell %d), skipping",
                matched.name,
                w,
                h,
                cell,
            )
            self._cache[animation_key] = []
            return self._cache[animation_key]

        cols = w // cell
        rows = h // cell
        frames: list[QPixmap] = []

        for row in range(rows):
            for col in range(cols):
                frame = pixmap.copy(col * cell, row * cell, cell, cell)
                frames.append(frame)

        self._cache[animation_key] = frames
        return frames

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
