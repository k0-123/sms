from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.network.client import NetworkClient
from app.network.discovery import DeviceDiscovery, DiscoveredDevice
from app.repositories import devices_repo
from app.repositories._util import new_id
from app.services import credential_store


class DevicesScreen(QWidget):
    """Discover, pair with, and manage the Android companion phone."""

    def __init__(self, network_client: NetworkClient, parent=None):
        super().__init__(parent)
        self.client = network_client
        self._connected = False
        self.discovery = DeviceDiscovery(self)
        self._discovered: dict[str, DiscoveredDevice] = {}
        self._pending_pair_device: DiscoveredDevice | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        header = QVBoxLayout()
        header.setSpacing(2)
        title = QLabel("Hardware Gateway Link")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;")
        subtitle = QLabel("DISCOVER & PAIR ANDROID COMPANION GATEWAY OVER LOCAL NETWORK")
        subtitle.setStyleSheet("font-size: 10px; color: #71717a; font-weight: 700; letter-spacing: 1px;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Status Badge Card
        self.status_card = QFrame()
        self.status_card.setStyleSheet("background-color: #0c0c0c; border: 1px solid #1f1f1f; border-radius: 8px; padding: 12px;")
        status_layout = QHBoxLayout(self.status_card)
        status_layout.setContentsMargins(14, 8, 14, 8)
        
        status_title = QLabel("LINK STATE:")
        status_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #71717a; letter-spacing: 0.8px;")
        self.status_label = QLabel("🔴 OFFLINE")
        self.status_label.setStyleSheet("font-weight: 800; color: #ef4444; font-size: 13px;")
        status_layout.addWidget(status_title)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addWidget(self.status_card)

        # Discovered Section
        disc_label = QLabel("Discovered Phones on Wi-Fi:")
        disc_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #e2e8f0; margin-top: 6px;")
        layout.addWidget(disc_label)

        self.discovered_list = QListWidget()
        self.discovered_list.setMinimumHeight(110)
        layout.addWidget(self.discovered_list)

        btn_row = QHBoxLayout()
        self.rescan_btn = QPushButton("[ 🔍 SCAN_NETWORK ]")
        self.pair_btn = QPushButton("[ 🔗 PAIR_SELECTED ]")
        self.pair_btn.setStyleSheet("background-color: #18181b; border: 1px solid #00e599; color: #00e599; font-weight: 700;")
        self.manual_pair_btn = QPushButton("[ 🌐 PAIR_VIA_IP ]")
        
        btn_row.addWidget(self.rescan_btn)
        btn_row.addWidget(self.pair_btn)
        btn_row.addWidget(self.manual_pair_btn)
        layout.addLayout(btn_row)

        # Paired Section
        paired_label = QLabel("PAIRED HARDWARE NODES:")
        paired_label.setStyleSheet("font-weight: 700; font-size: 11px; color: #71717a; margin-top: 10px; letter-spacing: 0.8px;")
        layout.addWidget(paired_label)

        self.paired_list = QListWidget()
        self.paired_list.setMinimumHeight(110)
        layout.addWidget(self.paired_list)

        row2 = QHBoxLayout()
        self.connect_btn = QPushButton("[ ⚡ CONNECT_LINK ]")
        self.connect_btn.setStyleSheet("background-color: #18181b; border: 1px solid #00e599; color: #00e599; font-weight: 700;")
        self.unpair_btn = QPushButton("[ ✕ UNPAIR_NODE ]")
        self.unpair_btn.setStyleSheet("background-color: #270909; border: 1px solid #7f1d1d; color: #fca5a5;")
        row2.addWidget(self.connect_btn)
        row2.addWidget(self.unpair_btn)
        layout.addLayout(row2)

        self.rescan_btn.clicked.connect(self._rescan)
        self.pair_btn.clicked.connect(self._pair_selected)
        self.manual_pair_btn.clicked.connect(self._pair_manual)
        self.connect_btn.clicked.connect(self._connect_selected)
        self.unpair_btn.clicked.connect(self._unpair_selected)

        self.discovery.device_found.connect(self._on_device_found)
        self.client.connected.connect(self._on_connected)
        self.client.disconnected.connect(self._on_disconnected)
        self.client.pair_response.connect(self._on_pair_response)

        self.refresh_paired()
        self._rescan()

    # -- discovery -----------------------------------------------------
    def _rescan(self) -> None:
        self.discovered_list.clear()
        self._discovered.clear()
        self.discovery.stop()
        self.discovery.start()

    def _on_device_found(self, device: DiscoveredDevice) -> None:
        self._discovered[device.name] = device
        label = f"📱 {device.device_name or device.name}  •  IP: {device.address}:{device.port}"
        item = QListWidgetItem(label)
        item.setData(1, device.name)
        self.discovered_list.addItem(item)

    # -- pairing ---------------------------------------------------------
    def _pair_manual(self) -> None:
        ip, ok = QInputDialog.getText(
            self, "Phone IP Address", "Enter your Phone's Wi-Fi IP address (e.g. 192.168.1.19):"
        )
        if not ok or not ip:
            return
        ip = ip.strip()
        code, ok = QInputDialog.getText(
            self, "Enter Pairing Code", "Enter the 6-digit code shown on the phone (e.g. 634681):"
        )
        if not ok or not code:
            return
        code = code.strip()
        device = DiscoveredDevice(
            name=f"Android Phone ({ip})",
            address=ip,
            port=8765,
            device_name="Android Phone",
        )
        self._pending_pair_device = device
        my_device_id = new_id()
        self._pending_pair_device.device_id = my_device_id
        self._pending_code = code
        self.client.connected.connect(self._send_pending_pair_request)
        self.client.connect_to(device.address, device.port)

    def _pair_selected(self) -> None:
        item = self.discovered_list.currentItem()
        if item is None:
            QMessageBox.information(self, "No device selected", "Select a discovered phone from the list first.")
            return
        device = self._discovered.get(item.data(1))
        if device is None:
            return

        code, ok = QInputDialog.getText(
            self, "Enter Pairing Code", "Enter the 6-digit code shown on the phone:"
        )
        if not ok or not code:
            return

        self._pending_pair_device = device
        my_device_id = new_id()
        self._pending_pair_device.device_id = self._pending_pair_device.device_id or my_device_id
        self.client.connect_to(device.address, device.port)
        self._pending_code = code
        self.client.connected.connect(self._send_pending_pair_request)

    def _send_pending_pair_request(self) -> None:
        self.client.connected.disconnect(self._send_pending_pair_request)
        if self._pending_pair_device is None:
            return
        self._my_id = new_id()
        self.client.send_pair_request(self._my_id, "Desktop App", self._pending_code)

    def _on_pair_response(self, accepted: bool, token: str, reason: str) -> None:
        device = self._pending_pair_device
        self._pending_pair_device = None
        if device is None:
            return
        if not accepted:
            QMessageBox.warning(
                self, "Pairing declined",
                reason or "Pairing was declined on the phone. Please try again."
            )
            return
        device_id = device.device_id or self._my_id
        credential_store.store_token(device_id, token)
        devices_repo.create(
            device_id, device.device_name or device.name, pairing_token_ref=device_id,
            last_ip=device.address,
        )
        QMessageBox.information(self, "Paired Successfully", f"Successfully paired with {device.device_name}!")
        self.refresh_paired()

    # -- connect / unpair --------------------------------------------------
    def _connect_selected(self) -> None:
        item = self.paired_list.currentItem()
        if item is None:
            if self.paired_list.count() > 0:
                item = self.paired_list.item(0)
            else:
                QMessageBox.warning(self, "No Device", "No paired devices found. Pair your phone first.")
                return
        device_id = item.data(1)
        device = devices_repo.get(device_id)
        if device is None or not device["last_ip"]:
            QMessageBox.warning(self, "Cannot connect", "This device has no known IP address. Rescan and re-pair.")
            return
        token = credential_store.get_token(device_id)
        if token is None:
            QMessageBox.warning(self, "Not paired", "No stored pairing token for this device. Please re-pair.")
            return
        self.client.connect_to(device["last_ip"], 8765)
        self._auth_device_id = device_id
        self._auth_token = token
        self.client.connected.connect(self._send_auth_once)

    def _send_auth_once(self) -> None:
        self.client.connected.disconnect(self._send_auth_once)
        self.client.send_auth(self._auth_device_id, self._auth_token)
        devices_repo.mark_connected(self._auth_device_id)

    def _unpair_selected(self) -> None:
        item = self.paired_list.currentItem()
        if item is None:
            return
        device_id = item.data(1)
        self.client.send_unpair(device_id)
        devices_repo.unpair(device_id)
        credential_store.delete_token(device_id)
        self.refresh_paired()

    def _on_connected(self) -> None:
        self._connected = True
        self.status_label.setText("🟢 Connected")
        self.status_label.setStyleSheet("font-weight: 700; color: #34d399; font-size: 14px;")

    def _on_disconnected(self, reason: str) -> None:
        self._connected = False
        self.status_label.setText("🔴 Disconnected")
        self.status_label.setStyleSheet("font-weight: 700; color: #f87171; font-size: 14px;")
        if reason:
            QMessageBox.warning(self, "Disconnected", reason)

    def refresh_paired(self) -> None:
        self.paired_list.clear()
        for device in devices_repo.list_all(paired_only=True):
            item = QListWidgetItem(f"📱 {device['device_name']}  •  Last IP: {device['last_ip'] or 'unknown'}")
            item.setData(1, device["id"])
            self.paired_list.addItem(item)
