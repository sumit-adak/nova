"""Commands package - registry builder."""

from app.commands.applications import ApplicationLauncher
from app.commands.browser import BrowserCommands
from app.commands.files import FileCommands
from app.commands.git_tools import GitCommands
from app.commands.projects import ProjectCommands
from app.commands.registry import CommandRegistry
from app.commands.system import SystemCommands
from app.commands.utilities import UtilityCommands
from app.core.config import ConfigManager
from app.core.state import PermissionLevel


def build_registry(config: ConfigManager | None = None) -> CommandRegistry:
    """Build and populate the command registry with all approved actions."""
    config = config or ConfigManager()
    registry = CommandRegistry()

    apps = ApplicationLauncher(config)
    files = FileCommands()
    git = GitCommands()
    browser = BrowserCommands(config)
    system = SystemCommands()
    projects = ProjectCommands(config, apps)
    utilities = UtilityCommands()

    async def open_github() -> "ActionResult":
        return await browser.open_quick_url("github")

    async def open_localhost() -> "ActionResult":
        return await browser.open_quick_url("localhost")

    from app.commands.registry import ActionResult  # noqa: F811

    registry.register(
        "open_application", "Open a configured application",
        PermissionLevel.SAFE, apps.open_application, ["app", "args"],
    )
    registry.register(
        "close_application", "Close a running application",
        PermissionLevel.CONFIRMATION_REQUIRED, apps.close_application, ["app"],
    )
    registry.register(
        "open_folder", "Open a folder in File Explorer",
        PermissionLevel.SAFE, files.open_folder, ["path"],
    )
    registry.register(
        "open_file", "Open a file with default application",
        PermissionLevel.SAFE, files.open_file, ["path"],
    )
    registry.register(
        "create_folder", "Create a new folder",
        PermissionLevel.SAFE, files.create_folder, ["path"],
    )
    registry.register(
        "create_file", "Create a new file",
        PermissionLevel.SAFE, files.create_file, ["path", "content"],
    )
    registry.register(
        "read_file", "Read content of a file",
        PermissionLevel.SAFE, files.read_file, ["path"],
    )
    registry.register(
        "edit_file", "Edit or modify a file (append, overwrite, or replace content)",
        PermissionLevel.SAFE, files.edit_file, ["path", "content", "mode", "search", "replace"],
    )
    registry.register(
        "git_status", "Check git status of repository",
        PermissionLevel.SAFE, git.git_status, ["repo_path"],
    )
    registry.register(
        "git_add", "Stage files in git",
        PermissionLevel.SAFE, git.git_add, ["path", "repo_path"],
    )
    registry.register(
        "git_commit", "Commit staged git changes",
        PermissionLevel.SAFE, git.git_commit, ["message", "repo_path"],
    )
    registry.register(
        "git_push", "Push committed changes to remote git repository",
        PermissionLevel.SAFE, git.git_push, ["branch", "remote", "repo_path"],
    )
    registry.register(
        "git_sync", "Stage, commit, and push changes to remote repository",
        PermissionLevel.SAFE, git.git_sync, ["message", "branch", "remote", "repo_path"],
    )
    registry.register(
        "git_diff", "Show git diff of repository",
        PermissionLevel.SAFE, git.git_diff, ["repo_path"],
    )
    registry.register(
        "delete_folder", "Delete a folder permanently",
        PermissionLevel.CONFIRMATION_REQUIRED, files.delete_folder, ["path"],
    )
    registry.register(
        "delete_folder_confirmed", "Confirmed folder deletion",
        PermissionLevel.CONFIRMATION_REQUIRED, files.delete_folder_confirmed, ["path"],
    )
    registry.register(
        "delete_file", "Delete a file permanently",
        PermissionLevel.CONFIRMATION_REQUIRED, files.delete_file, ["path"],
    )
    registry.register(
        "delete_file_confirmed", "Confirmed file deletion",
        PermissionLevel.CONFIRMATION_REQUIRED, files.delete_file_confirmed, ["path"],
    )
    registry.register(
        "open_url", "Open a URL in browser",
        PermissionLevel.SAFE, browser.open_url, ["url"],
    )
    registry.register(
        "search_web", "Search the web",
        PermissionLevel.SAFE, browser.search_web, ["query", "engine"],
    )
    registry.register(
        "search_error", "Search for a programming error",
        PermissionLevel.SAFE, browser.search_error, ["error"],
    )
    registry.register(
        "open_github", "Open GitHub website",
        PermissionLevel.SAFE, open_github, [],
    )
    registry.register(
        "open_localhost", "Open localhost in browser",
        PermissionLevel.SAFE, open_localhost, [],
    )
    registry.register(
        "get_system_info", "Get system information",
        PermissionLevel.SAFE, system.get_system_info, [],
    )
    registry.register(
        "get_cpu_usage", "Get CPU usage",
        PermissionLevel.SAFE, system.get_cpu_usage, [],
    )
    registry.register(
        "get_memory_usage", "Get memory/RAM usage",
        PermissionLevel.SAFE, system.get_memory_usage, [],
    )
    registry.register(
        "get_gpu_usage", "Get GPU usage",
        PermissionLevel.SAFE, system.get_gpu_usage, [],
    )
    registry.register(
        "get_disk_usage", "Get disk/storage usage",
        PermissionLevel.SAFE, system.get_disk_usage, ["path"],
    )
    registry.register(
        "get_network_stats", "Get network statistics",
        PermissionLevel.SAFE, system.get_network_stats, [],
    )
    registry.register(
        "get_battery_status", "Get battery status",
        PermissionLevel.SAFE, system.get_battery_status, [],
    )
    registry.register(
        "kill_process", "Kill a process",
        PermissionLevel.CONFIRMATION_REQUIRED, system.kill_process, ["process_name"],
    )
    registry.register(
        "kill_process_confirmed", "Confirmed process kill",
        PermissionLevel.CONFIRMATION_REQUIRED, system.kill_process_confirmed, ["process_name"],
    )
    registry.register(
        "shutdown", "Shut down the computer",
        PermissionLevel.CONFIRMATION_REQUIRED, system.shutdown, [],
    )
    registry.register(
        "shutdown_confirmed", "Confirmed shutdown",
        PermissionLevel.CONFIRMATION_REQUIRED, system.shutdown_confirmed, [],
    )
    registry.register(
        "restart", "Restart the computer",
        PermissionLevel.CONFIRMATION_REQUIRED, system.restart, [],
    )
    registry.register(
        "restart_confirmed", "Confirmed restart",
        PermissionLevel.CONFIRMATION_REQUIRED, system.restart_confirmed, [],
    )
    registry.register(
        "launch_project", "Open a developer project workspace",
        PermissionLevel.SAFE, projects.launch_project,
        ["project_name", "open_editor", "open_terminal", "open_folder"],
    )
    registry.register(
        "list_projects", "List configured projects",
        PermissionLevel.SAFE, projects.list_projects, [],
    )
    registry.register(
        "take_screenshot", "Take a screenshot",
        PermissionLevel.SAFE, utilities.take_screenshot, ["filename"],
    )
    registry.register(
        "set_volume", "Set system volume (0-100)",
        PermissionLevel.SAFE, utilities.set_volume, ["level"],
    )
    registry.register(
        "start_timer", "Start a countdown timer",
        PermissionLevel.SAFE, utilities.start_timer, ["seconds", "label"],
    )
    registry.register(
        "run_dev_command", "Run an approved developer command",
        PermissionLevel.CONFIRMATION_REQUIRED, utilities.run_dev_command, ["command"],
    )
    registry.register(
        "run_dev_command_confirmed", "Confirmed dev command execution",
        PermissionLevel.CONFIRMATION_REQUIRED, utilities.run_dev_command_confirmed, ["command"],
    )

    return registry
