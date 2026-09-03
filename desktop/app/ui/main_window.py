from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from app.network.client import NetworkClient
from app.repositories import devices_repo
from app.ui.screens.campaign_wizard.wizard_screen import CampaignWizardScreen
from app.ui.screens.contacts_screen import ContactsScreen
from app.ui.screens.dashboard_screen import DashboardScreen
from app.ui.screens.devices_screen import DevicesScreen
from app.ui.screens.history_screen import HistoryScreen
from app.ui.screens.settings_screen import SettingsScreen
from app.ui.screens.templates_screen import TemplatesScreen
from app.ui.theme import APP_STYLESHEET
from app.ui.widgets.sidebar import NAV_ITEMS, Sidebar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMS Bridge — Mobile Gateway & Campaign Manager")
        self.resize(1100, 750)
        self.setMinimumSize(950, 650)
        self.setStyleSheet(APP_STYLESHEET)

        self.network_client = NetworkClient(self)

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar(central)
        layout.addWidget(self.sidebar)

        self.dashboard_screen = DashboardScreen()
        self.devices_screen = DevicesScreen(self.network_client)
        self.campaign_wizard_screen = CampaignWizardScreen(self.network_client)
        self.history_screen = HistoryScreen(self.campaign_wizard_screen.engine)
        self.settings_screen = SettingsScreen(self.devices_screen)

        self.stack = QStackedWidget(central)
        self.screens = {
            "Dashboard": self.dashboard_screen,
            "Contacts": ContactsScreen(),
            "New Campaign": self.campaign_wizard_screen,
            "Templates": TemplatesScreen(),
            "History": self.history_screen,
            "Devices": self.devices_screen,
            "Settings": self.settings_screen,
        }
        for _, key in NAV_ITEMS:
            self.stack.addWidget(self.screens[key])
        layout.addWidget(self.stack, stretch=1)

        self.sidebar.navigated.connect(self._navigate)
        self.dashboard_screen.request_navigation.connect(self._navigate_from_key)

        self.network_client.connected.connect(self._on_device_connected)
        self.network_client.disconnected.connect(self._on_device_disconnected)

        # Initial connection check
        self._check_initial_device_state()

    def _check_initial_device_state(self) -> None:
        paired = devices_repo.list_all(paired_only=True)
        if paired:
            device = paired[0]
            self.sidebar.set_connection_status(False, device["device_name"])
        else:
            self.sidebar.set_connection_status(False)

    def _on_device_connected(self) -> None:
        paired = devices_repo.list_all(paired_only=True)
        device_name = paired[0]["device_name"] if paired else "Phone"
        self.sidebar.set_connection_status(True, device_name)
        self.dashboard_screen.refresh()

    def _on_device_disconnected(self, _reason: str = "") -> None:
        self.sidebar.set_connection_status(False)
        self.dashboard_screen.refresh()

    def _navigate_from_key(self, key: str) -> None:
        for idx, (_, nav_key) in enumerate(NAV_ITEMS):
            if nav_key == key:
                self.sidebar.list_widget.setCurrentRow(idx)
                break
        self._navigate(key)

    def _navigate(self, screen_name: str) -> None:
        widget = self.screens.get(screen_name)
        if widget is None:
            return
        if screen_name == "Dashboard":
            self.dashboard_screen.refresh()
        elif screen_name == "History":
            self.history_screen.refresh()
        elif screen_name == "Settings":
            self.settings_screen.reload()
        elif screen_name == "New Campaign":
            self.campaign_wizard_screen.reset()
        elif screen_name == "Contacts":
            self.screens["Contacts"].refresh()
        self.stack.setCurrentWidget(widget)

    def closeEvent(self, event) -> None:
        self.devices_screen.discovery.stop()
        self.network_client.shutdown()
        super().closeEvent(event)
