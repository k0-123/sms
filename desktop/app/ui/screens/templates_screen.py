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
        header.setSpacing(2)
        title = QLabel("Template Registry")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;")
        subtitle = QLabel("DISPATCH TEMPLATES • DYNAMIC MACROS: {NAME}")
        subtitle.setStyleSheet("font-size: 10px; color: #71717a; font-weight: 700; letter-spacing: 1px;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        body_row = QHBoxLayout()
        body_row.setSpacing(14)

        left = QVBoxLayout()
        left_lbl = QLabel("SAVED MANIFESTS:")
        left_lbl.setStyleSheet("font-size: 10px; color: #71717a; font-weight: 700; letter-spacing: 0.8px;")
        left.addWidget(left_lbl)
        self.list_widget = QListWidget()
        left.addWidget(self.list_widget)
        body_row.addLayout(left, stretch=1)

        right = QVBoxLayout()
        right_lbl = QLabel("TEMPLATE PAYLOAD:")
        right_lbl.setStyleSheet("font-size: 10px; color: #71717a; font-weight: 700; letter-spacing: 0.8px;")
        right.addWidget(right_lbl)
        self.body_edit = QPlainTextEdit()
        self.body_edit.setPlaceholderText("> Hi {name}, this is an automated dispatch from...")
        right.addWidget(self.body_edit)
        body_row.addLayout(right, stretch=2)

        layout.addLayout(body_row)

        row = QHBoxLayout()
        self.new_btn = QPushButton("[ + NEW_TEMPLATE ]")
        self.save_btn = QPushButton("[ 💾 SAVE_PAYLOAD ]")
        self.save_btn.setStyleSheet("background-color: #18181b; border: 1px solid #00e599; color: #00e599; font-weight: 700;")
        self.delete_btn = QPushButton("[ 🗑️ PURGE ]")
        self.delete_btn.setStyleSheet("background-color: #270909; border: 1px solid #7f1d1d; color: #fca5a5;")
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
