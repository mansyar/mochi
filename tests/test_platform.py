"""Tests for mochi.utils.platform."""

from pathlib import Path
from unittest.mock import patch

from mochi.utils.platform import get_data_dir, get_platform, is_alt_held, set_click_through


class TestGetPlatform:
    """Test OS detection stub."""

    def test_returns_string(self) -> None:
        result = get_platform()
        assert isinstance(result, str)
        assert result in ("win32", "darwin", "linux")


class TestGetDataDir:
    """Test data directory resolution."""

    @patch("mochi.utils.platform.sys.platform", "win32")
    @patch("mochi.utils.platform.os.environ", {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"})
    def test_windows_uses_appdata(self) -> None:
        path = get_data_dir()
        assert "AppData" in str(path)

    @patch("mochi.utils.platform.sys.platform", "darwin")
    @patch("mochi.utils.platform.os.environ", {"HOME": "/Users/test"})
    def test_macos_uses_application_support(self) -> None:
        path = get_data_dir()
        assert "Application Support" in str(path)

    @patch("mochi.utils.platform.sys.platform", "linux")
    @patch("mochi.utils.platform.os.environ", {"HOME": "/home/test"})
    def test_linux_uses_xdg_data_home(self) -> None:
        path = get_data_dir()
        assert ".local/share" in str(path)

    def test_returns_path(self) -> None:
        result = get_data_dir()
        assert isinstance(result, Path)


class TestIsAltHeld:
    """Test Alt key detection stub."""

    def test_returns_bool(self) -> None:
        result = is_alt_held()
        assert isinstance(result, bool)


class TestSetClickThrough:
    """Test click-through toggle stub."""

    def test_accepts_widget_and_bool(self) -> None:
        # Should not raise when called with None (no widget yet)
        set_click_through(None, True)
        set_click_through(None, False)
