import numpy as np
from icpsim.core import labels
from icpsim.models.demo_model import DemoModel, run_project
from icpsim.extensions.arde import arde_factor, gas_run_widths
from icpsim.extensions.loading import loading_factor


def test_run_basic(project):
    r = DemoModel(project).run()
    assert r.label == labels.DEMO
    assert len(r.frames) == 8
    assert r.frames[0].time_s == 0 and abs(r.frames[-1].time_s - 60) < 1e-6
    d = [f.depth_nm[0] for f in r.frames]
    assert d[0] == 0 and all(b >= a - 1e-9 for a, b in zip(d, d[1:])) and d[-1] > 50
    assert all(len(f.surface) > 0 for f in r.frames)


def test_mask_protects(project):
    m = DemoModel(project)
    r = m.run()
    g0, g1 = r.frames[0].grid, r.frames[-1].grid
    gan = m.idx["GaN"]
    # GaN under the mask far from openings is intact
    col = int(3300 / m.dx)
    assert (g1[:, col] == gan).sum() == (g0[:, col] == gan).sum()


def test_arde_reduces_narrow(project):
    project.recipe.steps[0].time_s = 120
    r = DemoModel(project).run()
    wide, narrow = r.frames[-1].depth_nm[0], r.frames[-1].depth_nm[1]
    assert narrow < wide


def test_extensions():
    assert arde_factor(0) == 1 and arde_factor(5, 0.1) < 1
    assert loading_factor(0.2, 0.3) == 1.0 and loading_factor(0.8, 0.3) < 1.0
    g = np.array([[1, 1, 0, 1]], bool)
    assert list(gas_run_widths(g, 10)[0]) == [20, 20, 0, 10]


def test_calibrated_label(project):
    project.coefficients.calibrated = True
    assert run_project(project).label == labels.CALIBRATED


def test_selectivity_affects_mask(project):
    project.recipe.steps[0].time_s = 120
    m = DemoModel(project)
    project.mask.selectivity = 1.0
    r1 = m.run()
    project.mask.selectivity = 20.0
    r2 = DemoModel(project).run()
    mi = m.idx["SiO2"]
    assert (r1.frames[-1].grid == mi).sum() < (r2.frames[-1].grid == mi).sum()
