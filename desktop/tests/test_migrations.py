from app.db.connection import get_connection
from app.db.migrations import run_migrations
from app.repositories import campaigns_repo, contacts_repo, messages_repo


def test_run_migrations_creates_all_tables():
    run_migrations()
    conn = get_connection()
    tables = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert {"contacts", "templates", "devices", "campaigns", "messages"} <= tables


def test_contact_and_message_roundtrip():
    run_migrations()
    contact_id = contacts_repo.create("Rahul Sharma", "9876543210", "+919876543210")
    campaign_id = campaigns_repo.create("Test Campaign", "Hello {name}")
    message_id = messages_repo.create(campaign_id, contact_id, "+919876543210", "Hello Rahul Sharma")

    assert messages_repo.next_dispatchable(campaign_id)["id"] == message_id

    messages_repo.mark_sending(message_id)
    assert messages_repo.get(message_id)["status"] == "SENDING"

    messages_repo.mark_sent(message_id)
    assert messages_repo.get(message_id)["status"] == "SENT"

    # Retry must never touch a SENT message.
    assert messages_repo.mark_retry(message_id) is False
    assert messages_repo.get(message_id)["status"] == "SENT"

    campaigns_repo.refresh_counts(campaign_id)
    campaign = campaigns_repo.get(campaign_id)
    assert campaign["sent_count"] == 1
    assert campaign["total_count"] == 1
