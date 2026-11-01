"""Simulation result container: time-ordered profile frames + provenance label."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from . import labels


@dataclass
class Frame:
    time_s: float
    surface: list                 # list of (N,2) arrays [x_nm, y_nm] (y up, 0 = substrate bottom)
    grid: np.ndarray | None = None  # optional material-index grid (row 0 = top)
    depth_nm: dict = field(default_factory=dict)  # per-opening etch depth below initial semiconductor top


@dataclass
class SimResult:
    frames: list
    label: str
    material_names: list          # index -> name (index 0 = gas)
    extent: tuple                 # (x0, x1, y0, y1) nm
    meta: dict = field(default_factory=dict)

    @property
    def label_text(self):
        return labels.TEXT[self.label]

    @property
    def times(self):
        return [f.time_s for f in self.frames]

    def frame_index_at(self, t):
        return int(np.argmin([abs(x - t) for x in self.times]))
