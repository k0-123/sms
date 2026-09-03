from PySide6.QtWidgets import (
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
        layout.addWidget(QLabel("DEVICES"))

        self.status_label = QLabel("\U0001F534 Not connected")
        layout.addWidget(self.status_label)

        layout.addWidget(QLabel("Discovered phones on your Wi-Fi:"))
        self.discovered_list = QListWidget()
        layout.addWidget(self.discovered_list)

        row = QHBoxLayout()
        self.rescan_btn = QPushButton("Rescan")
        self.pair_btn = QPushButton("Pair Selected")
        row.addWidget(self.rescan_btn)
        row.addWidget(self.pair_btn)
        layout.addLayout(row)

        layout.addWidget(QLabel("Paired devices:"))
        self.paired_list = QListWidget()
        layout.addWidget(self.paired_list)

        row2 = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.unpair_btn = QPushButton("Unpair")
        row2.addWidget(self.connect_btn)
        row2.addWidget(self.unpair_btn)
        layout.addLayout(row2)

        self.rescan_btn.clicked.connect(self._rescan)
        self.pair_btn.clicked.connect(self._pair_selected)
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
        label = f"{device.device_name or device.name} ({device.address}:{device.port})"
        item = QListWidgetItem(label)
        item.setData(1, device.name)
        self.discovered_list.addItem(item)

    # -- pairing ---------------------------------------------------------
    def _pair_selected(self) -> None:
        item = self.discovered_list.currentItem()
        if item is None:
            QMessageBox.information(self, "No device selected", "Select a discovered phone first.")
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
        # send_pair_request is issued once `connected` fires; store the code for that handler.
        self._pending_code = code
        self.client.connected.connect(self._send_pending_pair_request)

    def _send_pending_pair_request(self) -> None:
        self.client.connected.disconnect(self._send_pending_pair_request)
        if self._pending_pair_device is None:
            return
        self._my_id = new_id()
        self.client.send_pair_request(self._my_id, "My PC", self._pending_code)

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
        QMessageBox.information(self, "Paired", f"Successfully paired with {device.device_name}.")
        self.refresh_paired()

    # -- connect / unpair --------------------------------------------------
    def _connect_selected(self) -> None:
        item = self.paired_list.currentItem()
        if item is None:
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
        self.status_label.setText("\U0001F7E2 Connected")

    def _on_disconnected(self, reason: str) -> None:
        self._connected = False
        self.status_label.setText("\U0001F534 Phone Disconnected")
        if reason:
            QMessageBox.warning(self, "Disconnected", reason)

    def refresh_paired(self) -> None:
        self.paired_list.clear()
        for device in devices_repo.list_all(paired_only=True):
            item = QListWidgetItem(f"{device['device_name']} ({device['last_ip'] or 'unknown IP'})")
            item.setData(1, device["id"])
            self.paired_list.addItem(item)
