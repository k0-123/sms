import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

import app.config as config


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point the app at a throwaway SQLite DB for every test."""
    import app.db.connection as connection

    connection.close_connection()
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(config, "APPDATA_DIR", str(tmp_path))
    yield
    connection.close_connection()
