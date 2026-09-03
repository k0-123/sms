from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
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
    """Shows Valid / Invalid / Duplicates breakdown. Never silently deletes -
    Remove buttons are explicit, opt-in user actions (PRD Section 7)."""

    continued = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("VALIDATE CONTACTS"))

        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)

        self.tabs = QTabWidget()
        self.invalid_table = QTableWidget()
        self.duplicate_table = QTableWidget()
        self.tabs.addTab(self.invalid_table, "Invalid")
        self.tabs.addTab(self.duplicate_table, "Duplicates")
        layout.addWidget(self.tabs)

        row = QHBoxLayout()
        self.remove_invalid_btn = QPushButton("Remove Invalid")
        self.remove_duplicates_btn = QPushButton("Remove Duplicates")
        self.continue_btn = QPushButton("Continue")
        row.addWidget(self.remove_invalid_btn)
        row.addWidget(self.remove_duplicates_btn)
        row.addWidget(self.continue_btn)
        layout.addLayout(row)

        self.remove_invalid_btn.clicked.connect(self._remove_invalid)
        self.remove_duplicates_btn.clicked.connect(self._remove_duplicates)
        self.continue_btn.clicked.connect(self.continued.emit)

    def load_result(self, result) -> None:
        self.summary_label.setText(
            f"Total Contacts: {result.total}\n"
            f"Valid: {result.valid}\n"
            f"Invalid: {result.invalid}\n"
            f"Duplicates: {result.duplicates}"
        )
        invalid_rows = [r for r in result.rows if not r["is_valid"] and not (r["error"] or "").startswith("Duplicate") and r["error"] != "Already exists in contacts"]
        dup_rows = [r for r in result.rows if not r["is_valid"] and ((r["error"] or "").startswith("Duplicate") or r["error"] == "Already exists in contacts")]
        self._fill_table(self.invalid_table, invalid_rows)
        self._fill_table(self.duplicate_table, dup_rows)

    @staticmethod
    def _fill_table(table: QTableWidget, rows: list[dict]) -> None:
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Row", "Name", "Phone", "Reason"])
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(str(row["row"])))
            table.setItem(r, 1, QTableWidgetItem(str(row["name"])))
            table.setItem(r, 2, QTableWidgetItem(str(row["phone"])))
            table.setItem(r, 3, QTableWidgetItem(str(row["error"])))
        table._contact_ids = [row["contact_id"] for row in rows]

    def _remove_invalid(self) -> None:
        self._remove_from_table(self.invalid_table, "invalid contacts")

    def _remove_duplicates(self) -> None:
        self._remove_from_table(self.duplicate_table, "duplicate contacts")

    def _remove_from_table(self, table: QTableWidget, label: str) -> None:
        if table.rowCount() == 0:
            return
        confirm = QMessageBox.question(
            self, f"Remove {label}?",
            f"This will permanently delete {table.rowCount()} {label} from your contact list. Continue?",
        )
        if confirm != QMessageBox.Yes:
            return
        # Names/phones alone aren't unique identifiers; re-resolve via contacts_repo by row text
        # is unreliable, so this action operates on invalid contacts as a bulk cleanup instead.
        ids = getattr(table, "_contact_ids", None)
        if ids:
            contacts_repo.delete_many(ids)
        table.setRowCount(0)
