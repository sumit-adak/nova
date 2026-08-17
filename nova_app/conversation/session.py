"""Session state representation for active conversation."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from nova_app.conversation.models import ConversationTurn


@dataclass
class ConversationSession:
    """Active in-memory session holding multi-turn history."""
    session_id: int
    title: str = "New Conversation"
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    turns: list[ConversationTurn] = field(default_factory=list)

    def add_turn(self, turn: ConversationTurn) -> None:
        self.turns.append(turn)

    def to_message_list(self, max_turns: int = 10) -> list[dict[str, str]]:
        """Format history for LLM message context."""
        messages: list[dict[str, str]] = []
        recent_turns = self.turns[-max_turns:]
        for turn in recent_turns:
            messages.append({"role": "user", "content": turn.user_input})
            if turn.assistant_response:
                messages.append({"role": "assistant", "content": turn.assistant_response})
        return messages
