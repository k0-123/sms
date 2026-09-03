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
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Title
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Step 3: Select Campaign Recipients")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Choose which verified contacts should receive this message broadcast.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, stretch=1)

        self.count_label = QLabel("0 contacts selected")
        self.count_label.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 12px;")
        layout.addWidget(self.count_label)

        row = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.deselect_all_btn = QPushButton("Deselect All")
        self.continue_btn = QPushButton("Next: Compose Message ➔")
        self.continue_btn.setStyleSheet("background-color: #6366f1; color: white; font-weight: 700; font-size: 13px; padding: 10px 24px;")
        
        row.addWidget(self.select_all_btn)
        row.addWidget(self.deselect_all_btn)
        row.addStretch()
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
            item = QListWidgetItem(f"📱  {contact['name']:<25}  •  {contact['phone_e164']}")
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

    def _update_count(self) -> None:
        selected = sum(
            1 for i in range(self.list_widget.count())
            if self.list_widget.item(i).checkState() == Qt.Checked
        )
        self.count_label.setText(f"👥 {selected} of {self.list_widget.count()} contact(s) selected for this campaign")

    def _continue(self) -> None:
        ids = [
            self.list_widget.item(i).data(Qt.UserRole)
            for i in range(self.list_widget.count())
            if self.list_widget.item(i).checkState() == Qt.Checked
        ]
        self.continued.emit(ids)
