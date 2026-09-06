"""CRUD for campaigns."""
import sqlite3
from typing import Optional

from app.config import DEFAULT_DAILY_LIMIT, DEFAULT_RATE_LIMIT_MS, DEFAULT_RING_DURATION_SEC
from app.db.connection import get_connection
from app.repositories._util import new_id, now_iso


def create(
    name: str,
    message_body: str,
    campaign_type: str = "SMS",
    template_id: Optional[str] = None,
    device_id: Optional[str] = None,
    rate_limit_ms: int = DEFAULT_RATE_LIMIT_MS,
    daily_limit: int = DEFAULT_DAILY_LIMIT,
    ring_duration_sec: int = DEFAULT_RING_DURATION_SEC,
) -> str:
    conn = get_connection()
    campaign_id = new_id()
    ts = now_iso()
    conn.execute(
        """INSERT INTO campaigns
           (id, name, campaign_type, template_id, message_body, device_id, status, auto_paused,
            total_count, sent_count, failed_count, rate_limit_ms, daily_limit, ring_duration_sec,
            created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, 'DRAFT', 0, 0, 0, 0, ?, ?, ?, ?, ?)""",
        (campaign_id, name, campaign_type, template_id, message_body, device_id,
         rate_limit_ms, daily_limit, ring_duration_sec, ts, ts),
    )
    conn.commit()
    return campaign_id


def get(campaign_id: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    return conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()


def list_all() -> list[sqlite3.Row]:
    conn = get_connection()
    return conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC").fetchall()


def update_status(
    campaign_id: str, status: str, auto_paused: bool = False, pause_reason: Optional[str] = None
) -> None:
    conn = get_connection()
    completed_at = now_iso() if status == "COMPLETED" else None
    conn.execute(
        """UPDATE campaigns SET status = ?, auto_paused = ?, pause_reason = ?, updated_at = ?,
           completed_at = COALESCE(?, completed_at) WHERE id = ?""",
        (status, 1 if auto_paused else 0, pause_reason, now_iso(), completed_at, campaign_id),
    )
    conn.commit()


def refresh_counts(campaign_id: str) -> None:
    """Recompute total/sent/failed counts from the messages table."""
    conn = get_connection()
    row = conn.execute(
        """SELECT COUNT(*) AS total,
                  SUM(CASE WHEN status = 'SENT' THEN 1 ELSE 0 END) AS sent,
                  SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed
           FROM messages WHERE campaign_id = ?""",
        (campaign_id,),
    ).fetchone()
    conn.execute(
        "UPDATE campaigns SET total_count = ?, sent_count = ?, failed_count = ?, updated_at = ? WHERE id = ?",
        (row["total"] or 0, row["sent"] or 0, row["failed"] or 0, now_iso(), campaign_id),
    )
    conn.commit()


def set_rate_limit(campaign_id: str, rate_limit_ms: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE campaigns SET rate_limit_ms = ?, updated_at = ? WHERE id = ?",
        (rate_limit_ms, now_iso(), campaign_id),
    )
    conn.commit()


def delete(campaign_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
    conn.commit()
