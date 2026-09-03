"""Drives a campaign's send queue.

Design note on daily pacing: the Android companion app owns the actual SMS
send rate and the phone's daily quota (it has the persistent, always-on
foreground service; the desktop app does not need to stay open for sending
to continue day over day). The desktop engine's job is to hand the full
batch of PENDING/RETRY messages to the phone's local queue once, then listen
for `sms_status` push updates to keep the local DB and UI in sync - it never
independently reschedules or paces dispatch to the phone.

State machine (per message): PENDING -> SENDING (accepted into the phone's
queue) -> SENT | FAILED. FAILED -> RETRY -> SENDING -> ... Retry never
touches a SENT row (enforced in messages_repo.mark_retry).
"""
from PySide6.QtCore import QObject, Signal

from app.network.client import NetworkClient
from app.repositories import campaigns_repo, messages_repo


class CampaignEngine(QObject):
    progress_updated = Signal(str, int, int, int)  # campaign_id, sent, failed, total
    message_status_changed = Signal(str, str)  # message_id, status
    campaign_paused = Signal(str, str)  # campaign_id, reason
    campaign_resumed = Signal(str)  # campaign_id
    campaign_completed = Signal(str)  # campaign_id

    def __init__(self, network_client: NetworkClient, parent=None):
        super().__init__(parent)
        self.client = network_client
        self._active_campaign_id: str | None = None

        self.client.sms_job_ack.connect(self._on_job_ack)
        self.client.sms_status.connect(self._on_sms_status)
        self.client.disconnected.connect(self._on_disconnected)
        self.client.connected.connect(self._on_reconnected)

    # -- campaign lifecycle ------------------------------------------------
    def start_campaign(self, campaign_id: str) -> None:
        self._active_campaign_id = campaign_id
        campaigns_repo.update_status(campaign_id, "SENDING")
        self._dispatch_all_pending(campaign_id)

    def pause(self, campaign_id: str) -> None:
        campaigns_repo.update_status(campaign_id, "PAUSED", pause_reason="USER")
        self.client.send_pause()
        self.campaign_paused.emit(campaign_id, "Paused by user.")

    def resume(self, campaign_id: str) -> None:
        campaigns_repo.update_status(campaign_id, "SENDING")
        self.client.send_resume()
        # Anything genuinely never sent to the phone yet still needs dispatching
        # (e.g. resuming after an app restart, before the phone had a chance to ack it).
        self._dispatch_all_pending(campaign_id)
        self.campaign_resumed.emit(campaign_id)

    def retry_failed(self, campaign_id: str) -> int:
        count = messages_repo.retry_all_failed(campaign_id)
        if count:
            self._dispatch_all_pending(campaign_id)
        return count

    def cancel(self, campaign_id: str) -> None:
        self.client.send_cancel_campaign(campaign_id)
        campaigns_repo.update_status(campaign_id, "CANCELLED")

    # -- dispatch ------------------------------------------------------------
    def _dispatch_all_pending(self, campaign_id: str) -> None:
        campaign = campaigns_repo.get(campaign_id)
        if campaign is None:
            return
        while True:
            message = messages_repo.next_dispatchable(campaign_id)
            if message is None:
                break
            self.client.send_sms_job(
                message_id=message["id"],
                campaign_id=campaign_id,
                phone_number=message["phone_e164"],
                text=message["rendered_text"],
                rate_limit_ms=campaign["rate_limit_ms"],
                daily_limit=campaign["daily_limit"],
            )
            messages_repo.mark_sending(message["id"])
            self.message_status_changed.emit(message["id"], "SENDING")
        self._refresh_and_check_completion(campaign_id)

    # -- incoming events from the phone --------------------------------------
    def _on_job_ack(self, message_id: str) -> None:
        # Already marked SENDING at dispatch time; ack just confirms durability.
        pass

    def _on_sms_status(self, message_id: str, status: str, error, sent_at) -> None:
        message = messages_repo.get(message_id)
        if message is None:
            return
        if status in ("SENT", "DELIVERED"):
            messages_repo.mark_sent(message_id)
        elif status == "FAILED":
            messages_repo.mark_failed(message_id, error or "The phone reported this message failed to send.")
        elif status == "SENDING":
            pass  # already SENDING locally
        self.message_status_changed.emit(message_id, status)
        self._refresh_and_check_completion(message["campaign_id"])

    def _on_disconnected(self, reason: str) -> None:
        if self._active_campaign_id is None:
            return
        campaign = campaigns_repo.get(self._active_campaign_id)
        if campaign is not None and campaign["status"] == "SENDING":
            campaigns_repo.update_status(self._active_campaign_id, "PAUSED", auto_paused=True, pause_reason="DISCONNECTED")
            self.campaign_paused.emit(self._active_campaign_id, reason)

    def _on_reconnected(self) -> None:
        if self._active_campaign_id is None:
            return
        campaign = campaigns_repo.get(self._active_campaign_id)
        if campaign is not None and campaign["auto_paused"] and campaign["pause_reason"] == "DISCONNECTED":
            campaigns_repo.update_status(self._active_campaign_id, "SENDING")
            self.campaign_resumed.emit(self._active_campaign_id)

    # -- bookkeeping -----------------------------------------------------
    def _refresh_and_check_completion(self, campaign_id: str) -> None:
        campaigns_repo.refresh_counts(campaign_id)
        campaign = campaigns_repo.get(campaign_id)
        if campaign is None:
            return
        self.progress_updated.emit(campaign_id, campaign["sent_count"], campaign["failed_count"], campaign["total_count"])
        pending_or_retry = messages_repo.next_dispatchable(campaign_id)
        still_sending = any(
            m["status"] == "SENDING" for m in messages_repo.list_for_campaign(campaign_id)
        )
        if pending_or_retry is None and not still_sending and campaign["status"] not in ("COMPLETED", "CANCELLED"):
            campaigns_repo.update_status(campaign_id, "COMPLETED")
            self.campaign_completed.emit(campaign_id)
