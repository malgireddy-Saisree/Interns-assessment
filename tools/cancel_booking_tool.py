"""
Cancel an existing booking and process refund.
"""
import json
from langchain_core.tools import tool
from db.sqlite_client import cancel_booking


@tool
def cancel_booking_tool(booking_id: str) -> str:
    """Cancel a booking and process a refund based on cancellation policy. This WRITES to the database.
    Args:
        booking_id: The booking ID to cancel (e.g. 'BK1001').
    Returns a JSON string with cancellation + refund details or error.
    """
    result = cancel_booking(booking_id)
    return json.dumps(result, indent=2)
