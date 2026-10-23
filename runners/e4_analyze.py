"""E4 analysis (offline, uses GT after all decisions are made).

  dev  spoof_blind development numbers on the block-T dev slice (runs/20261023-E4/dev_blind)
  H    the pre-registered held-out evaluation on block H (runs/20261023-E4/preregistration.json)

Method (frozen, D-51): MINT-v0 + R1 (src/mint/reliability/r1.py), dense counterfactual, composed
output, UNKNOWN = keep. Per (frame, condition): undefended Y+, R1 output, E0 oracle bounds
(e0_analyze.frame_policies). A family on a frame where the attack was not applied, or a frame with
n = 1, is evaluated as clean (as E0-E3). AP is OpenCOOD's (non-global sort), frames concatenated in
(scenario, frame) order; the bootstrap keeps that order (as E2).

  python runners/e4_analyze.py dev|H
"""
import argparse
import glob
import gzip
import json
import os
import pickle
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import e0_analyze as A  # noqa: E402  (installs shims, paths)

import numpy as np  # noqa: E402
from mint.fusion.compose import compose, finalize  # noqa: E402
from mint.reliability import r1, v0  # noqa: E402

RUN = os.path.join(ROOT, "runs/20261023-E4")
ORIG = ("spoof_feat", "remove_feat", "shift_feat", "spoof_pts")
TYPES = ("ADD", "REMOVE", "SHIFT")
POLS = ("undefended", "R1")
ORACLES = ("oracle_attacker", "vis_oracle_attacker", "oracle_all", "vis_oracle_all")
IOU = 0.7
BLOCK = 10
N_BOOT = 2000
MIN_LOSS = 0.005


# ------------------------------------------------------------------ AP (numpy mirror of OpenCOOD, as E2)
def tpfp(st):
    s = st[IOU]
    return np.asarray(s["tp"], np.int64), np.asarray(s["fp"], np.int64), int(s["gt"])


def ap_from(parts):
    tp = np.concatenate([p[0] for p in parts]) if parts else np.zeros(0, np.int64)
    fp = np.concatenate([p[1] for p in parts]) if parts else np.zeros(0, np.int64)
    gt = sum(p[2] for p in parts)
    ctp, cfp = np.cumsum(tp), np.cumsum(fp)
    rec = np.concatenate([[0.0], ctp / gt, [1.0]])
    with np.errstate(invalid="ignore"):
        prec = np.concatenate([[0.0], ctp / np.maximum(ctp + cfp, 1), [0.0]])
    prec = np.maximum.accumulate(prec[::-1])[::-1]
    i = np.nonzero(rec[1:] != rec[:-1])[0] + 1
    return float(np.sum((rec[i] - rec[i - 1]) * prec[i]))


def metrics(F, idx, conds, families):
    """Point metrics on frames idx: delta_<c> = AP_R1 - AP_undef (AP@0.7), clean relative loss,
    recovery per family (None if attack loss < 0.005), means over `families` present in conds."""
    ap = {k: ap_from([F[k][j] for j in idx]) for k in F}
    clean = ap[("clean", "undefended")]
    out = {"clean_rel_loss": 1 - ap[("clean", "R1")] / clean}
    for c in conds:
        out[f"delta_{c}"] = ap[(c, "R1")] - ap[(c, "undefended")]
        if c == "clean":
            continue
        loss = clean - ap[(c, "undefended")]
        out[f"attack_loss_{c}"] = loss
        out[f"recovery_{c}"] = None if loss < MIN_LOSS else (ap[(c, "R1")] - ap[(c, "undefended")]) / loss
    fam = [f for f in families if f in conds]
    if fam:
        out["mean_delta_orig"] = float(np.mean([out[f"delta_{f}"] for f in fam]))
        rec = [out[f"recovery_{f}"] for f in fam]
        out["mean_recovery_orig"] = None if any(r is None for r in rec) else float(np.mean(rec))
    return out, ap


def bootstrap(F, keys, conds, families, kind, seed=0, n_boot=N_BOOT):
    """keys: (scen, frame) in original order. kind 'block10': contiguous 10-frame blocks within each
    scenario, resampled within scenario (stratified); 'scenario': whole scenarios (coarse)."""
    scen = list(dict.fromkeys(s for s, _ in keys))
    pos = {s: [j for j, k in enumerate(keys) if k[0] == s] for s in scen}
    units, strata = [], []
    if kind == "scenario":
        units = [pos[s] for s in scen]
        strata = [list(range(len(units)))]
    else:
        for s in scen:
            p = pos[s]
            first = len(units)
            units += [p[k:k + BLOCK] for k in range(0, len(p), BLOCK)]
            strata.append(list(range(first, len(units))))
    rng = np.random.default_rng(seed)
    vals = {}
    for _ in range(n_boot):
        pick = []
        for st in strata:
            pick += list(rng.choice(st, len(st)))
        idx = sorted(j for u in pick for j in units[u])
        m, _ = metrics(F, idx, conds, families)
        for k, v in m.items():
            vals.setdefault(k, []).append(v)
    out = {}
    for k, v in vals.items():
        ok = [x for x in v if x is not None]
        lo, hi = (None, None) if not ok else (float(np.percentile(ok, 2.5)), float(np.percentile(ok, 97.5)))
        out[k] = {"ci95": None if lo is None else [round(lo, 4), round(hi, 4)], "dropped": len(v) - len(ok)}
    out["_blocks"] = len(units)
    return out


# ------------------------------------------------------------------ per-unit breakdown (as E1)
def gating_effects(rel):
    return [e for e, v in zip(rel.effects, rel.verdicts) if v == "gate"]


def load_frames(files, key_field=None):
    out = []
    for p in files:
        R = pickle.load(gzip.open(p))
        for fr in R["frames"]:
            out.append((fr.get(key_field) if key_field else R["scenario"], fr))
        yield R, out
        out = []


def evaluate(frame_iter, conds, families):
    pp = A.post_processor()
    F = {(c, p): [] for c in conds for p in POLS}
    stats = {}
    keys, units, real, nagents = [], {c: [] for c in conds}, {c: [] for c in conds}, []
    for scen, fr in frame_iter:
        n = fr["n_agents"]
        keys.append((scen, fr["frame"]))
        nagents.append(n)
        for cond in conds:
            use = cond if n >= 2 else "clean"
            pol, recs, applied, c = A.frame_policies(pp, fr, use, n)
            lab = {(r["sender"], r["tile"]): r for r in recs}
            rel = r1.assess(c["effects"], v0.Params())
            ch = v0.gating_choice(rel)
            pol["R1"] = finalize(pp, compose(c["cands"], ch)) if ch else pol["undefended"]
            for p in POLS + ORACLES:
                st = A.frame_stat(*pol[p], fr["gt"])
                stats.setdefault((cond, p), []).append(st)
                if p in POLS:
                    F[(cond, p)].append(tpfp(st))
            for k, r in rel.items():
                ge = gating_effects(r) if r.gate else []
                d = lab[k]["D"] if k in lab else 0.0
                units[cond].append({"scen": scen, "frame": fr["frame"], "sender": k[0], "tile": k[1], "status": r.status,
                                    "gate": r.gate, "D": d, "touched": bool(lab[k]["touched"]) if k in lab else False,
                                    "applied": applied, "types": sorted({e["type"] for e in r.effects}),
                                    "gating_types": sorted({e["type"] for e in ge})})
            if cond != "clean" and n >= 2:
                fam_r = "spoof_feat" if cond == "spoof_blind" else cond
                rz = A.realization(pp, fr, fam_r, c, applied)
                rz["ledger"] = fr["conditions"].get(cond, {}).get("ledger", {})
                if applied and cond in ("spoof_feat", "spoof_pts", "spoof_blind") and rz.get("realized"):
                    dx, dy = c["ledger"]["dst_center"]
                    hits = [e for e in c["effects"] if e["sender"] == 1 and e["type"] in ("ADD", "SHIFT")
                            and e["plus"] is not None and np.hypot(*(np.asarray(e["plus"]).mean(0)[:2] - [dx, dy])) < 3.0]
                    tl = tuple(hits[0]["tile_plus"])
                    rz["hit_unit_status"] = rel[(1, tl)].status if (1, tl) in rel else None
                    rz["hit_unit_gated"] = bool(rel[(1, tl)].gate) if (1, tl) in rel else False
                real[cond].append(rz)
    return pp, F, stats, keys, units, real, nagents


def unit_breakdown(U, M=A.M):
    G = [u for u in U if u["gate"]]
    H = [u for u in U if u["D"] > M]
    Us = [u for u in U if u["D"] < -M]
    FR = [u for u in Us if u["gate"]]
    st = {s: sum(u["status"] == s for u in U) for s in ("KNOWN", "UNKNOWN_NO_EVIDENCE", "NOT_APPLICABLE_SELF")}
    d = {"units": len(U), **{f"n_{k}": v for k, v in st.items()},
         "frac_KNOWN": None if not U else round(st["KNOWN"] / len(U), 3),
         "frac_UNKNOWN": None if not U else round(st["UNKNOWN_NO_EVIDENCE"] / len(U), 3),
         "gated": len(G), "gated_harmful": sum(u["D"] > M for u in G),
         "gated_neutral": sum(-M <= u["D"] <= M for u in G), "false_rejections_useful": len(FR),
         "precision": None if not G else round(sum(u["D"] > M for u in G) / len(G), 3),
         "harmful_units": len(H), "harmful_KNOWN": sum(u["status"] == "KNOWN" for u in H),
         "useful_units": len(Us)}
    for typ in TYPES:
        d[f"gated_by_{typ}"] = sum(typ in u["gating_types"] for u in G)
        d[f"gated_harmful_by_{typ}"] = sum(typ in u["gating_types"] for u in G if u["D"] > M)
        d[f"false_rej_by_{typ}"] = sum(typ in u["gating_types"] for u in FR)
    att = [u for u in U if u["sender"] == 1 and u["applied"] and u["touched"] and u["D"] > M]
    d["attacker_touched_harmful"] = len(att)
    d["attacker_touched_harmful_KNOWN"] = sum(u["status"] == "KNOWN" for u in att)
    d["attacker_touched_harmful_gated"] = sum(u["gate"] for u in att)
    return d


def realization_summary(rr):
    app = [r for r in rr if r.get("applied")]
    d = {"frames_with_sender": len(rr), "applied": len(app), "realized": sum(bool(r.get("realized")) for r in app)}
    if any("dst_receiver_rays" in r for r in app):
        rz = [r for r in app if r.get("realized")]
        rays = [r["dst_receiver_rays"] for r in rz]
        d["realized_dst_rays_lt3_or_self"] = sum(v is None or v < 3 for v in rays)
        d["realized_hit_unit_KNOWN"] = sum(r.get("hit_unit_status") == "KNOWN" for r in rz)
        d["realized_hit_unit_gated_by_R1"] = sum(bool(r.get("hit_unit_gated")) for r in rz)
        pr = [r["ledger"].get("predicted_box_rays") for r in app if "predicted_box_rays" in r["ledger"]]
        if pr:
            d["predicted_box_rays_max"] = int(max(pr))
            d["dst_tries_median"] = float(np.median([r["ledger"]["dst_tries"] for r in app]))
        nb = [r for r in rr if not r.get("applied") and "dst_tries" in r.get("ledger", {})]
        d["not_applied_no_blind_dst"] = len(nb)
    if any("target_detected_clean" in r for r in app):
        d["target_detected_clean"] = sum(bool(r.get("target_detected_clean")) for r in app)
    return d


def ap_table(stats, conds, pols):
    ap = {k: A.ap(A.merge(v)) for k, v in stats.items()}
    clean = ap[("clean", "undefended")]
    tab = {}
    for c in conds:
        row = {}
        for p in pols:
            r = ap[(c, p)]
            row[p] = {"AP@0.5": round(r[0.5], 4), "AP@0.7": round(r[0.7], 4)}
            if p != "undefended":
                row[p]["delta_AP@0.7"] = round(r[0.7] - ap[(c, "undefended")][0.7], 4)
                row[p]["delta_AP@0.5"] = round(r[0.5] - ap[(c, "undefended")][0.5], 4)
            if c != "clean":
                loss = {k: clean[k] - ap[(c, "undefended")][k] for k in (0.5, 0.7)}
                if p == "undefended":
                    row[p]["attack_loss_AP@0.7"] = round(loss[0.7], 4)
                    row[p]["attack_loss_AP@0.5"] = round(loss[0.5], 4)
                else:
                    for k in (0.5, 0.7):
                        row[p][f"recovery_AP@{k}"] = None if loss[k] < MIN_LOSS else \
                            round((r[k] - ap[(c, "undefended")][k]) / loss[k], 3)
            elif p != "undefended":
                row[p]["rel_loss_AP@0.7"] = round(1 - r[0.7] / clean[0.7], 4)
        tab[c] = row
    return tab, ap


def overhead_summary(timing):
    """D-42 overhead by n: same-repetition baseline denominator and isolated-encode denominator
    (isolated encode p50 over all timed block-H frames + plain_only of the same repetition)."""
    from collections import defaultdict
    iso = float(np.median([t["encode_isolated_s"] for t in timing]))
    out = {"encode_isolated_p50_s": round(iso, 4), "frames": len(timing), "by_n": {}}
    by = defaultdict(list)
    for t in timing:
        by[t["n_agents"]].append(t)
    pq = lambda x: {"p50": round(float(np.median(x)), 4), "p95": round(float(np.percentile(x, 95)), 4)}
    for n, T in sorted(by.items()):
        d = {"frames": len(T)}
        for m in [k for k in T[0] if k not in ("n_agents", "encode_isolated_s", "frame", "scen")]:
            R = [t[m] for t in T]
            d[m] = {"overhead": pq([r["overhead"] for r in R]),
                    "overhead_isolated_encode": pq([r["mint_extra_s"] / (iso + r["plain_baseline_s"]) for r in R]),
                    "baseline_s": pq([r["baseline_s"] for r in R]), "mint_extra_s": pq([r["mint_extra_s"] for r in R]),
                    "counterfactual_s": pq([r["counterfactual_s"] for r in R])}
            if R[0]["tiles"] is not None:
                d[m]["tile_fraction"] = {"mean": round(float(np.mean([r["tiles"] for r in R])) / 572, 4),
                                         **pq([r["tiles"] / 572 for r in R])}
        out["by_n"][str(n)] = d
    return out


def run(mode):
    if mode == "dev":
        files = [os.path.join(RUN, "dev_blind", "cache", "devslice_blind.pkl.gz")]
        conds, families, key_field = ("clean", "spoof_feat", "spoof_blind"), ("spoof_feat",), "scen_key"
        out_p = os.path.join(RUN, "dev_blind", "spoof_blind_dev.json")
    else:
        files = sorted(glob.glob(os.path.join(RUN, "cache", "20*_[0-9][0-9].pkl.gz")))
        conds, families, key_field = ("clean",) + ORIG + ("spoof_blind",), ORIG, None
        out_p = os.path.join(RUN, "e4_heldout.json")
    meta, timing = [], []

    def frames():
        for R, fl in load_frames(files, key_field):
            meta.append({"scenario": R["scenario"], "frames": len(R["frames"]),
                         "compose_checks": len(R.get("compose_checks", [])),
                         "compose_all_identical": all(c["same_candidates"] and c["same_final"] for c in R.get("compose_checks", []))})
            for t in R.get("timing", []):
                timing.append(dict(t, scen=R["scenario"]))
            yield from fl
            print("loaded", R["scenario"], flush=True)

    pp, F, stats, keys, units, real, nag = evaluate(frames(), conds, families)
    tab, apv = ap_table(stats, conds, POLS + ORACLES)
    point, ap_np = metrics(F, list(range(len(keys))), conds, families)
    out = {"mode": mode, "files": [os.path.relpath(f, ROOT) for f in files], "scenarios": meta,
           "frames": len(keys), "n_agents_hist": {str(k): nag.count(k) for k in sorted(set(nag))},
           "numpy_ap_vs_opencood_max_abs_diff": max(abs(ap_np[k] - apv[k][IOU]) for k in ap_np),
           "AP": tab, "point_AP@0.7": {k: None if v is None else round(v, 5) for k, v in point.items()}}
    out["bootstrap_block10"] = bootstrap(F, keys, conds, families, "block10")
    if len({s for s, _ in keys}) > 1:
        out["bootstrap_scenario"] = bootstrap(F, keys, conds, families, "scenario")
        out["bootstrap_scenario"]["_caveat"] = "whole-scenario blocks; few blocks, coarse"
    out["units_R1"] = {c: unit_breakdown(units[c]) for c in conds}
    out["realization"] = {c: realization_summary(real[c]) for c in conds if c != "clean"}
    if timing:
        out["overhead"] = overhead_summary(timing)
    if mode == "H":
        b = out["bootstrap_block10"]
        crit = {"i_mean_delta_orig_ci_lo_gt_0": {"point": round(point["mean_delta_orig"], 5),
                                                  "ci95": b["mean_delta_orig"]["ci95"],
                                                  "pass": b["mean_delta_orig"]["ci95"][0] > 0},
                "ii_clean_rel_loss_ci_hi_le_0.01": {"point": round(point["clean_rel_loss"], 5),
                                                    "ci95": b["clean_rel_loss"]["ci95"],
                                                    "pass": b["clean_rel_loss"]["ci95"][1] <= 0.01},
                "iii_no_orig_family_point_delta_lt_-0.002": {f: round(point[f"delta_{f}"], 5) for f in ORIG}}
        crit["iii_no_orig_family_point_delta_lt_-0.002"]["pass"] = all(point[f"delta_{f}"] >= -0.002 for f in ORIG)
        crit["success"] = bool(crit["i_mean_delta_orig_ci_lo_gt_0"]["pass"] and crit["ii_clean_rel_loss_ci_hi_le_0.01"]["pass"]
                               and crit["iii_no_orig_family_point_delta_lt_-0.002"]["pass"])
        out["criteria"] = crit
    json.dump(out, open(out_p, "w"), indent=1, default=str)
    show = {k: v for k, v in out.items() if k not in ("bootstrap_block10", "bootstrap_scenario")}
    print(json.dumps(show, indent=1, default=str))
    print("block10", json.dumps({k: v["ci95"] for k, v in out["bootstrap_block10"].items() if k != "_blocks"}))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("dev", "H"))
    run(ap.parse_args().mode)


if __name__ == "__main__":
    main()
