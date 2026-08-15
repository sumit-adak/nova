# NOVA - Windows AI Desktop Assistant

NOVA is a production-quality, futuristic AI-powered desktop assistant for Windows 11. It understands natural language and voice commands, safely executes registered system actions, monitors your hardware in real time, and integrates with your developer workflow.

## Features

- **Natural language commands** — Open apps, folders, projects, search the web, check system stats
- **Voice interaction** — Push-to-talk microphone with offline text-to-speech responses
- **Safe command engine** — AI maps intent to registered actions; no arbitrary shell execution
- **Confirmation system** — Destructive actions require explicit user approval
- **Developer workflow** — Launch project workspaces (VS Code + terminal + folder)
- **System monitoring** — Real-time CPU, RAM, GPU, disk, network, battery
- **Activity log** — Full history of commands, intents, and results
- **Local memory** — Store preferences (never API keys or passwords)
- **Offline mode** — Local commands work without an AI API key
- **Multi-provider AI** — OpenAI, Google Gemini, or offline pattern matching
- **Premium dark UI** — Futuristic glassmorphism design with smooth animations

## Screenshots

> Placeholder — run NOVA and capture screenshots of Dashboard, Chat, System Monitor, and Settings.

## Architecture

```
User Input (text/voice)
        │
        ▼
  Intent Parser (AI or offline rules)
        │
        ▼
  Command Registry (approved actions only)
        │
        ▼
  Action Execution + Safety Checks
        │
        ▼
  Response (UI + TTS + Activity Log)
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `app/core/` | Config, logging, security, state management |
| `app/ai/` | Provider abstraction, intent parsing, prompts |
| `app/commands/` | Registered safe actions (apps, files, system, etc.) |
| `app/voice/` | Speech-to-text and text-to-speech |
| `app/system_monitor/` | Real-time hardware metrics |
| `app/memory/` | SQLite preferences storage |
| `app/ui/` | PySide6 desktop interface |
| `app/services/` | Assistant orchestration |

## Requirements

- Windows 11 (Windows 10 also supported)
- Python 3.11
- Microphone (optional, for voice)
- OpenAI or Gemini API key (optional, for AI chat)

## Installation

```powershell
cd C:\Users\SUMIT ADAK\Projects\NOVA

python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt
```

### Environment Variables

Copy the example env file and configure:

```powershell
copy .env.example .env
```

Edit `.env`:

```env
NOVA_AI_PROVIDER=offline
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
NOVA_LOG_LEVEL=INFO
NOVA_DEFAULT_BROWSER=chrome
NOVA_VOICE_ENABLED=true
NOVA_TTS_ENABLED=true
```

## Running NOVA

```powershell
.venv\Scripts\activate
python -m app.main
```

The application launches as a desktop window with no terminal required.

## Example Commands

| Command | Action |
|---------|--------|
| "Open VS Code" | Launches Visual Studio Code |
| "Open my PlantGuard project" | Opens VS Code, folder, and terminal |
| "What's my RAM usage?" | Reports memory statistics |
| "Search for TensorFlow image classification" | Opens Google search |
| "Take a screenshot" | Saves screenshot to `data/screenshots/` |
| "Open GitHub" | Opens github.com |
| "Show my system stats" | Displays system information |
| "Set volume to 50" | Adjusts system volume |
| "Start timer for 300 seconds" | Starts a countdown timer |

## Configuring PlantGuard-AI

1. Open NOVA → **Settings** → **Projects** tab
2. Set the path:

```json
{
  "PlantGuard": "C:\\Users\\SUMIT ADAK\\Desktop\\PlantGuard-AI"
}
```

3. Click **Save Settings**
4. Say or type: **"Open PlantGuard"**

NOVA will open VS Code, the project folder in File Explorer, and a terminal in that directory.

## Configuring Applications

Go to **Settings → Applications** to add or override app paths:

```json
{
  "vscode": {
    "name": "Visual Studio Code",
    "paths": ["C:\\Users\\You\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"]
  }
}
```

If an app isn't found, NOVA shows a helpful error directing you to Settings.

## Voice Setup

1. Ensure a microphone is connected
2. Install PyAudio: `pip install PyAudio`
3. Enable voice in Settings or `.env`
4. Click the microphone button on the Dashboard (push-to-talk)
5. Speak your command — NOVA transcribes, executes, and speaks the response

Wake word ("Hey Nova") architecture is designed for future addition. Currently uses push-to-talk only.

## AI Provider Setup

### OpenAI

```env
NOVA_AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
```

### Google Gemini

```env
NOVA_AI_PROVIDER=gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-1.5-flash
```

### Offline (no API key)

```env
NOVA_AI_PROVIDER=offline
```

Offline mode supports pattern-matched commands for apps, system stats, projects, search, and more.

## Security Model

- **No arbitrary shell execution** — AI output maps to registered functions only
- **Confirmation required** for delete, shutdown, restart, kill process, run scripts
- **Path validation** — Prevents directory traversal attacks
- **No secrets in memory** — API keys loaded from `.env` only
- **Input sanitization** — All file paths and URLs validated before use
- **Structured logging** — Sensitive data never logged (`logs/nova.log`)

## Testing

```powershell
.venv\Scripts\activate
pytest tests/ -v
```

Tests cover: command registry, intent parsing, application detection, path validation, memory, system monitoring, safety confirmation, configuration, and AI provider abstraction. No API key required.

## Building NOVA.exe

```powershell
build_windows.bat
```

Or manually:

```powershell
.venv\Scripts\activate
pip install pyinstaller
pyinstaller nova.spec --clean --noconfirm
```

Output: `dist/NOVA.exe` — launches without a terminal window.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| PyAudio install fails | `pip install pipwin && pipwin install pyaudio` |
| VS Code not found | Configure path in Settings → Applications |
| Microphone not working | Check Windows privacy settings for microphone access |
| GPU metrics N/A | Normal on systems without NVIDIA GPU or GPUtil |
| AI unavailable | Local commands still work in offline mode |
| Volume control fails | Run `pip install pycaw comtypes` |

## Future Improvements

- Wake word detection ("Hey Nova")
- Plugin system for custom commands
- Multi-monitor screenshot support
- System tray minimization
- Custom themes and accent colors
- Cloud sync for preferences (opt-in)
- FastAPI local API for external integrations

## License

MIT — use freely for personal and commercial projects.

## Updates
- Recent updates and documentation improvements.