"""Applies schema.sql to the DB on launch. Idempotent (CREATE TABLE IF NOT EXISTS)."""
import os

from app.db.connection import get_connection

_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def run_migrations() -> None:
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn = get_connection()
    conn.executescript(schema_sql)
    conn.commit()
