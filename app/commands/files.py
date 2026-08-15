"""File and folder operation commands."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from app.commands.registry import ActionResult
from app.core.security import SecurityError, sanitize_filename, validate_path


class FileCommands:
    """Safe file and folder operations."""

    async def open_folder(self, path: str) -> ActionResult:
        """Open a folder in File Explorer."""
        try:
            resolved = validate_path(path, must_exist=True)
            if not resolved.is_dir():
                return ActionResult(success=False, message=f"Not a folder: {path}")
            os.startfile(resolved)  # noqa: S606 - Windows-specific
            return ActionResult(success=True, message=f"Opened folder: {resolved.name}")
        except SecurityError as exc:
            return ActionResult(success=False, message=str(exc))

    async def open_file(self, path: str) -> ActionResult:
        """Open a file with its default application."""
        try:
            resolved = validate_path(path, must_exist=True)
            if not resolved.is_file():
                return ActionResult(success=False, message=f"Not a file: {path}")
            os.startfile(resolved)  # noqa: S606
            return ActionResult(success=True, message=f"Opened file: {resolved.name}")
        except SecurityError as exc:
            return ActionResult(success=False, message=str(exc))

    async def create_folder(self, path: str) -> ActionResult:
        """Create a new folder."""
        try:
            resolved = validate_path(path)
            resolved.mkdir(parents=True, exist_ok=True)
            return ActionResult(success=True, message=f"Created folder: {resolved}")
        except SecurityError as exc:
            return ActionResult(success=False, message=str(exc))
        except OSError as exc:
            return ActionResult(success=False, message=f"Failed to create folder: {exc}")

    async def create_file(self, path: str, content: str = "") -> ActionResult:
        """Create a new file with optional content."""
        try:
            resolved = validate_path(path)
            sanitize_filename(resolved.name)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
            return ActionResult(success=True, message=f"Created file: {resolved.name}")
        except SecurityError as exc:
            return ActionResult(success=False, message=str(exc))
        except OSError as exc:
            return ActionResult(success=False, message=f"Failed to create file: {exc}")

    async def delete_folder(self, path: str) -> ActionResult:
        """Delete a folder (requires confirmation)."""
        try:
            resolved = validate_path(path, must_exist=True)
            if not resolved.is_dir():
                return ActionResult(success=False, message=f"Not a folder: {path}")
            return ActionResult(
                success=False,
                requires_confirmation=True,
                confirmation_message=(
                    f"This action will permanently delete {resolved}. Continue?"
                ),
                data={"path": str(resolved), "action": "delete_folder_confirmed"},
            )
        except SecurityError as exc:
            return ActionResult(success=False, message=str(exc))

    async def delete_folder_confirmed(self, path: str) -> ActionResult:
        """Execute folder deletion after confirmation."""
        try:
            import shutil

            resolved = validate_path(path, must_exist=True)
            shutil.rmtree(resolved)
            return ActionResult(success=True, message=f"Deleted folder: {resolved.name}")
        except SecurityError as exc:
            return ActionResult(success=False, message=str(exc))
        except OSError as exc:
            return ActionResult(success=False, message=f"Failed to delete: {exc}")

    async def delete_file(self, path: str) -> ActionResult:
        """Delete a file (requires confirmation)."""
        try:
            resolved = validate_path(path, must_exist=True)
            if not resolved.is_file():
                return ActionResult(success=False, message=f"Not a file: {path}")
            return ActionResult(
                success=False,
                requires_confirmation=True,
                confirmation_message=(
                    f"This action will permanently delete {resolved.name}. Continue?"
                ),
                data={"path": str(resolved), "action": "delete_file_confirmed"},
            )
        except SecurityError as exc:
            return ActionResult(success=False, message=str(exc))

    async def delete_file_confirmed(self, path: str) -> ActionResult:
        """Execute file deletion after confirmation."""
        try:
            resolved = validate_path(path, must_exist=True)
            resolved.unlink()
            return ActionResult(success=True, message=f"Deleted file: {resolved.name}")
        except SecurityError as exc:
            return ActionResult(success=False, message=str(exc))
        except OSError as exc:
            return ActionResult(success=False, message=f"Failed to delete: {exc}")

    async def read_file(self, path: str) -> ActionResult:
        """Read and return content of a file."""
        try:
            p = Path(path)
            if not p.is_absolute():
                from app.core.config import BASE_DIR
                p = BASE_DIR / path
            resolved = validate_path(p, must_exist=True)
            if not resolved.is_file():
                return ActionResult(success=False, message=f"Not a file: {path}")
            content = resolved.read_text(encoding="utf-8", errors="replace")
            preview = content[:500] + ("..." if len(content) > 500 else "")
            return ActionResult(
                success=True,
                message=f"Read {resolved.name} ({len(content)} chars):\n{preview}",
                data={"path": str(resolved), "content": content},
            )
        except SecurityError as exc:
            return ActionResult(success=False, message=str(exc))
        except OSError as exc:
            return ActionResult(success=False, message=f"Failed to read file: {exc}")

    async def edit_file(
        self,
        path: str,
        content: str = "",
        mode: str = "append",
        search: str = "",
        replace: str = "",
    ) -> ActionResult:
        """Edit or update a file (supports append, overwrite, search-and-replace)."""
        try:
            p = Path(path)
            if not p.is_absolute():
                from app.core.config import BASE_DIR
                p = BASE_DIR / path

            resolved = validate_path(p)
            sanitize_filename(resolved.name)
            resolved.parent.mkdir(parents=True, exist_ok=True)

            existing = ""
            if resolved.exists():
                existing = resolved.read_text(encoding="utf-8", errors="replace")

            mode_lower = mode.lower().strip()
            if mode_lower == "overwrite":
                new_content = content
            elif mode_lower == "replace" and search:
                new_content = existing.replace(search, replace or content)
            elif mode_lower == "append":
                separator = "\n" if existing and not existing.endswith("\n") else ""
                new_content = existing + separator + content
            else:
                # Default: if file exists and content given, append; else write
                if existing and content:
                    separator = "\n" if not existing.endswith("\n") else ""
                    new_content = existing + separator + content
                else:
                    new_content = content or existing

            resolved.write_text(new_content, encoding="utf-8")
            return ActionResult(
                success=True,
                message=f"Updated {resolved.name} ({mode_lower}).",
                data={"path": str(resolved), "mode": mode_lower},
            )
        except SecurityError as exc:
            return ActionResult(success=False, message=str(exc))
        except OSError as exc:
            return ActionResult(success=False, message=f"Failed to edit file: {exc}")

