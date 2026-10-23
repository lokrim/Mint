"""Counterfactual effects of one contribution (methodology_candidates.md §0).

Compare post-NMS boxes with all contributions (Y+) and with sender i excluded (Y-):
  ADD     box in Y+ unmatched in Y-        (contribution asserts an object)
  REMOVE  box in Y- unmatched in Y+        (contribution asserts absence)
  SHIFT   matched, centre moved > d_shift m or yaw changed > yaw_shift deg
Boxes are OpenCOOD corners (N, 8, 3). Tile attribution uses the box centre in either version (D-22).
"""
import numpy as np
from scipy.optimize import linear_sum_assignment
from shapely.geometry import Polygon


def polys(c):
    return [Polygon(b[:4, :2]) for b in c]


def bev_iou_matrix(a, b):
    pa, pb = polys(a), polys(b)
    m = np.zeros((len(pa), len(pb)))
    for i, p in enumerate(pa):
        for j, q in enumerate(pb):
            inter = p.intersection(q).area
            if inter > 0:
                m[i, j] = inter / (p.area + q.area - inter)
    return m


def yaw_of(c):
    v = c[0] - c[3]
    return np.arctan2(v[1], v[0])


def effects(Bp, Sp, Bm, Sm, iou_match=0.1, d_shift=0.3, yaw_shift_deg=10.0):
    Bp = np.zeros((0, 8, 3)) if Bp is None else np.asarray(Bp)
    Bm = np.zeros((0, 8, 3)) if Bm is None else np.asarray(Bm)
    out = []
    iou = bev_iou_matrix(Bp, Bm) if len(Bp) and len(Bm) else np.zeros((len(Bp), len(Bm)))
    mp, mm = set(), set()
    if iou.size:
        r, c = linear_sum_assignment(-iou)
        for i, j in zip(r, c):
            if iou[i, j] >= iou_match:
                mp.add(i); mm.add(j)
                d = np.linalg.norm(Bp[i].mean(0)[:2] - Bm[j].mean(0)[:2])
                dy = abs(np.degrees(np.angle(np.exp(1j * (yaw_of(Bp[i]) - yaw_of(Bm[j]))))))
                dy = min(dy, 180 - dy)          # box heading ambiguity
                if d > d_shift or dy > yaw_shift_deg:
                    out.append({"type": "SHIFT", "plus": Bp[i], "minus": Bm[j], "d": float(d), "dyaw": float(dy),
                                "score_plus": float(Sp[i]), "score_minus": float(Sm[j])})
    for i in range(len(Bp)):
        if i not in mp:
            out.append({"type": "ADD", "plus": Bp[i], "minus": None, "score_plus": float(Sp[i])})
    for j in range(len(Bm)):
        if j not in mm:
            out.append({"type": "REMOVE", "plus": None, "minus": Bm[j], "score_minus": float(Sm[j])})
    return out


def tile_of(box, pc_range, tile_m):
    x, y = box.mean(0)[:2]
    return int(np.floor((y - pc_range[1]) / tile_m)), int(np.floor((x - pc_range[0]) / tile_m))


def gt_match(box, gt, thr):
    if box is None or gt is None or len(gt) == 0:
        return 0.0
    return float(bev_iou_matrix(box[None], np.asarray(gt)).max())
