"""
test_observability.py
Tests observability tools using LIVE data from stayease.db.
Run: python test_observability.py
"""

import sqlite3
from observability.logger import log_info, log_debug, log_warning, log_error
from observability.tracker import (
    track_cancellation,
    track_complaint,
    track_escalation,
    track_modification,
    track_error,
)
from observability.stats import print_stats

DB_PATH = "stayease.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Fetch live data from DB ───────────────────────────────────────────────────
conn = get_conn()
cur  = conn.cursor()

cur.execute("SELECT booking_id, customer_id, grand_total FROM bookings LIMIT 1")
booking = dict(cur.fetchone())

cur.execute("SELECT complaint_id, booking_id, type, priority FROM complaints LIMIT 1")
complaint_row = cur.fetchone()
complaint = dict(complaint_row) if complaint_row else None

cur.execute("SELECT escalation_id, customer_id, reason FROM escalations LIMIT 1")
escalation_row = cur.fetchone()
escalation = dict(escalation_row) if escalation_row else None

cur.execute("SELECT booking_id, check_in, check_out FROM bookings LIMIT 1")
mod = dict(cur.fetchone())

conn.close()

print(f"\n📦 Live data loaded from DB")
print(f"   Booking  : {booking}")
print(f"   Complaint: {complaint}")
print(f"   Escalation: {escalation}")


# ── Test Logger ───────────────────────────────────────────────────────────────
print("\n--- Testing Logger ---")
log_info(f"Testing with live booking: {booking['booking_id']}")
log_debug(f"Booking grand total: Rs.{booking['grand_total']}")
log_warning("This is a warning log test")
log_error("This is an error log test")
print("✅ Logger working — check stayease_agent.log")


# ── Test Tracker ──────────────────────────────────────────────────────────────
print("\n--- Testing Tracker with live data ---")

track_cancellation(booking["booking_id"], booking["customer_id"], booking["grand_total"])
print(f"✅ track_cancellation | booking={booking['booking_id']} | refund=Rs.{booking['grand_total']}")

if complaint:
    track_complaint(complaint["complaint_id"], complaint["booking_id"], complaint["type"], complaint["priority"])
    print(f"✅ track_complaint | id={complaint['complaint_id']} | type={complaint['type']}")
else:
    print("⚠️  No complaints in DB to test with")

if escalation:
    track_escalation(escalation["escalation_id"], escalation["customer_id"], escalation["reason"])
    print(f"✅ track_escalation | id={escalation['escalation_id']}")
else:
    print("⚠️  No escalations in DB to test with")

track_modification(
    mod["booking_id"],
    f"{mod['check_in']} to {mod['check_out']}",
    "2026-05-01 to 2026-05-05"
)
print(f"✅ track_modification | booking={mod['booking_id']}")

track_error("test", Exception("live test error"), {"booking_id": booking["booking_id"]})
print("✅ track_error done")


# ── Print live stats ──────────────────────────────────────────────────────────
print("\n--- Live Business Metrics from DB ---")
print_stats()


# ── Show last 5 audit log entries ─────────────────────────────────────────────
print("--- Last 5 Audit Log Entries ---")
conn = get_conn()
cur  = conn.cursor()
cur.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 5")
for row in cur.fetchall():
    r = dict(row)
    print(f"  [{r['timestamp']}] {r['action']} | {r['record_id']}")
conn.close()

print("\n✅ All observability tools tested with live data!")
print("📁 Check stayease_agent.log for file logs")