"""
observability/tracker.py
Tracks ONLY business events to audit_log in stayease.db.
LangSmith handles tool/LLM traces — this handles business metrics only.
"""

import sqlite3
import json
from datetime import datetime
from observability.logger import log_info, log_error

DB_PATH = "stayease.db"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _write_to_audit(table_name, record_id, action, old_value="", new_value=""):
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO audit_log
                (table_name, record_id, action, old_value, new_value)
            VALUES (?, ?, ?, ?, ?)
        """, (table_name, str(record_id), action,
              str(old_value)[:500], str(new_value)[:500]))
        conn.commit()
        conn.close()
    except Exception as e:
        log_error(f"audit_log write failed | {e}")


def track_cancellation(booking_id: str, customer_id: str, refund_amount: float):
    """Call this when a booking is cancelled."""
    _write_to_audit(
        table_name = "bookings",
        record_id  = booking_id,
        action     = "CANCELLATION",
        new_value  = json.dumps({
            "customer_id":   customer_id,
            "refund_amount": refund_amount,
            "timestamp":     datetime.now().isoformat(),
        }),
    )
    log_info(f"CANCELLATION | booking={booking_id} | refund=Rs.{refund_amount}")


def track_complaint(complaint_id: str, booking_id: str, complaint_type: str, priority: str):
    """Call this when a complaint is raised."""
    _write_to_audit(
        table_name = "complaints",
        record_id  = complaint_id,
        action     = "COMPLAINT_RAISED",
        new_value  = json.dumps({
            "booking_id":     booking_id,
            "type":           complaint_type,
            "priority":       priority,
            "timestamp":      datetime.now().isoformat(),
        }),
    )
    log_info(f"COMPLAINT | id={complaint_id} | type={complaint_type} | priority={priority}")


def track_escalation(escalation_id: str, customer_id: str, reason: str):
    """Call this when conversation is escalated to human."""
    _write_to_audit(
        table_name = "escalations",
        record_id  = escalation_id,
        action     = "ESCALATION",
        new_value  = json.dumps({
            "customer_id": customer_id,
            "reason":      reason,
            "timestamp":   datetime.now().isoformat(),
        }),
    )
    log_info(f"ESCALATION | id={escalation_id} | reason={reason}")


def track_modification(booking_id: str, old_dates: str, new_dates: str):
    """Call this when booking dates are modified."""
    _write_to_audit(
        table_name = "bookings",
        record_id  = booking_id,
        action     = "MODIFICATION",
        old_value  = old_dates,
        new_value  = new_dates,
    )
    log_info(f"MODIFICATION | booking={booking_id} | {old_dates} → {new_dates}")


def track_error(source: str, error: Exception, context: dict = {}):
    """Call this when any unexpected error occurs."""
    _write_to_audit(
        table_name = source,
        record_id  = source,
        action     = "ERROR",
        new_value  = json.dumps({
            "error":   str(error),
            "context": {k: str(v) for k, v in context.items()},
        }),
    )
    log_error(f"ERROR | source={source} | {error}")