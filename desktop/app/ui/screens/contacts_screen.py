from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
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
from app.services.export import export_campaign_results


class ContactsScreen(QWidget):
    request_send_campaign = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Header Title & Subtitle (Like QuickText)
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title = QLabel("Contacts")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #0f172a;")
        subtitle = QLabel("The people you send messages to. Import them from a file or add them by hand.")
        subtitle.setStyleSheet("font-size: 13.5px; color: #64748b;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # Action Buttons Toolbar
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.import_file_btn = QPushButton("Import from file")
        self.import_file_btn.setStyleSheet(
            "background-color: #1d4ed8; color: #ffffff; font-weight: 600; "
            "border: 1px solid #1e40af; border-radius: 6px; padding: 8px 16px;"
        )
        self.import_file_btn.setCursor(Qt.PointingHandCursor)

        self.import_phone_btn = QPushButton("Import from phone")
        self.import_phone_btn.setStyleSheet(
            "background-color: #1e3a8a; color: #ffffff; font-weight: 600; "
            "border: 1px solid #172554; border-radius: 6px; padding: 8px 16px;"
        )
        self.import_phone_btn.setCursor(Qt.PointingHandCursor)

        self.add_btn = QPushButton("Add contact")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet("color: #dc2626; border-color: #fca5a5;")
        self.lists_btn = QPushButton("Lists")
        self.export_btn = QPushButton("Export")

        action_row.addWidget(self.import_file_btn)
        action_row.addWidget(self.import_phone_btn)
        action_row.addWidget(self.add_btn)
        action_row.addWidget(self.edit_btn)
        action_row.addWidget(self.delete_btn)
        action_row.addWidget(self.lists_btn)
        action_row.addWidget(self.export_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

        # Search Bar + Filter + Count
        search_row = QHBoxLayout()
        search_row.setSpacing(12)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search contacts...")
        self.search_box.setClearButtonEnabled(True)

        self.list_filter_combo = QComboBox()
        self.list_filter_combo.addItems(["All lists", "Valid Numbers Only", "Recent Imports"])

        self.count_label = QLabel("0 contacts")
        self.count_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500;")

        search_row.addWidget(self.search_box, stretch=1)
        search_row.addWidget(self.list_filter_combo)
        search_row.addWidget(self.count_label)
        layout.addLayout(search_row)

        # Main Table Container
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Phone number", "Details (Name)", "Lists", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.table, stretch=1)

        # Signals
        self.search_box.textChanged.connect(self.refresh)
        self.list_filter_combo.currentTextChanged.connect(self.refresh)
        self.import_file_btn.clicked.connect(self._import_from_file)
        self.import_phone_btn.clicked.connect(self._import_from_phone)
        self.add_btn.clicked.connect(self._add_contact_manual)
        self.delete_btn.clicked.connect(self._delete_selected)
        self.export_btn.clicked.connect(self._export_contacts)

        self.refresh()

    def refresh(self) -> None:
        search = self.search_box.text().strip() or None
        valid_only = self.list_filter_combo.currentText() == "Valid Numbers Only"
        contacts = contacts_repo.list_all(valid_only=valid_only, search=search)

        self.table.setRowCount(len(contacts))
        self.count_label.setText(f"{len(contacts)} contact{'s' if len(contacts) != 1 else ''}")

        for r, c in enumerate(contacts):
            phone_str = c["phone_e164"] or c["phone_raw"]
            name_str = c["name"] or "Unnamed"
            status_str = "✅ Valid" if c["is_valid"] else f"⚠️ {c['validation_error'] or 'Invalid'}"

            item_phone = QTableWidgetItem(phone_str)
            item_phone.setFlags(item_phone.flags() | Qt.ItemIsUserCheckable)
            item_phone.setCheckState(Qt.Unchecked)
            item_phone.setData(Qt.UserRole, c["id"])

            self.table.setItem(r, 0, item_phone)
            self.table.setItem(r, 1, QTableWidgetItem(name_str))
            self.table.setItem(r, 2, QTableWidgetItem("Default"))
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
            if not mapping["name"] or not mapping["phone"]:
                headers = list(df.columns)
                name_col = headers[0] if headers else "Name"
                phone_col = headers[1] if len(headers) > 1 else headers[0]
                mapping = {"name": name_col, "phone": phone_col}
            result = import_contacts(df, mapping, source_file=path)
            QMessageBox.information(
                self, "Import Successful",
                f"Imported {result.total} contacts:\n• {result.valid} Valid\n• {result.invalid} Invalid\n• {result.duplicates} Duplicates"
            )
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Import Failed", f"Could not read file:\n{exc}")

    def _import_from_phone(self) -> None:
        QMessageBox.information(
            self, "Import from Phone",
            "To sync contacts directly from your phone's address book, start the SMS Bridge companion app on your phone."
        )

    def _add_contact_manual(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Contact", "Contact Name:")
        if not ok or not name.strip():
            return
        phone, ok = QInputDialog.getText(self, "Add Contact", "Phone Number (e.g. +919024709980):")
        if not ok or not phone.strip():
            return
        phone_clean = phone.strip()
        e164 = phone_clean if phone_clean.startswith("+") else ("+91" + phone_clean if len(phone_clean) == 10 else phone_clean)
        contacts_repo.create(name=name.strip(), phone_raw=phone_clean, phone_e164=e164, is_valid=True)
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
            QMessageBox.information(self, "No Selection", "Please check or select contact(s) to delete.")
            return

        confirm = QMessageBox.question(
            self, "Delete Contacts",
            f"Are you sure you want to delete {len(selected_ids)} contact(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            contacts_repo.delete_batch(selected_ids)
            self.refresh()

    def _export_contacts(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Contacts", "contacts.xlsx", "Excel Files (*.xlsx);;CSV Files (*.csv)")
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
        QMessageBox.information(self, "Exported", f"Successfully exported {len(contacts)} contacts to:\n{path}")
