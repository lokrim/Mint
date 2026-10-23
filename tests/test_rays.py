"""Property and counterexample tests for mint.geometry.rays (plan: Stage 2 tests)."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
from mint.geometry.rays import RangeImage, box_frame, classify_box, ray_obb  # noqa: E402


def corners(cx, cy, cz, l, w, h, yaw):
    t = np.array([[1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, -1],
                  [1, -1, 1], [1, 1, 1], [-1, 1, 1], [-1, -1, 1]]) / 2 * np.array([l, w, h])
    c, s = np.cos(yaw), np.sin(yaw)
    rot = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return t @ rot.T + np.array([cx, cy, cz])


def inside(p, cen, ax, half):
    q = (p - cen) @ ax.T
    return np.all(np.abs(q) <= half + 1e-9, axis=-1)


def test_box_frame_roundtrip():
    c = corners(5, -2, 0.3, 4.0, 1.8, 1.5, 0.7)
    cen, ax, half = box_frame(c)
    assert np.allclose(cen, [5, -2, 0.3])
    assert np.allclose(half, [2.0, 0.9, 0.75])
    assert np.allclose(ax @ ax.T, np.eye(3))


def test_ray_obb_matches_bruteforce():
    rng = np.random.default_rng(0)
    for _ in range(200):
        c = corners(*rng.uniform(-20, 20, 2), rng.uniform(-1, 1), *rng.uniform(0.5, 5, 3),
                    rng.uniform(-np.pi, np.pi))
        cen, ax, half = box_frame(c)
        d = rng.normal(size=(64, 3))
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        # aim half the rays at the box
        d[:32] = (cen + rng.uniform(-0.5, 0.5, (32, 3)) * half * 2) @ np.eye(3)
        d[:32] /= np.linalg.norm(d[:32], axis=1, keepdims=True)
        t_in, t_out = ray_obb(d, cen, ax, half)
        ts = np.linspace(0, 60, 6001)
        for k in range(d.shape[0]):
            ins = inside(ts[:, None] * d[k], cen, ax, half)
            if ins.any():
                assert t_in[k] <= t_out[k]
                assert abs(ts[ins].min() - t_in[k]) < 0.02 and abs(ts[ins].max() - t_out[k]) < 0.02
            else:
                assert t_in[k] > t_out[k] - 0.02


def synthetic_lidar(scene_fn, n_rings=32, n_cols=720, el=(-15, 5)):
    """Ray-cast a scene function (dirs -> range or nan) into a point cloud."""
    els = np.radians(np.linspace(el[1], el[0], n_rings))
    azs = -np.pi + (np.arange(n_cols) + 0.5) * 2 * np.pi / n_cols
    E, A = np.meshgrid(els, azs, indexing="ij")
    d = np.stack([np.cos(E) * np.cos(A), np.cos(E) * np.sin(A), np.sin(E)], -1).reshape(-1, 3)
    r = scene_fn(d)
    ok = np.isfinite(r)
    return d[ok] * r[ok, None], n_rings, n_cols


def wall_and_box(box_c, solid=True, occluder=None):
    cen, ax, half = box_frame(box_c)

    def scene(d):
        r = np.full(d.shape[0], np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            r_wall = np.where(d[:, 0] > 1e-6, 40.0 / d[:, 0], np.nan)   # wall at x = 40
        r = np.where(np.isfinite(r_wall) & (np.abs(d[:, 2] * r_wall) < 30), r_wall, r)
        if solid:
            t_in, t_out = ray_obb(d, cen, ax, half)
            r = np.where((t_in <= t_out) & (t_in < np.nan_to_num(r, nan=1e9)), t_in, r)
        if occluder is not None:
            oc, oa, oh = box_frame(occluder)
            t_in, t_out = ray_obb(d, oc, oa, oh)
            r = np.where((t_in <= t_out) & (t_in < np.nan_to_num(r, nan=1e9)), t_in, r)
        return r
    return scene


BOX = corners(15, 0, -0.2, 4.0, 1.8, 1.6, 0.2)


def test_ring_discovery():
    pts, nr, nc = synthetic_lidar(wall_and_box(BOX))
    ri = RangeImage.from_points(pts, n_cols=nc)
    assert ri.stats["rings"] == nr


def test_solid_box_supported():
    pts, _, nc = synthetic_lidar(wall_and_box(BOX, solid=True))
    c = classify_box(RangeImage.from_points(pts, n_cols=nc), BOX)
    assert c["SUP"] > 10 and c["TRAV"] == 0


def test_empty_box_traversed():
    """Counterexample: a claimed box in free space in front of a wall -> traversal."""
    pts, _, nc = synthetic_lidar(wall_and_box(BOX, solid=False))
    c = classify_box(RangeImage.from_points(pts, n_cols=nc), BOX)
    assert c["TRAV"] > 10 and c["SUP"] == 0


def test_occluded_box_is_not_evidence():
    """Counterexample: an occluder in front -> OCC only, never SUP/TRAV (status unknown)."""
    occ = corners(7, 0, -0.2, 1.0, 6.0, 4.0, 0.0)
    pts, _, nc = synthetic_lidar(wall_and_box(BOX, solid=False, occluder=occ))
    c = classify_box(RangeImage.from_points(pts, n_cols=nc), BOX)
    assert c["OCC"] > 10 and c["SUP"] == 0 and c["TRAV"] == 0


def test_no_return_is_not_traversal():
    """Counterexample: no wall behind an empty box -> NR slots, never counted as TRAV."""
    def sky(d):
        return np.full(d.shape[0], np.nan)
    pts, _, nc = synthetic_lidar(wall_and_box(BOX, solid=True))   # need rings for directions
    ri = RangeImage.from_points(pts, n_cols=nc)
    ri.rng[:] = np.nan
    c = classify_box(ri, BOX)
    assert c["TRAV"] == 0 and c["SUP"] == 0 and c["NR"] > 10


def test_each_ray_counted_once():
    pts, _, nc = synthetic_lidar(wall_and_box(BOX, solid=True))
    c = classify_box(RangeImage.from_points(pts, n_cols=nc), BOX)
    assert c["SUP"] + c["TRAV"] + c["OCC"] + c["NR"] == c["candidates"]


def test_pointwise_matches_slot_counts_on_exact_grid():
    from mint.geometry.rays import classify_points
    for solid in (True, False):
        pts, _, nc = synthetic_lidar(wall_and_box(BOX, solid=solid))
        a = classify_box(RangeImage.from_points(pts, n_cols=nc), BOX)
        b = classify_points(pts, BOX)
        assert (a["SUP"], a["TRAV"], a["OCC"]) == (b["SUP"], b["TRAV"], b["OCC"])


def test_receiver_inside_box_is_not_applicable():
    from mint.geometry.rays import classify_points
    ego = corners(0.5, 0, -0.5, 4.5, 2.0, 1.6, 0.0)
    pts, _, _ = synthetic_lidar(wall_and_box(BOX))
    c = classify_points(pts, ego)
    assert c["self_box"] and c["candidates"] == 0


def test_roof_mounted_sensor_above_own_box_is_self():
    """Regression (Stage-2 finding): sensor 0.3 m above the ego box top must still be 'self'."""
    from mint.geometry.rays import classify_points
    ego = corners(0.5, 0, -1.0, 4.5, 2.0, 1.5, 0.0)          # top at z = -0.25, sensor at 0
    pts, _, _ = synthetic_lidar(wall_and_box(BOX))
    assert classify_points(pts, ego)["self_box"]
