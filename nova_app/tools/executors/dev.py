"""Developer workflow executors (projects, Git, terminal)."""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from nova_app.integrations.git_integration import get_git_client
from nova_app.integrations.vscode import get_vscode_client
from nova_app.tools.validators.path_validator import get_path_validator


class OpenProjectArgs(BaseModel):
    project_path: str = Field(description="Path or directory of the project to open")
    open_terminal_too: bool = Field(default=True, description="Whether to launch a terminal window in the directory")


class OpenTerminalArgs(BaseModel):
    path: str | None = Field(default=None, description="Directory to open the terminal in (defaults to home or current)")


class GitStatusArgs(BaseModel):
    repo_path: str | None = Field(default=None, description="Path to git repository (defaults to active project)")


class GitCommitArgs(BaseModel):
    message: str = Field(description="Commit message describing changes")
    repo_path: str | None = Field(default=None, description="Path to git repository")
    stage_all: bool = Field(default=True, description="Stage all modified and untracked files before committing")


class GitPushArgs(BaseModel):
    remote: str = Field(default="origin", description="Target remote name (e.g. origin)")
    branch: str | None = Field(default=None, description="Branch to push (defaults to active branch)")
    repo_path: str | None = Field(default=None, description="Path to git repository")


def open_terminal_executor(args: OpenTerminalArgs) -> dict[str, Any]:
    """Launch Windows Terminal / PowerShell at the target directory."""
    validator = get_path_validator()
    target = validator.validate_path(args.path) if args.path else Path.home()

    # Look for Windows Terminal (wt.exe), powershell.exe, or cmd.exe
    wt = shutil.which("wt.exe")
    if wt:
        subprocess.Popen([wt, "-d", str(target)], shell=False)
        terminal_bin = "wt.exe"
    else:
        subprocess.Popen(["powershell.exe", "-NoExit", "-Command", f"Set-Location '{target}'"], shell=False)
        terminal_bin = "powershell.exe"

    return {
        "status": "launched_terminal",
        "directory": str(target),
        "terminal": terminal_bin,
    }


def open_project_executor(args: OpenProjectArgs) -> dict[str, Any]:
    """Open project workspace in VS Code and optional terminal."""
    vscode = get_vscode_client()
    res = vscode.open_workspace(args.project_path)

    if args.open_terminal_too:
        open_terminal_executor(OpenTerminalArgs(path=args.project_path))

    return {
        "status": "project_opened",
        "path": res["path"],
        "ide": "vscode",
    }


def git_status_executor(args: GitStatusArgs) -> dict[str, Any]:
    """Inspect Git status."""
    git_client = get_git_client()
    return git_client.get_status(args.repo_path)


def git_commit_executor(args: GitCommitArgs) -> dict[str, Any]:
    """Commit changes in the Git repository."""
    git_client = get_git_client()
    return git_client.commit(message=args.message, repo_path=args.repo_path, stage_all=args.stage_all)


def git_push_executor(args: GitPushArgs) -> dict[str, Any]:
    """Push local Git commits to remote repository."""
    git_client = get_git_client()
    return git_client.push(remote_name=args.remote, branch_name=args.branch, repo_path=args.repo_path)
