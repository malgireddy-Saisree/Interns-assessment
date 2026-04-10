"""
Persistent conversation memory using Azure Cosmos DB.
Keeps the last k turns per conversation_id.
"""
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from config.settings import CONVERSATION_WINDOW_SIZE
from db.cosmos_client import get_memory_document, save_memory_document


@dataclass
class _Message:
    type: str  
    content: str


class _CosmosChatMemory:
    """Chat memory that persists messages into Cosmos DB."""

    def __init__(self, conversation_id: str, k: int = 10):
        self.conversation_id = conversation_id
        self.k = k

    @property
    def messages(self) -> List[_Message]:
        """Fetch messages from Cosmos DB."""
        doc = get_memory_document(self.conversation_id)
        history = doc.get("history", [])
        return [_Message(**m) for m in history]

    def add_user_message(self, content: str) -> None:
        """Add human message and persist."""
        self._add_message("human", content)

    def add_ai_message(self, content: str) -> None:
        """Add assistant message and persist."""
        self._add_message("ai", content)

    def _add_message(self, msg_type: str, content: str) -> None:
        doc = get_memory_document(self.conversation_id)
        history = doc.get("history", [])
        history.append({"type": msg_type, "content": content})
        
        # Trim history: keep last k pairs (2*k messages)
        max_msgs = self.k * 2
        if len(history) > max_msgs:
            history = history[-max_msgs:]
        
        doc["history"] = history
        save_memory_document(doc)


class ConversationMemory:
    """Wrapper that matches the previous session-based interface but uses Cosmos DB."""

    def __init__(self, conversation_id: str, k: int = 10):
        self.chat_memory = _CosmosChatMemory(conversation_id, k=k)


def get_memory(conversation_id: str) -> ConversationMemory:
    """Return a memory object for a conversation, linked to Cosmos DB."""
    return ConversationMemory(conversation_id, k=CONVERSATION_WINDOW_SIZE)


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
