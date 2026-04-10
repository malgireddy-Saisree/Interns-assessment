"""
Escalation agent — triggered when the guest asks to speak to a human,
or after repeated failed resolution attempts. Inserts an escalation
record into the DB and sends a notification.
"""
import json
from typing import Dict, Any, Optional

from db.sqlite_client import create_escalation
from tools.notification_tool import notification_tool


def escalate(
    customer_id: str,
    reason: str,
    conversation_summary: str = "",
    booking_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an escalation in the database and notify front-desk staff.
    """
    result = create_escalation(
        customer_id=customer_id,
        reason=reason,
        conversation_summary=conversation_summary,
        booking_id=booking_id,
    )

    # Notify front-desk (placeholder)
    notification_tool.invoke({
        "recipient": "frontdesk@stayease.com",
        "subject": f"Escalation {result['escalation_id']} — {reason}",
        "message": (
            f"Customer {customer_id} has requested human assistance.\n"
            f"Reason: {reason}\n"
            f"Booking: {booking_id or 'N/A'}\n"
            f"Summary: {conversation_summary or 'N/A'}"
        ),
    })

    return result
