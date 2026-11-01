"""Material definitions (relative etch factors are DEMO-model inputs)."""
from __future__ import annotations
from dataclasses import dataclass, asdict


@dataclass
class Material:
    name: str
    color: str = "#888888"
    ion_factor: float = 1.0      # relative ion-assisted (directional) etch yield vs GaN
    chem_factor: float = 1.0     # relative chemical (isotropic) reactivity vs GaN
    is_mask: bool = False

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Material(**d)


def default_materials() -> dict:
    mats = [
        Material("GaN", "#4f7fbf", 1.0, 1.0),
        Material("AlGaN", "#7aa6d6", 0.8, 0.6),
        Material("Sapphire", "#d9c27a", 0.02, 0.0),
        Material("Si", "#9e9e9e", 1.2, 1.5),
        Material("SiO2", "#e0e0e0", 0.15, 0.0, True),
        Material("Photoresist", "#c77dbb", 0.5, 0.1, True),
        Material("SiN", "#b0bec5", 0.2, 0.0, True),
        Material("Ni", "#707070", 0.02, 0.0, True),
    ]
    return {m.name: m for m in mats}
