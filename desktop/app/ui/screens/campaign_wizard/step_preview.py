import random

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.repositories import contacts_repo
from app.services.message import render


class StepPreview(QWidget):
    """Shows the rendered message for a few sampled selected contacts."""

    continued = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._samples: list = []
        self._index = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Title
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Step 5: Preview Personalized Messages")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Verify how your text and dynamic {name} tags look for actual recipients before broadcasting.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Recipient Card
        self.recipient_box = QFrame()
        self.recipient_box.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 12px;")
        recip_layout = QVBoxLayout(self.recipient_box)
        recip_layout.setContentsMargins(12, 8, 12, 8)
        
        self.recipient_label = QLabel()
        self.recipient_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #38bdf8;")
        recip_layout.addWidget(self.recipient_label)
        layout.addWidget(self.recipient_box)

        # Rendered message box
        layout.addWidget(QLabel("Rendered SMS Output:"))
        self.message_view = QTextEdit()
        self.message_view.setReadOnly(True)
        self.message_view.setMinimumHeight(140)
        layout.addWidget(self.message_view)

        # Navigation row
        nav_row = QHBoxLayout()
        self.prev_btn = QPushButton("◀  Previous Sample")
        self.next_btn = QPushButton("Next Sample  ▶")
        nav_row.addWidget(self.prev_btn)
        nav_row.addWidget(self.next_btn)
        nav_row.addStretch()
        
        self.continue_btn = QPushButton("Next: Final Confirmation ➔")
        self.continue_btn.setStyleSheet("background-color: #6366f1; color: white; font-weight: 700; font-size: 13px; padding: 10px 24px;")
        nav_row.addWidget(self.continue_btn)
        layout.addLayout(nav_row)

        self.prev_btn.clicked.connect(self._show_prev)
        self.next_btn.clicked.connect(self._show_next)
        self.continue_btn.clicked.connect(self.continued.emit)

    def load(self, contact_ids: list[str], message_body: str, sample_size: int = 5) -> None:
        contacts = [contacts_repo.get(cid) for cid in contact_ids]
        contacts = [c for c in contacts if c is not None]
        sample = random.sample(contacts, min(sample_size, len(contacts))) if contacts else []
        self._samples = [(c, render(message_body, c["name"])) for c in sample]
        self._index = 0
        self._render()

    def _render(self) -> None:
        if not self._samples:
            self.recipient_label.setText("No contacts to preview.")
            self.message_view.setPlainText("")
            return
        contact, rendered = self._samples[self._index]
        self.recipient_label.setText(
            f"📱 Recipient {self._index + 1} of {len(self._samples)}:   {contact['name']}  •  {contact['phone_e164']}"
        )
        self.message_view.setPlainText(rendered)

    def _show_prev(self) -> None:
        if self._samples and self._index > 0:
            self._index -= 1
            self._render()

    def _show_next(self) -> None:
        if self._samples and self._index < len(self._samples) - 1:
            self._index += 1
            self._render()
