from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

NAV_ITEMS = [
    ("[ DASHBOARD ]", "Dashboard"),
    ("[ CONTACTS ]", "Contacts"),
    ("[ NEW_CAMPAIGN ]", "New Campaign"),
    ("[ VOICE_CALL ]", "Voice Call"),
    ("[ TEMPLATES ]", "Templates"),
    ("[ HISTORY ]", "History"),
    ("[ DEVICES ]", "Devices"),
    ("[ SETTINGS ]", "Settings"),
]


class Sidebar(QWidget):
    navigated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(230)
        self.setObjectName("SidebarContainer")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 14)
        layout.setSpacing(10)

        # OPS_NAV Top Bar
        top_bar = QHBoxLayout()
        ops_title = QLabel("■  OPS_NAV")
        ops_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #a1a1aa; letter-spacing: 1px;")
        
        self.link_status = QLabel("LINK.OK 🟢")
        self.link_status.setStyleSheet("font-size: 10px; font-weight: 700; color: #00e599;")
        
        top_bar.addWidget(ops_title)
        top_bar.addStretch()
        top_bar.addWidget(self.link_status)
        layout.addLayout(top_bar)

        # Network Telemetry Box
        telemetry_box = QFrame()
        telemetry_box.setStyleSheet(
            "QFrame {"
            "  background-color: #0c0c0c;"
            "  border: 1px solid #1a1a1a;"
            "  border-radius: 6px;"
            "  padding: 10px;"
            "}"
        )
        t_layout = QVBoxLayout(telemetry_box)
        t_layout.setContentsMargins(6, 6, 6, 6)
        t_layout.setSpacing(3)

        net_header = QLabel("ACTIVE_NETWORK")
        net_header.setStyleSheet("font-size: 10px; color: #71717a; font-weight: 700; letter-spacing: 0.8px;")
        
        self.device_name_label = QLabel("Mobile Gateway")
        self.device_name_label.setStyleSheet("font-size: 14px; font-weight: 800; color: #ffffff;")
        
        cycle_row = QHBoxLayout()
        cycle_label = QLabel("CYCLE")
        cycle_label.setStyleSheet("font-size: 9px; color: #71717a;")
        cycle_val = QLabel("2026.09")
        cycle_val.setStyleSheet("font-size: 11px; font-weight: 700; color: #a1a1aa;")
        cycle_row.addWidget(cycle_label)
        cycle_row.addWidget(cycle_val)
        cycle_row.addStretch()

        t_layout.addWidget(net_header)
        t_layout.addWidget(self.device_name_label)
        t_layout.addLayout(cycle_row)
        layout.addWidget(telemetry_box)

        # Section Header
        ops_sec = QLabel("OPERATIONS")
        ops_sec.setStyleSheet("font-size: 10px; color: #52525b; font-weight: 700; letter-spacing: 1px; margin-top: 6px;")
        layout.addWidget(ops_sec)

        # Nav List
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("Sidebar")
        self.list_widget.setFocusPolicy(Qt.NoFocus)

        for display_name, key in NAV_ITEMS:
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, key)
            self.list_widget.addItem(item)

        self.list_widget.currentItemChanged.connect(self._on_item_changed)
        layout.addWidget(self.list_widget, stretch=1)

        self.list_widget.setCurrentRow(0)

    def _on_item_changed(self, current: QListWidgetItem, _prev) -> None:
        if current:
            key = current.data(Qt.UserRole)
            if key:
                self.navigated.emit(key)

    def set_connection_status(self, connected: bool, device_name: str = "") -> None:
        if connected:
            self.link_status.setText("LINK.OK 🟢")
            self.link_status.setStyleSheet("font-size: 10px; font-weight: 700; color: #00e599;")
            self.device_name_label.setText(device_name if device_name else "Phone Gateway")
        else:
            self.link_status.setText("OFFLINE 🔴")
            self.link_status.setStyleSheet("font-size: 10px; font-weight: 700; color: #ef4444;")
            self.device_name_label.setText("No Device Linked")
