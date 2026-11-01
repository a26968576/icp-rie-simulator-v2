"""Timeline: play/pause + slider (drag to scrub through stored profile frames)."""
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSlider, QLabel, QToolButton, QStyle
from . import icons


class TimelineSlider(QWidget):
    frameChanged = Signal(int)

    def __init__(self):
        super().__init__()
        h = QHBoxLayout(self)
        h.setContentsMargins(4, 2, 4, 2)
        self.play_btn = QToolButton()
        self.play_btn.setIconSize(QSize(26, 26))
        self.play_btn.setToolTip("Play / pause profile evolution")
        self.first = QToolButton(); self.first.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.last = QToolButton(); self.last.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.first.setToolTip("First frame (before)"); self.last.setToolTip("Last frame (after)")
        self.slider = QSlider(Qt.Horizontal)
        self.label = QLabel("t = 0.0 s")
        self.label.setMinimumWidth(170)
        for w in (self.play_btn, self.first, self.slider, self.last, self.label):
            h.addWidget(w)
        self.timer = QTimer(self)
        self.timer.setInterval(80)
        self.timer.timeout.connect(self._tick)
        self.slider.valueChanged.connect(self._changed)
        self.first.clicked.connect(lambda: self.slider.setValue(0))
        self.last.clicked.connect(lambda: self.slider.setValue(self.slider.maximum()))
        self.play_btn.clicked.connect(self.toggle_play)
        self.times = [0.0]
        self._set_icon()
        self.setEnabled(False)

    @property
    def playing(self):
        return self.timer.isActive()

    def _set_icon(self):
        self.play_btn.setIcon(icons.pause() if self.playing else icons.play())

    def toggle_play(self):
        if self.playing:
            self.timer.stop()
        else:
            if self.slider.value() >= self.slider.maximum():
                self.slider.setValue(0)
            self.timer.start()
        self._set_icon()

    def stop(self):
        self.timer.stop()
        self._set_icon()

    def _tick(self):
        if self.slider.value() >= self.slider.maximum():
            self.stop()
        else:
            self.slider.setValue(self.slider.value() + 1)

    def set_times(self, times):
        self.stop()
        self.times = list(times)
        self.slider.blockSignals(True)
        self.slider.setRange(0, max(len(self.times) - 1, 0))
        self.slider.setValue(self.slider.maximum())
        self.slider.blockSignals(False)
        self.setEnabled(len(self.times) > 1)
        self._changed(self.slider.value())

    def _changed(self, i):
        if self.times:
            self.label.setText(f"frame {i + 1}/{len(self.times)}   t = {self.times[i]:.1f} s")
        self.frameChanged.emit(i)
