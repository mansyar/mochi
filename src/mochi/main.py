"""Application entry point for Mochi.

Bootstraps the Qt ``QApplication``, initializes logging, and runs
the event loop.
"""

import logging
import sys

from PySide6.QtWidgets import QApplication

from mochi.utils.logger import setup_logging


def create_application() -> QApplication:
    """Create and configure the Qt application instance.

    Sets organization and application metadata, initialises logging,
    and returns the ``QApplication`` singleton.

    Returns
    -------
    QApplication
        The configured application instance.
    """
    setup_logging()

    app = QApplication(sys.argv)
    app.setOrganizationName("Mochi")
    app.setApplicationName("Mochi")

    return app


def main() -> None:
    """Main entry point — called from ``python -m mochi``.

    Creates the application, logs a startup message, and enters the
    Qt event loop.
    """
    app = create_application()

    logger = logging.getLogger("mochi")
    logger.info("Mochi started")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
