import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from icpsim.core.project import gan_preset


@pytest.fixture
def project():
    p = gan_preset("SiO2")
    p.settings.grid_nm = 50.0
    p.settings.n_frames = 8
    p.recipe.steps[0].time_s = 60.0
    p.settings.use_literature = False   # pure DEMO-model tests (literature tested in test_rate_sources)
    return p


@pytest.fixture(autouse=True)
def _zh_language():
    from icpsim import i18n
    i18n.set_language("zh")
    yield
    i18n.set_language("zh")
