"""Windows 11 Dark Glassmorphic Theme & Stylesheet for NOVA."""

DARK_THEME_QSS = """
/* Global Window Styling */
QMainWindow, QDialog, QWidget#centralWidget {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: "Segoe UI", "Inter", -apple-system, sans-serif;
    font-size: 13px;
}

/* Glassmorphic Cards & Panels */
QFrame.glassCard, QWidget.glassCard {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px;
}

/* Header & Status Bar */
QFrame#topBar {
    background-color: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 8px 16px;
}

/* Chat & Activity View */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollBar:vertical {
    border: none;
    background: #0d1117;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #58a6ff;
}

/* Inputs & Textboxes */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #f0f6fc;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #1f6feb;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #58a6ff;
}

/* Buttons */
QPushButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #c9d1d9;
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
    color: #f0f6fc;
}
QPushButton:pressed {
    background-color: #161b22;
}

QPushButton.primaryButton {
    background-color: #238636;
    border: 1px solid rgba(240, 246, 252, 0.1);
    color: #ffffff;
    font-weight: 600;
}
QPushButton.primaryButton:hover {
    background-color: #2ea043;
}

QPushButton.dangerButton {
    background-color: #da3633;
    border: 1px solid rgba(240, 246, 252, 0.1);
    color: #ffffff;
    font-weight: 600;
}
QPushButton.dangerButton:hover {
    background-color: #f85149;
}

/* Status Pill */
QLabel#statusPill {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 4px 10px;
    font-size: 11px;
    color: #8b949e;
}

/* Labels */
QLabel {
    color: #c9d1d9;
}
QLabel.titleLabel {
    font-size: 16px;
    font-weight: 600;
    color: #f0f6fc;
}
"""


def apply_theme(app) -> None:
    """Apply modern dark stylesheet to the QApplication."""
    app.setStyleSheet(DARK_THEME_QSS)
