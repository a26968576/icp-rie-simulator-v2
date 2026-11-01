"""ARDE (aspect-ratio-dependent etching, 'RIE lag'), DEMO empirical form:
rate(AR) = rate0 / (1 + alpha * AR).  Applied per surface cell in the demo model,
on top of the geometric shadowing that the visibility calculation already gives."""
import numpy as np


def arde_factor(aspect_ratio, alpha: float = 0.08):
    ar = np.maximum(np.asarray(aspect_ratio, dtype=float), 0.0)
    return 1.0 / (1.0 + alpha * ar)


def gas_run_widths(gas: np.ndarray, dx: float) -> np.ndarray:
    """For each gas cell, width (nm) of the horizontal gas run it belongs to; 0 for solid."""
    ny, nx = gas.shape
    W = np.zeros(gas.shape, dtype=float)
    for j in range(ny):
        row = gas[j]
        if row.all():
            W[j] = nx * dx
            continue
        d = np.diff(np.concatenate(([0], row.astype(np.int8), [0])))
        starts = np.flatnonzero(d == 1)
        ends = np.flatnonzero(d == -1)
        for a, b in zip(starts, ends):
            W[j, a:b] = (b - a) * dx
    return W
