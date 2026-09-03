import os

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
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
        layout.addWidget(QLabel("SETTINGS"))

        # -- Phone ------------------------------------------------------
        phone_box = QGroupBox("Phone")
        phone_form = QFormLayout(phone_box)
        self.connected_device_label = QLabel()
        phone_form.addRow("Connected device:", self.connected_device_label)
        self.test_connection_btn = QPushButton("Test Connection")
        phone_form.addRow(self.test_connection_btn)
        layout.addWidget(phone_box)

        # -- Sending -------------------------------------------------------
        sending_box = QGroupBox("Sending")
        sending_form = QFormLayout(sending_box)
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(500, 60000)
        self.rate_spin.setSuffix(" ms")
        sending_form.addRow("Default sending interval:", self.rate_spin)
        self.daily_limit_spin = QSpinBox()
        self.daily_limit_spin.setRange(1, 2000)
        sending_form.addRow("Default daily SMS limit:", self.daily_limit_spin)
        self.auto_pause_check = QCheckBox("Auto-pause campaign when phone disconnects")
        sending_form.addRow(self.auto_pause_check)
        layout.addWidget(sending_box)

        # -- Contacts ------------------------------------------------------
        contacts_box = QGroupBox("Contacts")
        contacts_form = QFormLayout(contacts_box)
        self.default_name_col_edit = QLineEdit()
        contacts_form.addRow("Default name column:", self.default_name_col_edit)
        self.default_phone_col_edit = QLineEdit()
        contacts_form.addRow("Default phone column:", self.default_phone_col_edit)
        self.duplicate_handling_combo = QComboBox()
        self.duplicate_handling_combo.addItems(["flag", "skip"])
        contacts_form.addRow("Duplicate handling:", self.duplicate_handling_combo)
        layout.addWidget(contacts_box)

        # -- Storage -------------------------------------------------------
        storage_box = QGroupBox("Storage")
        storage_form = QFormLayout(storage_box)
        storage_form.addRow("Database location:", QLabel(DB_PATH))
        self.delete_data_btn = QPushButton("Delete Local Data...")
        storage_form.addRow(self.delete_data_btn)
        layout.addWidget(storage_box)

        self.save_btn = QPushButton("Save Settings")
        layout.addWidget(self.save_btn)
        layout.addStretch()

        self.save_btn.clicked.connect(self._save)
        self.test_connection_btn.clicked.connect(self._test_connection)
        self.delete_data_btn.clicked.connect(self._delete_local_data)

        self.reload()

    def reload(self) -> None:
        s = settings_store.load()
        self.rate_spin.setValue(s["default_rate_limit_ms"])
        self.daily_limit_spin.setValue(s["default_daily_limit"])
        self.auto_pause_check.setChecked(s["auto_pause_on_disconnect"])
        self.default_name_col_edit.setText(s["default_name_column"])
        self.default_phone_col_edit.setText(s["default_phone_column"])
        self.duplicate_handling_combo.setCurrentText(s["duplicate_handling"])

        if self.devices_screen is not None:
            from app.repositories import devices_repo

            paired = devices_repo.list_all(paired_only=True)
            self.connected_device_label.setText(paired[0]["device_name"] if paired else "No phone paired")

    def _save(self) -> None:
        settings_store.save(
            {
                "default_rate_limit_ms": self.rate_spin.value(),
                "default_daily_limit": self.daily_limit_spin.value(),
                "auto_pause_on_disconnect": self.auto_pause_check.isChecked(),
                "default_name_column": self.default_name_col_edit.text(),
                "default_phone_column": self.default_phone_col_edit.text(),
                "duplicate_handling": self.duplicate_handling_combo.currentText(),
            }
        )
        QMessageBox.information(self, "Saved", "Settings saved.")

    def _test_connection(self) -> None:
        if self.devices_screen is None:
            return
        connected = getattr(self.devices_screen, "_connected", False)
        if connected:
            QMessageBox.information(self, "Connection OK", "Phone is connected.")
        else:
            QMessageBox.warning(
                self, "No phone connected",
                "No phone connected.\n\nPlease connect your Android phone before starting the campaign."
            )

    def _delete_local_data(self) -> None:
        confirm = QMessageBox.question(
            self, "Delete all local data?",
            "This will permanently delete all contacts, campaigns, and history stored on this "
            "computer. This cannot be undone. Continue?",
        )
        if confirm != QMessageBox.Yes:
            return
        close_connection()
        try:
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            for ext in ("-wal", "-shm"):
                p = DB_PATH + ext
                if os.path.exists(p):
                    os.remove(p)
        except OSError as exc:
            QMessageBox.critical(self, "Could not delete data", str(exc))
            return
        run_migrations()
        QMessageBox.information(self, "Deleted", "All local data has been deleted.")
