"""Application stylesheet (modern, compact)."""

QSS = """
QMainWindow, QWidget, QDialog { font-size: 10pt;
    font-family: "Microsoft JhengHei UI", "Microsoft JhengHei", "Noto Sans CJK TC", "PingFang TC", sans-serif; }
QLabel#Note { color: #546e7a; font-size: 9pt; }
QLabel#Formula { color: #0d47a1; font-weight: bold; background: #e3f2fd; border-radius: 4px; padding: 3px; }
QLabel#Warn { color: #b71c1c; font-size: 9pt; }
QMainWindow { background: #f3f5f8; }
QToolBar { background: #ffffff; border-bottom: 1px solid #d5dbe3; spacing: 4px; padding: 3px; }
QToolButton { padding: 3px 6px; border-radius: 6px; }
QToolButton:hover { background: #e3ecf8; }
QToolButton:checked { background: #cfe0f7; }
QGroupBox { background: #ffffff; border: 1px solid #d5dbe3; border-radius: 8px; margin-top: 14px;
            padding: 8px 6px 6px 6px; font-weight: bold; color: #1f3b5c; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
QGroupBox QLabel, QGroupBox QTableWidget, QGroupBox QDoubleSpinBox, QGroupBox QComboBox { font-weight: normal; }
QTableWidget { border: 1px solid #e0e5ec; gridline-color: #e8ecf1; background: #fbfcfe; }
QHeaderView::section { background: #eef2f7; border: none; border-right: 1px solid #dde3ea; padding: 2px; }
QPushButton { background: #eef2f7; border: 1px solid #ccd5e0; border-radius: 6px; padding: 3px 8px; }
QPushButton:hover { background: #e1e9f4; }
QPushButton#RunButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #43b35b, stop:1 #2e9d46);
    color: white; font-size: 14pt; font-weight: bold; border: 1px solid #23803a; border-radius: 10px;
    padding: 10px 14px; }
QPushButton#RunButton:hover { background: #3aa852; }
QPushButton#RunButton:pressed { background: #23803a; }
QPushButton#RunButton:disabled { background: #9fcfaa; }
QPushButton#SmallAction { padding: 6px 10px; font-weight: bold; }
QTabWidget::pane { border: 1px solid #d5dbe3; border-radius: 6px; background: #f3f5f8; }
QTabBar::tab { padding: 6px 14px; background: #e4e9f0; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #ffffff; font-weight: bold; }
QSlider::groove:horizontal { height: 6px; background: #d5dbe3; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #1e6fd9; border-radius: 3px; }
QSlider::handle:horizontal { background: #ffffff; border: 2px solid #1e6fd9; width: 14px; margin: -6px 0;
                             border-radius: 8px; }
QScrollArea { border: none; background: transparent; }
"""
