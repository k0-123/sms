import random

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.repositories import contacts_repo
from app.services.message import render


class StepPreview(QWidget):
    """Shows the rendered message for a few randomly-sampled selected contacts,
    so the user can confirm {name} personalization looks right before sending."""

    continued = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._samples: list = []
        self._index = 0

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("MESSAGE PREVIEW"))

        self.recipient_label = QLabel()
        layout.addWidget(self.recipient_label)

        self.message_view = QTextEdit()
        self.message_view.setReadOnly(True)
        layout.addWidget(self.message_view)

        row = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        row.addWidget(self.prev_btn)
        row.addWidget(self.next_btn)
        layout.addLayout(row)

        self.continue_btn = QPushButton("Continue")
        layout.addWidget(self.continue_btn)

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
            f"Recipient {self._index + 1} of {len(self._samples)}:\n{contact['name']}\n{contact['phone_e164']}"
        )
        self.message_view.setPlainText(rendered)

    def _show_prev(self) -> None:
        if self._samples:
            self._index = (self._index - 1) % len(self._samples)
            self._render()

    def _show_next(self) -> None:
        if self._samples:
            self._index = (self._index + 1) % len(self._samples)
            self._render()
