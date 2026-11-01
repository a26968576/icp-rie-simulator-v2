"""Main window of ICP-RIE Simulator V2.

Left side ("Process" tab), stacked top -> bottom:
  1. Mask & materials (mask material/thickness/selectivity, openings/CD, layer stack)
  2. Gas species & flows
  3. Main recipe (ICP, RF bias, pressure, temperature, time, steps)
  + big green RUN button.
"Advanced" tab: model backend, ARDE/loading, calibration, material library.
All user-facing lengths are micrometers.
"""
from __future__ import annotations
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QSplitter,
                               QFileDialog, QMessageBox, QCheckBox, QToolBar, QApplication, QGroupBox,
                               QScrollArea, QPushButton, QToolButton, QMenu)
from ..core import labels
from ..core.project import gan_preset, Project
from ..models.demo_model import run_project
from ..io import project_io, export
from . import icons
from .style import QSS
from .recipe_panel import RecipePanel, GasFlowPanel
from .material_editor import MaterialPanel, LayerPanel
from .mask_editor import MaskPanel
from .settings_panel import SettingsPanel
from .calibration_panel import CalibrationPanel
from .timeline import TimelineSlider
from .profile_view import ProfileView

APP_TITLE = "ICP-RIE Simulator V2"


def _group(title, widget):
    g = QGroupBox(title)
    v = QVBoxLayout(g)
    v.setContentsMargins(6, 4, 6, 4)
    v.setSpacing(3)
    v.addWidget(widget)
    return g


def _scroll(widget):
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setWidget(widget)
    return sa


class MainWindow(QMainWindow):
    def __init__(self, project: Project | None = None):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setStyleSheet(QSS)
        self.resize(1500, 880)
        self.project = project or gan_preset("SiO2")
        self.result = None

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(6, 4, 6, 4)
        root.setSpacing(4)
        self.banner = QLabel()
        self.banner.setAlignment(Qt.AlignCenter)
        self.banner.setWordWrap(True)
        root.addWidget(self.banner)

        # ---------- left: process (stacked) + advanced ----------
        self.recipe_panel = RecipePanel()
        self.gas_panel = GasFlowPanel(self.recipe_panel)
        self.material_panel = MaterialPanel()
        self.layer_panel = LayerPanel()
        self.mask_panel = MaskPanel()
        self.settings_panel = SettingsPanel()
        self.cal_panel = CalibrationPanel(lambda: self.sync_from_widgets() or self.project)

        top = QWidget()
        tv = QVBoxLayout(top)
        tv.setContentsMargins(0, 0, 0, 0)
        tv.setSpacing(4)
        tv.addWidget(self.mask_panel)
        tv.addWidget(self.layer_panel)
        process = QWidget()
        pv = QVBoxLayout(process)
        pv.setContentsMargins(4, 4, 4, 4)
        pv.setSpacing(2)
        self.grp_mask = _group("①  Mask && materials", top)
        self.grp_gas = _group("②  Gas species && flows", self.gas_panel)
        self.grp_recipe = _group("③  Main recipe", self.recipe_panel)
        for g in (self.grp_mask, self.grp_gas, self.grp_recipe):
            pv.addWidget(g)
        pv.addStretch(1)

        adv = QWidget()
        av = QVBoxLayout(adv)
        av.setContentsMargins(4, 4, 4, 4)
        av.addWidget(_group("Model backend && extensions (ARDE / loading)", self.settings_panel))
        av.addWidget(_group("Calibration (experimental depth vs time)", self.cal_panel))
        av.addWidget(_group("Material library", self.material_panel))
        av.addStretch(1)

        self.tabs = QTabWidget()
        self.tabs.addTab(_scroll(process), icons.wafer(), "Process")
        self.tabs.addTab(_scroll(adv), "Advanced")

        self.run_btn = QPushButton("  RUN SIMULATION")
        self.run_btn.setObjectName("RunButton")
        self.run_btn.setIcon(icons.play("#ffffff"))
        self.run_btn.setIconSize(QSize(26, 26))
        self.run_btn.setMinimumHeight(52)
        self.run_btn.setToolTip("Run the etch simulation (F5)")
        self.run_btn.clicked.connect(self.run_simulation)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setObjectName("SmallAction")
        self.reset_btn.setIcon(icons.reset())
        self.reset_btn.setToolTip("Clear the result and reload the current preset values")
        self.reset_btn.clicked.connect(self.reset_view)
        runrow = QHBoxLayout()
        runrow.addWidget(self.run_btn, 1)
        runrow.addWidget(self.reset_btn)

        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(4)
        lv.addWidget(self.tabs, 1)
        lv.addLayout(runrow)
        left.setMinimumWidth(440)
        left.setMaximumWidth(560)

        # ---------- right: plot + timeline ----------
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        self.view = ProfileView()
        rv.addWidget(self.view, 1)
        self.timeline = TimelineSlider()
        rv.addWidget(self.timeline)
        h = QHBoxLayout()
        self.overlay = QCheckBox("Overlay BEFORE outline on AFTER")
        self.overlay.setChecked(True)
        self.status_lbl = QLabel("")
        h.addWidget(self.overlay)
        h.addStretch(1)
        h.addWidget(self.status_lbl)
        rv.addLayout(h)

        split = QSplitter(Qt.Horizontal)
        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(1, 1)
        root.addWidget(split, 1)
        self.setCentralWidget(central)

        self.timeline.frameChanged.connect(self.view.show_frame)
        self.overlay.toggled.connect(self._overlay)
        self.cal_panel.calibrationChanged.connect(self.update_banner)
        self.settings_panel.backend.currentIndexChanged.connect(lambda *_: self.update_banner())
        self._build_toolbar()
        self.populate()

    # ----- toolbar -----
    def _act(self, icon, text, fn, tip=None, shortcut=None, checkable=False):
        a = QAction(icon, text, self)
        a.setToolTip(tip or text)
        a.setCheckable(checkable)
        if shortcut:
            a.setShortcut(shortcut)
        a.triggered.connect(fn)
        return a

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setIconSize(QSize(26, 26))
        tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        tb.setMovable(False)
        self.addToolBar(tb)
        preset_btn = QToolButton()
        preset_btn.setIcon(icons.wafer())
        preset_btn.setText("Presets")
        preset_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        preset_btn.setPopupMode(QToolButton.InstantPopup)
        m = QMenu(preset_btn)
        m.addAction("GaN / Cl2-BCl3 with SiO2 mask", lambda: self.load_preset("SiO2"))
        m.addAction("GaN / Cl2-BCl3 with photoresist mask", lambda: self.load_preset("Photoresist"))
        preset_btn.setMenu(m)
        tb.addWidget(preset_btn)
        tb.addAction(self._act(icons.folder(), "Open", self.open_project, "Open project (JSON)", "Ctrl+O"))
        tb.addAction(self._act(icons.disk(), "Save", self.save_project, "Save project (JSON)", "Ctrl+S"))
        tb.addSeparator()
        self.act_run = self._act(icons.play(), "Run", self.run_simulation, "Run simulation", "F5")
        tb.addAction(self.act_run)
        tb.addAction(self._act(icons.stop(), "Stop", self.stop_playback, "Stop timeline playback"))
        tb.addAction(self._act(icons.reset(), "Reset", self.reset_view, "Clear result"))
        tb.addSeparator()
        self.act_compare = self._act(icons.compare(), "Before/After", self.view.set_compare,
                                     "Toggle side-by-side BEFORE | AFTER comparison", checkable=True)
        self.act_compare.setChecked(True)
        tb.addAction(self.act_compare)
        tb.addSeparator()
        tb.addAction(self._act(icons.badge("PNG", icons.PURPLE), "Export PNG", lambda: self.export_png(),
                               "Export figure as PNG"))
        tb.addAction(self._act(icons.badge("CSV", icons.GREEN), "Export CSV", lambda: self.export_csv(),
                               "Export profile points (µm) as CSV"))
        tb.addAction(self._act(icons.badge("JSON", icons.ORANGE), "Export JSON", lambda: self.save_project(),
                               "Export project / recipe as JSON (µm)"))

    # ----- model <-> widgets -----
    def populate(self):
        p = self.project
        self.material_panel.set_materials(p.materials)
        self.layer_panel.set_stack(p.stack)
        self.mask_panel.set_material_names(p.materials.keys())
        self.mask_panel.set_mask(p.mask)
        self.recipe_panel.set_recipe(p.recipe)
        self.gas_panel.show_step(0)
        self.settings_panel.set_settings(p.settings)
        self.update_banner()

    def sync_from_widgets(self):
        p = self.project
        p.materials = self.material_panel.materials()
        self.mask_panel.set_material_names(p.materials.keys())
        p.stack = self.layer_panel.stack()
        p.mask = self.mask_panel.mask()
        p.recipe = self.recipe_panel.recipe()
        p.settings = self.settings_panel.settings()

    def update_banner(self):
        lab = labels.label_for(self.settings_panel.settings().backend, self.project.coefficients.calibrated)
        shown = self.result.label if self.result is not None else lab
        extra = ""
        if self.result is not None and self.result.meta.get("fallback_reason"):
            extra = f"  (ViennaPS fallback: {self.result.meta['fallback_reason']})"
        if self.result is not None and shown != lab:
            extra += "  - settings changed since last run; re-run to update."
        self.banner.setText(f"<b>[{shown}]</b> {labels.TEXT[shown]}{extra}")
        self.banner.setStyleSheet(f"background:{labels.COLOR[shown]};color:white;padding:6px;font-size:13px;"
                                  "border-radius:6px;")

    # ----- actions -----
    def load_preset(self, mask):
        self.project = gan_preset(mask)
        self.reset_view()
        self.populate()

    def reset_view(self):
        self.stop_playback()
        self.result = None
        self.view.clear_result()
        self.timeline.set_times([0.0])
        self.status_lbl.setText("")
        self.update_banner()

    def stop_playback(self):
        self.timeline.stop()

    def run_simulation(self):
        self.stop_playback()
        try:
            self.sync_from_widgets()
            self.status_lbl.setText("running...")
            self.run_btn.setEnabled(False)
            QApplication.processEvents()
            self.result = run_project(self.project)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, APP_TITLE, f"Simulation failed:\n{e}")
            self.status_lbl.setText("failed")
            return None
        finally:
            self.run_btn.setEnabled(True)
        self.view.overlay = self.overlay.isChecked()
        self.view.set_result(self.result, self.project.materials)
        self.timeline.set_times(self.result.times)
        f = self.result.frames[-1]
        self.status_lbl.setText(f"{self.result.meta.get('backend')} | final depths: " +
                                ", ".join(f"#{k + 1} {v / 1000:.3f} µm" for k, v in f.depth_nm.items()))
        self.update_banner()
        return self.result

    def _overlay(self, on):
        self.view.overlay = on
        self.view.show_frame(self.timeline.slider.value())

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open project", "", "Project (*.json)")
        if path:
            try:
                self.project = project_io.load_project(path)
                self.reset_view()
                self.populate()
            except Exception as e:  # noqa: BLE001
                QMessageBox.critical(self, APP_TITLE, str(e))

    def save_project(self, path=None):
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, "Save project", "project.json", "Project (*.json)")
        if path:
            self.sync_from_widgets()
            project_io.save_project(self.project, path)

    def export_png(self, path=None):
        if self.result is None:
            return
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, "Export PNG", "profile.png", "PNG (*.png)")
        if path:
            export.export_png(self.view.fig, path, self.result, self.project)

    def export_csv(self, path=None):
        if self.result is None:
            return
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, "Export profile CSV", "profile.csv", "CSV (*.csv)")
        if path:
            export.export_profile_csv(self.result, path, self.timeline.slider.value(), self.project)
