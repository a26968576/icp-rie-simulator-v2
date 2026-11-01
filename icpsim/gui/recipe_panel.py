"""Main recipe step editor + gas species/flow panel (gas flows belong to the selected recipe step)."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from ..core.recipe import Recipe, RecipeStep
from ..i18n import tr
from .widgets import make_table, set_rows, get_rows, add_remove_bar, note

QUICK_GASES = ("CF4", "O2", "Ar", "BCl3", "Cl2", "N2")


class RecipePanel(QWidget):
    stepSelected = Signal(int)

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(3)
        keys = ["hdr_step", "hdr_icp", "hdr_bias", "hdr_p", "hdr_t", "hdr_time"]
        self.table = make_table([tr(k) for k in keys], max_rows=4, tips=[tr(k).replace("\n", " ") for k in keys])
        v.addWidget(self.table)
        self.total = QLabel()
        bar = add_remove_bar(self.add_step, self.remove_step, trailing=[self.total])
        v.addWidget(bar)
        self._gases = []
        self.table.currentCellChanged.connect(lambda r, *_: self.stepSelected.emit(r))
        self.table.itemChanged.connect(lambda *_: self._update_total())

    def _update_total(self):
        try:
            self.total.setText(tr("total_time", t=self.recipe().total_time_s))
        except ValueError:
            self.total.setText("")

    def set_recipe(self, recipe: Recipe):
        self._gases = [dict(s.gases_sccm) for s in recipe.steps]
        set_rows(self.table, [[s.name, s.icp_power_w, s.rf_bias_w, s.pressure_mtorr, s.temperature_c, s.time_s]
                              for s in recipe.steps])
        if recipe.steps:
            self.table.setCurrentCell(0, 0)
        self._update_total()

    def recipe(self) -> Recipe:
        steps = []
        for i, r in enumerate(get_rows(self.table)):
            steps.append(RecipeStep(r[0], float(r[1]), float(r[2]), float(r[3]),
                                    dict(self._gases[i]) if i < len(self._gases) else {}, float(r[4]), float(r[5])))
        return Recipe(steps)

    def gases(self, i):
        return self._gases[i] if 0 <= i < len(self._gases) else {}

    def set_gases(self, i, g):
        if 0 <= i < len(self._gases):
            self._gases[i] = dict(g)

    def add_step(self):
        r = self.recipe()
        new = RecipeStep(name=f"Step {len(r.steps) + 1}")
        if r.steps:
            new.gases_sccm = dict(r.steps[-1].gases_sccm)
        r.steps.append(new)
        self.set_recipe(r)

    def remove_step(self):
        i = self.table.currentRow()
        r = self.recipe()
        if 0 <= i < len(r.steps) and len(r.steps) > 1:
            r.steps.pop(i)
            self.set_recipe(r)


class GasFlowPanel(QWidget):
    """Gas species and flows (sccm) of the currently selected recipe step."""
    gasesChanged = Signal()

    def __init__(self, recipe_panel: RecipePanel):
        super().__init__()
        self.rp = recipe_panel
        self.idx = 0
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(3)
        self.title = QLabel()
        v.addWidget(self.title)
        self.table = make_table([tr("hdr_gas"), tr("hdr_flow")], max_rows=4)
        v.addWidget(self.table)
        quick = [("+" + g, (lambda gg: (lambda: self.add_gas(gg)))(g), tr("quick_add_tip", g=g)) for g in QUICK_GASES]
        self.bar = add_remove_bar(lambda: self.add_gas("Gas"), self._remove, extra=quick)
        self.quick_buttons = {g: self.bar.buttons["+" + g] for g in QUICK_GASES}
        v.addWidget(self.bar)
        v.addWidget(note(tr("gas_note")))
        self.table.itemChanged.connect(self._commit)
        recipe_panel.stepSelected.connect(self.show_step)

    def show_step(self, i):
        self.idx = max(i, 0)
        g = self.rp.gases(self.idx)
        tot = sum(v for v in g.values() if v > 0)
        self.title.setText(tr("gas_title", n=self.idx + 1, tot=tot))
        set_rows(self.table, [[k, v] for k, v in g.items()])

    def _commit(self, *_):
        g = {}
        for name, val in get_rows(self.table):
            try:
                if name.strip():
                    g[name.strip()] = float(val)
            except ValueError:
                pass
        self.rp.set_gases(self.idx, g)
        self.gasesChanged.emit()

    def add_gas(self, name):
        g = dict(self.rp.gases(self.idx))
        g.setdefault(name, 10.0 if name != "Gas" else 0.0)
        self.rp.set_gases(self.idx, g)
        self.show_step(self.idx)
        self.gasesChanged.emit()

    def _remove(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
            self._commit()
