import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for clean view on any screen resolution
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f8fafc; }")
        
        container = QWidget()
        container.setStyleSheet("background-color: #f8fafc;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(36, 28, 36, 36)
        layout.setSpacing(20)

        # Header Title & Subtitle
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #0f172a;")
        subtitle = QLabel("Configure transmission intervals, default Excel column mappings, and app preferences.")
        subtitle.setStyleSheet("font-size: 13.5px; color: #64748b;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Section Helper Card Function
        def make_section(title_text: str) -> tuple[QFrame, QVBoxLayout]:
            card = QFrame()
            card.setStyleSheet(
                "QFrame {"
                "  background-color: #ffffff;"
                "  border: 1px solid #e2e8f0;"
                "  border-radius: 10px;"
                "  padding: 16px;"
                "}"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 16, 20, 16)
            card_layout.setSpacing(12)

            sec_title = QLabel(title_text)
            sec_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")
            card_layout.addWidget(sec_title)
            return card, card_layout

        # Input styling for perfect visibility
        input_style = (
            "background-color: #ffffff; color: #0f172a; border: 1.5px solid #cbd5e1; "
            "border-radius: 6px; padding: 8px 12px; font-size: 13px; font-weight: 600; min-height: 22px;"
        )

        # 1. Phone Gateway Section
        phone_card, phone_layout = make_section("📱 Phone Gateway Connection")
        phone_form = QFormLayout()
        phone_form.setSpacing(12)
        phone_form.setLabelAlignment(Qt.AlignLeft)

        self.connected_device_label = QLabel("No phone paired")
        self.connected_device_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #2563eb;")
        phone_form.addRow("Paired Companion Device:", self.connected_device_label)

        self.test_connection_btn = QPushButton("📡  Test Connection to Phone")
        self.test_connection_btn.setFixedWidth(220)
        self.test_connection_btn.setStyleSheet(
            "background-color: #f1f5f9; color: #1e293b; border: 1px solid #cbd5e1; "
            "border-radius: 6px; padding: 8px 16px; font-weight: 600;"
        )
        phone_form.addRow("", self.test_connection_btn)
        phone_layout.addLayout(phone_form)
        layout.addWidget(phone_card)

        # 2. Transmission Limits Section
        sending_card, sending_layout = make_section("⚡ SMS Transmission & Rate Limits")
        sending_form = QFormLayout()
        sending_form.setSpacing(12)
        sending_form.setLabelAlignment(Qt.AlignLeft)

        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(500, 60000)
        self.rate_spin.setSingleStep(500)
        self.rate_spin.setSuffix(" ms between messages")
        self.rate_spin.setStyleSheet(input_style)
        self.rate_spin.setFixedWidth(300)
        sending_form.addRow("Default Sending Interval:", self.rate_spin)

        self.daily_limit_spin = QSpinBox()
        self.daily_limit_spin.setRange(1, 5000)
        self.daily_limit_spin.setSuffix(" messages / day")
        self.daily_limit_spin.setStyleSheet(input_style)
        self.daily_limit_spin.setFixedWidth(300)
        sending_form.addRow("Daily SMS Limit (Carrier Safe):", self.daily_limit_spin)

        self.auto_pause_check = QCheckBox("Auto-pause campaign immediately if phone disconnects")
        self.auto_pause_check.setStyleSheet("color: #334155; font-size: 13px; font-weight: 500;")
        self.auto_pause_check.setChecked(True)
        sending_form.addRow("", self.auto_pause_check)
        sending_layout.addLayout(sending_form)
        layout.addWidget(sending_card)

        # 3. Excel Import Section
        contacts_card, contacts_layout = make_section("📋 Default Excel Import Mappings")
        contacts_form = QFormLayout()
        contacts_form.setSpacing(12)
        contacts_form.setLabelAlignment(Qt.AlignLeft)

        self.default_name_col_edit = QLineEdit()
        self.default_name_col_edit.setPlaceholderText("Name, Full Name, Contact")
        self.default_name_col_edit.setStyleSheet(input_style)
        self.default_name_col_edit.setFixedWidth(300)
        contacts_form.addRow("Default Name Column:", self.default_name_col_edit)

        self.default_phone_col_edit = QLineEdit()
        self.default_phone_col_edit.setPlaceholderText("Phone, Mobile, Number")
        self.default_phone_col_edit.setStyleSheet(input_style)
        self.default_phone_col_edit.setFixedWidth(300)
        contacts_form.addRow("Default Phone Column:", self.default_phone_col_edit)

        self.duplicate_handling_combo = QComboBox()
        self.duplicate_handling_combo.addItems(["Skip duplicate numbers", "Overwrite existing contact", "Allow duplicate numbers"])
        self.duplicate_handling_combo.setStyleSheet(input_style)
        self.duplicate_handling_combo.setFixedWidth(300)
        contacts_form.addRow("Duplicate Phone Handling:", self.duplicate_handling_combo)
        contacts_layout.addLayout(contacts_form)
        layout.addWidget(contacts_card)

        # 4. Database Maintenance Section
        db_card, db_layout = make_section("🗑️ Database Maintenance")
        db_form = QFormLayout()
        db_form.setSpacing(12)
        db_form.setLabelAlignment(Qt.AlignLeft)

        self.clear_data_btn = QPushButton("⚠️  Reset / Clear Local Database")
        self.clear_data_btn.setFixedWidth(260)
        self.clear_data_btn.setStyleSheet(
            "background-color: #fef2f2; color: #dc2626; border: 1.5px solid #fca5a5; "
            "border-radius: 6px; padding: 8px 16px; font-weight: 700;"
        )
        db_form.addRow("Danger Zone:", self.clear_data_btn)
        db_layout.addLayout(db_form)
        layout.addWidget(db_card)

        # Save Button Row
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("💾  Save All Settings")
        self.save_btn.setStyleSheet(
            "background-color: #1d4ed8; color: #ffffff; font-weight: 700; font-size: 14px; "
            "border: 1px solid #1e40af; border-radius: 6px; padding: 10px 28px;"
        )
        self.save_btn.setCursor(Qt.PointingHandCursor)
        btn_row.addWidget(self.save_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Connect signals
        self.save_btn.clicked.connect(self._save)
        self.clear_data_btn.clicked.connect(self._clear_database)
        self.test_connection_btn.clicked.connect(self._test_connection)

        self.reload()

    def reload(self) -> None:
        cfg = settings_store.load()
        self.rate_spin.setValue(int(cfg.get("default_rate_limit_ms", 2000)))
        self.daily_limit_spin.setValue(int(cfg.get("default_daily_limit", 100)))
        self.auto_pause_check.setChecked(bool(cfg.get("auto_pause_on_disconnect", True)))
        self.default_name_col_edit.setText(str(cfg.get("default_name_column", "Name")))
        self.default_phone_col_edit.setText(str(cfg.get("default_phone_column", "Phone")))
        dup = cfg.get("duplicate_handling", "skip")
        idx = {"skip": 0, "overwrite": 1, "allow": 2}.get(dup, 0)
        self.duplicate_handling_combo.setCurrentIndex(idx)

        from app.repositories import devices_repo
        paired = devices_repo.list_all(paired_only=True)
        if paired:
            device = paired[0]
            status = "🟢 Connected" if self.devices_screen and self.devices_screen._connected else "⚪ Paired (Offline)"
            self.connected_device_label.setText(f"{device['device_name']}  ({status})")
            self.connected_device_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #16a34a;")
        else:
            self.connected_device_label.setText("No phone paired (Pair in 'Your phone' tab)")
            self.connected_device_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #dc2626;")

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
        QMessageBox.information(self, "Saved", "✅ All settings saved successfully!")

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
            QMessageBox.warning(self, "Not Connected", "No active connection to companion phone. Please go to 'Your phone' tab and connect.")
