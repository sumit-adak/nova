"""OpenAI provider implementation."""

from __future__ import annotations

import json
from typing import Any

from app.ai.prompts import CHAT_SYSTEM_PROMPT, INTENT_SYSTEM_PROMPT
from app.ai.provider import AIProvider
from app.core.config import Settings
from app.core.logger import get_logger

logger = get_logger("openai")


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None

    @property
    def name(self) -> str:
        return "OpenAI"

    @property
    def is_available(self) -> bool:
        return bool(self.settings.openai_api_key)

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        return self._client

    async def chat(self, messages: list[dict[str, str]], system_prompt: str = "") -> str:
        if not self.is_available:
            return "AI service is unavailable. Local commands are still working."

        client = self._get_client()
        api_messages = [{"role": "system", "content": system_prompt or CHAT_SYSTEM_PROMPT}]
        api_messages.extend(messages)

        try:
            response = await client.chat.completions.create(
                model=self.settings.openai_model,
                messages=api_messages,
                max_tokens=1024,
                temperature=0.7,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error("OpenAI chat error: %s", exc)
            return f"AI service error: {exc}"

    async def parse_intent(
        self, user_input: str, available_actions: list[dict[str, str]]
    ) -> dict[str, Any]:
        if not self.is_available:
            return {"type": "offline", "action": None, "parameters": {}, "response": ""}

        actions_text = "\n".join(
            f"- {a['name']}: {a['description']} (params: {a['parameters']})"
            for a in available_actions
        )
        system = INTENT_SYSTEM_PROMPT.format(actions=actions_text)

        client = self._get_client()
        try:
            response = await client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_input},
                ],
                max_tokens=512,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as exc:
            logger.error("OpenAI intent parse error: %s", exc)
            return {"type": "error", "action": None, "parameters": {}, "response": str(exc)}
