from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.repositories import contacts_repo


class ContactsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("CONTACTS"))

        top_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by name or phone...")
        top_row.addWidget(self.search_box)
        layout.addLayout(top_row)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.selected_label = QLabel()
        layout.addWidget(self.selected_label)

        row = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.deselect_all_btn = QPushButton("Deselect All")
        self.delete_btn = QPushButton("Delete Selected")
        row.addWidget(self.select_all_btn)
        row.addWidget(self.deselect_all_btn)
        row.addWidget(self.delete_btn)
        layout.addLayout(row)

        self.search_box.textChanged.connect(self.refresh)
        self.select_all_btn.clicked.connect(self._select_all)
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        self.delete_btn.clicked.connect(self._delete_selected)
        self.list_widget.itemChanged.connect(self._update_selected_count)

        self.refresh()

    def refresh(self) -> None:
        search = self.search_box.text().strip() or None
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for contact in contacts_repo.list_all(search=search):
            label = f"{'✓' if contact['is_valid'] else '✗'} {contact['name']}    {contact['phone_e164'] or contact['phone_raw']}"
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, contact["id"])
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        self._update_selected_count()

    def selected_contact_ids(self) -> list[str]:
        ids = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                ids.append(item.data(Qt.UserRole))
        return ids

    def _select_all(self) -> None:
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)

    def _deselect_all(self) -> None:
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)

    def _update_selected_count(self) -> None:
        self.selected_label.setText(f"{len(self.selected_contact_ids())} contacts selected")

    def _delete_selected(self) -> None:
        ids = self.selected_contact_ids()
        if not ids:
            QMessageBox.information(self, "Nothing selected", "Check the contacts you want to delete first.")
            return
        confirm = QMessageBox.question(
            self, "Delete contacts?", f"Permanently delete {len(ids)} contact(s)?"
        )
        if confirm != QMessageBox.Yes:
            return
        contacts_repo.delete_many(ids)
        self.refresh()
