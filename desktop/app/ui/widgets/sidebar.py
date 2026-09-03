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
    ("👥  Contacts", "Contacts"),
    ("✈️  Send", "New Campaign"),
    ("📄  Templates", "Templates"),
    ("🕒  History", "History"),
    ("📱  Your phone", "Devices"),
    ("⚙️  Settings", "Settings"),
]


class Sidebar(QWidget):
    navigated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(230)
        self.setObjectName("SidebarContainer")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 18, 12, 16)
        layout.setSpacing(10)

        # QuickText Brand Header
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(8, 0, 8, 8)
        header_layout.setSpacing(3)

        brand_title = QLabel("QuickText")
        brand_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1e40af;")
        brand_sub = QLabel("Text messages from your PC")
        brand_sub.setStyleSheet("font-size: 11.5px; color: #64748b; font-weight: 500;")
        header_layout.addWidget(brand_title)
        header_layout.addWidget(brand_sub)
        layout.addWidget(header_widget)

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

        # Bottom Phone Status Card (Like in QuickText screenshot)
        self.phone_card = QFrame()
        self.phone_card.setStyleSheet(
            "QFrame {"
            "  background-color: #f8fafc;"
            "  border: 1px solid #e2e8f0;"
            "  border-radius: 8px;"
            "  padding: 10px;"
            "}"
        )
        phone_layout = QVBoxLayout(self.phone_card)
        phone_layout.setContentsMargins(4, 4, 4, 4)
        phone_layout.setSpacing(4)

        self.phone_status_dot = QLabel("🔴 Disconnected")
        self.phone_status_dot.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #dc2626;")
        self.phone_name_label = QLabel("Pair in 'Your phone'")
        self.phone_name_label.setStyleSheet("font-size: 11px; color: #64748b;")

        phone_layout.addWidget(self.phone_status_dot)
        phone_layout.addWidget(self.phone_name_label)
        layout.addWidget(self.phone_card)

        # App version
        version_label = QLabel("v1.4.1")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("font-size: 10px; color: #94a3b8;")
        layout.addWidget(version_label)

        self.list_widget.setCurrentRow(0)

    def _on_item_changed(self, current: QListWidgetItem, _prev) -> None:
        if current:
            key = current.data(Qt.UserRole)
            if key:
                self.navigated.emit(key)

    def set_connection_status(self, connected: bool, device_name: str = "") -> None:
        if connected:
            name_str = device_name if device_name else "Android Phone"
            self.phone_status_dot.setText("🟢 Connected")
            self.phone_status_dot.setStyleSheet("font-size: 11.5px; font-weight: 700; color: #16a34a;")
            self.phone_name_label.setText(name_str)
        else:
            self.phone_status_dot.setText("🔴 Disconnected")
            self.phone_status_dot.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #dc2626;")
            self.phone_name_label.setText("Tap 'Your phone' to pair")
