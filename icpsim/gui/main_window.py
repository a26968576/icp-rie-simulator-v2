"""Main window of ICP-RIE Simulator V2.

UI language: Traditional Chinese "中文 (English)" by default, English toggle in the toolbar (icpsim/i18n.py).
Left side ("製程 Process" tab), stacked top -> bottom:
  1. Mask & materials (mask material/thickness/selectivity, openings/CD, layer stack)
  2. Gas species & flows
  3. Main recipe (ICP, RF bias, pressure, temperature, time, steps)
  + big green RUN button.
  4. Rate sources (which source each material's etch rate comes from)
"材料與蝕刻率" tab: material library (factors optional), experimental rates/selectivities, selectivity matrix.
"進階 Advanced" tab: model backend, ARDE/loading, literature database (editable), calibration.
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
from ..core.recipe import material_rates
from .. import i18n
from ..i18n import tr
from .rate_panel import UserRatesPanel, RateSourcesPanel, SelectivityMatrix, SelectivityMatrixDialog
from .literature_panel import LiteraturePanel
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

APP_TITLE = "ICP-RIE Simulator V2"   # window title is translated (i18n key app_title)


def _group(title, widget):
    g = QGroupBox(title.replace("&", "&&"))
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
        self.setStyleSheet(QSS)
        self.resize(1560, 900)
        self.project = project or gan_preset("SiO2")
        self.result = None
        self.toolbar = None
        self._build_ui()
        self.populate()

    def _build_ui(self):
        self.setWindowTitle(tr("app_title"))
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(6, 4, 6, 4)
        root.setSpacing(4)
        self.banner = QLabel()
        self.banner.setAlignment(Qt.AlignCenter)
        self.banner.setWordWrap(True)
        root.addWidget(self.banner)

        # ---------- left: process (stacked) / materials & rates / advanced ----------
        self.recipe_panel = RecipePanel()
        self.gas_panel = GasFlowPanel(self.recipe_panel)
        self.user_rates_panel = UserRatesPanel()
        self.material_panel = MaterialPanel(lambda: self.user_rates_panel.entries())
        self.layer_panel = LayerPanel()
        self.mask_panel = MaskPanel()
        self.settings_panel = SettingsPanel()
        self.cal_panel = CalibrationPanel(lambda: self.sync_from_widgets() or self.project)
        self.sources_panel = RateSourcesPanel(self.resolve_rates, self.show_matrix)
        self.matrix = SelectivityMatrix()
        self.lit_panel = LiteraturePanel()

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
        self.grp_mask = _group(tr("grp_mask"), top)
        self.grp_gas = _group(tr("grp_gas"), self.gas_panel)
        self.grp_recipe = _group(tr("grp_recipe"), self.recipe_panel)
        self.grp_sources = _group(tr("grp_sources"), self.sources_panel)
        for g in (self.grp_mask, self.grp_gas, self.grp_recipe, self.grp_sources):
            pv.addWidget(g)
        pv.addStretch(1)

        mat = QWidget()
        mv = QVBoxLayout(mat)
        mv.setContentsMargins(4, 4, 4, 4)
        mv.addWidget(_group(tr("grp_matlib"), self.material_panel))
        mv.addWidget(_group(tr("grp_userrates"), self.user_rates_panel))
        self.grp_matrix = _group(tr("grp_matrix"), self.matrix)
        mv.addWidget(self.grp_matrix)
        mv.addStretch(1)

        adv = QWidget()
        av = QVBoxLayout(adv)
        av.setContentsMargins(4, 4, 4, 4)
        av.addWidget(_group(tr("grp_backend"), self.settings_panel))
        av.addWidget(_group(tr("grp_litdb"), self.lit_panel))
        av.addWidget(_group(tr("grp_calib"), self.cal_panel))
        av.addStretch(1)

        self.tabs = QTabWidget()
        self.tabs.addTab(_scroll(process), icons.wafer(), tr("tab_process").replace("&", "&&"))
        self.mat_scroll = _scroll(mat)
        self.tabs.addTab(self.mat_scroll, tr("tab_materials").replace("&", "&&"))
        self.tabs.addTab(_scroll(adv), tr("tab_advanced").replace("&", "&&"))

        self.run_btn = QPushButton("  " + tr("run"))
        self.run_btn.setObjectName("RunButton")
        self.run_btn.setIcon(icons.play("#ffffff"))
        self.run_btn.setIconSize(QSize(26, 26))
        self.run_btn.setMinimumHeight(52)
        self.run_btn.setToolTip(tr("run_tip"))
        self.run_btn.clicked.connect(self.run_simulation)
        self.reset_btn = QPushButton(tr("reset"))
        self.reset_btn.setObjectName("SmallAction")
        self.reset_btn.setIcon(icons.reset())
        self.reset_btn.setToolTip(tr("reset_tip"))
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
        left.setMinimumWidth(640)
        left.setMaximumWidth(780)

        # ---------- right: plot + timeline ----------
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        self.view = ProfileView()
        rv.addWidget(self.view, 1)
        self.timeline = TimelineSlider()
        rv.addWidget(self.timeline)
        h = QHBoxLayout()
        self.overlay = QCheckBox(tr("overlay"))
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
        self.material_panel.materialsChanged.connect(self._materials_changed)
        self.material_panel.libraryLoaded.connect(lambda m, r: self.user_rates_panel.set_entries(r))
        self.user_rates_panel.changed.connect(self.refresh_sources)
        self.gas_panel.gasesChanged.connect(self.refresh_sources)
        self._build_toolbar()

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
        if self.toolbar is not None:
            self.removeToolBar(self.toolbar)
            self.toolbar.deleteLater()
        tb = QToolBar("Main")
        self.toolbar = tb
        tb.setIconSize(QSize(26, 26))
        tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        tb.setMovable(False)
        self.addToolBar(tb)
        preset_btn = QToolButton()
        preset_btn.setIcon(icons.wafer())
        preset_btn.setText(tr("presets"))
        preset_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        preset_btn.setPopupMode(QToolButton.InstantPopup)
        m = QMenu(preset_btn)
        m.addAction(tr("preset_sio2"), lambda: self.load_preset("SiO2"))
        m.addAction(tr("preset_pr"), lambda: self.load_preset("Photoresist"))
        preset_btn.setMenu(m)
        tb.addWidget(preset_btn)
        tb.addAction(self._act(icons.folder(), tr("open"), self.open_project, tr("open_tip"), "Ctrl+O"))
        tb.addAction(self._act(icons.disk(), tr("save"), self.save_project, tr("save_tip"), "Ctrl+S"))
        tb.addSeparator()
        self.act_run = self._act(icons.play(), tr("run"), self.run_simulation, tr("run_tip"), "F5")
        tb.addAction(self.act_run)
        tb.addAction(self._act(icons.stop(), tr("stop"), self.stop_playback, tr("stop_tip")))
        tb.addAction(self._act(icons.reset(), tr("reset"), self.reset_view, tr("reset_tip")))
        tb.addSeparator()
        self.act_compare = self._act(icons.compare(), tr("compare"), self.view.set_compare,
                                     tr("compare_tip"), checkable=True)
        self.act_compare.setChecked(True)
        tb.addAction(self.act_compare)
        tb.addSeparator()
        tb.addAction(self._act(icons.badge("PNG", icons.PURPLE), tr("export_png"), lambda: self.export_png(),
                               tr("export_png_tip")))
        tb.addAction(self._act(icons.badge("CSV", icons.GREEN), tr("export_csv"), lambda: self.export_csv(),
                               tr("export_csv_tip")))
        tb.addAction(self._act(icons.badge("JSON", icons.ORANGE), tr("export_json"), lambda: self.save_project(),
                               tr("export_json_tip")))
        tb.addSeparator()
        self.act_lang = self._act(icons.badge("中/EN", icons.BLUE),
                                  tr("lang"), self.toggle_language, tr("lang_tip"))
        tb.addAction(self.act_lang)

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
        self.user_rates_panel.set_entries(p.user_rates)
        self.update_banner()
        self.refresh_sources()

    def sync_from_widgets(self):
        p = self.project
        p.materials = self.material_panel.materials()
        self.mask_panel.set_material_names(p.materials.keys())
        p.stack = self.layer_panel.stack()
        p.mask = self.mask_panel.mask()
        p.recipe = self.recipe_panel.recipe()
        p.settings = self.settings_panel.settings()
        p.user_rates = self.user_rates_panel.entries()

    def update_banner(self):
        prov = self.result.meta.get("rate_sources") if self.result is not None else None
        lab = labels.label_for(self.settings_panel.settings().backend, self.project.coefficients.calibrated, prov)
        shown = self.result.label if self.result is not None else lab
        extra = ""
        if self.result is not None and self.result.meta.get("fallback_reason"):
            extra = f"  (ViennaPS fallback: {self.result.meta['fallback_reason']})"
        if self.result is not None and shown != lab:
            extra += "  - " + tr("settings_changed")
        if self.result is not None and self.result.meta.get("rate_sources"):
            extra += "<br>" + tr("rates_label") + ": " + labels.provenance_text_lang(self.result.meta["rate_sources"])
        self.banner.setText(f"<b>[{shown}]</b> {labels.text(shown)}{extra}")
        self.banner.setStyleSheet(f"background:{labels.COLOR[shown]};color:white;padding:6px;font-size:10pt;"
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
            self.status_lbl.setText(tr("running"))
            self.run_btn.setEnabled(False)
            QApplication.processEvents()
            self.result = run_project(self.project)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, APP_TITLE, f"{tr('sim_failed')}:\n{e}")
            self.status_lbl.setText(tr("failed"))
            return None
        finally:
            self.run_btn.setEnabled(True)
        self.view.overlay = self.overlay.isChecked()
        self.view.set_result(self.result, self.project.materials)
        self.timeline.set_times(self.result.times)
        f = self.result.frames[-1]
        self.status_lbl.setText(f"{self.result.meta.get('backend')} | {tr('final_depths')}: " +
                                ", ".join(f"#{k + 1} {v / 1000:.3f} µm" for k, v in f.depth_nm.items()))
        self.update_banner()
        self.refresh_sources()
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

    # ----- rate sources / language -----
    def resolve_rates(self, all_materials=False):
        """(names, Resolution) for recipe step 1 of the current widget state."""
        self.sync_from_widgets()
        p = self.project
        if all_materials:
            names = list(p.materials)
        else:
            names = list(dict.fromkeys([l.material for l in p.stack.layers] + [p.mask.material]))
        _, res = material_rates(p.recipe.steps[0], p, names)
        return names, res

    def refresh_sources(self):
        try:
            res = self.sources_panel.refresh()
            names, resall = self.resolve_rates(True)
            self.matrix.set_data(self._matrix_names(names, resall), resall)
            return res
        except Exception:  # noqa: BLE001  (half-edited tables)
            return None

    def show_matrix(self):
        names, res = self.resolve_rates(True)
        self._matrix_dlg = SelectivityMatrixDialog(self._matrix_names(names, res), res, self)
        self._matrix_dlg.show()
        return self._matrix_dlg

    def _matrix_names(self, names, res):
        """Used materials first, then every other material that has a non-zero rate."""
        p = self.project
        used = list(dict.fromkeys([p.mask.material] + [l.material for l in reversed(p.stack.layers)]))
        rest = [n for n in names if n not in used and (res.rates[n].rate_nm_min or 0) > 0]
        return [n for n in used if n in res.rates] + rest

    def _materials_changed(self):
        mats = self.material_panel.materials()
        self.mask_panel.set_material_names(mats.keys())
        self.refresh_sources()

    def toggle_language(self, *_):
        self.set_language("en" if i18n.LANG == "zh" else "zh")

    def set_language(self, lang):
        self.sync_from_widgets()
        i18n.set_language(lang)
        tab = self.tabs.currentIndex()
        result = self.result
        self._build_ui()
        self.populate()
        self.tabs.setCurrentIndex(tab)
        if result is not None:
            self.result = result
            self.view.set_result(result, self.project.materials)
            self.timeline.set_times(result.times)
            self.update_banner()
