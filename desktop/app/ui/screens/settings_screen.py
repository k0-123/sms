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

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #050505; }")

        container = QWidget()
        container.setStyleSheet("background-color: #050505;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 22, 32, 32)
        layout.setSpacing(18)

        # Header Title & Subtitle
        header = QVBoxLayout()
        header.setSpacing(2)
        title = QLabel("System Configuration")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;")
        subtitle = QLabel("RADIO THROTTLE LIMITS • EXCEL INGESTION PRESETS • LOCAL DB CONTROLS")
        subtitle.setStyleSheet("font-size: 10px; color: #71717a; font-weight: 700; letter-spacing: 1px;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Helper to create a dark card section
        def make_section(title_text: str) -> tuple[QFrame, QVBoxLayout]:
            card = QFrame()
            card.setStyleSheet(
                "QFrame {"
                "  background-color: #0c0c0c;"
                "  border: 1px solid #1f1f1f;"
                "  border-radius: 8px;"
                "  padding: 14px;"
                "}"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 14, 18, 14)
            card_layout.setSpacing(12)

            sec_title = QLabel(title_text)
            sec_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #a1a1aa; letter-spacing: 0.8px;")
            card_layout.addWidget(sec_title)
            return card, card_layout

        # High-contrast readable input styling
        input_style = (
            "background-color: #080808; color: #ffffff; border: 1px solid #27272a; "
            "border-radius: 5px; padding: 7px 12px; font-size: 12.5px; font-weight: 600; min-height: 20px;"
        )

        # 1. Phone Gateway Section
        phone_card, phone_layout = make_section("HARDWARE GATEWAY LINK")
        phone_form = QFormLayout()
        phone_form.setSpacing(12)
        phone_form.setLabelAlignment(Qt.AlignLeft)

        self.connected_device_label = QLabel("No phone paired")
        self.connected_device_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #00e599;")
        phone_form.addRow("Paired Companion Device:", self.connected_device_label)

        self.test_connection_btn = QPushButton("[ 📡 TEST_LINK_PROBE ]")
        self.test_connection_btn.setFixedWidth(220)
        self.test_connection_btn.setStyleSheet(
            "background-color: #18181b; color: #e4e4e7; border: 1px solid #27272a; "
            "border-radius: 5px; padding: 7px 14px; font-weight: 600;"
        )
        phone_form.addRow("", self.test_connection_btn)
        phone_layout.addLayout(phone_form)
        layout.addWidget(phone_card)

        # 2. Transmission Limits Section
        sending_card, sending_layout = make_section("SMS TRANSMISSION & THROTTLE LIMITS")
        sending_form = QFormLayout()
        sending_form.setSpacing(12)
        sending_form.setLabelAlignment(Qt.AlignLeft)

        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(500, 60000)
        self.rate_spin.setSingleStep(500)
        self.rate_spin.setSuffix(" ms between packets")
        self.rate_spin.setStyleSheet(input_style)
        self.rate_spin.setFixedWidth(300)
        sending_form.addRow("Default Sending Interval:", self.rate_spin)

        self.daily_limit_spin = QSpinBox()
        self.daily_limit_spin.setRange(1, 5000)
        self.daily_limit_spin.setSuffix(" msgs / day quota")
        self.daily_limit_spin.setStyleSheet(input_style)
        self.daily_limit_spin.setFixedWidth(300)
        sending_form.addRow("Daily Limit (Carrier Safe):", self.daily_limit_spin)

        self.auto_pause_check = QCheckBox("Auto-pause campaign immediately if phone disconnects")
        self.auto_pause_check.setStyleSheet("color: #a1a1aa; font-size: 12.5px; font-weight: 500;")
        self.auto_pause_check.setChecked(True)
        sending_form.addRow("", self.auto_pause_check)
        sending_layout.addLayout(sending_form)
        layout.addWidget(sending_card)

        # 3. Excel Import Section
        contacts_card, contacts_layout = make_section("DATASET INGESTION PRESETS")
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
        db_card, db_layout = make_section("PERSISTENCE & STORAGE MAINTENANCE")
        db_form = QFormLayout()
        db_form.setSpacing(12)
        db_form.setLabelAlignment(Qt.AlignLeft)

        self.clear_data_btn = QPushButton("[ ⚠️ FLUSH_LOCAL_DATABASE ]")
        self.clear_data_btn.setFixedWidth(260)
        self.clear_data_btn.setStyleSheet(
            "background-color: #270909; color: #fca5a5; border: 1px solid #7f1d1d; "
            "border-radius: 5px; padding: 7px 14px; font-weight: 700;"
        )
        db_form.addRow("Danger Zone:", self.clear_data_btn)
        db_layout.addLayout(db_form)
        layout.addWidget(db_card)

        # Save Button Row
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("[ 💾 COMMIT_CONFIGURATION ]")
        self.save_btn.setStyleSheet(
            "background-color: #18181b; color: #00e599; font-weight: 700; font-size: 13px; "
            "border: 1px solid #00e599; border-radius: 5px; padding: 9px 24px;"
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
            self.connected_device_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #34d399;")
        else:
            self.connected_device_label.setText("No phone paired (Pair in 'Devices' tab)")
            self.connected_device_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #f87171;")

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
            QMessageBox.warning(self, "Not Connected", "No active connection to companion phone. Please go to 'Devices' tab and connect.")
