"""Anthropic Claude LLM provider implementation."""
import json
import re
import structlog
from nova_app.ai_engine.provider_base import AIIntentResponse, LLMProvider
from nova_app.config.settings import Settings, get_settings
from nova_app.tools.schema import ToolCall

logger = structlog.get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic Claude models."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def is_available(self) -> bool:
        return bool(self.settings.anthropic_api_key)

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
    ) -> AIIntentResponse:
        if not self.settings.anthropic_api_key:
            raise ValueError("Anthropic API Key is not configured.")

        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.settings.anthropic_api_key)

            formatted_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in messages
                if m["role"] in ["user", "assistant"]
            ]

            response = await client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=2048,
                system=system_prompt,
                messages=formatted_messages,
                temperature=temperature,
            )

            raw_text = response.content[0].text if response.content else "{}"
            clean_json = raw_text
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
            if json_match:
                clean_json = json_match.group(1)

            parsed = json.loads(clean_json)

            tool_calls = [
                ToolCall(
                    tool_name=tc.get("tool_name", ""),
                    arguments=tc.get("arguments", {}),
                    reasoning=tc.get("reasoning"),
                )
                for tc in parsed.get("tool_calls", [])
            ]

            return AIIntentResponse(
                thought=parsed.get("thought", ""),
                tool_calls=tool_calls,
                response=parsed.get("response", ""),
                raw_text=raw_text,
            )
        except Exception as e:
            logger.error("Anthropic API call failed", error=str(e))
            raise
