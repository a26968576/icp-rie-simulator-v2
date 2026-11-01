import pytest
from icpsim.core import labels, gas_chemistry as gc
from icpsim.core.recipe import gan_rates, material_rates, RateCoefficients, RecipeStep, Recipe
from icpsim.core.mask import MaskGeometry, Opening
from icpsim.core.project import gan_preset, Project


def test_preset_valid():
    for m in ("SiO2", "Photoresist"):
        p = gan_preset(m)
        p.validate()
        assert p.mask.material == m and "GaN" in [l.material for l in p.stack.layers]
        assert p.recipe.steps[0].gases_sccm == {"Cl2": 25.0, "BCl3": 5.0}


def test_rates_trends():
    c = RateCoefficients()
    base = RecipeStep()
    i0, c0 = gan_rates(base, c)
    assert i0 > 0 and c0 > 0
    hi_bias = RecipeStep(rf_bias_w=200)
    assert gan_rates(hi_bias, c)[0] > i0
    hi_icp = RecipeStep(icp_power_w=800)
    assert gan_rates(hi_icp, c)[1] > c0
    total_min = (i0 + c0) * 60
    assert 100 < total_min < 1500  # plausible demo order of magnitude


def test_selectivity():
    p = gan_preset()
    p.settings.use_literature = False
    p.mask.selectivity = 5.0
    r, res = material_rates(p.recipe.steps[0], p)
    assert sum(r["GaN"]) / sum(r["SiO2"]) == pytest.approx(5.0)
    assert res.rates["SiO2"].source == "preset" and res.rates["GaN"].source == "demo"


def test_mask_validation():
    m = MaskGeometry(openings=[Opening(1000, 500), Opening(1200, 500)])
    with pytest.raises(ValueError):
        m.validate()
    m = MaskGeometry(domain_width_nm=1000, openings=[Opening(500, 200)])
    m.validate()
    assert m.is_open(500) and not m.is_open(50)
    assert m.open_fraction() == pytest.approx(0.2)


def test_recipe_step_at():
    r = Recipe([RecipeStep("a", time_s=10), RecipeStep("b", time_s=5)])
    assert r.total_time_s == 15
    assert r.step_at(3).name == "a" and r.step_at(12).name == "b" and r.step_at(99).name == "b"


def test_labels():
    assert labels.label_for("demo", False) == labels.DEMO
    assert labels.label_for("demo", True) == labels.CALIBRATED
    assert labels.label_for("viennaps", False) == labels.VIENNAPS_UNCAL
    assert "UNCALIBRATED" in labels.TEXT[labels.DEMO]
    assert not labels.is_calibrated(labels.VIENNAPS_UNCAL)


def test_project_roundtrip_dict():
    p = gan_preset()
    q = Project.from_dict(p.to_dict())
    assert q.to_dict() == p.to_dict()


def test_gas_chem():
    assert gc.chlorine_index({}) == 0
    assert gc.chlorine_index({"Cl2": 30}) > gc.chlorine_index({"Cl2": 10, "Ar": 20})
    assert gc.arrhenius(20) == pytest.approx(1.0)
