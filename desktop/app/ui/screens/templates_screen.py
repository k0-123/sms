from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.repositories import templates_repo


class TemplatesScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Message Templates")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Create reusable SMS message templates with dynamic placeholders like {name}.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        body_row = QHBoxLayout()
        body_row.setSpacing(16)

        left = QVBoxLayout()
        left.addWidget(QLabel("Saved Templates:"))
        self.list_widget = QListWidget()
        left.addWidget(self.list_widget)
        body_row.addLayout(left, stretch=1)

        right = QVBoxLayout()
        right.addWidget(QLabel("Template Content (use {name} for recipient's name):"))
        self.body_edit = QPlainTextEdit()
        self.body_edit.setPlaceholderText("Hi {name}, this is an automated update regarding your account...")
        right.addWidget(self.body_edit)
        body_row.addLayout(right, stretch=2)

        layout.addLayout(body_row)

        row = QHBoxLayout()
        self.new_btn = QPushButton("➕  New Template")
        self.save_btn = QPushButton("💾  Save Changes")
        self.save_btn.setStyleSheet("background-color: #6366f1; color: white; font-weight: 700;")
        self.delete_btn = QPushButton("🗑️  Delete")
        self.delete_btn.setStyleSheet("background-color: #450a0a; color: #fca5a5;")
        row.addWidget(self.new_btn)
        row.addWidget(self.save_btn)
        row.addStretch()
        row.addWidget(self.delete_btn)
        layout.addLayout(row)

        self.list_widget.currentItemChanged.connect(self._load_selected)
        self.new_btn.clicked.connect(self._new_template)
        self.save_btn.clicked.connect(self._save_selected)
        self.delete_btn.clicked.connect(self._delete_selected)

        self.refresh()

    def refresh(self) -> None:
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for t in templates_repo.list_all():
            item = QListWidgetItem(f"📝 {t['name']}")
            item.setData(1, t["id"])
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        self.body_edit.clear()

    def _load_selected(self, current, _previous) -> None:
        if current is None:
            self.body_edit.clear()
            return
        template_id = current.data(1)
        template = templates_repo.get(template_id)
        if template:
            self.body_edit.setPlainText(template["body"])

    def _new_template(self) -> None:
        name, ok = QInputDialog.getText(self, "New Template", "Enter a name for the new template:")
        if not ok or not name.strip():
            return
        template_id = templates_repo.create(name.strip(), "")
        self.refresh()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(1) == template_id:
                self.list_widget.setCurrentItem(item)
                break

    def _save_selected(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            QMessageBox.information(self, "No template selected", "Select a template from the list first.")
            return
        template_id = item.data(1)
        templates_repo.update_body(template_id, self.body_edit.toPlainText())
        QMessageBox.information(self, "Saved", "Template saved successfully.")

    def _delete_selected(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        template_id = item.data(1)
        confirm = QMessageBox.question(
            self, "Delete Template", "Are you sure you want to delete this template?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            templates_repo.delete(template_id)
            self.refresh()
