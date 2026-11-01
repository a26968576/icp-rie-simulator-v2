"""Mask geometry: a mask layer of given material/thickness with openings (CD)."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict


@dataclass
class Opening:
    center_nm: float
    cd_nm: float


@dataclass
class MaskGeometry:
    material: str = "SiO2"
    thickness_nm: float = 500.0
    domain_width_nm: float = 6000.0
    openings: list = field(default_factory=list)
    selectivity: float = 6.0  # target GaN : mask etch-rate ratio

    def validate(self):
        if self.selectivity <= 0:
            raise ValueError("Selectivity must be > 0")
        if self.thickness_nm <= 0:
            raise ValueError("Mask thickness must be > 0")
        spans = sorted((o.center_nm - o.cd_nm / 2, o.center_nm + o.cd_nm / 2) for o in self.openings)
        for a, b in spans:
            if a < 0 or b > self.domain_width_nm or b <= a:
                raise ValueError("Opening outside domain or CD <= 0")
        for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
            if a2 < b1:
                raise ValueError("Overlapping openings")

    def is_open(self, x_nm: float) -> bool:
        return any(abs(x_nm - o.center_nm) <= o.cd_nm / 2 for o in self.openings)

    def open_fraction(self) -> float:
        return sum(o.cd_nm for o in self.openings) / self.domain_width_nm

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        d = dict(d)
        d["openings"] = [Opening(**o) for o in d.get("openings", [])]
        return MaskGeometry(**d)
