"""QuickText Clean Modern Light Theme & Design System."""

APP_STYLESHEET = """
QMainWindow {
    background-color: #f8fafc;
}

QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
    color: #1e293b;
    font-size: 13px;
    background-color: transparent;
}

/* === Main Window & Content Surface === */
QStackedWidget {
    background-color: #f8fafc;
}

/* === Sidebar Styling === */
#SidebarContainer {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
}

#Sidebar {
    background-color: #ffffff;
    border: none;
    outline: none;
    padding: 8px 12px;
}

#Sidebar::item {
    padding: 10px 14px;
    margin: 3px 0px;
    border-radius: 8px;
    color: #475569;
    font-size: 13.5px;
    font-weight: 500;
}

#Sidebar::item:hover {
    background-color: #f1f5f9;
    color: #0f172a;
}

#Sidebar::item:selected {
    background-color: #e0f2fe;
    color: #0284c7;
    font-weight: 600;
}

/* === Headers & Typography === */
.ScreenTitle {
    font-size: 24px;
    font-weight: 700;
    color: #0f172a;
}

.ScreenSubtitle {
    font-size: 13px;
    color: #64748b;
    margin-bottom: 12px;
}

/* === White Cards / Surfaces === */
.WhiteCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px;
}

/* === Action Buttons (QuickText Style) === */
QPushButton {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 15px;
    color: #334155;
    font-weight: 500;
    font-size: 13px;
    min-height: 18px;
}

QPushButton:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
    color: #0f172a;
}

QPushButton:pressed {
    background-color: #f1f5f9;
}

QPushButton:disabled {
    background-color: #f8fafc;
    border-color: #e2e8f0;
    color: #cbd5e1;
}

/* Primary Solid Blue Button */
.PrimaryBtn, QPushButton#PrimaryBtn {
    background-color: #1d4ed8;
    border: 1px solid #1e40af;
    color: #ffffff;
    font-weight: 600;
}

.PrimaryBtn:hover, QPushButton#PrimaryBtn:hover {
    background-color: #1e40af;
    border-color: #172554;
    color: #ffffff;
}

.PrimaryBtn:pressed, QPushButton#PrimaryBtn:pressed {
    background-color: #1e3a8a;
}

/* Secondary Deep Blue Button */
.SecondaryBlueBtn {
    background-color: #0f766e;
    border: 1px solid #115e59;
    color: #ffffff;
    font-weight: 600;
}

.SecondaryBlueBtn:hover {
    background-color: #115e59;
    color: #ffffff;
}

/* Danger / Delete Button */
.DangerBtn {
    background-color: #ffffff;
    border: 1px solid #fca5a5;
    color: #dc2626;
}

.DangerBtn:hover {
    background-color: #fef2f2;
    border-color: #ef4444;
}

/* === Text Inputs & Search Boxes === */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 12px;
    color: #0f172a;
    font-size: 13px;
}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1.5px solid #2563eb;
    background-color: #ffffff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid #cbd5e1;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    selection-background-color: #e0f2fe;
    selection-color: #0284c7;
    padding: 4px;
}

/* === Tables & Data Grids === */
QTableWidget, QTableView, QListWidget, QListView {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #f1f5f9;
    outline: none;
    color: #1e293b;
}

QTableWidget::item, QListWidget::item {
    padding: 9px 12px;
    border-bottom: 1px solid #f1f5f9;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #eff6ff;
    color: #1d4ed8;
    font-weight: 500;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #64748b;
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    font-weight: 600;
    font-size: 12px;
}

/* === Group Boxes === */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 22px;
    padding-top: 18px;
    padding-bottom: 14px;
    padding-left: 14px;
    padding-right: 14px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 6px;
    color: #1e293b;
    font-size: 13px;
    font-weight: 700;
}

/* === Progress Bars === */
QProgressBar {
    background-color: #e2e8f0;
    border: none;
    border-radius: 6px;
    text-align: center;
    color: #1e293b;
    font-weight: 600;
    height: 16px;
}

QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 6px;
}

/* === Tabs === */
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background-color: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background-color: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 18px;
    color: #64748b;
    margin-right: 4px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #0284c7;
    font-weight: 600;
    border-bottom: 2px solid #0284c7;
}

/* === Scrollbars === */
QScrollBar:vertical {
    background-color: #f8fafc;
    width: 9px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #cbd5e1;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
