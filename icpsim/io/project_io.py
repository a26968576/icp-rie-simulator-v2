"""JSON project / recipe save & load.

Format version 3 stores ALL lengths in micrometers (keys ending in `_um`).
Version 2 files (lengths in nm, keys `_nm`) are still loaded transparently."""
from __future__ import annotations
import json
from ..core.project import Project
from ..core.recipe import Recipe
from ..core import labels

FORMAT = "icp-rie-sim-v2/project"
VERSION = 3


def _conv_keys(obj, to_um: bool):
    """Recursively rename *_nm <-> *_um and scale values."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if to_um and k.endswith("_nm") and isinstance(v, (int, float)):
                out[k[:-3] + "_um"] = v / 1000.0
            elif not to_um and k.endswith("_um") and isinstance(v, (int, float)):
                out[k[:-3] + "_nm"] = v * 1000.0
            else:
                out[k] = _conv_keys(v, to_um)
        return out
    if isinstance(obj, list):
        return [_conv_keys(x, to_um) for x in obj]
    return obj


def _coef_out(d):
    c = dict(d)
    for k in ("k_ion_nm_min", "k_chem_nm_min"):
        c[k.replace("_nm_min", "_um_min")] = c.pop(k) / 1000.0
    return c


def _coef_in(d):
    c = dict(d)
    for k in ("k_ion_um_min", "k_chem_um_min"):
        if k in c:
            c[k.replace("_um_min", "_nm_min")] = c.pop(k) * 1000.0
    return c


def project_to_json_dict(project: Project) -> dict:
    pd = project.to_dict()
    coef = _coef_out(pd.pop("coefficients"))
    pd = _conv_keys(pd, True)
    pd["coefficients"] = coef
    lab = labels.label_for(project.settings.backend, project.coefficients.calibrated)
    return {"format": FORMAT, "version": VERSION, "length_unit": "um", "rate_unit": "um/min",
            "model_label": lab, "model_label_text": labels.TEXT[lab], "project": pd}


def project_from_json_dict(d) -> Project:
    if d.get("format") != FORMAT:
        raise ValueError("Not an ICP-RIE Simulator V2 project file")
    pd = d["project"]
    if d.get("version", 2) >= 3:
        coef = _coef_in(pd.get("coefficients", {}))
        pd = _conv_keys({k: v for k, v in pd.items() if k != "coefficients"}, False)
        pd["coefficients"] = coef
    return Project.from_dict(pd)


def save_project(project: Project, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(project_to_json_dict(project), f, indent=2, ensure_ascii=False)


def load_project(path) -> Project:
    with open(path, encoding="utf-8") as f:
        return project_from_json_dict(json.load(f))


def save_recipe(recipe: Recipe, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"format": "icp-rie-sim-v2/recipe", **recipe.to_dict()}, f, indent=2)


def load_recipe(path) -> Recipe:
    with open(path, encoding="utf-8") as f:
        return Recipe.from_dict(json.load(f))
