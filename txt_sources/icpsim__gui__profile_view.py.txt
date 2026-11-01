"""Matplotlib canvas: BEFORE (t = 0) vs AFTER (selected frame). Axes in micrometers."""
from __future__ import annotations
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from ..core import labels

UM = 1e-3  # nm -> um


def draw_frame(ax, result, frame, materials, title, before=None):
    ax.clear()
    x0, x1, y0, y1 = (v * UM for v in result.extent)
    if frame.grid is not None:
        cols = ["#ffffff"] + [materials[n].color if n in materials else "#888888" for n in result.material_names[1:]]
        ax.imshow(frame.grid, cmap=ListedColormap(cols), vmin=-0.5, vmax=len(cols) - 0.5,
                  extent=(x0, x1, y0, y1), origin="upper", interpolation="nearest", aspect="equal")
    if before is not None:
        for seg in before.surface:
            ax.plot(seg[:, 0] * UM, seg[:, 1] * UM, ":", color="#555555", lw=0.9)
    for seg in frame.surface:
        ax.plot(seg[:, 0] * UM, seg[:, 1] * UM, "-", color="k", lw=1.2)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xlabel("x (µm)")
    ax.set_ylabel("y (µm)")
    ax.set_title(title, fontsize=9)
    if not labels.is_calibrated(result.label):
        ax.text(0.5, 0.5, "DEMO / UNCALIBRATED\nillustrative only", transform=ax.transAxes, ha="center",
                va="center", fontsize=13, color="red", alpha=0.25, rotation=20, weight="bold")


def legend_handles(result, materials):
    from matplotlib.patches import Patch
    return [Patch(facecolor=materials[n].color, edgecolor="#444", label=n)
            for n in dict.fromkeys(result.material_names[1:]) if n in materials and n in result.meta.get(
                "used_materials", result.material_names)]


class ProfileView(FigureCanvasQTAgg):
    def __init__(self):
        self.fig = Figure(figsize=(10, 4.6), tight_layout=True)
        super().__init__(self.fig)
        self.result = None
        self.materials = {}
        self.overlay = True
        self.compare = True    # True: BEFORE | AFTER side by side ; False: AFTER only (larger)
        self.index = 0
        self._make_axes()
        self.show_placeholder()

    def _make_axes(self):
        self.fig.clear()
        if self.compare:
            self.ax_before, self.ax_after = self.fig.subplots(1, 2, sharey=True)
        else:
            self.ax_before, self.ax_after = None, self.fig.subplots(1, 1)

    def set_compare(self, on):
        self.compare = bool(on)
        self._make_axes()
        if self.result is None:
            self.show_placeholder()
        else:
            self.show_frame(self.index)

    def show_placeholder(self):
        for ax in (self.ax_before, self.ax_after):
            if ax is None:
                continue
            ax.clear()
            ax.set_xticks([]); ax.set_yticks([])
            ax.text(0.5, 0.5, "Press  ▶ RUN SIMULATION", ha="center", va="center", transform=ax.transAxes,
                    fontsize=14, color="#2e9d46", weight="bold")
        self.fig.suptitle("")
        self.draw_idle()

    def clear_result(self):
        self.result = None
        self.show_placeholder()

    def set_result(self, result, materials):
        self.result, self.materials = result, materials
        self.show_frame(len(result.frames) - 1)

    def show_frame(self, i):
        r = self.result
        if r is None:
            return
        i = int(np.clip(i, 0, len(r.frames) - 1))
        self.index = i
        f0, f = r.frames[0], r.frames[i]
        if self.ax_before is not None:
            draw_frame(self.ax_before, r, f0, self.materials, "BEFORE  t = 0 s")
        depth = ", ".join(f"#{k + 1}: {v * UM:.3f} µm" for k, v in f.depth_nm.items())
        draw_frame(self.ax_after, r, f, self.materials, f"AFTER  t = {f.time_s:.1f} s   depth {depth}",
                   before=f0 if self.overlay else None)
        h = legend_handles(r, self.materials)
        if h:
            self.ax_after.legend(handles=h, loc="lower right", fontsize=7, framealpha=0.85)
        self.fig.suptitle(f"[{r.label}] {labels.TEXT[r.label]}", fontsize=8, color=labels.COLOR[r.label])
        self.draw_idle()
