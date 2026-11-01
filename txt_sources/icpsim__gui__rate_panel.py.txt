"""Experimental rate/selectivity input, rate-source view and selectivity matrix."""
from __future__ import annotations
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QComboBox, QPushButton,
                               QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox)
from ..core import rate_sources as rs
from ..core.labels import SOURCE_ZH
from ..i18n import tr
from .. import i18n
from .widgets import make_table, set_rows, get_rows, add_remove_bar, note

UNIT_SHOW = {"A/s": "Å/s", "um/min": "µm/min", "nm/min": "nm/min"}
UNIT_PARSE = {"Å/s": "A/s", "A/s": "A/s", "µm/min": "um/min", "um/min": "um/min", "nm/min": "nm/min",
              "nm/s": "nm/s"}
SRC_COLOR = {"experimental": "#c8e6c9", "calibrated": "#c8e6c9", "literature": "#e1bee7", "preset": "#fff9c4",
             "demo": "#ffcdd2", "none": "#ffcdd2"}


def kind_text(k):
    return tr("kind_rate") if k == "rate" else tr("kind_sel")


def parse_kind(t):
    t = t.strip().lower()
    return "selectivity" if (t.startswith("sel") or "選擇" in t) else "rate"


def source_text(src):
    from .. import i18n
    return SOURCE_ZH.get(src, src) if i18n.LANG == "zh" else src


class UserRatesPanel(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(3)
        f = QLabel(tr("sel_formula"))
        f.setObjectName("Formula")
        f.setWordWrap(True)
        v.addWidget(f)
        v.addWidget(note(tr("sel_example")))
        v.addWidget(note(tr("userrates_note")))
        keys = ["hdr_material", "hdr_kind", "hdr_value", "hdr_unit", "hdr_ref", "hdr_chemistry", "hdr_note"]
        tips = [None, "蝕刻率 (rate) / 選擇比 (selectivity)", None, "Å/s, µm/min, nm/min（選擇比免填）",
                "選擇比的分母材料 (mask/reference)", "例 Cl2/BCl3；* = 所有配方", None]
        self.table = make_table([tr(k) for k in keys], max_rows=6, tips=tips, stretch=False)
        v.addWidget(self.table)
        v.addWidget(add_remove_bar(self._add, self._remove,
                                   extra=[("+ " + tr("kind_rate"), self._add_rate, tr("kind_rate")),
                                          ("+ " + tr("kind_sel"), self._add_sel, tr("kind_sel"))]))
        # calculator
        row = QHBoxLayout()
        self.calc_t = QDoubleSpinBox(); self.calc_m = QDoubleSpinBox()
        for s in (self.calc_t, self.calc_m):
            s.setRange(0, 1e6); s.setDecimals(2); s.setSuffix(" Å/s")
        self.calc_t.setValue(100.0); self.calc_m.setValue(30.0)
        self.calc_out = QLabel()
        row.addWidget(QLabel(tr("calc") + ":"))
        row.addWidget(QLabel("R_目標" if i18n.LANG == "zh" else "R_target")); row.addWidget(self.calc_t)
        row.addWidget(QLabel("÷ R_光罩" if i18n.LANG == "zh" else "÷ R_mask")); row.addWidget(self.calc_m)
        row.addWidget(self.calc_out); row.addStretch(1)
        v.addLayout(row)
        self.calc_t.valueChanged.connect(self._calc); self.calc_m.valueChanged.connect(self._calc)
        self._calc()
        self.table.itemChanged.connect(lambda *_: self.changed.emit())

    def _calc(self):
        s = rs.selectivity(self.calc_t.value(), self.calc_m.value())
        self.calc_out.setText(f"= S {s:.2f}" if s != float("inf") else "= ∞")
        return s

    def set_entries(self, entries):
        set_rows(self.table, [[u.material, kind_text(u.kind), u.value, UNIT_SHOW.get(u.unit, u.unit)
                               if u.kind == "rate" else "", u.reference, u.chemistry, u.note] for u in entries])

    def entries(self):
        out = []
        for r in get_rows(self.table):
            if not r[0].strip():
                continue
            try:
                val = float(r[2])
            except ValueError:
                continue
            k = parse_kind(r[1])
            out.append(rs.UserRateEntry(r[0].strip(), k, val, UNIT_PARSE.get(r[3].strip(), "A/s"),
                                        r[4].strip(), r[5].strip() or "*", r[6]))
        return out

    def add_entry(self, e: rs.UserRateEntry):
        self.set_entries(self.entries() + [e])
        self.changed.emit()

    def _add_rate(self):
        self.add_entry(rs.UserRateEntry("光阻1", "rate", 30.0, "A/s", "", "*"))

    def _add_sel(self):
        self.add_entry(rs.UserRateEntry("PDMS", "selectivity", 3.33, "A/s", "光阻1", "*"))

    def _add(self):
        self._add_rate()

    def _remove(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
            self.changed.emit()


class RateSourcesPanel(QWidget):
    """Shows, for the current recipe step 1, which source each used material's rate comes from."""
    def __init__(self, resolve_fn, matrix_fn):
        super().__init__()
        self.resolve_fn = resolve_fn
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(3)
        keys = ["hdr_material", "hdr_rate_um", "hdr_rate_as", "hdr_source"]
        self.table = make_table([tr(k) for k in keys], max_rows=5)
        v.addWidget(self.table)
        self.warn = QLabel()
        self.warn.setWordWrap(True)
        self.warn.setObjectName("Warn")
        v.addWidget(self.warn)
        h = QHBoxLayout()
        self.refresh_btn = QPushButton(tr("refresh")); self.refresh_btn.setToolTip(tr("refresh_tip"))
        self.matrix_btn = QPushButton(tr("show_matrix"))
        self.refresh_btn.clicked.connect(self.refresh)
        self.matrix_btn.clicked.connect(matrix_fn)
        h.addWidget(self.refresh_btn); h.addWidget(self.matrix_btn); h.addStretch(1)
        v.addLayout(h)
        v.addWidget(note(tr("sources_note")))

    def refresh(self):
        try:
            names, res = self.resolve_fn()
        except Exception as e:  # noqa: BLE001
            self.warn.setText(str(e))
            return None
        rows = []
        for n in names:
            r = res.rates[n]
            rows.append([n, "" if r.rate_nm_min is None else f"{r.rate_nm_min / 1000:.4f}",
                         "" if r.rate_nm_min is None else f"{r.rate_nm_min / 6:.2f}", source_text(r.source)])
        set_rows(self.table, rows, readonly_cols=(0, 1, 2, 3))
        for i, n in enumerate(names):
            r = res.rates[n]
            for c in range(4):
                it = self.table.item(i, c)
                it.setBackground(QColor(SRC_COLOR.get(r.source, "#ffffff")))
                it.setToolTip(r.detail)
        self.warn.setText("⚠ " + "\n⚠ ".join(res.warnings) if res.warnings else tr("no_warn"))
        return res


class SelectivityMatrix(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        self.info = QLabel()
        self.info.setWordWrap(True)
        v.addWidget(QLabel(tr("sel_formula")))
        v.addWidget(self.info)
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setMinimumHeight(200)
        v.addWidget(self.table)

    def set_data(self, names, res):
        M = rs.selectivity_matrix(res, names)
        self.info.setText(tr("matrix_note", chem=rs.chem_text(res.chemistry)))
        self.table.setRowCount(len(names)); self.table.setColumnCount(len(names))
        src = {n: res.rates[n].source for n in names}
        self.table.setHorizontalHeaderLabels([f"{n}\n({'光罩' if i18n.LANG == 'zh' else 'mask'})" for n in names])
        self.table.setVerticalHeaderLabels([f"{n} [{source_text(src[n]).split(' ')[0]}]" for n in names])
        for i, row in enumerate(M):
            for j, s in enumerate(row):
                it = QTableWidgetItem("—" if s is None else ("∞" if s == float("inf") else f"{s:.3g}"))
                it.setTextAlignment(Qt.AlignCenter)
                if i == j:
                    it.setBackground(QColor("#eeeeee"))
                elif s is not None:
                    it.setBackground(QColor("#c8e6c9" if s >= 1 else "#ffe0b2"))
                it.setToolTip(f"S({names[i]}:{names[j]}) = R({names[i]}) / R({names[j]})")
                self.table.setItem(i, j, it)
        self.table.resizeRowsToContents()
        return M


class SelectivityMatrixDialog(QDialog):
    def __init__(self, names, res, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("grp_matrix"))
        v = QVBoxLayout(self)
        self.matrix = SelectivityMatrix()
        self.matrix.set_data(names, res)
        v.addWidget(self.matrix)
        b = QDialogButtonBox(QDialogButtonBox.Close)
        b.rejected.connect(self.reject)
        v.addWidget(b)
        self.resize(760, 420)
