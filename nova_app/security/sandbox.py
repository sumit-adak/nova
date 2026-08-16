"""Subprocess sandboxing and safe binary launcher without shell=True."""
import asyncio
import subprocess
from pathlib import Path
from nova_app.core.exceptions import SecurityError

# Allow-listed Windows/developer binary names
ALLOWLISTED_BINARIES = {
    "code",
    "code.cmd",
    "git",
    "git.exe",
    "explorer",
    "explorer.exe",
    "notepad",
    "notepad.exe",
    "calc",
    "calc.exe",
    "wt",
    "wt.exe",
    "cmd.exe",
    "powershell.exe",
}


def sanitize_and_validate_binary(binary_name: str) -> str:
    """Ensure binary is in allowlist or points to a valid safe executable path."""
    clean_name = Path(binary_name).name.lower()
    if clean_name in ALLOWLISTED_BINARIES:
        return binary_name

    # If it's a full path, verify it exists and is an executable
    binary_path = Path(binary_name)
    if binary_path.is_file() and binary_path.suffix.lower() in [".exe", ".cmd", ".bat"]:
        return str(binary_path)

    raise SecurityError(f"Binary '{binary_name}' is not in the safe allowlist.")


async def run_sandboxed_command(
    args: list[str],
    cwd: str | Path | None = None,
    timeout_sec: float = 30.0,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    """
    Execute a subprocess without shell=True, validating executable against allowlist.
    """
    if not args:
        raise SecurityError("Command arguments cannot be empty.")

    validated_binary = sanitize_and_validate_binary(args[0])
    command_list = [validated_binary] + args[1:]

    # Run strictly with create_subprocess_exec (NO shell=True)
    process = await asyncio.create_subprocess_exec(
        *command_list,
        cwd=str(cwd) if cwd else None,
        stdout=asyncio.subprocess.PIPE if capture_output else None,
        stderr=asyncio.subprocess.PIPE if capture_output else None,
    )

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_sec)
        return subprocess.CompletedProcess(
            args=command_list,
            returncode=process.returncode or 0,
            stdout=stdout.decode("utf-8", errors="replace") if stdout else "",
            stderr=stderr.decode("utf-8", errors="replace") if stderr else "",
        )
    except asyncio.TimeoutError:
        process.kill()
        raise TimeoutError(f"Command {' '.join(command_list)} timed out after {timeout_sec}s.")
