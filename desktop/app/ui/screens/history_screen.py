from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.repositories import campaigns_repo, contacts_repo, messages_repo
from app.services.export import export_campaign_results


class HistoryScreen(QWidget):
    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._selected_campaign_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Campaign History & Logs")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Review past dispatch runs, export delivery metrics, and retry failed transmissions.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Campaigns Table
        layout.addWidget(QLabel("All Campaigns:"))
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(5)
        self.campaigns_table.setHorizontalHeaderLabels(["Date", "Campaign Name", "Total Contacts", "Sent", "Failed"])
        self.campaigns_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.campaigns_table.itemSelectionChanged.connect(self._on_campaign_selected)
        layout.addWidget(self.campaigns_table, stretch=2)

        detail_row = QHBoxLayout()
        self.export_btn = QPushButton("📥  Export Results to Excel / CSV")
        self.retry_failed_btn = QPushButton("🔄  Retry Failed Messages")
        self.retry_failed_btn.setStyleSheet("background-color: #6366f1; color: white; font-weight: 700;")
        detail_row.addWidget(self.export_btn)
        detail_row.addWidget(self.retry_failed_btn)
        detail_row.addStretch()
        layout.addLayout(detail_row)

        self.export_btn.clicked.connect(self._export_selected)
        self.retry_failed_btn.clicked.connect(self._retry_selected)

        # Failed details table
        layout.addWidget(QLabel("Failed Messages in Selected Campaign:"))
        self.failed_table = QTableWidget()
        self.failed_table.setColumnCount(4)
        self.failed_table.setHorizontalHeaderLabels(["Recipient Name", "Phone Number", "Failure Reason", "Timestamp"])
        self.failed_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.failed_table, stretch=1)

        self.refresh()

    def refresh(self) -> None:
        campaigns = campaigns_repo.list_all()
        self.campaigns_table.setRowCount(len(campaigns))
        self._campaign_ids = []
        for r, c in enumerate(campaigns):
            self.campaigns_table.setItem(r, 0, QTableWidgetItem((c["created_at"] or "")[:19].replace("T", " ")))
            self.campaigns_table.setItem(r, 1, QTableWidgetItem(c["name"]))
            self.campaigns_table.setItem(r, 2, QTableWidgetItem(str(c["total_count"])))
            self.campaigns_table.setItem(r, 3, QTableWidgetItem(f"✅ {c['sent_count']}"))
            self.campaigns_table.setItem(r, 4, QTableWidgetItem(f"❌ {c['failed_count']}" if c['failed_count'] > 0 else "0"))
            self._campaign_ids.append(c["id"])

    def _on_campaign_selected(self) -> None:
        row = self.campaigns_table.currentRow()
        if row < 0 or row >= len(self._campaign_ids):
            self._selected_campaign_id = None
            self.failed_table.setRowCount(0)
            return
        campaign_id = self._campaign_ids[row]
        self._selected_campaign_id = campaign_id
        failed = messages_repo.list_failed(campaign_id)
        self.failed_table.setRowCount(len(failed))
        for r, m in enumerate(failed):
            contact = contacts_repo.get(m["contact_id"]) if m["contact_id"] else None
            self.failed_table.setItem(r, 0, QTableWidgetItem(contact["name"] if contact else ""))
            self.failed_table.setItem(r, 1, QTableWidgetItem(m["phone_e164"]))
            self.failed_table.setItem(r, 2, QTableWidgetItem(m["error_message"] or "Unknown error"))
            self.failed_table.setItem(r, 3, QTableWidgetItem((m["sent_at"] or m["created_at"] or "")[:19].replace("T", " ")))

    def _export_selected(self) -> None:
        if not self._selected_campaign_id:
            QMessageBox.information(self, "No campaign selected", "Select a campaign from the table first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not path:
            return
        export_campaign_results(self._selected_campaign_id, path)
        QMessageBox.information(self, "Exported", f"Results exported to:\n{path}")

    def _retry_selected(self) -> None:
        if not self._selected_campaign_id:
            QMessageBox.information(self, "No campaign selected", "Select a campaign from the table first.")
            return
        failed = messages_repo.list_failed(self._selected_campaign_id)
        if not failed:
            QMessageBox.information(self, "No failed messages", "This campaign has no failed messages to retry.")
            return
        if self.engine is None:
            QMessageBox.warning(self, "Engine unavailable", "Campaign engine is not ready.")
            return
        self.engine.start_campaign(self._selected_campaign_id, resume_only_failed=True)
        QMessageBox.information(self, "Retrying", f"Retrying {len(failed)} failed message(s).")
        self.refresh()
