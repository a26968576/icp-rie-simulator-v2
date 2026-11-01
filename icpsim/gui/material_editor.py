"""Material library editor and layer-stack editor (thickness in um)."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from ..core.materials import Material
from ..core.layer_stack import LayerStack, Layer
from .widgets import make_table, set_rows, get_rows, add_remove_bar


class MaterialPanel(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(QLabel("Ion / chem factors are relative to GaN (DEMO-model inputs)"))
        self.table = make_table(["Name", "Color", "Ion factor", "Chem factor", "Mask (1/0)"], max_rows=10)
        v.addWidget(self.table)
        v.addWidget(add_remove_bar(self._add, self._remove))

    def set_materials(self, mats):
        set_rows(self.table, [[m.name, m.color, m.ion_factor, m.chem_factor, int(m.is_mask)] for m in mats.values()])

    def materials(self):
        out = {}
        for r in get_rows(self.table):
            if r[0].strip():
                out[r[0].strip()] = Material(r[0].strip(), r[1] or "#888888", float(r[2]), float(r[3]),
                                             r[4].strip() in ("1", "true", "True", "yes"))
        return out

    def _add(self):
        m = self.materials()
        n = f"Custom{len(m)}"
        m[n] = Material(n, "#aa5500", 1.0, 1.0)
        self.set_materials(m)

    def _remove(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)


class LayerPanel(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(3)
        v.addWidget(QLabel("Layer stack, TOP → BOTTOM (under the mask)"))
        self.table = make_table(["Material", "Thickness (um)"], max_rows=4)
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
