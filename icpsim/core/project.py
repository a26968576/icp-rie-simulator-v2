"""Project = everything needed to run a simulation; plus the GaN validation preset."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from .materials import Material, default_materials
from .layer_stack import LayerStack, Layer
from .mask import MaskGeometry, Opening
from .rate_sources import UserRateEntry
from .recipe import Recipe, RecipeStep, RateCoefficients


@dataclass
class SimSettings:
    grid_nm: float = 25.0
    gas_headroom_nm: float = 500.0
    n_frames: int = 60
    ion_spread_deg: float = 4.0
    backend: str = "demo"          # "demo" | "viennaps"
    enable_arde: bool = True
    arde_alpha: float = 0.08
    enable_loading: bool = True
    loading_beta: float = 0.3
    wafer_open_fraction: float = 0.2
    use_literature: bool = True    # use literature DB when no user data


@dataclass
class Project:
    name: str = "project"
    materials: dict = field(default_factory=default_materials)
    stack: LayerStack = field(default_factory=LayerStack)
    mask: MaskGeometry = field(default_factory=MaskGeometry)
    recipe: Recipe = field(default_factory=Recipe)
    coefficients: RateCoefficients = field(default_factory=RateCoefficients)
    settings: SimSettings = field(default_factory=SimSettings)
    user_rates: list = field(default_factory=list)   # [rate_sources.UserRateEntry]

    def validate(self):
        self.stack.validate(self.materials)
        self.mask.validate()
        if self.mask.material not in self.materials:
            raise ValueError("Unknown mask material")
        if not self.recipe.steps:
            raise ValueError("Recipe has no steps")

    def to_dict(self):
        return {
            "name": self.name,
            "materials": {k: v.to_dict() for k, v in self.materials.items()},
            "stack": self.stack.to_dict(),
            "mask": self.mask.to_dict(),
            "recipe": self.recipe.to_dict(),
            "coefficients": asdict(self.coefficients),
            "settings": asdict(self.settings),
            "user_rates": [u.to_dict() for u in self.user_rates],
        }

    @staticmethod
    def from_dict(d):
        return Project(
            name=d.get("name", "project"),
            materials=_load_materials(d["materials"]),
            stack=LayerStack.from_dict(d["stack"]),
            mask=MaskGeometry.from_dict(d["mask"]),
            recipe=Recipe.from_dict(d["recipe"]),
            coefficients=RateCoefficients(**d.get("coefficients", {})),
            settings=SimSettings(**d.get("settings", {})),
            user_rates=[UserRateEntry.from_dict(u) for u in d.get("user_rates", [])],
        )


def gan_preset(mask_material: str = "SiO2") -> Project:
    """First validation case: GaN on sapphire, SiO2 or photoresist mask, Cl2/BCl3 ICP-RIE.
    Recipe values are in a typical literature range; DEMO output is illustrative only."""
    sio2 = mask_material == "SiO2"
    return Project(
        name=f"GaN Cl2/BCl3 ICP-RIE ({mask_material} mask) - validation preset",
        stack=LayerStack([Layer("Sapphire", 500.0), Layer("GaN", 2500.0)]),
        mask=MaskGeometry(material=mask_material, thickness_nm=500.0 if sio2 else 1200.0,
                          domain_width_nm=6000.0,
                          openings=[Opening(1500.0, 2000.0), Opening(4400.0, 500.0)],
                          selectivity=6.0 if sio2 else 1.5),
        recipe=Recipe([RecipeStep("Main etch", 400.0, 100.0, 5.0, {"Cl2": 25.0, "BCl3": 5.0}, 20.0, 180.0)]),
    )


def _load_materials(d):
    mats = {}
    for k, v in d.items():
        if k == "SiN":                       # v2 name
            k = "Si3N4"; v = dict(v, name="Si3N4")
        mats[k] = Material.from_dict(v)
    return mats
