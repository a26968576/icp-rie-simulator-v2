"""Material library JSON: materials (physical factors optional) + user experimental rates/selectivities."""
from __future__ import annotations
import json
from ..core.materials import Material
from ..core.rate_sources import UserRateEntry

FORMAT = "icp-rie-sim-v2/material-library"


def library_dict(materials: dict, user_rates: list) -> dict:
    return {"format": FORMAT, "version": 1,
            "selectivity_definition": "S = R_target / R_mask (target = material, mask = reference)",
            "materials": [m.to_dict() for m in materials.values()],
            "user_rates": [u.to_dict() for u in user_rates]}


def save_library(path, materials: dict, user_rates: list):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(library_dict(materials, user_rates), f, indent=2, ensure_ascii=False)


def load_library(path):
    """Returns (materials dict, user_rates list)."""
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("format") != FORMAT:
        raise ValueError("Not a material library file")
    mats = {m["name"]: Material.from_dict(m) for m in d.get("materials", [])}
    return mats, [UserRateEntry.from_dict(u) for u in d.get("user_rates", [])]
