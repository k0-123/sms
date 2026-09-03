"""Local storage of pairing tokens, DPAPI-protected on Windows.

File layout at CREDENTIALS_PATH: {"<device_id>": {"token_b64": "<dpapi-blob-b64>"}}.
Falls back to plaintext storage on non-Windows platforms where DPAPI isn't
available - acceptable for local dev/testing off-target, never for a real
deployment.
"""
import base64
import json
import os
from typing import Optional

from app.config import CREDENTIALS_PATH, ensure_app_dirs

try:
    import win32crypt  # type: ignore

    _HAS_DPAPI = True
except ImportError:  # pragma: no cover - only exercised off-Windows
    _HAS_DPAPI = False


def _protect(plaintext: bytes) -> bytes:
    if _HAS_DPAPI:
        return win32crypt.CryptProtectData(plaintext, None, None, None, None, 0)
    return plaintext


def _unprotect(blob: bytes) -> bytes:
    if _HAS_DPAPI:
        return win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1]
    return blob


def _load_all() -> dict:
    if not os.path.exists(CREDENTIALS_PATH):
        return {}
    with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_all(data: dict) -> None:
    ensure_app_dirs()
    with open(CREDENTIALS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)


def store_token(device_id: str, pairing_token: str) -> None:
    data = _load_all()
    blob = _protect(pairing_token.encode("utf-8"))
    data[device_id] = {"token_b64": base64.b64encode(blob).decode("ascii")}
    _save_all(data)


def get_token(device_id: str) -> Optional[str]:
    data = _load_all()
    entry = data.get(device_id)
    if entry is None:
        return None
    blob = base64.b64decode(entry["token_b64"])
    return _unprotect(blob).decode("utf-8")


def delete_token(device_id: str) -> None:
    data = _load_all()
    if device_id in data:
        del data[device_id]
        _save_all(data)
