"""Tests for git tools and file operations."""

import pytest
from pathlib import Path
from app.commands.git_tools import GitCommands
from app.commands.files import FileCommands


@pytest.mark.asyncio
async def test_git_status():
    git = GitCommands()
    result = await git.git_status()
    # NOVA is a git repo, so git status should succeed
    assert result.success is True
    assert "Git Status" in result.message


@pytest.mark.asyncio
async def test_file_read_and_edit(tmp_path):
    files = FileCommands()
    test_file = tmp_path / "test_doc.md"
    test_file.write_text("# Initial Header\n", encoding="utf-8")

    # Read
    read_res = await files.read_file(str(test_file))
    assert read_res.success is True
    assert "# Initial Header" in read_res.data["content"]

    # Append
    edit_res = await files.edit_file(str(test_file), content="New Section", mode="append")
    assert edit_res.success is True
    assert "Updated" in edit_res.message
    content = test_file.read_text(encoding="utf-8")
    assert "# Initial Header" in content
    assert "New Section" in content

    # Replace
    edit_res2 = await files.edit_file(str(test_file), search="New Section", replace="Replaced Section", mode="replace")
    assert edit_res2.success is True
    content2 = test_file.read_text(encoding="utf-8")
    assert "Replaced Section" in content2
