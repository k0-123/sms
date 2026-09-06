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

from app.engine.call_engine import CallEngine
from app.engine.campaign_engine import CampaignEngine
from app.repositories import contacts_repo, messages_repo

_SMS_STATUS_ICON = {
    "PENDING": "⏳ Pending",
    "SENDING": "📤 Sending...",
    "SENT": "✅ Delivered",
    "FAILED": "❌ Failed",
    "RETRY": "🔄 Retrying",
}

_CALL_STATUS_ICON = {
    "PENDING": "⏳ Queued",
    "SENDING": "📞 Calling...",
    "SENT": "✅ Call Completed",
    "ANSWERED": "✅ Answered",
    "NO_ANSWER": "✅ Rang (No Answer)",
    "FAILED": "❌ Call Failed",
    "RETRY": "🔄 Retrying",
}


class StepSendMonitor(QWidget):
    """Live campaign progress with pause/resume/retry controls.

    Supports both CampaignEngine (SMS) and CallEngine (voice calls).
    """

    def __init__(self, sms_engine: CampaignEngine, call_engine: CallEngine | None = None, parent=None):
        super().__init__(parent)
        self.sms_engine = sms_engine
        self.call_engine = call_engine
        self._active_engine: CampaignEngine | CallEngine | None = None
        self._is_call: bool = False
        self.campaign_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Title
        header = QVBoxLayout()
        header.setSpacing(4)
        self.title_label = QLabel("Campaign Dispatch Monitor")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        self.subtitle_label = QLabel("Live transmission progress.")
        self.subtitle_label.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(self.title_label)
        header.addWidget(self.subtitle_label)
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
        self.retry_btn = QPushButton("🔄  Retry Failed")
        self.retry_btn.setStyleSheet("background-color: #6366f1; color: white; font-weight: 700;")
        
        row.addWidget(self.pause_btn)
        row.addWidget(self.resume_btn)
        row.addStretch()
        row.addWidget(self.retry_btn)
        layout.addLayout(row)

        self.pause_btn.clicked.connect(self._pause)
        self.resume_btn.clicked.connect(self._resume)
        self.retry_btn.clicked.connect(self._retry)

        # Connect SMS engine signals
        self.sms_engine.progress_updated.connect(self._on_progress)
        self.sms_engine.campaign_paused.connect(self._on_paused)
        self.sms_engine.campaign_resumed.connect(self._on_resumed)
        self.sms_engine.campaign_completed.connect(self._on_completed)

        # Connect Call engine signals
        if self.call_engine:
            self.call_engine.progress_updated.connect(self._on_progress)
            self.call_engine.campaign_paused.connect(self._on_paused)
            self.call_engine.campaign_resumed.connect(self._on_resumed)
            self.call_engine.campaign_completed.connect(self._on_completed)

    def load(self, campaign_id: str, is_call: bool = False) -> None:
        self.campaign_id = campaign_id
        self._is_call = is_call
        self.banner_label.clear()
        self.banner_label.setStyleSheet("")

        if is_call:
            self.title_label.setText("📞 Call Campaign Monitor")
            self.subtitle_label.setText("Live progress as voice calls are placed through your phone.")
            self.table.setHorizontalHeaderLabels(["Recipient Name", "Phone Number", "Call Status"])
        else:
            self.title_label.setText("Campaign Dispatch Monitor")
            self.subtitle_label.setText("Live transmission progress as SMS messages are dispatched through your phone.")
            self.table.setHorizontalHeaderLabels(["Recipient Name", "Phone Number", "Delivery Status"])

        self._refresh_table()

    def start(self, campaign_id: str, is_call: bool = False) -> None:
        """Called by the wizard to load the monitor AND kick off the engine."""
        self._is_call = is_call
        self.load(campaign_id, is_call)
        if is_call and self.call_engine:
            self._active_engine = self.call_engine
            self.call_engine.start_campaign(campaign_id)
        else:
            self._active_engine = self.sms_engine
            self.sms_engine.start_campaign(campaign_id)

    def _on_progress(self, campaign_id: str, sent: int, failed: int, total: int) -> None:
        if campaign_id != self.campaign_id:
            return
        pending = max(0, total - sent - failed)
        pct = int(sent / total * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)

        if self._is_call:
            self.counts_label.setText(
                f"📊 Progress: {sent}/{total} ({pct}%)    |    ✅ Called: {sent}    ❌ Failed: {failed}    ⏳ Queued: {pending}"
            )
        else:
            self.counts_label.setText(
                f"📊 Progress: {sent}/{total} ({pct}%)    |    ✅ Sent: {sent}    ❌ Failed: {failed}    ⏳ Pending: {pending}"
            )
        self._refresh_table()

    def _on_paused(self, _campaign_id: str, reason: str) -> None:
        self.banner_label.setText(f"⏸️ Campaign Paused: {reason}")
        self.banner_label.setStyleSheet(
            "background-color: #451a03; color: #fde68a; border: 1px solid #b45309; "
            "border-radius: 8px; padding: 10px 14px; font-weight: 600;"
        )

    def _on_resumed(self, _campaign_id: str) -> None:
        self.banner_label.clear()
        self.banner_label.setStyleSheet("")

    def _on_completed(self, _campaign_id: str) -> None:
        if self._is_call:
            self.banner_label.setText("🎉 All calls in this campaign have been completed!")
        else:
            self.banner_label.setText("🎉 All messages in this campaign have been processed!")
        self.banner_label.setStyleSheet(
            "background-color: #064e3b; color: #6ee7b7; border: 1px solid #059669; "
            "border-radius: 8px; padding: 10px 14px; font-weight: 700;"
        )
        self._refresh_table()

    def _refresh_table(self) -> None:
        if not self.campaign_id:
            return
        status_map = _CALL_STATUS_ICON if self._is_call else _SMS_STATUS_ICON
        messages = messages_repo.list_for_campaign(self.campaign_id)
        self.table.setRowCount(len(messages))
        for r, m in enumerate(messages):
            contact = contacts_repo.get(m["contact_id"]) if m["contact_id"] else None
            name = contact["name"] if contact else "--"
            status_text = status_map.get(m["status"], m["status"])
            self.table.setItem(r, 0, QTableWidgetItem(name))
            self.table.setItem(r, 1, QTableWidgetItem(m["phone_e164"]))
            self.table.setItem(r, 2, QTableWidgetItem(status_text))

    def _pause(self) -> None:
        if self.campaign_id and self._active_engine:
            self._active_engine.pause(self.campaign_id)

    def _resume(self) -> None:
        if self.campaign_id and self._active_engine:
            self._active_engine.resume(self.campaign_id)

    def _retry(self) -> None:
        if self.campaign_id and self._active_engine:
            self._active_engine.retry_failed(self.campaign_id)
