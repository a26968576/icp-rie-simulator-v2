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


def material_rates(step, coef, materials, mask_material: str, selectivity: float):
    """nm/s (ion, chem) per material name. Mask material rate = GaN rate / selectivity."""
    gi, gch = gan_rates(step, coef)
    out = {name: (gi * m.ion_factor, gch * m.chem_factor) for name, m in materials.items()}
    out[mask_material] = (gi / selectivity, gch / selectivity)
    return out
