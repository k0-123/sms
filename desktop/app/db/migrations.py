"""Applies schema.sql to the DB on launch. Idempotent (CREATE TABLE IF NOT EXISTS).

After the initial schema, incremental ALTERs add columns introduced in later
versions.  SQLite lacks ``ALTER TABLE ... IF NOT EXISTS``, so we wrap each
statement in a try/except and silently ignore the "duplicate column" error.
"""
import os
import sqlite3

from app.db.connection import get_connection

_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

# Each entry: (ALTER SQL, human description for logging).
_COLUMN_MIGRATIONS: list[tuple[str, str]] = [
    (
        "ALTER TABLE campaigns ADD COLUMN campaign_type TEXT NOT NULL DEFAULT 'SMS'",
        "campaigns.campaign_type",
    ),
    (
        "ALTER TABLE campaigns ADD COLUMN ring_duration_sec INTEGER NOT NULL DEFAULT 15",
        "campaigns.ring_duration_sec",
    ),
    (
        "ALTER TABLE campaigns ADD COLUMN audio_path TEXT",
        "campaigns.audio_path",
    ),
]


def run_migrations() -> None:
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn = get_connection()
    conn.executescript(schema_sql)
    conn.commit()

    # Incremental column additions for pre-existing databases.
    for sql, _desc in _COLUMN_MIGRATIONS:
        try:
            conn.execute(sql)
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists — safe to ignore

