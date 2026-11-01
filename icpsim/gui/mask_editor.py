"""Mask material / thickness / selectivity and openings (center, CD) - all lengths in um."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QComboBox, QDoubleSpinBox, QLabel
from ..core.mask import MaskGeometry, Opening
from ..i18n import tr
from .widgets import make_table, set_rows, get_rows, add_remove_bar


def spin(lo, hi, val=0.0, dec=3, suffix=""):
    s = QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setDecimals(dec)
    s.setValue(val)
    if suffix:
        s.setSuffix(" " + suffix)
    s.setSingleStep(10 ** -(dec - 1) if dec > 1 else 1)
    return s


class MaskPanel(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(3)
        g = QGridLayout()
        g.setHorizontalSpacing(6)
        g.setVerticalSpacing(3)
        self.material = QComboBox()
        self.thickness = spin(0.001, 100, 0.5, 3, "µm")
        self.width = spin(0.1, 1000, 6.0, 3, "µm")
        self.selectivity = spin(0.01, 1e4, 6.0, 2)
        self.selectivity.setToolTip(tr("mask_sel_tip"))
        self.thickness.setToolTip(tr("mask_thickness"))
        rows = [("mask_material", self.material), ("mask_thickness", self.thickness),
                ("domain_width", self.width), ("mask_sel", self.selectivity)]
        for i, (k, w) in enumerate(rows):
            lab = QLabel(tr(k))
            lab.setToolTip(w.toolTip() or tr(k))
            g.addWidget(lab, i, 0)
            g.addWidget(w, i, 1)
        g.setColumnStretch(1, 1)
        v.addLayout(g)
        v.addWidget(QLabel(tr("openings")))
        self.table = make_table([tr("hdr_center"), tr("hdr_cd")], max_rows=3)
        v.addWidget(self.table)
        v.addWidget(add_remove_bar(self._add, self._remove))

    def set_material_names(self, names):
        cur = self.material.currentText()
        self.material.blockSignals(True)
        self.material.clear()
        self.material.addItems(list(names))
        if cur in names:
            self.material.setCurrentText(cur)
        self.material.blockSignals(False)

    def set_mask(self, m: MaskGeometry):
        self.material.setCurrentText(m.material)
        self.thickness.setValue(m.thickness_nm / 1000)
        self.width.setValue(m.domain_width_nm / 1000)
        self.selectivity.setValue(m.selectivity)
        set_rows(self.table, [[o.center_nm / 1000, o.cd_nm / 1000] for o in m.openings])

    def mask(self):
        return MaskGeometry(self.material.currentText(), self.thickness.value() * 1000, self.width.value() * 1000,
                            [Opening(float(a) * 1000, float(b) * 1000) for a, b in get_rows(self.table)],
                            self.selectivity.value())

    def _add(self):
        m = self.mask()
        m.openings.append(Opening(m.domain_width_nm / 2, 500.0))
        set_rows(self.table, [[o.center_nm / 1000, o.cd_nm / 1000] for o in m.openings])

    def _remove(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
