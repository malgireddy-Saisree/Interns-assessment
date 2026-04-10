"""
Add services to an existing booking, or file a complaint.
"""
import json
from tools.tool_registry import tool
from db.sqlite_client import (
    add_booking_service,
    create_complaint,
    get_booking,
    get_services_for_hotel,
)


@tool
def guest_services_tool(
    action: str,
    booking_id: str,
    service_id: str = "",
    quantity: int = 1,
    complaint_type: str = "",
    complaint_description: str = "",
    priority: str = "medium",
) -> str:
    """Handle guest service requests: add a service to a booking or file a complaint. WRITES to the database.
    Args:
        action: Either 'add_service' or 'file_complaint'.
        booking_id: The booking ID (e.g. 'BK1001').
        service_id: Service ID to add (for 'add_service' action, e.g. 'SVC001').
        quantity: Quantity of the service (for 'add_service', default 1).
        complaint_type: Type of complaint, e.g. 'maintenance', 'cleanliness', 'noise' (for 'file_complaint').
        complaint_description: Detailed description of the complaint (for 'file_complaint').
        priority: Complaint priority — 'low', 'medium', or 'high' (for 'file_complaint').
    Returns a JSON string with result.
    """
    if action == "add_service":
        if not service_id:
            bk = get_booking(booking_id)
            if not bk:
                return json.dumps({"error": f"Booking '{booking_id}' not found."})
            services = get_services_for_hotel(bk["hotel_id"])
            return json.dumps({
                "message": "Please specify a service_id. Available services:",
                "available_services": services,
            }, indent=2, default=str)
        result = add_booking_service(booking_id, service_id, quantity)
        return json.dumps(result, indent=2, default=str)

    elif action == "file_complaint":
        bk = get_booking(booking_id)
        if not bk:
            return json.dumps({"error": f"Booking '{booking_id}' not found."})
        result = create_complaint(
            booking_id=booking_id,
            customer_id=bk["customer_id"],
            hotel_id=bk["hotel_id"],
            complaint_type=complaint_type,
            description=complaint_description,
            priority=priority,
        )
        return json.dumps(result, indent=2, default=str)

    else:
        return json.dumps({"error": f"Unknown action '{action}'. Use 'add_service' or 'file_complaint'."})
