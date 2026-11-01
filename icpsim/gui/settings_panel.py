"""Simulation settings: backend, grid, frames, ARDE / loading extensions."""
from PySide6.QtWidgets import QWidget, QFormLayout, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QLabel
from ..core.project import SimSettings
from ..i18n import tr
from ..models import physics_backend_viennaps as vb


def _d(lo, hi, dec=2):
    s = QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setDecimals(dec)
    return s


class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        f = QFormLayout(self)
        self.backend = QComboBox()
        self.backend.addItem(tr("be_demo"), "demo")
        self.backend.addItem(tr("be_vps") + ("" if vb.is_available() else " — " + tr("not_installed")), "viennaps")
        self.grid = _d(0.001, 0.5, 3)
        self.grid.setSuffix(" µm")
        self.grid.setSingleStep(0.005)
        self.frames = QSpinBox()
        self.frames.setRange(2, 500)
        self.spread = _d(0, 45, 1)
        self.arde = QCheckBox(tr("arde_on"))
        self.alpha = _d(0, 10, 3)
        self.loading = QCheckBox(tr("loading_on"))
        self.beta = _d(0, 10, 3)
        self.openfrac = _d(0, 1, 3)
        self.use_lit = QCheckBox(tr("use_lit"))
        f.addRow(tr("backend"), self.backend)
        f.addRow(tr("grid"), self.grid)
        f.addRow(tr("frames"), self.frames)
        f.addRow(tr("spread"), self.spread)
        f.addRow(self.arde)
        f.addRow(tr("arde_alpha"), self.alpha)
        f.addRow(self.loading)
        f.addRow(tr("loading_beta"), self.beta)
        f.addRow(tr("openfrac"), self.openfrac)
        f.addRow(self.use_lit)
        st = QLabel(tr("vps_status") + ": " + (tr("available") if vb.is_available()
                                               else f"{tr('unavailable')} ({vb.unavailable_reason()})"))
        st.setWordWrap(True)
        f.addRow(st)
        self._s = SimSettings()

    def set_settings(self, s: SimSettings):
        self._s = s
        self.backend.setCurrentIndex(1 if s.backend == "viennaps" else 0)
        self.grid.setValue(s.grid_nm / 1000)
        self.frames.setValue(s.n_frames)
        self.spread.setValue(s.ion_spread_deg)
        self.arde.setChecked(s.enable_arde)
        self.alpha.setValue(s.arde_alpha)
        self.loading.setChecked(s.enable_loading)
        self.beta.setValue(s.loading_beta)
        self.openfrac.setValue(s.wafer_open_fraction)
        self.use_lit.setChecked(s.use_literature)

    def settings(self) -> SimSettings:
        return SimSettings(self.grid.value() * 1000, self._s.gas_headroom_nm, self.frames.value(), self.spread.value(),
                           self.backend.currentData(), self.arde.isChecked(), self.alpha.value(),
                           self.loading.isChecked(), self.beta.value(), self.openfrac.value(),
                           self.use_lit.isChecked())
