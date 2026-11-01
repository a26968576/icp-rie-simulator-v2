"""Calibration tab: load experimental depth-vs-time CSV, fit, apply/reset."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QPlainTextEdit, QFileDialog,
                               QSpinBox, QHBoxLayout)
from ..calibration import fit as cal


class CalibrationPanel(QWidget):
    calibrationChanged = Signal()

    def __init__(self, get_project):
        super().__init__()
        self.get_project = get_project
        self.result = None
        self.path = ""
        v = QVBoxLayout(self)
        v.addWidget(QLabel("CSV columns: time_s, depth_nm [, cd_nm]  (see examples/gan_experiment_example.csv)"))
        h = QHBoxLayout()
        h.addWidget(QLabel("Recipe step #"))
        self.step = QSpinBox()
        self.step.setRange(1, 99)
        h.addWidget(self.step)
        v.addLayout(h)
        self.load_btn = QPushButton("Load CSV and fit...")
        self.apply_btn = QPushButton("Apply calibration (results become CALIBRATED)")
        self.reset_btn = QPushButton("Reset to DEMO coefficients")
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        for w in (self.load_btn, self.apply_btn, self.reset_btn, self.text):
            v.addWidget(w)
        self.load_btn.clicked.connect(self._load)
        self.apply_btn.clicked.connect(self.apply)
        self.reset_btn.clicked.connect(self.reset)
        self.apply_btn.setEnabled(False)

    def _load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Experimental data", "", "CSV (*.csv)")
        if path:
            self.fit(path)

    def fit(self, path):
        try:
            self.result = cal.fit_csv(path, self.get_project(), self.step.value() - 1)
            self.path = path
            self.text.setPlainText(self.result.summary())
            self.apply_btn.setEnabled(True)
        except Exception as e:  # noqa: BLE001
            self.text.setPlainText(f"Fit failed: {e}")
        return self.result

    def apply(self):
        if self.result:
            cal.apply_calibration(self.get_project(), self.result, self.path)
            self.text.appendPlainText("\nApplied. Re-run the simulation.")
            self.calibrationChanged.emit()

    def reset(self):
        cal.reset_calibration(self.get_project())
        self.text.appendPlainText("\nReset to DEMO (uncalibrated) coefficients.")
        self.calibrationChanged.emit()
