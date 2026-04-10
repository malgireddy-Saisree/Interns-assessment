"""
SQLite database client for StayEase.
Provides connection management, generic query/execute helpers,
and domain-specific helpers that read and WRITE to the database.
"""
import sqlite3
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from config.settings import DB_PATH


# ── Connection ────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Return a connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── Generic helpers ───────────────────────────────────────────

def query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Run a SELECT and return a list of dicts."""
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()) -> int:
    """Run an INSERT / UPDATE / DELETE and return rowcount."""
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


# ── Audit log ─────────────────────────────────────────────────

def log_audit(
    table_name: str,
    record_id: str,
    action: str,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
) -> None:
    """Write an entry to the audit_log table."""
    execute(
        "INSERT INTO audit_log (table_name, record_id, action, old_value, new_value) "
        "VALUES (?, ?, ?, ?, ?)",
        (table_name, record_id, action, old_value, new_value),
    )


# ── Hotel / Room helpers ──────────────────────────────────────

def get_hotel(hotel_id: str) -> Optional[Dict[str, Any]]:
    """Get a single hotel by ID."""
    rows = query("SELECT * FROM hotels WHERE hotel_id = ?", (hotel_id,))
    return rows[0] if rows else None


def get_all_hotels() -> List[Dict[str, Any]]:
    """Return every hotel."""
    return query("SELECT * FROM hotels")


def get_room_types(hotel_id: str) -> List[Dict[str, Any]]:
    """Return all room types for a hotel."""
    return query("SELECT * FROM room_types WHERE hotel_id = ?", (hotel_id,))


def get_services_for_hotel(hotel_id: str) -> List[Dict[str, Any]]:
    """Return all services offered by a hotel."""
    return query("SELECT * FROM services WHERE hotel_id = ?", (hotel_id,))


# ── Availability ──────────────────────────────────────────────

def get_available_rooms(
    hotel_id: str,
    room_type: str,
    check_in: str,
    check_out: str,
) -> Dict[str, Any]:
    """
    Count how many rooms of (hotel_id, room_type) are already booked
    in the overlapping date range, then subtract from total_rooms.
    Returns dict with available_count, price_per_night, total_rooms.
    """
    # Get total rooms for this type
    rt_rows = query(
        "SELECT total_rooms, price_per_night FROM room_types "
        "WHERE hotel_id = ? AND room_type = ?",
        (hotel_id, room_type),
    )
    if not rt_rows:
        return {"error": f"Room type '{room_type}' not found at hotel '{hotel_id}'."}

    total = rt_rows[0]["total_rooms"]
    price = rt_rows[0]["price_per_night"]

    # Count overlapping confirmed / checked-in bookings
    overlap = query(
        "SELECT COUNT(*) AS cnt FROM bookings "
        "WHERE hotel_id = ? AND room_type = ? "
        "AND status IN ('confirmed', 'checked_in') "
        "AND check_in < ? AND check_out > ?",
        (hotel_id, room_type, check_out, check_in),
    )
    booked = overlap[0]["cnt"] if overlap else 0
    available = max(0, total - booked)

    return {
        "hotel_id": hotel_id,
        "room_type": room_type,
        "check_in": check_in,
        "check_out": check_out,
        "total_rooms": total,
        "booked_rooms": booked,
        "available_rooms": available,
        "price_per_night": price,
    }


# ── Booking ───────────────────────────────────────────────────

def create_booking(
    customer_id: str,
    hotel_id: str,
    room_type: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    special_requests: str = "",
    payment_method: str = "credit_card",
) -> Dict[str, Any]:
    """
    Insert a new booking, update customer total_stays, log audit.
    Returns the full booking dict on success, or error dict.
    """
    # Validate customer exists
    cust = get_customer(customer_id)
    if not cust:
        return {"error": f"Customer '{customer_id}' not found."}

    # Check availability
    avail = get_available_rooms(hotel_id, room_type, check_in, check_out)
    if "error" in avail:
        return avail
    if avail["available_rooms"] <= 0:
        return {"error": f"No {room_type} rooms available at {hotel_id} for {check_in} to {check_out}."}

    # Calculate cost
    d_in = date.fromisoformat(check_in)
    d_out = date.fromisoformat(check_out)
    nights = (d_out - d_in).days
    if nights <= 0:
        return {"error": "check_out must be after check_in."}

    price = avail["price_per_night"]
    total_room_cost = price * nights
    grand_total = total_room_cost  # services added later

    booking_id = f"BK{uuid.uuid4().hex[:6].upper()}"
    now = datetime.now().isoformat(sep=" ", timespec="seconds")

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO bookings "
            "(booking_id, customer_id, hotel_id, room_type, check_in, check_out, "
            " nights, guests, room_price_per_night, total_room_cost, "
            " total_services_cost, grand_total, amount_paid, status, "
            " payment_method, payment_status, refund_amount, refund_date, "
            " special_requests, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?,?,?,?,0,NULL,?,?,?)",
            (
                booking_id, customer_id, hotel_id, room_type,
                check_in, check_out, nights, guests,
                price, total_room_cost, grand_total, grand_total,
                "confirmed", payment_method, "paid",
                special_requests, now, now,
            ),
        )
        # Update customer total_stays
        conn.execute(
            "UPDATE customers SET total_stays = total_stays + 1 WHERE customer_id = ?",
            (customer_id,),
        )
        conn.commit()
    finally:
        conn.close()

    log_audit("bookings", booking_id, "INSERT", None, f"New booking for {customer_id}")

    hotel = get_hotel(hotel_id)
    hotel_name = hotel["name"] if hotel else hotel_id

    return {
        "booking_id": booking_id,
        "customer_id": customer_id,
        "customer_name": cust["name"],
        "hotel_name": hotel_name,
        "room_type": room_type,
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "guests": guests,
        "price_per_night": price,
        "total_room_cost": total_room_cost,
        "grand_total": grand_total,
        "status": "confirmed",
        "payment_status": "paid",
    }


# ── Cancel Booking ────────────────────────────────────────────

def cancel_booking(booking_id: str) -> Dict[str, Any]:
    """
    Cancel a booking: set status='cancelled', calculate refund based
    on hotel cancellation policy, insert into refunds table.
    """
    rows = query("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
    if not rows:
        return {"error": f"Booking '{booking_id}' not found."}

    bk = rows[0]
    if bk["status"] in ("cancelled", "completed"):
        return {"error": f"Booking is already '{bk['status']}'. Cannot cancel."}

    hotel = get_hotel(bk["hotel_id"])
    if not hotel:
        return {"error": "Hotel not found for this booking."}

    # Calculate hours until check-in
    checkin_dt = datetime.fromisoformat(bk["check_in"])
    hours_until = (checkin_dt - datetime.now()).total_seconds() / 3600

    # Determine refund based on hotel's cancellation tiers
    free_hours = hotel.get("free_cancel_hours", 48) or 48
    partial_hours = hotel.get("no_refund_hours", 24) or 24
    partial_pct = hotel.get("partial_refund_pct", 50) or 50

    amount_paid = bk["amount_paid"] or bk["grand_total"]

    if hours_until >= free_hours:
        refund_amount = amount_paid  # full refund
        refund_reason = "Free cancellation applied"
    elif hours_until >= partial_hours:
        refund_amount = round(amount_paid * partial_pct / 100, 2)
        refund_reason = f"Partial refund ({partial_pct}%) applied"
    else:
        refund_amount = 0
        refund_reason = "No refund — cancelled within no-refund window"

    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    refund_id = f"REF{uuid.uuid4().hex[:6].upper()}"

    conn = get_connection()
    try:
        old_status = bk["status"]
        conn.execute(
            "UPDATE bookings SET status = 'cancelled', payment_status = 'refunded', "
            "refund_amount = ?, refund_date = ?, updated_at = ? WHERE booking_id = ?",
            (refund_amount, now, now, booking_id),
        )
        conn.execute(
            "INSERT INTO refunds (refund_id, booking_id, customer_id, amount, reason, status, "
            "initiated_at, completed_at) VALUES (?,?,?,?,?,?,?,?)",
            (refund_id, booking_id, bk["customer_id"], refund_amount,
             refund_reason, "completed", now, now),
        )
        conn.commit()
    finally:
        conn.close()

    log_audit("bookings", booking_id, "CANCEL", f"status={old_status}", "status=cancelled")

    return {
        "booking_id": booking_id,
        "previous_status": old_status,
        "new_status": "cancelled",
        "refund_id": refund_id,
        "refund_amount": refund_amount,
        "refund_reason": refund_reason,
    }


# ── Booking Services ──────────────────────────────────────────

def add_booking_service(
    booking_id: str,
    service_id: str,
    quantity: int = 1,
) -> Dict[str, Any]:
    """
    Add a service to a booking. Inserts into booking_services and
    recalculates total_services_cost + grand_total on the booking row.
    """
    # Validate booking
    bk_rows = query("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
    if not bk_rows:
        return {"error": f"Booking '{booking_id}' not found."}
    bk = bk_rows[0]

    if bk["status"] in ("cancelled", "completed"):
        return {"error": f"Cannot add services — booking is '{bk['status']}'."}

    # Validate service
    svc_rows = query("SELECT * FROM services WHERE service_id = ?", (service_id,))
    if not svc_rows:
        return {"error": f"Service '{service_id}' not found."}
    svc = svc_rows[0]

    cost = svc["price"] * quantity

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO booking_services (booking_id, service_id, quantity, cost) VALUES (?,?,?,?)",
            (booking_id, service_id, quantity, cost),
        )
        # Recalculate totals
        conn.execute(
            "UPDATE bookings SET "
            " total_services_cost = (SELECT COALESCE(SUM(cost),0) FROM booking_services WHERE booking_id = ?), "
            " grand_total = total_room_cost + (SELECT COALESCE(SUM(cost),0) FROM booking_services WHERE booking_id = ?), "
            " updated_at = ? "
            "WHERE booking_id = ?",
            (booking_id, booking_id, datetime.now().isoformat(sep=" ", timespec="seconds"), booking_id),
        )
        conn.commit()
    finally:
        conn.close()

    log_audit("booking_services", booking_id, "ADD_SERVICE", None, f"{service_id} x{quantity}")

    return {
        "booking_id": booking_id,
        "service_added": svc["name"],
        "quantity": quantity,
        "cost": cost,
        "message": f"Added {svc['name']} (x{quantity}) for ₹{cost} to booking {booking_id}.",
    }


# ── Customer helpers ──────────────────────────────────────────

def get_customer(customer_id: str) -> Optional[Dict[str, Any]]:
    """Get a single customer by ID."""
    rows = query("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    return rows[0] if rows else None


def get_customer_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Look up a customer by email."""
    rows = query("SELECT * FROM customers WHERE email = ?", (email,))
    return rows[0] if rows else None

def create_customer(name: str, email: str, phone: str = "") -> Dict[str, Any]:
    """Register a new customer and return their profile."""
    # Check if email already exists
    existing = get_customer_by_email(email)
    if existing:
        return {"error": f"Customer with email '{email}' already exists.", "customer_id": existing["customer_id"]}
    
    # Generate ID and insert
    cust_id = f"C{uuid.uuid4().hex[:4].upper()}"
    execute(
        "INSERT INTO customers (customer_id, name, email, phone) "
        "VALUES (?, ?, ?, ?)",
        (cust_id, name, email, phone)
    )
    
    return {
        "customer_id": cust_id,
        "name": name,
        "email": email,
        "phone": phone,
        "loyalty_points": 0,
        "total_stays": 0
    }


def get_booking(booking_id: str) -> Optional[Dict[str, Any]]:
    """Get a single booking by ID."""
    rows = query("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
    return rows[0] if rows else None


def get_customer_bookings(customer_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Return a customer's most recent bookings."""
    return query(
        "SELECT * FROM bookings WHERE customer_id = ? ORDER BY created_at DESC LIMIT ?",
        (customer_id, limit),
    )


# ── Complaints ────────────────────────────────────────────────

def create_complaint(
    booking_id: str,
    customer_id: str,
    hotel_id: str,
    complaint_type: str,
    description: str,
    priority: str = "medium",
) -> Dict[str, Any]:
    """Insert a new complaint and return its ID."""
    complaint_id = f"CMP{uuid.uuid4().hex[:6].upper()}"
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    execute(
        "INSERT INTO complaints "
        "(complaint_id, booking_id, customer_id, hotel_id, type, description, "
        " status, priority, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (complaint_id, booking_id, customer_id, hotel_id,
         complaint_type, description, "open", priority, now, now),
    )
    log_audit("complaints", complaint_id, "INSERT", None, description)
    return {
        "complaint_id": complaint_id,
        "status": "open",
        "message": f"Complaint {complaint_id} registered. Our team will look into it.",
    }


# ── Escalations ──────────────────────────────────────────────

def create_escalation(
    customer_id: str,
    reason: str,
    conversation_summary: str = "",
    booking_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert an escalation record."""
    # Ensure the customer exists to avoid Foreign Key constraint failures
    existing_cust = get_customer(customer_id)
    if not existing_cust:
        customer_id = "UNKNOWN"
        if not get_customer("UNKNOWN"):
            execute(
                "INSERT INTO customers (customer_id, name, email) VALUES (?, ?, ?)",
                ("UNKNOWN", "Anonymous User", "anonymous@stayease.com")
            )

    esc_id = f"ESC{uuid.uuid4().hex[:6].upper()}"
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    execute(
        "INSERT INTO escalations "
        "(escalation_id, booking_id, customer_id, reason, conversation_summary, "
        " status, created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (esc_id, booking_id, customer_id, reason, conversation_summary, "open", now),
    )
    log_audit("escalations", esc_id, "INSERT", None, reason)
    return {
        "escalation_id": esc_id,
        "status": "open",
        "message": "Your request has been escalated to our front desk team. "
                   "A staff member will reach out to you shortly.",
    }
