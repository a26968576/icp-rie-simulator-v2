import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from icpsim.io import project_io, export
from icpsim.models.demo_model import run_project
from icpsim.core.recipe import Recipe, RecipeStep


def test_project_json(tmp_path, project):
    path = tmp_path / "p.json"
    project_io.save_project(project, path)
    d = json.loads(path.read_text(encoding="utf-8"))
    assert d["model_label"] == "DEMO" and "UNCALIBRATED" in d["model_label_text"]
    assert d["length_unit"] == "um" and d["version"] == 3
    assert d["project"]["mask"]["thickness_um"] == 0.5
    assert d["project"]["mask"]["openings"][1]["cd_um"] == 0.5
    assert d["project"]["stack"]["layers"][1]["thickness_um"] == 2.5
    q = project_io.load_project(path)
    import pytest
    assert q.mask.thickness_nm == pytest.approx(project.mask.thickness_nm)
    assert q.stack.total_thickness == pytest.approx(project.stack.total_thickness)
    assert q.coefficients.k_ion_nm_min == pytest.approx(project.coefficients.k_ion_nm_min)
    assert q.settings.grid_nm == pytest.approx(project.settings.grid_nm)


def test_load_legacy_v2_nm_json(tmp_path, project):
    """Backward compatibility: version-2 files stored lengths in nm."""
    path = tmp_path / "old.json"
    path.write_text(json.dumps({"format": project_io.FORMAT, "version": 2, "project": project.to_dict()}))
    q = project_io.load_project(path)
    assert q.to_dict() == project.to_dict()


def test_recipe_json(tmp_path):
    r = Recipe([RecipeStep("x", time_s=7)])
    project_io.save_recipe(r, tmp_path / "r.json")
    assert project_io.load_recipe(tmp_path / "r.json").steps[0].time_s == 7


def test_csv_png(tmp_path, project):
    res = run_project(project)
    c = tmp_path / "prof.csv"
    export.export_profile_csv(res, c, -1, project)
    txt = c.read_text(encoding="utf-8")
    assert "# model_label: DEMO" in txt and "x_um,y_um" in txt and "depth_um_per_opening" in txt
    ys = [float(l.split(",")[2]) for l in txt.splitlines()[1:] if l and not l.startswith("#") and l[0].isdigit()]
    assert max(ys) < 10  # micrometers, not nm
    assert len(txt.splitlines()) > 20
    fig = plt.figure()
    png = tmp_path / "p.png"
    export.export_png(fig, png, res, project)
    assert png.read_bytes()[:4] == b"\x89PNG"
    from PIL import Image
    assert "DEMO" in Image.open(png).info.get("Description", "")
