"""Calibration: fit rate coefficients from user experimental etch depth vs time.

CSV format (header required, '#' comment lines allowed):
    time_s,depth_um[,cd_um]      (micrometers, preferred)
    time_s,depth_nm[,cd_nm]      (nanometers, also accepted)
- Without cd_nm: linear fit depth = R*t + d0 -> GaN open-area rate R (nm/min).
- With several cd_nm values: per-CD rates are fitted, R0 and ARDE alpha are obtained from
  1/R = 1/R0 + (alpha/R0) * (mean_depth/CD).
The demo model's flat-surface rate for the chosen recipe step is then scaled to match R0.
A single recipe point cannot separate ion vs chemical parts, so both are scaled equally.
"""
from __future__ import annotations
import csv
from dataclasses import dataclass, field
import numpy as np
from ..core.recipe import gan_rates
from ..extensions.loading import loading_factor


@dataclass
class CalibrationResult:
    # internal values in nm; use the *_um properties for display
    rate_nm_min: float
    offset_nm: float
    r2: float
    n_points: int
    scale: float
    model_rate_nm_min: float
    arde_alpha: float | None = None
    per_cd_rates: dict = field(default_factory=dict)

    @property
    def rate_um_min(self):
        return self.rate_nm_min / 1000.0

    def summary(self):
        s = (f"Fitted GaN rate R0 = {self.rate_nm_min / 1000:.4f} um/min (offset {self.offset_nm / 1000:.4f} um, "
             f"R^2 = {self.r2:.4f}, n = {self.n_points}); demo model predicted {self.model_rate_nm_min / 1000:.4f} "
             f"um/min -> scale x{self.scale:.3f}")
        if self.arde_alpha is not None:
            s += f"; ARDE alpha = {self.arde_alpha:.4f}"
        return s


def read_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        lines = [l for l in f if l.strip() and not l.lstrip().startswith("#")]
    reader = csv.DictReader(lines)
    for r in reader:
        r = {k.strip().lower(): v for k, v in r.items() if k}
        if "time_s" not in r or not ("depth_um" in r or "depth_nm" in r):
            raise ValueError("CSV needs columns time_s, depth_um [, cd_um]  (or depth_nm/cd_nm)")
        depth = float(r["depth_um"]) * 1000.0 if "depth_um" in r else float(r["depth_nm"])
        cd = None
        if r.get("cd_um") not in (None, ""):
            cd = float(r["cd_um"]) * 1000.0
        elif r.get("cd_nm") not in (None, ""):
            cd = float(r["cd_nm"])
        rows.append((float(r["time_s"]), depth, cd))
    if len(rows) < 2:
        raise ValueError("Need at least 2 data points")
    return rows


def linear_fit(t, d):
    t = np.asarray(t, float); d = np.asarray(d, float)
    A = np.vstack([t, np.ones_like(t)]).T
    (k, b), *_ = np.linalg.lstsq(A, d, rcond=None)
    pred = A @ np.array([k, b])
    ss = float(np.sum((d - d.mean()) ** 2))
    r2 = 1.0 - float(np.sum((d - pred) ** 2)) / ss if ss > 0 else 1.0
    return float(k), float(b), r2


def fit_rows(rows, project, step_index=0) -> CalibrationResult:
    cds = sorted({r[2] for r in rows if r[2] is not None})
    alpha = None
    per = {}
    if len(cds) >= 2:
        xs, inv = [], []
        r2s = []
        for cd in cds:
            sub = [r for r in rows if r[2] == cd]
            k, b, r2 = linear_fit([r[0] for r in sub], [r[1] for r in sub])
            per[cd] = k * 60.0
            r2s.append(r2)
            xs.append(np.mean([r[1] for r in sub]) / cd)
            inv.append(1.0 / k)
        slope, icpt, _ = linear_fit(xs, inv)
        R0 = 60.0 / icpt
        alpha = max(slope / icpt, 0.0)
        offset, r2 = 0.0, float(np.mean(r2s))
    else:
        k, offset, r2 = linear_fit([r[0] for r in rows], [r[1] for r in rows])
        R0 = k * 60.0
    if R0 <= 0:
        raise ValueError("Fitted rate is not positive - check data")
    step = project.recipe.steps[step_index]
    c = project.coefficients
    base = type(c)(**{**c.__dict__, "scale_ion": 1.0, "scale_chem": 1.0})
    gi, gc_ = gan_rates(step, base)
    s = project.settings
    load = loading_factor(s.wafer_open_fraction, s.loading_beta) if s.enable_loading else 1.0
    model = (gi + gc_) * 60.0 * load
    return CalibrationResult(R0, offset, r2, len(rows), R0 / model, model, alpha, per)


def fit_csv(path, project, step_index=0) -> CalibrationResult:
    return fit_rows(read_csv(path), project, step_index)


def apply_calibration(project, result: CalibrationResult, source: str = ""):
    c = project.coefficients
    c.scale_ion = c.scale_chem = result.scale
    c.calibrated = True
    c.calibration_note = f"{result.summary()} [source: {source}]"
    if result.arde_alpha is not None:
        project.settings.arde_alpha = result.arde_alpha
    return project


def reset_calibration(project):
    c = project.coefficients
    c.scale_ion = c.scale_chem = 1.0
    c.calibrated = False
    c.calibration_note = ""
