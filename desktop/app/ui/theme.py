"""Industrial Terminal Ops / Cyber-Console Design Theme for SMS Bridge.
Inspired by mission-critical control rooms, telemetry dashboards, and minimalist monospace HUDs.
"""

APP_STYLESHEET = """
QMainWindow {
    background-color: #050505;
}

QWidget {
    font-family: 'Consolas', 'JetBrains Mono', 'Segoe UI', monospace, sans-serif;
    color: #e4e4e7;
    font-size: 12.5px;
    background-color: transparent;
}

/* === Sidebar Container & Terminal HUD === */
#SidebarContainer {
    background-color: #080808;
    border-right: 1px solid #1a1a1a;
}

#Sidebar {
    background-color: #080808;
    border: none;
    outline: none;
    padding: 6px 8px;
}

#Sidebar::item {
    padding: 10px 14px;
    margin: 3px 0px;
    border-radius: 6px;
    color: #71717a;
    font-size: 12.5px;
    font-weight: 600;
    letter-spacing: 0.5px;
    border: 1px solid transparent;
}

#Sidebar::item:hover {
    background-color: #121212;
    color: #ffffff;
    border: 1px solid #27272a;
}

#Sidebar::item:selected {
    background-color: #18181b;
    color: #00e599;
    font-weight: 700;
    border: 1px solid #27272a;
    border-left: 3px solid #00e599;
}

/* === Headers & Monospace Telemetry === */
.ScreenTitle {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
}

.ScreenSubtitle {
    font-size: 11px;
    color: #71717a;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
}

/* === Terminal Cards & Panels === */
.OpsCard {
    background-color: #0c0c0c;
    border: 1px solid #1f1f1f;
    border-radius: 8px;
    padding: 16px;
}

/* === Buttons === */
QPushButton {
    background-color: #0f0f0f;
    border: 1px solid #27272a;
    border-radius: 5px;
    padding: 7px 14px;
    color: #e4e4e7;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.3px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #1a1a1e;
    border-color: #3f3f46;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #000000;
    border-color: #00e599;
    color: #00e599;
}

QPushButton:disabled {
    background-color: #09090b;
    border-color: #18181b;
    color: #3f3f46;
}

/* Primary Ops Button */
.PrimaryBtn, QPushButton#PrimaryBtn {
    background-color: #18181b;
    border: 1px solid #00e599;
    color: #00e599;
    font-weight: 700;
}

.PrimaryBtn:hover, QPushButton#PrimaryBtn:hover {
    background-color: #00e599;
    color: #000000;
}

/* Success Button */
.SuccessBtn {
    background-color: #064e3b;
    border: 1px solid #10b981;
    color: #a7f3d0;
    font-weight: 700;
}

.SuccessBtn:hover {
    background-color: #10b981;
    color: #000000;
}

/* Danger / Kill Button */
.DangerBtn {
    background-color: #270909;
    border: 1px solid #7f1d1d;
    color: #fca5a5;
    font-weight: 600;
}

.DangerBtn:hover {
    background-color: #7f1d1d;
    color: #ffffff;
}

/* === Inputs, SpinBoxes & Combos - Terminal Prompt Style === */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
    background-color: #080808;
    border: 1px solid #222222;
    border-radius: 5px;
    padding: 7px 10px;
    color: #ffffff;
    font-size: 12.5px;
    font-weight: 500;
    selection-background-color: #00e599;
    selection-color: #000000;
}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #00e599;
    background-color: #0c0c0c;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #222222;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}

QComboBox QAbstractItemView {
    background-color: #0c0c0c;
    border: 1px solid #27272a;
    border-radius: 5px;
    selection-background-color: #18181b;
    selection-color: #00e599;
    padding: 4px;
    color: #ffffff;
}

/* === Tables & Queues === */
QTableWidget, QTableView, QListWidget, QListView {
    background-color: #080808;
    border: 1px solid #1a1a1a;
    border-radius: 6px;
    gridline-color: #141414;
    outline: none;
    color: #e4e4e7;
}

QTableWidget::item, QListWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #121212;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #141414;
    color: #ffffff;
    border-left: 2px solid #00e599;
}

QHeaderView::section {
    background-color: #0d0d0d;
    color: #71717a;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #1f1f1f;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* === Group Boxes === */
QGroupBox {
    background-color: #0a0a0a;
    border: 1px solid #1f1f1f;
    border-radius: 8px;
    margin-top: 22px;
    padding-top: 18px;
    padding-bottom: 12px;
    padding-left: 12px;
    padding-right: 12px;
    font-weight: 700;
    color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: 5px;
    color: #a1a1aa;
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* === Progress Bars === */
QProgressBar {
    background-color: #0d0d0d;
    border: 1px solid #222222;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
    height: 16px;
}

QProgressBar::chunk {
    background-color: #00e599;
    border-radius: 3px;
}

/* === Tabs === */
QTabWidget::pane {
    border: 1px solid #1f1f1f;
    border-radius: 6px;
    background-color: #080808;
    top: -1px;
}

QTabBar::tab {
    background-color: #0d0d0d;
    border: 1px solid #1f1f1f;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    padding: 7px 16px;
    color: #71717a;
    margin-right: 3px;
    font-weight: 600;
    font-size: 11.5px;
    text-transform: uppercase;
}

QTabBar::tab:selected {
    background-color: #080808;
    color: #00e599;
    font-weight: 700;
    border-bottom: 2px solid #00e599;
}

/* === Scrollbars === */
QScrollBar:vertical {
    background-color: #050505;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #27272a;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3f3f46;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
