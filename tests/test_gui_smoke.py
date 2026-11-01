import json
import pytest

pytest.importorskip("PySide6")


@pytest.fixture
def win():
    from PySide6.QtWidgets import QApplication
    from icpsim.gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.settings_panel.grid.setValue(0.05)   # um
    w.settings_panel.frames.setValue(6)
    w.show()
    yield w
    w.close()


def test_main_window(win, tmp_path):
    w = win
    assert "LITERATURE" in w.banner.text() or "DEMO" in w.banner.text()
    assert w.run_btn.text().strip() == "開始模擬 (Run Simulation)" and not w.run_btn.icon().isNull()
    # um widgets map to nm internals
    assert w.mask_panel.thickness.value() == pytest.approx(0.5)
    assert w.mask_panel.mask().thickness_nm == pytest.approx(500)
    assert w.layer_panel.stack().layers[-1].material == "GaN"   # top row shown first, stored bottom->top
    r = w.run_simulation()
    assert r is not None and len(r.frames) == 6
    assert "µm" in w.status_lbl.text()
    w.timeline.slider.setValue(2)
    assert "影格" in w.timeline.label.text() and "3/6" in w.timeline.label.text()
    w.export_png(str(tmp_path / "a.png"))
    w.export_csv(str(tmp_path / "a.csv"))
    w.save_project(str(tmp_path / "a.json"))
    assert json.loads((tmp_path / "a.json").read_text())["length_unit"] == "um"
    assert (tmp_path / "a.png").exists() and "x_um" in (tmp_path / "a.csv").read_text()


def test_layout_order_and_controls(win):
    w = win
    titles = [w.grp_mask.title(), w.grp_gas.title(), w.grp_recipe.title()]
    assert "Mask" in titles[0] and "Gas" in titles[1] and "Recipe" in titles[2]
    assert "光罩" in titles[0] and "氣體" in titles[1] and "配方" in titles[2]
    ys = [g.y() for g in (w.grp_mask, w.grp_gas, w.grp_recipe)]
    assert ys == sorted(ys)
    assert w.tabs.tabText(2) == "進階 (Advanced)"
    # before/after toggle
    w.run_simulation()
    w.act_compare.trigger()
    assert w.view.ax_before is None
    w.act_compare.trigger()
    assert w.view.ax_before is not None
    # timeline play / pause / stop
    w.timeline.slider.setValue(0)
    w.timeline.toggle_play()
    assert w.timeline.playing
    w.timeline._tick()
    assert w.timeline.slider.value() == 1
    w.stop_playback()
    assert not w.timeline.playing
    # gas quick-add and steps
    w.gas_panel.add_gas("Ar")
    assert "Ar" in w.recipe_panel.gases(0)
    w.recipe_panel.add_step()
    assert w.recipe_panel.recipe().steps[1].name == "Step 2"
    w.reset_view()
    assert w.result is None
    w.load_preset("Photoresist")
    assert w.mask_panel.mask().material == "Photoresist"


def test_gui_rates_materials_and_language(win, tmp_path):
    from PySide6.QtWidgets import QLabel, QAbstractButton
    from icpsim.core.rate_sources import UserRateEntry
    w = win
    # quick-add buttons for all six gases
    for g in ("CF4", "O2", "Ar", "BCl3", "Cl2", "N2"):
        assert g in w.gas_panel.quick_buttons
    w.gas_panel.quick_buttons["CF4"].click()
    assert "CF4" in w.recipe_panel.gases(0)
    # custom material without physical parameters + experimental rate
    w.material_panel.add_material("光阻1", is_mask=True)
    assert w.material_panel.materials()["光阻1"].ion_factor is None
    w.mask_panel.material.setCurrentText("光阻1")
    w.user_rates_panel.add_entry(UserRateEntry("光阻1", "rate", 30.0, "A/s"))
    res = w.refresh_sources()
    assert res.rates["光阻1"].source == "experimental"
    assert w.sources_panel.table.item(w.sources_panel.table.rowCount() - 1, 3).text().startswith("實驗值")
    assert w.user_rates_panel._calc() == pytest.approx(3.33, abs=0.01)
    dlg = w.show_matrix()
    assert dlg.matrix.table.rowCount() >= 2
    dlg.close()
    # library save / load
    f = tmp_path / "lib.json"
    w.material_panel.save_library(str(f))
    assert w.material_panel.load_library(str(f)) is not None
    assert w.user_rates_panel.entries()[0].material == "光阻1"
    # literature DB editable in Advanced tab
    n = w.lit_panel.table.rowCount()
    assert n >= 30
    w.lit_panel._add()
    assert w.lit_panel.table.rowCount() == n + 1
    w.lit_panel.save(str(tmp_path / "db.json"))
    w.lit_panel.restore_builtin()
    # fonts >= 9 pt
    for lab in w.findChildren(QLabel) + w.findChildren(QAbstractButton):
        pt = lab.font().pointSizeF()
        assert pt < 0 or pt >= 9, lab.text()
    # English toggle and back
    w.set_language("en")
    assert w.run_btn.text().strip() == "Run Simulation"
    w.set_language("zh")
    assert "開始模擬" in w.run_btn.text()
    assert w.mask_panel.mask().material == "光阻1"
