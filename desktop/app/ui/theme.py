"""Modern Dark Theme & Design Tokens for SMS Bridge Desktop Application."""

APP_STYLESHEET = """
QMainWindow {
    background-color: #0b1120;
}

QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
    color: #f8fafc;
    font-size: 13px;
}

/* === Sidebar Styling === */
#Sidebar {
    background-color: #0f172a;
    border-right: 1px solid #1e293b;
    outline: none;
    padding: 12px 8px;
}

#Sidebar::item {
    padding: 12px 16px;
    margin: 4px 0px;
    border-radius: 8px;
    color: #94a3b8;
    font-size: 14px;
    font-weight: 500;
}

#Sidebar::item:hover {
    background-color: #1e293b;
    color: #f8fafc;
}

#Sidebar::item:selected {
    background-color: #312e81;
    color: #818cf8;
    font-weight: 600;
    border-left: 3px solid #6366f1;
}

/* === Headers & Typography === */
.ScreenTitle {
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 8px;
}

.ScreenSubtitle {
    font-size: 13px;
    color: #94a3b8;
    margin-bottom: 16px;
}

/* === Metric Cards === */
.MetricCard {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px;
}

.MetricCardTitle {
    font-size: 12px;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.MetricCardValue {
    font-size: 26px;
    font-weight: 800;
    color: #f8fafc;
    margin-top: 4px;
}

.MetricCardSubtitle {
    font-size: 12px;
    color: #64748b;
    margin-top: 2px;
}

/* === Buttons === */
QPushButton {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 16px;
    color: #f8fafc;
    font-weight: 600;
    font-size: 13px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #475569;
}

QPushButton:pressed {
    background-color: #0f172a;
}

QPushButton:disabled {
    background-color: #1e293b;
    border-color: #1e293b;
    color: #475569;
}

.PrimaryButton, QPushButton#PrimaryAction {
    background-color: #6366f1;
    border: 1px solid #4f46e5;
    color: #ffffff;
    font-weight: 600;
}

.PrimaryButton:hover, QPushButton#PrimaryAction:hover {
    background-color: #4f46e5;
    border-color: #4338ca;
}

.PrimaryButton:pressed, QPushButton#PrimaryAction:pressed {
    background-color: #3730a3;
}

.DangerButton {
    background-color: #450a0a;
    border: 1px solid #991b1b;
    color: #fca5a5;
}

.DangerButton:hover {
    background-color: #7f1d1d;
    border-color: #b91c1c;
}

/* === Inputs, Combos, SpinBoxes === */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
    background-color: #151e2e;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    color: #f8fafc;
    font-size: 13px;
}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #6366f1;
    background-color: #182234;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid #334155;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    selection-background-color: #312e81;
    selection-color: #818cf8;
    padding: 4px;
}

/* === Tables & Lists === */
QTableWidget, QTableView, QListWidget, QListView {
    background-color: #151e2e;
    border: 1px solid #334155;
    border-radius: 10px;
    gridline-color: #1e293b;
    outline: none;
    color: #f8fafc;
}

QTableWidget::item, QListWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #1e293b;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #312e81;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #334155;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
}

/* === GroupBoxes === */
QGroupBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    margin-top: 24px;
    padding-top: 18px;
    padding-bottom: 12px;
    padding-left: 12px;
    padding-right: 12px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 6px;
    color: #818cf8;
    font-size: 13px;
    font-weight: 700;
}

/* === Progress Bar === */
QProgressBar {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    text-align: center;
    color: #f8fafc;
    font-weight: 600;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #6366f1;
    border-radius: 7px;
}

/* === Tabs === */
QTabWidget::pane {
    border: 1px solid #334155;
    border-radius: 8px;
    background-color: #151e2e;
    top: -1px;
}

QTabBar::tab {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 18px;
    color: #94a3b8;
    margin-right: 4px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #151e2e;
    color: #818cf8;
    font-weight: 600;
    border-bottom: 2px solid #6366f1;
}

/* === Scrollbars === */
QScrollBar:vertical {
    background-color: #0f172a;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #334155;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
