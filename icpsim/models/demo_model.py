"""DEMO etch model - cell-based 2D profile evolution.

*** Empirical, UNCALIBRATED, illustrative. Not a physical prediction. ***

Each grid cell holds a material index (0 = gas) and a remaining fraction h in [0, 1].
Exposed solid cells lose material at

    rate = R_ion(material) * F_ion + R_chem(material) * F_neutral   [nm/s]

F_ion     : fraction of a narrow (+-ion_spread) fan of downward rays that reach the cell
            through gas (directional ion component, gives anisotropy and mask shadowing)
F_neutral : cosine-weighted fraction of a wide (+-80 deg) fan of rays reaching the cell
            (isotropic chemical component, gives undercut/bowing and geometric RIE lag)
Optional extensions: ARDE factor 1/(1+alpha*AR) and macro loading factor.
"""
from __future__ import annotations
import math
import numpy as np
from ..core import labels
from ..core.frames import Frame, SimResult
from ..core.recipe import material_rates
from ..core.rate_sources import rate_meta
from ..extensions.arde import arde_factor, gas_run_widths
from ..extensions.loading import loading_factor


def _visibility(gas: np.ndarray, angles_deg, weights) -> np.ndarray:
    """Weighted fraction of straight rays from the top boundary that arrive at each cell
    having traversed only gas cells."""
    ny, nx = gas.shape
    acc = np.zeros(gas.shape, dtype=float)
    for a, w in zip(angles_deg, weights):
        s = math.tan(math.radians(a))
        V = np.zeros(gas.shape, dtype=bool)
        V[0] = True
        prev_off = 0
        for j in range(1, ny):
            off = int(round(s * j))
            sh = off - prev_off
            prev_off = off
            src = V[j - 1] & gas[j - 1]
            if sh == 0:
                V[j] = src
            elif sh > 0:
                V[j, sh:] = src[:-sh]
                V[j, :sh] = src[:sh][::-1]  # reflective side wall
            else:
                k = -sh
                V[j, :-k] = src[k:]
                V[j, -k:] = src[-k:][::-1]
        acc += w * V
    return acc / float(np.sum(weights))


class DemoModel:
    name = "demo"

    def __init__(self, project):
        self.p = project

    # ---------- geometry ----------
    def build_grid(self):
        p = self.p
        dx = p.settings.grid_nm
        names = ["gas"] + list(p.materials.keys())
        idx = {n: i for i, n in enumerate(names)}
        H = p.stack.total_thickness + p.mask.thickness_nm + p.settings.gas_headroom_nm
        ny = int(math.ceil(H / dx))
        nx = int(math.ceil(p.mask.domain_width_nm / dx))
        yc = H - (np.arange(ny) + 0.5) * dx           # row centers (y up)
        xc = (np.arange(nx) + 0.5) * dx
        grid = np.zeros((ny, nx), dtype=np.int16)
        y0 = 0.0
        for layer in p.stack.layers:
            y1 = y0 + layer.thickness_nm
            grid[(yc >= y0) & (yc < y1), :] = idx[layer.material]
            y0 = y1
        ytop = y0
        mrows = (yc >= ytop) & (yc < ytop + p.mask.thickness_nm)
        mcols = np.array([not p.mask.is_open(x) for x in xc])
        grid[np.ix_(mrows, mcols)] = idx[p.mask.material]
        self.names, self.idx, self.dx, self.H, self.ytop = names, idx, dx, H, ytop
        self.xc, self.yc = xc, yc
        return grid

    def surface_lines(self, grid, health):
        import contourpy
        solid = np.where(grid > 0, np.clip(health, 0, 1), 0.0)
        # pad with gas on top so contour closes cleanly
        cg = contourpy.contour_generator(self.xc, self.yc, solid)
        return [np.asarray(l) for l in cg.lines(0.5)]

    def depths(self, grid, health):
        out = {}
        for i, o in enumerate(self.p.mask.openings):
            col = int(np.clip(o.center_nm // self.dx, 0, grid.shape[1] - 1))
            solid = np.flatnonzero(grid[:, col] > 0)
            if solid.size == 0:
                out[i] = self.ytop
                continue
            j = solid[0]
            ysurf = self.yc[j] + 0.5 * self.dx - (1 - health[j, col]) * self.dx
            out[i] = float(max(self.ytop - ysurf, 0.0))
        return out

    # ---------- evolution ----------
    def run(self, progress=None) -> SimResult:
        p = self.p
        p.validate()
        s = p.settings
        grid = self.build_grid()
        health = np.ones(grid.shape, dtype=float)
        dx = self.dx
        total = p.recipe.total_time_s
        n = max(2, s.n_frames)
        frame_times = np.linspace(0.0, total, n)
        sp = max(s.ion_spread_deg, 0.0)
        ion_ang = np.linspace(-sp, sp, 5) if sp > 0 else np.array([0.0])
        ion_w = np.exp(-0.5 * (ion_ang / (sp / 2 if sp > 0 else 1)) ** 2)
        neu_ang = np.linspace(-80, 80, 17)
        neu_w = np.cos(np.radians(neu_ang))
        load = loading_factor(s.wafer_open_fraction, s.loading_beta) if s.enable_loading else 1.0
        mask_top = self.ytop + p.mask.thickness_nm

        used_names = list(dict.fromkeys([l.material for l in p.stack.layers] + [p.mask.material]))
        rcache = {}
        frames = [Frame(0.0, self.surface_lines(grid, health), grid.copy(), self.depths(grid, health))]
        t = 0.0
        fi = 1
        while fi < n:
            step = p.recipe.step_at(min(t, total - 1e-9))
            if id(step) not in rcache:
                rcache[id(step)] = material_rates(step, p, used_names)
            rates = rcache[id(step)][0]
            R_ion = np.zeros(len(self.names))
            R_chem = np.zeros(len(self.names))
            for name, (ri, rc) in rates.items():
                if name in self.idx:
                    R_ion[self.idx[name]], R_chem[self.idx[name]] = ri * load, rc * load
            rmax = max(float((R_ion + R_chem).max()), 1e-9)
            dt = min(0.5 * dx / rmax, frame_times[fi] - t)
            gas = grid == 0
            nb = np.zeros_like(gas)
            nb[1:] |= gas[:-1]; nb[:-1] |= gas[1:]; nb[:, 1:] |= gas[:, :-1]; nb[:, :-1] |= gas[:, 1:]
            nb[0] |= True
            exposed = (~gas) & nb
            if exposed.any():
                Fi = _visibility(gas, ion_ang, ion_w)
                Fn = _visibility(gas, neu_ang, neu_w)
                # chemical attack also from lateral gas neighbours (isotropic): take max with side exposure
                side = np.zeros_like(gas)
                side[:, 1:] |= gas[:, :-1]; side[:, :-1] |= gas[:, 1:]
                Fn_side = np.zeros_like(Fn)
                Fn_side[:, 1:] = np.maximum(Fn_side[:, 1:], Fn[:, :-1] * gas[:, :-1])
                Fn_side[:, :-1] = np.maximum(Fn_side[:, :-1], Fn[:, 1:] * gas[:, 1:])
                Fn = np.maximum(Fn, 0.5 * Fn_side)
                rate = R_ion[grid] * Fi + R_chem[grid] * Fn
                if s.enable_arde:
                    W = gas_run_widths(gas, dx)
                    Wn = np.zeros_like(W)
                    Wn[1:] = np.maximum(Wn[1:], W[:-1]); Wn[:, 1:] = np.maximum(Wn[:, 1:], W[:, :-1])
                    Wn[:, :-1] = np.maximum(Wn[:, :-1], W[:, 1:])
                    depth = np.maximum(mask_top - self.yc, 0.0)[:, None]
                    AR = np.where(Wn > 0, depth / np.maximum(Wn, dx), 0.0)
                    rate = rate * arde_factor(AR, s.arde_alpha)
                health -= np.where(exposed, rate * dt / dx, 0.0)
                dead = exposed & (health <= 0)
                grid[dead] = 0
                health[dead] = 1.0
            t += dt
            if t >= frame_times[fi] - 1e-9:
                frames.append(Frame(float(frame_times[fi]), self.surface_lines(grid, health), grid.copy(),
                                    self.depths(grid, health)))
                fi += 1
                if progress:
                    progress(fi / n)
        rmeta = rate_meta([v[1] for v in rcache.values()], used_names)
        prov = rmeta["rate_sources"]
        lab = labels.label_for("demo", p.coefficients.calibrated, prov)
        return SimResult(frames, lab, self.names, (0.0, p.mask.domain_width_nm, 0.0, self.H),
                         {"backend": "demo", "grid_nm": dx, "loading_factor": load,
                          "arde": s.enable_arde,
                          "used_materials": used_names, **rmeta, "mask_top_nm": mask_top, "semiconductor_top_nm": self.ytop})


def run_project(project, progress=None) -> SimResult:
    """Entry point used by GUI/CLI: chooses backend from project.settings.backend."""
    if project.settings.backend == "viennaps":
        from .physics_backend_viennaps import run_with_fallback
        return run_with_fallback(project, progress)
    return DemoModel(project).run(progress)
