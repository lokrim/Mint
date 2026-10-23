"""E5 comparison methods (D-56). None has a tunable parameter.

* ``ego_only``: the receiver's output with every sender excluded everywhere
  (``cands[frozenset(senders)]``, already decoded by the dense counterfactual).
* ``b_ray``: box-level receiver-ray filter on the final Y+ (no counterfactual). For every final box,
  the receiver's own ray counts are computed with the same code and count variant as R1
  (``rays.classify_points``, standard count SUP / (SUP + TRAV)). A box is dropped iff it is KNOWN
  (>= n_min = 3 rays and not the receiver's own box) and the Wilson 95% upper bound of s is < 0.5,
  the same test as R1's ADD gate. Every other box is kept (UNKNOWN / self = keep).
* ``assess_noremove``: R1 with REMOVE verdicts never gating. The mirror ("useful") conditions are
  unchanged, so a resolvably useful REMOVE still blocks its unit from gating. ADD and SHIFT are as R1.

The Wilson bound is a resolvability margin on spatially correlated ray counts, not a probability
(see r1.py).
"""
import numpy as np

from mint.geometry.rays import classify_points
from mint.reliability import r1
from mint.reliability.v0 import Params, Reliability, effect_status, units


def ego_only(cands, n):
    """Candidates of the receiver alone (all senders 1..n-1 excluded)."""
    return cands[frozenset(range(1, n))]


def box_rays(pts, box):
    """Receiver ray record of one box, R1's standard count: {"SUP", "TRAV", "self_box"}."""
    a = classify_points(pts, box)
    return {"SUP": a["SUP"], "TRAV": a["TRAV"], "self_box": bool(a["self_box"])}


def b_ray_verdict(r, n_min=Params().n_min):
    """'drop' iff KNOWN and Wilson-95 upper bound of s < 0.5; 'keep_unknown' / 'keep_self' / 'keep'."""
    if r["self_box"]:
        return "keep_self"
    n = r["SUP"] + r["TRAV"]
    if n < n_min:
        return "keep_unknown"
    _, hi = r1.wilson(r["SUP"], n)
    return "drop" if hi < 0.5 else "keep"


def b_ray(boxes, scores, pts=None, rays=None, n_min=Params().n_min):
    """Filter final boxes. rays: precomputed box_rays() per box (else computed from pts).

    Returns (boxes, scores, verdicts, rays)."""
    boxes = np.asarray(boxes)
    scores = np.asarray(scores)
    if rays is None:
        p = np.asarray(pts, np.float64)
        rays = [box_rays(p, b) for b in boxes]
    assert len(rays) == len(boxes)
    v = [b_ray_verdict(r, n_min) for r in rays]
    keep = np.array([x != "drop" for x in v], bool)
    if len(boxes) == 0:
        return boxes, scores, v, rays
    return boxes[keep], scores[keep], v, rays


def effect_verdict_noremove(e, variant="std"):
    v = r1.effect_verdict(e, variant)
    return "none" if e["type"] == "REMOVE" and v == "gate" else v


def assess_noremove(effects, p: Params = Params()):
    """r1.assess with REMOVE gate verdicts replaced by 'none' (same interface and statuses)."""
    out = {}
    for (i, t), effs in units(effects).items():
        st = [effect_status(e, p) for e in effs]
        if all(s == "KNOWN" for s in st):
            v = [effect_verdict_noremove(e, p.variant) for e in effs]
            g = "gate" in v and "useful" not in v
            out[(i, t)] = Reliability(i, t, "KNOWN", None, None, float(v.count("gate") - v.count("useful")), g,
                                      effects=effs)
            out[(i, t)].verdicts = v
        else:
            status = "NOT_APPLICABLE_SELF" if "NOT_APPLICABLE_SELF" in st else "UNKNOWN_NO_EVIDENCE"
            out[(i, t)] = Reliability(i, t, status, None, None, None, False, effects=effs)
    return out
