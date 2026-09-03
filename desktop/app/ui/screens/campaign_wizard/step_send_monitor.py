from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.engine.campaign_engine import CampaignEngine
from app.repositories import contacts_repo, messages_repo

_STATUS_ICON = {"PENDING": "⏳", "SENDING": "⏳", "SENT": "✓", "FAILED": "✕", "RETRY": "⏳"}


class StepSendMonitor(QWidget):
    """Live campaign progress with pause/resume/retry controls."""

    def __init__(self, engine: CampaignEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.campaign_id: str | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("SENDING MESSAGES"))

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.counts_label = QLabel()
        layout.addWidget(self.counts_label)

        self.banner_label = QLabel()
        self.banner_label.setWordWrap(True)
        layout.addWidget(self.banner_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Phone", "Status"])
        layout.addWidget(self.table)

        row = QHBoxLayout()
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.retry_btn = QPushButton("Retry Failed Messages")
        row.addWidget(self.pause_btn)
        row.addWidget(self.resume_btn)
        row.addWidget(self.retry_btn)
        layout.addLayout(row)

        self.pause_btn.clicked.connect(self._pause)
        self.resume_btn.clicked.connect(self._resume)
        self.retry_btn.clicked.connect(self._retry)

        self.engine.progress_updated.connect(self._on_progress)
        self.engine.campaign_paused.connect(self._on_paused)
        self.engine.campaign_resumed.connect(self._on_resumed)
        self.engine.campaign_completed.connect(self._on_completed)
        self.engine.message_status_changed.connect(self._on_message_status)

    def start(self, campaign_id: str) -> None:
        self.campaign_id = campaign_id
        self._reload_table()
        self.banner_label.setText("")
        self.engine.start_campaign(campaign_id)

    def _reload_table(self) -> None:
        if not self.campaign_id:
            return
        rows = messages_repo.list_for_campaign(self.campaign_id)
        self.table.setRowCount(len(rows))
        self._row_by_message_id = {}
        for r, m in enumerate(rows):
            contact = contacts_repo.get(m["contact_id"])
            self.table.setItem(r, 0, QTableWidgetItem(contact["name"] if contact else ""))
            self.table.setItem(r, 1, QTableWidgetItem(m["phone_e164"]))
            self.table.setItem(r, 2, QTableWidgetItem(f"{_STATUS_ICON.get(m['status'], '')} {m['status']}"))
            self._row_by_message_id[m["id"]] = r

    def _on_message_status(self, message_id: str, status: str) -> None:
        row = getattr(self, "_row_by_message_id", {}).get(message_id)
        if row is not None:
            self.table.setItem(row, 2, QTableWidgetItem(f"{_STATUS_ICON.get(status, '')} {status}"))

    def _on_progress(self, campaign_id: str, sent: int, failed: int, total: int) -> None:
        if campaign_id != self.campaign_id:
            return
        done = sent + failed
        self.progress_bar.setMaximum(max(total, 1))
        self.progress_bar.setValue(done)
        pending = total - done
        self.counts_label.setText(f"{done} / {total}\n✓ Sent: {sent}    ✕ Failed: {failed}    ⏳ Pending: {pending}")

    def _on_paused(self, campaign_id: str, reason: str) -> None:
        if campaign_id != self.campaign_id:
            return
        if "disconnect" in reason.lower() or "lost" in reason.lower():
            self.banner_label.setText(f"⚠ PHONE DISCONNECTED\n\nSending has been automatically paused.\n{reason}")
        else:
            self.banner_label.setText("CAMPAIGN PAUSED")

    def _on_resumed(self, campaign_id: str) -> None:
        if campaign_id == self.campaign_id:
            self.banner_label.setText("")

    def _on_completed(self, campaign_id: str) -> None:
        if campaign_id == self.campaign_id:
            self.banner_label.setText("Campaign completed.")

    def _pause(self) -> None:
        if self.campaign_id:
            self.engine.pause(self.campaign_id)

    def _resume(self) -> None:
        if self.campaign_id:
            self.engine.resume(self.campaign_id)

    def _retry(self) -> None:
        if self.campaign_id:
            self.engine.retry_failed(self.campaign_id)
            self._reload_table()
