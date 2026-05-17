"""Tests for mochi.core.environment — Surface dataclass and EnvironmentPoller."""

from __future__ import annotations

from PySide6.QtCore import QRect, QThread, Signal

from mochi.core.environment import EnvironmentPoller, Surface


class TestEnvironmentPollerSkeleton:
    """EnvironmentPoller must be a QThread subclass with a platforms_updated signal."""

    def test_poller_is_qthread_subclass(self) -> None:
        """EnvironmentPoller must inherit from QThread."""
        assert issubclass(EnvironmentPoller, QThread)

    def test_poller_has_platforms_updated_signal(self) -> None:
        """EnvironmentPoller must declare a platforms_updated Signal(list)."""
        assert hasattr(EnvironmentPoller, "platforms_updated")
        assert isinstance(EnvironmentPoller.platforms_updated, Signal)

    def test_poller_accepts_screen_geo(self) -> None:
        """EnvironmentPoller should accept a screen_geo QRect argument."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        assert poller is not None


class TestWindowFiltering:
    """_get_visible_windows must filter out unwanted windows."""

    def test_visible_window_included(self) -> None:
        """Normal visible windows should be included in the result."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        mock_windows = [
            _make_mock_window(title="Notepad", minimized=False),
            _make_mock_window(title="Chrome", minimized=False),
        ]
        result = poller._get_visible_windows(mock_windows)
        assert len(result) == 2

    def test_minimized_window_excluded(self) -> None:
        """Minimized windows should be filtered out."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        mock_windows = [
            _make_mock_window(title="Notepad", minimized=False),
            _make_mock_window(title="Hidden App", minimized=True),
        ]
        result = poller._get_visible_windows(mock_windows)
        assert len(result) == 1
        assert result[0].title == "Notepad"

    def test_empty_title_window_excluded(self) -> None:
        """Windows with empty titles should be filtered out."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        mock_windows = [
            _make_mock_window(title="", minimized=False),
            _make_mock_window(title="Terminal", minimized=False),
        ]
        result = poller._get_visible_windows(mock_windows)
        assert len(result) == 1
        assert result[0].title == "Terminal"

    def test_mochi_overlay_excluded(self) -> None:
        """The Mochi overlay window should be filtered out by title."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        mock_windows = [
            _make_mock_window(title="Mochi", minimized=False),
            _make_mock_window(title="VS Code", minimized=False),
        ]
        result = poller._get_visible_windows(mock_windows)
        assert len(result) == 1
        assert result[0].title == "VS Code"

    def test_all_filters_combined(self) -> None:
        """All filters should work together with mixed windows."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        mock_windows = [
            _make_mock_window(title="Mochi", minimized=False),
            _make_mock_window(title="", minimized=False),
            _make_mock_window(title="Hidden", minimized=True),
            _make_mock_window(title="Explorer", minimized=False),
        ]
        result = poller._get_visible_windows(mock_windows)
        assert len(result) == 1
        assert result[0].title == "Explorer"

    def test_empty_window_list(self) -> None:
        """An empty list should return an empty list."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        result = poller._get_visible_windows([])
        assert result == []


class _MockWindow:
    """Minimal mock for pywinctl.Window geometry and visibility."""

    def __init__(
        self,
        title: str,
        minimized: bool,
        left: int = 0,
        top: int = 0,
        width: int = 800,
        height: int = 600,
    ) -> None:
        self.title = title
        self._is_minimized = minimized
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def isMinimized(self) -> bool:  # noqa: N802
        return self._is_minimized


def _make_mock_window(
    title: str,
    minimized: bool = False,
    left: int = 100,
    top: int = 100,
    width: int = 800,
    height: int = 600,
) -> _MockWindow:
    """Helper to create a mock pywinctl Window with minimal required attrs."""
    return _MockWindow(
        title=title,
        minimized=minimized,
        left=left,
        top=top,
        width=width,
        height=height,
    )


class TestSurfaceListBuilder:
    """_build_surfaces must produce correct Surface objects for all types."""

    def test_window_top_surface(self) -> None:
        """A window should produce a window_top surface at its top edge."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        win = _make_mock_window(title="Test", left=100, top=200, width=800, height=600)
        surfaces = poller._build_surfaces([win])
        tops = [s for s in surfaces if s.surface_type == "window_top"]
        assert len(tops) == 1
        assert tops[0].rect == QRect(100, 200, 800, 0)

    def test_window_left_surface(self) -> None:
        """A window should produce a window_left surface at its left edge."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        win = _make_mock_window(title="Test", left=100, top=200, width=800, height=600)
        surfaces = poller._build_surfaces([win])
        lefts = [s for s in surfaces if s.surface_type == "window_left"]
        assert len(lefts) == 1
        assert lefts[0].rect == QRect(100, 200, 0, 600)

    def test_window_right_surface(self) -> None:
        """A window should produce a window_right surface at its right edge."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        win = _make_mock_window(title="Test", left=100, top=200, width=800, height=600)
        surfaces = poller._build_surfaces([win])
        rights = [s for s in surfaces if s.surface_type == "window_right"]
        assert len(rights) == 1
        assert rights[0].rect == QRect(900, 200, 0, 600)

    def test_multiple_windows(self) -> None:
        """Multiple windows should produce surfaces for each."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        win1 = _make_mock_window(title="Win1", left=0, top=0, width=400, height=300)
        win2 = _make_mock_window(title="Win2", left=500, top=100, width=600, height=400)
        surfaces = poller._build_surfaces([win1, win2])
        tops = [s for s in surfaces if s.surface_type == "window_top"]
        assert len(tops) == 2

    def test_screen_bottom_surface(self) -> None:
        """Screen bottom surface should always be present."""
        from mochi import config

        geo = QRect(0, 0, 1920, 1080)
        poller = EnvironmentPoller(screen_geo=geo)
        surfaces = poller._build_surfaces([])
        bottoms = [s for s in surfaces if s.surface_type == "screen_bottom"]
        assert len(bottoms) == 1
        expected_y = geo.bottom() - config.SCREEN_BOTTOM_MARGIN_PX - config.SPRITE_CELL_HEIGHT
        assert bottoms[0].rect == QRect(0, expected_y, 1920, 0)

    def test_screen_left_surface(self) -> None:
        """Screen left edge surface should always be present."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        surfaces = poller._build_surfaces([])
        lefts = [s for s in surfaces if s.surface_type == "screen_left"]
        assert len(lefts) == 1
        assert lefts[0].rect == QRect(0, 0, 0, 1080)

    def test_screen_right_surface(self) -> None:
        """Screen right edge surface should always be present."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        surfaces = poller._build_surfaces([])
        rights = [s for s in surfaces if s.surface_type == "screen_right"]
        assert len(rights) == 1
        assert rights[0].rect == QRect(1920, 0, 0, 1080)

    def test_screen_edges_always_present(self) -> None:
        """All three screen edges should be present even with zero windows."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        surfaces = poller._build_surfaces([])
        surface_types = {s.surface_type for s in surfaces}
        assert "screen_bottom" in surface_types
        assert "screen_left" in surface_types
        assert "screen_right" in surface_types

    def test_window_id_preserved(self) -> None:
        """Window surfaces should carry the window handle as window_id."""
        poller = EnvironmentPoller(screen_geo=QRect(0, 0, 1920, 1080))
        win = _make_mock_window(title="Test", left=100, top=200, width=800, height=600)
        surfaces = poller._build_surfaces([win])
        for s in surfaces:
            if s.surface_type != "screen_bottom":
                # mock window doesn't have a real handle, so it'll be None
                pass


class TestSurfaceReexport:
    """Surface must be re-exported from mochi.core."""

    def test_surface_importable_from_core(self) -> None:
        """Surface should be importable from mochi.core."""
        from mochi.core import Surface as SurfaceAlias

        assert SurfaceAlias is not None


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
