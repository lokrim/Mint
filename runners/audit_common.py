"""Audit helpers: E4-format condition records from given features, and method evaluation with both
the frozen non-global OpenCOOD AP and a global-sort AP. Read-only use of frozen modules."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import e0_analyze as A  # noqa: E402  (shims, paths)
import e0_stream as E  # noqa: E402
import e4_analyze as Z  # noqa: E402
import e5_analyze as X  # noqa: E402

import numpy as np  # noqa: E402
from mint.effects.effects import bev_iou_matrix, effects as get_effects, tile_of  # noqa: E402
from mint.fusion.compose import finalize  # noqa: E402
from mint.reliability import baselines as BL  # noqa: E402

METHODS = ("undefended", "ego_only", "B-RAY", "R1", "R1_noREMOVE")


def cond_record(model, ds, batch, feats, n, ego_pts, gmask, pcr, led):
    """Exactly the per-condition body of e4_stream.frame_record, plus yplus_rays (float64 scan)."""
    cands, _ = E.decode_all(model, ds, batch, feats, n)
    yp, sp = finalize(ds.post_processor, cands[frozenset()])
    effs = []
    for s_idx in range(1, n):
        ym, sm = finalize(ds.post_processor, cands[frozenset([s_idx])])
        for e in get_effects(yp, sp, ym, sm):
            effs.append({"sender": s_idx, "type": e["type"], "plus": e["plus"], "minus": e["minus"],
                         "score_plus": e.get("score_plus"), "score_minus": e.get("score_minus"),
                         "tile_plus": None if e["plus"] is None else tile_of(e["plus"], pcr, E.TILE_M),
                         "tile_minus": None if e["minus"] is None else tile_of(e["minus"], pcr, E.TILE_M),
                         "rays_plus": E.ray_rec(ego_pts, gmask, e["plus"]),
                         "rays_minus": E.ray_rec(ego_pts, gmask, e["minus"])})
    return {"ledger": led, "cands": cands, "effects": effs, "yplus_rays": [BL.box_rays(ego_pts, b) for b in yp]}


def ap_global(stats, iou):
    tp = np.concatenate([np.asarray(s[iou]["tp"], float) for s in stats]) if stats else np.zeros(0)
    fp = np.concatenate([np.asarray(s[iou]["fp"], float) for s in stats]) if stats else np.zeros(0)
    sc = np.concatenate([np.asarray(s[iou]["score"], float) for s in stats]) if stats else np.zeros(0)
    gt = sum(s[iou]["gt"] for s in stats)
    o = np.argsort(-sc, kind="stable")
    return Z.ap_from([(tp[o].astype(np.int64), fp[o].astype(np.int64), gt)])


def evaluate(frames, conds, realized=None):
    """frames: list of (scen, fr). Returns per (cond, method) AP@0.7/0.5 non-global and global, B-RAY box
    outcomes, and per-frame stats. realized: optional {(cond): set of frame keys} for realized-only APs."""
    pp = A.post_processor()
    stats = {(c, m): [] for c in conds for m in METHODS}
    keys = []
    bray = {c: [] for c in conds}
    for scen, fr in frames:
        n = fr["n_agents"]
        keys.append((scen, fr["frame"]))
        memo = {}
        for c in conds:
            out, side = X.frame_methods(pp, fr, c, n, memo)
            for m in METHODS:
                stats[(c, m)].append(A.frame_stat(*out[m], fr["gt"]))
            bray[c] += X.bray_box_record(side["bray_verdicts"], side["yp"], fr["gt"])
    return summarize(stats, keys, conds, realized), {c: X.bray_summary(bray[c]) for c in conds}, stats, keys


def summarize(stats, keys, conds, realized=None):
    def table(idx):
        res = {}
        for c in conds:
            row = {}
            for m in METHODS:
                S = [stats[(c, m)][j] for j in idx]
                row[m] = {"AP@0.7": Z.ap_from([X.tpfp(s, 0.7) for s in S]), "AP@0.5": Z.ap_from([X.tpfp(s, 0.5) for s in S]),
                          "AP@0.7_global": ap_global(S, 0.7)}
            res[c] = row
        out = {}
        for c in conds:
            out[c] = {}
            for m in METHODS:
                r = {k: round(v, 4) for k, v in res[c][m].items()}
                if m != "undefended":
                    for k in ("AP@0.7", "AP@0.7_global", "AP@0.5"):
                        r["d" + k] = round(res[c][m][k] - res[c]["undefended"][k], 4)
                if c != "clean" and "clean" in res:
                    loss = res["clean"]["undefended"]["AP@0.7"] - res[c]["undefended"]["AP@0.7"]
                    if m == "undefended":
                        r["attack_loss@0.7"] = round(loss, 4)
                    else:
                        r["recovery@0.7"] = None if loss < 0.005 else round(r["dAP@0.7"] / loss, 3)
                out[c][m] = r
        return out
    res = {"all_frames": table(list(range(len(keys)))), "frames": len(keys)}
    if realized:
        res["realized_only"] = {}
        for c, ks in realized.items():
            idx = [j for j, k in enumerate(keys) if k in ks]
            if idx:
                t = table(idx)
                res["realized_only"][c] = {"frames": len(idx), "clean": t["clean"], c: t[c]}
    return res


def spoof_box_outcomes(fr, c, rays_key="yplus_rays"):
    """For a realized spoof (ledger dst_center): B-RAY verdicts of attacker ADD/SHIFT boxes within 3 m."""
    led = c["ledger"]
    if not led.get("applied") or "dst_center" not in led or "cands" not in c:
        return None
    dx, dy = led["dst_center"]
    pp = A.post_processor()
    yp, _ = finalize(pp, c["cands"][frozenset()])
    out = []
    rays = c.get(rays_key) or [BL.box_rays(np.asarray(fr["ego_pts"], np.float64), b) for b in yp]
    for b, r in zip(yp, rays):
        if np.hypot(*(np.asarray(b).mean(0)[:2] - [dx, dy])) < 3.0:
            gtm = float(bev_iou_matrix(np.asarray(b)[None], fr["gt"]).max()) if len(fr["gt"]) else 0.0
            out.append({"verdict": BL.b_ray_verdict(r), "rays": r["SUP"] + r["TRAV"], "SUP": r["SUP"], "gt_iou": round(gtm, 3)})
    return out
