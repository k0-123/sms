from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
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
        layout.addWidget(QLabel("HISTORY"))

        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(5)
        self.campaigns_table.setHorizontalHeaderLabels(["Date", "Campaign", "Contacts", "Sent", "Failed"])
        self.campaigns_table.itemSelectionChanged.connect(self._on_campaign_selected)
        layout.addWidget(self.campaigns_table)

        detail_row = QHBoxLayout()
        self.export_btn = QPushButton("Export Results")
        self.retry_failed_btn = QPushButton("Retry Failed Messages")
        detail_row.addWidget(self.export_btn)
        detail_row.addWidget(self.retry_failed_btn)
        layout.addLayout(detail_row)

        self.export_btn.clicked.connect(self._export_selected)
        self.retry_failed_btn.clicked.connect(self._retry_selected)

        layout.addWidget(QLabel("Failed messages:"))
        self.failed_table = QTableWidget()
        self.failed_table.setColumnCount(4)
        self.failed_table.setHorizontalHeaderLabels(["Name", "Phone", "Error", "Time"])
        layout.addWidget(self.failed_table)

        self.refresh()

    def refresh(self) -> None:
        campaigns = campaigns_repo.list_all()
        self.campaigns_table.setRowCount(len(campaigns))
        self._campaign_ids = []
        for r, c in enumerate(campaigns):
            self.campaigns_table.setItem(r, 0, QTableWidgetItem((c["created_at"] or "")[:10]))
            self.campaigns_table.setItem(r, 1, QTableWidgetItem(c["name"]))
            self.campaigns_table.setItem(r, 2, QTableWidgetItem(str(c["total_count"])))
            self.campaigns_table.setItem(r, 3, QTableWidgetItem(str(c["sent_count"])))
            self.campaigns_table.setItem(r, 4, QTableWidgetItem(str(c["failed_count"])))
            self._campaign_ids.append(c["id"])

    def _on_campaign_selected(self) -> None:
        rows = self.campaigns_table.selectionModel().selectedRows()
        if not rows:
            return
        self._selected_campaign_id = self._campaign_ids[rows[0].row()]
        failed = messages_repo.list_for_campaign(self._selected_campaign_id, status="FAILED")
        self.failed_table.setRowCount(len(failed))
        for r, m in enumerate(failed):
            contact = contacts_repo.get(m["contact_id"])
            self.failed_table.setItem(r, 0, QTableWidgetItem(contact["name"] if contact else ""))
            self.failed_table.setItem(r, 1, QTableWidgetItem(m["phone_e164"]))
            self.failed_table.setItem(r, 2, QTableWidgetItem(m["error"] or ""))
            self.failed_table.setItem(r, 3, QTableWidgetItem(m["updated_at"] or ""))

    def _export_selected(self) -> None:
        if not self._selected_campaign_id:
            QMessageBox.information(self, "No campaign selected", "Select a campaign first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Results", "campaign_results.xlsx", "Excel Files (*.xlsx)")
        if not path:
            return
        export_campaign_results(self._selected_campaign_id, path)
        QMessageBox.information(self, "Exported", f"Results exported to {path}")

    def _retry_selected(self) -> None:
        if not self._selected_campaign_id or not self.engine:
            return
        count = self.engine.retry_failed(self._selected_campaign_id)
        QMessageBox.information(self, "Retry queued", f"Re-queued {count} failed message(s).")
        self.refresh()
        self._on_campaign_selected()
