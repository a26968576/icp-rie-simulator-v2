"""Material definitions (relative etch factors are DEMO-model inputs)."""
from __future__ import annotations
from dataclasses import dataclass, asdict


@dataclass
class Material:
    name: str
    color: str = "#888888"
    ion_factor: float | None = None   # DEMO: relative ion-assisted yield vs GaN (None = unknown)
    chem_factor: float | None = None  # DEMO: relative chemical reactivity vs GaN (None = unknown)
    is_mask: bool = False
    note: str = ""

    @property
    def has_physics(self) -> bool:
        return self.ion_factor is not None and self.chem_factor is not None

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Material(**{k: v for k, v in d.items() if k in Material.__dataclass_fields__})


def default_materials() -> dict:
    mats = [
        Material("GaN", "#4f7fbf", 1.0, 1.0),
        Material("AlGaN", "#7aa6d6", 0.8, 0.6),
        Material("Sapphire", "#d9c27a", 0.02, 0.0),
        Material("Si", "#9e9e9e", 1.2, 1.5),
        Material("SiO2", "#e0e0e0", 0.15, 0.0, True),
        Material("Photoresist", "#c77dbb", 0.5, 0.1, True),
        Material("Si3N4", "#b0bec5", 0.2, 0.0, True),
        Material("Ni", "#707070", 0.02, 0.0, True),
    ]
    # user-style materials without physical parameters (rates come from data only)
    mats += [Material("PDMS", "#9ccc65"), Material("Polyimide", "#ffb74d", is_mask=True),
             Material("SU-8", "#80cbc4", is_mask=True), Material("Cr", "#5d4037", is_mask=True)]
    return {m.name: m for m in mats}
