"""Application launch and discovery executors for Windows."""
import os
import shutil
import subprocess
from typing import Any
from pydantic import BaseModel, Field

KNOWN_APPS: dict[str, list[str]] = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "vscode": ["code.cmd", "code.exe", "code"],
    "code": ["code.cmd", "code.exe", "code"],
    "chrome": [
        "chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ],
    "edge": [
        "msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "explorer": ["explorer.exe"],
    "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
    "cmd": ["cmd.exe"],
    "powershell": ["powershell.exe"],
}


class OpenApplicationArgs(BaseModel):
    app_name: str = Field(description="Name or executable of the application to open")


class ListApplicationsArgs(BaseModel):
    filter_query: str | None = Field(default=None, description="Optional substring to filter applications")


def open_application_executor(args: OpenApplicationArgs) -> dict[str, Any]:
    """Open an installed Windows application safely."""
    app_key = args.app_name.lower().strip()

    # 1. Check known aliases
    candidate_paths = KNOWN_APPS.get(app_key, [args.app_name])

    for target in candidate_paths:
        # If in PATH or absolute executable exists
        found_bin = shutil.which(target) or (target if os.path.isfile(target) else None)
        if found_bin:
            subprocess.Popen([found_bin], shell=False)
            return {
                "status": "launched",
                "app_name": args.app_name,
                "executable": found_bin,
            }

    # 2. Try directly running via os.startfile for Windows protocols / shell items
    try:
        os.startfile(args.app_name)
        return {
            "status": "launched",
            "app_name": args.app_name,
            "method": "startfile",
        }
    except Exception as e:
        raise ValueError(f"Could not find or launch application '{args.app_name}': {str(e)}")


def list_applications_executor(args: ListApplicationsArgs) -> dict[str, Any]:
    """List available common applications and known targets."""
    apps = list(KNOWN_APPS.keys())
    if args.filter_query:
        q = args.filter_query.lower()
        apps = [a for a in apps if q in a]

    return {
        "count": len(apps),
        "applications": apps,
    }
