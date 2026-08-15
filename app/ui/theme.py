"""NOVA UI theme constants and styles."""

# Colors
BG_PRIMARY = "#0A0A0F"
BG_SECONDARY = "#12121A"
BG_CARD = "#1A1A24"
BG_GLASS = "rgba(26, 26, 36, 180)"

ACCENT_PURPLE = "#9B59B6"
ACCENT_ORANGE = "#E67E22"
ACCENT_PURPLE_GLOW = "#BB6BD9"
ACCENT_ORANGE_GLOW = "#F39C12"

TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#A0A0B0"
TEXT_MUTED = "#606070"

BORDER = "#2A2A3A"
SUCCESS = "#2ECC71"
ERROR = "#E74C3C"
WARNING = "#F1C40F"

# State colors
STATE_COLORS = {
    "idle": TEXT_SECONDARY,
    "listening": ACCENT_ORANGE,
    "thinking": ACCENT_PURPLE,
    "executing": ACCENT_PURPLE_GLOW,
    "success": SUCCESS,
    "error": ERROR,
    "confirmation_required": WARNING,
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_PRIMARY};
    color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}}

QScrollBar:vertical {{
    background: {BG_SECONDARY};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {ACCENT_PURPLE};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QPushButton {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {BG_SECONDARY};
    border-color: {ACCENT_PURPLE};
}}
QPushButton:pressed {{
    background-color: {ACCENT_PURPLE};
}}

QPushButton#primaryBtn {{
    background-color: {ACCENT_PURPLE};
    border: none;
    color: white;
    font-weight: 600;
}}
QPushButton#primaryBtn:hover {{
    background-color: {ACCENT_PURPLE_GLOW};
}}

QPushButton#dangerBtn {{
    background-color: {ERROR};
    border: none;
    color: white;
}}
QPushButton#dangerBtn:hover {{
    background-color: #C0392B;
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px;
    selection-background-color: {ACCENT_PURPLE};
}}

QListWidget {{
    background-color: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    padding: 8px;
    border-radius: 6px;
}}
QListWidget::item:selected {{
    background-color: {BG_CARD};
    color: {ACCENT_PURPLE_GLOW};
}}

QLabel#titleLabel {{
    font-size: 28px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}

QLabel#subtitleLabel {{
    font-size: 14px;
    color: {TEXT_SECONDARY};
}}

QLabel#navLabel {{
    font-size: 13px;
    color: {TEXT_SECONDARY};
    padding: 10px 16px;
    border-radius: 8px;
}}
QLabel#navLabel:hover {{
    color: {TEXT_PRIMARY};
    background-color: {BG_CARD};
}}
QLabel#navLabelActive {{
    font-size: 13px;
    color: {ACCENT_PURPLE_GLOW};
    padding: 10px 16px;
    border-radius: 8px;
    background-color: {BG_CARD};
    border-left: 3px solid {ACCENT_PURPLE};
}}

QTabWidget::pane {{
    border: none;
    background: transparent;
}}
QTabBar::tab {{
    background: {BG_CARD};
    color: {TEXT_SECONDARY};
    padding: 8px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {BG_SECONDARY};
    color: {ACCENT_PURPLE_GLOW};
}}

QProgressBar {{
    background-color: {BG_SECONDARY};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_PURPLE}, stop:1 {ACCENT_ORANGE});
    border-radius: 4px;
}}
"""
