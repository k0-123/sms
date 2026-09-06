from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import (
    DEFAULT_CALL_DAILY_LIMIT,
    DEFAULT_CALL_RATE_LIMIT_MS,
    DEFAULT_DAILY_LIMIT,
    DEFAULT_RATE_LIMIT_MS,
    DEFAULT_RING_DURATION_SEC,
)
from app.repositories import devices_repo
from app.services.message import sms_part_count


class StepConfirm(QWidget):
    """Final review before dispatch. The user must explicitly click START.

    Emits: start_sending(rate_limit_ms, daily_limit, campaign_type, ring_duration_sec)
    """

    start_sending = Signal(int, int, str, int)  # rate_limit_ms, daily_limit, campaign_type, ring_duration_sec

    def __init__(self, parent=None):
        super().__init__(parent)
        self._campaign_type = "SMS"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Title
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Campaign Summary & Confirmation")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Review transmission parameters and launch the broadcast through your companion phone.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # ── Campaign Type Toggle ──────────────────────────────────────
        type_frame = QFrame()
        type_frame.setStyleSheet(
            "QFrame { background-color: #1a1a2e; border: 1px solid #2d2d44; border-radius: 10px; padding: 12px; }"
        )
        type_layout = QVBoxLayout(type_frame)
        type_layout.setSpacing(8)

        type_header = QLabel("CAMPAIGN TYPE")
        type_header.setStyleSheet("font-size: 11px; font-weight: 700; color: #a1a1aa; letter-spacing: 1px;")
        type_layout.addWidget(type_header)

        radio_row = QHBoxLayout()
        self.radio_sms = QRadioButton("📱  SMS Campaign")
        self.radio_sms.setStyleSheet(
            "QRadioButton { font-size: 14px; font-weight: 700; color: #38bdf8; padding: 8px 16px; }"
            "QRadioButton::indicator { width: 18px; height: 18px; }"
        )
        self.radio_call = QRadioButton("📞  Voice Call Campaign")
        self.radio_call.setStyleSheet(
            "QRadioButton { font-size: 14px; font-weight: 700; color: #a78bfa; padding: 8px 16px; }"
            "QRadioButton::indicator { width: 18px; height: 18px; }"
        )
        self.radio_sms.setChecked(True)

        self.type_group = QButtonGroup(self)
        self.type_group.addButton(self.radio_sms, 0)
        self.type_group.addButton(self.radio_call, 1)
        self.type_group.idToggled.connect(self._on_type_changed)

        radio_row.addWidget(self.radio_sms)
        radio_row.addWidget(self.radio_call)
        radio_row.addStretch()
        type_layout.addLayout(radio_row)

        self.type_hint = QLabel()
        self.type_hint.setStyleSheet("font-size: 12px; color: #71717a;")
        self.type_hint.setWordWrap(True)
        type_layout.addWidget(self.type_hint)
        layout.addWidget(type_frame)

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

        # ── Settings Form ─────────────────────────────────────────────
        form = QFormLayout()
        form.setSpacing(10)

        # SMS settings
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(500, 60000)
        self.rate_spin.setSingleStep(500)
        self.rate_spin.setValue(DEFAULT_RATE_LIMIT_MS)
        self.rate_spin.setSuffix(" ms between messages")
        self.rate_label = QLabel("Sending Interval (Delay):")
        form.addRow(self.rate_label, self.rate_spin)

        self.daily_spin = QSpinBox()
        self.daily_spin.setRange(1, 2000)
        self.daily_spin.setValue(DEFAULT_DAILY_LIMIT)
        self.daily_spin.setSuffix(" SMS / day")
        self.daily_label = QLabel("Daily SMS Limit (Carrier Safe):")
        form.addRow(self.daily_label, self.daily_spin)

        # Call settings
        self.ring_spin = QSpinBox()
        self.ring_spin.setRange(5, 60)
        self.ring_spin.setSingleStep(5)
        self.ring_spin.setValue(DEFAULT_RING_DURATION_SEC)
        self.ring_spin.setSuffix(" seconds ring time")
        self.ring_label = QLabel("Ring Duration (per call):")
        form.addRow(self.ring_label, self.ring_spin)

        layout.addLayout(form)

        self.limit_note = QLabel()
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

        self.start_btn.clicked.connect(self._emit_start)

        # Initial visibility
        self._apply_type_visibility()

    def _emit_start(self) -> None:
        ctype = "CALL" if self.radio_call.isChecked() else "SMS"
        self.start_sending.emit(
            self.rate_spin.value(),
            self.daily_spin.value(),
            ctype,
            self.ring_spin.value(),
        )

    def _on_type_changed(self, btn_id: int, checked: bool) -> None:
        if not checked:
            return
        self._campaign_type = "CALL" if btn_id == 1 else "SMS"
        self._apply_type_visibility()
        self._refresh_summary()

    def _apply_type_visibility(self) -> None:
        is_call = self._campaign_type == "CALL"

        # Show/hide call-specific vs SMS-specific controls
        self.ring_label.setVisible(is_call)
        self.ring_spin.setVisible(is_call)

        if is_call:
            self.rate_spin.setValue(DEFAULT_CALL_RATE_LIMIT_MS)
            self.rate_spin.setSuffix(" ms between calls")
            self.rate_label.setText("Gap Between Calls:")
            self.daily_spin.setValue(DEFAULT_CALL_DAILY_LIMIT)
            self.daily_spin.setSuffix(" calls / day")
            self.daily_label.setText("Daily Call Limit:")
            self.start_btn.setText("📞  START CALLING")
            self.start_btn.setStyleSheet(
                "background-color: #7c3aed; color: white; font-weight: 800; font-size: 14px; padding: 12px 28px;"
            )
            self.type_hint.setText(
                "📞 Voice Call Campaign — Your Android phone will dial each contact sequentially. "
                "Calls ring for the configured duration then auto-hangup (missed call awareness). "
                "Only one call runs at a time."
            )
            self.limit_note.setText(
                "ℹ️ Calls are placed one at a time using your phone's native dialer. "
                "Each call will ring for the configured duration before auto-hangup. "
                "If the daily limit is reached, the phone pauses and continues tomorrow."
            )
        else:
            self.rate_spin.setValue(DEFAULT_RATE_LIMIT_MS)
            self.rate_spin.setSuffix(" ms between messages")
            self.rate_label.setText("Sending Interval (Delay):")
            self.daily_spin.setValue(DEFAULT_DAILY_LIMIT)
            self.daily_spin.setSuffix(" SMS / day")
            self.daily_label.setText("Daily SMS Limit (Carrier Safe):")
            self.start_btn.setText("🚀  START SENDING")
            self.start_btn.setStyleSheet(
                "background-color: #059669; color: white; font-weight: 800; font-size: 14px; padding: 12px 28px;"
            )
            self.type_hint.setText(
                "📱 SMS Campaign — Text messages are sent through your Android phone's SIM card. "
                "Standard carrier charges may apply."
            )
            self.limit_note.setText(
                "ℹ️ Actual SMS sending limits are controlled by your carrier and phone. "
                "If your campaign exceeds the daily quota, your phone will automatically pause and continue sending tomorrow."
            )

    def _refresh_summary(self) -> None:
        # Re-generate summary text with stored values
        if hasattr(self, "_last_load_args"):
            self.load(**self._last_load_args)

    def load(self, contact_count: int, message_body: str, device_id: str | None, connected: bool, campaign_type: str = "SMS") -> None:
        self._last_load_args = {
            "contact_count": contact_count,
            "message_body": message_body,
            "device_id": device_id,
            "connected": connected,
            "campaign_type": campaign_type,
        }
        self._campaign_type = campaign_type
        if campaign_type == "CALL":
            self.radio_call.setChecked(True)
        else:
            self.radio_sms.setChecked(True)
        self._apply_type_visibility()

        device = devices_repo.get(device_id) if device_id else None
        device_name = device["device_name"] if device else "No phone paired"
        status = "🟢 Connected" if connected else "🔴 Disconnected"
        status_text = "✅ Ready to start." if connected else "⚠️ Please connect your Android phone in Devices tab before starting."

        if campaign_type == "CALL":
            ring_sec = self.ring_spin.value()
            est_time_sec = contact_count * (ring_sec + 3)
            est_min = est_time_sec // 60
            est_sec = est_time_sec % 60
            self.summary_label.setText(
                f"<b>Campaign Type:</b>  📞 Voice Call (Missed Call Awareness)<br>"
                f"<b>Recipients:</b>  {contact_count} contact(s)<br>"
                f"<b>Ring Duration:</b>  {ring_sec} seconds per call<br>"
                f"<b>Estimated Time:</b>  ~{est_min}m {est_sec}s for all {contact_count} calls<br>"
                f"<b>Gateway Phone:</b>  {device_name} ({status})<br><br>"
                f"<b>Status:</b> {status_text}"
            )
        else:
            _, parts = sms_part_count(message_body)
            self.summary_label.setText(
                f"<b>Campaign Type:</b>  📱 SMS Text Message<br>"
                f"<b>Recipients:</b>  {contact_count} contact(s)<br>"
                f"<b>Message Length:</b>  {len(message_body)} characters ({parts} SMS part{'s' if parts != 1 else ''} per recipient)<br>"
                f"<b>Total SMS to Send:</b>  {contact_count * parts} SMS parts<br>"
                f"<b>Gateway Phone:</b>  {device_name} ({status})<br><br>"
                f"<b>Status:</b> {status_text}"
            )
        self.start_btn.setEnabled(connected)
