"""
Guest services agent — handles in-stay requests:
room service, housekeeping, maintenance, add-on services, complaints.
The planner routes here for guest service intents.
"""
import json
from typing import Dict, Any

from db.sqlite_client import (
    add_booking_service,
    create_complaint,
    get_booking,
    get_services_for_hotel,
)


def list_available_services(booking_id: str) -> Dict[str, Any]:
    """Return the list of services available for a booking's hotel."""
    bk = get_booking(booking_id)
    if not bk:
        return {"error": f"Booking '{booking_id}' not found."}
    services = get_services_for_hotel(bk["hotel_id"])
    return {
        "booking_id": booking_id,
        "hotel_id": bk["hotel_id"],
        "available_services": services,
    }


def add_service(booking_id: str, service_id: str, quantity: int = 1) -> Dict[str, Any]:
    """Add a service to a booking — writes to DB."""
    return add_booking_service(booking_id, service_id, quantity)


def file_complaint(
    booking_id: str,
    complaint_type: str,
    description: str,
    priority: str = "medium",
) -> Dict[str, Any]:
    """File a guest complaint — writes to DB."""
    bk = get_booking(booking_id)
    if not bk:
        return {"error": f"Booking '{booking_id}' not found."}
    return create_complaint(
        booking_id=booking_id,
        customer_id=bk["customer_id"],
        hotel_id=bk["hotel_id"],
        complaint_type=complaint_type,
        description=description,
        priority=priority,
    )
