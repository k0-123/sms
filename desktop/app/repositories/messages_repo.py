"""CRUD + state-machine transitions for campaign messages.

Status flow: PENDING -> SENDING -> SENT | FAILED ; FAILED -> RETRY -> SENDING -> ...
`id` doubles as the protocol `message_id` (dedup key) sent to the Android app.
"""
import sqlite3
from typing import Optional

from app.db.connection import get_connection
from app.repositories._util import new_id, now_iso

TERMINAL_STATUSES = ("SENT", "FAILED")


def create(campaign_id: str, contact_id: str, phone_e164: str, rendered_text: str) -> str:
    conn = get_connection()
    message_id = new_id()
    ts = now_iso()
    conn.execute(
        """INSERT INTO messages
           (id, campaign_id, contact_id, phone_e164, rendered_text, status,
            attempt_count, synced_to_desktop, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, 'PENDING', 0, 0, ?, ?)""",
        (message_id, campaign_id, contact_id, phone_e164, rendered_text, ts, ts),
    )
    conn.commit()
    return message_id


def get(message_id: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    return conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()


def list_for_campaign(campaign_id: str, status: Optional[str] = None) -> list[sqlite3.Row]:
    conn = get_connection()
    query = "SELECT * FROM messages WHERE campaign_id = ?"
    params: list = [campaign_id]
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at ASC"
    return conn.execute(query, params).fetchall()


def next_dispatchable(campaign_id: str) -> Optional[sqlite3.Row]:
    """Next PENDING or RETRY message to dispatch, oldest first."""
    conn = get_connection()
    return conn.execute(
        """SELECT * FROM messages WHERE campaign_id = ? AND status IN ('PENDING', 'RETRY')
           ORDER BY created_at ASC LIMIT 1""",
        (campaign_id,),
    ).fetchone()


def mark_sending(message_id: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE messages SET status = 'SENDING', attempt_count = attempt_count + 1, "
        "dispatched_at = ?, updated_at = ? WHERE id = ?",
        (now_iso(), now_iso(), message_id),
    )
    conn.commit()


def mark_sent(message_id: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE messages SET status = 'SENT', error = NULL, sent_at = ?, "
        "synced_to_desktop = 1, updated_at = ? WHERE id = ?",
        (now_iso(), now_iso(), message_id),
    )
    conn.commit()


def mark_failed(message_id: str, error: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE messages SET status = 'FAILED', error = ?, synced_to_desktop = 1, "
        "updated_at = ? WHERE id = ?",
        (error, now_iso(), message_id),
    )
    conn.commit()


def mark_retry(message_id: str) -> bool:
    """Only allowed from FAILED. Never touches SENT rows. Returns True if applied."""
    conn = get_connection()
    cur = conn.execute(
        "UPDATE messages SET status = 'RETRY', updated_at = ? WHERE id = ? AND status = 'FAILED'",
        (now_iso(), message_id),
    )
    conn.commit()
    return cur.rowcount > 0


def retry_all_failed(campaign_id: str) -> int:
    conn = get_connection()
    cur = conn.execute(
        "UPDATE messages SET status = 'RETRY', updated_at = ? WHERE campaign_id = ? AND status = 'FAILED'",
        (now_iso(), campaign_id),
    )
    conn.commit()
    return cur.rowcount


def mark_synced(message_id: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE messages SET synced_to_desktop = 1, updated_at = ? WHERE id = ?",
        (now_iso(), message_id),
    )
    conn.commit()


def unsynced_sending() -> list[sqlite3.Row]:
    """Messages stuck in SENDING with no confirmed terminal status - reconciliation candidates."""
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM messages WHERE status = 'SENDING' AND synced_to_desktop = 0"
    ).fetchall()
