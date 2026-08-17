"""Memory executors for storing and reading preferences and shortcuts."""
from typing import Any
from pydantic import BaseModel, Field
from nova_app.memory.store import get_memory_store


class SavePreferenceArgs(BaseModel):
    key: str = Field(description="Preference name / key (e.g. favorite_browser, theme)")
    value: str = Field(description="Preference value to store")


class GetPreferenceArgs(BaseModel):
    key: str = Field(description="Preference key to look up")


class ListPreferencesArgs(BaseModel):
    pass


class AddShortcutArgs(BaseModel):
    phrase: str = Field(description="Trigger phrase for shortcut")
    tool_name: str = Field(description="Target registered tool name to execute")
    default_args: dict[str, Any] = Field(default_factory=dict, description="Default arguments for tool")


async def save_preference_executor(args: SavePreferenceArgs) -> dict[str, Any]:
    """Save a user preference (rejects secrets)."""
    store = get_memory_store()
    await store.set_preference(args.key, args.value)
    return {
        "status": "saved",
        "key": args.key,
        "value": args.value,
    }


async def get_preference_executor(args: GetPreferenceArgs) -> dict[str, Any]:
    """Retrieve a stored preference."""
    store = get_memory_store()
    val = await store.get_preference(args.key)
    return {
        "key": args.key,
        "value": val,
        "exists": val is not None,
    }


async def list_preferences_executor(args: ListPreferencesArgs) -> dict[str, Any]:
    """List all saved user preferences."""
    store = get_memory_store()
    prefs = await store.list_preferences()
    return {
        "count": len(prefs),
        "preferences": prefs,
    }


async def add_shortcut_executor(args: AddShortcutArgs) -> dict[str, Any]:
    """Add a shortcut mapping phrase to tool."""
    store = get_memory_store()
    await store.set_shortcut(args.phrase, args.tool_name, args.default_args)
    return {
        "status": "shortcut_added",
        "phrase": args.phrase,
        "tool_name": args.tool_name,
    }
