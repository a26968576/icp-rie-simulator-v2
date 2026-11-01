"""Material library editor (physical factors optional) and layer-stack editor (thickness in um)."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox
from ..core.materials import Material
from ..core.layer_stack import LayerStack, Layer
from ..i18n import tr
from ..io import material_library
from .widgets import make_table, set_rows, get_rows, add_remove_bar, note


def _opt(x):
    x = (x or "").strip()
    return float(x) if x else None


class MaterialPanel(QWidget):
    materialsChanged = Signal()
    libraryLoaded = Signal(object, object)      # materials, user_rates

    def __init__(self, get_user_rates=lambda: []):
        super().__init__()
        self.get_user_rates = get_user_rates
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(3)
        v.addWidget(note(tr("matlib_note")))
        keys = ["hdr_name", "hdr_color", "hdr_ion", "hdr_chem", "hdr_ismask", "hdr_note"]
        self.table = make_table([tr(k) for k in keys], max_rows=7)
        v.addWidget(self.table)
        self.load_btn = QPushButton(tr("lib_load")); self.load_btn.setToolTip(tr("lib_tip"))
        self.save_btn = QPushButton(tr("lib_save")); self.save_btn.setToolTip(tr("lib_tip"))
        self.load_btn.clicked.connect(lambda: self.load_library())
        self.save_btn.clicked.connect(lambda: self.save_library())
        v.addWidget(add_remove_bar(self._add, self._remove, add_text="+ " + tr("add_material"),
                                   trailing=[self.load_btn, self.save_btn]))
        self.table.itemChanged.connect(lambda *_: self.materialsChanged.emit())

    def set_materials(self, mats):
        set_rows(self.table, [[m.name, m.color, m.ion_factor, m.chem_factor, int(m.is_mask), m.note]
                              for m in mats.values()])

    def materials(self):
        out = {}
        for r in get_rows(self.table):
            if r[0].strip():
                out[r[0].strip()] = Material(r[0].strip(), r[1] or "#888888", _opt(r[2]), _opt(r[3]),
                                             r[4].strip() in ("1", "true", "True", "yes", "是"), r[5])
        return out

    def add_material(self, name, color="#aa5500", is_mask=False):
        m = self.materials()
        m[name] = Material(name, color, None, None, is_mask)
        self.set_materials(m)
        self.materialsChanged.emit()

    def _add(self):
        n = f"材料{len(self.materials()) + 1}"
        self.add_material(n)

    def _remove(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
            self.materialsChanged.emit()

    def save_library(self, path=None):
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, tr("lib_save"), "materials.json", "JSON (*.json)")
        if path:
            material_library.save_library(path, self.materials(), self.get_user_rates())
        return path

    def load_library(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, tr("lib_load"), "", "JSON (*.json)")
        if path:
            try:
                mats, rates = material_library.load_library(path)
            except Exception as e:  # noqa: BLE001
                QMessageBox.critical(self, tr("lib_load"), str(e))
                return None
            self.set_materials(mats)
            self.libraryLoaded.emit(mats, rates)
            self.materialsChanged.emit()
            return mats, rates
        return None


class LayerPanel(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(3)
        v.addWidget(QLabel(tr("layers")))
        self.table = make_table([tr("hdr_material"), tr("hdr_thick")], max_rows=4)
        v.addWidget(self.table)
        v.addWidget(add_remove_bar(self._add, self._remove))

    # table shows top layer first; LayerStack stores bottom -> top
    def set_stack(self, st: LayerStack):
        set_rows(self.table, [[l.material, l.thickness_nm / 1000] for l in reversed(st.layers)])

    def stack(self):
        rows = [r for r in get_rows(self.table) if r[0].strip()]
        return LayerStack([Layer(r[0].strip(), float(r[1]) * 1000) for r in reversed(rows)])

    def _add(self):
        s = self.stack()
        s.layers.append(Layer("GaN", 500.0))
        self.set_stack(s)

    def _remove(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
