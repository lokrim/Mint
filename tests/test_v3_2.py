"""preregistration_v3_2 (v3.1 + D-71): stealth-infeasible PGD records no longer crash the stream's v3_extra."""
import inspect
import json
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import v3_stream as S3  # noqa: E402
import v3_1_stream as S31  # noqa: E402
import v3_2_stream as S32  # noqa: E402

V31 = os.path.join(ROOT, S31.PREREG_V31)
V32 = os.path.join(ROOT, S32.PREREG_V32)
INFEASIBLE = {"ledger": {"applied": False, "reason": "stealth_infeasible"}}


def test_copy_mabs_skips_infeasible():
    pgd = {"pgd_remove@r0.25": {"mabs": [1.0, 2.0], "ledger": {"applied": True}},
           "pgd_remove_stealth@r1.0": dict(INFEASIBLE)}
    mabs = S32.copy_mabs({"clean": [3.0]}, pgd)
    assert mabs == {"clean": [3.0], "pgd_remove@r0.25": [1.0, 2.0]}
    assert pgd["pgd_remove_stealth@r1.0"] == INFEASIBLE                 # record kept as pgd_conditions returned it


def test_copy_mabs_other_missing_raises():
    with pytest.raises(AssertionError):
        S32.copy_mabs({}, {"pgd_remove@r0.25": {"ledger": {"applied": False, "reason": "something_else"}}})


def _body(fn):
    src = inspect.getsource(fn)
    doc = fn.__doc__
    return src[src.index(doc) + len(doc):]


def test_v3_extra_is_v31_except_copy_loop():
    old = _body(S31.v3_extra)
    loop = '    for c, r in pgd.items():\n        mabs[c] = r["mabs"]\n'
    assert old.count(loop) == 1
    assert _body(S32.v3_extra) == old.replace(loop, "    copy_mabs(mabs, pgd)\n")


def _stub(monkeypatch, mod):
    """Stub the model-side calls of v3_extra; the stealth families come back infeasible."""
    monkeypatch.setattr(mod.E, "cav_contents", lambda ds, i: [(0, {"lidar_np": np.zeros((4, 4))}),
                                                              (1, {"lidar_np": np.zeros((4, 4))})])
    monkeypatch.setattr(mod.E, "projected_points", lambda cav, pcr: None)
    monkeypatch.setattr(mod, "agent_features", lambda model, ego: (None, None))
    monkeypatch.setattr(mod, "ground_mask", lambda ego: (None, None))
    monkeypatch.setattr(mod.V, "bnorm_extras", lambda *a: {"clean": [0.1, 0.2, 0.3]})

    def pgd_conditions(model, pp, batch, feats0, n, ego, gmask, pcr, scen, i, levels, sigma, thr, tau):
        (fam, rs), = levels.items()
        return {S31.V.cond_name(fam, r): dict(INFEASIBLE) if "stealth" in fam else {"mabs": [r], "ledger": {}}
                for r in rs}
    monkeypatch.setattr(mod.V, "pgd_conditions", pgd_conditions)


LEVELS = {"pgd_remove": [0.25], "pgd_remove_stealth": [0.25, 1.0]}


def _call(fn):
    class DS:
        post_processor = None
    return fn(None, DS(), {"ego": None}, {"n_agents": 2}, "scen", 0, None, None, LEVELS, None, None, None)


def test_v31_crashes_v32_does_not(monkeypatch):
    _stub(monkeypatch, S31)
    _stub(monkeypatch, S32)
    with pytest.raises(KeyError, match="mabs"):                        # the final-test crash, reproduced
        _call(S31.v3_extra)
    ex = _call(S32.v3_extra)
    assert set(ex["mabs"]) == {"clean", "pgd_remove@r0.25"}
    assert set(ex["pgd"]) == {"pgd_remove@r0.25", "pgd_remove_stealth@r0.25", "pgd_remove_stealth@r1.0"}
    assert ex["pgd"]["pgd_remove_stealth@r1.0"]["ledger"]["reason"] == "stealth_infeasible"
    assert "attack_s" in ex["pgd"]["pgd_remove_stealth@r1.0"]


def test_install_wires_v31_and_frozen_main():
    old = (S3.PREREG, S3.run_scenario, S31.v3_extra, S31.PREREG_V31)
    try:
        S32.install()
        assert S3.PREREG == S32.PREREG_V32 and S3.run_scenario is S31.run_scenario
        assert S31.v3_extra is S32.v3_extra and S31.PREREG_V31 == S32.PREREG_V32
        assert S31.run_scenario.__globals__["v3_extra"] is S32.v3_extra   # looked up at call time
    finally:
        S3.PREREG, S3.run_scenario, S31.v3_extra, S31.PREREG_V31 = old


@pytest.mark.skipif(not os.path.exists(V32), reason="preregistration_v3_2.json not written yet")
def test_prereg_v32_difference():
    a, b = json.load(open(V31)), json.load(open(V32))
    assert b["pgd_families"] == a["pgd_families"]                       # conditions, levels, attack unchanged
    for k in ("D-64_dual_AP", "B-NORM", "comparison_set", "outcome", "D-69_reporting", "secondary_tables_v3",
              "procedural_checks", "opencood", "estimated_runtime", "difference_from_v3"):
        assert b[k] == a[k], k
    assert {k: v for k, v in b["streaming"].items() if k != "runner"} == \
        {k: v for k, v in a["streaming"].items() if k != "runner"}
    assert "v3_2_stream.py" in b["streaming"]["runner"]
    assert b["analysis"] == [s.replace("preregistration_v3_1.json", "preregistration_v3_2.json") for s in a["analysis"]]
    for p, h in a["frozen_sha256"].items():                              # every v3.1-frozen file unchanged
        assert b["frozen_sha256"][p] == h, p
    assert set(b["frozen_sha256"]) - set(a["frozen_sha256"]) == {"runners/v3_2_stream.py", "runners/v3_2_dryrun.py",
                                                                    "tests/test_v3_2.py"}
    assert b["D-71"]["decision"].startswith("D-71")
