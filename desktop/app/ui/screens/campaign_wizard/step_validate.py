from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.repositories import contacts_repo


class StepValidate(QWidget):
    """Shows Valid / Invalid / Duplicates breakdown."""

    continued = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Title
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Step 2: Validate Contacts")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Review imported contacts, verify phone number formats, and clean up duplicates.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Summary box
        summary_box = QFrame()
        summary_box.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 12px;")
        summary_layout = QVBoxLayout(summary_box)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #f8fafc;")
        summary_layout.addWidget(self.summary_label)
        layout.addWidget(summary_box)

        self.tabs = QTabWidget()
        self.invalid_table = QTableWidget()
        self.duplicate_table = QTableWidget()
        self.invalid_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.duplicate_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabs.addTab(self.invalid_table, "⚠️ Invalid Numbers")
        self.tabs.addTab(self.duplicate_table, "👥 Duplicate Numbers")
        layout.addWidget(self.tabs, stretch=1)

        row = QHBoxLayout()
        self.remove_invalid_btn = QPushButton("Remove Invalid")
        self.remove_duplicates_btn = QPushButton("Remove Duplicates")
        self.continue_btn = QPushButton("Next: Select Recipients ➔")
        self.continue_btn.setStyleSheet("background-color: #6366f1; color: white; font-weight: 700; font-size: 13px; padding: 10px 24px;")
        
        row.addWidget(self.remove_invalid_btn)
        row.addWidget(self.remove_duplicates_btn)
        row.addStretch()
        row.addWidget(self.continue_btn)
        layout.addLayout(row)

        self.remove_invalid_btn.clicked.connect(self._remove_invalid)
        self.remove_duplicates_btn.clicked.connect(self._remove_duplicates)
        self.continue_btn.clicked.connect(self.continued.emit)

    def load_result(self, result) -> None:
        self.summary_label.setText(
            f"📊 Total Contacts: {result.total}    |    ✅ Valid: {result.valid}    |    ⚠️ Invalid: {result.invalid}    |    👥 Duplicates: {result.duplicates}"
        )
        invalid_rows = [r for r in result.rows if not r["is_valid"] and not (r["error"] or "").startswith("Duplicate") and r["error"] != "Already exists in contacts"]
        dup_rows = [r for r in result.rows if not r["is_valid"] and ((r["error"] or "").startswith("Duplicate") or r["error"] == "Already exists in contacts")]
        self._fill_table(self.invalid_table, invalid_rows)
        self._fill_table(self.duplicate_table, dup_rows)

    def _fill_table(self, table: QTableWidget, rows: list) -> None:
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Name", "Raw Phone", "Reason / Issue"])
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(str(row.get("name", ""))))
            table.setItem(r, 1, QTableWidgetItem(str(row.get("phone_raw", ""))))
            table.setItem(r, 2, QTableWidgetItem(str(row.get("error", ""))))

    def _remove_invalid(self) -> None:
        deleted = contacts_repo.delete_invalid()
        self.invalid_table.setRowCount(0)
        QMessageBox.information(self, "Invalid contacts removed", f"Removed {deleted} invalid contact(s).")

    def _remove_duplicates(self) -> None:
        deleted = contacts_repo.deduplicate()
        self.duplicate_table.setRowCount(0)
        QMessageBox.information(self, "Duplicates removed", f"Removed {deleted} duplicate contact(s).")
