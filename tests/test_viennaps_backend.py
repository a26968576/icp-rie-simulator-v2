import pytest
from icpsim.core import labels
from icpsim.models import physics_backend_viennaps as vb
from icpsim.models.demo_model import run_project


def test_fallback_when_unavailable(project, monkeypatch):
    monkeypatch.setattr(vb, "_vps", None)
    monkeypatch.setattr(vb, "_IMPORT_ERROR", "ImportError('simulated')")
    project.settings.backend = "viennaps"
    r = run_project(project)
    assert r.label == labels.DEMO
    assert "not installed" in r.meta["fallback_reason"]
    with pytest.raises(RuntimeError):
        vb.ViennaPSBackend(project).run()


@pytest.mark.skipif(not vb.is_available(), reason="viennaps not installed")
def test_real_viennaps(project):
    project.settings.backend = "viennaps"
    r = run_project(project)
    assert r.meta["backend"] == "viennaps"
    assert r.label == labels.VIENNAPS_UNCAL
    d = r.frames[-1].depth_nm[0]
    assert d > 50
    # mask region stays (surface max near mask top)
    import numpy as np
    ys = np.concatenate([s[:, 1] for s in r.frames[-1].surface])
    assert ys.max() > project.stack.total_thickness
