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
        layout.addWidget(QLabel("TEMPLATES"))

        body_row = QHBoxLayout()
        self.list_widget = QListWidget()
        body_row.addWidget(self.list_widget, stretch=1)

        right = QVBoxLayout()
        right.addWidget(QLabel("Body (supports {name}):"))
        self.body_edit = QPlainTextEdit()
        right.addWidget(self.body_edit)
        body_row.addLayout(right, stretch=2)
        layout.addLayout(body_row)

        row = QHBoxLayout()
        self.new_btn = QPushButton("New Template")
        self.save_btn = QPushButton("Save Changes")
        self.delete_btn = QPushButton("Delete Template")
        row.addWidget(self.new_btn)
        row.addWidget(self.save_btn)
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
            item = QListWidgetItem(t["name"])
            item.setData(1, t["id"])
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        self.body_edit.clear()

    def _load_selected(self, current, _previous) -> None:
        if current is None:
            self.body_edit.clear()
            return
        template = templates_repo.get(current.data(1))
        self.body_edit.setPlainText(template["body"] if template else "")

    def _new_template(self) -> None:
        name, ok = QInputDialog.getText(self, "New Template", "Template name:")
        if not ok or not name.strip():
            return
        template_id = templates_repo.create(name.strip(), "")
        self.refresh()
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).data(1) == template_id:
                self.list_widget.setCurrentRow(i)
                break

    def _save_selected(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            QMessageBox.information(self, "No template selected", "Create or select a template first.")
            return
        templates_repo.update(item.data(1), body=self.body_edit.toPlainText())
        QMessageBox.information(self, "Saved", "Template saved.")

    def _delete_selected(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        confirm = QMessageBox.question(self, "Delete template?", f"Delete '{item.text()}'?")
        if confirm != QMessageBox.Yes:
            return
        templates_repo.delete(item.data(1))
        self.refresh()
