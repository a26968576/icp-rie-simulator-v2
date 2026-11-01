"""Headless screenshot of the GUI with the GaN preset simulated."""
import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from icpsim.gui.main_window import MainWindow

out = sys.argv[1] if len(sys.argv) > 1 else "screenshot.png"
app = QApplication.instance() or QApplication([])
w = MainWindow()
w.resize(1600, 900)
w.show()
w.run_simulation()
w.timeline.slider.setValue(int(w.timeline.slider.maximum() * 0.75))
app.processEvents()
w.view.draw()
app.processEvents()
w.grab().save(out)
print("saved", out)
