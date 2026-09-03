"""Human-readable, non-blocking error/status toasts (PRD Section 29)."""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QWidget


class Toast(QLabel):
    """A small self-dismissing banner. Call show_message() to display text."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setStyleSheet(
            "background-color: #323232; color: white; padding: 10px; border-radius: 6px;"
        )
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, duration_ms: int = 4000) -> None:
        self.setText(text)
        self.adjustSize()
        parent_rect = self.parentWidget().rect()
        self.move(
            (parent_rect.width() - self.width()) // 2,
            parent_rect.height() - self.height() - 30,
        )
        self.show()
        self.raise_()
        self._timer.start(duration_ms)
