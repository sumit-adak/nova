"""Git command tools for developer automation."""

from __future__ import annotations

import subprocess
from pathlib import Path

from app.commands.registry import ActionResult
from app.core.config import BASE_DIR
from app.core.logger import get_logger
from app.core.security import validate_path

logger = get_logger("git")


class GitCommands:
    """Git version control automation."""

    def __init__(self, default_dir: Path | None = None) -> None:
        self.default_dir = default_dir or BASE_DIR

    def _resolve_repo_dir(self, repo_path: str = "") -> Path:
        if not repo_path or not repo_path.strip():
            return self.default_dir
        try:
            return validate_path(repo_path, must_exist=True)
        except Exception:
            p = Path(repo_path)
            return p if p.exists() else self.default_dir

    def _run_git(self, args: list[str], cwd: Path) -> tuple[int, str, str]:
        """Execute a git command in the given directory."""
        try:
            proc = subprocess.run(
                ["git"] + args,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=30,
            )
            return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "Git command timed out after 30s."
        except Exception as exc:
            return -1, "", str(exc)

    async def git_status(self, repo_path: str = "") -> ActionResult:
        """Get git status of a repository."""
        cwd = self._resolve_repo_dir(repo_path)
        code, stdout, stderr = self._run_git(["status", "--short"], cwd)
        if code != 0:
            return ActionResult(
                success=False,
                message=f"Git status failed: {stderr or 'Not a git repository.'}",
            )
        msg = stdout if stdout else "Working tree clean, no changes."
        return ActionResult(
            success=True,
            message=f"Git Status ({cwd.name}):\n{msg}",
            data={"status": stdout, "cwd": str(cwd)},
        )

    async def git_add(self, path: str = ".", repo_path: str = "") -> ActionResult:
        """Stage files in git."""
        cwd = self._resolve_repo_dir(repo_path)
        target = path.strip() if path else "."
        code, stdout, stderr = self._run_git(["add", target], cwd)
        if code != 0:
            return ActionResult(
                success=False,
                message=f"Git add failed: {stderr}",
            )
        return ActionResult(
            success=True,
            message=f"Staged changes in {cwd.name} ({target}).",
            data={"staged": target, "cwd": str(cwd)},
        )

    async def git_commit(self, message: str = "Update files", repo_path: str = "") -> ActionResult:
        """Commit staged changes."""
        cwd = self._resolve_repo_dir(repo_path)
        msg = message.strip() if message else "Update files"
        code, stdout, stderr = self._run_git(["commit", "-m", msg], cwd)
        if code != 0:
            if "nothing to commit" in (stdout + stderr).lower():
                return ActionResult(
                    success=True,
                    message="Nothing to commit, working tree clean.",
                    data={"cwd": str(cwd)},
                )
            return ActionResult(
                success=False,
                message=f"Git commit failed: {stderr or stdout}",
            )
        return ActionResult(
            success=True,
            message=f"Committed changes in {cwd.name}: '{msg}'.",
            data={"commit_message": msg, "output": stdout, "cwd": str(cwd)},
        )

    async def git_push(
        self,
        branch: str = "",
        remote: str = "origin",
        repo_path: str = "",
    ) -> ActionResult:
        """Push committed changes to remote repository."""
        cwd = self._resolve_repo_dir(repo_path)
        target_remote = remote.strip() if remote else "origin"

        # Detect current branch
        code_b, current_branch, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
        active_branch = current_branch if code_b == 0 and current_branch else "master"

        target_branch = branch.strip() if branch else active_branch

        # Try push to target branch
        code, stdout, stderr = self._run_git(["push", target_remote, target_branch], cwd)
        if code != 0:
            # If target branch was specified as 'main' but local is 'master' (or vice versa), try pushing local branch to target remote ref
            if active_branch != target_branch:
                code, stdout, stderr = self._run_git(["push", target_remote, f"{active_branch}:{target_branch}"], cwd)

            if code != 0:
                # Try simple git push
                code, stdout, stderr = self._run_git(["push", target_remote, active_branch], cwd)
                if code != 0:
                    code, stdout, stderr = self._run_git(["push"], cwd)

        if code != 0:
            return ActionResult(
                success=False,
                message=f"Git push failed: {stderr or stdout or 'Check remote configuration.'}",
            )

        return ActionResult(
            success=True,
            message=f"Pushed to {target_remote}/{target_branch or active_branch} in {cwd.name}.",
            data={"remote": target_remote, "branch": target_branch or active_branch, "cwd": str(cwd)},
        )

    async def git_sync(
        self,
        message: str = "Update files",
        branch: str = "main",
        remote: str = "origin",
        repo_path: str = "",
    ) -> ActionResult:
        """Stage all changes, commit with message, and push to remote."""
        cwd = self._resolve_repo_dir(repo_path)
        # 1. Add
        add_res = await self.git_add(path=".", repo_path=str(cwd))
        if not add_res.success:
            return add_res

        # 2. Commit
        commit_res = await self.git_commit(message=message, repo_path=str(cwd))
        if not commit_res.success:
            return commit_res

        # 3. Push
        push_res = await self.git_push(branch=branch, remote=remote, repo_path=str(cwd))
        if not push_res.success:
            return push_res

        return ActionResult(
            success=True,
            message=f"Successfully committed ('{message}') and pushed to {branch}.",
            data={"cwd": str(cwd), "message": message, "branch": branch},
        )

    async def git_diff(self, repo_path: str = "") -> ActionResult:
        """Show uncommitted git diff."""
        cwd = self._resolve_repo_dir(repo_path)
        code, stdout, stderr = self._run_git(["diff"], cwd)
        if code != 0:
            return ActionResult(success=False, message=f"Git diff failed: {stderr}")
        diff_text = stdout if stdout else "No unstaged changes."
        if len(diff_text) > 800:
            diff_text = diff_text[:800] + "\n...(truncated)"
        return ActionResult(
            success=True,
            message=f"Git Diff:\n{diff_text}",
            data={"diff": stdout, "cwd": str(cwd)},
        )
