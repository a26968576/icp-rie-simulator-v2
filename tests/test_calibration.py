import pytest
from icpsim.calibration import fit as cal
from icpsim.core.recipe import gan_rates
from icpsim.models.demo_model import run_project
from icpsim.core import labels


def _write(tmp_path, rows, header="time_s,depth_nm"):
    p = tmp_path / "exp.csv"
    p.write_text("# comment\n" + header + "\n" + "\n".join(",".join(map(str, r)) for r in rows))
    return p


def test_linear_fit(tmp_path, project):
    path = _write(tmp_path, [(30, 150), (60, 300), (120, 600)])  # 300 nm/min
    res = cal.fit_csv(path, project)
    assert res.rate_nm_min == pytest.approx(300, rel=1e-6)
    assert res.r2 == pytest.approx(1.0)
    cal.apply_calibration(project, res, str(path))
    gi, gc = gan_rates(project.recipe.steps[0], project.coefficients)
    assert (gi + gc) * 60 == pytest.approx(300, rel=1e-6)  # loading factor 1 at reference
    r = run_project(project)
    assert r.label == labels.CALIBRATED
    cal.reset_calibration(project)
    assert not project.coefficients.calibrated


def test_um_csv(tmp_path, project):
    path = _write(tmp_path, [(30, 0.15), (60, 0.30), (120, 0.60)], "time_s,depth_um")
    res = cal.fit_csv(path, project)
    assert res.rate_um_min == pytest.approx(0.3, rel=1e-6)
    assert "um/min" in res.summary()


def test_example_csv(project):
    import os
    ex = os.path.join(os.path.dirname(__file__), "..", "examples", "gan_experiment_example.csv")
    assert 0.3 < cal.fit_csv(ex, project).rate_um_min < 0.5


def test_arde_fit(tmp_path, project):
    rows = []
    alpha, R0 = 0.1, 6.0  # nm/s
    for cd in (2000, 500):
        for t in (30, 60, 90):
            d = R0 * t / (1 + alpha * (R0 * 60 / cd))  # mean depth ~ R0*60
            rows.append((t, d, cd))
    res = cal.fit_rows([(a, b, c) for a, b, c in rows], project)
    assert res.arde_alpha is not None and res.arde_alpha > 0
    assert len(res.per_cd_rates) == 2


def test_bad_csv(tmp_path, project):
    with pytest.raises(ValueError):
        cal.fit_csv(_write(tmp_path, [(1, 2), (2, 3)], "a,b"), project)
    with pytest.raises(ValueError):
        cal.fit_csv(_write(tmp_path, [(1, 2)]), project)
