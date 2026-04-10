"""
observability/stats.py
Reads business metrics from audit_log in stayease.db.
LangSmith handles LLM/tool stats — this handles business stats only.
"""

import sqlite3
import json

DB_PATH = "stayease.db"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_stats() -> dict:
    conn = _get_conn()
    cur  = conn.cursor()

    # Business metrics from actual tables
    cur.execute("SELECT COUNT(*) FROM bookings WHERE status = 'cancelled'")
    total_cancellations = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM bookings WHERE status = 'confirmed'")
    total_confirmed = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM bookings WHERE status = 'checked_in'")
    total_checked_in = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status = 'open'")
    open_complaints = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status = 'resolved'")
    resolved_complaints = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM escalations WHERE status = 'open'")
    open_escalations = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM refunds WHERE status = 'processing'")
    pending_refunds = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM refunds WHERE status = 'completed'")
    completed_refunds = cur.fetchone()[0]

    cur.execute("SELECT SUM(amount) FROM refunds WHERE status = 'completed'")
    total_refund_amount = cur.fetchone()[0] or 0

    # Complaint breakdown by type
    cur.execute("""
        SELECT type, COUNT(*) as count
        FROM   complaints
        GROUP  BY type
        ORDER  BY count DESC
    """)
    complaint_breakdown = {r["type"]: r["count"] for r in cur.fetchall()}

    # Recent audit events
    cur.execute("""
        SELECT * FROM audit_log
        ORDER  BY timestamp DESC
        LIMIT  20
    """)
    recent_events = [dict(r) for r in cur.fetchall()]

    # Cancellations over last 7 days
    cur.execute("""
        SELECT DATE(timestamp) AS day, COUNT(*) AS count
        FROM   audit_log
        WHERE  action = 'CANCELLATION'
        AND    timestamp >= DATE('now', '-7 days')
        GROUP  BY day
        ORDER  BY day
    """)
    cancellations_over_time = {r["day"]: r["count"] for r in cur.fetchall()}

    # Complaints over last 7 days
    cur.execute("""
        SELECT DATE(timestamp) AS day, COUNT(*) AS count
        FROM   audit_log
        WHERE  action = 'COMPLAINT_RAISED'
        AND    timestamp >= DATE('now', '-7 days')
        GROUP  BY day
        ORDER  BY day
    """)
    complaints_over_time = {r["day"]: r["count"] for r in cur.fetchall()}

    conn.close()

    return {
        # Booking metrics
        "total_cancellations":      total_cancellations,
        "total_confirmed":          total_confirmed,
        "total_checked_in":         total_checked_in,

        # Complaint metrics
        "open_complaints":          open_complaints,
        "resolved_complaints":      resolved_complaints,
        "complaint_breakdown":      complaint_breakdown,

        # Escalation metrics
        "open_escalations":         open_escalations,

        # Refund metrics
        "pending_refunds":          pending_refunds,
        "completed_refunds":        completed_refunds,
        "total_refund_amount":      total_refund_amount,

        # Time series
        "cancellations_over_time":  cancellations_over_time,
        "complaints_over_time":     complaints_over_time,

        # Recent events
        "recent_events":            recent_events,
    }


def print_stats():
    s = get_stats()
    print("\n" + "=" * 50)
    print("  StayEase — Business Metrics")
    print("=" * 50)
    print(f"  Confirmed Bookings   : {s['total_confirmed']}")
    print(f"  Checked In           : {s['total_checked_in']}")
    print(f"  Cancellations        : {s['total_cancellations']}")
    print(f"  Open Complaints      : {s['open_complaints']}")
    print(f"  Resolved Complaints  : {s['resolved_complaints']}")
    print(f"  Open Escalations     : {s['open_escalations']}")
    print(f"  Pending Refunds      : {s['pending_refunds']}")
    print(f"  Completed Refunds    : {s['completed_refunds']}")
    print(f"  Total Refunded       : Rs.{s['total_refund_amount']}")
    print(f"\n  Complaint Types:")
    for t, c in s["complaint_breakdown"].items():
        print(f"    {t:<20} {c}")
    print("=" * 50 + "\n")