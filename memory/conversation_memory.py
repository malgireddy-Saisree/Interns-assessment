"""
LangChain ConversationBufferWindowMemory wrapper.
Keeps the last k turns per conversation_id so GPT-4o has context
of the full conversation so far.
"""
from typing import Dict, List
from dataclasses import dataclass, field
from config.settings import CONVERSATION_WINDOW_SIZE


@dataclass
class _Message:
    type: str  # "human" or "ai"
    content: str


class _ChatMemory:
    """Simple chat memory that stores messages in a list."""

    def __init__(self, k: int = 10):
        self.k = k
        self.messages: List[_Message] = []

    def add_user_message(self, content: str) -> None:
        self.messages.append(_Message(type="human", content=content))
        self._trim()

    def add_ai_message(self, content: str) -> None:
        self.messages.append(_Message(type="ai", content=content))
        self._trim()

    def _trim(self) -> None:
        # Keep last k pairs (2*k messages)
        max_msgs = self.k * 2
        if len(self.messages) > max_msgs:
            self.messages = self.messages[-max_msgs:]


class ConversationMemory:
    """Wrapper mimicking LangChain's ConversationBufferWindowMemory."""

    def __init__(self, k: int = 10):
        self.chat_memory = _ChatMemory(k=k)


_memories: Dict[str, ConversationMemory] = {}


def get_memory(conversation_id: str) -> ConversationMemory:
    """Return (or create) the memory object for a conversation."""
    if conversation_id not in _memories:
        _memories[conversation_id] = ConversationMemory(k=CONVERSATION_WINDOW_SIZE)
    return _memories[conversation_id]


def get_history_str(conversation_id: str) -> str:
    """Return conversation history as a formatted string for prompt injection."""
    mem = get_memory(conversation_id)
    messages = mem.chat_memory.messages
    if not messages:
        return "(No previous conversation)"
    lines = []
    for msg in messages:
        role = "User" if msg.type == "human" else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)
