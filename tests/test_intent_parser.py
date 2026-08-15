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


def test_open_spotify_play_any_song(parser):
    intent = parser.parse("open spotify and play any song")
    assert intent["type"] in ("action", "actions")
    if intent["type"] == "actions":
        action_names = [a["action"] for a in intent["actions"]]
        assert "open_application" in action_names
        assert "play_music" in action_names
        music_act = next(a for a in intent["actions"] if a["action"] == "play_music")
        assert music_act["parameters"]["platform"] == "spotify"
        assert music_act["parameters"]["query"] == "Today's Top Hits"
    else:
        assert intent["action"] == "play_music"
        assert intent["parameters"]["platform"] == "spotify"
        assert intent["parameters"]["query"] == "Today's Top Hits"


def test_open_spotify_play_specific_song(parser):
    intent = parser.parse("open spotify and play Starboy")
    assert intent["type"] in ("action", "actions")
    if intent["type"] == "actions":
        action_names = [a["action"] for a in intent["actions"]]
        assert "open_application" in action_names
        assert "play_music" in action_names
        music_act = next(a for a in intent["actions"] if a["action"] == "play_music")
        assert music_act["parameters"]["platform"] == "spotify"
        assert "Starboy" in music_act["parameters"]["query"]
    else:
        assert intent["action"] == "play_music"
        assert intent["parameters"]["platform"] == "spotify"
        assert "Starboy" in intent["parameters"]["query"]



def test_play_song_on_spotify(parser):
    intent = parser.parse("play Shape of You on spotify")
    assert intent["type"] == "action"
    assert intent["action"] == "play_music"
    assert intent["parameters"]["platform"] == "spotify"
    assert "Shape of You" in intent["parameters"]["query"]


def test_play_song_on_youtube(parser):
    intent = parser.parse("play Bohemian Rhapsody on youtube")
    assert intent["type"] == "action"
    assert intent["action"] == "play_music"
    assert intent["parameters"]["platform"] == "youtube"
    assert "Bohemian Rhapsody" in intent["parameters"]["query"]


def test_open_and_search(parser):
    intent = parser.parse("open and search Python tutorials")
    assert intent["type"] == "action"
    assert intent["action"] == "search_web"
    assert intent["parameters"]["query"] == "Python tutorials"
    assert intent["parameters"]["engine"] == "google"


def test_open_youtube_and_search(parser):
    intent = parser.parse("open youtube and search lofi hip hop")
    assert intent["type"] == "action"
    assert intent["action"] == "search_web"
    assert intent["parameters"]["query"] == "lofi hip hop"
    assert intent["parameters"]["engine"] == "youtube"


def test_search_on_spotify(parser):
    intent = parser.parse("search Eminem on spotify")
    assert intent["type"] == "action"
    assert intent["action"] == "search_web"
    assert intent["parameters"]["query"] == "Eminem"
    assert intent["parameters"]["engine"] == "spotify"


def test_send_whatsapp_message_intent(parser):
    intent = parser.parse("send whatsapp to +1234567890 saying hello how are you")
    assert intent["type"] == "action"
    assert intent["action"] == "send_whatsapp_message"
    assert "+1234567890" in intent["parameters"]["phone"]
    assert "hello how are you" in intent["parameters"]["message"]


def test_open_whatsapp_and_search_number(parser):
    intent = parser.parse("open whatsapp and search 9876543210 and write let's meet")
    assert intent["type"] == "action"
    assert intent["action"] == "send_whatsapp_message"
    assert "9876543210" in intent["parameters"]["phone"]
    assert "let's meet" in intent["parameters"]["message"]


def test_send_email_intent(parser):
    intent = parser.parse("write an email to test@example.com subject Project Review body All looking good")
    assert intent["type"] == "action"
    assert intent["action"] == "send_email"
    assert intent["parameters"]["to"] == "test@example.com"
    assert intent["parameters"]["subject"] == "Project Review"
    assert intent["parameters"]["body"] == "All looking good"


def test_send_file_intent(parser):
    intent = parser.parse("send file report.pdf to boss@example.com")
    assert intent["type"] == "action"
    assert intent["action"] == "send_file"
    assert "report.pdf" in intent["parameters"]["path"]
    assert "boss@example.com" in intent["parameters"]["recipient"]



