"""MINT online inference for one receiver frame (no ground truth anywhere in this module).

  feats   = per-agent features (receiver encodes its own scan; sender features arrive on the wire)
  Y+      = decode(fuse(all agents))                                # plain AttFuse output
  Y-(i)   = decode(fuse(sender i excluded)) for every sender         # n_senders counterfactuals
  effects = ADD / REMOVE / SHIFT between Y+ and Y-(i)                # effects.py
  rays    = receiver's own scan through each effect box             # rays.py (+ ground.py)
  rel     = rule.assess(effects)                                    # v0 (theta) or r1 (Wilson)
  output  = finalize(compose(decodes, gating choice))               # no extra decode (E1 A1)

Post-fusion computation is pixel-local (V-03), so a tile-wise gated output equals the tile-wise
composition of the decodes already computed (mint.fusion.compose). A tile in which two or more
senders are gated needs the decode with that whole subset excluded; it is computed only then
(never with 2 agents) and counted in `extra_decodes`.

Counterfactual modes (E1 A3; identical outputs up to float rounding, checked by the runner):
  sequential  one decode per sender
  batched     the n-1 counterfactual decodes in one forward pass (batch dimension)
  footprint   per sender, decode only the tiles in `footprints[i]` and copy Y+ heads elsewhere.
              NOT exact in general: outside its points a sender's feature is a non-zero constant
              (BatchNorm bias) that still takes softmax attention weight, so excluding it changes
              the fused feature there too. Diagnostic only.
Extra cost per frame: the counterfactual decodes; zero extra bytes on the wire.
"""
import time

import numpy as np
import torch

from mint.model.attfuse_parts import agent_features, decode, decode_batch, fuse_scale
from mint.fusion.compose import TILE_PX, candidates, compose, finalize
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


def _exclude_masks(feats, n, s):
    if not s:
        return None
    out = []
    for f in feats:
        m = torch.ones((n, f.shape[2], f.shape[3]), dtype=torch.bool)
        for i in s:
            m[i] = False
        out.append(m)
    return out


def _heads(model, feats, n, masks=None):
    return decode(model, [fuse_scale(f[:n], None if masks is None else masks[k])[0] for k, f in enumerate(feats)])


def _cands(pp, ego, psm, rm):
    return candidates(pp, psm, rm, ego["anchor_box"], ego["transformation_matrix"])


def _to_tiles(x, px):
    """[C, H, W] -> [R, Cc, C, px, px] (rows zero-padded to a whole number of tiles)."""
    c, h, w = x.shape
    r = -(-h // px)
    x = torch.nn.functional.pad(x, (0, 0, 0, r * px - h))
    return x.reshape(c, r, px, w // px, px).permute(1, 3, 0, 2, 4)


def _from_tiles(full, tiles_out, sel):
    """Write per-tile head outputs [T, C, 8, 8] into a copy of full [1, C, H, W] at tiles sel."""
    _, c, h, w = full.shape
    t = _to_tiles(full[0].clone(), TILE_PX)                 # R, Cc, C, 8, 8
    t[sel[:, 0], sel[:, 1]] = tiles_out
    r, cc = t.shape[0], t.shape[1]
    return t.permute(2, 0, 3, 1, 4).reshape(c, r * TILE_PX, cc * TILE_PX)[:, :h].unsqueeze(0)


def counterfactual_heads(model, feats, n, senders, mode, base=None, footprints=None):
    """{i: (psm, rm)} for Y-(i), i in senders."""
    if mode == "sequential":
        return {i: _heads(model, feats, n, _exclude_masks(feats, n, [i])) for i in senders}
    fused = [[fuse_scale(f[:n], m[k])[0] for k, f in enumerate(feats)]
             for m in (_exclude_masks(feats, n, [i]) for i in senders)]
    if mode == "batched":
        psm, rm = decode_batch(model, [torch.stack([fz[k] for fz in fused]) for k in range(len(feats))])
        return {i: (psm[j:j + 1], rm[j:j + 1]) for j, i in enumerate(senders)}
    if mode == "footprint":
        w_head = feats[0].shape[3]
        out = {}
        for j, i in enumerate(senders):
            sel = torch.nonzero(torch.as_tensor(footprints[i]))
            if len(sel) == 0:
                out[i] = base
                continue
            parts = []
            for k, f in enumerate(fused[j]):
                px = TILE_PX * f.shape[2] // w_head
                parts.append(_to_tiles(f, px)[sel[:, 0], sel[:, 1]])
            psm_t, rm_t = decode_batch(model, parts)
            out[i] = (_from_tiles(base[0], psm_t, sel), _from_tiles(base[1], rm_t, sel))
        return out
    raise ValueError(mode)


def pillar_footprints(batch_ego, n, grid=(200, 704), pillars_per_tile=16, dilate=0):
    """{i: bool [tile rows, tile cols]} tiles holding any pillar of agent i (optionally dilated)."""
    c = batch_ego["processed_lidar"]["voxel_coords"]
    out = {}
    for i in range(1, n):
        s = c[c[:, 0] == i]
        m = torch.zeros(grid)
        m[s[:, 2].long(), s[:, 3].long()] = 1
        t = torch.nn.functional.max_pool2d(m[None, None], pillars_per_tile, pillars_per_tile, ceil_mode=True)
        if dilate:
            t = torch.nn.functional.max_pool2d(t, 2 * dilate + 1, 1, dilate)
        out[i] = t[0, 0] > 0
    return out


@torch.no_grad()
def mint_frame(model, pp, batch, receiver_xyz, pc_range, params=v0.Params(), feats=None, rule=v0,
               cf_mode="sequential", footprints=None):
    """Returns dict(boxes, scores, reliability, choice, timing_s, extra_decodes).

    receiver_xyz: receiver scan, sensor frame. feats: per-scale [n, C, H, W] (encoded here if None,
    timed as encode_all). Timing keys: plain (fusion + decode + post-process of Y+), counterfactual
    (Y-(i) decodes + post-process + effects), evidence (rays + rule), compose (composition + final
    post-process, plus any multi-sender subset decode).
    """
    t = {}
    ego = batch["ego"]
    n = int(ego["record_len"][0])
    if feats is None:
        t0 = time.perf_counter()
        feats, _ = agent_features(model, ego)
        t["encode_all"] = time.perf_counter() - t0
    else:
        n = feats[0].shape[0]          # may exceed record_len when features are replicated (timing)
    t1 = time.perf_counter()
    base = _heads(model, feats, n)
    cands = {frozenset(): _cands(pp, ego, *base)}
    yp, sp = finalize(pp, cands[frozenset()])
    t["plain"] = time.perf_counter() - t1
    t2 = time.perf_counter()
    senders = list(range(1, n))
    heads = counterfactual_heads(model, feats, n, senders, cf_mode, base, footprints)
    eff = []
    for i in senders:
        cands[frozenset([i])] = _cands(pp, ego, *heads[i])
        ym, sm = finalize(pp, cands[frozenset([i])])
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
    rel = rule.assess(eff, params)
    t["evidence"] = time.perf_counter() - t3
    t4 = time.perf_counter()
    choice = v0.gating_choice(rel)
    extra = 0
    for s in set(choice.values()) - set(cands):
        cands[s] = _cands(pp, ego, *_heads(model, feats, n, _exclude_masks(feats, n, s)))
        extra += 1
    if choice:
        yp, sp = finalize(pp, compose(cands, choice))
    t["compose"] = time.perf_counter() - t4
    return {"boxes": yp, "scores": sp, "reliability": rel, "choice": choice, "timing_s": t,
            "extra_decodes": extra, "cands": cands, "effects": eff}


def mint_v0_frame(model, pp, batch, receiver_xyz, pc_range, params=v0.Params(), feats=None):
    """MINT-v0.0 (backwards-compatible name)."""
    return mint_frame(model, pp, batch, receiver_xyz, pc_range, params, feats, v0)
