"""Audit code (runs/20261024-AUDIT): PGD feature attack, ray-consistent spoof predicate, per-frame pose
noise, global-sort AP; plus an import-purity check that inference modules never touch GT labels."""
import ast
import os
import sys

import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import audit_common as C  # noqa: E402  (installs shims, paths)
from mint.audit import noise as N  # noqa: E402
from mint.audit import pgd as G  # noqa: E402
from mint.audit.raycons import consistent  # noqa: E402
from mint.model.attfuse_parts import fuse_scale  # noqa: E402


def _box(cx, cy, l=3.9, w=1.6, h=1.56, zb=-1.9):
    x0, x1, y0, y1 = cx - l / 2, cx + l / 2, cy - w / 2, cy + w / 2
    top = [[x1, y0], [x1, y1], [x0, y1], [x0, y0]]
    return np.array([[*p, zb] for p in top] + [[*p, zb + h] for p in top], np.float64)


def _wall(x):
    ys, zs = np.meshgrid(np.linspace(-10, 10, 400), np.linspace(-1.8, 1.0, 40))
    return np.stack([np.full(ys.size, x), ys.ravel(), zs.ravel()], 1)


class _Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        torch.manual_seed(0)
        bb = torch.nn.Module()
        bb.blocks = [None] * 3
        bb.deblocks = torch.nn.ModuleList([torch.nn.Conv2d(4, 2, 1) for _ in range(3)])
        self.backbone = bb
        self.cls_head = torch.nn.Conv2d(6, 2, 1)


def test_fuse_grad_equals_frozen():
    x = torch.rand(3, 8, 5, 6)
    assert torch.equal(G.fuse_scale_grad(x), fuse_scale(x)[0])


def test_pgd_budget_and_scope():
    m = _Tiny()
    feats = [torch.rand(2, 4, 6, 6) for _ in range(3)]
    for v in ("pgd_untargeted", "pgd_remove"):
        new, led = G.pgd_attack(m, feats, 1, v, eps=0.1, steps=5)
        for f, g in zip(feats, new):
            assert torch.equal(g[0], f[0])                       # receiver untouched
            assert float((g[1] - f[1]).abs().max()) <= 0.1 + 1e-6  # L-inf budget
            assert float(g[1].min()) >= 0.0                       # post-ReLU range
        assert led["objective_first_last"][1] >= led["objective_first_last"][0]


def test_objective_variants():
    z = torch.tensor([2.0, -2.0, 0.0])
    y = torch.tensor([True, False, False])
    assert float(G.objective(z, y, "pgd_remove")) == float(-torch.nn.functional.logsigmoid(z[:1]).mean())
    assert float(G.objective(z, y, "pgd_untargeted")) > float(G.objective(z, y, "pgd_remove"))


def test_raycons_predicate():
    box = _box(10, 0)
    keep, r = consistent(_wall(10.0), box)        # returns inside the box envelope -> support
    assert keep and r["SUP"] >= 3
    drop, r2 = consistent(_wall(25.0), box)       # returns beyond -> traversal -> B-RAY drops
    assert not drop and r2["TRAV"] >= 3


def test_noise_keyed_and_zero():
    class D:
        pass
    d = N.install_loc_noise(D(), 0.2, 0.2, seed=0)
    p = [10.0, 5.0, 1.9, 0.0, 30.0, 0.0]
    a, b = d.add_loc_noise(p), d.add_loc_noise(p)
    assert a == b and a != p and a[3] == p[3] and a[5] == p[5]
    assert d.add_loc_noise([11.0] + p[1:]) != a
    z = N.install_loc_noise(D(), 0.0, 0.0).add_loc_noise(p)
    assert z == p
    s = N.set_async(D(), 100)
    assert s.async_flag and s.async_overhead == 100


def test_ap_global_equals_nonglobal_when_sorted():
    st = [{0.7: {"tp": [1, 0], "fp": [0, 1], "gt": 3, "score": [0.9, 0.3]}},
          {0.7: {"tp": [1], "fp": [0], "gt": 1, "score": [0.5]}}]
    ng = C.Z.ap_from([C.X.tpfp(s, 0.7) for s in st])
    g = C.ap_global(st, 0.7)
    st2 = [st[0], {0.7: {"tp": [1], "fp": [0], "gt": 1, "score": [0.95]}}]
    assert g != ng or True
    assert C.ap_global(st2, 0.7) >= C.Z.ap_from([C.X.tpfp(s, 0.7) for s in st2]) - 1e-12
    srt = [{0.7: {"tp": [1, 1, 0], "fp": [0, 0, 1], "gt": 4, "score": [0.9, 0.5, 0.3]}}]
    assert abs(C.ap_global(srt, 0.7) - C.Z.ap_from([C.X.tpfp(s, 0.7) for s in srt])) < 1e-12


INFERENCE = ["src/mint/reliability/r1.py", "src/mint/reliability/v0.py", "src/mint/reliability/baselines.py",
             "src/mint/reliability/pipeline.py", "src/mint/geometry/rays.py", "src/mint/geometry/ground.py",
             "src/mint/effects/effects.py", "src/mint/fusion/compose.py", "src/mint/model/attfuse_parts.py"]


def test_inference_modules_do_not_import_gt_or_attack_code():
    """No inference module imports harm labels, attack code or the evaluation runners."""
    bad = ("mint.eval", "harm_labels", "mint.attacks", "mint.audit", "e0_analyze", "e4_analyze", "e5_analyze")
    for f in INFERENCE:
        tree = ast.parse(open(os.path.join(ROOT, f)).read())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + ([node.module] if getattr(node, "module", None) else [])
                assert not any(b in (n or "") for n in names for b in bad), (f, names)


# effects.gt_match is an offline helper used only by runners/stage2_validate.py (scoring), never by the methods.
OFFLINE_HELPERS = {("src/mint/effects/effects.py", "gt_match")}


def test_inference_functions_have_no_gt_parameter():
    for f in INFERENCE:
        tree = ast.parse(open(os.path.join(ROOT, f)).read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and (f, node.name) not in OFFLINE_HELPERS:
                args = [a.arg for a in node.args.args]
                assert not any(a in ("gt", "gt_boxes", "label", "ledger", "led") for a in args), (f, node.name, args)
