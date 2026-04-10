"""
Booking agent — handles the multi-turn slot-filling flow for new bookings.
The planner delegates here when booking intent is detected.

In the current architecture the planner's GPT-4o + tool loop handles
slot filling automatically (the system prompt instructs it to collect
all fields before calling booking_tool). This module provides a
helper that the planner could invoke for more complex booking logic.
"""
import json
from typing import Dict, Any, Optional

from db.sqlite_client import get_available_rooms, create_booking
from memory.session_memory import get_session, update_session

REQUIRED_SLOTS = [
    "customer_id", "hotel_id", "room_type", "check_in", "check_out", "guests"
]


def check_slots(conversation_id: str) -> Dict[str, Any]:
    """
    Check which booking slots are already collected in the session.
    Returns dict with 'complete' bool and 'missing' list.
    """
    session = get_session(conversation_id)
    booking_data = session.get("booking_slots", {})
    missing = [s for s in REQUIRED_SLOTS if s not in booking_data or not booking_data[s]]
    return {
        "complete": len(missing) == 0,
        "missing": missing,
        "collected": booking_data,
    }


def update_slots(conversation_id: str, new_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge new slot values into the session and return updated status.
    """
    session = get_session(conversation_id)
    booking_data = session.get("booking_slots", {})
    booking_data.update({k: v for k, v in new_data.items() if v})
    update_session(conversation_id, {"booking_slots": booking_data})
    return check_slots(conversation_id)


def execute_booking(conversation_id: str) -> Dict[str, Any]:
    """
    If all slots are filled, run availability check then create the booking.
    Clears the booking slots from session on success.
    """
    status = check_slots(conversation_id)
    if not status["complete"]:
        return {"error": f"Missing slots: {status['missing']}"}

    data = status["collected"]

    # Check availability first
    avail = get_available_rooms(
        data["hotel_id"], data["room_type"], data["check_in"], data["check_out"]
    )
    if "error" in avail:
        return avail
    if avail["available_rooms"] <= 0:
        return {"error": "No rooms available for the requested dates and type."}

    # Create booking
    result = create_booking(
        customer_id=data["customer_id"],
        hotel_id=data["hotel_id"],
        room_type=data["room_type"],
        check_in=data["check_in"],
        check_out=data["check_out"],
        guests=int(data.get("guests", 1)),
        special_requests=data.get("special_requests", ""),
        payment_method=data.get("payment_method", "credit_card"),
    )

    if "error" not in result:
        # Clear booking slots from session
        session = get_session(conversation_id)
        session.pop("booking_slots", None)
        update_session(conversation_id, session)

    return result
