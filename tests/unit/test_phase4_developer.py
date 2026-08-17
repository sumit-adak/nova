"""Unit tests for Phase 4: Developer Assistant (Project detection, VS Code, Git tools)."""
import os
import git
import pytest
from unittest.mock import patch
from nova_app.computer_index.project_detector import ProjectDetector
from nova_app.integrations.git_integration import GitClient
from nova_app.integrations.vscode import VSCodeClient
from nova_app.tools.registry import ToolRegistry
from nova_app.tools.schema import ToolCall


@pytest.mark.asyncio
async def test_project_detector_finds_projects(tmp_path):
    proj_dir = tmp_path / "my_cool_project"
    proj_dir.mkdir()
    (proj_dir / "pyproject.toml").write_text("[project]\nname='cool'")
    (proj_dir / ".git").mkdir()

    detector = ProjectDetector()
    results = await detector.scan_directories([tmp_path])

    assert len(results) >= 1
    names = [r["name"] for r in results]
    assert "my_cool_project" in names
    matched = [r for r in results if r["name"] == "my_cool_project"][0]
    assert matched["type"] == "python"
    assert matched["vcs"] == "git"


def test_git_client_status_and_commit(tmp_path):
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # Initialize a clean repo
    repo = git.Repo.init(repo_dir)
    # Set dummy user config for committing in test
    repo.config_writer().set_value("user", "name", "Nova Tester").release()
    repo.config_writer().set_value("user", "email", "test@nova.local").release()

    # Create initial file
    (repo_dir / "README.md").write_text("# Test Repo")
    repo.git.add(A=True)
    repo.index.commit("Initial commit")

    with patch("nova_app.tools.validators.path_validator.get_path_validator") as mock_val:
        mock_val.return_value.validate_path.return_value = repo_dir

        git_client = GitClient()
        status = git_client.get_status(repo_dir)

        assert status["branch"] in ["master", "main"]
        assert status["is_dirty"] is False
        assert status["untracked_count"] == 0

        # Create untracked file
        (repo_dir / "new_feature.py").write_text("print('hello')")
        status2 = git_client.get_status(repo_dir)
        assert status2["is_dirty"] is True
        assert status2["untracked_count"] == 1

        # Commit via client
        commit_res = git_client.commit("Add new feature", repo_path=repo_dir, stage_all=True)
        assert commit_res["status"] == "committed"
        assert len(commit_res["commit_hash"]) == 7


@pytest.mark.asyncio
async def test_developer_tools_in_registry():
    registry = ToolRegistry()

    assert registry.get("open_project") is not None
    assert registry.get("open_terminal") is not None
    assert registry.get("git_status") is not None
    assert registry.get("git_commit") is not None
    assert registry.get("git_push") is not None

    # Test git_push is HIGH risk and requires confirmation
    push_call = ToolCall(tool_name="git_push", arguments={"remote": "origin"})
    res = await registry.execute_tool_call(push_call, confirmed_by_user=None, auto_prompt_confirmation=False)
    assert res.success is False
    assert "requires explicit user confirmation" in res.error
