"""X2: ray-consistent spoof (evaluation only). spoof_feat whose destination is chosen so that the
spoofed box is KNOWN to the receiver and NOT dropped by B-RAY (worst case: the attacker knows the
receiver's scan, as for spoof_blind). Mirrors blind.attack_spoof_blind with the opposite predicate."""
import numpy as np

from mint.attacks import patches as P
from mint.attacks.blind import patch_shift_m, translate_box
from mint.reliability.baselines import b_ray_verdict, box_rays


def consistent(recv_pts, box):
    r = box_rays(recv_pts, box)
    v = b_ray_verdict(r)
    return v == "keep", r


def attack_spoof_raycons(feats, a, gt, att_pts, recv_pts, rng, min_att_pts=20, contains_origin=None, tries=300):
    gt_xy = gt.mean(1)[:, :2] if len(gt) else np.zeros((0, 2))
    vis = [j for j in range(len(gt)) if P.points_in_box(att_pts, gt[j]).sum() >= min_att_pts
           and not (contains_origin is not None and contains_origin(gt[j], 0.2))]
    led = {"family": "spoof_raycons", "attacker": a, "eligible_targets": len(vis), "applied": False}
    if not vis:
        return feats, led
    j = int(rng.choice(vis))
    cx, cy = gt_xy[j]
    src = P.coarse_patch(cx, cy, P.box_half(gt[j]))
    if not P.in_grid(src, feats):
        return feats, led
    for k in range(tries):
        p = P.sample_free_patch(rng, src, feats, gt_xy, tries=1)
        if p is None:
            continue
        ok, r = consistent(recv_pts, translate_box(gt[j], *patch_shift_m(src, p)))
        if ok:
            new = [f.clone() for f in feats]
            P.copy_patch(new, a, src, p)
            dx, dy = patch_shift_m(src, p)
            led.update(applied=True, source_gt=j, dst_center=[round(v, 2) for v in P.patch_center(p)],
                       shift_m=[round(dx, 2), round(dy, 2)], predicted_box_rays={"SUP": r["SUP"], "TRAV": r["TRAV"]},
                       dst_tries=k + 1)
            return new, led
    led["dst_tries"] = tries
    return feats, led
