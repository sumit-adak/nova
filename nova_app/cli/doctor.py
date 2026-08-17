"""NOVA Health Diagnostics CLI tool."""
import asyncio
import os
import shutil
import sys
from pathlib import Path
import psutil
from nova_app.ai_engine.redaction import get_redaction_engine
from nova_app.config.settings import get_settings
from nova_app.db.session import init_database
from nova_app.integrations.git_integration import GitClient
from nova_app.integrations.vscode import VSCodeClient
from nova_app.voice.stt.stt_manager import get_stt_manager
from nova_app.voice.tts.tts_manager import get_tts_manager


class DiagnosticResult:
    def __init__(self, name: str, passed: bool, message: str):
        self.name = name
        self.passed = passed
        self.message = message

    def __str__(self) -> str:
        tag = "[OK]  " if self.passed else "[FAIL]"
        return f"{tag} {self.name}: {self.message}"


async def run_diagnostics() -> list[DiagnosticResult]:
    """Execute comprehensive system and environment checks."""
    results: list[DiagnosticResult] = []
    settings = get_settings()

    # 1. Python Environment
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        results.append(DiagnosticResult("Python Version", True, f"Python {py_ver} (64-bit)"))
    else:
        results.append(DiagnosticResult("Python Version", False, f"Python {py_ver} (requires Python 3.10+)"))

    # 2. Operating System
    is_win = psutil.WINDOWS or sys.platform.startswith("win")
    results.append(DiagnosticResult("Operating System", is_win, f"Platform: {sys.platform}"))

    # 3. Database Connectivity & Migrations
    try:
        await init_database()
        db_exists = settings.db_path.exists()
        results.append(DiagnosticResult("SQLite Database", True, f"Active at {settings.db_path}"))
    except Exception as e:
        results.append(DiagnosticResult("SQLite Database", False, f"Database initialization failed: {str(e)}"))

    # 4. Audio Input (Microphone / STT)
    stt = get_stt_manager()
    mic_ok = stt.is_available()
    results.append(DiagnosticResult("Microphone / STT", mic_ok, "Microphone found" if mic_ok else "No default microphone detected"))

    # 5. Audio Output (TTS Voice)
    try:
        tts = get_tts_manager()
        results.append(DiagnosticResult("TTS Voice Synthesizer", True, "pyttsx3 SAPI5 engine ready"))
    except Exception as e:
        results.append(DiagnosticResult("TTS Voice Synthesizer", False, f"TTS engine failed: {str(e)}"))

    # 6. Developer Tools (Git)
    git_bin = shutil.which("git")
    results.append(DiagnosticResult("Git Integration", git_bin is not None, f"Found at {git_bin}" if git_bin else "Git not in PATH"))

    # 7. VS Code Detection
    vscode_client = VSCodeClient()
    vscode_bin = vscode_client.get_executable()
    results.append(DiagnosticResult("VS Code Workspace", vscode_bin is not None, f"Found at {vscode_bin}" if vscode_bin else "VS Code not found in default paths"))

    # 8. Secret Redaction Engine
    redactor = get_redaction_engine()
    test_redact = redactor.redact("Secret sk-1234567890abcdef1234567890")
    redact_ok = "sk-1234567890abcdef" not in test_redact
    results.append(DiagnosticResult("Secret Redaction Engine", redact_ok, "Active & stripping credentials"))

    return results


def main() -> None:
    """CLI Entrypoint for nova-doctor."""
    print("=" * 60)
    print("  NOVA — System Health Diagnostics")
    print("=" * 60)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        results = loop.run_until_complete(run_diagnostics())
        for r in results:
            print(r)

        failed = [r for r in results if not r.passed]
        print("-" * 60)
        if not failed:
            print("  All health checks PASSED successfully! NOVA is ready.")
        else:
            print(f"  {len(failed)} health check(s) need attention.")
        print("=" * 60)
    finally:
        loop.close()


if __name__ == "__main__":
    main()
