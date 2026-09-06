"""Shared wire protocol between the desktop app (WebSocket client) and the
Android companion app (WebSocket server). This is the single source of truth
for message shapes - the Android app's ProtocolHandler.kt must match exactly.

Envelope: {"type": str, "id": str, "ts": ISO8601 str, "payload": dict}
"""
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

# Message types
PAIR_REQUEST = "pair_request"
PAIR_RESPONSE = "pair_response"
AUTH = "auth"
AUTH_ACK = "auth_ack"
HEARTBEAT = "heartbeat"
HEARTBEAT_ACK = "heartbeat_ack"
SMS_JOB = "sms_job"
SMS_JOB_ACK = "sms_job_ack"
SMS_STATUS = "sms_status"
CALL_JOB = "call_job"
CALL_JOB_ACK = "call_job_ack"
CALL_STATUS = "call_status"
UPLOAD_CALL_AUDIO = "upload_call_audio"
UPLOAD_CALL_AUDIO_ACK = "upload_call_audio_ack"
PAUSE = "pause"
RESUME = "resume"
CANCEL_CAMPAIGN = "cancel_campaign"
UNPAIR = "unpair"
ERROR = "error"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Envelope:
    type: str
    payload: dict
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ts: str = field(default_factory=_now_iso)

    def to_json(self) -> str:
        return json.dumps({"type": self.type, "id": self.id, "ts": self.ts, "payload": self.payload})

    @staticmethod
    def from_json(raw: str) -> "Envelope":
        data = json.loads(raw)
        return Envelope(type=data["type"], payload=data.get("payload", {}), id=data["id"], ts=data["ts"])


def build(msg_type: str, payload: Optional[dict] = None, msg_id: Optional[str] = None) -> Envelope:
    kwargs: dict[str, Any] = {"type": msg_type, "payload": payload or {}}
    if msg_id is not None:
        kwargs["id"] = msg_id
    return Envelope(**kwargs)


def pair_request(device_id: str, device_name: str, pairing_code: str) -> Envelope:
    return build(PAIR_REQUEST, {"device_id": device_id, "device_name": device_name, "pairing_code": pairing_code})


def auth(device_id: str, pairing_token: str) -> Envelope:
    return build(AUTH, {"device_id": device_id, "pairing_token": pairing_token})


def heartbeat() -> Envelope:
    return build(HEARTBEAT, {})


def sms_job(
    message_id: str,
    campaign_id: str,
    phone_number: str,
    text: str,
    sim_slot: int = 0,
    rate_limit_ms: int = 2000,
    daily_limit: int = 100,
) -> Envelope:
    return build(
        SMS_JOB,
        {
            "message_id": message_id,
            "campaign_id": campaign_id,
            "phone_number": phone_number,
            "text": text,
            "sim_slot": sim_slot,
            # Phone-side pacing config, carried on every job so the Android app
            # can enforce it without tracking separate per-campaign state.
            "rate_limit_ms": rate_limit_ms,
            "daily_limit": daily_limit,
        },
    )


def call_job(
    message_id: str,
    campaign_id: str,
    phone_number: str,
    ring_duration_sec: int = 15,
    sim_slot: int = 0,
    rate_limit_ms: int = 3000,
    daily_limit: int = 200,
    has_audio: bool = False,
) -> Envelope:
    return build(
        CALL_JOB,
        {
            "message_id": message_id,
            "campaign_id": campaign_id,
            "phone_number": phone_number,
            "ring_duration_sec": ring_duration_sec,
            "sim_slot": sim_slot,
            "rate_limit_ms": rate_limit_ms,
            "daily_limit": daily_limit,
            "has_audio": has_audio,
        },
    )


def upload_call_audio(campaign_id: str, filename: str, audio_base64: str) -> Envelope:
    return build(
        UPLOAD_CALL_AUDIO,
        {
            "campaign_id": campaign_id,
            "filename": filename,
            "audio_base64": audio_base64,
        },
    )


def pause() -> Envelope:
    return build(PAUSE, {})


def resume() -> Envelope:
    return build(RESUME, {})


def cancel_campaign(campaign_id: str) -> Envelope:
    return build(CANCEL_CAMPAIGN, {"campaign_id": campaign_id})


def unpair(device_id: str) -> Envelope:
    return build(UNPAIR, {"device_id": device_id})
