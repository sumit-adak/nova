"""Google Gemini LLM provider implementation."""
import json
import re
import structlog
from nova_app.ai_engine.provider_base import AIIntentResponse, LLMProvider
from nova_app.config.settings import Settings, get_settings
from nova_app.tools.schema import ToolCall

logger = structlog.get_logger(__name__)


class GeminiProvider(LLMProvider):
    """Provider for Google Gemini models."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def is_available(self) -> bool:
        return bool(self.settings.gemini_api_key)

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
    ) -> AIIntentResponse:
        if not self.settings.gemini_api_key:
            raise ValueError("Gemini API Key is not configured.")

        # Try google.genai or fallback to google.generativeai
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.settings.gemini_api_key)
            model = genai.GenerativeModel(
                model_name=self.settings.gemini_model if "gemini" in self.settings.gemini_model else "gemini-1.5-flash",
                system_instruction=system_prompt
            )

            # Build chat history
            user_content = ""
            for m in messages:
                user_content += f"{m['role'].upper()}: {m['content']}\n"

            response = await model.generate_content_async(
                user_content,
                generation_config={"temperature": temperature}
            )

            raw_text = response.text or "{}"
            # Extract JSON from markdown code fences if wrapped
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
            logger.error("Gemini API call failed", error=str(e))
            raise
