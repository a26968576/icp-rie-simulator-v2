"""Headless screenshots of the (Traditional Chinese) GUI.

    QT_QPA_PLATFORM=offscreen python make_screenshot.py screenshot.png screenshot_materials.png

Scenario: user material 光阻1 (no physical parameters) as mask on PDMS, O2/CF4 recipe.
Example experimental inputs: 光阻1 = 30 Å/s, S(PDMS:光阻1) = 3.33 (i.e. PDMS 100 Å/s).
"""
import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from icpsim.core.project import Project
from icpsim.core.materials import default_materials, Material
from icpsim.core.layer_stack import LayerStack, Layer
from icpsim.core.mask import MaskGeometry, Opening
from icpsim.core.recipe import Recipe, RecipeStep
from icpsim.core.rate_sources import UserRateEntry
from icpsim.gui.main_window import MainWindow

out1 = sys.argv[1] if len(sys.argv) > 1 else "screenshot.png"
out2 = sys.argv[2] if len(sys.argv) > 2 else "screenshot_materials.png"


def demo_project():
    mats = default_materials()
    mats["光阻1"] = Material("光阻1", "#c77dbb", None, None, True, "使用者光阻 (user resist)")
    return Project(
        name="PDMS O2/CF4 with 光阻1 mask (example user data)",
        materials=mats,
        stack=LayerStack([Layer("PDMS", 5000.0)]),
        mask=MaskGeometry("光阻1", 2000.0, 8000.0, [Opening(2500.0, 2500.0), Opening(6000.0, 1200.0)], 1.0),
        recipe=Recipe([RecipeStep("Main etch", 500.0, 100.0, 30.0, {"O2": 10.0, "CF4": 40.0}, 20.0, 240.0)]),
        user_rates=[UserRateEntry("光阻1", "rate", 30.0, "A/s", "", "*", "範例實驗值 example"),
                    UserRateEntry("PDMS", "selectivity", 100 / 30, "A/s", "光阻1", "O2/CF4", "100/30 Å/s")],
    )


app = QApplication.instance() or QApplication([])
f = QFont("Microsoft JhengHei UI")
f.setFamilies(["Microsoft JhengHei UI", "Noto Sans CJK TC"])
f.setPointSize(10)
app.setFont(f)
w = MainWindow(demo_project())
w.resize(1600, 1080)
w.show()
w.settings_panel.grid.setValue(0.04)
w.run_simulation()
w.timeline.slider.setValue(int(w.timeline.slider.maximum() * 0.75))
app.processEvents()
w.view.draw()
app.processEvents()
w.grab().save(out1)
w.tabs.setCurrentIndex(1)
app.processEvents()
w.mat_scroll.verticalScrollBar().setValue(w.mat_scroll.verticalScrollBar().maximum())
app.processEvents()
w.grab().save(out2)
print("saved", out1, out2, "|", w.result.label)
