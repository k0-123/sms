from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import DEFAULT_DAILY_LIMIT, DEFAULT_RATE_LIMIT_MS
from app.repositories import devices_repo
from app.services.message import sms_part_count


class StepConfirm(QWidget):
    """Final review before dispatch. The user must explicitly click START SENDING."""

    start_sending = Signal(int, int)  # rate_limit_ms, daily_limit

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Title
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Step 6: Campaign Summary & Confirmation")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Review transmission parameters and launch the broadcast through your companion phone.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Summary Card
        self.summary_card = QFrame()
        self.summary_card.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px;")
        card_layout = QVBoxLayout(self.summary_card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(8)

        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-size: 13px; line-height: 1.5; color: #f8fafc;")
        card_layout.addWidget(self.summary_label)
        layout.addWidget(self.summary_card)

        # Settings Form
        form = QFormLayout()
        form.setSpacing(10)
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(500, 60000)
        self.rate_spin.setSingleStep(500)
        self.rate_spin.setValue(DEFAULT_RATE_LIMIT_MS)
        self.rate_spin.setSuffix(" ms between messages")
        form.addRow("Sending Interval (Delay):", self.rate_spin)

        self.daily_spin = QSpinBox()
        self.daily_spin.setRange(1, 2000)
        self.daily_spin.setValue(DEFAULT_DAILY_LIMIT)
        self.daily_spin.setSuffix(" SMS / day")
        form.addRow("Daily SMS Limit (Carrier Safe):", self.daily_spin)
        layout.addLayout(form)

        self.limit_note = QLabel(
            "ℹ️ Actual SMS sending limits are controlled by your carrier and phone. "
            "If your campaign exceeds the daily quota, your phone will automatically pause and continue sending tomorrow."
        )
        self.limit_note.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.limit_note.setWordWrap(True)
        layout.addWidget(self.limit_note)

        layout.addStretch()

        row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.start_btn = QPushButton("🚀  START SENDING")
        self.start_btn.setStyleSheet("background-color: #059669; color: white; font-weight: 800; font-size: 14px; padding: 12px 28px;")
        row.addWidget(self.cancel_btn)
        row.addStretch()
        row.addWidget(self.start_btn)
        layout.addLayout(row)

        self.start_btn.clicked.connect(
            lambda: self.start_sending.emit(self.rate_spin.value(), self.daily_spin.value())
        )

    def load(self, contact_count: int, message_body: str, device_id: str | None, connected: bool) -> None:
        _, parts = sms_part_count(message_body)
        device = devices_repo.get(device_id) if device_id else None
        device_name = device["device_name"] if device else "No phone paired"
        status = "🟢 Connected" if connected else "🔴 Disconnected"
        
        status_text = "✅ Ready to start transmission." if connected else "⚠️ Please connect your Android phone in Devices tab before starting."
        self.summary_label.setText(
            f"<b>Recipients:</b>  {contact_count} contact(s)<br>"
            f"<b>Message Length:</b>  {len(message_body)} characters ({parts} SMS part{'s' if parts != 1 else ''} per recipient)<br>"
            f"<b>Total SMS to Send:</b>  {contact_count * parts} SMS parts<br>"
            f"<b>Gateway Phone:</b>  {device_name} ({status})<br><br>"
            f"<b>Status:</b> {status_text}"
        )
        self.start_btn.setEnabled(connected)
