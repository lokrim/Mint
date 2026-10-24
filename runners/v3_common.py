"""preregistration_v3 helpers shared by the block-H PGD development runs and the final-test stream.

* compact model inputs (exact: rebuilt tensors are asserted equal to the originals),
* clean feature statistics (for sigma_k, D-65) and per-agent mean |feature| (B-NORM, D-66),
* re-computation of an E4 family's attacked features with the same rng (exactly e4_stream.frame_record's
  branch) so B-NORM sees what the receiver received,
* per-condition records in the E4 cache format plus `yplus_rays` (float64 scan),
* PGD condition records (D-65).
No method output depends on GT; GT enters only the attack placement of the E4 families (as before).
"""
import dataclasses
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import e0_stream as E  # noqa: E402  (shims + paths)

import numpy as np  # noqa: E402
import torch  # noqa: E402

from mint.attacks import pgd_stealth as PS  # noqa: E402
from mint.attacks import pgd_v3 as P  # noqa: E402
from mint.attacks.blind import attack_spoof_blind  # noqa: E402
from mint.effects.effects import effects as get_effects, tile_of  # noqa: E402
from mint.fusion.compose import finalize  # noqa: E402
from mint.geometry.rays import contains_origin  # noqa: E402
from mint.reliability import baselines as BL  # noqa: E402
from mint.reliability import bnorm  # noqa: E402

PGD_ATTACKER = 1


# ------------------------------------------------------------------ inputs
def compact_inputs(batch):
    """Lossless compact copy of what agent_features + decode_all read from a collated test batch."""
    ego = batch["ego"]
    pl = ego["processed_lidar"]
    nump = pl["voxel_num_points"].numpy()
    vf = pl["voxel_features"].numpy()
    pts = np.concatenate([vf[j, :k] for j, k in enumerate(nump)], 0) if len(nump) else np.zeros((0, 4), np.float32)
    return {"points": pts.astype(np.float32), "voxel_coords": pl["voxel_coords"].numpy().copy(),
            "voxel_num_points": nump.copy(), "max_points": int(vf.shape[1]), "record_len": ego["record_len"].numpy().copy(),
            "transformation_matrix": ego["transformation_matrix"].numpy().copy()}


def rebuild_batch(inp, anchor_box):
    nump = inp["voxel_num_points"]
    vf = np.zeros((len(nump), inp["max_points"], 4), np.float32)
    off = np.concatenate([[0], np.cumsum(nump)])
    for j, k in enumerate(nump):
        vf[j, :k] = inp["points"][off[j]:off[j + 1]]
    pl = {"voxel_features": torch.from_numpy(vf), "voxel_coords": torch.from_numpy(inp["voxel_coords"]),
          "voxel_num_points": torch.from_numpy(nump)}
    return {"ego": {"processed_lidar": pl, "record_len": torch.from_numpy(inp["record_len"]),
                    "anchor_box": torch.as_tensor(anchor_box), "transformation_matrix": torch.from_numpy(inp["transformation_matrix"])}}


def inputs_equal(batch, rebuilt):
    a, b = batch["ego"], rebuilt["ego"]
    ok = all(torch.equal(a["processed_lidar"][k], b["processed_lidar"][k]) for k in ("voxel_features", "voxel_coords",
                                                                                   "voxel_num_points"))
    return bool(ok and torch.equal(a["record_len"], b["record_len"]) and torch.equal(a["anchor_box"], b["anchor_box"])
                and torch.equal(a["transformation_matrix"], b["transformation_matrix"]))


# ------------------------------------------------------------------ feature statistics
def feat_moments(feats):
    """Per agent and scale: [count, sum, sum of squares, sum |x|] (float64), shape [n, K, 4]."""
    out = []
    for f in feats:
        x = f.double()
        cnt = float(x[0].numel())
        out.append(torch.stack([torch.full((x.shape[0],), cnt, dtype=torch.float64), x.sum(dim=(1, 2, 3)),
                                (x * x).sum(dim=(1, 2, 3)), x.abs().sum(dim=(1, 2, 3))], 1).numpy())
    return np.stack(out, 1)


def same(a, b):
    """Deep equality for ledgers (dict/list/np/torch/scalars)."""
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return isinstance(b, (list, tuple)) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if torch.is_tensor(a) or isinstance(a, np.ndarray):
        return (torch.is_tensor(b) or isinstance(b, np.ndarray)) and np.asarray(a).dtype == np.asarray(b).dtype \
            and np.array_equal(np.asarray(a), np.asarray(b))
    if dataclasses.is_dataclass(a) and not isinstance(a, type):
        return type(a) is type(b) and all(same(getattr(a, f.name), getattr(b, f.name)) for f in dataclasses.fields(a))
    if isinstance(a, float) and isinstance(b, float) and np.isnan(a) and np.isnan(b):
        return True
    return a == b


def attacked_feats(model, batch, fam, feats0, gt, att_pts, ego_pts, rng, pcr, vs):
    """Exactly e4_stream.frame_record's attack branch for one family (same rng key -> same result)."""
    led = {"family": fam, "applied": fam == "clean"}
    feats = feats0
    if fam in ("spoof_feat", "remove_feat", "shift_feat"):
        feats, led = E.attack_features(fam, feats0, 1, gt, att_pts, rng)
    elif fam == "spoof_blind":
        feats, led = attack_spoof_blind(feats0, 1, gt, att_pts, ego_pts, rng, E.MIN_ATT_PTS, contains_origin)
    elif fam == "spoof_pts":
        f2, led = E.attack_points(model, batch["ego"], gt, att_pts, 1, rng, pcr, vs)
        if f2 is not None:
            feats = f2
    return feats, led


def bnorm_extras(model, batch, rec, scen, i, feats0, att_pts, ego_pts, pcr, vs, rng_scen=None):
    """mean |feature| per agent and scale for every condition of an E4 record (clean and applied families);
    the recomputed ledger must equal the record's. Returns {cond: [n, K] array}."""
    out = {"clean": bnorm.mean_abs(feats0)}
    for fam, c in rec["conditions"].items():
        if fam == "clean" or "cands" not in c:
            continue
        f, led = attacked_feats(model, batch, fam, feats0, rec["gt"], att_pts, ego_pts,
                                E.rng_for(fam, rng_scen or scen, i, rec.get("seed", 0)), pcr, vs)
        assert same(led, c["ledger"]), f"ledger mismatch {scen} {i} {fam}"
        out[fam] = bnorm.mean_abs(f)
    return out


def yplus_rays(pp, cond, ego_pts):
    yp, _ = finalize(pp, cond["cands"][frozenset()])
    return [BL.box_rays(ego_pts, b) for b in yp]


# ------------------------------------------------------------------ condition records
def cond_record(model, pp, batch, feats, n, ego_pts, gmask, pcr, led):
    """The per-condition body of e4_stream.frame_record (no attention tiles), plus yplus_rays (float64)."""
    cands, _ = E.decode_all(model, types.SimpleNamespace(post_processor=pp), batch, feats, n)
    yp, sp = finalize(pp, cands[frozenset()])
    effs = []
    for s_idx in range(1, n):
        ym, sm = finalize(pp, cands[frozenset([s_idx])])
        for e in get_effects(yp, sp, ym, sm):
            effs.append({"sender": s_idx, "type": e["type"], "plus": e["plus"], "minus": e["minus"],
                         "score_plus": e.get("score_plus"), "score_minus": e.get("score_minus"),
                         "tile_plus": None if e["plus"] is None else tile_of(e["plus"], pcr, E.TILE_M),
                         "tile_minus": None if e["minus"] is None else tile_of(e["minus"], pcr, E.TILE_M),
                         "rays_plus": E.ray_rec(ego_pts, gmask, e["plus"]),
                         "rays_minus": E.ray_rec(ego_pts, gmask, e["minus"])})
    return {"ledger": led, "cands": cands, "effects": effs, "yplus_rays": [BL.box_rays(ego_pts, b) for b in yp]}


def cond_name(fam, r):
    return f"{fam}@r{r}"


def pgd_conditions(model, pp, batch, feats0, n, ego_pts, gmask, pcr, scen, i, levels, sigma, score_thr, tau=None):
    """levels: {family: [r, ...]}; sigma: per-scale sender std (plan); tau: B-NORM thresholds (needed by the
    D-68 stealth families). Returns {cond: record} with B-NORM magnitudes in record['mabs'].
    n = 1: no attacker -> nothing (scored as clean, as every family)."""
    out = {}
    if n < 2:
        return out
    for fam, rs in levels.items():
        for r in rs:
            eps = [r * s for s in sigma]
            if fam in PS.FAMILIES:
                f, led = PS.pgd_attack_stealth(model, feats0, PGD_ATTACKER, fam, eps, tau, PS.rng_for(fam, r, scen, i),
                                               score_thr)
            else:
                f, led = P.pgd_attack(model, feats0, PGD_ATTACKER, fam, eps, P.rng_for(fam, r, scen, i), score_thr)
            led["r"] = r
            if f is None:                               # stealth infeasible: not applied, scored as clean
                out[cond_name(fam, r)] = {"ledger": led}
                continue
            for k in range(len(f)):
                others = [j for j in range(n) if j != PGD_ATTACKER]
                assert torch.equal(f[k][others], feats0[k][others])
            c = cond_record(model, pp, batch, f, n, ego_pts, gmask, pcr, led)
            c["mabs"] = bnorm.mean_abs(f)
            out[cond_name(fam, r)] = c
    return out
