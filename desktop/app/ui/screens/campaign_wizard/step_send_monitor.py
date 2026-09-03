from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
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

_STATUS_ICON = {"PENDING": "⏳ Pending", "SENDING": "📤 Sending...", "SENT": "✅ Delivered", "FAILED": "❌ Failed", "RETRY": "🔄 Retrying"}


class StepSendMonitor(QWidget):
    """Live campaign progress with pause/resume/retry controls."""

    def __init__(self, engine: CampaignEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.campaign_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Title
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Campaign Dispatch Monitor")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Live transmission progress as SMS messages are dispatched through your phone.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(22)
        layout.addWidget(self.progress_bar)

        # Stat pills row
        self.counts_label = QLabel("Initializing...")
        self.counts_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(self.counts_label)

        self.banner_label = QLabel()
        self.banner_label.setWordWrap(True)
        layout.addWidget(self.banner_label)

        # Live Messages Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Recipient Name", "Phone Number", "Delivery Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table, stretch=1)

        # Action Buttons
        row = QHBoxLayout()
        self.pause_btn = QPushButton("⏸️  Pause Campaign")
        self.resume_btn = QPushButton("▶️  Resume Campaign")
        self.resume_btn.setStyleSheet("background-color: #059669; color: white; font-weight: 700;")
        self.retry_btn = QPushButton("🔄  Retry Failed Messages")
        self.retry_btn.setStyleSheet("background-color: #6366f1; color: white; font-weight: 700;")
        
        row.addWidget(self.pause_btn)
        row.addWidget(self.resume_btn)
        row.addStretch()
        row.addWidget(self.retry_btn)
        layout.addLayout(row)

        self.pause_btn.clicked.connect(self._pause)
        self.resume_btn.clicked.connect(self._resume)
        self.retry_btn.clicked.connect(self._retry)

        self.engine.progress_updated.connect(self._on_progress)
        self.engine.campaign_paused.connect(self._on_paused)
        self.engine.campaign_resumed.connect(self._on_resumed)
        self.engine.campaign_completed.connect(self._on_completed)

    def load(self, campaign_id: str) -> None:
        self.campaign_id = campaign_id
        self.banner_label.clear()
        self.banner_label.setStyleSheet("")
        self._refresh_table()

    def _on_progress(self, sent: int, total: int, pending: int, failed: int) -> None:
        pct = int(sent / total * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.counts_label.setText(
            f"📊 Progress: {sent}/{total} ({pct}%)    |    ✅ Sent: {sent}    ❌ Failed: {failed}    ⏳ Pending: {pending}"
        )
        self._refresh_table()

    def _on_paused(self, reason: str) -> None:
        self.banner_label.setText(f"⏸️ Campaign Paused: {reason}")
        self.banner_label.setStyleSheet(
            "background-color: #451a03; color: #fde68a; border: 1px solid #b45309; "
            "border-radius: 8px; padding: 10px 14px; font-weight: 600;"
        )

    def _on_resumed(self) -> None:
        self.banner_label.clear()
        self.banner_label.setStyleSheet("")

    def _on_completed(self) -> None:
        self.banner_label.setText("🎉 All messages in this campaign have been processed!")
        self.banner_label.setStyleSheet(
            "background-color: #064e3b; color: #6ee7b7; border: 1px solid #059669; "
            "border-radius: 8px; padding: 10px 14px; font-weight: 700;"
        )
        self._refresh_table()

    def _refresh_table(self) -> None:
        if not self.campaign_id:
            return
        messages = messages_repo.list_for_campaign(self.campaign_id)
        self.table.setRowCount(len(messages))
        for r, m in enumerate(messages):
            contact = contacts_repo.get(m["contact_id"]) if m["contact_id"] else None
            name = contact["name"] if contact else "--"
            status_text = _STATUS_ICON.get(m["status"], m["status"])
            self.table.setItem(r, 0, QTableWidgetItem(name))
            self.table.setItem(r, 1, QTableWidgetItem(m["phone_e164"]))
            self.table.setItem(r, 2, QTableWidgetItem(status_text))

    def _pause(self) -> None:
        if self.campaign_id:
            self.engine.pause_campaign(self.campaign_id, "Paused by user.")

    def _resume(self) -> None:
        if self.campaign_id:
            self.engine.resume_campaign(self.campaign_id)

    def _retry(self) -> None:
        if self.campaign_id:
            self.engine.retry_failed(self.campaign_id)
