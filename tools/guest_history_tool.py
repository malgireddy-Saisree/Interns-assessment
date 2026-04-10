"""
Look up guest profile and booking history.
"""
import json
from langchain_core.tools import tool
from db.sqlite_client import get_customer, get_customer_bookings, get_customer_by_email


@tool
def guest_history_tool(customer_id: str = "", email: str = "") -> str:
    """Look up a guest's profile and their recent booking history.
    Args:
        customer_id: Customer ID (e.g. 'C001'). Provide this OR email.
        email: Customer email. Provide this OR customer_id.
    Returns a JSON string with customer profile and last 5 bookings.
    """
    customer = None
    if customer_id:
        customer = get_customer(customer_id)
    elif email:
        customer = get_customer_by_email(email)

    if not customer:
        return json.dumps({"error": "Customer not found."})

    bookings = get_customer_bookings(customer["customer_id"], limit=5)
    return json.dumps({"customer": customer, "recent_bookings": bookings}, indent=2, default=str)
