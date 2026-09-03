from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.repositories import contacts_repo


class StepSelect(QWidget):
    """Select which valid contacts this campaign will message."""

    continued = Signal(list)  # list[contact_id]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("SELECT CONTACTS"))

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.count_label = QLabel()
        layout.addWidget(self.count_label)

        row = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.deselect_all_btn = QPushButton("Deselect All")
        self.continue_btn = QPushButton("Continue")
        row.addWidget(self.select_all_btn)
        row.addWidget(self.deselect_all_btn)
        row.addWidget(self.continue_btn)
        layout.addLayout(row)

        self.select_all_btn.clicked.connect(self._select_all)
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        self.continue_btn.clicked.connect(self._continue)
        self.list_widget.itemChanged.connect(self._update_count)

    def reload(self) -> None:
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for contact in contacts_repo.list_all(valid_only=True):
            item = QListWidgetItem(f"{contact['name']}    {contact['phone_e164']}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)  # default: all valid contacts selected
            item.setData(Qt.UserRole, contact["id"])
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        self._update_count()

    def _select_all(self) -> None:
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)
        self._update_count()

    def _deselect_all(self) -> None:
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)
        self._update_count()

    def _selected_ids(self) -> list[str]:
        return [
            self.list_widget.item(i).data(Qt.UserRole)
            for i in range(self.list_widget.count())
            if self.list_widget.item(i).checkState() == Qt.Checked
        ]

    def _update_count(self) -> None:
        self.count_label.setText(f"{len(self._selected_ids())} contacts selected")

    def _continue(self) -> None:
        ids = self._selected_ids()
        if ids:
            self.continued.emit(ids)
