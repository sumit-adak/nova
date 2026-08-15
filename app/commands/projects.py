"""Developer project workspace commands."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from app.commands.applications import ApplicationLauncher
from app.commands.registry import ActionResult
from app.core.config import ConfigManager
from app.core.security import validate_path


class ProjectCommands:
    """Launch and manage developer project workspaces."""

    PROJECT_ALIASES: dict[str, str] = {
        "plantguard": "PlantGuard",
        "plantguard-ai": "PlantGuard",
        "plant guard": "PlantGuard",
        "portfolio": "Portfolio",
        "my portfolio": "Portfolio",
        "railway": "Railway",
    }

    def __init__(self, config: ConfigManager, app_launcher: ApplicationLauncher) -> None:
        self.config = config
        self.app_launcher = app_launcher

    def resolve_project(self, name: str) -> str | None:
        """Resolve project alias to canonical name."""
        projects = self.config.load_projects()
        if name in projects:
            return name
        alias = self.PROJECT_ALIASES.get(name.lower().strip())
        if alias and alias in projects:
            return alias
        for key in projects:
            if key.lower() == name.lower():
                return key
        return None

    def get_project_path(self, name: str) -> Path | None:
        """Get configured path for a project."""
        resolved = self.resolve_project(name)
        if not resolved:
            return None
        projects = self.config.load_projects()
        path_str = projects.get(resolved)
        if not path_str:
            return None
        try:
            return validate_path(path_str)
        except Exception:
            return Path(path_str)

    async def launch_project(
        self,
        project_name: str,
        open_editor: bool = True,
        open_terminal: bool = True,
        open_folder: bool = True,
    ) -> ActionResult:
        """Launch a configured developer project workspace."""
        resolved = self.resolve_project(project_name)
        if not resolved:
            return ActionResult(
                success=False,
                message=(
                    f"Project '{project_name}' not found. "
                    "Configure it in Settings > Projects."
                ),
            )

        path = self.get_project_path(resolved)
        if not path:
            return ActionResult(success=False, message=f"Invalid path for project {resolved}.")

        if not path.exists():
            return ActionResult(
                success=False,
                message=(
                    f"Project folder does not exist: {path}. "
                    "Update the path in Settings."
                ),
            )

        settings = self.config.load_settings()
        messages: list[str] = []

        if open_folder:
            os.startfile(path)  # noqa: S606
            messages.append("folder")

        if open_editor:
            editor = settings.get("default_editor", "vscode")
            editor_result = await self.app_launcher.open_application(editor, str(path))
            if editor_result.success:
                messages.append("editor")
            else:
                messages.append(f"editor failed: {editor_result.message}")

        if open_terminal:
            terminal = settings.get("default_terminal", "terminal")
            term_result = await self._open_terminal_in(path, terminal)
            if term_result.success:
                messages.append("terminal")
            else:
                messages.append(f"terminal failed: {term_result.message}")

        return ActionResult(
            success=True,
            message=f"Opening {resolved}.",
            data={"project": resolved, "path": str(path), "opened": messages},
        )

    async def _open_terminal_in(self, path: Path, terminal: str) -> ActionResult:
        """Open terminal in project directory."""
        try:
            if terminal in ("terminal", "wt"):
                subprocess.Popen(
                    ["wt", "-d", str(path)],
                    shell=True,
                )
            elif terminal in ("powershell", "pwsh"):
                subprocess.Popen(
                    ["powershell", "-NoExit", "-Command", f"Set-Location '{path}'"],
                )
            else:
                subprocess.Popen(
                    ["cmd", "/k", f"cd /d {path}"],
                )
            return ActionResult(success=True, message="Terminal opened.")
        except OSError as exc:
            return ActionResult(success=False, message=str(exc))

    async def list_projects(self) -> ActionResult:
        """List configured projects."""
        projects = self.config.load_projects()
        if not projects:
            return ActionResult(success=True, message="No projects configured.")
        names = ", ".join(projects.keys())
        return ActionResult(
            success=True,
            message=f"Configured projects: {names}",
            data={"projects": projects},
        )
