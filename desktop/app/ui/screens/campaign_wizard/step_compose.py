from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
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
        layout.addWidget(QLabel("WRITE MESSAGE"))

        row = QHBoxLayout()
        self.template_combo = QComboBox()
        self.load_template_btn = QPushButton("Use Template")
        self.insert_name_btn = QPushButton("Insert {name}")
        row.addWidget(self.template_combo)
        row.addWidget(self.load_template_btn)
        row.addWidget(self.insert_name_btn)
        layout.addLayout(row)

        self.body_edit = QPlainTextEdit()
        layout.addWidget(self.body_edit)

        self.counter_label = QLabel()
        layout.addWidget(self.counter_label)

        self.continue_btn = QPushButton("Continue")
        layout.addWidget(self.continue_btn)

        self.body_edit.textChanged.connect(self._update_counter)
        self.insert_name_btn.clicked.connect(lambda: self.body_edit.insertPlainText("{name}"))
        self.load_template_btn.clicked.connect(self._load_template)
        self.continue_btn.clicked.connect(self._continue)

        self._update_counter()

    def reload_templates(self) -> None:
        self.template_combo.clear()
        for t in templates_repo.list_all():
            self.template_combo.addItem(t["name"], t["id"])

    def _load_template(self) -> None:
        template_id = self.template_combo.currentData()
        if not template_id:
            return
        template = templates_repo.get(template_id)
        if template:
            self.body_edit.setPlainText(template["body"])

    def _update_counter(self) -> None:
        text = self.body_edit.toPlainText()
        chars, parts = sms_part_count(text)
        warning = ""
        if parts > 1:
            warning = "  ⚠ This message will be split into multiple SMS parts."
        self.counter_label.setText(f"Characters: {chars}    SMS Parts: {parts}{warning}")

    def _continue(self) -> None:
        text = self.body_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Empty message", "Please write a message before continuing.")
            return
        self.continued.emit(text)
