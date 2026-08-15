"""Google Gemini provider implementation."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from app.ai.prompts import CHAT_SYSTEM_PROMPT, INTENT_SYSTEM_PROMPT
from app.ai.provider import AIProvider
from app.core.config import Settings
from app.core.logger import get_logger

logger = get_logger("gemini")

FALLBACK_MODELS = [
    "gemini-3.7-flash",
    "gemini-flash-latest",
    "gemini-2.5-pro",
]


class GeminiProvider(AIProvider):
    """Google Gemini API provider."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model = None
        self._active_model_name = settings.gemini_model or "gemini-3.7-flash"

    @property
    def name(self) -> str:
        return "Google Gemini"

    @property
    def is_available(self) -> bool:
        return bool(self.settings.gemini_api_key)

    def _get_model(self, model_name: str | None = None):
        target_model = model_name or self._active_model_name
        import google.generativeai as genai
        genai.configure(api_key=self.settings.gemini_api_key)
        return genai.GenerativeModel(target_model)

    def _generate_sync(self, prompt: str) -> str:
        """Synchronously generate content with model fallback."""
        import google.generativeai as genai

        models_to_try = [self._active_model_name] + [
            m for m in FALLBACK_MODELS if m != self._active_model_name
        ]

        last_error = None
        for m_name in models_to_try:
            try:
                model = self._get_model(m_name)
                response = model.generate_content(prompt)
                self._active_model_name = m_name
                return response.text or ""
            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                if "404" in err_str or "not found" in err_str.lower() or "no longer available" in err_str.lower():
                    logger.warning("Gemini model %s unavailable, trying next fallback...", m_name)
                    continue
                raise exc

        raise last_error or RuntimeError("All Gemini models failed")

    async def chat(self, messages: list[dict[str, str]], system_prompt: str = "") -> str:
        if not self.is_available:
            return "AI service is unavailable. Local commands are still working."

        prompt_parts = [system_prompt or CHAT_SYSTEM_PROMPT]
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"{role}: {content}")

        full_prompt = "\n".join(prompt_parts)

        try:
            return await asyncio.to_thread(self._generate_sync, full_prompt)
        except Exception as exc:
            logger.error("Gemini chat error: %s", exc)
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
        prompt = f"{system}\n\nUser: {user_input}\n\nRespond with valid JSON only."

        try:
            text = await asyncio.to_thread(self._generate_sync, prompt)
            text = text.strip()
            # Extract JSON block or brackets
            if "```" in text:
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
                if match:
                    text = match.group(1).strip()
            # If text still contains non-JSON prefix/suffix
            if not (text.startswith("{") and text.endswith("}")):
                brace_start = text.find("{")
                brace_end = text.rfind("}")
                if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
                    text = text[brace_start:brace_end + 1]

            return json.loads(text)
        except Exception as exc:
            logger.error("Gemini intent parse error: %s", exc)
            return {"type": "error", "action": None, "parameters": {}, "response": str(exc)}
