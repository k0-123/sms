"""App-wide paths and constants."""
import os

APP_NAME = "SMSBridge"

APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
DB_PATH = os.path.join(APPDATA_DIR, "smsbridge.db")
CREDENTIALS_PATH = os.path.join(APPDATA_DIR, "device_credentials.json")

WS_PORT = 8765
HEARTBEAT_INTERVAL_SECONDS = 5
HEARTBEAT_MISSED_LIMIT = 3  # disconnected after this many missed heartbeats
DEFAULT_RATE_LIMIT_MS = 2000
DEFAULT_DAILY_LIMIT = 100  # phone-side daily SMS cap; remaining contacts auto-continue next day

# Voice-call campaign defaults
DEFAULT_RING_DURATION_SEC = 15      # how long each call rings before auto-hangup
DEFAULT_CALL_RATE_LIMIT_MS = 3000   # gap between consecutive calls
DEFAULT_CALL_DAILY_LIMIT = 200      # phone-side daily call cap

INDIAN_MOBILE_REGEX = r"^(?:\+91|91)?([6-9]\d{9})$"


def ensure_app_dirs() -> None:
    os.makedirs(APPDATA_DIR, exist_ok=True)
