"""Very simple, ILLUSTRATIVE plasma/gas chemistry descriptors (DEMO model).

These proxies are NOT a plasma model; they only give plausible trends:
- more ICP power  -> more ions and Cl radicals
- more RF bias    -> higher ion energy (directional component)
- small BCl3 fraction -> helps remove native oxide; large fraction dilutes Cl supply
- higher pressure -> more neutrals, less directional ions
"""
from __future__ import annotations
import math

KNOWN_GASES = ["Cl2", "BCl3", "Ar", "N2", "SF6", "O2", "CHF3", "HBr"]


def chlorine_index(gases: dict) -> float:
    total = sum(v for v in gases.values() if v > 0)
    if total <= 0:
        return 0.0
    x = gases.get("Cl2", 0.0) / total
    b = gases.get("BCl3", 0.0) / total
    return x * (1.0 + 0.6 * b) + 0.3 * b


def ion_energy_index(bias_w: float, pressure_mtorr: float) -> float:
    return math.sqrt(max(bias_w, 0.0) / 100.0) / (1.0 + 0.02 * max(pressure_mtorr - 5.0, 0.0))


def ion_flux_index(icp_w: float) -> float:
    return math.sqrt(max(icp_w, 0.0) / 400.0)


def radical_index(icp_w: float, pressure_mtorr: float) -> float:
    return (max(icp_w, 0.0) / 400.0) * math.sqrt(max(pressure_mtorr, 0.1) / 5.0)


def arrhenius(temp_c: float, ea_ev: float = 0.1, ref_c: float = 20.0) -> float:
    k = 8.617e-5
    return math.exp(-ea_ev / k * (1.0 / (temp_c + 273.15) - 1.0 / (ref_c + 273.15)))
