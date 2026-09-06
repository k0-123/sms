"""Asyncio WebSocket client to the Android companion app, running its own
event loop on a dedicated QThread. All results reach the GUI thread only via
Qt signals (thread-safe) - never touch widgets from this thread.

Transport is plain ws:// on the local Wi-Fi network (not wss://): generating
a trustworthy self-signed certificate purely on-device, on both ends, adds
real complexity for limited benefit on a single trusted home/office LAN.
Security instead comes from the pairing flow itself - a one-time code plus
an explicit Allow/Deny confirmation on the phone - and a long-lived pairing
token that every reconnect must present (see credential_store.py).
"""
import asyncio
import threading
from typing import Optional

import websockets
from PySide6.QtCore import QObject, QThread, Signal

from app import config
from app.network import protocol


class _EventLoopThread(QThread):
    """Runs a plain asyncio loop for its entire lifetime instead of a Qt
    event loop. Overriding run() (rather than connecting to `started`) means
    the thread returns and terminates as soon as the asyncio loop stops -
    it never falls through to QThread's default exec() call, which would
    otherwise start a second, un-quittable Qt loop on the same thread."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._ready = threading.Event()

    def run(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._ready.set()
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()

    def wait_until_ready(self, timeout: float = 5.0) -> None:
        self._ready.wait(timeout=timeout)

    def stop(self) -> None:
        if self.loop is not None and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.wait(2000)


class NetworkClient(QObject):
    connected = Signal()
    disconnected = Signal(str)  # human-readable reason
    pair_response = Signal(bool, str, str)  # accepted, pairing_token, reason
    auth_ack = Signal(bool, str, str, str)  # accepted, session_token, phone_number, reason
    heartbeat_ack = Signal(object, int)  # battery_pct (float|None), queue_depth
    sms_job_ack = Signal(str)  # message_id
    sms_status = Signal(str, str, object, object)  # message_id, status, error, sent_at
    call_job_ack = Signal(str)  # message_id
    call_status = Signal(str, str, object, object)  # message_id, status, error, ended_at
    call_audio_uploaded = Signal(str, bool, str)  # campaign_id, success, error
    protocol_error = Signal(str, str)  # code, message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = _EventLoopThread()
        self._thread.start()
        self._thread.wait_until_ready()
        self._loop = self._thread.loop
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._missed_heartbeats = 0

    # -- lifecycle -----------------------------------------------------
    def shutdown(self) -> None:
        if self._loop is None:
            return
        fut = asyncio.run_coroutine_threadsafe(self._disconnect(), self._loop)
        try:
            fut.result(timeout=2)
        except Exception:
            pass
        self._thread.stop()

    # -- public API (thread-safe, callable from GUI thread) ------------
    def connect_to(self, host: str, port: int = config.WS_PORT) -> None:
        asyncio.run_coroutine_threadsafe(self._connect(host, port), self._loop)

    def send_pair_request(self, device_id: str, device_name: str, pairing_code: str) -> None:
        self._send(protocol.pair_request(device_id, device_name, pairing_code))

    def send_auth(self, device_id: str, pairing_token: str) -> None:
        self._send(protocol.auth(device_id, pairing_token))

    def send_sms_job(
        self,
        message_id: str,
        campaign_id: str,
        phone_number: str,
        text: str,
        sim_slot: int = 0,
        rate_limit_ms: int = 2000,
        daily_limit: int = 100,
    ) -> None:
        self._send(protocol.sms_job(message_id, campaign_id, phone_number, text, sim_slot, rate_limit_ms, daily_limit))

    def send_call_job(
        self,
        message_id: str,
        campaign_id: str,
        phone_number: str,
        ring_duration_sec: int = 15,
        sim_slot: int = 0,
        rate_limit_ms: int = 3000,
        daily_limit: int = 200,
        has_audio: bool = False,
    ) -> None:
        self._send(protocol.call_job(message_id, campaign_id, phone_number, ring_duration_sec, sim_slot, rate_limit_ms, daily_limit, has_audio))

    def send_upload_call_audio(self, campaign_id: str, filename: str, audio_base64: str) -> None:
        self._send(protocol.upload_call_audio(campaign_id, filename, audio_base64))

    def send_pause(self) -> None:
        self._send(protocol.pause())

    def send_resume(self) -> None:
        self._send(protocol.resume())

    def send_cancel_campaign(self, campaign_id: str) -> None:
        self._send(protocol.cancel_campaign(campaign_id))

    def send_unpair(self, device_id: str) -> None:
        self._send(protocol.unpair(device_id))

    def disconnect_now(self) -> None:
        asyncio.run_coroutine_threadsafe(self._disconnect(), self._loop)

    # -- internals -------------------------------------------------------
    def _send(self, envelope: protocol.Envelope) -> None:
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._send_async(envelope), self._loop)

    async def _send_async(self, envelope: protocol.Envelope) -> None:
        if self._ws is None:
            return
        try:
            await self._ws.send(envelope.to_json())
        except Exception:
            pass  # surfaced via the recv loop's disconnect handling

    async def _connect(self, host: str, port: int) -> None:
        await self._disconnect()
        try:
            uri = f"ws://{host}:{port}"
            self._ws = await websockets.connect(uri)
        except Exception as exc:
            self.disconnected.emit(f"Could not connect to phone: {exc}")
            return

        self.connected.emit()
        self._missed_heartbeats = 0
        self._heartbeat_task = asyncio.ensure_future(self._heartbeat_loop())
        asyncio.ensure_future(self._recv_loop())

    async def _disconnect(self) -> None:
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    async def _heartbeat_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(config.HEARTBEAT_INTERVAL_SECONDS)
                if self._ws is None:
                    return
                self._missed_heartbeats += 1
                if self._missed_heartbeats > config.HEARTBEAT_MISSED_LIMIT:
                    self.disconnected.emit(
                        "Phone connection was lost.\n\n"
                        "Please reconnect your Android phone and try again."
                    )
                    await self._disconnect()
                    return
                await self._send_async(protocol.heartbeat())
        except asyncio.CancelledError:
            pass

    async def _recv_loop(self) -> None:
        assert self._ws is not None
        try:
            async for raw in self._ws:
                self._handle_message(raw)
        except Exception:
            pass
        finally:
            was_connected = self._ws is not None
            self._ws = None
            if was_connected:
                self.disconnected.emit(
                    "Phone connection was lost.\n\nPlease reconnect your Android phone and try again."
                )

    def _handle_message(self, raw: str) -> None:
        try:
            env = protocol.Envelope.from_json(raw)
        except Exception:
            return
        p = env.payload
        if env.type == protocol.PAIR_RESPONSE:
            self.pair_response.emit(p.get("accepted", False), p.get("pairing_token", ""), p.get("reason", ""))
        elif env.type == protocol.AUTH_ACK:
            self.auth_ack.emit(
                p.get("accepted", False), p.get("session_token", ""), p.get("phone_number", ""), p.get("reason", "")
            )
        elif env.type == protocol.HEARTBEAT_ACK:
            self._missed_heartbeats = 0
            self.heartbeat_ack.emit(p.get("battery_pct"), p.get("queue_depth", 0))
        elif env.type == protocol.SMS_JOB_ACK:
            self.sms_job_ack.emit(p.get("message_id", ""))
        elif env.type == protocol.SMS_STATUS:
            self.sms_status.emit(p.get("message_id", ""), p.get("status", ""), p.get("error"), p.get("sent_at"))
        elif env.type == protocol.CALL_JOB_ACK:
            self.call_job_ack.emit(p.get("message_id", ""))
        elif env.type == protocol.CALL_STATUS:
            self.call_status.emit(p.get("message_id", ""), p.get("status", ""), p.get("error"), p.get("ended_at"))
        elif env.type == protocol.UPLOAD_CALL_AUDIO_ACK:
            self.call_audio_uploaded.emit(
                p.get("campaign_id", ""),
                p.get("success", False),
                p.get("error", ""),
            )
        elif env.type == protocol.ERROR:
            self.protocol_error.emit(p.get("code", ""), p.get("message", ""))
