from PySide6.QtCore import QObject, Signal

from app.db.migrations import run_migrations
from app.engine.campaign_engine import CampaignEngine
from app.repositories import campaigns_repo, contacts_repo, messages_repo


class FakeNetworkClient(QObject):
    """Mimics the parts of NetworkClient the engine depends on, without any real sockets."""

    connected = Signal()
    disconnected = Signal(str)
    sms_job_ack = Signal(str)
    sms_status = Signal(str, str, object, object)

    def __init__(self):
        super().__init__()
        self.sent_jobs = []
        self.paused = False
        self.resumed = False
        self.cancelled_campaigns = []

    def send_sms_job(self, message_id, campaign_id, phone_number, text, sim_slot=0, rate_limit_ms=2000, daily_limit=100):
        self.sent_jobs.append(message_id)

    def send_pause(self):
        self.paused = True

    def send_resume(self):
        self.resumed = True

    def send_cancel_campaign(self, campaign_id):
        self.cancelled_campaigns.append(campaign_id)


def _make_campaign_with_messages(n=3):
    run_migrations()
    campaign_id = campaigns_repo.create("Test", "Hello {name}")
    message_ids = []
    for i in range(n):
        contact_id = contacts_repo.create(f"Contact {i}", f"98765432{i}0", f"+19876543{i}0")
        message_ids.append(messages_repo.create(campaign_id, contact_id, f"+19876543{i}0", f"Hello Contact {i}"))
    return campaign_id, message_ids


def test_start_campaign_dispatches_all_pending():
    campaign_id, message_ids = _make_campaign_with_messages(3)
    fake = FakeNetworkClient()
    engine = CampaignEngine(fake)

    engine.start_campaign(campaign_id)

    assert sorted(fake.sent_jobs) == sorted(message_ids)
    for mid in message_ids:
        assert messages_repo.get(mid)["status"] == "SENDING"
    assert campaigns_repo.get(campaign_id)["status"] == "SENDING"


def test_sms_status_sent_updates_message_and_completes_campaign():
    campaign_id, message_ids = _make_campaign_with_messages(2)
    fake = FakeNetworkClient()
    engine = CampaignEngine(fake)
    engine.start_campaign(campaign_id)

    fake.sms_status.emit(message_ids[0], "SENT", None, "2026-01-01T00:00:00Z")
    fake.sms_status.emit(message_ids[1], "SENT", None, "2026-01-01T00:00:00Z")

    assert messages_repo.get(message_ids[0])["status"] == "SENT"
    campaign = campaigns_repo.get(campaign_id)
    assert campaign["sent_count"] == 2
    assert campaign["status"] == "COMPLETED"


def test_sms_status_failed_then_retry_never_touches_sent():
    campaign_id, message_ids = _make_campaign_with_messages(2)
    fake = FakeNetworkClient()
    engine = CampaignEngine(fake)
    engine.start_campaign(campaign_id)

    fake.sms_status.emit(message_ids[0], "SENT", None, "2026-01-01T00:00:00Z")
    fake.sms_status.emit(message_ids[1], "FAILED", "SIM not ready", None)

    assert messages_repo.get(message_ids[0])["status"] == "SENT"
    assert messages_repo.get(message_ids[1])["status"] == "FAILED"

    fake.sent_jobs.clear()
    retried = engine.retry_failed(campaign_id)

    assert retried == 1
    assert messages_repo.get(message_ids[0])["status"] == "SENT"  # untouched
    assert fake.sent_jobs == [message_ids[1]]  # only the failed one re-dispatched


def test_disconnect_auto_pauses_active_campaign():
    campaign_id, message_ids = _make_campaign_with_messages(1)
    fake = FakeNetworkClient()
    engine = CampaignEngine(fake)
    engine.start_campaign(campaign_id)

    fake.disconnected.emit("Phone connection was lost.")

    campaign = campaigns_repo.get(campaign_id)
    assert campaign["status"] == "PAUSED"
    assert campaign["auto_paused"] == 1
    assert campaign["pause_reason"] == "DISCONNECTED"


def test_reconnect_resumes_auto_paused_campaign():
    campaign_id, message_ids = _make_campaign_with_messages(1)
    fake = FakeNetworkClient()
    engine = CampaignEngine(fake)
    engine.start_campaign(campaign_id)
    fake.disconnected.emit("lost")
    assert campaigns_repo.get(campaign_id)["status"] == "PAUSED"

    fake.connected.emit()

    assert campaigns_repo.get(campaign_id)["status"] == "SENDING"
