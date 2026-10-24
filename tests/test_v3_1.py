"""preregistration_v3_1 (v3 + D-70): level construction, install() wiring, prereg difference vs v3."""
import copy
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import v3_stream as S3  # noqa: E402
import v3_1_stream as S31  # noqa: E402

V3 = os.path.join(ROOT, "runs/20261024-E5/preregistration_v3.json")
V31 = os.path.join(ROOT, S31.PREREG_V31)


def _pr31():
    pr = copy.deepcopy(json.load(open(V3)))
    pr["pgd_families"]["D-70_strong_level"] = {"conditions": [{"family": "pgd_untargeted_stealth", "r": 1.0},
                                                              {"family": "pgd_remove_stealth", "r": 1.0}]}
    pr["pgd_families"]["test_conditions"] += ["pgd_untargeted_stealth@r1.0", "pgd_remove_stealth@r1.0"]
    return pr


def test_levels_v31():
    lv = S31.levels_v31(_pr31())
    assert lv == {"pgd_untargeted": [0.25], "pgd_remove": [0.25], "pgd_untargeted_stealth": [0.5, 1.0],
                  "pgd_remove_stealth": [0.25, 1.0]}


def test_levels_v31_rejects_mismatch():
    pr = _pr31()
    pr["pgd_families"]["test_conditions"].pop()           # condition list must name exactly the run levels
    with pytest.raises(AssertionError):
        S31.levels_v31(pr)
    pr = _pr31()
    pr["pgd_families"]["D-70_strong_level"]["conditions"].append({"family": "pgd_remove_stealth", "r": 0.25})
    with pytest.raises(AssertionError):                   # no duplicate of an existing level
        S31.levels_v31(pr)


def test_install_wires_frozen_main():
    old = (S3.PREREG, S3.run_scenario)
    try:
        S31.install()
        assert S3.PREREG == S31.PREREG_V31 and S3.run_scenario is S31.run_scenario
    finally:
        S3.PREREG, S3.run_scenario = old


@pytest.mark.skipif(not os.path.exists(V31), reason="preregistration_v3_1.json not written yet")
def test_prereg_v31_difference():
    a, b = json.load(open(V3)), json.load(open(V31))
    assert S31.levels_v31(b)["pgd_untargeted_stealth"] == [0.5, 1.0]
    assert b["pgd_families"]["test_levels"] == a["pgd_families"]["test_levels"]        # v3 levels unchanged
    assert b["pgd_families"]["test_conditions"][:4] == a["pgd_families"]["test_conditions"]
    for k in ("D-64_dual_AP", "B-NORM", "comparison_set", "outcome", "D-69_reporting", "secondary_tables_v3",
              "procedural_checks", "opencood"):
        assert b[k] == a[k], k
    for p, h in a["frozen_sha256"].items():
        assert b["frozen_sha256"][p] == h, p
