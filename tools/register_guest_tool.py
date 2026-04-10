"""
Register a new guest in the system.
"""
import json
from langchain_core.tools import tool
from db.sqlite_client import create_customer


@tool
def register_guest_tool(name: str, email: str, phone: str = "") -> str:
    """Register a new customer/guest in the system. Use this if the guest does not already have an ID. WRITES to the database.
    Args:
        name: Full name of the new guest.
        email: Email address of the new guest.
        phone: Phone number of the new guest (optional).
    Returns a JSON string with the newly created customer profile.
    """
    result = create_customer(name=name, email=email, phone=phone)
    return json.dumps(result, indent=2)
