"""File and folder executors for NOVA."""
import os
import subprocess
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from nova_app.tools.validators.path_validator import get_path_validator


class OpenFileArgs(BaseModel):
    path: str = Field(description="Absolute or relative file path to open")


class OpenFolderArgs(BaseModel):
    path: str = Field(description="Absolute or relative folder path to open in Windows Explorer")


class SearchFilesArgs(BaseModel):
    query: str = Field(description="Filename or substring to search for")
    root_directory: str | None = Field(default=None, description="Root folder to search within")
    max_results: int = Field(default=20, description="Max number of results to return")


class GetFileInfoArgs(BaseModel):
    path: str = Field(description="File path to inspect")


def open_file_executor(args: OpenFileArgs) -> dict[str, Any]:
    """Open a file with its default Windows application."""
    validator = get_path_validator()
    valid_path = validator.validate_path(args.path)

    if not valid_path.is_file():
        raise ValueError(f"Target '{valid_path}' is not a regular file.")

    os.startfile(str(valid_path))
    return {
        "status": "opened",
        "path": str(valid_path),
        "name": valid_path.name,
        "size_bytes": valid_path.stat().st_size,
    }


def open_folder_executor(args: OpenFolderArgs) -> dict[str, Any]:
    """Open a folder in Windows Explorer."""
    validator = get_path_validator()
    valid_path = validator.validate_path(args.path)

    if not valid_path.is_dir():
        raise ValueError(f"Target '{valid_path}' is not a directory.")

    subprocess.Popen(["explorer.exe", str(valid_path)])
    return {
        "status": "opened",
        "path": str(valid_path),
        "name": valid_path.name,
    }


def search_files_executor(args: SearchFilesArgs) -> dict[str, Any]:
    """Search for files by name within allowed directories."""
    validator = get_path_validator()
    search_root = (
        validator.validate_path(args.root_directory)
        if args.root_directory
        else Path.home()
    )

    query_lower = args.query.lower()
    matches = []

    # Limit depth search for responsiveness
    for root, dirs, files in os.walk(search_root):
        # Skip hidden / system directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", ".venv", "__pycache__"]]
        for f in files:
            if query_lower in f.lower():
                full_path = Path(root) / f
                try:
                    matches.append({
                        "name": f,
                        "path": str(full_path),
                        "size_bytes": full_path.stat().st_size,
                    })
                except (OSError, PermissionError):
                    continue
                if len(matches) >= args.max_results:
                    break
        if len(matches) >= args.max_results:
            break

    return {
        "query": args.query,
        "results_count": len(matches),
        "matches": matches,
    }


def get_file_info_executor(args: GetFileInfoArgs) -> dict[str, Any]:
    """Inspect file metadata."""
    validator = get_path_validator()
    valid_path = validator.validate_path(args.path)
    stat = valid_path.stat()

    return {
        "name": valid_path.name,
        "path": str(valid_path),
        "is_dir": valid_path.is_dir(),
        "is_file": valid_path.is_file(),
        "size_bytes": stat.st_size,
        "created_at": stat.st_ctime,
        "modified_at": stat.st_mtime,
    }
