"""CRUD + queries for the contacts table."""
import sqlite3
from typing import Optional

from app.db.connection import get_connection
from app.repositories._util import new_id, now_iso


def create(
    name: str,
    phone_raw: str,
    phone_e164: str,
    email: Optional[str] = None,
    extra_json: Optional[str] = None,
    source_file: Optional[str] = None,
    is_valid: bool = True,
    validation_error: Optional[str] = None,
) -> str:
    conn = get_connection()
    contact_id = new_id()
    ts = now_iso()
    conn.execute(
        """INSERT INTO contacts
           (id, name, phone_raw, phone_e164, email, extra_json, source_file,
            is_valid, validation_error, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (contact_id, name, phone_raw, phone_e164, email, extra_json, source_file,
         1 if is_valid else 0, validation_error, ts, ts),
    )
    conn.commit()
    return contact_id


def get(contact_id: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    return conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()


def find_by_phone_e164(phone_e164: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM contacts WHERE phone_e164 = ? ORDER BY created_at ASC LIMIT 1",
        (phone_e164,),
    ).fetchone()


def list_all(valid_only: bool = False, search: Optional[str] = None) -> list[sqlite3.Row]:
    conn = get_connection()
    query = "SELECT * FROM contacts WHERE 1=1"
    params: list = []
    if valid_only:
        query += " AND is_valid = 1"
    if search:
        query += " AND (name LIKE ? OR phone_e164 LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    query += " ORDER BY name ASC"
    return conn.execute(query, params).fetchall()


def update(contact_id: str, **fields) -> None:
    if not fields:
        return
    conn = get_connection()
    fields["updated_at"] = now_iso()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(
        f"UPDATE contacts SET {set_clause} WHERE id = ?",
        (*fields.values(), contact_id),
    )
    conn.commit()


def delete(contact_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()


def delete_many(contact_ids: list[str]) -> None:
    if not contact_ids:
        return
    conn = get_connection()
    placeholders = ",".join("?" for _ in contact_ids)
    conn.execute(f"DELETE FROM contacts WHERE id IN ({placeholders})", contact_ids)
    conn.commit()


def counts() -> dict:
    conn = get_connection()
    row = conn.execute(
        """SELECT
             COUNT(*) AS total,
             SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) AS valid,
             SUM(CASE WHEN is_valid = 0 THEN 1 ELSE 0 END) AS invalid
           FROM contacts"""
    ).fetchone()
    return {"total": row["total"] or 0, "valid": row["valid"] or 0, "invalid": row["invalid"] or 0}
