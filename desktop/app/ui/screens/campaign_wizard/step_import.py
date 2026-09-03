from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
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
        layout.addWidget(QLabel("IMPORT CONTACTS"))

        self.pick_btn = QPushButton("Import Excel")
        self.pick_btn.clicked.connect(self._pick_file)
        layout.addWidget(self.pick_btn)

        self.file_label = QLabel("No file selected.")
        layout.addWidget(self.file_label)

        form = QFormLayout()
        self.name_combo = QComboBox()
        self.phone_combo = QComboBox()
        self.email_combo = QComboBox()
        form.addRow("Name Column:", self.name_combo)
        form.addRow("Phone Column:", self.phone_combo)
        form.addRow("Email Column (optional):", self.email_combo)
        layout.addLayout(form)

        for combo in (self.name_combo, self.phone_combo, self.email_combo):
            combo.currentTextChanged.connect(self._refresh_preview)

        layout.addWidget(QLabel("Preview (first 5 rows):"))
        self.preview_table = QTableWidget()
        layout.addWidget(self.preview_table)

        row = QHBoxLayout()
        self.import_btn = QPushButton("Import Contacts")
        self.import_btn.clicked.connect(self._do_import)
        self.import_btn.setEnabled(False)
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
        self.file_label.setText(path)

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
        email_col = self.email_combo.currentText() or None
        if not name_col or not phone_col:
            QMessageBox.warning(self, "Missing mapping", "Please select both a Name and a Phone column.")
            return
        result = import_contacts(self._file_path, self._df, name_col, phone_col, email_col)
        if result.total == 0:
            QMessageBox.warning(
                self, "No valid contacts found", "Please check your Excel file."
            )
            return
        self.imported.emit(result)
