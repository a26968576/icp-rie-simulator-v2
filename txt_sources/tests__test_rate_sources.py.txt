"""Gases, rate-source priority, selectivity, cycles, library IO, literature DB schema, zh UI."""
import json
import pytest
from icpsim.core import rate_sources as rs, labels, literature as lit
from icpsim.core.rate_sources import UserRateEntry, resolve
from icpsim.core.materials import Material, default_materials
from icpsim.core.project import gan_preset
from icpsim.core.recipe import material_rates
from icpsim.core import gas_chemistry as gc
from icpsim.io import material_library, project_io

GASES = ["CF4", "O2", "Ar", "BCl3", "Cl2", "N2"]


def test_known_gases():
    for g in GASES:
        assert g in gc.KNOWN_GASES


def test_selectivity_example_3_33():
    # user's definition: S = etched-target rate / mask rate ; resist 30 A/s, PDMS 100 A/s -> 3.33
    assert rs.selectivity(100, 30) == pytest.approx(3.333, abs=1e-3)
    res = resolve(["光阻1", "PDMS"], {"O2": 10, "CF4": 40},
                  [UserRateEntry("光阻1", "rate", 30, "A/s"),
                   UserRateEntry("PDMS", "selectivity", 100 / 30, reference="光阻1")])
    assert res.rates["PDMS"].rate_A_s == pytest.approx(100.0)
    assert res.rates["PDMS"].source == "experimental"
    M = rs.selectivity_matrix(res, ["PDMS", "光阻1"])
    assert M[0][1] == pytest.approx(3.33, abs=0.01) and M[1][0] == pytest.approx(0.3)
    # reverse direction: target known, mask derived
    res = resolve(["光阻1", "PDMS"], {"O2": 1}, [UserRateEntry("PDMS", "rate", 100, "A/s"),
                                                UserRateEntry("PDMS", "selectivity", 3.3333, reference="光阻1")])
    assert res.rates["光阻1"].rate_A_s == pytest.approx(30.0, rel=1e-3)


def test_units():
    assert rs.to_nm_min(30, "A/s") == pytest.approx(180)
    assert rs.to_nm_min(0.6, "um/min") == pytest.approx(600)
    assert rs.from_nm_min(180, "A/s") == pytest.approx(30)


def test_priority_user_over_literature():
    db = lit.LiteratureDB.load(lit.DEFAULT_DB_PATH)
    gases = {"Cl2": 25, "BCl3": 5}
    res = resolve(["GaN", "SiO2"], gases, [], db)
    assert res.rates["GaN"].source == "literature" and res.rates["SiO2"].source == "literature"
    res = resolve(["GaN", "SiO2"], gases, [UserRateEntry("GaN", "rate", 0.5, "um/min")], db)
    assert res.rates["GaN"].source == "experimental" and res.rates["GaN"].rate_nm_min == pytest.approx(500)
    # SiO2 still from literature selectivity chained to the user GaN rate
    assert res.rates["SiO2"].source == "experimental" or res.rates["SiO2"].source == "literature"
    # user selectivity beats literature selectivity
    res = resolve(["GaN", "SiO2"], gases, [UserRateEntry("GaN", "rate", 0.5, "um/min"),
                                           UserRateEntry("GaN", "selectivity", 10, reference="SiO2")], db)
    assert res.rates["SiO2"].rate_nm_min == pytest.approx(50) and res.rates["SiO2"].source == "experimental"
    # chemistry binding: a Cl2/BCl3-bound user value is not used for an O2 recipe
    res = resolve(["GaN"], {"O2": 5}, [UserRateEntry("GaN", "rate", 1, "um/min", chemistry="Cl2/BCl3")], db)
    assert res.rates["GaN"].source == "none" and res.warnings


def test_either_source_sufficient_and_no_data_warning():
    db = lit.LiteratureDB.load(lit.DEFAULT_DB_PATH)
    res = resolve(["Sapphire"], {"Cl2": 20, "BCl3": 80}, [], db)       # literature only
    assert res.rates["Sapphire"].source == "literature"
    res = resolve(["膠材"], {"Cl2": 20, "BCl3": 80}, [], db)            # nothing
    assert res.rates["膠材"].rate_nm_min is None and any("膠材" in w for w in res.warnings)


def test_cycle_detection():
    ents = [UserRateEntry("A", "selectivity", 2, reference="B"), UserRateEntry("B", "selectivity", 2, reference="C"),
            UserRateEntry("C", "selectivity", 2, reference="A")]
    res = resolve(["A", "B", "C"], {"O2": 1}, ents)
    assert res.cycles and not res.cycles[0][1]
    assert any("INCONSISTENT" in w for w in res.warnings)
    assert all(res.rates[n].source == "none" for n in "ABC")        # no absolute anchor
    ok = [UserRateEntry("A", "selectivity", 2, reference="B"), UserRateEntry("B", "selectivity", 2, reference="C"),
          UserRateEntry("A", "selectivity", 4, reference="C"), UserRateEntry("C", "rate", 1, "A/s")]
    res = resolve(["A", "B", "C"], {"O2": 1}, ok)
    assert res.cycles and res.cycles[0][1]
    assert res.rates["A"].rate_A_s == pytest.approx(4)


def test_literature_db_schema():
    raw = json.loads(lit.DEFAULT_DB_PATH.read_text(encoding="utf-8"))
    assert raw["format"] == lit.FORMAT and len(raw["entries"]) >= 30
    for e in raw["entries"]:
        assert lit.validate_entry(e) == [], e["id"]
        s = e["source"]
        assert s["authors"] and s["title"] and (s["doi"] or s["url"])
        assert isinstance(e["conditions"], dict) and e["gases"]
    ids = [e["id"] for e in raw["entries"]]
    assert len(ids) == len(set(ids))
    mats = lit.LiteratureDB.load(lit.DEFAULT_DB_PATH).materials()
    for m in ("GaN", "SiO2", "Si3N4", "Si", "Photoresist", "PDMS", "Polyimide", "SU-8", "Sapphire", "Ni"):
        assert m in mats


def test_literature_db_save_load(tmp_path):
    db = lit.LiteratureDB.load(lit.DEFAULT_DB_PATH)
    db.entries[0]["rate_nm_min"] = 123.0
    p = db.save(tmp_path / "db.json")
    assert lit.LiteratureDB.load(p).entries[0]["rate_nm_min"] == 123.0


def test_library_io(tmp_path):
    mats = default_materials()
    mats["光阻1"] = Material("光阻1", "#c77dbb", None, None, True)
    ents = [UserRateEntry("光阻1", "rate", 30, "A/s"), UserRateEntry("PDMS", "selectivity", 3.33, reference="光阻1")]
    f = tmp_path / "lib.json"
    material_library.save_library(f, mats, ents)
    m2, e2 = material_library.load_library(f)
    assert m2["光阻1"].ion_factor is None and m2["光阻1"].is_mask and not m2["光阻1"].has_physics
    assert e2 == ents
    assert "光阻1" in f.read_text(encoding="utf-8")


def test_project_roundtrip_with_user_rates(tmp_path):
    p = gan_preset()
    p.materials["光阻1"] = Material("光阻1", is_mask=True)
    p.user_rates = [UserRateEntry("光阻1", "rate", 30, "A/s")]
    project_io.save_project(p, tmp_path / "p.json")
    q = project_io.load_project(tmp_path / "p.json")
    assert q.user_rates == p.user_rates and q.materials["光阻1"].ion_factor is None


def _custom_project(backend="demo"):
    p = gan_preset()
    p.settings.grid_nm = 50.0
    p.settings.n_frames = 4
    p.recipe.steps[0].time_s = 30.0
    p.settings.backend = backend
    p.materials["光阻1"] = Material("光阻1", "#c77dbb", None, None, True)
    p.mask.material = "光阻1"
    p.user_rates = [UserRateEntry("光阻1", "rate", 30, "A/s"), UserRateEntry("GaN", "rate", 0.6, "um/min"),
                    UserRateEntry("Sapphire", "rate", 0.1, "um/min")]
    return p


def test_labels_experimental_literature_demo():
    from icpsim.models.demo_model import run_project
    r = run_project(_custom_project())
    assert r.label == labels.EXPERIMENTAL and r.meta["rate_sources"]["光阻1"] == "experimental"
    p = _custom_project()
    p.user_rates = p.user_rates[:1]
    r = run_project(p)
    assert r.label == labels.LITERATURE and r.meta["rate_sources"]["GaN"] == "literature"
    p.settings.use_literature = False
    r = run_project(p)
    assert r.label == labels.DEMO and r.meta["rate_sources"]["GaN"] == "demo"
    rates, _ = material_rates(p.recipe.steps[0], p)
    assert sum(rates["光阻1"]) * 60 == pytest.approx(180)


def test_viennaps_backend_uses_rate_sources():
    pytest.importorskip("viennaps")
    from icpsim.models.demo_model import run_project
    r = run_project(_custom_project("viennaps"))
    assert r.meta["backend"] == "viennaps", r.meta.get("fallback_reason")
    assert r.label == labels.VIENNAPS_EXP
    d = r.frames[-1].depth_nm[0]
    assert d == pytest.approx(300, rel=0.25)        # 0.6 um/min * 30 s


def test_zh_labels_and_i18n():
    from icpsim import i18n
    assert i18n.tr("mask_thickness") == "光罩厚度 (Mask Thickness)"
    assert i18n.tr("hdr_bias").startswith("偏壓功率") and "RF Bias" in i18n.tr("hdr_bias")
    assert i18n.tr("run") == "開始模擬 (Run Simulation)"
    for k, (zh, en) in i18n.S.items():
        assert zh and en, k
    i18n.set_language("en")
    assert i18n.tr("run") == "Run Simulation"
    i18n.set_language("zh")
