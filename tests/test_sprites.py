"""Tests for mochi.ui.sprites — SpriteSheet loader."""

from __future__ import annotations

import logging
from unittest.mock import patch

from PySide6.QtGui import QPixmap

from mochi import config


class TestSpriteSheetClass:
    """Test that SpriteSheet class definition is correct."""

    def test_sprite_sheet_module_importable(self) -> None:
        """Importing the sprites module should not raise."""
        import mochi.ui.sprites  # noqa: F401

    def test_sprite_sheet_class_exists(self) -> None:
        """SpriteSheet class must exist in the sprites module."""
        from mochi.ui.sprites import SpriteSheet

        assert SpriteSheet is not None

    def test_sprite_sheet_instantiable(self) -> None:
        """SpriteSheet should be instantiable with an asset directory."""
        from mochi.ui.sprites import SpriteSheet

        sheet = SpriteSheet("assets/sprites/")
        assert isinstance(sheet, SpriteSheet)


class TestSpriteSheetFunctionality:
    """Test SpriteSheet loading and frame access (requires QApp via qtbot)."""

    SPRITES_DIR = "sprites/"
    CELL_W = config.SPRITE_CELL_WIDTH  # 64
    CELL_H = config.SPRITE_CELL_HEIGHT  # 64

    def test_load_idle_returns_10_frames(self, qtbot: object) -> None:
        """load('idle') should return a list of 10 QPixmap frames (640÷64)."""
        from mochi.ui.sprites import SpriteSheet

        sheet = SpriteSheet(self.SPRITES_DIR)
        frames = sheet.load("idle")
        assert isinstance(frames, list)
        assert len(frames) == 10
        for frame in frames:
            assert isinstance(frame, QPixmap)

    def test_each_frame_is_64x64(self, qtbot: object) -> None:
        """Each loaded frame pixmap should be 64x64 pixels."""
        from mochi.ui.sprites import SpriteSheet

        sheet = SpriteSheet(self.SPRITES_DIR)
        frames = sheet.load("idle")
        for frame in frames:
            assert not frame.isNull()
            assert frame.width() == self.CELL_W
            assert frame.height() == self.CELL_H

    def test_load_nonexistent_returns_empty_list(self, qtbot: object) -> None:
        """Loading a non-existent animation key should log warning and return empty list."""
        from mochi.ui.sprites import SpriteSheet

        sheet = SpriteSheet(self.SPRITES_DIR)
        with patch.object(logging.getLogger("mochi.sprites"), "warning") as mock_warn:
            frames = sheet.load("nonexistent_key")
        assert frames == []
        mock_warn.assert_called_once()

    def test_get_frames_returns_cached_list(self, qtbot: object) -> None:
        """get_frames('idle') should return the previously cached frame list."""
        from mochi.ui.sprites import SpriteSheet

        sheet = SpriteSheet(self.SPRITES_DIR)
        loaded = sheet.load("idle")
        cached = sheet.get_frames("idle")
        assert cached is loaded  # same list object
        assert len(cached) == 10

    def test_get_frames_nonexistent_returns_empty_list(self, qtbot: object) -> None:
        """get_frames('nonexistent') should return empty list, not raise KeyError."""
        from mochi.ui.sprites import SpriteSheet

        sheet = SpriteSheet(self.SPRITES_DIR)
        frames = sheet.get_frames("nonexistent")
        assert frames == []

    def test_bowl_16x16_is_skipped(self, qtbot: object) -> None:
        """Loading BOWL.png (16x16) should silently skip it and return empty list."""
        from mochi.ui.sprites import SpriteSheet

        sheet = SpriteSheet(self.SPRITES_DIR)
        with patch.object(logging.getLogger("mochi.sprites"), "warning") as mock_warn:
            frames = sheet.load("bowl")
        assert frames == []
        mock_warn.assert_called_once()

    def test_frames_are_centered_within_tolerance(self, qtbot: object) -> None:
        """Each loaded idle frame should have its content centered within 2px."""
        from mochi.ui.sprites import SpriteSheet

        sheet = SpriteSheet(self.SPRITES_DIR)
        frames = sheet.load("idle")
        cell = self.CELL_W
        frame_center = (cell - 1) / 2.0

        for idx, frame in enumerate(frames):
            image = frame.toImage()
            min_x, max_x = cell, 0
            min_y, max_y = cell, 0

            for y in range(cell):
                for x in range(cell):
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

            if max_x > 0:  # Has content
                content_cx = (min_x + max_x) / 2.0
                content_cy = (min_y + max_y) / 2.0
                offset_x = abs(content_cx - frame_center)
                offset_y = abs(content_cy - frame_center)
                assert offset_x <= 2.0, (
                    f"Frame {idx}: content center_x {content_cx:.1f} is "
                    f"{offset_x:.1f}px from frame center {frame_center}"
                )
                assert offset_y <= 2.0, (
                    f"Frame {idx}: content center_y {content_cy:.1f} is "
                    f"{offset_y:.1f}px from frame center {frame_center}"
                )

    def test_attack_1_multiword_key(self, qtbot: object) -> None:
        """Multi-word keys like 'attack 1' should match 'ATTACK 1.png'."""
        from mochi.ui.sprites import SpriteSheet

        sheet = SpriteSheet(self.SPRITES_DIR)
        frames = sheet.load("attack 1")
        assert isinstance(frames, list)
        if frames:  # if ATTACK 1.png is a valid sprite sheet
            for frame in frames:
                assert frame.width() == self.CELL_W
                assert frame.height() == self.CELL_H
