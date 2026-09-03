from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

NAV_ITEMS = [
    ("📊  Dashboard", "Dashboard"),
    ("👥  Contacts", "Contacts"),
    ("🚀  New Campaign", "New Campaign"),
    ("📝  Templates", "Templates"),
    ("📜  History", "History"),
    ("📱  Devices", "Devices"),
    ("⚙️  Settings", "Settings"),
]


class Sidebar(QWidget):
    navigated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setObjectName("SidebarContainer")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # App Brand Header
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #0f172a; padding: 18px 12px 10px 12px;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        brand_title = QLabel("⚡ SMS Bridge")
        brand_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #ffffff;")
        brand_sub = QLabel("Local Mobile Gateway")
        brand_sub.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 500;")
        header_layout.addWidget(brand_title)
        header_layout.addWidget(brand_sub)
        layout.addWidget(header_widget)

        # Nav List
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("Sidebar")
        self.list_widget.setFocusPolicy(Qt.NoFocus)

        self._key_map: dict[str, str] = {}
        for display_name, key in NAV_ITEMS:
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, key)
            self.list_widget.addItem(item)
            self._key_map[display_name] = key

        self.list_widget.currentItemChanged.connect(self._on_item_changed)
        layout.addWidget(self.list_widget, stretch=1)

        # Connection status footer pill
        self.footer_badge = QLabel("🔴 Offline")
        self.footer_badge.setStyleSheet(
            "background-color: #1e293b; color: #94a3b8; border-radius: 8px; "
            "padding: 8px 12px; margin: 8px 12px 16px 12px; font-size: 11px; font-weight: 600;"
        )
        layout.addWidget(self.footer_badge)

        self.list_widget.setCurrentRow(0)

    def _on_item_changed(self, current: QListWidgetItem, _prev) -> None:
        if current:
            key = current.data(Qt.UserRole)
            if key:
                self.navigated.emit(key)

    def set_connection_status(self, connected: bool, device_name: str = "") -> None:
        if connected:
            name_str = f" ({device_name})" if device_name else ""
            self.footer_badge.setText(f"🟢 Phone Connected{name_str}")
            self.footer_badge.setStyleSheet(
                "background-color: #064e3b; color: #6ee7b7; border-radius: 8px; "
                "padding: 8px 12px; margin: 8px 12px 16px 12px; font-size: 11px; font-weight: 600;"
            )
        else:
            self.footer_badge.setText("🔴 Phone Disconnected")
            self.footer_badge.setStyleSheet(
                "background-color: #450a0a; color: #fca5a5; border-radius: 8px; "
                "padding: 8px 12px; margin: 8px 12px 16px 12px; font-size: 11px; font-weight: 600;"
            )
