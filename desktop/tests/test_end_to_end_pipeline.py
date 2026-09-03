"""Exercises the full desktop-side pipeline without any real network/hardware:
Excel import -> validation -> contact selection -> message personalization ->
campaign creation -> dispatch to the (fake) phone -> phone-reported SENT status
-> campaign completion. This is what "import an Excel sheet, write one message,
click send" actually runs through end to end.
"""
import pandas as pd
from PySide6.QtCore import QObject, Signal

from app.db.migrations import run_migrations
from app.engine.campaign_engine import CampaignEngine
from app.repositories import campaigns_repo, contacts_repo, messages_repo
from app.services.excel_import import import_contacts, read_excel
from app.services.message import render


class FakeNetworkClient(QObject):
    connected = Signal()
    disconnected = Signal(str)
    sms_job_ack = Signal(str)
    sms_status = Signal(str, str, object, object)

    def __init__(self):
        super().__init__()
        self.sent_jobs = {}

    def send_sms_job(self, message_id, campaign_id, phone_number, text, sim_slot=0, rate_limit_ms=2000, daily_limit=100):
        self.sent_jobs[message_id] = (phone_number, text)

    def send_pause(self):
        pass

    def send_resume(self):
        pass

    def send_cancel_campaign(self, campaign_id):
        pass


def test_full_pipeline_excel_to_completed_campaign(tmp_path):
    run_migrations()

    # 1. Excel import with a realistic mixed-quality sheet.
    df = pd.DataFrame(
        {
            "Name": ["Rahul Sharma", "Amit Singh", "Priya Verma", "No Phone"],
            "Phone Number": ["9876543210", "+91 98765 43211", "12345", ""],
        }
    )
    path = tmp_path / "contacts.xlsx"
    df.to_excel(path, index=False, engine="openpyxl")
    loaded = read_excel(str(path))
    result = import_contacts(str(path), loaded, "Name", "Phone Number")

    assert result.valid == 2
    assert result.invalid == 2

    # 2. Select only the valid contacts (mirrors StepSelect's default behavior).
    valid_contacts = contacts_repo.list_all(valid_only=True)
    selected_ids = [c["id"] for c in valid_contacts]
    assert len(selected_ids) == 2

    # 3. Compose with personalization.
    message_body = "Namaste {name}, this is an important announcement."

    # 4. Build the campaign + per-contact rendered messages (mirrors wizard_screen._on_start_sending).
    campaign_id = campaigns_repo.create("Announcement", message_body, rate_limit_ms=2000, daily_limit=100)
    for contact_id in selected_ids:
        contact = contacts_repo.get(contact_id)
        rendered = render(message_body, contact["name"])
        messages_repo.create(campaign_id, contact_id, contact["phone_e164"], rendered)
    campaigns_repo.refresh_counts(campaign_id)
    assert campaigns_repo.get(campaign_id)["total_count"] == 2

    # 5. Dispatch via the engine to a fake phone.
    fake = FakeNetworkClient()
    engine = CampaignEngine(fake)
    engine.start_campaign(campaign_id)

    assert len(fake.sent_jobs) == 2
    for phone_number, text in fake.sent_jobs.values():
        assert "Namaste" in text
        assert "{name}" not in text  # personalization applied per-recipient

    # 6. Phone reports both as SENT.
    for message_id in list(fake.sent_jobs.keys()):
        fake.sms_status.emit(message_id, "SENT", None, "2026-09-03T10:00:00Z")

    campaign = campaigns_repo.get(campaign_id)
    assert campaign["status"] == "COMPLETED"
    assert campaign["sent_count"] == 2
    assert campaign["failed_count"] == 0
