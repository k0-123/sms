"""Simple local JSON-backed user preferences (Settings screen)."""
import json
import os

from app.config import APPDATA_DIR, DEFAULT_DAILY_LIMIT, DEFAULT_RATE_LIMIT_MS, ensure_app_dirs

_SETTINGS_PATH = os.path.join(APPDATA_DIR, "settings.json")

_DEFAULTS = {
    "default_rate_limit_ms": DEFAULT_RATE_LIMIT_MS,
    "default_daily_limit": DEFAULT_DAILY_LIMIT,
    "auto_pause_on_disconnect": True,
    "default_name_column": "",
    "default_phone_column": "",
    "duplicate_handling": "flag",  # "flag" | "skip"
}


def load() -> dict:
    if not os.path.exists(_SETTINGS_PATH):
        return dict(_DEFAULTS)
    with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    merged = dict(_DEFAULTS)
    merged.update(data)
    return merged


def save(settings: dict) -> None:
    ensure_app_dirs()
    with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
