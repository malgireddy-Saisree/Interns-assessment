"""
Notification placeholder — logs to console and audit_log.
In production this would send email/SMS via Azure Communication Services.
"""
import json
from datetime import datetime
from tools.tool_registry import tool
from db.sqlite_client import log_audit


@tool
def notification_tool(
    recipient: str,
    subject: str,
    message: str,
) -> str:
    """Send a notification to a guest or staff member (logs to console in dev mode).
    Args:
        recipient: Email address or name of the recipient.
        subject: Subject line of the notification.
        message: Body of the notification message.
    Returns confirmation that the notification was logged.
    """
    timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")
    print(f"\n[NOTIFICATION] [{timestamp}]")
    print(f"   To:      {recipient}")
    print(f"   Subject: {subject}")
    print(f"   Message: {message}\n")

    log_audit("notifications", recipient, "SEND", None, f"{subject}: {message}")

    return json.dumps({
        "status": "sent",
        "recipient": recipient,
        "subject": subject,
        "timestamp": timestamp,
        "note": "Notification logged (email/SMS not configured in dev mode).",
    }, indent=2)
