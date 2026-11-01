"""Recipe steps and DEMO rate computation."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from . import gas_chemistry as gc


@dataclass
class RecipeStep:
    name: str = "Main etch"
    icp_power_w: float = 400.0
    rf_bias_w: float = 100.0
    pressure_mtorr: float = 5.0
    gases_sccm: dict = field(default_factory=lambda: {"Cl2": 25.0, "BCl3": 5.0})
    temperature_c: float = 20.0
    time_s: float = 180.0


@dataclass
class Recipe:
    steps: list = field(default_factory=list)

    @property
    def total_time_s(self):
        return sum(s.time_s for s in self.steps)

    def step_at(self, t: float):
        acc = 0.0
        for s in self.steps:
            acc += s.time_s
            if t < acc:
                return s
        return self.steps[-1]

    def to_dict(self):
        return {"steps": [asdict(s) for s in self.steps]}

    @staticmethod
    def from_dict(d):
        return Recipe([RecipeStep(**s) for s in d["steps"]])


@dataclass
class RateCoefficients:
    """DEMO base coefficients for GaN (nm/min at the reference recipe).
    `scale_*` are set by calibration (calibration.fit)."""
    k_ion_nm_min: float = 330.0
    k_chem_nm_min: float = 60.0
    ea_ev: float = 0.1
    scale_ion: float = 1.0
    scale_chem: float = 1.0
    calibrated: bool = False
    calibration_note: str = ""


def gan_rates(step: RecipeStep, coef: RateCoefficients):
    """(ion_directional, chemical_isotropic) GaN etch rates in nm/s on an open flat surface."""
    cl = gc.chlorine_index(step.gases_sccm)
    ion = coef.k_ion_nm_min * coef.scale_ion * gc.ion_flux_index(step.icp_power_w) * \
        gc.ion_energy_index(step.rf_bias_w, step.pressure_mtorr) * cl
    chem = coef.k_chem_nm_min * coef.scale_chem * gc.radical_index(step.icp_power_w, step.pressure_mtorr) * \
        cl * gc.arrhenius(step.temperature_c, coef.ea_ev)
    return ion / 60.0, chem / 60.0


def material_rates(step, project, names=None):
    """Per-material (ion, chem) etch rates in nm/s plus the rate-source Resolution.

    Total rate per material comes from rate_sources.resolve (user experimental > literature >
    mask-tab preset / DEMO factors). It is split into directional (ion) and isotropic (chem)
    parts: the DEMO isotropic (chemical) rate is kept when the material has factors and the rest is
    directional; materials without factors: masks 100 % directional, others 90 % directional."""
    from . import rate_sources as rs
    from .literature import get_active
    p = project
    coef = p.coefficients
    gi, gch = gan_rates(step, coef)
    names = list(names) if names is not None else list(p.materials)
    demo, demo_chem = {}, {}
    for n in names:
        m = p.materials.get(n)
        if m is not None and m.has_physics:
            i, c = gi * m.ion_factor, gch * m.chem_factor
            demo[n] = (i + c) * 60.0
            demo_chem[n] = c
    calibrated = {}
    if coef.calibrated and "GaN" in demo:
        calibrated["GaN"] = demo.pop("GaN")
    lit = get_active() if getattr(p.settings, "use_literature", True) else None
    top = p.stack.layers[-1].material if p.stack.layers else None
    res = rs.resolve(names, step.gases_sccm, p.user_rates, lit, demo, calibrated,
                     p.mask.material, top, p.mask.selectivity)
    out = {}
    for n in names:
        r = (res.rates[n].rate_nm_min or 0.0) / 60.0
        m = p.materials.get(n)
        if n in demo_chem:                       # keep DEMO isotropic part, rest is directional
            c = min(demo_chem[n], r)
        elif m is not None and m.is_mask:
            c = 0.0
        else:
            c = 0.1 * r
        out[n] = (r - c, c)
    return out, res
