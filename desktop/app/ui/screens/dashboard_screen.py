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
        "  background-color: #1e293b;"
        "  border: 1px solid #334155;"
        "  border-radius: 12px;"
        "  padding: 16px;"
        "}"
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(6)

    title_label = QLabel(title.upper())
    title_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.5px;")
    layout.addWidget(title_label)

    value_label = QLabel("--")
    value_label.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc;")
    layout.addWidget(value_label)

    sub_label = QLabel("")
    sub_label.setStyleSheet("font-size: 12px; color: #64748b;")
    layout.addWidget(sub_label)

    layout.addStretch()
    return card, value_label, sub_label


class DashboardScreen(QWidget):
    request_navigation = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title = QLabel("Dashboard Overview")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Monitor mobile phone connection status, contact database, and SMS campaigns.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # Grid of Cards
        grid = QGridLayout()
        grid.setSpacing(16)

        # Card 1: Phone
        self.phone_card, self.phone_val, self.phone_sub = make_card("📱 Companion Phone")
        grid.addWidget(self.phone_card, 0, 0)

        # Card 2: Contacts
        self.contacts_card, self.contacts_val, self.contacts_sub = make_card("👥 Total Contacts")
        grid.addWidget(self.contacts_card, 0, 1)

        # Card 3: Campaigns
        self.camp_card, self.camp_val, self.camp_sub = make_card("🚀 Active Campaign")
        grid.addWidget(self.camp_card, 1, 0)

        # Card 4: Quick Action
        action_card = QFrame()
        action_card.setStyleSheet(
            "QFrame {"
            "  background-color: #1e293b;"
            "  border: 1px solid #334155;"
            "  border-radius: 12px;"
            "  padding: 16px;"
            "}"
        )
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(16, 16, 16, 16)
        action_layout.setSpacing(10)

        act_title = QLabel("⚡ QUICK ACTIONS")
        act_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.5px;")
        action_layout.addWidget(act_title)

        self.new_campaign_btn = QPushButton("🚀  Launch New Campaign")
        self.new_campaign_btn.setStyleSheet(
            "background-color: #6366f1; color: white; font-weight: 700; font-size: 13px; "
            "padding: 10px 16px; border-radius: 8px; border: none;"
        )
        self.new_campaign_btn.setCursor(Qt.PointingHandCursor)
        action_layout.addWidget(self.new_campaign_btn)

        self.devices_btn = QPushButton("📱  Manage Devices")
        self.devices_btn.setStyleSheet(
            "background-color: #0f172a; color: #94a3b8; font-weight: 600; font-size: 12px; "
            "padding: 8px 16px; border-radius: 8px; border: 1px solid #334155;"
        )
        self.devices_btn.setCursor(Qt.PointingHandCursor)
        action_layout.addWidget(self.devices_btn)
        action_layout.addStretch()

        grid.addWidget(action_card, 1, 1)
        layout.addLayout(grid)

        layout.addStretch()

        self.new_campaign_btn.clicked.connect(lambda: self.request_navigation.emit("New Campaign"))
        self.devices_btn.clicked.connect(lambda: self.request_navigation.emit("Devices"))

        self.refresh()

    def refresh(self) -> None:
        paired = devices_repo.list_all(paired_only=True)
        if paired:
            device = paired[0]
            ip_str = f" • IP: {device['last_ip']}" if device['last_ip'] else ""
            self.phone_val.setText("🟢 Connected")
            self.phone_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #34d399;")
            self.phone_sub.setText(f"{device['device_name']}{ip_str}")
        else:
            self.phone_val.setText("🔴 Disconnected")
            self.phone_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #f87171;")
            self.phone_sub.setText("Open Devices tab to pair companion phone.")

        counts = contacts_repo.counts()
        valid = counts.get('valid', 0)
        total = counts.get('total', 0)
        self.contacts_val.setText(str(valid))
        self.contacts_sub.setText(f"{valid} valid phone numbers ({total} total in DB)")

        campaigns = campaigns_repo.list_all()
        active = next((c for c in campaigns if c["status"] in ("SENDING", "PAUSED")), None)
        if active:
            self.camp_val.setText(f"{active['sent_count']} / {active['total_count']}")
            self.camp_sub.setText(f"Status: {active['status']} • Campaign: {active['name']}")
        else:
            self.camp_val.setText("Idle")
            self.camp_sub.setText("No active broadcast in progress.")
