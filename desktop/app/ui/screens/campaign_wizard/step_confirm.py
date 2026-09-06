import os
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import (
    ALLOWED_AUDIO_EXTENSIONS,
    DEFAULT_CALL_DAILY_LIMIT,
    DEFAULT_CALL_RATE_LIMIT_MS,
    DEFAULT_DAILY_LIMIT,
    DEFAULT_RATE_LIMIT_MS,
    DEFAULT_RING_DURATION_SEC,
    MAX_AUDIO_SIZE_MB,
)
from app.repositories import devices_repo
from app.services.message import sms_part_count


class StepConfirm(QWidget):
    """Final review before dispatch. The user must explicitly click START.

    Emits: start_sending(rate_limit_ms, daily_limit, campaign_type, ring_duration_sec, audio_path)
    """

    start_sending = Signal(int, int, str, int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._campaign_type = "SMS"
        self._audio_path: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Title
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Campaign Summary & Launch")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Review transmission parameters and launch the broadcast through your companion phone.")
        subtitle.setStyleSheet("font-size: 12px; color: #71717a;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # ── Campaign Type Selector Card ──────────────────────────────
        self.type_frame = QFrame()
        self.type_frame.setObjectName("TypeCard")
        self.type_frame.setStyleSheet(
            "#TypeCard {"
            "  background-color: #0c0c0e;"
            "  border: 1px solid #27272a;"
            "  border-radius: 8px;"
            "}"
            "#TypeCard QLabel { color: #a1a1aa; font-size: 11px; font-weight: 700; letter-spacing: 0.8px; }"
        )
        type_layout = QVBoxLayout(self.type_frame)
        type_layout.setContentsMargins(16, 12, 16, 12)
        type_layout.setSpacing(8)

        type_header = QLabel("CAMPAIGN DISPATCH MODE")
        type_layout.addWidget(type_header)

        radio_row = QHBoxLayout()
        radio_row.setSpacing(24)

        self.radio_sms = QRadioButton("📱  SMS Text Message")
        self.radio_sms.setStyleSheet(
            "QRadioButton {"
            "  color: #38bdf8;"
            "  font-size: 13.5px;"
            "  font-weight: 700;"
            "  spacing: 8px;"
            "  min-height: 26px;"
            "}"
            "QRadioButton::indicator { width: 16px; height: 16px; }"
        )

        self.radio_call = QRadioButton("📞  Voice Call Broadcast")
        self.radio_call.setStyleSheet(
            "QRadioButton {"
            "  color: #a78bfa;"
            "  font-size: 13.5px;"
            "  font-weight: 700;"
            "  spacing: 8px;"
            "  min-height: 26px;"
            "}"
            "QRadioButton::indicator { width: 16px; height: 16px; }"
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
        self.type_hint.setStyleSheet("color: #71717a; font-size: 12px; padding: 0px;")
        self.type_hint.setWordWrap(True)
        type_layout.addWidget(self.type_hint)

        layout.addWidget(self.type_frame)

        # ── Voice Audio Selection Card ───────────────────────────────
        self.audio_frame = QFrame()
        self.audio_frame.setObjectName("AudioCard")
        self.audio_frame.setStyleSheet(
            "#AudioCard {"
            "  background-color: #081320;"
            "  border: 1px solid #1e3a5f;"
            "  border-radius: 8px;"
            "}"
            "#AudioCard QLabel { color: #38bdf8; font-size: 11px; font-weight: 700; letter-spacing: 0.8px; }"
        )
        audio_layout = QVBoxLayout(self.audio_frame)
        audio_layout.setContentsMargins(16, 14, 16, 14)
        audio_layout.setSpacing(10)

        audio_hdr = QLabel("🎙️  VOICE AUDIO ANNOUNCEMENT (OPTIONAL MP3 / WAV)")
        audio_layout.addWidget(audio_hdr)

        audio_btn_row = QHBoxLayout()
        audio_btn_row.setSpacing(12)

        self.btn_select_audio = QPushButton("📁  Select MP3 / Audio File")
        self.btn_select_audio.setStyleSheet(
            "QPushButton {"
            "  background-color: #1d4ed8;"
            "  color: #ffffff;"
            "  font-weight: 700;"
            "  font-size: 12.5px;"
            "  border-radius: 5px;"
            "  padding: 8px 16px;"
            "}"
            "QPushButton:hover { background-color: #2563eb; }"
        )

        self.btn_clear_audio = QPushButton("✖ Remove")
        self.btn_clear_audio.setStyleSheet(
            "QPushButton {"
            "  background-color: #27272a;"
            "  color: #fca5a5;"
            "  font-weight: 600;"
            "  font-size: 12px;"
            "  border-radius: 5px;"
            "  padding: 8px 14px;"
            "}"
            "QPushButton:hover { background-color: #3f3f46; }"
        )
        self.btn_clear_audio.setVisible(False)

        self.audio_status_lbl = QLabel("No audio selected — Phone will place Awareness Missed Call (Rings and hangs up)")
        self.audio_status_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")

        audio_btn_row.addWidget(self.btn_select_audio)
        audio_btn_row.addWidget(self.btn_clear_audio)
        audio_btn_row.addWidget(self.audio_status_lbl, stretch=1)
        audio_layout.addLayout(audio_btn_row)

        self.btn_select_audio.clicked.connect(self._on_select_audio)
        self.btn_clear_audio.clicked.connect(self._on_clear_audio)

        layout.addWidget(self.audio_frame)

        # ── Summary Card ─────────────────────────────────────────────
        self.summary_card = QFrame()
        self.summary_card.setObjectName("SummaryCard")
        self.summary_card.setStyleSheet(
            "#SummaryCard {"
            "  background-color: #0c0c0c;"
            "  border: 1px solid #1f1f1f;"
            "  border-radius: 8px;"
            "}"
            "#SummaryCard QLabel { color: #f4f4f5; font-size: 13px; line-height: 1.6; }"
        )
        card_layout = QVBoxLayout(self.summary_card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(6)

        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("color: #f4f4f5; font-size: 13px;")
        card_layout.addWidget(self.summary_label)
        layout.addWidget(self.summary_card)

        # ── Settings Form ─────────────────────────────────────────────
        form_card = QFrame()
        form_card.setObjectName("FormCard")
        form_card.setStyleSheet(
            "#FormCard {"
            "  background-color: #09090b;"
            "  border: 1px solid #18181b;"
            "  border-radius: 8px;"
            "}"
            "#FormCard QLabel { color: #a1a1aa; font-size: 12.5px; font-weight: 600; }"
        )
        form_box_layout = QVBoxLayout(form_card)
        form_box_layout.setContentsMargins(16, 14, 16, 14)

        form = QFormLayout()
        form.setSpacing(12)

        # Rate interval
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(500, 60000)
        self.rate_spin.setSingleStep(500)
        self.rate_spin.setValue(DEFAULT_RATE_LIMIT_MS)
        self.rate_spin.setSuffix(" ms between messages")
        self.rate_label = QLabel("Interval Delay:")
        form.addRow(self.rate_label, self.rate_spin)

        # Daily limit
        self.daily_spin = QSpinBox()
        self.daily_spin.setRange(1, 2000)
        self.daily_spin.setValue(DEFAULT_DAILY_LIMIT)
        self.daily_spin.setSuffix(" SMS / day")
        self.daily_label = QLabel("Daily Limit:")
        form.addRow(self.daily_label, self.daily_spin)

        # Ring duration (calls only)
        self.ring_spin = QSpinBox()
        self.ring_spin.setRange(5, 60)
        self.ring_spin.setSingleStep(5)
        self.ring_spin.setValue(DEFAULT_RING_DURATION_SEC)
        self.ring_spin.setSuffix(" seconds ring time")
        self.ring_label = QLabel("Ring Duration (per call):")
        form.addRow(self.ring_label, self.ring_spin)

        form_box_layout.addLayout(form)
        layout.addWidget(form_card)

        self.limit_note = QLabel()
        self.limit_note.setStyleSheet("color: #71717a; font-size: 11.5px; padding: 2px 0;")
        self.limit_note.setWordWrap(True)
        layout.addWidget(self.limit_note)

        layout.addStretch()

        # Action Buttons
        row = QHBoxLayout()
        self.cancel_btn = QPushButton("[ Cancel ]")
        self.cancel_btn.setStyleSheet("padding: 10px 20px; font-weight: 600;")
        self.start_btn = QPushButton("🚀  START SENDING")
        self.start_btn.setStyleSheet(
            "background-color: #059669; color: white; font-weight: 800; font-size: 13.5px; padding: 12px 28px; border-radius: 6px;"
        )
        row.addWidget(self.cancel_btn)
        row.addStretch()
        row.addWidget(self.start_btn)
        layout.addLayout(row)

        self.start_btn.clicked.connect(self._emit_start)

        # Initial visibility
        self._apply_type_visibility()

    def _on_select_audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Call Announcement Audio",
            "",
            "Audio Files (*.mp3 *.wav);;All Files (*.*)",
        )
        if not path:
            return
        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb > MAX_AUDIO_SIZE_MB:
            QMessageBox.warning(
                self,
                "File Too Large",
                f"The selected audio file is {size_mb:.1f} MB. Maximum allowed is {MAX_AUDIO_SIZE_MB} MB.",
            )
            return
        self._audio_path = path
        filename = os.path.basename(path)
        self.audio_status_lbl.setText(f"✅ Loaded: {filename} ({size_mb:.2f} MB) — will play on speakerphone when answered")
        self.audio_status_lbl.setStyleSheet("color: #00e599; font-size: 12px; font-weight: 700;")
        self.btn_clear_audio.setVisible(True)
        self._refresh_summary()

    def _on_clear_audio(self) -> None:
        self._audio_path = None
        self.audio_status_lbl.setText("No audio selected — Phone will place Awareness Missed Call (Rings and hangs up)")
        self.audio_status_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        self.btn_clear_audio.setVisible(False)
        self._refresh_summary()

    def _emit_start(self) -> None:
        ctype = "CALL" if self.radio_call.isChecked() else "SMS"
        self.start_sending.emit(
            self.rate_spin.value(),
            self.daily_spin.value(),
            ctype,
            self.ring_spin.value(),
            self._audio_path or "",
        )

    def _on_type_changed(self, btn_id: int, checked: bool) -> None:
        if not checked:
            return
        self._campaign_type = "CALL" if btn_id == 1 else "SMS"
        self._apply_type_visibility()
        self._refresh_summary()

    def _apply_type_visibility(self) -> None:
        is_call = self._campaign_type == "CALL"

        self.ring_label.setVisible(is_call)
        self.ring_spin.setVisible(is_call)
        self.audio_frame.setVisible(is_call)

        if is_call:
            self.rate_spin.setValue(DEFAULT_CALL_RATE_LIMIT_MS)
            self.rate_spin.setSuffix(" ms gap")
            self.rate_label.setText("Gap Between Calls:")
            self.daily_spin.setValue(DEFAULT_CALL_DAILY_LIMIT)
            self.daily_spin.setSuffix(" calls / day")
            self.daily_label.setText("Daily Call Quota:")
            self.start_btn.setText("📞  START CALLING")
            self.start_btn.setStyleSheet(
                "background-color: #7c3aed; color: white; font-weight: 800; font-size: 13.5px; padding: 12px 28px; border-radius: 6px;"
            )
            self.type_hint.setText(
                "📞 Voice Call Mode: Your Android phone dials each contact sequentially. "
                "If an MP3 is chosen, speakerphone automatically broadcasts your audio into the mic upon answer."
            )
            self.limit_note.setText(
                "ℹ️ Calls are placed one by one using your phone's native dialer. "
                "If the recipient doesn't answer within the ring duration, it hangs up and continues."
            )
        else:
            self.rate_spin.setValue(DEFAULT_RATE_LIMIT_MS)
            self.rate_spin.setSuffix(" ms delay")
            self.rate_label.setText("Interval Delay:")
            self.daily_spin.setValue(DEFAULT_DAILY_LIMIT)
            self.daily_spin.setSuffix(" SMS / day")
            self.daily_label.setText("Daily SMS Quota:")
            self.start_btn.setText("🚀  START SENDING")
            self.start_btn.setStyleSheet(
                "background-color: #059669; color: white; font-weight: 800; font-size: 13.5px; padding: 12px 28px; border-radius: 6px;"
            )
            self.type_hint.setText(
                "📱 SMS Mode: Text messages are sent through your Android phone's SIM card."
            )
            self.limit_note.setText(
                "ℹ️ If your campaign exceeds the daily carrier limit, your phone automatically pauses and continues tomorrow."
            )

    def _refresh_summary(self) -> None:
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
        status = "<span style='color: #00e599;'>Connected 🟢</span>" if connected else "<span style='color: #ef4444;'>Disconnected 🔴</span>"
        status_text = "Ready to start broadcast." if connected else "Please connect your Android phone in the Devices tab before starting."

        if campaign_type == "CALL":
            ring_sec = self.ring_spin.value()
            est_time_sec = contact_count * (ring_sec + 3)
            est_min = est_time_sec // 60
            est_sec = est_time_sec % 60
            audio_info = f"<b>Audio Message:</b> <span style='color: #38bdf8;'>{os.path.basename(self._audio_path)}</span> (Plays on answer via Speakerphone)<br>" if self._audio_path else "<b>Audio Message:</b> <span style='color: #a1a1aa;'>None (Missed Call Awareness Ring)</span><br>"
            self.summary_label.setText(
                f"<b>Dispatch Type:</b> 📞 Voice Call Broadcast<br>"
                f"<b>Total Recipients:</b> {contact_count} contact(s)<br>"
                f"<b>Max Ring Duration:</b> {ring_sec} seconds<br>"
                f"{audio_info}"
                f"<b>Estimated Duration:</b> ~{est_min}m {est_sec}s for all calls<br>"
                f"<b>Companion Phone:</b> {device_name} ({status})<br><br>"
                f"<b>Status:</b> {status_text}"
            )
        else:
            _, parts = sms_part_count(message_body)
            self.summary_label.setText(
                f"<b>Dispatch Type:</b> 📱 SMS Text Campaign<br>"
                f"<b>Total Recipients:</b> {contact_count} contact(s)<br>"
                f"<b>Message Length:</b> {len(message_body)} characters ({parts} SMS part{'s' if parts != 1 else ''})<br>"
                f"<b>Total SMS to Send:</b> {contact_count * parts} SMS parts<br>"
                f"<b>Companion Phone:</b> {device_name} ({status})<br><br>"
                f"<b>Status:</b> {status_text}"
            )
        self.start_btn.setEnabled(connected)
