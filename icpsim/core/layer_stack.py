"""Layer stack (listed bottom -> top, excluding the mask)."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict


@dataclass
class Layer:
    material: str
    thickness_nm: float


@dataclass
class LayerStack:
    layers: list = field(default_factory=list)

    @property
    def total_thickness(self) -> float:
        return sum(l.thickness_nm for l in self.layers)

    def validate(self, materials):
        for l in self.layers:
            if l.material not in materials:
                raise ValueError(f"Unknown material {l.material!r}")
            if l.thickness_nm <= 0:
                raise ValueError("Layer thickness must be > 0")

    def to_dict(self):
        return {"layers": [asdict(l) for l in self.layers]}

    @staticmethod
    def from_dict(d):
        return LayerStack([Layer(**l) for l in d["layers"]])
