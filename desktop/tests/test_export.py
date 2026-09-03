import pandas as pd

from app.db.migrations import run_migrations
from app.repositories import campaigns_repo, contacts_repo, messages_repo
from app.services.export import export_campaign_results


def test_export_campaign_results_writes_expected_columns(tmp_path):
    run_migrations()
    campaign_id = campaigns_repo.create("Test", "Hello {name}")
    contact_id = contacts_repo.create("Rahul Sharma", "9876543210", "+919876543210")
    message_id = messages_repo.create(campaign_id, contact_id, "+919876543210", "Hello Rahul Sharma")
    messages_repo.mark_sending(message_id)
    messages_repo.mark_sent(message_id)

    out_path = str(tmp_path / "results.xlsx")
    export_campaign_results(campaign_id, out_path)

    df = pd.read_excel(out_path, engine="openpyxl")
    assert list(df.columns) == ["Name", "Phone", "Message", "Status", "Error", "Date/Time"]
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "Rahul Sharma"
    assert df.iloc[0]["Status"] == "SENT"
