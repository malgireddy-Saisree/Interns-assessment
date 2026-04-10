"""
Search for hotel information and FAQs.
Uses SQLite queries against hotels, room_types, and services tables,
plus a static FAQ dictionary for common questions.
"""
import json
from tools.tool_registry import tool
from db.sqlite_client import get_all_hotels, get_room_types, get_services_for_hotel

# Static FAQ for common questions
_STATIC_FAQ = {
    "check_in_time": "Check-in time varies by hotel. StayEase City Grand: 14:00 (2 PM). StayEase Beach Resort: 15:00 (3 PM).",
    "check_out_time": "Check-out time varies by hotel. StayEase City Grand: 12:00 (noon). StayEase Beach Resort: 11:00 (11 AM).",
    "cancellation_policy": (
        "Our cancellation policy:\n"
        "• Free cancellation if cancelled 48+ hours before check-in (full refund)\n"
        "• 50% refund if cancelled 24-48 hours before check-in\n"
        "• No refund if cancelled less than 24 hours before check-in\n"
        "(Exact hours vary by hotel.)"
    ),
    "pet_policy": "Pets are not allowed at StayEase properties. Service animals are an exception with prior approval.",
    "parking": "Free valet parking is available at StayEase City Grand. StayEase Beach Resort offers complimentary self-parking.",
    "wifi": "Complimentary high-speed WiFi is available in all rooms and public areas at all StayEase properties.",
    "payment_methods": "We accept Credit Cards, Debit Cards, UPI, and Net Banking.",
    "loyalty_program": (
        "StayEase Loyalty Tiers:\n"
        "• Bronze: 0-999 points — base benefits\n"
        "• Silver: 1000-2999 points — 5% discount, late checkout\n"
        "• Gold: 3000+ points — 10% discount, room upgrades, complimentary breakfast"
    ),
}


@tool
def faq_search_tool(question: str) -> str:
    """Search for hotel information, room details, services, policies, and FAQs.
    Args:
        question: The user's question about the hotel, rooms, services, or policies.
    Returns a JSON string with relevant information.
    """
    q = question.lower()
    results = {}

    # Check static FAQ
    faq_matches = []
    keywords_map = {
        "check_in_time": ["check in", "check-in", "checkin", "arrival time"],
        "check_out_time": ["check out", "check-out", "checkout", "departure time"],
        "cancellation_policy": ["cancel", "cancellation", "refund policy"],
        "pet_policy": ["pet", "dog", "cat", "animal"],
        "parking": ["parking", "valet", "car"],
        "wifi": ["wifi", "wi-fi", "internet"],
        "payment_methods": ["payment", "pay", "credit", "debit", "upi"],
        "loyalty_program": ["loyalty", "points", "tier", "rewards", "membership"],
    }
    for key, keywords in keywords_map.items():
        if any(kw in q for kw in keywords):
            faq_matches.append({"topic": key, "answer": _STATIC_FAQ[key]})

    if faq_matches:
        results["faq"] = faq_matches

    if any(w in q for w in ["hotel", "property", "location", "address", "phone", "contact", "amenities", "facilities"]):
        results["hotels"] = get_all_hotels()

    if any(w in q for w in ["room", "suite", "deluxe", "standard", "price", "rate", "cost", "occupancy"]):
        rooms_all = []
        for h in get_all_hotels():
            rts = get_room_types(h["hotel_id"])
            for rt in rts:
                rt["hotel_name"] = h["name"]
            rooms_all.extend(rts)
        results["rooms"] = rooms_all

    if any(w in q for w in ["service", "spa", "breakfast", "dinner", "transfer", "airport", "sport", "romantic"]):
        services_all = []
        for h in get_all_hotels():
            svcs = get_services_for_hotel(h["hotel_id"])
            for s in svcs:
                s["hotel_name"] = h["name"]
            services_all.extend(svcs)
        results["services"] = services_all

    if not results:
        results["hotels"] = get_all_hotels()
        results["note"] = "No specific match found. Here is general hotel information."

    return json.dumps(results, indent=2, default=str)
