"""
Persistent session memory using Azure Cosmos DB.
Stores partial slot data between turns.
"""
from typing import Any, Dict
from db.cosmos_client import get_memory_document, save_memory_document


def get_session(conversation_id: str) -> Dict[str, Any]:
    """Return session dict (slots) for this conversation, or empty dict."""
    doc = get_memory_document(conversation_id)
    return doc.get("session", {})


def set_session(conversation_id: str, data: Dict[str, Any]) -> None:
    """Overwrite session dict for this conversation."""
    doc = get_memory_document(conversation_id)
    doc["session"] = data
    save_memory_document(doc)


def update_session(conversation_id: str, updates: Dict[str, Any]) -> None:
    """Merge updates into existing session."""
    doc = get_memory_document(conversation_id)
    session = doc.get("session", {})
    session.update(updates)
    doc["session"] = session
    save_memory_document(doc)


def clear_session(conversation_id: str) -> None:
    """Remove session for this conversation (clears slots but keeps history)."""
    doc = get_memory_document(conversation_id)
    doc["session"] = {}
    save_memory_document(doc)
