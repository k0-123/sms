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
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Contact Management")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Search, view, and manage phone numbers in your local database.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Search Bar
        top_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Search contacts by name or phone number...")
        self.search_box.setClearButtonEnabled(True)
        top_row.addWidget(self.search_box)
        layout.addLayout(top_row)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, stretch=1)

        self.selected_label = QLabel("0 contacts selected")
        self.selected_label.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 12px;")
        layout.addWidget(self.selected_label)

        row = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.deselect_all_btn = QPushButton("Deselect All")
        self.delete_btn = QPushButton("🗑️  Delete Selected")
        self.delete_btn.setStyleSheet("background-color: #450a0a; color: #fca5a5;")
        row.addWidget(self.select_all_btn)
        row.addWidget(self.deselect_all_btn)
        row.addStretch()
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
            icon = "✅" if contact["is_valid"] else "⚠️"
            label = f"{icon}  {contact['name']:<25}  •  {contact['phone_e164'] or contact['phone_raw']}"
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, contact["id"])
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        self._update_selected_count()

    def _select_all(self) -> None:
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)
        self._update_selected_count()

    def _deselect_all(self) -> None:
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)
        self._update_selected_count()

    def _update_selected_count(self) -> None:
        count = sum(1 for i in range(self.list_widget.count()) if self.list_widget.item(i).checkState() == Qt.Checked)
        self.selected_label.setText(f"{count} contact{'s' if count != 1 else ''} selected (out of {self.list_widget.count()} total)")

    def _delete_selected(self) -> None:
        selected_ids = [
            self.list_widget.item(i).data(Qt.UserRole)
            for i in range(self.list_widget.count())
            if self.list_widget.item(i).checkState() == Qt.Checked
        ]
        if not selected_ids:
            return
        confirm = QMessageBox.question(
            self, "Delete Contacts",
            f"Are you sure you want to delete {len(selected_ids)} contact(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            contacts_repo.delete_batch(selected_ids)
            self.refresh()
