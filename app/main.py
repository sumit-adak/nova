"""NOVA application entry point."""

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.core.config import get_settings
from app.core.logger import setup_logging
from app.ui.main_window import MainWindow


def main() -> int:
    """Launch the NOVA desktop application."""
    settings = get_settings()
    setup_logging(settings.nova_log_level)

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("NOVA")
    app.setOrganizationName("NOVA")
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
