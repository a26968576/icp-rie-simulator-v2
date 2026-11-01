"""Small table helpers shared by editor panels."""
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, QToolButton, QHBoxLayout, QWidget,
                               QAbstractItemView)


def make_table(headers, max_rows=4):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(22)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t._max_rows = max_rows
    _fit(t)
    t.model().rowsInserted.connect(lambda *_: _fit(t))
    t.model().rowsRemoved.connect(lambda *_: _fit(t))
    return t


def _fit(t):
    """Height = header + rows (min 1, max max_rows) -> no wasted whitespace."""
    n = min(max(t.rowCount(), 1), t._max_rows)
    t.setFixedHeight(t.horizontalHeader().sizeHint().height() + n * t.verticalHeader().defaultSectionSize() + 4)


def set_rows(table, rows):
    table.blockSignals(True)
    table.setRowCount(0)
    for r in rows:
        i = table.rowCount()
        table.insertRow(i)
        for c, v in enumerate(r):
            table.setItem(i, c, QTableWidgetItem(_fmt(v)))
    table.blockSignals(False)
    _fit(table)


def _fmt(v):
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def get_rows(table):
    return [[(table.item(i, c).text() if table.item(i, c) else "") for c in range(table.columnCount())]
            for i in range(table.rowCount())]


def add_remove_bar(on_add, on_remove, extra=()):
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(3)
    for text, fn in list(extra) + [("+", on_add), ("−", on_remove)]:
        b = QToolButton()
        b.setText(text)
        b.setMinimumSize(QSize(26, 22))
        b.clicked.connect(fn)
        h.addWidget(b)
    h.addStretch(1)
    return w
