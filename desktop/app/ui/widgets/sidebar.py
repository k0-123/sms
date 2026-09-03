from PySide6.QtCore import Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

NAV_ITEMS = [
    "Dashboard",
    "Contacts",
    "New Campaign",
    "Templates",
    "History",
    "Devices",
    "Settings",
]


class Sidebar(QListWidget):
    navigated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(180)
        for label in NAV_ITEMS:
            QListWidgetItem(label, self)
        self.currentTextChanged.connect(self.navigated.emit)
        self.setCurrentRow(0)
