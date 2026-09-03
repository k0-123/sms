"""Exports a campaign's message results to an Excel file."""
import pandas as pd

from app.repositories import contacts_repo, messages_repo


def export_campaign_results(campaign_id: str, out_path: str) -> None:
    rows = []
    for m in messages_repo.list_for_campaign(campaign_id):
        contact = contacts_repo.get(m["contact_id"])
        rows.append(
            {
                "Name": contact["name"] if contact else "",
                "Phone": m["phone_e164"],
                "Message": m["rendered_text"],
                "Status": m["status"],
                "Error": m["error"] or "",
                "Date/Time": m["sent_at"] or m["dispatched_at"] or "",
            }
        )
    df = pd.DataFrame(rows, columns=["Name", "Phone", "Message", "Status", "Error", "Date/Time"])
    df.to_excel(out_path, index=False, engine="openpyxl")
