"""Tests for mochi.main and mochi.__main__."""

from unittest.mock import MagicMock, patch

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
        app.setApplicationName.assert_called_once_with("Mochi")

    @patch("mochi.main.QApplication")
    @patch("mochi.main.setup_logging")
    def test_logging_initialized(
        self, mock_logging: object, mock_qapp: object
    ) -> None:
        """setup_logging should be called during initialization."""
        main.create_application()
        mock_logging.assert_called_once()


class TestMainIntegration:
    """Tests for main() integration with Canvas."""

    @patch("mochi.main.QApplication")
    @patch("mochi.main.setup_logging")
    @patch("mochi.main.Canvas")
    @patch("mochi.main.QTimer")
    @patch("mochi.main.sys")
    def test_main_creates_canvas_and_shows_it(
        self,
        mock_sys: MagicMock,
        mock_qtimer: MagicMock,
        mock_canvas_cls: MagicMock,
        mock_logging: object,
        mock_qapp: object,
    ) -> None:
        """main() should instantiate Canvas and call .show()."""
        main.main()
        mock_canvas_cls.assert_called_once()
        mock_canvas_cls.return_value.show.assert_called_once()

    @patch("mochi.main.QApplication")
    @patch("mochi.main.setup_logging")
    @patch("mochi.main.Canvas")
    @patch("mochi.main.QTimer")
    @patch("mochi.main.sys")
    def test_canvas_dimensions_logged(
        self,
        mock_sys: MagicMock,
        mock_qtimer: MagicMock,
        mock_canvas_cls: MagicMock,
        mock_logging: object,
        mock_qapp: object,
    ) -> None:
        """main() should log Canvas dimensions at INFO level."""
        mock_canvas = MagicMock()
        mock_canvas.width.return_value = 1920
        mock_canvas.height.return_value = 1080
        mock_canvas_cls.return_value = mock_canvas

        with patch("mochi.main.logging.getLogger") as mock_get_logger:
            mock_mochi_logger = MagicMock()
            mock_get_logger.return_value = mock_mochi_logger
            main.main()

            info_calls = [
                c for c in mock_mochi_logger.info.call_args_list
                if "Canvas created" in str(c)
            ]
            assert len(info_calls) > 0

    @patch("mochi.main.QApplication")
    @patch("mochi.main.setup_logging")
    @patch("mochi.main.Canvas")
    @patch("mochi.main.QTimer")
    @patch("mochi.main.sys")
    def test_set_click_through_called_via_timer(
        self,
        mock_sys: MagicMock,
        mock_qtimer: MagicMock,
        mock_canvas_cls: MagicMock,
        mock_logging: object,
        mock_qapp: object,
    ) -> None:
        """main() should schedule set_click_through via QTimer.singleShot."""
        main.main()
        # Verify QTimer.singleShot was called with 0 and a callable
        mock_qtimer.singleShot.assert_called_once()
        args, _ = mock_qtimer.singleShot.call_args
        assert args[0] == 0
        assert callable(args[1])
