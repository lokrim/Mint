"""MINT-v0.0 online inference for one receiver frame (no ground truth anywhere in this module).

  feats   = agent_features(model, batch["ego"])                    # unchanged AttFuse encoder
  Y+      = decode(fuse(all agents))                                # plain AttFuse output
  Y-(i)   = decode(fuse(sender i excluded)) for every sender         # n_senders extra decodes
  effects = ADD / REMOVE / SHIFT between Y+ and Y-(i)                # effects.py
  rays    = receiver's own scan through each effect box             # rays.py (+ ground.py)
  rel     = v0.assess(effects)                                      # KNOWN / UNKNOWN, raw scores
  output  = decode(fuse with sender i excluded only in its gated tiles) iff anything is gated
Extra cost per frame: n_senders decodes + at most one final decode; zero extra bytes on the wire.
"""
import time

import numpy as np
import torch

from mint.model.attfuse_parts import agent_features, decode, fuse_scale
from mint.fusion.compose import candidates, finalize, tile_include_masks
from mint.geometry.rays import classify_points
from mint.geometry.ground import classify_points_ground, ground_mask
from mint.effects.effects import effects as get_effects, tile_of
from mint.reliability import v0

TILE_M = 6.4


def receiver_ray_record(pts, gmask, box):
    if box is None:
        return None
    a = classify_points(pts, box)
    g = classify_points_ground(pts, gmask, box)
    return {"std": {k: a[k] for k in ("SUP", "TRAV", "OCC", "candidates")},
            "gnd": {k: g[k] for k in ("SUP", "TRAV", "OCC", "TRAV_GROUND", "candidates")},
            "self_box": bool(a["self_box"]), "range_m": round(float(np.linalg.norm(np.asarray(box).mean(0)[:2])), 2)}


def _decode(model, pp, ego, feats, n, masks=None):
    psm, rm = decode(model, [fuse_scale(f[:n], None if masks is None else masks[k])[0] for k, f in enumerate(feats)])
    return candidates(pp, psm, rm, ego["anchor_box"], ego["transformation_matrix"])


@torch.no_grad()
def mint_v0_frame(model, pp, batch, receiver_xyz, pc_range, params=v0.Params(), feats=None):
    """Returns dict(boxes, scores, reliability, timing). receiver_xyz: receiver scan, sensor frame."""
    t = {}
    t0 = time.perf_counter()
    ego = batch["ego"]
    n = int(ego["record_len"][0])
    if feats is None:
        feats, _ = agent_features(model, ego)
    t["encode"] = time.perf_counter() - t0
    t1 = time.perf_counter()
    yp, sp = finalize(pp, _decode(model, pp, ego, feats, n))
    t["plain"] = time.perf_counter() - t1
    t2 = time.perf_counter()
    eff = []
    for i in range(1, n):
        m = [torch.ones((n, f.shape[2], f.shape[3]), dtype=torch.bool) for f in feats]
        for x in m:
            x[i] = False
        ym, sm = finalize(pp, _decode(model, pp, ego, feats, n, m))
        for e in get_effects(yp, sp, ym, sm):
            eff.append({"sender": i, "type": e["type"], "plus": e["plus"], "minus": e["minus"],
                        "tile_plus": None if e["plus"] is None else tile_of(e["plus"], pc_range, TILE_M),
                        "tile_minus": None if e["minus"] is None else tile_of(e["minus"], pc_range, TILE_M)})
    t["counterfactual"] = time.perf_counter() - t2
    t3 = time.perf_counter()
    pts = np.asarray(receiver_xyz, np.float64)
    gmask, _ = ground_mask(pts) if params.variant == "gnd" else (np.zeros(len(pts), bool), None)
    for e in eff:
        e["rays_plus"] = receiver_ray_record(pts, gmask, e["plus"])
        e["rays_minus"] = receiver_ray_record(pts, gmask, e["minus"])
    rel = v0.assess(eff, params)
    t["evidence"] = time.perf_counter() - t3
    t4 = time.perf_counter()
    choice = v0.gating_choice(rel)
    if choice:
        masks = tile_include_masks(n, [(f.shape[2], f.shape[3]) for f in feats], choice)
        yp, sp = finalize(pp, _decode(model, pp, ego, feats, n, masks))
    t["final"] = time.perf_counter() - t4
    return {"boxes": yp, "scores": sp, "reliability": rel, "choice": choice, "timing_s": t}
