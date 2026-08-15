"""Tests for offline intent parser."""

import pytest

from app.ai.intent_parser import OfflineIntentParser


@pytest.fixture
def parser():
    return OfflineIntentParser()


def test_open_vscode(parser):
    intent = parser.parse("open VS Code")
    assert intent["type"] == "action"
    assert intent["action"] == "open_application"
    assert intent["parameters"]["app"] == "vscode"


def test_ram_usage(parser):
    intent = parser.parse("what's my RAM usage?")
    assert intent["action"] == "get_memory_usage"


def test_plantguard(parser):
    intent = parser.parse("open my PlantGuard project")
    assert intent["action"] == "launch_project"
    assert intent["parameters"]["project_name"] == "PlantGuard"


def test_screenshot(parser):
    intent = parser.parse("take a screenshot")
    assert intent["action"] == "take_screenshot"


def test_search(parser):
    intent = parser.parse("search for TensorFlow image classification")
    assert intent["action"] == "search_web"
    assert "TensorFlow" in intent["parameters"]["query"]


def test_conversation_fallback(parser):
    intent = parser.parse("explain quantum computing in detail")
    assert intent["type"] == "conversation"


def test_git_sync(parser):
    intent = parser.parse("sync to main")
    assert intent["type"] == "action"
    assert intent["action"] == "git_sync"
    assert intent["parameters"]["branch"] == "main"


def test_commit_and_push(parser):
    intent = parser.parse("commit and push to main")
    assert intent["type"] in ("action", "actions")
    if intent["type"] == "actions":
        actions = [a["action"] for a in intent["actions"]]
        assert "git_commit" in actions or "git_sync" in actions
    else:
        assert intent["action"] in ("git_sync", "git_push")


def test_edit_file(parser):
    intent = parser.parse("edit current readme file")
    assert intent["type"] == "action"
    assert intent["action"] == "edit_file"
    assert intent["parameters"]["path"] == "README.md"


def test_compound_workflow(parser):
    query = "open vs code and do some changes in current readme file and commit and push it to the main branch"
    intent = parser.parse(query)
    assert intent["type"] == "actions"
    assert len(intent["actions"]) >= 2
    actions = [a["action"] for a in intent["actions"]]
    assert "open_application" in actions
    assert "edit_file" in actions or "git_sync" in actions

