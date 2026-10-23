"""OFFLINE ONLY: ground-truth harm labels D (contract §5.1, notation D-35). Never import this from
inference code (tests/test_purity.py enforces it).

  L_u(Y) = w_fp * #FP + w_fn * #FN + w_loc * sum_TP (1 - IoU)
over GT boxes and predicted boxes whose BEV centres lie in tile u; matching is Hungarian on BEV
IoU with threshold `iou_thr` (vehicles: 0.5).
  D = L_u(Y+) - L_u(Y-(i,u));  HARMFUL iff D > m, USEFUL iff D < -m, NEUTRAL otherwise.
"""
import numpy as np
from scipy.optimize import linear_sum_assignment

from mint.effects.effects import bev_iou_matrix

TILE_M = 6.4
PC_RANGE = (-140.8, -40.0)


def tiles_of(corners):
    if len(corners) == 0:
        return np.zeros((0, 2), np.int64)
    c = np.asarray(corners).mean(1)
    return np.stack([np.floor((c[:, 1] - PC_RANGE[1]) / TILE_M), np.floor((c[:, 0] - PC_RANGE[0]) / TILE_M)],
                    1).astype(np.int64)


def local_error(pred, gt, iou_thr=0.5, w_fp=1.0, w_fn=1.0, w_loc=0.5):
    if len(pred) == 0 or len(gt) == 0:
        return w_fp * len(pred) + w_fn * len(gt)
    iou = bev_iou_matrix(np.asarray(pred), np.asarray(gt))
    r, c = linear_sum_assignment(-iou)
    ok = iou[r, c] >= iou_thr
    tp = int(ok.sum())
    return w_fp * (len(pred) - tp) + w_fn * (len(gt) - tp) + w_loc * float((1 - iou[r, c][ok]).sum())


def tile_errors(pred, gt, iou_thr=0.5):
    """{tile: L_u} for every tile holding a predicted or GT centre."""
    tp, tg = tiles_of(pred), tiles_of(gt)
    keys = set(map(tuple, tp)) | set(map(tuple, tg))
    out = {}
    for k in keys:
        mp = np.all(tp == k, 1) if len(tp) else np.zeros(0, bool)
        mg = np.all(tg == k, 1) if len(tg) else np.zeros(0, bool)
        out[k] = local_error(np.asarray(pred)[mp] if len(pred) else pred,
                             np.asarray(gt)[mg] if len(gt) else gt, iou_thr)
    return out


def harm_D(y_plus, y_minus, gt, iou_thr=0.5):
    """{tile: D} over tiles where Y+ and Y- differ or hold boxes. y_* are corner arrays."""
    ep, em = tile_errors(y_plus, gt, iou_thr), tile_errors(y_minus, gt, iou_thr)
    eg = tile_errors(np.zeros((0, 8, 3)), gt, iou_thr)
    out = {}
    for k in set(ep) | set(em):
        out[k] = ep.get(k, eg.get(k, 0.0)) - em.get(k, eg.get(k, 0.0))
    return out


def label(d, m=0.5):
    return "HARMFUL" if d > m else ("USEFUL" if d < -m else "NEUTRAL")
