"""Sleek Dark Theme with Crystal-Clear High-Contrast Inputs for SMS Bridge."""

APP_STYLESHEET = """
QMainWindow {
    background-color: #0f172a;
}

QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
    color: #f8fafc;
    font-size: 13px;
    background-color: transparent;
}

/* === Sidebar Styling === */
#SidebarContainer {
    background-color: #0f172a;
    border-right: 1px solid #1e293b;
}

#Sidebar {
    background-color: #0f172a;
    border: none;
    outline: none;
    padding: 8px 10px;
}

#Sidebar::item {
    padding: 11px 16px;
    margin: 4px 0px;
    border-radius: 8px;
    color: #94a3b8;
    font-size: 13.5px;
    font-weight: 500;
}

#Sidebar::item:hover {
    background-color: #1e293b;
    color: #ffffff;
}

#Sidebar::item:selected {
    background-color: #312e81;
    color: #c7d2fe;
    font-weight: 700;
    border-left: 3px solid #818cf8;
}

/* === Headers & Typography === */
.ScreenTitle {
    font-size: 24px;
    font-weight: 800;
    color: #ffffff;
}

.ScreenSubtitle {
    font-size: 13px;
    color: #94a3b8;
    margin-bottom: 12px;
}

/* === Cards / Panels === */
.DarkCard {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 18px;
}

/* === Action Buttons === */
QPushButton {
    background-color: #1e293b;
    border: 1px solid #475569;
    border-radius: 7px;
    padding: 8px 16px;
    color: #f8fafc;
    font-weight: 600;
    font-size: 13px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #64748b;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #0f172a;
}

QPushButton:disabled {
    background-color: #1e293b;
    border-color: #1e293b;
    color: #475569;
}

/* Primary Button */
.PrimaryBtn, QPushButton#PrimaryBtn {
    background-color: #6366f1;
    border: 1px solid #4f46e5;
    color: #ffffff;
    font-weight: 700;
}

.PrimaryBtn:hover, QPushButton#PrimaryBtn:hover {
    background-color: #4f46e5;
}

/* Success Button */
.SuccessBtn {
    background-color: #059669;
    border: 1px solid #047857;
    color: #ffffff;
    font-weight: 700;
}

.SuccessBtn:hover {
    background-color: #047857;
}

/* Danger Button */
.DangerBtn {
    background-color: #450a0a;
    border: 1px solid #991b1b;
    color: #fca5a5;
    font-weight: 600;
}

.DangerBtn:hover {
    background-color: #7f1d1d;
}

/* === Inputs, SpinBoxes & Combos - High-Contrast Visible Styling === */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
    background-color: #0b1329;
    border: 1.5px solid #475569;
    border-radius: 7px;
    padding: 8px 12px;
    color: #ffffff;
    font-size: 13.5px;
    font-weight: 600;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1.5px solid #818cf8;
    background-color: #0f172a;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid #475569;
    border-top-right-radius: 7px;
    border-bottom-right-radius: 7px;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    border: 1px solid #475569;
    border-radius: 7px;
    selection-background-color: #312e81;
    selection-color: #c7d2fe;
    padding: 4px;
    color: #ffffff;
}

/* === Tables & Lists === */
QTableWidget, QTableView, QListWidget, QListView {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    gridline-color: #1e293b;
    outline: none;
    color: #f8fafc;
}

QTableWidget::item, QListWidget::item {
    padding: 9px 12px;
    border-bottom: 1px solid #1e293b;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #312e81;
    color: #ffffff;
    font-weight: 600;
}

QHeaderView::section {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 9px 12px;
    border: none;
    border-bottom: 1px solid #334155;
    font-weight: 700;
    font-size: 12px;
    text-transform: uppercase;
}

/* === Group Boxes === */
QGroupBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    margin-top: 24px;
    padding-top: 20px;
    padding-bottom: 14px;
    padding-left: 14px;
    padding-right: 14px;
    font-weight: 700;
    color: #f8fafc;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 6px;
    color: #818cf8;
    font-size: 13.5px;
    font-weight: 700;
}

/* === Progress Bars === */
QProgressBar {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 7px;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #6366f1;
    border-radius: 6px;
}

/* === Tabs === */
QTabWidget::pane {
    border: 1px solid #334155;
    border-radius: 8px;
    background-color: #0f172a;
    top: -1px;
}

QTabBar::tab {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-bottom: none;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
    padding: 8px 18px;
    color: #94a3b8;
    margin-right: 4px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #0f172a;
    color: #818cf8;
    font-weight: 700;
    border-bottom: 2px solid #6366f1;
}

/* === Scrollbars === */
QScrollBar:vertical {
    background-color: #0f172a;
    width: 9px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #475569;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #64748b;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
