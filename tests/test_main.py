"""Tests for mochi.main and mochi.__main__."""

from unittest.mock import patch

from mochi import main


class TestMain:
    """Tests for the main module."""

    @patch("mochi.main.QApplication")
    @patch("mochi.main.setup_logging")
    def test_create_application_returns_qapplication(
        self, mock_logging: object, mock_qapp: object
    ) -> None:
        """create_application() should return a QApplication instance."""
        app = main.create_application()
        assert app is not None

    @patch("mochi.main.QApplication")
    @patch("mochi.main.setup_logging")
    def test_application_name_is_mochi(
        self, mock_logging: object, mock_qapp: object
    ) -> None:
        """Application name should be 'Mochi'."""
        app = main.create_application()
        assert app is not None
        main.QApplication.setApplicationName.assert_called_once_with("Mochi")

    @patch("mochi.main.QApplication")
    @patch("mochi.main.setup_logging")
    def test_logging_initialized(
        self, mock_logging: object, mock_qapp: object
    ) -> None:
        """setup_logging should be called during initialization."""
        main.create_application()
        mock_logging.assert_called_once()
