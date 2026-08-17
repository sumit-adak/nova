"""Settings configuration dialog for NOVA."""
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
)
from PySide6.QtCore import Qt
from nova_app.config.settings import Settings, get_settings


class SettingsDialog(QDialog):
    """Preferences and configuration modal."""

    def __init__(self, parent=None, settings: Settings | None = None):
        super().__init__(parent)
        self.settings = settings or get_settings()
        self.setWindowTitle("NOVA Settings")
        self.setMinimumSize(480, 360)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        title = QLabel("Application Settings", self)
        title.setProperty("class", "titleLabel")
        main_layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        # AI Provider
        self.combo_ai_provider = QComboBox(self)
        self.combo_ai_provider.addItems(["offline", "openai", "gemini", "anthropic", "local"])
        self.combo_ai_provider.setCurrentText(self.settings.ai_provider)
        form.addRow("AI Provider:", self.combo_ai_provider)

        # OpenAI API Key
        self.txt_openai_key = QLineEdit(self)
        self.txt_openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_openai_key.setText(self.settings.openai_api_key or "")
        form.addRow("OpenAI API Key:", self.txt_openai_key)

        # Gemini API Key
        self.txt_gemini_key = QLineEdit(self)
        self.txt_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_gemini_key.setText(self.settings.gemini_api_key or "")
        form.addRow("Gemini API Key:", self.txt_gemini_key)

        # Default Browser
        self.combo_browser = QComboBox(self)
        self.combo_browser.addItems(["chrome", "edge", "firefox", "default"])
        self.combo_browser.setCurrentText(self.settings.default_browser)
        form.addRow("Default Browser:", self.combo_browser)

        # Voice Rate
        self.slider_voice_rate = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_voice_rate.setRange(100, 250)
        self.slider_voice_rate.setValue(self.settings.voice_rate)
        form.addRow("Voice Speed (WPM):", self.slider_voice_rate)

        main_layout.addLayout(form)
        main_layout.addStretch()

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save Settings", self)
        self.btn_save.setProperty("class", "primaryButton")
        self.btn_save.clicked.connect(self._save_and_accept)
        btn_layout.addWidget(self.btn_save)

        main_layout.addLayout(btn_layout)

    def _save_and_accept(self) -> None:
        self.settings.ai_provider = self.combo_ai_provider.currentText()
        self.settings.openai_api_key = self.txt_openai_key.text() or None
        self.settings.gemini_api_key = self.txt_gemini_key.text() or None
        self.settings.default_browser = self.combo_browser.currentText()
        self.settings.voice_rate = self.slider_voice_rate.value()
        self.accept()
