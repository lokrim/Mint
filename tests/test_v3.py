"""preregistration_v3 code: PGD (D-65), B-NORM (D-66), dual-AP analysis (D-64), exact compact inputs,
procedural checks; purity of the new inference module; frozen hashes of v3."""
import ast
import hashlib
import json
import os
import sys

import numpy as np
import pytest
import torch

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import v3_analyze as Y  # noqa: E402  (installs shims, paths)
import v3_common as V  # noqa: E402
import v3_stream as S3  # noqa: E402
from mint.attacks import pgd_v3 as P  # noqa: E402
from mint.model.attfuse_parts import decode, fuse_scale  # noqa: E402
from mint.reliability import bnorm  # noqa: E402


class _Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        torch.manual_seed(0)
        bb = torch.nn.Module()
        bb.blocks = [None] * 3
        bb.deblocks = torch.nn.ModuleList([torch.nn.Conv2d(4, 2, 1) for _ in range(3)])
        self.backbone = bb
        self.cls_head = torch.nn.Conv2d(6, 2, 1)
        self.reg_head = torch.nn.Conv2d(6, 14, 1)


def _feats(n=2):
    torch.manual_seed(1)
    return [torch.relu(torch.randn(n, 4, 6, 6)) for _ in range(3)]


def test_heads_grad_equals_frozen_decode():
    m, f = _Tiny(), _feats(3)
    with torch.no_grad():
        a = decode(m, [fuse_scale(x)[0] for x in f])
        b = P.heads_grad(m, f)
    assert torch.equal(a[0], b[0]) and torch.equal(a[1], b[1])


@pytest.mark.parametrize("fam", P.FAMILIES)
def test_pgd_budget_scope_and_ascent(fam):
    m, f = _Tiny(), _feats(3)
    eps = [0.1, 0.05, 0.02]
    new, led = P.pgd_attack(m, f, 1, fam, eps, P.rng_for(fam, 0.5, "s", 0), score_thr=0.4)
    for k, (x, y) in enumerate(zip(f, new)):
        assert torch.equal(y[0], x[0]) and torch.equal(y[2], x[2])          # only the attacker row changes
        assert float((y[1] - x[1]).abs().max()) <= eps[k] * (1 + 1e-6)      # per-scale L-inf budget
        assert float(y[1].min()) >= 0.0                                      # feature domain
    h = led["objective_hist"]
    assert len(h) == P.STEPS + 1 and h[-1] >= h[0]
    new2, _ = P.pgd_attack(m, f, 1, fam, eps, P.rng_for(fam, 0.5, "s", 0), score_thr=0.4)
    assert all(torch.equal(a, b) for a, b in zip(new, new2))                 # deterministic per key
    assert all(p.requires_grad for p in m.parameters())                      # model state restored


def test_pgd_objectives_use_no_gt():
    z = torch.tensor([[[[2.0, -2.0]]]])
    pos = torch.tensor([[[[True, False]]]])
    rm = torch.zeros(1, 7, 1, 2)
    r = float(P.objective(z.expand(1, 1, 1, 2), rm, pos, rm, "pgd_remove"))
    assert abs(r - float(-torch.nn.functional.logsigmoid(torch.tensor(2.0)))) < 1e-6
    u = float(P.objective(z, rm, pos, rm, "pgd_untargeted"))
    assert u > r
    args = P.pgd_attack.__code__.co_varnames[:P.pgd_attack.__code__.co_argcount]
    assert not any(a in ("gt", "gt_boxes", "label") for a in args)


def test_bnorm_rule():
    m = np.array([[1.0, 1.0, 1.0], [1.2, 0.9, 1.0], [1.0, 1.0, 3.0]])
    tau = [1.5, 1.5, 1.5]
    assert np.allclose(bnorm.ratios(m), [[1.2, 0.9, 1.0], [1.0, 1.0, 3.0]])
    assert bnorm.flagged(m, tau) == [2]
    assert bnorm.flagged(m, [np.inf] * 3) == []
    assert bnorm.flagged(m, [1.1, 1.5, 1.5]) == [1, 2]                      # any scale suffices
    cands = {frozenset(): "all", frozenset([2]): "w/o 2", frozenset([1, 2]): "w/o 1,2"}
    assert bnorm.output_cands(cands, m, tau) == "w/o 2"
    f = [torch.ones(2, 3, 2, 2), 2 * torch.ones(2, 3, 2, 2)]
    assert np.allclose(bnorm.mean_abs(f), [[1, 2], [1, 2]])


def test_compact_inputs_roundtrip():
    rng = np.random.default_rng(0)
    nump = np.array([3, 1, 32, 5], np.int32)
    vf = np.zeros((4, 32, 4), np.float32)
    for j, k in enumerate(nump):
        vf[j, :k] = rng.random((k, 4))
    b = {"ego": {"processed_lidar": {"voxel_features": torch.from_numpy(vf),
                                     "voxel_coords": torch.from_numpy(rng.integers(0, 9, (4, 4)).astype(np.int32)),
                                     "voxel_num_points": torch.from_numpy(nump)},
                 "record_len": torch.tensor([2]), "anchor_box": torch.zeros(2, 2, 2, 7, dtype=torch.float64),
                 "transformation_matrix": torch.eye(4)}}
    inp = V.compact_inputs(b)
    assert inp["points"].shape == (41, 4)
    assert V.inputs_equal(b, V.rebuild_batch(inp, np.zeros((2, 2, 2, 7))))
    b["ego"]["processed_lidar"]["voxel_features"][0, 5, 0] = 1.0              # non-zero padding would be lost
    assert not V.inputs_equal(b, V.rebuild_batch(inp, np.zeros((2, 2, 2, 7))))


def test_ledger_equality_helper():
    assert V.same({"a": [1, np.array([1.0, 2.0])], "b": None}, {"a": [1, np.array([1.0, 2.0])], "b": None})
    assert not V.same({"a": np.array([1.0])}, {"a": np.array([1.5])})
    assert V.same({frozenset([1]): (np.zeros(2), [0.5])}, {frozenset([1]): (np.zeros(2), [0.5])})


def _parts():
    # two frames; frame-order and global-rank AP differ
    return [(np.array([1, 0]), np.array([0, 1]), np.array([0.9, 0.8]), 2),
            (np.array([1]), np.array([0]), np.array([0.95]), 1)]


def test_store_ap_matches_frozen_and_global():
    st = Y.Store({("c", "m", 0.7): _parts()})
    fo = st.ap(("c", "m", 0.7), [0, 1], False)
    assert fo == Y.Z.ap_from([(p[0], p[1], p[3]) for p in _parts()])
    gl = st.ap(("c", "m", 0.7), [0, 1], True)
    o = np.argsort(-np.array([0.9, 0.8, 0.95]), kind="stable")
    assert gl == Y.Z.ap_from([(np.array([1, 0, 1])[o], np.array([0, 1, 0])[o], 3)])
    assert gl != fo
    assert st.ap(("c", "m", 0.7), [1, 1], False) == Y.Z.ap_from([(np.array([1, 1]), np.array([0, 0]), 2)])


def test_bootstrap_resampling_equals_frozen():
    keys = [("a", i) for i in range(23)] + [("b", i) for i in range(7)]
    u1, s1 = Y.units_strata(keys, "block10")
    assert [len(u) for u in u1] == [10, 10, 3, 7] and s1 == [[0, 1, 2], [3]]
    u2, s2 = Y.units_strata(keys, "scenario")
    assert len(u2) == 2 and s2 == [[0, 1]]


def test_pgd_realized_rule():
    from mint.effects.effects import bev_iou_matrix  # noqa: F401
    b = lambda x: np.array([[x + 2, -1, 0], [x + 2, 1, 0], [x - 2, 1, 0], [x - 2, -1, 0]] * 2, float)
    yc = np.stack([b(0), b(20)])
    assert Y.pgd_realized("pgd_remove@r0.5", yc, yc[:1])
    assert not Y.pgd_realized("pgd_remove@r0.5", yc, np.concatenate([yc, b(40)[None]]))
    assert Y.pgd_realized("pgd_untargeted@r0.5", yc, np.concatenate([yc, b(40)[None]]))
    assert not Y.pgd_realized("pgd_untargeted@r0.5", yc, yc)


def test_selection_and_stop_rules():
    lv = {"pgd_untargeted": [0.25, 0.5, 1.0], "pgd_remove": [0.25, 0.5, 1.0]}
    pt = {"global": {"attack_loss|pgd_untargeted@r0.25": 0.01, "attack_loss|pgd_untargeted@r0.5": 0.03,
                     "attack_loss|pgd_untargeted@r1.0": 0.2, "attack_loss|pgd_remove@r0.25": 0.0,
                     "attack_loss|pgd_remove@r0.5": 0.01, "attack_loss|pgd_remove@r1.0": 0.019}}
    s = Y.pgd_selection(pt, lv)
    assert s["pgd_untargeted"]["selected_r"] == 0.5 and s["pgd_untargeted"]["status"] == "selected"
    assert s["pgd_remove"]["selected_r"] == 1.0 and s["pgd_remove"]["status"].startswith("too weak")
    fl = {f"{f}@r{r}": {"catch_rate": 0.99} for f in lv for r in lv[f]}
    assert Y.bnorm_stop(fl, lv)["stop"]
    fl["pgd_remove@r0.25"]["catch_rate"] = 0.5
    fl["pgd_untargeted@r0.5"]["catch_rate"] = 0.95
    assert not Y.bnorm_stop(fl, lv)["stop"]


def test_d64_combination():
    assert Y.d64(True, True)["success"] and Y.d64(True, True)["verdict"] == "success under both AP definitions"
    for a, b in ((True, False), (False, True)):
        r = Y.d64(a, b)
        assert not r["success"] and r["verdict"] == "AP-definition-dependent"
    assert Y.d64(False, False)["verdict"] == "fails under both AP definitions"
    assert Y.d64(True, True)["headline_AP"] == "global"


def test_interrupted_download_stops():
    assert S3.interrupted({"downloads": [{"status": "complete"}, {"status": "started (counted at full size)"}]})
    assert not S3.interrupted({"downloads": [{"status": "complete"}]})


def test_new_inference_module_is_pure():
    bad = ("mint.eval", "harm_labels", "mint.attacks", "mint.audit", "e0_analyze", "e4_analyze", "e5_analyze")
    tree = ast.parse(open(os.path.join(ROOT, "src/mint/reliability/bnorm.py")).read())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] + ([node.module] if getattr(node, "module", None) else [])
            assert not any(b in (n or "") for n in names for b in bad)
        if isinstance(node, ast.FunctionDef):
            assert not any(a.arg in ("gt", "gt_boxes", "label", "ledger", "led") for a in node.args.args)


PREREG_V3 = os.path.join(ROOT, "runs/20261024-E5/preregistration_v3.json")


@pytest.mark.skipif(not os.path.exists(PREREG_V3), reason="v3 not written yet")
def test_v3_frozen_hashes_and_untouched_v2_methods():
    pr = json.load(open(PREREG_V3))
    for p, h in pr["frozen_sha256"].items():
        assert hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest() == h, p
    v2 = json.load(open(os.path.join(ROOT, "runs/20261024-E5/preregistration_v2.json")))["file_sha256"]
    for p in ("src/mint/reliability/r1.py", "src/mint/reliability/baselines.py", "src/mint/reliability/pipeline.py"):
        assert pr["frozen_sha256"][p] == v2[p]
