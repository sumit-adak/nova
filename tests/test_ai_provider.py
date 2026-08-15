"""Tests for AI provider abstraction."""

import pytest

from app.ai import create_provider
from app.core.config import Settings


def test_offline_provider_default():
    settings = Settings(nova_ai_provider="offline", openai_api_key="", gemini_api_key="")
    provider = create_provider(settings)
    assert provider.name == "Offline"
    assert provider.is_available


@pytest.mark.asyncio
async def test_offline_intent_parsing():
    settings = Settings(nova_ai_provider="offline", openai_api_key="", gemini_api_key="")
    provider = create_provider(settings)
    actions = [{"name": "get_cpu_usage", "description": "CPU", "parameters": ""}]
    intent = await provider.parse_intent("what's my cpu usage", actions)
    assert intent["action"] == "get_cpu_usage"


@pytest.mark.asyncio
async def test_offline_chat_message():
    settings = Settings(nova_ai_provider="offline", openai_api_key="", gemini_api_key="")
    provider = create_provider(settings)
    response = await provider.chat([{"role": "user", "content": "hello"}])
    assert "local commands" in response.lower()
