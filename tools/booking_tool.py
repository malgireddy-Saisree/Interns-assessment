"""
Create a new booking in the database.
"""
import json
from tools.tool_registry import tool
from db.sqlite_client import create_booking


@tool
def booking_tool(
    customer_id: str,
    hotel_id: str,
    room_type: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    special_requests: str = "",
    payment_method: str = "credit_card",
) -> str:
    """Book a room at a StayEase hotel. This WRITES to the database.
    Args:
        customer_id: Customer ID (e.g. 'C001').
        hotel_id: Hotel ID (e.g. 'H001').
        room_type: Room type — 'standard', 'deluxe', or 'suite'.
        check_in: Check-in date in YYYY-MM-DD format.
        check_out: Check-out date in YYYY-MM-DD format.
        guests: Number of guests (default 1).
        special_requests: Any special requests for the booking.
        payment_method: Payment method — 'credit_card', 'debit_card', 'upi', 'net_banking'.
    Returns a JSON string with booking confirmation or error.
    """
    result = create_booking(
        customer_id=customer_id,
        hotel_id=hotel_id,
        room_type=room_type,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        special_requests=special_requests,
        payment_method=payment_method,
    )
    return json.dumps(result, indent=2)
