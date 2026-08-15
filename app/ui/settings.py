"""Settings page."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QScrollArea, QFrame, QTabWidget, QTextEdit,
)

from app.ui.theme import BG_CARD, TEXT_SECONDARY
from app.core.config import ConfigManager, get_settings


class SettingsPage(QWidget):
    """Application settings configuration."""

    settings_saved = Signal()
    memory_cleared = Signal()

    def __init__(self, config: ConfigManager | None = None, parent=None):
        super().__init__(parent)
        self.config = config or ConfigManager()
        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)

        title = QLabel("Settings")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._general_tab(), "General")
        tabs.addTab(self._ai_tab(), "AI Provider")
        tabs.addTab(self._projects_tab(), "Projects")
        tabs.addTab(self._apps_tab(), "Applications")
        tabs.addTab(self._memory_tab(), "Memory")
        layout.addWidget(tabs)

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

    def _general_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        self.preferred_name = QLineEdit()
        self.voice_enabled = QCheckBox("Voice input enabled")
        self.tts_enabled = QCheckBox("Text-to-speech enabled")
        self.wake_word = QCheckBox("Wake word (future - currently push-to-talk)")
        self.wake_word.setEnabled(False)
        self.default_browser = QComboBox()
        self.default_browser.addItems(["chrome", "edge", "firefox"])
        self.default_editor = QComboBox()
        self.default_editor.addItems(["vscode"])
        self.default_terminal = QComboBox()
        self.default_terminal.addItems(["terminal", "powershell"])

        for label, widget in [
            ("Preferred name", self.preferred_name),
            ("Default browser", self.default_browser),
            ("Default editor", self.default_editor),
            ("Default terminal", self.default_terminal),
        ]:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)
        layout.addWidget(self.voice_enabled)
        layout.addWidget(self.tts_enabled)
        layout.addWidget(self.wake_word)
        layout.addStretch()
        return w

    def _ai_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        self.ai_provider = QComboBox()
        self.ai_provider.addItems(["offline", "openai", "gemini"])
        env = get_settings()
        self.api_status = QLabel()
        self._update_api_status(env)
        layout.addWidget(QLabel("AI Provider"))
        layout.addWidget(self.ai_provider)
        layout.addWidget(self.api_status)
        note = QLabel(
            "API keys are loaded from .env file (never stored in app memory).\n"
            "Set OPENAI_API_KEY or GEMINI_API_KEY in your .env file."
        )
        note.setStyleSheet(f"color: {TEXT_SECONDARY};")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()
        return w

    def _projects_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Projects (JSON format: name = path)"))
        self.projects_edit = QTextEdit()
        self.projects_edit.setPlaceholderText('{\n  "PlantGuard": "C:\\\\Users\\\\You\\\\Desktop\\\\PlantGuard-AI"\n}')
        layout.addWidget(self.projects_edit)
        return w

    def _apps_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Custom application paths (JSON)"))
        self.apps_edit = QTextEdit()
        layout.addWidget(self.apps_edit)
        note = QLabel("Add or override app paths. Each app needs 'name' and 'paths' array.")
        note.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(note)
        return w

    def _memory_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        self.memory_list = QTextEdit()
        self.memory_list.setReadOnly(True)
        layout.addWidget(QLabel("Stored preferences (no secrets)"))
        layout.addWidget(self.memory_list)
        clear_btn = QPushButton("Clear All Memory")
        clear_btn.setObjectName("dangerBtn")
        clear_btn.clicked.connect(self.memory_cleared.emit)
        layout.addWidget(clear_btn)
        return w

    def _update_api_status(self, env) -> None:
        openai_ok = "configured" if env.openai_api_key else "not set"
        gemini_ok = "configured" if env.gemini_api_key else "not set"
        self.api_status.setText(
            f"OpenAI key: {openai_ok} | Gemini key: {gemini_ok} | "
            f"Active provider: {env.nova_ai_provider}"
        )

    def _load_settings(self) -> None:
        import json
        settings = self.config.load_settings()
        self.preferred_name.setText(settings.get("preferred_name", ""))
        self.voice_enabled.setChecked(settings.get("voice_enabled", True))
        self.tts_enabled.setChecked(settings.get("tts_enabled", True))
        browser = settings.get("default_browser", "chrome")
        idx = self.default_browser.findText(browser)
        if idx >= 0:
            self.default_browser.setCurrentIndex(idx)
        editor = settings.get("default_editor", "vscode")
        idx = self.default_editor.findText(editor)
        if idx >= 0:
            self.default_editor.setCurrentIndex(idx)
        terminal = settings.get("default_terminal", "terminal")
        idx = self.default_terminal.findText(terminal)
        if idx >= 0:
            self.default_terminal.setCurrentIndex(idx)

        env = get_settings()
        idx = self.ai_provider.findText(env.nova_ai_provider)
        if idx >= 0:
            self.ai_provider.setCurrentIndex(idx)

        projects = self.config.load_projects()
        self.projects_edit.setPlainText(json.dumps(projects, indent=2))
        apps = self.config.load_applications()
        self.apps_edit.setPlainText(json.dumps(apps, indent=2))

    def _save(self) -> None:
        import json
        settings = self.config.load_settings()
        settings.update({
            "preferred_name": self.preferred_name.text(),
            "voice_enabled": self.voice_enabled.isChecked(),
            "tts_enabled": self.tts_enabled.isChecked(),
            "default_browser": self.default_browser.currentText(),
            "default_editor": self.default_editor.currentText(),
            "default_terminal": self.default_terminal.currentText(),
        })
        self.config.save_settings(settings)

        try:
            projects = json.loads(self.projects_edit.toPlainText())
            self.config.save_projects(projects)
        except json.JSONDecodeError:
            pass

        try:
            apps = json.loads(self.apps_edit.toPlainText())
            self.config.save_applications(apps)
        except json.JSONDecodeError:
            pass

        self.settings_saved.emit()

    def refresh_memory(self, items: list[dict]) -> None:
        if not items:
            self.memory_list.setPlainText("No stored preferences.")
            return
        lines = [f"{i['key']}: {i['value']} ({i['category']})" for i in items]
        self.memory_list.setPlainText("\n".join(lines))
