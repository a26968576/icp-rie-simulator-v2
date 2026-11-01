"""Small table helpers shared by editor panels."""
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, QToolButton, QHBoxLayout, QWidget,
                               QAbstractItemView, QLabel)
from ..i18n import tr

ROW_H = 26


def make_table(headers, max_rows=4, stretch=True, tips=None):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    hh = t.horizontalHeader()
    hh.setSectionResizeMode(QHeaderView.Stretch if stretch else QHeaderView.Interactive)
    hh.setMinimumSectionSize(48)
    if not stretch:
        hh.setStretchLastSection(True)
    hh.setDefaultAlignment(Qt.AlignCenter)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(ROW_H)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setWordWrap(False)
    for i, tip in enumerate(tips or []):
        if tip and t.horizontalHeaderItem(i):
            t.horizontalHeaderItem(i).setToolTip(tip)
    t._max_rows = max_rows
    t._stretch = stretch
    _fit(t)
    t.model().rowsInserted.connect(lambda *_: _fit(t))
    t.model().rowsRemoved.connect(lambda *_: _fit(t))
    return t


def _fit(t):
    """Height = header + rows (min 1, max max_rows) -> no wasted whitespace."""
    n = min(max(t.rowCount(), 1), t._max_rows)
    extra = 0 if t._stretch else 18          # room for a horizontal scrollbar
    t.setFixedHeight(t.horizontalHeader().sizeHint().height() + n * ROW_H + 6 + extra)


def set_rows(table, rows, readonly_cols=()):
    table.blockSignals(True)
    table.setRowCount(0)
    for r in rows:
        i = table.rowCount()
        table.insertRow(i)
        for c, v in enumerate(r):
            it = QTableWidgetItem(_fmt(v))
            it.setToolTip(_fmt(v))
            if c in readonly_cols:
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            table.setItem(i, c, it)
    table.blockSignals(False)
    if not table._stretch:
        table.resizeColumnsToContents()
        for c in range(table.columnCount()):
            table.setColumnWidth(c, min(table.columnWidth(c), 260))
    _fit(table)


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def get_rows(table):
    return [[(table.item(i, c).text() if table.item(i, c) else "") for c in range(table.columnCount())]
            for i in range(table.rowCount())]


def add_remove_bar(on_add, on_remove, extra=(), add_text="+", trailing=()):
    """extra: [(text, fn[, tooltip])] buttons placed before + / −."""
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(3)
    items = list(extra) + [(add_text, on_add, tr("add_row")), ("−", on_remove, tr("remove_row"))]
    w.buttons = {}
    for item in items:
        text, fn = item[0], item[1]
        b = QToolButton()
        b.setText(text)
        b.setMinimumSize(QSize(30, 26))
        if len(item) > 2:
            b.setToolTip(item[2])
        b.clicked.connect(fn)
        h.addWidget(b)
        w.buttons[text] = b
    for t in trailing:
        h.addWidget(t)
    h.addStretch(1)
    return w


def note(text):
    lab = QLabel(text)
    lab.setWordWrap(True)
    lab.setObjectName("Note")
    return lab
