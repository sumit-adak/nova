"""Unit and security tests for Phase 5: Memory System."""
import pytest
from nova_app.core.exceptions import SecurityError
from nova_app.memory.retention import RetentionManager
from nova_app.memory.secret_guard import SecretGuard
from nova_app.memory.store import MemoryStore
from nova_app.tools.registry import ToolRegistry
from nova_app.tools.schema import ToolCall


def test_secret_guard_blocks_sensitive_keys_and_values():
    guard = SecretGuard()

    # Sensitive key
    with pytest.raises(SecurityError, match="refer to a secret"):
        guard.validate_content("my_db_password", "supersecret123")

    with pytest.raises(SecurityError, match="refer to a secret"):
        guard.validate_content("api_key", "valid_looking_key")

    # Sensitive value containing OpenAI key
    with pytest.raises(SecurityError, match="contains sensitive credentials"):
        guard.validate_content("notes", "Use key sk-1234567890abcdef1234567890 for login")

    # Benign content passes
    guard.validate_content("favorite_editor", "vscode")
    guard.validate_content("theme", "dark")


@pytest.mark.asyncio
async def test_memory_store_preferences_crud():
    store = MemoryStore()

    await store.set_preference("editor", "vscode")
    val = await store.get_preference("editor")
    assert val == "vscode"

    prefs = await store.list_preferences()
    assert prefs.get("editor") == "vscode"

    deleted = await store.delete_preference("editor")
    assert deleted is True
    assert await store.get_preference("editor") is None


@pytest.mark.asyncio
async def test_memory_store_shortcuts_and_ranking():
    store = MemoryStore()

    await store.set_shortcut("status", "git_status", {"repo_path": None})
    sc = await store.get_shortcut("status")
    assert sc is not None
    assert sc.tool_name == "git_status"

    # Context retrieval
    await store.set_preference("font_size", "14")
    context = await store.retrieve_context()
    assert "font_size" in context.preferences


@pytest.mark.asyncio
async def test_retention_pruning():
    retention = RetentionManager()
    # Prune task history
    pruned_tasks = await retention.prune_task_history(max_records=100)
    assert isinstance(pruned_tasks, int)

    # Prune old messages
    pruned_msgs = await retention.prune_old_messages(days=365)
    assert isinstance(pruned_msgs, int)


@pytest.mark.asyncio
async def test_memory_tools_in_registry():
    registry = ToolRegistry()

    # Save preference tool
    call = ToolCall(tool_name="save_preference", arguments={"key": "default_view", "value": "compact"})
    res = await registry.execute_tool_call(call, actor="test")
    assert res.success is True
    assert res.data["status"] == "saved"

    # Get preference tool
    get_call = ToolCall(tool_name="get_preference", arguments={"key": "default_view"})
    get_res = await registry.execute_tool_call(get_call, actor="test")
    assert get_res.success is True
    assert get_res.data["value"] == "compact"
