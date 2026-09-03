"""CRUD for paired devices."""
import sqlite3
from typing import Optional

from app.db.connection import get_connection
from app.repositories._util import now_iso


def create(
    device_id: str,
    device_name: str,
    pairing_token_ref: str,
    last_ip: Optional[str] = None,
    cert_fingerprint: Optional[str] = None,
    phone_number: Optional[str] = None,
) -> None:
    conn = get_connection()
    ts = now_iso()
    conn.execute(
        """INSERT INTO devices
           (id, device_name, last_ip, pairing_token_ref, cert_fingerprint,
            phone_number, is_paired, last_connected_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)""",
        (device_id, device_name, last_ip, pairing_token_ref, cert_fingerprint, phone_number, ts, ts),
    )
    conn.commit()


def get(device_id: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    return conn.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()


def list_all(paired_only: bool = False) -> list[sqlite3.Row]:
    conn = get_connection()
    query = "SELECT * FROM devices"
    if paired_only:
        query += " WHERE is_paired = 1"
    query += " ORDER BY last_connected_at DESC"
    return conn.execute(query).fetchall()


def mark_connected(device_id: str, last_ip: Optional[str] = None) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE devices SET last_connected_at = ?, last_ip = COALESCE(?, last_ip) WHERE id = ?",
        (now_iso(), last_ip, device_id),
    )
    conn.commit()


def unpair(device_id: str) -> None:
    conn = get_connection()
    conn.execute("UPDATE devices SET is_paired = 0 WHERE id = ?", (device_id,))
    conn.commit()


def delete(device_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    conn.commit()
