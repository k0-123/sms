from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.repositories import templates_repo
from app.services.message import sms_part_count


class StepCompose(QWidget):
    """Message editor with {name} personalization and live SMS character/part count."""

    continued = Signal(str)  # message body

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Title
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Step 4: Compose Message")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Write your SMS text. Use {name} to automatically insert recipient names.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Template Picker Bar
        tmpl_box = QFrame()
        tmpl_box.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 6px;")
        tmpl_layout = QHBoxLayout(tmpl_box)
        tmpl_layout.setContentsMargins(8, 4, 8, 4)
        tmpl_layout.setSpacing(10)

        tmpl_label = QLabel("Template:")
        tmpl_label.setStyleSheet("font-weight: 600; color: #94a3b8;")
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(180)
        self.load_template_btn = QPushButton("Load Template")
        self.insert_name_btn = QPushButton("➕ Insert {name}")
        self.insert_name_btn.setStyleSheet("background-color: #312e81; color: #c7d2fe; border: 1px solid #4338ca;")

        tmpl_layout.addWidget(tmpl_label)
        tmpl_layout.addWidget(self.template_combo)
        tmpl_layout.addWidget(self.load_template_btn)
        tmpl_layout.addStretch()
        tmpl_layout.addWidget(self.insert_name_btn)
        layout.addWidget(tmpl_box)

        # Body Edit
        self.body_edit = QPlainTextEdit()
        self.body_edit.setPlaceholderText("Type your SMS message here...\nExample: Hello {name}, your appointment is confirmed for tomorrow!")
        self.body_edit.setMinimumHeight(160)
        layout.addWidget(self.body_edit)

        # Counter Badge
        self.counter_label = QLabel("0 characters • 0 parts")
        self.counter_label.setStyleSheet(
            "background-color: #1e293b; color: #38bdf8; border: 1px solid #334155; "
            "border-radius: 6px; padding: 6px 12px; font-weight: 700; font-size: 12px;"
        )
        layout.addWidget(self.counter_label)

        # Next Button
        row = QHBoxLayout()
        self.continue_btn = QPushButton("Next: Preview Campaign ➔")
        self.continue_btn.setStyleSheet("background-color: #6366f1; color: white; font-weight: 700; font-size: 13px; padding: 10px 24px;")
        row.addStretch()
        row.addWidget(self.continue_btn)
        layout.addLayout(row)

        self.body_edit.textChanged.connect(self._update_counter)
        self.insert_name_btn.clicked.connect(lambda: self.body_edit.insertPlainText("{name}"))
        self.load_template_btn.clicked.connect(self._load_template)
        self.continue_btn.clicked.connect(self._continue)

        self._update_counter()

    def reload_templates(self) -> None:
        self.template_combo.clear()
        for t in templates_repo.list_all():
            self.template_combo.addItem(f"📝 {t['name']}", t["id"])

    def _load_template(self) -> None:
        template_id = self.template_combo.currentData()
        if not template_id:
            return
        t = templates_repo.get(template_id)
        if t:
            self.body_edit.setPlainText(t["body"])

    def _update_counter(self) -> None:
        text = self.body_edit.toPlainText()
        chars, parts = sms_part_count(text)
        single_limit = 160
        multi_chunk = 153
        if parts <= 1:
            remain = single_limit - chars
            self.counter_label.setText(f"📊 {chars}/{single_limit} characters  •  {parts} SMS part  •  ({remain} chars remaining in single SMS)")
            self.counter_label.setStyleSheet("background-color: #1e293b; color: #34d399; border: 1px solid #334155; border-radius: 6px; padding: 6px 12px; font-weight: 700; font-size: 12px;")
        else:
            self.counter_label.setText(f"📊 {chars} characters  •  {parts} concatenated SMS parts (153 chars/segment)")
            self.counter_label.setStyleSheet("background-color: #1e293b; color: #fbbf24; border: 1px solid #334155; border-radius: 6px; padding: 6px 12px; font-weight: 700; font-size: 12px;")

    def _continue(self) -> None:
        text = self.body_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Empty message", "Please enter a message body before continuing.")
            return
        self.continued.emit(self.body_edit.toPlainText())

    def reset(self) -> None:
        self.body_edit.clear()
        self.reload_templates()
        self._update_counter()
