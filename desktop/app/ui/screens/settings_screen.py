import os

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import DB_PATH
from app.db.connection import close_connection
from app.db.migrations import run_migrations
from app.services import settings_store


class SettingsScreen(QWidget):
    def __init__(self, devices_screen=None, parent=None):
        super().__init__(parent)
        self.devices_screen = devices_screen
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Application Settings")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("Configure default transmission rate limits, column mappings, and local database.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # -- Phone ------------------------------------------------------
        phone_box = QGroupBox("Phone Gateway Connection")
        phone_form = QFormLayout(phone_box)
        phone_form.setSpacing(10)
        self.connected_device_label = QLabel("None")
        self.connected_device_label.setStyleSheet("font-weight: 700; color: #818cf8;")
        phone_form.addRow("Paired Companion Device:", self.connected_device_label)
        self.test_connection_btn = QPushButton("📡  Test Connection to Phone")
        phone_form.addRow(self.test_connection_btn)
        layout.addWidget(phone_box)

        # -- Sending -------------------------------------------------------
        sending_box = QGroupBox("SMS Transmission & Throttle Limits")
        sending_form = QFormLayout(sending_box)
        sending_form.setSpacing(10)
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(500, 60000)
        self.rate_spin.setSingleStep(500)
        self.rate_spin.setSuffix(" ms between messages")
        sending_form.addRow("Default Sending Interval:", self.rate_spin)
        
        self.daily_limit_spin = QSpinBox()
        self.daily_limit_spin.setRange(1, 2000)
        self.daily_limit_spin.setSuffix(" messages / day")
        sending_form.addRow("Daily SMS Limit (Carrier Safe):", self.daily_limit_spin)
        
        self.auto_pause_check = QCheckBox("Auto-pause campaign immediately if phone disconnects")
        self.auto_pause_check.setChecked(True)
        sending_form.addRow(self.auto_pause_check)
        layout.addWidget(sending_box)

        # -- Contacts ------------------------------------------------------
        contacts_box = QGroupBox("Default Excel Import Mappings")
        contacts_form = QFormLayout(contacts_box)
        contacts_form.setSpacing(10)
        self.default_name_col_edit = QLineEdit()
        self.default_name_col_edit.setPlaceholderText("Name, Full Name, Contact")
        contacts_form.addRow("Default Name Column:", self.default_name_col_edit)
        
        self.default_phone_col_edit = QLineEdit()
        self.default_phone_col_edit.setPlaceholderText("Phone, Mobile, Number")
        contacts_form.addRow("Default Phone Column:", self.default_phone_col_edit)
        
        self.duplicate_handling_combo = QComboBox()
        self.duplicate_handling_combo.addItems(["Skip duplicate numbers", "Overwrite existing contact", "Allow duplicate numbers"])
        contacts_form.addRow("Duplicate Phone Handling:", self.duplicate_handling_combo)
        layout.addWidget(contacts_box)

        # -- Danger Zone ---------------------------------------------------
        db_box = QGroupBox("Database Maintenance")
        db_form = QFormLayout(db_box)
        db_form.setSpacing(10)
        self.clear_data_btn = QPushButton("⚠️  Reset / Clear Local Database")
        self.clear_data_btn.setStyleSheet("background-color: #450a0a; color: #fca5a5; font-weight: 600;")
        db_form.addRow("Danger Zone:", self.clear_data_btn)
        layout.addWidget(db_box)

        # Save Button Row
        row = QHBoxLayout()
        self.save_btn = QPushButton("💾  Save All Settings")
        self.save_btn.setStyleSheet("background-color: #6366f1; color: white; font-weight: 700; padding: 10px 24px;")
        row.addWidget(self.save_btn)
        row.addStretch()
        layout.addLayout(row)

        layout.addStretch()

        self.save_btn.clicked.connect(self._save)
        self.clear_data_btn.clicked.connect(self._clear_database)
        self.test_connection_btn.clicked.connect(self._test_connection)

        self.reload()

    def reload(self) -> None:
        cfg = settings_store.load()
        self.rate_spin.setValue(int(cfg.get("default_rate_limit_ms", 2000)))
        self.daily_limit_spin.setValue(int(cfg.get("default_daily_limit", 100)))
        self.auto_pause_check.setChecked(bool(cfg.get("auto_pause_on_disconnect", True)))
        self.default_name_col_edit.setText(cfg.get("default_name_column", "Name"))
        self.default_phone_col_edit.setText(cfg.get("default_phone_column", "Phone"))
        dup = cfg.get("duplicate_handling", "skip")
        idx = {"skip": 0, "overwrite": 1, "allow": 2}.get(dup, 0)
        self.duplicate_handling_combo.setCurrentIndex(idx)

        from app.repositories import devices_repo
        paired = devices_repo.list_all(paired_only=True)
        if paired:
            device = paired[0]
            status = "🟢 Connected" if self.devices_screen and self.devices_screen._connected else "⚪ Offline"
            self.connected_device_label.setText(f"{device['device_name']}  ({status})")
        else:
            self.connected_device_label.setText("No phone paired")

    def _save(self) -> None:
        dup_map = {0: "skip", 1: "overwrite", 2: "allow"}
        settings_store.save({
            "default_rate_limit_ms": self.rate_spin.value(),
            "default_daily_limit": self.daily_limit_spin.value(),
            "auto_pause_on_disconnect": self.auto_pause_check.isChecked(),
            "default_name_column": self.default_name_col_edit.text().strip(),
            "default_phone_column": self.default_phone_col_edit.text().strip(),
            "duplicate_handling": dup_map.get(self.duplicate_handling_combo.currentIndex(), "skip"),
        })
        QMessageBox.information(self, "Saved", "Settings saved successfully.")

    def _clear_database(self) -> None:
        confirm = QMessageBox.warning(
            self, "Reset Database",
            "This will delete all stored contacts, campaign history, and saved templates.\n\nAre you sure you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        close_connection()
        try:
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            run_migrations()
            QMessageBox.information(self, "Database Reset", "Database cleared and reinitialized.")
            self.reload()
        except Exception as exc:
            QMessageBox.critical(self, "Reset failed", f"Could not reset database: {exc}")

    def _test_connection(self) -> None:
        if self.devices_screen and self.devices_screen._connected:
            QMessageBox.information(self, "Connection Active", "Companion Android phone is actively connected!")
        else:
            QMessageBox.warning(self, "Not Connected", "No active connection to companion phone. Please go to Devices tab and connect.")
