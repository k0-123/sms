from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
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
        layout.addWidget(QLabel("CAMPAIGN SUMMARY"))

        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)

        form = QFormLayout()
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(500, 60000)
        self.rate_spin.setSingleStep(500)
        self.rate_spin.setValue(DEFAULT_RATE_LIMIT_MS)
        self.rate_spin.setSuffix(" ms between messages")
        form.addRow("Sending interval:", self.rate_spin)

        self.daily_spin = QSpinBox()
        self.daily_spin.setRange(1, 2000)
        self.daily_spin.setValue(DEFAULT_DAILY_LIMIT)
        form.addRow("Daily SMS limit (phone-enforced):", self.daily_spin)
        layout.addLayout(form)

        self.limit_note = QLabel(
            "Actual SMS sending limits are controlled by your carrier and phone. "
            "If your selection exceeds the daily limit, the phone will automatically "
            "continue sending the rest tomorrow."
        )
        self.limit_note.setWordWrap(True)
        layout.addWidget(self.limit_note)

        row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.start_btn = QPushButton("START SENDING")
        row.addWidget(self.cancel_btn)
        row.addWidget(self.start_btn)
        layout.addLayout(row)

        self.start_btn.clicked.connect(
            lambda: self.start_sending.emit(self.rate_spin.value(), self.daily_spin.value())
        )

    def load(self, contact_count: int, message_body: str, device_id: str | None, connected: bool) -> None:
        _, parts = sms_part_count(message_body)
        device = devices_repo.get(device_id) if device_id else None
        device_name = device["device_name"] if device else "No phone paired"
        status = "\U0001F7E2 Connected" if connected else "\U0001F534 Not connected"
        self.summary_label.setText(
            f"Contacts:       {contact_count}\n"
            f"Selected:       {contact_count}\n"
            f"Message Parts:  {parts}\n"
            f"Phone:          {device_name}\n"
            f"Connection:     {status}\n\n"
            f"Ready to send." if connected else
            f"Contacts:       {contact_count}\n"
            f"Selected:       {contact_count}\n"
            f"Message Parts:  {parts}\n"
            f"Phone:          {device_name}\n"
            f"Connection:     {status}\n\n"
            f"No phone connected.\n\nPlease connect your Android phone before starting the campaign."
        )
        self.start_btn.setEnabled(connected)
