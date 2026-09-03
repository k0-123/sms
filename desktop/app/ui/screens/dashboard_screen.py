from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.repositories import campaigns_repo, contacts_repo, devices_repo


class DashboardScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.title = QLabel("LOCAL SMS SENDER")
        self.title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self.title)

        self.phone_status_label = QLabel()
        layout.addWidget(self.phone_status_label)

        self.contacts_label = QLabel()
        layout.addWidget(self.contacts_label)

        self.campaign_label = QLabel()
        layout.addWidget(self.campaign_label)

        self.new_campaign_btn = QPushButton("+ New Campaign")
        layout.addWidget(self.new_campaign_btn)

        layout.addStretch()
        self.refresh()

    def refresh(self) -> None:
        paired = devices_repo.list_all(paired_only=True)
        if paired:
            device = paired[0]
            self.phone_status_label.setText(f"Phone\n\U0001F7E2 Connected\n{device['device_name']}")
        else:
            self.phone_status_label.setText(
                "Phone\n\U0001F534 Phone Disconnected\n\n"
                "Please connect your Android phone using the SMS Bridge companion app."
            )

        counts = contacts_repo.counts()
        self.contacts_label.setText(f"Contacts\n{counts['valid']}")

        campaigns = campaigns_repo.list_all()
        active = next((c for c in campaigns if c["status"] in ("SENDING", "PAUSED")), None)
        if active:
            self.campaign_label.setText(
                f"Current Campaign\n{active['sent_count']} / {active['total_count']} Sent"
            )
        else:
            self.campaign_label.setText("Current Campaign\nNone")
