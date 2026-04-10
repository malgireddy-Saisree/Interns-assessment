"""
Check room availability for a given hotel, room type, and date range.
"""
import json
from langchain_core.tools import tool
from db.sqlite_client import get_available_rooms, get_all_hotels, get_room_types


@tool
def availability_tool(
    check_in: str,
    check_out: str,
    room_type: str = "",
    hotel_id: str = "",
) -> str:
    """Check room availability at a StayEase hotel.
    Args:
        check_in: Check-in date in YYYY-MM-DD format.
        check_out: Check-out date in YYYY-MM-DD format.
        room_type: Room type — 'standard', 'deluxe', or 'suite'. If empty, checks all types.
        hotel_id: Hotel ID (e.g. 'H001'). If empty, checks all hotels.
    Returns a JSON string with availability details.
    """
    results = []
    if hotel_id:
        hotel_ids = [hotel_id]
    else:
        hotels = get_all_hotels()
        hotel_ids = [h["hotel_id"] for h in hotels]

    for hid in hotel_ids:
        if room_type:
            types = [room_type]
        else:
            rt = get_room_types(hid)
            types = [r["room_type"] for r in rt]
        for rt_name in types:
            avail = get_available_rooms(hid, rt_name, check_in, check_out)
            results.append(avail)

    return json.dumps(results, indent=2)
