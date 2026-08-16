"""Unit tests for Phase 1 tools, registry, executors, and offline intent router."""
import pytest
from unittest.mock import patch
from nova_app.ai_engine.offline_router import OfflineIntentRouter
from nova_app.tools.registry import ToolRegistry
from nova_app.tools.schema import ToolCall
from nova_app.tools.executors import (
    GetSystemStatsArgs,
    get_system_stats_executor,
    search_files_executor,
    SearchFilesArgs,
    list_applications_executor,
    ListApplicationsArgs,
)


@pytest.mark.asyncio
async def test_tool_registry_execution():
    registry = ToolRegistry()
    
    # 1. Successful execution of get_system_stats
    call = ToolCall(tool_name="get_system_stats", arguments={"include_disks": False})
    res = await registry.execute_tool_call(call, actor="test")

    assert res.success is True
    assert "cpu" in res.data
    assert "ram" in res.data
    assert res.error is None
    assert res.duration_ms >= 0

    # 2. Unknown tool fails safely
    bad_call = ToolCall(tool_name="nonexistent_dangerous_tool", arguments={})
    bad_res = await registry.execute_tool_call(bad_call, actor="test")
    assert bad_res.success is False
    assert "not registered" in bad_res.error

    # 3. Invalid arguments schema fails safely
    invalid_args_call = ToolCall(tool_name="set_volume", arguments={"level": 250})  # max 100
    invalid_res = await registry.execute_tool_call(invalid_args_call, actor="test")
    assert invalid_res.success is False
    assert "validation error" in invalid_res.error.lower()


def test_system_stats_executor():
    res = get_system_stats_executor(GetSystemStatsArgs(include_disks=True))
    assert "cpu" in res
    assert "ram" in res
    assert "percent" in res["cpu"]
    assert "percent" in res["ram"]


def test_list_applications_executor():
    res = list_applications_executor(ListApplicationsArgs(filter_query="calc"))
    assert res["count"] >= 1
    assert "calc" in res["applications"] or "calculator" in res["applications"]


def test_search_files_executor(tmp_path):
    subfolder = tmp_path / "documents"
    subfolder.mkdir()
    target_file = subfolder / "project_report_final.docx"
    target_file.write_text("dummy")

    with patch("nova_app.tools.validators.path_validator.get_path_validator") as mock_val:
        mock_val.return_value.validate_path.return_value = subfolder
        res = search_files_executor(SearchFilesArgs(query="project_report", root_directory=str(subfolder)))
        assert res["results_count"] == 1
        assert res["matches"][0]["name"] == "project_report_final.docx"


def test_offline_intent_router():
    router = OfflineIntentRouter()

    # System stats
    call1 = router.parse("how much ram is free?")
    assert call1 is not None
    assert call1.tool_name == "get_system_stats"

    # Screenshot
    call2 = router.parse("take a screenshot please")
    assert call2 is not None
    assert call2.tool_name == "take_screenshot"

    # Volume
    call3 = router.parse("set volume to 65")
    assert call3 is not None
    assert call3.tool_name == "set_volume"
    assert call3.arguments["level"] == 65

    # Timer
    call4 = router.parse("set timer for 15 minutes")
    assert call4 is not None
    assert call4.tool_name == "start_timer"
    assert call4.arguments["seconds"] == 900

    # Open app
    call5 = router.parse("open notepad")
    assert call5 is not None
    assert call5.tool_name == "open_application"
    assert call5.arguments["app_name"] == "notepad"
