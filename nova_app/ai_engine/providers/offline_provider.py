"""Offline provider wrapper using the deterministic OfflineIntentRouter."""
from nova_app.ai_engine.offline_router import get_offline_router
from nova_app.ai_engine.provider_base import AIIntentResponse, LLMProvider


class OfflineProvider(LLMProvider):
    """Offline rule-based provider that requires no API keys."""

    def is_available(self) -> bool:
        return True

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
    ) -> AIIntentResponse:
        user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_message = m.get("content", "")
                break

        router = get_offline_router()
        tool_call = router.parse(user_message)

        if tool_call:
            return AIIntentResponse(
                thought=f"Matched deterministic offline command pattern for '{tool_call.tool_name}'",
                tool_calls=[tool_call],
                response=f"Executing {tool_call.tool_name.replace('_', ' ')}...",
                raw_text=user_message,
            )

        return AIIntentResponse(
            thought="No offline rule match found.",
            tool_calls=[],
            response="I am in Offline Mode. I can help you open apps, check CPU/RAM stats, take screenshots, control volume, set timers, and search files locally.",
            raw_text=user_message,
        )
