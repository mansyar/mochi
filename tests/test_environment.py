"""Tests for mochi.core.environment — Surface dataclass and EnvironmentPoller."""

from __future__ import annotations

from PySide6.QtCore import QRect

from mochi.core.environment import Surface


class TestSurfaceDataclass:
    """Surface dataclass must have correct fields, types, and defaults."""

    def test_surface_is_dataclass(self) -> None:
        """Surface should be a dataclass (comparing by value, not identity)."""
        s1 = Surface(rect=QRect(0, 0, 100, 200), surface_type="window_top", window_id=42)
        s2 = Surface(rect=QRect(0, 0, 100, 200), surface_type="window_top", window_id=42)
        assert s1 == s2

    def test_surface_fields_exist(self) -> None:
        """Surface must have rect, surface_type, and window_id."""
        s = Surface(rect=QRect(10, 20, 300, 400), surface_type="screen_bottom", window_id=None)
        assert hasattr(s, "rect")
        assert hasattr(s, "surface_type")
        assert hasattr(s, "window_id")

    def test_surface_rect_type(self) -> None:
        """rect field must be a QRect."""
        s = Surface(rect=QRect(0, 0, 80, 64), surface_type="window_left", window_id=1)
        assert isinstance(s.rect, QRect)

    def test_surface_surface_type_str(self) -> None:
        """surface_type field must be a string."""
        s = Surface(rect=QRect(0, 0, 80, 64), surface_type="window_right", window_id=2)
        assert isinstance(s.surface_type, str)

    def test_surface_window_id_can_be_int(self) -> None:
        """window_id field can be an int."""
        s = Surface(rect=QRect(0, 0, 80, 64), surface_type="window_top", window_id=42)
        assert isinstance(s.window_id, int)

    def test_surface_window_id_can_be_none(self) -> None:
        """window_id field can be None (for screen edges)."""
        s = Surface(rect=QRect(0, 0, 80, 64), surface_type="screen_bottom", window_id=None)
        assert s.window_id is None

    def test_surface_valid_surface_types(self) -> None:
        """All six valid surface types should be accepted."""
        for st in (
            "window_top",
            "window_left",
            "window_right",
            "screen_bottom",
            "screen_left",
            "screen_right",
        ):
            s = Surface(rect=QRect(0, 0, 80, 64), surface_type=st, window_id=None)
            assert s.surface_type == st
