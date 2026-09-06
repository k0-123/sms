from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.repositories import contacts_repo
from app.services.excel_import import detect_columns, import_contacts, read_excel


class ContactsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)

        # Header Title & Monospace Telemetry
        header = QVBoxLayout()
        header.setSpacing(2)
        title = QLabel("Contacts Directory")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;")
        
        self.count_sub = QLabel("DISPLAYING 0 OF 0 TOTAL RECORDS")
        self.count_sub.setStyleSheet("font-size: 10px; color: #71717a; font-weight: 700; letter-spacing: 1px;")
        
        header.addWidget(title)
        header.addWidget(self.count_sub)
        layout.addLayout(header)

        # Prompt Search Bar
        search_box_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("> search --name or --phone")
        self.search_box.setClearButtonEnabled(True)
        search_box_layout.addWidget(self.search_box, stretch=1)
        layout.addLayout(search_box_layout)

        # Filter & Action Row
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.import_file_btn = QPushButton("[ 📁 IMPORT_FILE ]")
        self.import_file_btn.setStyleSheet("background-color: #18181b; border: 1px solid #00e599; color: #00e599; font-weight: 700;")
        
        self.add_btn = QPushButton("[ + ADD ]")
        self.delete_btn = QPushButton("[ 🗑️ DELETE ]")
        self.delete_btn.setStyleSheet("background-color: #270909; border: 1px solid #7f1d1d; color: #fca5a5;")
        self.export_btn = QPushButton("[ 📥 EXPORT ]")

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["MODE: ALL", "MODE: VALID ONLY", "MODE: INVALID ONLY"])

        action_row.addWidget(self.import_file_btn)
        action_row.addWidget(self.add_btn)
        action_row.addWidget(self.delete_btn)
        action_row.addWidget(self.export_btn)
        action_row.addStretch()
        action_row.addWidget(self.filter_combo)
        layout.addLayout(action_row)

        # Data Queue Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID / SELECT", "RECIPIENT NAME", "PHONE (E.164)", "TELEMETRY STATUS"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.table, stretch=1)

        # Signals
        self.search_box.textChanged.connect(self.refresh)
        self.filter_combo.currentTextChanged.connect(self.refresh)
        self.import_file_btn.clicked.connect(self._import_from_file)
        self.add_btn.clicked.connect(self._add_contact_manual)
        self.delete_btn.clicked.connect(self._delete_selected)
        self.export_btn.clicked.connect(self._export_contacts)

        self.refresh()

    def refresh(self) -> None:
        search = self.search_box.text().strip() or None
        mode = self.filter_combo.currentText()
        valid_only = mode == "MODE: VALID ONLY"
        contacts = contacts_repo.list_all(valid_only=valid_only, search=search)
        if mode == "MODE: INVALID ONLY":
            contacts = [c for c in contacts if not c["is_valid"]]

        self.table.setRowCount(len(contacts))
        counts = contacts_repo.counts()
        self.count_sub.setText(f"DISPLAYING {len(contacts)} OF {counts['total']} TOTAL RECORDS • {counts['valid']} VALID")

        for r, c in enumerate(contacts):
            phone_str = c["phone_e164"] or c["phone_raw"]
            name_str = c["name"] or "--"
            status_str = "🟢 VALID" if c["is_valid"] else f"🔴 INVALID ({c['validation_error'] or 'FORMAT_ERR'})"

            item_id = QTableWidgetItem(f"[{r+1:03d}]")
            item_id.setFlags(item_id.flags() | Qt.ItemIsUserCheckable)
            item_id.setCheckState(Qt.Unchecked)
            item_id.setData(Qt.UserRole, c["id"])

            self.table.setItem(r, 0, item_id)
            self.table.setItem(r, 1, QTableWidgetItem(name_str))
            self.table.setItem(r, 2, QTableWidgetItem(phone_str))
            self.table.setItem(r, 3, QTableWidgetItem(status_str))

    def _import_from_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select contacts file", "", "Excel/CSV Files (*.xlsx *.xls *.csv)"
        )
        if not path:
            return
        try:
            df = read_excel(path)
            mapping = detect_columns(df)
            headers = [str(c) for c in df.columns]
            if not mapping.get("phone") and headers:
                mapping["phone"] = headers[0]
            if len(headers) == 1 and mapping.get("name") == mapping.get("phone"):
                mapping["name"] = None
            result = import_contacts(df, column_mapping=mapping, source_file=path)
            QMessageBox.information(
                self, "Import Complete",
                f"Imported {result.total} records:\n• {result.valid} Valid\n• {result.invalid} Invalid\n• {result.duplicates} Duplicates"
            )
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Import Failed", f"Could not read file:\n{exc}")

    def _add_contact_manual(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Record", "Contact Name (optional):")
        if not ok:
            return
        phone, ok = QInputDialog.getText(self, "Add Record", "Phone Number (e.g. +919024709980):")
        if not ok or not phone.strip():
            return
        phone_clean = phone.strip()
        e164 = phone_clean if phone_clean.startswith("+") else ("+91" + phone_clean if len(phone_clean) == 10 else phone_clean)
        display_name = name.strip() if name.strip() else phone_clean
        contacts_repo.create(name=display_name, phone_raw=phone_clean, phone_e164=e164, is_valid=True)
        self.refresh()

    def _delete_selected(self) -> None:
        selected_ids = []
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.checkState() == Qt.Checked:
                selected_ids.append(item.data(Qt.UserRole))

        if not selected_ids:
            row = self.table.currentRow()
            if row >= 0:
                item = self.table.item(row, 0)
                if item:
                    selected_ids.append(item.data(Qt.UserRole))

        if not selected_ids:
            QMessageBox.information(self, "No Selection", "Please check or select record(s) to purge.")
            return

        confirm = QMessageBox.question(
            self, "Purge Records",
            f"Are you sure you want to permanently delete {len(selected_ids)} record(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            contacts_repo.delete_many(selected_ids)
            self.refresh()

    def _export_contacts(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Records", "contacts.xlsx", "Excel Files (*.xlsx);;CSV Files (*.csv)")
        if not path:
            return
        import pandas as pd
        contacts = contacts_repo.list_all()
        data = [{"Name": c["name"], "Phone": c["phone_e164"] or c["phone_raw"], "Valid": c["is_valid"]} for c in contacts]
        df = pd.DataFrame(data)
        if path.endswith(".csv"):
            df.to_csv(path, index=False)
        else:
            df.to_excel(path, index=False)
        QMessageBox.information(self, "Export Complete", f"Exported {len(contacts)} records to:\n{path}")
