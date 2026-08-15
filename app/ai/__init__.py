"""AI provider factory."""

from app.ai.gemini_provider import GeminiProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.provider import AIProvider
from app.core.config import Settings, get_settings


class OfflineProvider(AIProvider):
    """Offline provider that only supports local pattern matching."""

    @property
    def name(self) -> str:
        return "Offline"

    @property
    def is_available(self) -> bool:
        return True

    async def chat(self, messages: list[dict[str, str]], system_prompt: str = "") -> str:
        return (
            "AI service is unavailable, but local commands are still working. "
            "Try commands like 'open VS Code', 'what's my RAM usage', or 'open PlantGuard'."
        )

    async def parse_intent(
        self, user_input: str, available_actions: list[dict[str, str]]
    ) -> dict:
        from app.ai.intent_parser import OfflineIntentParser
        return OfflineIntentParser().parse(user_input)


def create_provider(settings: Settings | None = None) -> AIProvider:
    """Create the appropriate AI provider based on configuration."""
    settings = settings or get_settings()
    provider_name = settings.nova_ai_provider.lower()

    if provider_name == "openai" and settings.openai_api_key:
        return OpenAIProvider(settings)
    if provider_name == "gemini" and settings.gemini_api_key:
        return GeminiProvider(settings)

    if settings.openai_api_key:
        return OpenAIProvider(settings)
    if settings.gemini_api_key:
        return GeminiProvider(settings)

    return OfflineProvider()
