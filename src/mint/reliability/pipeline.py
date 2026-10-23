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
  trigger     (E3) per sender, decode only the tiles T(f) where Y+ has an anchor with score >= f
              (dilated by 1 tile); candidates elsewhere are absent from Y-(i), not copied from Y+.
              Fusion on tiles is bitwise equal to dense; the tile decode differs from the dense
              decode by float rounding. Misses REMOVE effects outside T(f); not adopted (E3 FAIL, D-49).
Extra cost per frame: the counterfactual decodes; zero extra bytes on the wire.
"""
import time
from contextlib import contextmanager

import numpy as np
import torch

from mint.model.attfuse_parts import agent_features, decode, decode_batch, fuse_scale
from mint.fusion.compose import TILE_PX, candidates, compose, finalize, tile_candidates
from mint.geometry.rays import classify_points
from mint.geometry.ground import classify_points_ground, ground_mask
from mint.effects.effects import effects as get_effects, tile_of
from mint.reliability import v0

TILE_M = 6.4


class Prof:
    """Optional sub-stage timer (E2 A1): prof.acc[stage] += seconds; a no-op when disabled."""

    def __init__(self, on=True):
        self.on, self.acc, self.stage = on, {}, None

    @contextmanager
    def __call__(self, name):
        if not self.on:
            yield
            return
        key = f"{self.stage}.{name}" if self.stage else name
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.acc[key] = self.acc.get(key, 0.0) + time.perf_counter() - t0


NOPROF = Prof(False)


class OpenCOODPost:
    """Post-processing as in E0/E1: compose.finalize (OpenCOOD nms_rotated) and effects.effects."""
    finalize = staticmethod(finalize)
    effects = staticmethod(get_effects)


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


def _heads(model, feats, n, masks=None, prof=NOPROF):
    with prof("fusion"):
        fused = [fuse_scale(f[:n], None if masks is None else masks[k])[0] for k, f in enumerate(feats)]
    with prof("deblocks_heads"):
        return decode(model, fused)


def _cands(pp, ego, psm, rm):
    return candidates(pp, psm, rm, ego["anchor_box"], ego["transformation_matrix"])


def _tile_cands(pp, ego, heads, sel, base):
    hw = tuple(base[0].shape[2:])
    if heads is None:
        a = base[0].shape[1]
        heads = (base[0].new_zeros((0, a, TILE_PX, TILE_PX)), base[1].new_zeros((0, base[1].shape[1], TILE_PX, TILE_PX)))
    return tile_candidates(pp, *heads, sel, ego["anchor_box"], ego["transformation_matrix"], hw)


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


def counterfactual_heads(model, feats, n, senders, mode, base=None, footprints=None, prof=NOPROF):
    """{i: (psm, rm)} for Y-(i), i in senders."""
    if mode == "sequential":
        return {i: _heads(model, feats, n, _exclude_masks(feats, n, [i]), prof) for i in senders}
    with prof("fusion"):
        fused = [[fuse_scale(f[:n], m[k])[0] for k, f in enumerate(feats)]
                 for m in (_exclude_masks(feats, n, [i]) for i in senders)]
    if mode == "batched":
        with prof("deblocks_heads"):
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


def trigger_mask(psm, f, dilate=1):
    """E3 T(f): bool [tile rows, tile cols], tiles holding any anchor with sigmoid(psm) >= f, dilated
    by `dilate` tiles (Chebyshev). psm: plain-path cls output [1, A, H, W]."""
    p = torch.sigmoid(psm[0]).amax(0)                                   # H, W
    h = p.shape[0]
    p = torch.nn.functional.pad(p, (0, 0, 0, -(-h // TILE_PX) * TILE_PX - h), value=0.0)
    t = torch.nn.functional.max_pool2d(p[None, None], TILE_PX, TILE_PX)[0, 0] >= f
    if dilate:
        t = torch.nn.functional.max_pool2d(t[None, None].float(), 2 * dilate + 1, 1, dilate)[0, 0] > 0
    return t


def tile_max_prob(psm):
    """Max anchor probability per tile [tile rows, tile cols] (float32; E3 cache)."""
    p = torch.sigmoid(psm[0]).amax(0)
    h = p.shape[0]
    p = torch.nn.functional.pad(p, (0, 0, 0, -(-h // TILE_PX) * TILE_PX - h), value=0.0)
    return torch.nn.functional.max_pool2d(p[None, None], TILE_PX, TILE_PX)[0, 0]


def gather_tiles(feats, n, sel):
    """Per scale: agent features of tiles sel laid out as [n, C, T*px, px] (fusion is pixel-local)."""
    w_head = feats[0].shape[3]
    out = []
    for f in feats:
        _, c, h, w = f.shape
        px = TILE_PX * w // w_head
        t = _to_tiles(f[:n].reshape(n * c, h, w), px)[sel[:, 0], sel[:, 1]]      # T, n*C, px, px
        out.append(t.reshape(len(sel), n, c, px, px).permute(1, 2, 0, 3, 4).reshape(n, c, len(sel) * px, px))
    return out


def trigger_heads(model, feats, n, senders, sel, prof=NOPROF):
    """{i: (psm_t [T, A, 8, 8], rm_t [T, 7A, 8, 8])} for Y-(i) on tiles sel only (one decode_batch)."""
    t = len(sel)
    if t == 0:
        return {i: None for i in senders}
    with prof("gather"):
        g = gather_tiles(feats, n, sel)
    with prof("fusion"):
        parts = [[] for _ in g]
        for i in senders:
            for k, x in enumerate(g):
                m = torch.ones((n, x.shape[2], x.shape[3]), dtype=torch.bool)
                m[i] = False
                y = fuse_scale(x, m)[0]                                     # C, T*px, px
                px = x.shape[3]
                parts[k].append(y.reshape(y.shape[0], t, px, px).permute(1, 0, 2, 3))
        parts = [torch.cat(p) for p in parts]
    with prof("deblocks_heads"):
        psm, rm = decode_batch(model, parts)
    return {i: (psm[j * t:(j + 1) * t], rm[j * t:(j + 1) * t]) for j, i in enumerate(senders)}


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
               cf_mode="sequential", footprints=None, post=OpenCOODPost, prof=NOPROF, trigger_f=None):
    """Returns dict(boxes, scores, reliability, choice, timing_s, extra_decodes).

    receiver_xyz: receiver scan, sensor frame. feats: per-scale [n, C, H, W] (encoded here if None,
    timed as encode_all). Timing keys: plain (fusion + decode + post-process of Y+), counterfactual
    (Y-(i) decodes + post-process + effects), evidence (rays + rule), compose (composition + final
    post-process, plus any multi-sender subset decode).
    post: post-processing implementation (finalize, effects); OpenCOODPost or the exact fast
    replacement mint.fusion.fastpost.FastPost (E2 A2). prof: optional sub-stage timer (E2 A1).
    cf_mode "trigger" (E3): Y-(i) only on the tiles T(trigger_f) of trigger_mask(); candidates outside
    T are absent from Y-(i) (not copied from Y+). Returned as "trigger" (bool tile mask).
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
    prof.stage = "plain"
    base = _heads(model, feats, n, None, prof)
    with prof("candidates"):
        cands = {frozenset(): _cands(pp, ego, *base)}
    with prof("finalize"):
        yp, sp = post.finalize(pp, cands[frozenset()])
    t["plain"] = time.perf_counter() - t1
    t2 = time.perf_counter()
    prof.stage = "counterfactual"
    senders = list(range(1, n))
    trig = None
    if cf_mode == "trigger":
        with prof("trigger"):
            trig = trigger_mask(base[0], trigger_f)
            sel = torch.nonzero(trig)
        heads = trigger_heads(model, feats, n, senders, sel, prof)
    else:
        heads = counterfactual_heads(model, feats, n, senders, cf_mode, base, footprints, prof)
    eff = []
    for i in senders:
        with prof("candidates"):
            if cf_mode == "trigger":
                cands[frozenset([i])] = _tile_cands(pp, ego, heads[i], sel, base)
            else:
                cands[frozenset([i])] = _cands(pp, ego, *heads[i])
        with prof("finalize"):
            ym, sm = post.finalize(pp, cands[frozenset([i])])
        with prof("effects"):
            for e in post.effects(yp, sp, ym, sm):
                eff.append({"sender": i, "type": e["type"], "plus": e["plus"], "minus": e["minus"],
                            "tile_plus": None if e["plus"] is None else tile_of(e["plus"], pc_range, TILE_M),
                            "tile_minus": None if e["minus"] is None else tile_of(e["minus"], pc_range, TILE_M)})
    t["counterfactual"] = time.perf_counter() - t2
    prof.stage = None
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
        yp, sp = post.finalize(pp, compose(cands, choice))
    t["compose"] = time.perf_counter() - t4
    return {"boxes": yp, "scores": sp, "reliability": rel, "choice": choice, "timing_s": t,
            "extra_decodes": extra, "cands": cands, "effects": eff, "trigger": trig}


def mint_v0_frame(model, pp, batch, receiver_xyz, pc_range, params=v0.Params(), feats=None):
    """MINT-v0.0 (backwards-compatible name)."""
    return mint_frame(model, pp, batch, receiver_xyz, pc_range, params, feats, v0)
