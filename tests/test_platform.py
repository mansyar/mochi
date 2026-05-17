"""Tests for mochi.utils.platform."""

from pathlib import Path
from unittest.mock import MagicMock, patch

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
    @patch("pathlib.Path.mkdir")
    def test_windows_uses_appdata(self, mock_mkdir: MagicMock) -> None:
        path = get_data_dir()
        assert "AppData" in str(path)
        assert path.name == "Mochi"

    @patch("mochi.utils.platform.sys.platform", "darwin")
    @patch("mochi.utils.platform.Path.home", return_value=Path("/Users/test"))
    @patch("pathlib.Path.mkdir")
    def test_macos_uses_application_support(
        self, mock_mkdir: MagicMock, mock_home: MagicMock
    ) -> None:
        path = get_data_dir()
        assert "Application Support" in str(path)
        assert path.name == "Mochi"

    @patch("mochi.utils.platform.sys.platform", "linux")
    @patch("mochi.utils.platform.os.environ", {"XDG_DATA_HOME": "/home/test/.local/share"})
    @patch("pathlib.Path.mkdir")
    def test_linux_uses_xdg_data_home_with_env(self, mock_mkdir: MagicMock) -> None:
        path = get_data_dir()
        assert ".local" in path.parts
        assert "share" in path.parts
        assert path.name == "mochi"

    @patch("mochi.utils.platform.sys.platform", "linux")
    @patch("mochi.utils.platform.Path.home", return_value=Path("/home/test"))
    @patch("pathlib.Path.mkdir")
    def test_linux_falls_back_to_home(self, mock_mkdir: MagicMock, mock_home: MagicMock) -> None:
        path = get_data_dir()
        assert ".local" in path.parts
        assert "share" in path.parts
        assert path.name == "mochi"

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

    def test_none_widget_does_not_raise(self) -> None:
        """set_click_through(None, True) should not raise."""
        set_click_through(None, True)

    def test_none_widget_false_does_not_raise(self) -> None:
        """set_click_through(None, False) should not raise."""
        set_click_through(None, False)

    def test_windows_enable_click_through(self) -> None:
        """On Windows, set_click_through(..., True) should call win32 helper."""
        with (
            patch("mochi.utils.platform.sys.platform", "win32"),
            patch("mochi.utils.platform._set_click_through_win32") as mock_set_ct,
        ):
            mock_widget = MagicMock()
            set_click_through(mock_widget, True)
            mock_set_ct.assert_called_once_with(mock_widget, True)

    def test_windows_disable_click_through(self) -> None:
        """On Windows, set_click_through(..., False) should call win32 helper."""
        with (
            patch("mochi.utils.platform.sys.platform", "win32"),
            patch("mochi.utils.platform._set_click_through_win32") as mock_set_ct,
        ):
            mock_widget = MagicMock()
            set_click_through(mock_widget, False)
            mock_set_ct.assert_called_once_with(mock_widget, False)

    def test_macos_does_not_crash(self) -> None:
        """On macOS, set_click_through should be a no-op (no crash)."""
        with patch("mochi.utils.platform.sys.platform", "darwin"):
            mock_widget = MagicMock()
            set_click_through(mock_widget, True)
            set_click_through(mock_widget, False)

    def test_linux_does_not_crash(self) -> None:
        """On Linux, set_click_through should be a no-op (no crash)."""
        with patch("mochi.utils.platform.sys.platform", "linux"):
            mock_widget = MagicMock()
            set_click_through(mock_widget, True)
            set_click_through(mock_widget, False)
