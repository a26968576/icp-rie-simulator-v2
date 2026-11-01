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
    assert "DEMO" in w.banner.text()
    assert w.run_btn.text().strip() == "RUN SIMULATION" and not w.run_btn.icon().isNull()
    # um widgets map to nm internals
    assert w.mask_panel.thickness.value() == pytest.approx(0.5)
    assert w.mask_panel.mask().thickness_nm == pytest.approx(500)
    assert w.layer_panel.stack().layers[-1].material == "GaN"   # top row shown first, stored bottom->top
    r = w.run_simulation()
    assert r is not None and len(r.frames) == 6
    assert "µm" in w.status_lbl.text()
    w.timeline.slider.setValue(2)
    assert "frame 3/6" in w.timeline.label.text()
    w.export_png(str(tmp_path / "a.png"))
    w.export_csv(str(tmp_path / "a.csv"))
    w.save_project(str(tmp_path / "a.json"))
    assert json.loads((tmp_path / "a.json").read_text())["length_unit"] == "um"
    assert (tmp_path / "a.png").exists() and "x_um" in (tmp_path / "a.csv").read_text()


def test_layout_order_and_controls(win):
    w = win
    titles = [w.grp_mask.title(), w.grp_gas.title(), w.grp_recipe.title()]
    assert "Mask" in titles[0] and "Gas" in titles[1] and "recipe" in titles[2]
    ys = [g.y() for g in (w.grp_mask, w.grp_gas, w.grp_recipe)]
    assert ys == sorted(ys)
    assert w.tabs.tabText(1) == "Advanced"
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
