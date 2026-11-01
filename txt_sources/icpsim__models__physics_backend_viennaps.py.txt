"""ViennaPS adapter (optional backend).

If the `viennaps` Python package (https://github.com/ViennaTools/ViennaPS) is importable,
`ViennaPSBackend.run()` builds a real 2D ViennaPS level-set domain from the project
(layer stack + mask with openings) and advances it with `DirectionalProcess`
(directional ion + isotropic chemical components per material).

IMPORTANT: ViennaPS gives a physics-based *surface evolution* (level sets, visibility),
but the per-material RATES fed to it come from the same DEMO coefficients
(or calibrated coefficients if the user ran calibration). Results are labelled
VIENNAPS_UNCALIBRATED / VIENNAPS_CALIBRATED accordingly.

If viennaps is missing or fails, `run_with_fallback()` falls back to the DEMO model and
records the reason in result.meta["fallback_reason"].
"""
from __future__ import annotations
import numpy as np
from ..core import labels
from ..core.frames import Frame, SimResult
from ..core.recipe import material_rates
from ..core.rate_sources import rate_meta

try:  # pragma: no cover - depends on environment
    import viennaps as _vps
    import viennals as _vls
    _IMPORT_ERROR = None
except Exception as e:  # noqa: BLE001
    _vps = None
    _vls = None
    _IMPORT_ERROR = repr(e)


def is_available() -> bool:
    return _vps is not None


def unavailable_reason():
    return _IMPORT_ERROR


_NAME_MAP = {"Sapphire": "Al2O3", "Photoresist": "PolySi"}  # nearest built-in tags (labels only)
_SPARE = ["Metal", "W", "Cu", "TiN", "Polymer", "Air", "Dielectric"]


def _vps_material(name, used):
    cand = _NAME_MAP.get(name, name)
    m = getattr(_vps.Material, cand, None)
    if m is None or m in used.values():
        for s in _SPARE:
            mm = getattr(_vps.Material, s, None)
            if mm is not None and mm not in used.values():
                m = mm
                break
    used[name] = m
    return m


class ViennaPSBackend:
    name = "viennaps"

    def __init__(self, project):
        self.p = project

    def _build(self):
        p = self.p
        vps, vls = _vps, _vls
        vps.setDimension(2)
        d2 = vps.d2
        vps.Logger.setLogLevel(vps.LogLevel.ERROR)
        um = 1e-3
        dx = p.settings.grid_nm * um
        W = p.mask.domain_width_nm * um
        H = (p.stack.total_thickness + p.mask.thickness_nm + p.settings.gas_headroom_nm) * um
        bc = [vls.BoundaryConditionEnum.REFLECTIVE_BOUNDARY, vls.BoundaryConditionEnum.INFINITE_BOUNDARY]
        bounds = [0.0, W, 0.0, H]
        dom = d2.Domain(bounds, bc, dx)
        used = {}
        y = 0.0
        for layer in p.stack.layers:
            y += layer.thickness_nm * um
            ls = vls.d2.Domain(bounds, bc, dx)
            vls.d2.MakeGeometry(ls, vls.d2.Plane([0.0, y], [0.0, 1.0])).apply()
            dom.insertNextLevelSetAsMaterial(ls, _vps_material(layer.material, used))
        # mask: blocks between openings on top of the stack
        ytop = y
        ymask = ytop + p.mask.thickness_nm * um
        spans = sorted(((o.center_nm - o.cd_nm / 2) * um, (o.center_nm + o.cd_nm / 2) * um) for o in p.mask.openings)
        edges = [0.0 - dx] + [v for s in spans for v in s] + [W + dx]
        mls = vls.d2.Domain(bounds, bc, dx)
        vls.d2.MakeGeometry(mls, vls.d2.Plane([0.0, ytop], [0.0, 1.0])).apply()
        for a, b in zip(edges[0::2], edges[1::2]):
            if b - a > dx * 0.5:
                box = vls.d2.Domain(bounds, bc, dx)
                vls.d2.MakeGeometry(box, vls.d2.Box([a, ytop - dx], [b, ymask])).apply()
                vls.d2.BooleanOperation(mls, box, vls.BooleanOperationEnum.UNION).apply()
        dom.insertNextLevelSetAsMaterial(mls, _vps_material(p.mask.material, used))
        return dom, used, ytop

    @staticmethod
    def _surface(dom):
        mesh = _vls.Mesh()
        _vls.ToSurfaceMesh(dom.getLevelSets()[-1], mesh).apply()
        nodes = np.asarray(mesh.getNodes())[:, :2] * 1e3
        lines = mesh.getLines()
        return [np.array([nodes[a], nodes[b]]) for a, b in lines], nodes

    def run(self, progress=None) -> SimResult:
        if not is_available():
            raise RuntimeError(f"viennaps not available: {_IMPORT_ERROR}")
        p = self.p
        p.validate()
        dom, used, ytop = self._build()
        d2 = _vps.d2
        total = p.recipe.total_time_s
        n = max(2, p.settings.n_frames)
        times = np.linspace(0, total, n)
        frames = []
        used_names = list(dict.fromkeys([l.material for l in p.stack.layers] + [p.mask.material]))
        rcache = {}
        segs, nodes = self._surface(dom)
        frames.append(Frame(0.0, segs, None, self._depths(nodes, ytop * 1e3)))
        for k in range(1, n):
            t0, t1 = times[k - 1], times[k]
            step = p.recipe.step_at(0.5 * (t0 + t1))
            if id(step) not in rcache:
                rcache[id(step)] = material_rates(step, p, used_names)
            rates = rcache[id(step)][0]
            # nm/s -> um/s ; with direction (0,-1,0) POSITIVE rates remove material (verified on viennaps 4.7)
            mrates = {}
            for name, m in used.items():
                ion, chem = rates.get(name, (0.0, 0.0))
                mrates[m] = (ion * 1e-3, chem * 1e-3)
            model = d2.DirectionalProcess([0.0, -1.0, 0.0], mrates, 0.0, 0.0)
            d2.Process(dom, model, float(t1 - t0)).apply()
            segs, nodes = self._surface(dom)
            frames.append(Frame(float(t1), segs, None, self._depths(nodes, ytop * 1e3)))
            if progress:
                progress(k / (n - 1))
        rmeta = rate_meta([v[1] for v in rcache.values()], used_names)
        prov = rmeta["rate_sources"]
        lab = labels.label_for("viennaps", p.coefficients.calibrated, prov)
        names = ["gas"] + [l.material for l in p.stack.layers] + [p.mask.material]
        ext = (0.0, p.mask.domain_width_nm, 0.0,
               p.stack.total_thickness + p.mask.thickness_nm + p.settings.gas_headroom_nm)
        return SimResult(frames, lab, names, ext, {"backend": "viennaps",
                                                   "viennaps_version": str(getattr(_vps, "__version__", "?")),
                                                   "material_tags": {k: str(v) for k, v in used.items()},
                                                   "used_materials": used_names, **rmeta})

    def _depths(self, nodes, ytop_nm):
        out = {}
        for i, o in enumerate(self.p.mask.openings):
            sel = np.abs(nodes[:, 0] - o.center_nm) < max(self.p.settings.grid_nm, 0.1 * o.cd_nm)
            out[i] = float(ytop_nm - nodes[sel, 1].min()) if sel.any() else 0.0
        return out


def run_with_fallback(project, progress=None) -> SimResult:
    """Try ViennaPS; on any problem fall back to the DEMO model and say so."""
    from .demo_model import DemoModel
    reason = None
    if is_available():
        try:
            return ViennaPSBackend(project).run(progress)
        except Exception as e:  # noqa: BLE001
            reason = f"ViennaPS run failed: {e!r}"
    else:
        reason = f"viennaps not installed ({_IMPORT_ERROR})"
    res = DemoModel(project).run(progress)
    res.meta["fallback_reason"] = reason
    res.meta["requested_backend"] = "viennaps"
    return res
