"""E3 steps 1 and 4: tile exactness and overhead of the candidate-tile counterfactual (development block T).

Frames: the 24-frame dev slice of 2021_08_22_13_37_16 (2 real agents). Rule: frozen R1.
Pre-registration: runs/20261023-E3/preregistration.json.

  exact     trigger-mode head outputs on T(0.05), T(0.10) and all tiles vs the dense counterfactual
            (max abs diff <= 1e-5 on 24/24 frames); candidates vs dense restricted to T(f)
  diag      after a step-1 failure: fusion vs decode share of the deviation, worst element in ULPs
  overhead  D-42 overhead at n = 2 for dense sequential (reference) and trigger f = 0.05 / 0.10,
            isolated-encode sensitivity, tile fractions, per-tile cost; baseline-only at n = 3..5
            (replicated sender features, timing only) for the projection

  python runners/e3_cost.py exact|overhead
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import e2_cost as C  # noqa: E402  (shims, paths, setup, frame_inputs, recv_encode, plain_only, pq)

import numpy as np  # noqa: E402
import torch  # noqa: E402

from mint.fusion.compose import TILE_PX  # noqa: E402
from mint.reliability import r1, v0  # noqa: E402
from mint.reliability import pipeline as PL  # noqa: E402

OUT = os.path.join(ROOT, "runs/20261023-E3")
FS = (0.05, 0.10)
N_TILES = 572
TOL = 1e-5


def restrict(c, mask):
    """Dense Candidates restricted to anchors whose tile is in mask (bool [R, C])."""
    r, k = c.tiles()
    return c.take(mask.numpy()[r, k])


@torch.no_grad()
def tile_diff(dense, tiles_out, sel, h):
    """max abs diff between tile outputs [T, C, 8, 8] and dense [1, C, H, W] at the same cells (< h rows)."""
    d = PL._to_tiles(dense[0], TILE_PX)[sel[:, 0], sel[:, 1]]                     # T, C, 8, 8
    rows = sel[:, 0, None] * TILE_PX + torch.arange(TILE_PX)                       # T, 8
    valid = (rows < h)[:, None, :, None].expand_as(d)
    return float((d - tiles_out).abs()[valid].max()) if len(sel) else 0.0


@torch.no_grad()
def part_exact(model, ds, pp, pcr, args):
    res = []
    for fi in range(min(args.frames, len(ds))):
        b, pts, feats = C.frame_inputs(model, ds, fi)
        ego, n = b["ego"], 2
        base = PL._heads(model, feats, n)
        dense = PL._heads(model, feats, n, PL._exclude_masks(feats, n, [1]))
        dc = PL._cands(pp, ego, *dense)
        h = base[0].shape[2]
        row = {"frame": fi}
        masks = {f"T({f})": PL.trigger_mask(base[0], f) for f in FS}
        masks["all"] = torch.ones_like(masks["T(0.05)"])
        for name, m in masks.items():
            sel = torch.nonzero(m)
            th = PL.trigger_heads(model, feats, n, [1], sel)[1]
            tc = PL._tile_cands(pp, ego, th, sel, base)
            rc = restrict(dc, m)
            same_idx = bool(np.array_equal(tc.idx, rc.idx))
            row[name] = {"tiles": int(len(sel)), "psm_maxabs": tile_diff(dense[0], th[0], sel, h),
                         "rm_maxabs": tile_diff(dense[1], th[1], sel, h), "cand_idx_equal": same_idx,
                         "n_cands": int(len(tc.idx)),
                         "cand_score_maxabs": float(np.abs(tc.scores - rc.scores).max()) if same_idx and len(tc.idx) else 0.0,
                         "cand_corner_maxabs": float(np.abs(tc.corners - rc.corners).max()) if same_idx and len(tc.idx) else 0.0,
                         "cand_bitwise": bool(same_idx and np.array_equal(tc.scores, rc.scores) and np.array_equal(tc.corners, rc.corners))}
        res.append(row)
        print(fi, {k: (v["tiles"], f"{max(v['psm_maxabs'], v['rm_maxabs']):.1e}", v["cand_idx_equal"])
                   for k, v in row.items() if k != "frame"}, flush=True)
    summ = {}
    for name in ("T(0.05)", "T(0.1)", "all"):
        mx = [max(r[name]["psm_maxabs"], r[name]["rm_maxabs"]) for r in res]
        summ[name] = {"frames_within_1e-5": f"{sum(x <= TOL for x in mx)}/{len(res)}", "max_abs_diff": max(mx),
                      "cand_idx_equal": f"{sum(r[name]['cand_idx_equal'] for r in res)}/{len(res)}",
                      "cand_bitwise": f"{sum(r[name]['cand_bitwise'] for r in res)}/{len(res)}",
                      "max_cand_score_diff": max(r[name]["cand_score_maxabs"] for r in res),
                      "max_cand_corner_diff": max(r[name]["cand_corner_maxabs"] for r in res),
                      "tile_fraction_mean": float(np.mean([r[name]["tiles"] for r in res])) / N_TILES}
    ok = all(max(r[k]["psm_maxabs"], r[k]["rm_maxabs"]) <= TOL for r in res for k in ("T(0.05)", "T(0.1)"))
    return {"note": "E3 step 1, development block T, 24-frame dev slice (n = 2): trigger-mode tile decode (gather -> "
                    "fuse_scale with sender 1 excluded -> decode_batch) vs dense counterfactual decode, head outputs at "
                    "the same cells (padded cells excluded); in-sample",
            "threads": torch.get_num_threads(), "tolerance": TOL, "criterion_24of24": bool(ok and len(res) == 24),
            "summary": summ, "raw": res}


@torch.no_grad()
def part_diag(model, ds, pp, pcr, args):
    """Why step 1 is not within 1e-5 (diagnostic, after the criterion failed): split the deviation into
    the fusion stage and the decode stage and express the max deviation in float32 ULPs of the value."""
    res = []
    for fi in range(min(args.frames, len(ds))):
        b, pts, feats = C.frame_inputs(model, ds, fi)
        n = 2
        base = PL._heads(model, feats, n)
        dmask = PL._exclude_masks(feats, n, [1])
        fused = [PL.fuse_scale(f[:n], dmask[k])[0] for k, f in enumerate(feats)]
        dense = PL.decode(model, fused)
        h, w_head = base[0].shape[2], feats[0].shape[3]
        row = {"frame": fi}
        for f in FS:
            sel = torch.nonzero(PL.trigger_mask(base[0], f))
            th = PL.trigger_heads(model, feats, n, [1], sel)[1]
            # (a) tile fusion vs dense fusion, per scale
            g = PL.gather_tiles(feats, n, sel)
            fus = []
            for k, x in enumerate(g):
                m = torch.ones((n, x.shape[2], x.shape[3]), dtype=torch.bool)
                m[1] = False
                y = PL.fuse_scale(x, m)[0]
                px = x.shape[3]
                yt = y.reshape(y.shape[0], len(sel), px, px).permute(1, 0, 2, 3)
                dt = PL._to_tiles(fused[k], px)[sel[:, 0], sel[:, 1]]
                fus.append(float((yt - dt).abs().max()))
            # (b) decode_batch on the dense-fused tiles (fusion identical) vs dense decode
            parts = [PL._to_tiles(fused[k], TILE_PX * fused[k].shape[2] // w_head)[sel[:, 0], sel[:, 1]]
                     for k in range(len(fused))]
            dpsm, drm = PL.decode_batch(model, parts)
            dec = max(tile_diff(dense[0], dpsm, sel, h), tile_diff(dense[1], drm, sel, h))
            # ULPs at the worst element of the full trigger path
            worst = None
            for name, dn, tt in (("psm", dense[0], th[0]), ("rm", dense[1], th[1])):
                d = PL._to_tiles(dn[0], TILE_PX)[sel[:, 0], sel[:, 1]]
                rows = sel[:, 0, None] * TILE_PX + torch.arange(TILE_PX)
                valid = (rows < h)[:, None, :, None].expand_as(d)
                diff = torch.where(valid, (d - tt).abs(), torch.zeros_like(d))
                j = int(diff.argmax())
                v = float(d.reshape(-1)[j])
                ulp = float(np.spacing(np.float32(abs(v))))
                cand = {"head": name, "abs_diff": float(diff.reshape(-1)[j]), "value": v, "ulp": ulp,
                        "ulps": round(float(diff.reshape(-1)[j]) / ulp, 2),
                        "rel_diff": float(diff.reshape(-1)[j]) / max(abs(v), 1e-30)}
                if worst is None or cand["abs_diff"] > worst["abs_diff"]:
                    worst = cand
            row[f"T({f})"] = {"fusion_maxabs_per_scale": fus, "decode_only_maxabs": dec, "worst": worst,
                              "rm_absmax_on_T": float(PL._to_tiles(dense[1][0], TILE_PX)[sel[:, 0], sel[:, 1]].abs().max())}
        res.append(row)
        print(fi, {k: (v["fusion_maxabs_per_scale"], v["decode_only_maxabs"], v["worst"]["ulps"], v["worst"]["value"])
                   for k, v in row.items() if k != "frame"}, flush=True)
    summ = {}
    for f in FS:
        k = f"T({f})"
        summ[k] = {"max_fusion_diff_per_scale": [max(r[k]["fusion_maxabs_per_scale"][s] for r in res) for s in range(3)],
                   "max_decode_only_diff": max(r[k]["decode_only_maxabs"] for r in res),
                   "max_ulps_at_worst_element": max(r[k]["worst"]["ulps"] for r in res),
                   "max_rel_diff_at_worst_element": max(r[k]["worst"]["rel_diff"] for r in res),
                   "frames_over_1e-5": [{"frame": r["frame"], **r[k]["worst"]} for r in res if r[k]["worst"]["abs_diff"] > TOL]}
    return {"note": "E3 step 1 diagnostic (run after the pre-registered criterion failed; does not change the outcome): "
                    "(a) tile fusion vs dense fusion per scale; (b) decode_batch of the dense-fused tiles vs the dense "
                    "decode (isolates the conv/BN/head path); worst element of the full trigger path in float32 ULPs",
            "threads": torch.get_num_threads(), "summary": summ, "raw": res}


ULP_MAX = 32
SCORE_TOL, CORNER_TOL = 1e-5, 1e-4


@torch.no_grad()
def tile_ulps(dense, tiles_out, sel, h):
    """Per-element |tile - dense| in float32 ULPs of the dense value (non-padded cells only)."""
    d = PL._to_tiles(dense[0], TILE_PX)[sel[:, 0], sel[:, 1]]
    rows = sel[:, 0, None] * TILE_PX + torch.arange(TILE_PX)
    valid = (rows < h)[:, None, :, None].expand_as(d)
    dv = d[valid].numpy().astype(np.float32)
    tv = tiles_out[valid].numpy().astype(np.float32)
    diff = np.abs(dv.astype(np.float64) - tv.astype(np.float64))
    ulp = np.spacing(np.abs(dv)).astype(np.float64)
    u = diff / ulp
    j = int(u.argmax()) if u.size else 0
    return {"max_ulps": float(u.max()) if u.size else 0.0, "n_over": int((u > ULP_MAX).sum()), "n": int(u.size),
            "worst": {"value": float(dv[j]), "abs_diff": float(diff[j]), "ulps": float(u[j])} if u.size else None,
            "over_examples": [{"value": float(dv[k]), "abs_diff": float(diff[k]), "ulps": float(u[k])}
                              for k in np.argsort(-u)[:5] if u[k] > ULP_MAX]}


@torch.no_grad()
def part_exact_ulp(model, ds, pp, pcr, args):
    """Step 1 re-run under the corrected criterion (prereg correction_2026-10-23, D-46)."""
    res = []
    for fi in range(min(args.frames, len(ds))):
        b, pts, feats = C.frame_inputs(model, ds, fi)
        ego, n = b["ego"], 2
        base = PL._heads(model, feats, n)
        dense = PL._heads(model, feats, n, PL._exclude_masks(feats, n, [1]))
        dc = PL._cands(pp, ego, *dense)
        h = base[0].shape[2]
        row = {"frame": fi}
        masks = {f"T({f})": PL.trigger_mask(base[0], f) for f in FS}
        masks["all"] = torch.ones_like(masks["T(0.05)"])
        for name, m in masks.items():
            sel = torch.nonzero(m)
            th = PL.trigger_heads(model, feats, n, [1], sel)[1]
            tc = PL._tile_cands(pp, ego, th, sel, base)
            rc = restrict(dc, m)
            same = bool(np.array_equal(tc.idx, rc.idx))
            sd = float(np.abs(tc.scores - rc.scores).max()) if same and len(tc.idx) else (0.0 if same else None)
            cd = float(np.abs(tc.corners - rc.corners).max()) if same and len(tc.idx) else (0.0 if same else None)
            up, ur = tile_ulps(dense[0], th[0], sel, h), tile_ulps(dense[1], th[1], sel, h)
            row[name] = {"tiles": int(len(sel)), "n_cands": int(len(tc.idx)), "a_cand_idx_equal": same,
                         "b_score_maxabs": sd, "b_corner_maxabs": cd,
                         "b_ok": bool(same and sd <= SCORE_TOL and cd <= CORNER_TOL),
                         "c_psm": up, "c_rm": ur, "c_max_ulps": max(up["max_ulps"], ur["max_ulps"]),
                         "c_ok": bool(up["n_over"] == 0 and ur["n_over"] == 0)}
            row[name]["ok"] = bool(same and row[name]["b_ok"] and row[name]["c_ok"])
        res.append(row)
        print(fi, {k: (v["tiles"], v["a_cand_idx_equal"], v["b_ok"], round(v["c_max_ulps"], 1),
                       v["c_psm"]["n_over"] + v["c_rm"]["n_over"]) for k, v in row.items() if k != "frame"}, flush=True)
    summ = {}
    for name in ("T(0.05)", "T(0.1)", "all"):
        R = [r[name] for r in res]
        summ[name] = {"a_frames": f"{sum(x['a_cand_idx_equal'] for x in R)}/{len(R)}",
                      "b_frames": f"{sum(x['b_ok'] for x in R)}/{len(R)}",
                      "c_frames": f"{sum(x['c_ok'] for x in R)}/{len(R)}",
                      "all_frames": f"{sum(x['ok'] for x in R)}/{len(R)}",
                      "max_score_diff": max((x["b_score_maxabs"] or 0.0) for x in R),
                      "max_corner_diff": max((x["b_corner_maxabs"] or 0.0) for x in R),
                      "max_ulps_psm": max(x["c_psm"]["max_ulps"] for x in R),
                      "max_ulps_rm": max(x["c_rm"]["max_ulps"] for x in R),
                      "elements_over_32ulp": sum(x["c_psm"]["n_over"] + x["c_rm"]["n_over"] for x in R),
                      "elements_checked": sum(x["c_psm"]["n"] + x["c_rm"]["n"] for x in R)}
    ok = all(r[k]["ok"] for r in res for k in ("T(0.05)", "T(0.1)")) and len(res) == 24
    return {"note": "E3 step 1 re-run under the corrected criterion (preregistration correction_2026-10-23, D-46): "
                    "(a) candidate anchor indices identical to dense restricted to T(f); (b) candidate score diff <= 1e-5 "
                    "and corner diff <= 1e-4 m; (c) every non-padded psm/rm element within 32 float32 ULP of the dense "
                    "value (ULP = numpy.spacing(|dense|)). 24-frame dev slice, n = 2; 'all' = all 572 tiles, reference "
                    "only; development / in-sample",
            "threads": torch.get_num_threads(), "ulp_max": ULP_MAX, "score_tol": SCORE_TOL, "corner_tol": CORNER_TOL,
            "criterion_24of24": bool(ok), "summary": summ, "raw": res}


def run(model, pp, b, pts, pcr, feats, mode, prof=PL.NOPROF, f=None):
    return PL.mint_frame(model, pp, b, pts, pcr, v0.Params(), feats=feats, rule=r1, cf_mode=mode, prof=prof, trigger_f=f)


TRIG_FWD = ("counterfactual.gather", "counterfactual.fusion", "counterfactual.deblocks_heads")
TRIG_SENDER = ("counterfactual.candidates", "counterfactual.finalize", "counterfactual.effects")


def part_overhead(model, ds, pp, pcr, args):
    modes = [("dense_sequential", "sequential", None)] + [(f"trigger_{f}", "trigger", f) for f in FS]
    rec = {m[0]: [] for m in modes}
    iso, base_n = [], {n: [] for n in (3, 4, 5)}
    for fi in range(min(args.frames, len(ds))):
        b, pts, feats = C.frame_inputs(model, ds, fi)
        if fi == 0:
            C.recv_encode(model, b)
            C.plain_only(model, pp, b, feats, PL.OpenCOODPost)
            for name, mode, f in modes:
                run(model, pp, b, pts, pcr, feats, mode, f=f)
        iso.append(float(np.median([C.recv_encode(model, b) for _ in range(5)])))
        reps = {m[0]: [] for m in modes}
        for _ in range(args.reps):
            tr0 = C.recv_encode(model, b)
            tp0 = C.plain_only(model, pp, b, feats, PL.OpenCOODPost)
            for name, mode, f in modes:
                C.recv_encode(model, b)
                pr = PL.Prof()
                o = run(model, pp, b, pts, pcr, feats, mode, pr, f)
                t = o["timing_s"]
                ex = t["counterfactual"] + t["evidence"] + t["compose"]
                tiles = None if o["trigger"] is None else int(o["trigger"].sum())
                reps[name].append({"baseline_s": tr0 + tp0, "plain_baseline_s": tp0, "encode_baseline_s": tr0,
                                   "mint_extra_s": ex, "overhead": ex / (tr0 + tp0),
                                   "tiles": tiles, "fwd_s": sum(pr.acc.get(k, 0.0) for k in TRIG_FWD),
                                   "sender_post_s": sum(pr.acc.get(k, 0.0) for k in TRIG_SENDER),
                                   "trigger_s": pr.acc.get("counterfactual.trigger", 0.0), **t})
        for name, *_ in modes:
            rec[name].append({k: (None if reps[name][0][k] is None else float(np.median([x[k] for x in reps[name]])))
                              for k in reps[name][0]})
        for n in (3, 4, 5):                       # baseline-only with replicated senders (projection)
            fn = [torch.cat([f] + [f[1:2]] * (n - 2)) for f in feats]
            base_n[n].append(float(np.median([C.recv_encode(model, b) + C.plain_only(model, pp, b, fn, PL.OpenCOODPost)
                                              for _ in range(args.reps)])))
        print("frame", fi, {k: (round(v[-1]["overhead"], 3), v[-1]["tiles"]) for k, v in rec.items()}, flush=True)
    enc_iso = float(np.median(iso))
    out = {"note": "E3 step 4, development block T, 24-frame dev slice, n = 2, rule R1, OpenCOOD post-processing; D-42 "
                   "protocol (baseline-only run shared per repetition; isolated-encode sensitivity); per-frame median of "
                   "interleaved reps, then p50/p95 over frames; in-sample",
           "threads": torch.get_num_threads(), "interop_threads": torch.get_num_interop_threads(), "reps": args.reps,
           "encode_isolated_p50_s": enc_iso, "encode_isolated_per_frame_s": iso, "D17_budget_p95": 0.10, "modes": {}}
    for name, mode, f in modes:
        R = rec[name]
        ov = [r["overhead"] for r in R]
        ov_iso = [r["mint_extra_s"] / (enc_iso + r["plain_baseline_s"]) for r in R]
        d = {"overhead": C.pq(ov), "overhead_isolated_encode": C.pq(ov_iso),
             "baseline_s": C.pq([r["baseline_s"] for r in R]), "mint_extra_s": C.pq([r["mint_extra_s"] for r in R]),
             "counterfactual_s": C.pq([r["counterfactual"] for r in R]), "evidence_s": C.pq([r["evidence"] for r in R]),
             "compose_s": C.pq([r["compose"] for r in R])}
        if mode == "trigger":
            tf = [r["tiles"] / N_TILES for r in R]
            d.update({"tile_fraction": {"mean": round(float(np.mean(tf)), 4), **C.pq(tf)},
                      "fwd_s": C.pq([r["fwd_s"] for r in R]), "trigger_s": C.pq([r["trigger_s"] for r in R]),
                      "sender_post_s": C.pq([r["sender_post_s"] for r in R]),
                      "c_tile_s": C.pq([r["fwd_s"] / r["tiles"] for r in R if r["tiles"]]),
                      "c_fixed_s": C.pq([r["trigger_s"] + r["evidence"] + r["compose"] for r in R])})
            p95, p95i = d["overhead"]["p95"], d["overhead_isolated_encode"]["p95"]
            d["band"] = "<=10%" if p95 <= 0.10 else ("10-25%" if p95 <= 0.25 else ">25%")
            d["meets_pass_overhead"] = bool(p95 <= 0.10 and p95i <= 0.15)
        out["modes"][name] = d
    out["baseline_only_replicated_s"] = {str(n): C.pq(v) for n, v in base_n.items()}
    out["baseline_only_n2_s"] = C.pq([r["baseline_s"] for r in rec["dense_sequential"]])
    out["raw"] = rec
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("part", choices=("exact", "exact_ulp", "diag", "overhead"))
    ap.add_argument("--frames", type=int, default=24)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--threads", type=int, default=8)
    args = ap.parse_args()
    model, ds, pp, pcr = C.setup(args.threads)
    out = {"exact": part_exact, "exact_ulp": part_exact_ulp, "diag": part_diag, "overhead": part_overhead}[args.part](model, ds, pp, pcr, args)
    os.makedirs(OUT, exist_ok=True)
    name = os.path.join(OUT, {"exact": "step1_tile_exactness.json", "exact_ulp": "step1_revised.json", "diag": "step1_diagnostic.json", "overhead": "step4_overhead.json"}[args.part])
    json.dump(out, open(name, "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in out.items() if k not in ("raw", "encode_isolated_per_frame_s")}, indent=1, default=str))


if __name__ == "__main__":
    main()
