"""E5 analysis: the D-56 comparison set on cached frames (offline; GT used only for scoring).

  dev   E5a development check on the block-T E0 caches (404 frames; clean + 4 original families).
        Development / in-sample. B-RAY ray counts for the final Y+ boxes are computed here from the
        cached receiver scan (stored as float16); their per-frame cost is timed here.
  test  the one-time final test (runs/<date>-E5/preregistration.json) on the 15-scenario test caches
        written by runners/e5_stream.py (clean + 4 original families + spoof_blind). B-RAY ray counts
        come from the stream (float64 scan, `yplus_rays`); cost comes from the stream's timing pass.

Methods (D-56), per (frame, condition):
  undefended            Y+ = finalize(cands[{}])
  ego_only              finalize(cands[all senders excluded])
  B-RAY                 baselines.b_ray on Y+ (no counterfactual)
  R1                    MINT-v0 + R1, dense counterfactual, composed output (D-51; headline)
  R1_noREMOVE           baselines.assess_noremove, composed output
  oracle_attacker       E0 bound: gate attacker (sender 1) units with D > 0.5
  vis_oracle_attacker   E0 bound: as above, KNOWN units only
A family on a frame where the attack was not applied, or a frame with n = 1, is evaluated as clean
(as E0-E4). AP is OpenCOOD's (non-global sort), frames concatenated in (scenario, frame) order; a
bootstrap resample keeps that order (as E2/E4).

  python runners/e5_analyze.py dev  --out runs/20261024-E5/dev
  python runners/e5_analyze.py test --run_dir runs/<date>-E5
"""
import argparse
import glob
import gzip
import json
import os
import pickle
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import e0_analyze as A  # noqa: E402  (installs shims, paths)
import e4_analyze as Z  # noqa: E402

import numpy as np  # noqa: E402
from mint.effects.effects import bev_iou_matrix  # noqa: E402
from mint.fusion.compose import compose, finalize  # noqa: E402
from mint.reliability import baselines as BL  # noqa: E402
from mint.reliability import r1, v0  # noqa: E402

ORIG = ("spoof_feat", "remove_feat", "shift_feat", "spoof_pts")
METHODS = ("undefended", "ego_only", "B-RAY", "R1", "R1_noREMOVE", "oracle_attacker", "vis_oracle_attacker")
BOOT_METHODS = ("undefended", "ego_only", "B-RAY", "R1", "R1_noREMOVE")
PAIRS = (("R1", "B-RAY"), ("R1", "R1_noREMOVE"), ("R1", "ego_only"))
STRATA = (("2", lambda n: n == 2), ("3", lambda n: n == 3), ("4+", lambda n: n >= 4))
MIN_SCEN_FOR_SCEN_BOOT = 5
DEV_CACHE = os.path.join(ROOT, "runs/20261023-E0/cache")
N_BOOT = 2000
MIN_LOSS = 0.005


def tpfp(st, iou):
    s = st[iou]
    return np.asarray(s["tp"], np.int64), np.asarray(s["fp"], np.int64), int(s["gt"])


# ------------------------------------------------------------------ per frame
def bray_for(fr, c, yp, sp, timer=None):
    """B-RAY on the final Y+ of condition record c. Uses c['yplus_rays'] (stream, float64 scan) when
    present; else computes from the cached receiver scan fr['ego_pts'] (float16 -> float64)."""
    rays = c.get("yplus_rays")
    if rays is not None:
        assert len(rays) == len(yp), (len(rays), len(yp))
        return BL.b_ray(yp, sp, rays=rays)
    pts = np.asarray(fr["ego_pts"], np.float64)
    t0 = time.perf_counter()
    out = BL.b_ray(yp, sp, pts=pts)
    if timer is not None:
        timer.append((time.perf_counter() - t0, len(yp)))
    return out


def unit_records(rel, lab, scen, frame, applied):
    U = []
    for k, r in rel.items():
        ge = Z.gating_effects(r) if r.gate else []
        d = lab[k]["D"] if k in lab else 0.0
        U.append({"scen": scen, "frame": frame, "sender": k[0], "tile": k[1], "status": r.status, "gate": r.gate,
                  "D": d, "touched": bool(lab[k]["touched"]) if k in lab else False, "applied": applied,
                  "types": sorted({e["type"] for e in r.effects}), "gating_types": sorted({e["type"] for e in ge})})
    return U


def frame_methods(pp, fr, cond, n, memo):
    """{method: (boxes, scores)} and side records for one frame and condition."""
    use = cond if n >= 2 else "clean"
    pol, recs, applied, c = A.frame_policies(pp, fr, use, n)
    yp, sp = pol["undefended"]
    out = {"undefended": (yp, sp), "oracle_attacker": pol["oracle_attacker"],
           "vis_oracle_attacker": pol["vis_oracle_attacker"]}
    out["ego_only"] = finalize(pp, BL.ego_only(c["cands"], n)) if n >= 2 else (yp, sp)
    rel = r1.assess(c["effects"], v0.Params())
    ch = v0.gating_choice(rel)
    out["R1"] = finalize(pp, compose(c["cands"], ch)) if ch else (yp, sp)
    reln = BL.assess_noremove(c["effects"], v0.Params())
    chn = v0.gating_choice(reln)
    out["R1_noREMOVE"] = finalize(pp, compose(c["cands"], chn)) if chn else (yp, sp)
    key = id(c)
    if key not in memo:
        memo[key] = bray_for(fr, c, yp, sp, memo.setdefault("_timer", []) if cond == "clean" else None)
    bb, bs, verd, rays = memo[key]
    out["B-RAY"] = (bb, bs)
    lab = {(r["sender"], r["tile"]): r for r in recs}
    side = {"applied": applied, "c": c, "rel": rel, "reln": reln, "lab": lab, "bray_verdicts": verd,
            "bray_rays": rays, "yp": yp}
    return out, side


def bray_box_record(verd, yp, gt):
    """Per-box B-RAY outcome with a GT-match flag (BEV IoU >= 0.5 to any GT box)."""
    if len(yp) == 0:
        return []
    m = bev_iou_matrix(np.asarray(yp), np.asarray(gt)).max(1) if len(gt) else np.zeros(len(yp))
    return [{"verdict": v, "gt_match": bool(x >= 0.5)} for v, x in zip(verd, m)]


def bray_summary(B):
    d = {"boxes": len(B)}
    for v in ("drop", "keep", "keep_unknown", "keep_self"):
        d[v] = sum(b["verdict"] == v for b in B)
    d["frac_KNOWN"] = None if not B else round((d["drop"] + d["keep"]) / len(B), 3)
    d["dropped_gt_matched"] = sum(b["verdict"] == "drop" and b["gt_match"] for b in B)
    d["dropped_unmatched"] = d["drop"] - d["dropped_gt_matched"]
    return d


def ray_consistency(fr, c):
    """Dev only: cached effect ray counts (float64 scan, E0) vs recomputed from the float16 cache, for
    every ADD/SHIFT effect's Y+ box. Returns (n boxes, n identical counts, n same B-RAY verdict)."""
    pts = np.asarray(fr["ego_pts"], np.float64)
    n = same = same_v = 0
    for e in c["effects"]:
        if e["plus"] is None:
            continue
        a = e["rays_plus"]
        b = BL.box_rays(pts, e["plus"])
        ra = {"SUP": a["std"]["SUP"], "TRAV": a["std"]["TRAV"], "self_box": a["self_box"]}
        n += 1
        same += int(ra == b)
        same_v += int(BL.b_ray_verdict(ra) == BL.b_ray_verdict(b))
    return n, same, same_v


def evaluate(frame_iter, conds, dev=False):
    pp = A.post_processor()
    F7 = {(c, m): [] for c in conds for m in METHODS}
    F5 = {(c, m): [] for c in conds for m in METHODS}
    stats7 = {}
    keys, nag = [], []
    units = {(c, m): [] for c in conds for m in ("R1", "R1_noREMOVE")}
    bray = {c: [] for c in conds}
    real = {c: [] for c in conds}
    bray_t, cons = [], [0, 0, 0]
    for scen, fr in frame_iter:
        n = fr["n_agents"]
        keys.append((scen, fr["frame"]))
        nag.append(n)
        memo = {}
        for cond in conds:
            out, side = frame_methods(pp, fr, cond, n, memo)
            for m in METHODS:
                st = A.frame_stat(*out[m], fr["gt"])
                F7[(cond, m)].append(tpfp(st, 0.7))
                F5[(cond, m)].append(tpfp(st, 0.5))
                stats7.setdefault((cond, m), []).append(st)
            units[(cond, "R1")] += unit_records(side["rel"], side["lab"], scen, fr["frame"], side["applied"])
            units[(cond, "R1_noREMOVE")] += unit_records(side["reln"], side["lab"], scen, fr["frame"], side["applied"])
            bray[cond] += bray_box_record(side["bray_verdicts"], side["yp"], fr["gt"])
            if cond == "clean" and dev:
                k = ray_consistency(fr, side["c"])
                cons = [a + b for a, b in zip(cons, k)]
            if cond != "clean" and n >= 2:
                c = side["c"]
                fam_r = "spoof_feat" if cond == "spoof_blind" else cond
                rz = A.realization(pp, fr, fam_r, c, side["applied"])
                rz["ledger"] = fr["conditions"].get(cond, {}).get("ledger", {})
                real[cond].append(rz)
        if memo.get("_timer"):
            dt, nb = memo["_timer"][0]
            bray_t.append({"scen": scen, "frame": fr["frame"], "n_agents": n, "boxes": nb, "bray_s": dt})
    return pp, F7, F5, stats7, keys, nag, units, bray, real, bray_t, cons


# ------------------------------------------------------------------ metrics and bootstrap
def metrics(F, idx, conds):
    ap = {k: Z.ap_from([F[k][j] for j in idx]) for k in F if k[1] in BOOT_METHODS}
    cl = ap[("clean", "undefended")]
    fam = [f for f in ORIG if f in conds]
    out = {}
    for m in BOOT_METHODS[1:]:
        out[f"rel_loss|{m}"] = 1 - ap[("clean", m)] / cl
        for c in conds:
            out[f"delta|{m}|{c}"] = ap[(c, m)] - ap[(c, "undefended")]
        out[f"mean_delta_orig|{m}"] = float(np.mean([out[f"delta|{m}|{f}"] for f in fam]))
    for a, b in PAIRS:
        for c in conds:
            out[f"paired|{a}-{b}|{c}"] = ap[(c, a)] - ap[(c, b)]
        out[f"paired_mean_orig|{a}-{b}"] = float(np.mean([out[f"paired|{a}-{b}|{f}"] for f in fam]))
    for m in ("R1", "B-RAY"):
        rec = []
        for c in conds:
            if c == "clean":
                continue
            loss = cl - ap[(c, "undefended")]
            r = None if loss < MIN_LOSS else (ap[(c, m)] - ap[(c, "undefended")]) / loss
            out[f"recovery|{m}|{c}"] = r
            if c in fam:
                rec.append(r)
        out[f"mean_recovery_orig|{m}"] = None if any(r is None for r in rec) else float(np.mean(rec))
    return out


def bootstrap(F, keys, conds, kind, subset=None, seed=0, n_boot=N_BOOT):
    """kind 'scenario': whole scenarios resampled with replacement (one stratum); 'block10': contiguous
    10-frame blocks within each scenario, resampled within scenario. subset: frame indices to use."""
    use = list(range(len(keys))) if subset is None else list(subset)
    scen = list(dict.fromkeys(keys[j][0] for j in use))
    pos = {s: [j for j in use if keys[j][0] == s] for s in scen}
    units, strata = [], []
    if kind == "scenario":
        units = [pos[s] for s in scen]
        strata = [list(range(len(units)))]
    else:
        for s in scen:
            p = pos[s]
            first = len(units)
            units += [p[k:k + Z.BLOCK] for k in range(0, len(p), Z.BLOCK)]
            strata.append(list(range(first, len(units))))
    rng = np.random.default_rng(seed)
    vals = {}
    for _ in range(n_boot):
        pick = []
        for st in strata:
            pick += list(rng.choice(st, len(st)))
        idx = sorted(j for u in pick for j in units[u])
        for k, v in metrics(F, idx, conds).items():
            vals.setdefault(k, []).append(v)
    out = {}
    for k, v in vals.items():
        ok = [x for x in v if x is not None]
        out[k] = {"ci95": None if not ok else [round(float(np.percentile(ok, 2.5)), 4),
                                               round(float(np.percentile(ok, 97.5)), 4)],
                  "dropped": len(v) - len(ok)}
    out["_blocks"] = len(units)
    out["_scenarios"] = len(scen)
    return out


def ap_table(F7, F5, conds, idx):
    ap7 = {k: Z.ap_from([F7[k][j] for j in idx]) for k in F7}
    ap5 = {k: Z.ap_from([F5[k][j] for j in idx]) for k in F5}
    tab = {}
    for c in conds:
        row = {}
        for m in METHODS:
            r = {"AP@0.7": round(ap7[(c, m)], 4), "AP@0.5": round(ap5[(c, m)], 4)}
            if m != "undefended":
                r["dAP@0.7"] = round(ap7[(c, m)] - ap7[(c, "undefended")], 4)
                r["dAP@0.5"] = round(ap5[(c, m)] - ap5[(c, "undefended")], 4)
            if c == "clean" and m != "undefended":
                r["rel_loss@0.7"] = round(1 - ap7[(c, m)] / ap7[("clean", "undefended")], 4)
            if c != "clean":
                loss = ap7[("clean", "undefended")] - ap7[(c, "undefended")]
                if m == "undefended":
                    r["attack_loss@0.7"] = round(loss, 4)
                else:
                    r["recovery@0.7"] = None if loss < MIN_LOSS else round((ap7[(c, m)] - ap7[(c, "undefended")]) / loss, 3)
            row[m] = r
        tab[c] = row
    return tab, ap7


def pq(x):
    return None if not len(x) else {"p50": round(float(np.median(x)), 4), "p95": round(float(np.percentile(x, 95)), 4),
                                    "n": len(x)}


def stratum_of(n):
    for name, f in STRATA:
        if f(n):
            return name
    return str(n)


def overhead_by_stratum(timing):
    """Test mode: stream timing records (e5_stream.time_frame_e5) grouped by 2 / 3 / 4+ (and n = 1)."""
    iso = float(np.median([t["encode_isolated_s"] for t in timing]))
    by = {}
    for t in timing:
        by.setdefault(stratum_of(t["n_agents"]), []).append(t)
    out = {"encode_isolated_p50_s": round(iso, 4), "frames": len(timing), "by_stratum": {}}
    for s, T in sorted(by.items()):
        d = {"frames": len(T)}
        for m in ("dense", "trigger_0.05", "B-RAY"):
            R = [t[m] for t in T if m in t]
            if not R:
                continue
            d[m] = {"overhead": pq([r["overhead"] for r in R]),
                    "overhead_isolated_encode": pq([r["mint_extra_s"] / (iso + r["plain_baseline_s"]) for r in R]),
                    "extra_s": pq([r["mint_extra_s"] for r in R]), "baseline_s": pq([r["baseline_s"] for r in R])}
        out["by_stratum"][s] = d
    return out


# ------------------------------------------------------------------ driver
def frames_from(files, meta, timing):
    for p in files:
        R = pickle.load(gzip.open(p))
        meta.append({"scenario": R["scenario"], "frames": len(R["frames"]),
                     "compose_checks": len(R.get("compose_checks", [])),
                     "compose_all_identical": all(c["same_candidates"] and c["same_final"]
                                                  for c in R.get("compose_checks", []))})
        for t in R.get("timing", []):
            timing.append(dict(t, scen=R["scenario"]))
        for fr in R["frames"]:
            yield R["scenario"], fr
        print("loaded", R["scenario"], flush=True)


def analyze(files, conds, dev, n_boot=N_BOOT):
    meta, timing = [], []
    pp, F7, F5, stats7, keys, nag, units, bray, real, bray_t, cons = evaluate(frames_from(files, meta, timing), conds, dev)
    idx = list(range(len(keys)))
    tab, ap7 = ap_table(F7, F5, conds, idx)
    ref = {k: A.ap(A.merge(v))[0.7] for k, v in stats7.items()}
    out = {"files": [os.path.relpath(f, ROOT) for f in files], "scenarios": meta, "frames": len(keys),
           "n_agents_hist": {str(k): nag.count(k) for k in sorted(set(nag))},
           "numpy_ap_vs_opencood_max_abs_diff": max(abs(ap7[k] - ref[k]) for k in ref),
           "AP": tab, "point": {k: None if v is None else round(v, 5) for k, v in metrics(F7, idx, conds).items()}}
    out["bootstrap_scenario"] = bootstrap(F7, keys, conds, "scenario", n_boot=n_boot)
    out["bootstrap_block10"] = bootstrap(F7, keys, conds, "block10", n_boot=n_boot)
    strata = {}
    for name, f in STRATA:
        sub = [j for j in idx if f(nag[j])]
        if not sub:
            continue
        d = {"frames": len(sub), "scenarios": len({keys[j][0] for j in sub}),
             "point": {k: None if v is None else round(v, 5) for k, v in metrics(F7, sub, conds).items()}}
        sel = lambda k: k.startswith(("mean_delta_orig|", "rel_loss|", "paired_mean_orig|", "delta|R1|"))
        b10 = bootstrap(F7, keys, conds, "block10", subset=sub, n_boot=n_boot)
        d["bootstrap_block10"] = {k: v for k, v in b10.items() if k.startswith("_") or sel(k)}
        if d["scenarios"] >= MIN_SCEN_FOR_SCEN_BOOT:
            bs = bootstrap(F7, keys, conds, "scenario", subset=sub, n_boot=n_boot)
            d["bootstrap_scenario"] = {k: v for k, v in bs.items() if k.startswith("_") or sel(k)}
        strata[name] = d
    out["by_agents"] = strata
    out["n1_frames"] = sum(n == 1 for n in nag)
    out["units"] = {f"{m}|{c}": Z.unit_breakdown(units[(c, m)]) for c in conds for m in ("R1", "R1_noREMOVE")}
    out["B-RAY_boxes"] = {c: bray_summary(bray[c]) for c in conds}
    out["realization"] = {c: Z.realization_summary(real[c]) for c in conds if c != "clean"}
    if bray_t:
        out["B-RAY_cost_dev"] = {"note": "seconds to count receiver rays for every final Y+ box and filter, clean "
                                         "condition, one run per frame, from the float16 cached scan (Apple M1 CPU, "
                                         "single process); no baseline timing exists in the block-T caches",
                                 "all": pq([t["bray_s"] for t in bray_t]),
                                 "boxes_per_frame": pq([t["boxes"] for t in bray_t]),
                                 "by_stratum": {s: pq([t["bray_s"] for t in bray_t if stratum_of(t["n_agents"]) == s])
                                                for s in ("2", "3", "4+")}}
    if dev:
        out["ray_count_check_dev"] = {"what": "ADD/SHIFT Y+ boxes (clean): cached E0 effect counts (float64 scan) vs "
                                              "recomputed from the float16 cache", "boxes": cons[0],
                                      "identical_counts": cons[1], "same_B-RAY_verdict": cons[2]}
    if timing:
        out["overhead"] = overhead_by_stratum(timing)
    return out


def criteria(out):
    """Pre-registered final-test criteria (runs/<date>-E5/preregistration.json)."""
    p, bs, b10 = out["point"], out["bootstrap_scenario"], out["bootstrap_block10"]
    md, rl = "mean_delta_orig|R1", "rel_loss|R1"
    c = {"primary_mean_dAP0.7_R1_orig": {"point": p[md], "ci95_scenario": bs[md]["ci95"], "ci95_block10": b10[md]["ci95"],
                                         "pass": bs[md]["ci95"][0] > 0},
         "clean_rel_loss_R1": {"point": p[rl], "ci95_scenario": bs[rl]["ci95"], "ci95_block10": b10[rl]["ci95"],
                               "pass": bs[rl]["ci95"][1] <= 0.01}}
    c["success"] = bool(c["primary_mean_dAP0.7_R1_orig"]["pass"] and c["clean_rel_loss_R1"]["pass"])
    k = "paired_mean_orig|R1-B-RAY"
    ci = bs[k]["ci95"]
    c["key_secondary_R1_minus_BRAY"] = {"point": p[k], "ci95_scenario": ci, "ci95_block10": b10[k]["ci95"],
                                        "ci_includes_0": bool(ci[0] <= 0 <= ci[1]),
                                        "required_statement": ("the counterfactual's benefit over a box-level filter is "
                                                               "not established") if ci[0] <= 0 <= ci[1] else None}
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("dev", "test"))
    ap.add_argument("--out", default="runs/20261024-E5/dev")
    ap.add_argument("--run_dir", default=None)
    ap.add_argument("--n_boot", type=int, default=N_BOOT)
    a = ap.parse_args()
    if a.mode == "dev":
        files = sorted(glob.glob(os.path.join(DEV_CACHE, "20*_[0-9][0-9].pkl.gz")))
        conds = ("clean",) + ORIG
        out_dir = os.path.join(ROOT, a.out)
        out_p = os.path.join(out_dir, "e5a_dev.json")
    else:
        run_dir = os.path.join(ROOT, a.run_dir)
        files = sorted(glob.glob(os.path.join(run_dir, "cache", "20*_[0-9][0-9].pkl.gz")))
        conds = ("clean",) + ORIG + ("spoof_blind",)
        out_dir = run_dir
        out_p = os.path.join(run_dir, "e5_test.json")
    os.makedirs(out_dir, exist_ok=True)
    out = {"mode": a.mode, "label": "DEVELOPMENT, block T, in-sample" if a.mode == "dev" else "FINAL TEST (one-time)"}
    out.update(analyze(files, conds, a.mode == "dev", a.n_boot))
    if a.mode == "test":
        out["criteria"] = criteria(out)
    json.dump(out, open(out_p, "w"), indent=1, default=str)
    show = {k: v for k, v in out.items() if not k.startswith("bootstrap") and k not in ("by_agents", "units")}
    print(json.dumps(show, indent=1, default=str))


if __name__ == "__main__":
    main()
