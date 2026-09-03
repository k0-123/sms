"""mDNS discovery of Android companion phones advertising _smsbridge._tcp.local."""
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import QObject, Signal
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

SERVICE_TYPE = "_smsbridge._tcp.local."


@dataclass
class DiscoveredDevice:
    name: str
    address: str
    port: int
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    pairing_required: bool = True


class _Listener(ServiceListener):
    def __init__(self, on_add, on_remove):
        self._on_add = on_add
        self._on_remove = on_remove

    def add_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        info = zc.get_service_info(service_type, name)
        if info is None or not info.addresses:
            return
        address = ".".join(str(b) for b in info.addresses[0])
        txt = {
            k.decode(): v.decode() if isinstance(v, bytes) else v
            for k, v in (info.properties or {}).items()
        }
        device = DiscoveredDevice(
            name=name,
            address=address,
            port=info.port or 8765,
            device_id=txt.get("deviceId"),
            device_name=txt.get("deviceName", name),
            pairing_required=txt.get("pairingRequired", "true") == "true",
        )
        self._on_add(device)

    def remove_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        self._on_remove(name)

    def update_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        self.add_service(zc, service_type, name)


class DeviceDiscovery(QObject):
    device_found = Signal(object)  # DiscoveredDevice
    device_lost = Signal(str)  # service name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._zeroconf: Optional[Zeroconf] = None
        self._browser: Optional[ServiceBrowser] = None

    def start(self) -> None:
        if self._zeroconf is not None:
            return
        self._zeroconf = Zeroconf()
        listener = _Listener(
            on_add=lambda d: self.device_found.emit(d),
            on_remove=lambda name: self.device_lost.emit(name),
        )
        self._browser = ServiceBrowser(self._zeroconf, SERVICE_TYPE, listener)

    def stop(self) -> None:
        if self._zeroconf is not None:
            self._zeroconf.close()
            self._zeroconf = None
            self._browser = None
