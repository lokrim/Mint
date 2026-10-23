"""E2: numpy AP mirror vs OpenCOOD, bootstrap blocks, Part C classification order, sub-stage timer."""
import copy
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import e2_rules as R  # noqa: E402  (installs shims, paths)
from opencood.utils import eval_utils  # noqa: E402
from mint.reliability.pipeline import Prof, NOPROF  # noqa: E402


def _frames(rng, n):
    out = []
    for _ in range(n):
        k = int(rng.integers(0, 12))
        tp = rng.integers(0, 2, k)
        out.append((tp.astype(np.int64), (1 - tp).astype(np.int64), int(rng.integers(0, 10)) + int(tp.sum())))
    return out


def test_ap_mirror_equals_opencood():
    rng = np.random.default_rng(1)
    for _ in range(50):
        F = _frames(rng, int(rng.integers(1, 30)))
        if sum(len(f[0]) for f in F) == 0:
            continue
        st = {0.7: {"tp": [], "fp": [], "gt": 0, "score": []}}
        for tp, fp, gt in F:
            st[0.7]["tp"] += tp.tolist(); st[0.7]["fp"] += fp.tolist(); st[0.7]["gt"] += gt
            st[0.7]["score"] += [0.5] * len(tp)
        ref = eval_utils.calculate_ap(copy.deepcopy(st), 0.7, False)[0]
        assert abs(R.ap_from(F) - ref) < 1e-12


def test_bootstrap_blocks_and_point():
    frames = [("a", i) for i in range(157)] + [("b", i) for i in range(112)] + [("c", i) for i in range(135)]
    rng = np.random.default_rng(0)
    F = {(c, p): _frames(rng, len(frames)) for c in ("clean", "x") for p in R.POL}
    old = R.N_BOOT
    R.N_BOOT = 5
    try:
        b10 = R.bootstrap(F, frames, ("clean", "x"), "block10")
        bs = R.bootstrap(F, frames, ("clean", "x"), "scenario")
    finally:
        R.N_BOOT = old
    assert b10["_blocks"] == 16 + 12 + 14 and bs["_blocks"] == 3
    m, _ = R.metrics(F, list(range(len(frames))), ("clean", "x"))
    assert "recovery_x" in m and "delta_clean" in m and "clean_rel_loss" in m


def test_classify_order():
    base = {"gt_max_iou": 0.0, "gt_nearest_centre_m": 10.0, "pts_in_box": 50, "pts_nonground": 40, "z_extent_nonground_m": 1.0}
    assert R.classify(dict(base, gt_max_iou=0.2, pts_in_box=0)) == "label/IoU artefact"
    assert R.classify(dict(base, gt_nearest_centre_m=1.5)) == "unclear"
    assert R.classify(dict(base, pts_in_box=5)) == "unclear"
    assert R.classify(base) == "receiver FP on unlabelled structure"
    assert R.classify(dict(base, z_extent_nonground_m=0.2)) == "genuine R1 error"
    assert R.classify(dict(base, pts_nonground=3)) == "genuine R1 error"


def test_prof():
    p = Prof()
    p.stage = "s"
    with p("a"):
        pass
    with p("a"):
        pass
    assert set(p.acc) == {"s.a"} and p.acc["s.a"] >= 0
    with NOPROF("a"):
        pass
    assert NOPROF.acc == {}
