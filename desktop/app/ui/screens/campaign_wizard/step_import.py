from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.excel_import import detect_columns, import_contacts, read_excel


class StepImport(QWidget):
    """Excel file picker -> column mapping (auto-detected, user can override) -> import."""

    imported = Signal(object)  # ImportResult

    def __init__(self, parent=None):
        super().__init__(parent)
        self._df = None
        self._file_path = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Title
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Step 1: Import Contacts File")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Upload an Excel spreadsheet (.xlsx, .xls) or CSV file with your contact list.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # File picker box
        file_box = QFrame()
        file_box.setStyleSheet("background-color: #1e293b; border: 1px dashed #475569; border-radius: 10px; padding: 14px;")
        file_layout = QHBoxLayout(file_box)
        
        self.pick_btn = QPushButton("📁  Choose Excel / CSV File...")
        self.pick_btn.setStyleSheet("background-color: #334155; color: white; font-weight: 600; padding: 10px 18px;")
        self.pick_btn.clicked.connect(self._pick_file)
        
        self.file_label = QLabel("No file selected.")
        self.file_label.setStyleSheet("color: #94a3b8; font-size: 13px;")
        
        file_layout.addWidget(self.pick_btn)
        file_layout.addWidget(self.file_label, stretch=1)
        layout.addWidget(file_box)

        # Mapping form
        form = QFormLayout()
        form.setSpacing(10)
        self.name_combo = QComboBox()
        self.phone_combo = QComboBox()
        self.email_combo = QComboBox()
        form.addRow("Name Column:", self.name_combo)
        form.addRow("Phone Column:", self.phone_combo)
        form.addRow("Email Column (optional):", self.email_combo)
        layout.addLayout(form)

        for combo in (self.name_combo, self.phone_combo, self.email_combo):
            combo.currentTextChanged.connect(self._refresh_preview)

        layout.addWidget(QLabel("Data Preview (First 5 Rows):"))
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(150)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.preview_table)

        row = QHBoxLayout()
        self.import_btn = QPushButton("Next: Import & Validate ➔")
        self.import_btn.setStyleSheet("background-color: #6366f1; color: white; font-weight: 700; font-size: 13px; padding: 10px 24px;")
        self.import_btn.clicked.connect(self._do_import)
        self.import_btn.setEnabled(False)
        row.addStretch()
        row.addWidget(self.import_btn)
        layout.addLayout(row)

    def _pick_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select contacts file", "", "Excel/CSV Files (*.xlsx *.xls *.csv)"
        )
        if not path:
            return
        try:
            self._df = read_excel(path)
        except Exception as exc:
            QMessageBox.critical(
                self, "Excel import failed",
                f"Please check that the file is a valid .xlsx or .csv file.\n\nDetails: {exc}"
            )
            return
        self._file_path = path
        self.file_label.setText(f"📄 {path}")
        self.file_label.setStyleSheet("color: #38bdf8; font-weight: 600;")

        headers = list(self._df.columns)
        mapping = detect_columns(self._df)
        for combo, key in ((self.name_combo, "name"), (self.phone_combo, "phone"), (self.email_combo, "email")):
            combo.blockSignals(True)
            combo.clear()
            if key == "email":
                combo.addItem("")
            combo.addItems(headers)
            if mapping[key]:
                combo.setCurrentText(mapping[key])
            combo.blockSignals(False)

        self.import_btn.setEnabled(True)
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        if self._df is None:
            return
        headers = list(self._df.columns)
        preview_rows = self._df.head(5)
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setHorizontalHeaderLabels(headers)
        self.preview_table.setRowCount(len(preview_rows))
        for r, (_, row) in enumerate(preview_rows.iterrows()):
            for c, header in enumerate(headers):
                self.preview_table.setItem(r, c, QTableWidgetItem(str(row[header])))

    def _do_import(self) -> None:
        if self._df is None:
            return
        name_col = self.name_combo.currentText()
        phone_col = self.phone_combo.currentText()
        if not name_col or not phone_col:
            QMessageBox.warning(self, "Missing mapping", "Please select both a Name and Phone column.")
            return
        email_col = self.email_combo.currentText() or None
        column_mapping = {"name": name_col, "phone": phone_col}
        if email_col:
            column_mapping["email"] = email_col

        try:
            result = import_contacts(self._df, column_mapping, source_file=self._file_path)
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", f"Could not import contacts: {exc}")
            return

        self.imported.emit(result)

    def reset(self) -> None:
        self._df = None
        self._file_path = None
        self.file_label.setText("No file selected.")
        self.file_label.setStyleSheet("color: #94a3b8;")
        self.name_combo.clear()
        self.phone_combo.clear()
        self.email_combo.clear()
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)
        self.import_btn.setEnabled(False)
