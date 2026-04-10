"""
In-process session memory keyed by conversation_id.
Stores partial slot data between turns (e.g. check_in collected
but check_out not yet given). In production this would be Redis.
"""
from typing import Any, Dict

_store: Dict[str, Dict[str, Any]] = {}


def get_session(conversation_id: str) -> Dict[str, Any]:
    """Return session dict for this conversation, or empty dict."""
    return _store.get(conversation_id, {})


def set_session(conversation_id: str, data: Dict[str, Any]) -> None:
    """Overwrite session dict for this conversation."""
    _store[conversation_id] = data


def update_session(conversation_id: str, updates: Dict[str, Any]) -> None:
    """Merge updates into existing session."""
    session = get_session(conversation_id)
    session.update(updates)
    _store[conversation_id] = session


def clear_session(conversation_id: str) -> None:
    """Remove session for this conversation."""
    _store.pop(conversation_id, None)
