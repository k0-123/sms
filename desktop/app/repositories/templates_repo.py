"""CRUD for message templates."""
import sqlite3
from typing import Optional

from app.db.connection import get_connection
from app.repositories._util import new_id, now_iso


def create(name: str, body: str) -> str:
    conn = get_connection()
    template_id = new_id()
    ts = now_iso()
    conn.execute(
        "INSERT INTO templates (id, name, body, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (template_id, name, body, ts, ts),
    )
    conn.commit()
    return template_id


def get(template_id: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    return conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()


def list_all() -> list[sqlite3.Row]:
    conn = get_connection()
    return conn.execute("SELECT * FROM templates ORDER BY name ASC").fetchall()


def update(template_id: str, name: Optional[str] = None, body: Optional[str] = None) -> None:
    conn = get_connection()
    fields = {}
    if name is not None:
        fields["name"] = name
    if body is not None:
        fields["body"] = body
    if not fields:
        return
    fields["updated_at"] = now_iso()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE templates SET {set_clause} WHERE id = ?", (*fields.values(), template_id))
    conn.commit()


def delete(template_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))
    conn.commit()
