"""Tests for command registry."""

import pytest


@pytest.mark.asyncio
async def test_registry_has_core_actions(registry):
    actions = {a.name for a in registry.list_actions()}
    assert "open_application" in actions
    assert "get_memory_usage" in actions
    assert "launch_project" in actions
    assert "take_screenshot" in actions
    assert "search_web" in actions


@pytest.mark.asyncio
async def test_unknown_action(registry):
    result = await registry.execute("nonexistent_action")
    assert not result.success
    assert "Unknown action" in result.message


@pytest.mark.asyncio
async def test_get_cpu_usage(registry):
    result = await registry.execute("get_cpu_usage")
    assert result.success
    assert "cpu_percent" in result.data


@pytest.mark.asyncio
async def test_get_memory_usage(registry):
    result = await registry.execute("get_memory_usage")
    assert result.success
    assert "used_gb" in result.data


@pytest.mark.asyncio
async def test_search_web_empty(registry):
    result = await registry.execute("search_web", {"query": ""})
    assert not result.success
