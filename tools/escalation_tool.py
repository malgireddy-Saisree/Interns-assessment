import json
from langchain_core.tools import tool
from tools.notification_tool import notification_tool
from db.sqlite_client import create_escalation

@tool
def trigger_escalation(customer_id: str, reason: str, conversation_summary: str = "", booking_id: str = "") -> str:
    """Trigger an escalation, file it in the DB, and notify front-desk.
    Args:
        customer_id: The customer ID if known.
        reason: Why the user wants to talk to a human.
        conversation_summary: Summary of what happened.
        booking_id: Relevant booking ID.
    Returns escalation confirmation.
    """
    result = create_escalation(
        customer_id=customer_id,
        reason=reason,
        conversation_summary=conversation_summary,
        booking_id=booking_id if booking_id else None,
    )

    # Notify front-desk
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
    return json.dumps(result, indent=2)
