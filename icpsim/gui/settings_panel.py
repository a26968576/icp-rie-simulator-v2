"""Simulation settings: backend, grid, frames, ARDE / loading extensions."""
from PySide6.QtWidgets import QWidget, QFormLayout, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QLabel
from ..core.project import SimSettings
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
        self.backend.addItem("DEMO cell model (illustrative)", "demo")
        self.backend.addItem("ViennaPS level-set" + ("" if vb.is_available() else " (NOT INSTALLED -> falls back)"),
                             "viennaps")
        self.grid = _d(0.001, 0.5, 3)
        self.grid.setSuffix(" um")
        self.grid.setSingleStep(0.005)
        self.frames = QSpinBox()
        self.frames.setRange(2, 500)
        self.spread = _d(0, 45, 1)
        self.arde = QCheckBox("Enable ARDE (aspect-ratio-dependent etch)")
        self.alpha = _d(0, 10, 3)
        self.loading = QCheckBox("Enable macro-loading")
        self.beta = _d(0, 10, 3)
        self.openfrac = _d(0, 1, 3)
        f.addRow("Backend", self.backend)
        f.addRow("Grid size", self.grid)
        f.addRow("Stored frames", self.frames)
        f.addRow("Ion angular spread (deg)", self.spread)
        f.addRow(self.arde)
        f.addRow("ARDE alpha", self.alpha)
        f.addRow(self.loading)
        f.addRow("Loading beta", self.beta)
        f.addRow("Wafer open-area fraction", self.openfrac)
        f.addRow(QLabel("ViennaPS: " + ("available" if vb.is_available() else f"unavailable ({vb.unavailable_reason()})")))
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

    def settings(self) -> SimSettings:
        return SimSettings(self.grid.value() * 1000, self._s.gas_headroom_nm, self.frames.value(), self.spread.value(),
                           self.backend.currentData(), self.arde.isChecked(), self.alpha.value(),
                           self.loading.isChecked(), self.beta.value(), self.openfrac.value())
