from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.repositories import campaigns_repo, contacts_repo, devices_repo


def make_card(title: str) -> tuple[QFrame, QLabel, QLabel]:
    card = QFrame()
    card.setStyleSheet(
        "QFrame {"
        "  background-color: #0c0c0c;"
        "  border: 1px solid #1f1f1f;"
        "  border-radius: 8px;"
        "  padding: 14px;"
        "}"
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(6)

    title_label = QLabel(title.upper())
    title_label.setStyleSheet("font-size: 10px; font-weight: 700; color: #71717a; letter-spacing: 1px;")
    layout.addWidget(title_label)

    value_label = QLabel("--")
    value_label.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
    layout.addWidget(value_label)

    sub_label = QLabel("")
    sub_label.setStyleSheet("font-size: 11px; color: #52525b;")
    layout.addWidget(sub_label)

    layout.addStretch()
    return card, value_label, sub_label


class DashboardScreen(QWidget):
    request_navigation = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(18)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        title = QLabel("Telemetry Console")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;")
        subtitle = QLabel("SMS GATEWAY CORE • LOCAL NETWORK STATUS")
        subtitle.setStyleSheet("font-size: 10px; color: #71717a; font-weight: 700; letter-spacing: 1px;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # 4 Metric Cards Grid
        grid = QGridLayout()
        grid.setSpacing(14)

        card1, self.phone_status_val, self.phone_status_sub = make_card("[ LINK_GATEWAY ]")
        card2, self.contacts_val, self.contacts_sub = make_card("[ CONTACTS_DB ]")
        card3, self.campaigns_val, self.campaigns_sub = make_card("[ ACTIVE_DISPATCH ]")
        card4, self.quick_action_val, self.quick_action_sub = make_card("[ SYSTEM_HEALTH ]")

        grid.addWidget(card1, 0, 0)
        grid.addWidget(card2, 0, 1)
        grid.addWidget(card3, 1, 0)
        grid.addWidget(card4, 1, 1)
        layout.addLayout(grid)

        # Action Panel
        action_card = QFrame()
        action_card.setStyleSheet(
            "QFrame {"
            "  background-color: #0c0c0c;"
            "  border: 1px solid #1f1f1f;"
            "  border-radius: 8px;"
            "  padding: 16px;"
            "}"
        )
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(16, 14, 16, 14)
        action_layout.setSpacing(12)

        sec_title = QLabel("OPERATIONAL SHORTCUTS")
        sec_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #71717a; letter-spacing: 1px;")
        action_layout.addWidget(sec_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_new_campaign = QPushButton("⚡  [ LAUNCH_NEW_CAMPAIGN ]")
        self.btn_new_campaign.setStyleSheet("background-color: #18181b; border: 1px solid #00e599; color: #00e599; font-weight: 700;")

        self.btn_voice_call = QPushButton("📞  [ START_VOICE_CALL ]")
        self.btn_voice_call.setStyleSheet("background-color: #18181b; border: 1px solid #38bdf8; color: #38bdf8; font-weight: 700;")
        
        self.btn_import_contacts = QPushButton("[ 👥 MANAGE_CONTACTS ]")
        self.btn_pair_device = QPushButton("[ 📱 LINK_PHONE ]")

        btn_row.addWidget(self.btn_new_campaign)
        btn_row.addWidget(self.btn_voice_call)
        btn_row.addWidget(self.btn_import_contacts)
        btn_row.addWidget(self.btn_pair_device)
        btn_row.addStretch()
        action_layout.addLayout(btn_row)

        layout.addWidget(action_card)
        layout.addStretch()

        self.btn_new_campaign.clicked.connect(lambda: self.request_navigation.emit("New Campaign"))
        self.btn_voice_call.clicked.connect(lambda: self.request_navigation.emit("Voice Call"))
        self.btn_import_contacts.clicked.connect(lambda: self.request_navigation.emit("Contacts"))
        self.btn_pair_device.clicked.connect(lambda: self.request_navigation.emit("Devices"))

        self.refresh()

    def refresh(self) -> None:
        paired = devices_repo.list_all(paired_only=True)
        if paired:
            dev = paired[0]
            self.phone_status_val.setText("LINK.OK 🟢")
            self.phone_status_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #00e599;")
            self.phone_status_sub.setText(f"{dev['device_name']} ({dev['ip_address']})")
        else:
            self.phone_status_val.setText("STANDBY ⚪")
            self.phone_status_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #71717a;")
            self.phone_status_sub.setText("No mobile device linked")

        counts = contacts_repo.counts()
        self.contacts_val.setText(f"{counts['valid']}")
        self.contacts_val.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        self.contacts_sub.setText(f"Total: {counts['total']} | Invalid: {counts['invalid']}")

        all_campaigns = campaigns_repo.list_all()
        active = [c for c in all_campaigns if c["status"] in ("SENDING", "PAUSED", "QUEUED")]
        completed = [c for c in all_campaigns if c["status"] == "COMPLETED"]
        if active:
            c = active[0]
            self.campaigns_val.setText(f"{c['status']}")
            self.campaigns_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #38bdf8;")
            self.campaigns_sub.setText(f"Job ID: {c['id'][:8]}...")
        else:
            self.campaigns_val.setText("IDLE")
            self.campaigns_val.setStyleSheet("font-size: 22px; font-weight: 800; color: #71717a;")
            self.campaigns_sub.setText(f"{len(completed)} total campaigns logged")

        self.quick_action_val.setText("NORMAL 🟢")
        self.quick_action_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #00e599;")
        self.quick_action_sub.setText("Local database synced & ready")
