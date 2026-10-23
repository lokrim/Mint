"""E1: rule R1 (Wilson resolvability) and the tile gather/scatter used by the footprint mode."""
import os
import sys

import numpy as np
import pytest
import torch

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "third_party", "OpenCOOD"))
from mint.model import opencood_shims  # noqa: E402

opencood_shims.install()
from mint.reliability import r1  # noqa: E402
from mint.reliability.pipeline import _from_tiles, _to_tiles  # noqa: E402


def rays(sup, trav, self_box=False):
    return {"std": {"SUP": sup, "TRAV": trav}, "self_box": self_box}


def eff(typ, plus=None, minus=None, sender=1, tile=(3, 4)):
    box = np.zeros((8, 3))
    return {"sender": sender, "type": typ, "plus": None if plus is None else box, "minus": None if minus is None else box,
            "tile_plus": tile if plus is not None else None, "tile_minus": tile if minus is not None else None,
            "rays_plus": plus, "rays_minus": minus}


def test_wilson_reference_values():
    lo, hi = r1.wilson(0, 10)                       # textbook: [0, 0.2775]
    assert lo == 0.0 and hi == pytest.approx(0.2775, abs=1e-4)
    lo, hi = r1.wilson(5, 10)                       # [0.2366, 0.7634]
    assert lo == pytest.approx(0.2366, abs=1e-4) and hi == pytest.approx(0.7634, abs=1e-4)


def test_add_gates_only_when_resolvably_empty():
    assert r1.effect_verdict(eff("ADD", plus=rays(0, 10))) == "gate"        # hi 0.28 < 0.5
    assert r1.effect_verdict(eff("ADD", plus=rays(1, 3))) == "none"         # s=0.25 but hi > 0.5
    assert r1.effect_verdict(eff("ADD", plus=rays(10, 0))) == "useful"


def test_remove_gates_only_when_resolvably_supported():
    assert r1.effect_verdict(eff("REMOVE", minus=rays(10, 0))) == "gate"
    assert r1.effect_verdict(eff("REMOVE", minus=rays(3, 1))) == "none"
    assert r1.effect_verdict(eff("REMOVE", minus=rays(0, 10))) == "useful"


def test_shift_needs_disjoint_intervals():
    assert r1.effect_verdict(eff("SHIFT", plus=rays(0, 10), minus=rays(10, 0))) == "gate"
    assert r1.effect_verdict(eff("SHIFT", plus=rays(10, 0), minus=rays(0, 10))) == "useful"
    assert r1.effect_verdict(eff("SHIFT", plus=rays(4, 6), minus=rays(6, 4))) == "none"   # overlapping


def test_unit_with_a_resolvably_useful_effect_is_kept():
    e1 = eff("ADD", plus=rays(0, 10))
    e2 = eff("REMOVE", minus=rays(0, 10))           # useful: sender removed an unsupported box
    rel = r1.assess([e1, e2])
    (k, r), = rel.items()
    assert r.status == "KNOWN" and not r.gate
    assert r1.assess([e1])[k].gate


def test_unknown_and_self_are_kept():
    assert r1.assess([eff("ADD", plus=rays(0, 2))])[(1, (3, 4))].status == "UNKNOWN_NO_EVIDENCE"
    assert not r1.assess([eff("ADD", plus=rays(0, 2))])[(1, (3, 4))].gate
    r = r1.assess([eff("ADD", plus=rays(0, 50, self_box=True))])[(1, (3, 4))]
    assert r.status == "NOT_APPLICABLE_SELF" and not r.gate


def test_tile_gather_scatter_roundtrip():
    x = torch.randn(1, 3, 100, 352)
    t = _to_tiles(x[0], 8)
    assert t.shape == (13, 44, 3, 8, 8)
    sel = torch.tensor([[0, 0], [12, 43], [5, 7]])
    y = _from_tiles(x, t[sel[:, 0], sel[:, 1]] * 0 + 7.0, sel)
    assert y.shape == x.shape
    assert (y[0, :, 96:100, 43 * 8:] == 7).all() and (y[0, :, 40:48, 56:64] == 7).all()
    m = torch.ones_like(x, dtype=torch.bool)
    m[..., 0:8, 0:8] = False
    m[..., 96:100, 344:352] = False
    m[..., 40:48, 56:64] = False
    assert torch.equal(y[m], x[m])
