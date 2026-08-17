"""Git integration client using GitPython."""
from pathlib import Path
from typing import Any
import git
import structlog
from nova_app.tools.validators.path_validator import get_path_validator

logger = structlog.get_logger(__name__)


class GitClient:
    """Provides structured inspection and execution of Git repository workflows."""

    def _get_repo(self, repo_path: str | Path | None = None) -> git.Repo:
        """Open Git repository with validated path."""
        validator = get_path_validator()
        target = validator.validate_path(str(repo_path)) if repo_path else Path.cwd()

        try:
            return git.Repo(target, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"Directory '{target}' is not a valid Git repository.")

    def get_status(self, repo_path: str | Path | None = None) -> dict[str, Any]:
        """Inspect Git repository status (active branch, untracked, modified, staged files)."""
        repo = self._get_repo(repo_path)
        active_branch = repo.active_branch.name if not repo.head.is_detached else "DETACHED"

        untracked = repo.untracked_files
        modified = [item.a_path for item in repo.index.diff(None)]
        staged = [item.a_path for item in repo.index.diff("HEAD")] if repo.head.is_valid() else []

        remotes = [r.name for r in repo.remotes]

        return {
            "root_path": repo.working_dir,
            "branch": active_branch,
            "is_dirty": repo.is_dirty(untracked_files=True),
            "untracked_count": len(untracked),
            "untracked_files": untracked[:20],
            "modified_count": len(modified),
            "modified_files": modified[:20],
            "staged_count": len(staged),
            "staged_files": staged[:20],
            "remotes": remotes,
        }

    def commit(self, message: str, repo_path: str | Path | None = None, stage_all: bool = False) -> dict[str, Any]:
        """Create a commit in the repository."""
        repo = self._get_repo(repo_path)

        if stage_all:
            repo.git.add(A=True)

        if not repo.index.diff("HEAD") and not repo.untracked_files and not repo.is_dirty():
            return {
                "status": "nothing_to_commit",
                "branch": repo.active_branch.name,
            }

        commit_obj = repo.index.commit(message)
        logger.info("Committed changes", hexsha=commit_obj.hexsha[:7], message=message)

        return {
            "status": "committed",
            "commit_hash": commit_obj.hexsha[:7],
            "message": message,
            "branch": repo.active_branch.name,
        }

    def push(
        self,
        remote_name: str = "origin",
        branch_name: str | None = None,
        repo_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Push branch to remote."""
        repo = self._get_repo(repo_path)
        branch = branch_name or repo.active_branch.name

        if remote_name not in [r.name for r in repo.remotes]:
            raise ValueError(f"Remote '{remote_name}' is not configured in repository.")

        remote = repo.remote(name=remote_name)
        push_info = remote.push(refspec=f"{branch}:{branch}")

        return {
            "status": "pushed",
            "remote": remote_name,
            "branch": branch,
            "info": str(push_info[0].summary if push_info else "OK"),
        }


_git_client_instance: GitClient | None = None


def get_git_client() -> GitClient:
    """Get singleton GitClient instance."""
    global _git_client_instance
    if _git_client_instance is None:
        _git_client_instance = GitClient()
    return _git_client_instance
