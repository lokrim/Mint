"""Evaluation-only attack family "spoof_blind" (E4): worst-case visibility-aware spoofing.

Same as spoof_feat (patches.py, A-F2a): copy the attacker's own feature patch around a real
object to a free location. The destination is restricted to places where the spoofed box would
have fewer than `max_rays` receiver rays (SUP + TRAV of the receiver's own scan through the box
core, rays.classify_points), i.e. where MINT's evidence is UNKNOWN and R1 keeps the sender.
The attacker is assumed to know the receiver's scan (worst case). It measures the known bypass;
it is not a method input and is never used to fit anything.

Predicted spoofed box = the source GT box translated by the patch shift (an integer number of
3.2 m coarse cells), keeping yaw and z. The detector's box can differ slightly, so the realized
effect is re-measured by the evaluation; this module only chooses the destination.
"""
import numpy as np

from mint.attacks import patches as P
from mint.geometry.rays import classify_points

MAX_RAYS = 3


def patch_shift_m(src, dst):
    """Metric (dx, dy) of moving patch src onto dst (same cell shape)."""
    return (dst[0] - src[0]) * P.COARSE_M, (dst[2] - src[2]) * P.COARSE_M


def translate_box(corners, dx, dy):
    c = np.array(corners, dtype=np.float64, copy=True)
    c[:, 0] += dx
    c[:, 1] += dy
    return c


def receiver_rays(recv_pts, box):
    """SUP + TRAV receiver rays through the box core; None for a box containing the receiver."""
    r = classify_points(recv_pts, box)
    return None if r["self_box"] else r["SUP"] + r["TRAV"]


def sample_blind_patch(rng, src, feats, gt_xy, src_box, recv_pts, max_rays=MAX_RAYS, tries=300):
    """First of up to `tries` random free patches (patches.sample_free_patch, one draw each) whose
    translated source box has < max_rays receiver rays. Returns (patch, rays, tries_used) or
    (None, None, tries)."""
    for k in range(tries):
        p = P.sample_free_patch(rng, src, feats, gt_xy, tries=1)
        if p is None:
            continue
        n = receiver_rays(recv_pts, translate_box(src_box, *patch_shift_m(src, p)))
        if n is not None and n < max_rays:
            return p, n, k + 1
    return None, None, tries


def attack_spoof_blind(feats, a, gt, att_pts, recv_pts, rng, min_att_pts=20, contains_origin=None):
    """spoof_feat with a receiver-blind destination. Returns (new feats, ledger); feats untouched
    (ledger applied=False) if no target or no blind destination is found."""
    gt_xy = gt.mean(1)[:, :2] if len(gt) else np.zeros((0, 2))
    vis = [j for j in range(len(gt)) if P.points_in_box(att_pts, gt[j]).sum() >= min_att_pts
           and not (contains_origin is not None and contains_origin(gt[j], 0.2))]
    led = {"family": "spoof_blind", "attacker": a, "eligible_targets": len(vis), "applied": False}
    if not vis:
        return feats, led
    j = int(rng.choice(vis))
    cx, cy = gt_xy[j]
    src = P.coarse_patch(cx, cy, P.box_half(gt[j]))
    if not P.in_grid(src, feats):
        return feats, led
    dst, n, used = sample_blind_patch(rng, src, feats, gt_xy, gt[j], recv_pts)
    led["dst_tries"] = used
    if dst is None:
        return feats, led
    new = [f.clone() for f in feats]
    P.copy_patch(new, a, src, dst)
    dx, dy = patch_shift_m(src, dst)
    led.update(applied=True, source_gt=j, dst_center=[round(v, 2) for v in P.patch_center(dst)],
               shift_m=[round(dx, 2), round(dy, 2)], predicted_box_rays=int(n))
    return new, led
