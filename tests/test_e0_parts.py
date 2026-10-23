"""Tests for the E0 / MINT-v0.0 building blocks: composition, ground-aware rays, patches, labels,
and the inference purity rule (no GT-label module importable from inference code)."""
import ast
import glob
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
from mint.fusion.compose import Candidates, compose, tile_include_masks  # noqa: E402
from mint.geometry.ground import classify_points_ground, ground_mask  # noqa: E402
from mint.geometry.rays import classify_points  # noqa: E402
from mint.attacks import patches as P  # noqa: E402
from mint.eval.harm_labels import harm_D, label, local_error  # noqa: E402
from test_rays import corners  # noqa: E402

H, W, A = 100, 352, 2


def fake_cands(idx, tag):
    idx = np.asarray(sorted(idx), np.int64)
    return Candidates(idx, np.full((len(idx), 8, 3), tag, np.float32), np.full(len(idx), tag, np.float32), (H, W), A)


def flat(h, w, a=0):
    return (h * W + w) * A + a


def test_compose_takes_gated_tile_from_subset_and_keeps_anchor_order():
    base = fake_cands([flat(0, 0), flat(9, 9), flat(20, 40)], 0.0)      # tiles (0,0) (1,1) (2,5)
    minus1 = fake_cands([flat(9, 10, 1), flat(20, 40)], 1.0)            # tile (1,1) changed
    c = compose({frozenset(): base, frozenset([1]): minus1}, {(1, 1): frozenset([1])})
    assert list(c.idx) == [flat(0, 0), flat(9, 10, 1), flat(20, 40)]
    assert list(c.scores) == [0.0, 1.0, 0.0]


def test_compose_empty_choice_is_identity():
    base = fake_cands([flat(3, 3)], 0.0)
    assert compose({frozenset(): base}, {}) is base


def test_tile_include_masks_scale_alignment():
    ms = tile_include_masks(3, [(100, 352), (50, 176), (25, 88)], {(2, 5): frozenset([2])})
    for m, px in zip(ms, (8, 4, 2)):
        assert (~m).sum() == px * px
        assert not m[2, 2 * px:3 * px, 5 * px:6 * px].any()
        assert m[0].all() and m[1].all()


def flat_ground_scan(h=1.9, rmax=60.0):
    """Points on a flat ground plane z = -h seen from the origin (dense rings)."""
    pts = []
    for el in np.radians(np.linspace(-25, -2, 50)):
        r = h / np.tan(-el)
        if r > rmax:
            continue
        az = np.linspace(-np.pi, np.pi, 1800, endpoint=False)
        pts.append(np.stack([r * np.cos(az), r * np.sin(az), np.full_like(az, -h)], 1))
    return np.concatenate(pts)


def test_ground_contamination_of_standard_count_and_ground_aware_fix():
    pts = flat_ground_scan()
    empty = corners(9.0, 0.0, -1.9 + 0.78, 3.9, 1.6, 1.56, 0.0)          # nothing there
    std = classify_points(pts, empty)
    g, _ = ground_mask(pts)
    gnd = classify_points_ground(pts, g, empty)
    assert std["SUP"] > 0                       # the documented failure: ground hits read as support
    assert gnd["SUP"] == 0 and gnd["TRAV"] >= std["SUP"]


def test_ground_aware_keeps_support_on_a_real_box():
    pts = flat_ground_scan()
    box = corners(12.0, 0.0, -1.9 + 0.78, 3.9, 1.6, 1.56, 0.0)
    # add a vertical face of the box as returns along rays (front face at x = 10.05)
    yy, zz = np.meshgrid(np.linspace(-0.7, 0.7, 15), np.linspace(-1.5, -0.5, 10))
    face = np.stack([np.full(yy.size, 10.1), yy.ravel(), zz.ravel()], 1)
    d = face / np.linalg.norm(face, axis=1, keepdims=True)
    keep = []
    for p in pts:                                 # drop ground returns occluded by the face
        dirp = p / np.linalg.norm(p)
        if not (np.min(np.linalg.norm(d - dirp, axis=1)) < 0.01 and np.linalg.norm(p) > 10):
            keep.append(p)
    scan = np.concatenate([np.asarray(keep), face])
    g, _ = ground_mask(scan)
    out = classify_points_ground(scan, g, box)
    assert out["SUP"] > 0 and out["SUP"] >= out["TRAV"]


def test_patch_slices_have_same_metric_extent():
    p = P.coarse_patch(10.0, 5.0, 3.0)
    feats = [torch.zeros(2, 1, 100, 352), torch.zeros(2, 1, 50, 176), torch.zeros(2, 1, 25, 88)]
    sizes = []
    for k, m in enumerate(P.SCALE_M):
        rs, cs = P._slices(p, k)
        sizes.append(((rs.stop - rs.start) * m, (cs.stop - cs.start) * m))
    assert sizes[0] == sizes[1] == sizes[2]
    src, dst = p, P.shift_patch(p, 2, -1)
    for f in feats:
        f[1] = torch.arange(f[1].numel(), dtype=torch.float32).reshape(f[1].shape)
    before = [f.clone() for f in feats]
    P.copy_patch(feats, 1, src, dst)
    for k, f in enumerate(feats):
        rs, cs = P._slices(src, k)
        rd, cd = P._slices(dst, k)
        assert torch.equal(f[1, :, rd, cd], before[k][1, :, rs, cs])
        assert torch.equal(f[0], before[k][0])                         # other agents untouched


def test_append_points_only_touches_target_agent():
    vf = torch.zeros(3, 32, 4)
    vf[:, 0] = 1.0
    pl = {"voxel_features": vf, "voxel_coords": torch.tensor([[0, 0, 50, 50], [1, 0, 50, 50], [1, 0, 60, 60]]),
          "voxel_num_points": torch.tensor([1, 1, 1])}
    rng = [-140.8, -40, -3, 140.8, 40, 1]
    vs = [0.4, 0.4, 4]
    x, y = -140.8 + 50 * 0.4 + 0.2, -40 + 50 * 0.4 + 0.2           # pillar (y=50, x=50)
    pts = np.array([[x, y, -1.0, 0.5], [x + 4, y, -1.0, 0.5]], np.float32)
    out = P.append_points_to_voxels(pl, 1, pts, rng, vs)
    assert out["voxel_num_points"].tolist()[:3] == [1, 2, 1]          # agent 1's existing pillar
    assert len(out["voxel_num_points"]) == 4                         # one new pillar
    assert out["voxel_coords"][3].tolist() == [1, 0, 50, 60]
    assert torch.equal(out["voxel_features"][0], vf[0])


def test_harm_label_signs():
    g = corners(10, 0, -1, 3.9, 1.6, 1.56, 0)[None]
    fp = corners(20, 0, -1, 3.9, 1.6, 1.56, 0)[None]                # same tile? x=20 vs 10 -> different tiles
    assert local_error(np.zeros((0, 8, 3)), g) == 1.0
    d_add_real = harm_D(g, np.zeros((0, 8, 3)), g)                   # keeping adds a TP
    assert label(sum(d_add_real.values())) == "USEFUL"
    d_add_fake = harm_D(fp, np.zeros((0, 8, 3)), np.zeros((0, 8, 3)))
    assert label(sum(d_add_fake.values())) == "HARMFUL"
    assert label(0.5) == "NEUTRAL" and label(-0.5) == "NEUTRAL"      # boundary convention D-35


INFERENCE_DIRS = ("fusion", "geometry", "effects", "model", "reliability")


def test_inference_code_cannot_import_gt_labels():
    for d in INFERENCE_DIRS:
        for f in glob.glob(os.path.join(ROOT, "src", "mint", d, "*.py")):
            tree = ast.parse(open(f).read())
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    mod = node.module if isinstance(node, ast.ImportFrom) else ",".join(a.name for a in node.names)
                    assert "mint.eval" not in (mod or ""), f"{f} imports {mod}"
                    assert "attacks" not in (mod or ""), f"{f} imports {mod}"
