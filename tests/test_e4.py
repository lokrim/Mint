"""E4: spoof_blind destination choice, block-H allowlist, held-out metrics and bootstrap."""
import os
import sys

import numpy as np
import pytest
import torch

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import e4_analyze as Z  # noqa: E402  (installs shims, paths)
from mint.attacks import blind as B  # noqa: E402
from mint.attacks import patches as P  # noqa: E402
from mint.geometry.rays import classify_points  # noqa: E402


def _box(cx, cy, l=3.9, w=1.6, h=1.56, zb=-1.9):
    x0, x1, y0, y1 = cx - l / 2, cx + l / 2, cy - w / 2, cy + w / 2
    top = [[x1, y0], [x1, y1], [x0, y1], [x0, y0]]          # OpenCOOD corner order (0-3 bottom, 4-7 top)
    return np.array([[*p, zb] for p in top] + [[*p, zb + h] for p in top], np.float64)


def _scan_with_wall():
    """Receiver points: a dense vertical wall at x = 15 m (y in [-10, 10]) -> boxes beyond it are
    behind the wall (OCC only, 0 SUP/TRAV); boxes before it (x < 15) are crossed by the wall rays (TRAV)."""
    ys, zs = np.meshgrid(np.linspace(-10, 10, 400), np.linspace(-1.8, 1.0, 40))
    return np.stack([np.full(ys.size, 15.0), ys.ravel(), zs.ravel()], 1)


def _feats():
    return [torch.zeros(2, 4, 200, 704), torch.zeros(2, 4, 100, 352), torch.zeros(2, 4, 50, 176)]


def test_translate_and_shift():
    src, dst = (10, 12, 5, 7), (13, 15, 4, 6)
    dx, dy = B.patch_shift_m(src, dst)
    assert (dx, dy) == (3 * P.COARSE_M, -1 * P.COARSE_M)
    b = _box(1.0, 2.0)
    t = B.translate_box(b, dx, dy)
    assert np.allclose(t[:, 0] - b[:, 0], dx) and np.allclose(t[:, 1] - b[:, 1], dy) and np.allclose(t[:, 2], b[:, 2])


def test_receiver_rays_wall():
    pts = _scan_with_wall()
    assert B.receiver_rays(pts, _box(8.0, 0.0)) >= 3            # in front of the wall: TRAV rays
    assert B.receiver_rays(pts, _box(25.0, 0.0)) == 0           # behind the wall: occluded only
    assert B.receiver_rays(pts, _box(0.0, 0.0)) is None         # the receiver's own box


def test_blind_destination_has_lt3_rays_and_is_free():
    pts = _scan_with_wall()
    feats = _feats()
    src_box = _box(8.0, 0.0)
    src = P.coarse_patch(8.0, 0.0, P.box_half(src_box))
    gt_xy = np.array([[8.0, 0.0], [-20.0, 10.0]])
    rng = np.random.default_rng(3)
    for _ in range(20):
        p, n, used = B.sample_blind_patch(rng, src, feats, gt_xy, src_box, pts)
        assert p is not None and n < 3 and 1 <= used <= 300
        assert P.free_of(p, gt_xy, 3.0) and P.in_grid(p, feats)
        box = B.translate_box(src_box, *B.patch_shift_m(src, p))
        r = classify_points(pts, box)
        assert not r["self_box"] and r["SUP"] + r["TRAV"] == n


def test_attack_spoof_blind_copies_patch_and_ledger():
    pts = _scan_with_wall()
    feats = [torch.randn(2, 4, 200, 704), torch.randn(2, 4, 100, 352), torch.randn(2, 4, 50, 176)]
    gt = np.stack([_box(8.0, 0.0)]).astype(np.float32)
    att = np.random.default_rng(0).uniform(-1, 1, (200, 3)) * [1.5, 0.6, 0.5] + [8.0, 0.0, -1.2]
    new, led = B.attack_spoof_blind(feats, 1, gt, att, pts, np.random.default_rng(1))
    assert led["applied"] and led["predicted_box_rays"] < 3 and led["family"] == "spoof_blind"
    assert torch.equal(new[0][0], feats[0][0])                 # receiver untouched
    src = P.coarse_patch(8.0, 0.0, P.box_half(gt[0]))
    dc, dr = (np.array(led["shift_m"]) / P.COARSE_M).round().astype(int)
    dst = P.shift_patch(src, dc, dr)
    for k in range(3):
        rs, cs = P._slices(src, k)
        rd, cd = P._slices(dst, k)
        assert torch.equal(new[k][1, :, rd, cd], feats[k][1, :, rs, cs])
    # no eligible target -> untouched
    new2, led2 = B.attack_spoof_blind(feats, 1, gt, att[:5], pts, np.random.default_rng(1))
    assert not led2["applied"] and new2 is feats


def test_block_h_allowlist_refuses_others():
    import e4_stream as S
    S.check_allowlist(list(S.H_SCENARIOS))
    for bad in (["2021_08_22_13_37_16"], ["2021_09_09_19_27_35"], ["2021_08_23_12_58_19"],
                [S.H_SCENARIOS[0], S.H_SCENARIOS[0]]):
        with pytest.raises(SystemExit):
            S.check_allowlist(bad)
    assert len(S.H_SCENARIOS) == 4 and S.BYTE_BUDGET == 3_200_000_000


def _frame(tp, fp, gt):
    return np.asarray(tp, np.int64), np.asarray(fp, np.int64), gt


def test_metrics_mean_delta_and_recovery():
    good, bad = _frame([1, 1], [0, 0], 2), _frame([1, 0], [0, 1], 2)
    conds = ("clean", "spoof_feat", "remove_feat")
    F = {("clean", "undefended"): [good, good], ("clean", "R1"): [good, good],
         ("spoof_feat", "undefended"): [bad, good], ("spoof_feat", "R1"): [good, good],
         ("remove_feat", "undefended"): [bad, good], ("remove_feat", "R1"): [bad, good]}
    m, ap = Z.metrics(F, [0, 1], conds, ("spoof_feat", "remove_feat"))
    assert ap[("clean", "undefended")] == pytest.approx(1.0)
    assert m["clean_rel_loss"] == pytest.approx(0.0)
    assert m["recovery_spoof_feat"] == pytest.approx(1.0) and m["recovery_remove_feat"] == pytest.approx(0.0)
    assert m["mean_delta_orig"] == pytest.approx(np.mean([m["delta_spoof_feat"], m["delta_remove_feat"]]))
    assert m["delta_spoof_feat"] > 0 and m["delta_remove_feat"] == 0


def test_bootstrap_block10_is_stratified_and_paired():
    good = _frame([1], [0], 1)
    keys = [("a", i) for i in range(25)] + [("b", i) for i in range(12)]
    F = {(c, p): [good] * len(keys) for c in ("clean", "spoof_feat") for p in ("undefended", "R1")}
    b = Z.bootstrap(F, keys, ("clean", "spoof_feat"), ("spoof_feat",), "block10", n_boot=50)
    assert b["_blocks"] == 3 + 2
    assert b["delta_spoof_feat"]["ci95"] == [0.0, 0.0] and b["mean_delta_orig"]["ci95"] == [0.0, 0.0]
    s = Z.bootstrap(F, keys, ("clean", "spoof_feat"), ("spoof_feat",), "scenario", n_boot=20)
    assert s["_blocks"] == 2
