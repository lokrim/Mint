"""preregistration_v3 analysis (D-64 dual AP, D-65 PGD families, D-66 B-NORM). Offline; GT for scoring only.

Every method except B-NORM comes from the frozen e5_analyze.frame_methods (unchanged): no defense, ego-only,
B-RAY, R1, R1-noREMOVE. B-NORM (mint.reliability.bnorm) drops every sender whose feature-magnitude ratio
exceeds tau_k at any scale. A condition on a frame where the attack was not applied, or a frame with n = 1,
is evaluated as clean (as E0-E5).

AP definitions (D-64), both at IoU 0.7 (and 0.5 in tables):
  frame   OpenCOOD frame-order AP (global_sort_detections=False): TP/FP concatenated in (scenario, frame)
          order, as the frozen e5_analyze (a bootstrap resample keeps sorted frame order)
  global  detections of all selected frames ranked by score (stable sort), then the same AP integral
Bootstrap = e5_analyze's resampling exactly (units, strata, default_rng(seed), draw order): 'scenario'
(whole scenarios) and 'block10' (10-frame blocks within scenario). One-sided p = (k + 1) / (B + 1).

  python runners/v3_analyze.py H    --run_dir runs/20261024-PGD            (development, exposed block H)
  python runners/v3_analyze.py H_stealth --run_dir runs/20261024-PGD       (D-68 stealth families on H, post hoc)
  python runners/v3_analyze.py test --run_dir runs/<date>-E5v3             (final test; after approval only)
  python runners/v3_analyze.py dry  --run_dir <dry-run dir> --prereg <v3>  (dry run, no assertion on 15/2066)
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
import e0_analyze as A  # noqa: E402  (shims, paths)
import e4_analyze as Z  # noqa: E402
import e5_analyze as X  # noqa: E402

import numpy as np  # noqa: E402
from mint.effects.effects import bev_iou_matrix  # noqa: E402
from mint.fusion.compose import finalize  # noqa: E402
from mint.reliability import bnorm  # noqa: E402

ORIG = X.ORIG                                         # 4 original families (v2 primary statistic)
MEAN3 = ("spoof_feat", "shift_feat", "spoof_pts")     # excluding remove_feat
METHODS = ("undefended", "ego_only", "B-NORM", "B-RAY", "R1", "R1_noREMOVE")
DEFS = ("frame", "global")
IOUS = (0.7, 0.5)
N_BOOT = X.N_BOOT
MIN_LOSS = X.MIN_LOSS
ALPHA = X.ALPHA
TEST_SCEN = 15
TEST_FRAMES = 2066
PGD_LOSS_BAR = 0.02
BNORM_CATCH_STOP = 0.95


# ------------------------------------------------------------------ frame sources
def _load(p):
    with gzip.open(p, "rb") as f:
        return pickle.load(f)


def frames_H(run_dir, inject_rays=True, with_pgd=True, meta=None, pgd_subs=("pgd",), keep=None):
    """Block-H re-stream: E4-format cache + side records (float64 Y+ rays, B-NORM magnitudes) + PGD records
    from each of `pgd_subs` (keep: optional set of PGD condition names to load)."""
    for p in sorted(glob.glob(os.path.join(run_dir, "cache", "20*_[0-9][0-9].pkl.gz"))):
        scen = os.path.basename(p)[:-7]
        R = _load(p)
        Xr = _load(os.path.join(run_dir, "extra", f"{scen}.pkl.gz"))
        gfr = {}
        for sub in (pgd_subs if with_pgd else ()):
            for g in _load(os.path.join(run_dir, sub, f"{scen}.pkl.gz"))["frames"]:
                d = gfr.setdefault(g["frame"], {"conditions": {}})
                d["conditions"].update({c: r for c, r in g["conditions"].items() if keep is None or c in keep})
        if meta is not None:
            meta.append({"scenario": scen, "frames": len(R["frames"])})
        for fr, ex in zip(R["frames"], Xr["frames"]):
            assert fr["frame"] == ex["frame"]
            mabs = dict(ex["mabs"])
            for c, rays in ex["yplus_rays"].items():
                if inject_rays:
                    fr["conditions"][c]["yplus_rays"] = rays
            if with_pgd:
                g = gfr[fr["frame"]]
                for c, rec in g["conditions"].items():
                    fr["conditions"][c] = rec
                    if "mabs" in rec:
                        mabs[c] = rec["mabs"]
            yield scen, fr, mabs
        print("loaded", scen, flush=True)


def frames_test(run_dir, meta=None):
    """Final-test caches: e5 format (cache/) + v3 side records (v3extra/: B-NORM magnitudes, PGD records)."""
    for p in sorted(glob.glob(os.path.join(run_dir, "cache", "20*_[0-9][0-9].pkl.gz"))):
        scen = os.path.basename(p)[:-7]
        R = _load(p)
        V = _load(os.path.join(run_dir, "v3extra", f"{scen}.pkl.gz"))
        if meta is not None:
            meta.append({"scenario": scen, "frames": len(R["frames"]),
                         "compose_all_identical": all(c["same_candidates"] and c["same_final"]
                                                      for c in R.get("compose_checks", []))})
        assert len(V["frames"]) == len(R["frames"])
        for fr, ex in zip(R["frames"], V["frames"]):
            assert fr["frame"] == ex["frame"]
            mabs = dict(ex["mabs"])
            for c, rec in ex["pgd"].items():
                fr["conditions"][c] = rec
                if "mabs" in rec:
                    mabs[c] = rec["mabs"]
            yield scen, fr, mabs
        print("loaded", scen, flush=True)


# ------------------------------------------------------------------ per frame
def pgd_realized(fam, yc, ya):
    """pgd_remove: a clean Y+ box lost; pgd_untargeted: lost or added (BEV IoU >= 0.5)."""
    yc, ya = np.asarray(yc), np.asarray(ya)
    if len(yc) and len(ya):
        m = bev_iou_matrix(yc, ya)
        lost, added = bool((m.max(1) < 0.5).any()), bool((m.max(0) < 0.5).any())
    else:
        lost, added = len(yc) > 0, len(ya) > 0
    return lost if fam.startswith("pgd_remove") else (lost or added)


def evaluate(frame_iter, conds, tau):
    pp = A.post_processor()
    S = {(c, m, i): [] for c in conds for m in METHODS for i in IOUS}
    keys, nag = [], []
    real = {c: [] for c in conds if c != "clean"}
    realized = {c: set() for c in conds if c != "clean"}
    flags = {c: {"frames_n2": 0, "applied": 0, "sender1_flagged": 0, "any_flagged": 0} for c in conds}
    bray = {c: [] for c in conds}
    for scen, fr, mabs in frame_iter:
        n = fr["n_agents"]
        k = (scen, fr["frame"])
        keys.append(k)
        nag.append(n)
        memo = {}
        yclean = None
        for cond in conds:
            out, side = X.frame_methods(pp, fr, cond, n, memo)
            applied = bool(side["applied"]) and n >= 2
            use = cond if applied else "clean"
            if n >= 2:
                fl = bnorm.flagged(mabs[use], tau)
                out["B-NORM"] = finalize(pp, side["c"]["cands"][frozenset(fl)]) if fl else out["undefended"]
                f = flags[cond]
                f["frames_n2"] += 1
                if applied or cond == "clean":
                    f["applied"] += 1
                    f["sender1_flagged"] += int(1 in fl)
                    f["any_flagged"] += int(bool(fl))
            else:
                out["B-NORM"] = out["undefended"]
            if cond == "clean":
                yclean = out["undefended"][0]
            for m in METHODS:
                st = A.frame_stat(*out[m], fr["gt"])
                for i in IOUS:
                    s = st[i]
                    S[(cond, m, i)].append((np.asarray(s["tp"], np.int64), np.asarray(s["fp"], np.int64),
                                            np.asarray(s["score"], np.float64), int(s["gt"])))
            bray[cond] += X.bray_box_record(side["bray_verdicts"], side["yp"], fr["gt"])
            if cond == "clean" or n < 2:
                continue
            if cond.startswith("pgd_"):
                rz = {"applied": applied}
                if applied:
                    rz["realized"] = pgd_realized(cond, yclean, out["undefended"][0])
            else:
                fam_r = "spoof_feat" if cond == "spoof_blind" else cond
                rz = A.realization(pp, fr, fam_r, side["c"], side["applied"])
            rz["ledger"] = {kk: v for kk, v in fr["conditions"].get(cond, {}).get("ledger", {}).items()
                            if kk not in ("objective_hist",)}
            rz["scen"], rz["frame"] = scen, fr["frame"]
            real[cond].append(rz)
            if rz.get("realized"):
                realized[cond].add(k)
    return S, keys, nag, real, realized, flags, bray


# ------------------------------------------------------------------ AP and metrics
class Store:
    """Per (cond, method, iou): concatenated per-frame TP/FP/score with frame offsets."""

    def __init__(self, S):
        self.d = {}
        for k, parts in S.items():
            off = np.concatenate([[0], np.cumsum([len(p[0]) for p in parts])]).astype(np.int64)
            tp = np.concatenate([p[0] for p in parts]) if parts else np.zeros(0, np.int64)
            fp = np.concatenate([p[1] for p in parts]) if parts else np.zeros(0, np.int64)
            sc = np.concatenate([p[2] for p in parts]) if parts else np.zeros(0)
            gt = np.asarray([p[3] for p in parts], np.int64)
            self.d[k] = (tp, fp, sc, gt, off)

    def ap(self, key, idx, glob):
        tp, fp, sc, gt, off = self.d[key]
        sel = np.concatenate([np.arange(off[j], off[j + 1]) for j in idx]) if len(idx) else np.zeros(0, np.int64)
        t, f = tp[sel], fp[sel]
        if glob:
            o = np.argsort(-sc[sel], kind="stable")
            t, f = t[o], f[o]
        return Z.ap_from([(t, f, int(gt[list(idx)].sum()))])


def metrics(st, idx, conds, glob, iou=0.7):
    ap = {(c, m): st.ap((c, m, iou), idx, glob) for c in conds for m in METHODS}
    cl = ap[("clean", "undefended")]
    out = {}
    fam4 = [f for f in ORIG if f in conds]
    fam3 = [f for f in MEAN3 if f in conds]
    for c in conds:
        if c != "clean":
            out[f"attack_loss|{c}"] = cl - ap[(c, "undefended")]
    for m in METHODS[1:]:
        out[f"rel_loss|{m}"] = 1 - ap[("clean", m)] / cl if cl > 0 else None
        for c in conds:
            out[f"delta|{m}|{c}"] = ap[(c, m)] - ap[(c, "undefended")]
            if c != "clean":
                loss = out[f"attack_loss|{c}"]
                out[f"recovery|{m}|{c}"] = None if loss < MIN_LOSS else out[f"delta|{m}|{c}"] / loss
        if fam4:
            out[f"mean_delta_orig|{m}"] = float(np.mean([out[f"delta|{m}|{f}"] for f in fam4]))
        if fam3:
            out[f"mean_delta_3|{m}"] = float(np.mean([out[f"delta|{m}|{f}"] for f in fam3]))
    for c in conds:
        out[f"paired|R1-B-RAY|{c}"] = ap[(c, "R1")] - ap[(c, "B-RAY")]
    if fam4:
        out["paired_mean_orig|R1-B-RAY"] = float(np.mean([out[f"paired|R1-B-RAY|{f}"] for f in fam4]))
    if fam3:
        out["paired_mean_3|R1-B-RAY"] = float(np.mean([out[f"paired|R1-B-RAY|{f}"] for f in fam3]))
    out["_AP"] = {f"{c}|{m}": v for (c, m), v in ap.items()}
    return out


def units_strata(keys, kind, subset=None):
    """Exactly e5_analyze.bootstrap's units and strata."""
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
    return units, strata


def draws(st, keys, conds, glob, kind, subset=None, seed=0, n_boot=N_BOOT, want=None):
    units, strata = units_strata(keys, kind, subset)
    rng = np.random.default_rng(seed)
    vals = {}
    for _ in range(n_boot):
        pick = []
        for s in strata:
            pick += list(rng.choice(s, len(s)))
        idx = sorted(j for u in pick for j in units[u])
        m = metrics(st, idx, conds, glob)
        for k, v in m.items():
            if k.startswith("_") or (want is not None and k not in want):
                continue
            vals.setdefault(k, []).append(np.nan if v is None else v)
    return {k: np.asarray(v, float) for k, v in vals.items()}, len(units)


def ci_of(v):
    ok = v[~np.isnan(v)]
    return {"ci95": None if not len(ok) else [round(float(np.percentile(ok, 2.5)), 4), round(float(np.percentile(ok, 97.5)), 4)],
            "dropped": int(np.isnan(v).sum())}


def one_sided_p(v):
    return float((np.sum(v <= 0) + 1) / (len(v) + 1))


def rnd(d):
    return {k: (None if v is None else round(v, 5)) for k, v in d.items() if not k.startswith("_")}


# ------------------------------------------------------------------ analysis
def analyze(frame_iter, conds, tau, n_boot=N_BOOT, realized_boot=True):
    t0 = time.time()
    S, keys, nag, real, realized, flags, bray = evaluate(frame_iter, conds, tau)
    st = Store(S)
    idx = list(range(len(keys)))
    out = {"frames": len(keys), "scenarios": len({k[0] for k in keys}),
           "n_agents_hist": {str(k): nag.count(k) for k in sorted(set(nag))}, "conditions": list(conds),
           "methods": list(METHODS), "B-NORM_tau": list(tau), "eval_s": round(time.time() - t0)}
    point, boot, ap_tab = {}, {}, {}
    for d in DEFS:
        g = d == "global"
        p7 = metrics(st, idx, conds, g, 0.7)
        p5 = metrics(st, idx, conds, g, 0.5)
        point[d] = rnd(p7)
        ap_tab[d] = {c: {m: {"AP@0.7": round(p7["_AP"][f"{c}|{m}"], 4), "AP@0.5": round(p5["_AP"][f"{c}|{m}"], 4)}
                         for m in METHODS} for c in conds}
        for c in conds:
            for m in METHODS:
                r = ap_tab[d][c][m]
                if m != "undefended":
                    r["dAP@0.7"] = round(p7[f"delta|{m}|{c}"], 4)
                    r["dAP@0.5"] = round(p5[f"delta|{m}|{c}"], 4)
                    if c != "clean":
                        rec = p7[f"recovery|{m}|{c}"]
                        r["recovery@0.7"] = None if rec is None else round(rec, 3)
                elif c != "clean":
                    r["attack_loss@0.7"] = round(p7[f"attack_loss|{c}"], 4)
        boot[d] = {}
        for kind in ("scenario", "block10"):
            D, nb = draws(st, keys, conds, g, kind, n_boot=n_boot)
            boot[d][kind] = {k: ci_of(v) for k, v in D.items()}
            boot[d][kind]["_units"] = nb
            if kind == "scenario":
                boot[d]["_scenario_draws"] = D
    out["AP"] = ap_tab
    out["point"] = point
    out["bootstrap"] = {d: {k: v for k, v in boot[d].items() if not k.startswith("_s")} for d in DEFS}
    out["criteria_v3"] = criteria_v3(point, boot, conds)
    out["tables"] = tables(point, out["bootstrap"], conds)
    out["realization"] = {c: Z.realization_summary(real[c]) for c in real}
    out["realized_only"] = realized_only(st, keys, conds, realized, n_boot if realized_boot else 0)
    out["B-NORM_flags"] = {c: dict(f, catch_rate=None if not f["applied"] else round(f["sender1_flagged"] / f["applied"], 4))
                           for c, f in flags.items()}
    out["B-RAY_boxes"] = {c: X.bray_summary(bray[c]) for c in conds}
    out["pgd_by_scenario"] = pgd_by_scenario(st, keys, real, conds)
    out["analysis_s"] = round(time.time() - t0)
    return out, st, keys


def criteria_v3(point, boot, conds):
    """v2 rule per AP definition (Holm co-test of B-RAY and R1 vs no defense on the scenario bootstrap,
    B-RAY clean-loss scenario CI high <= 1%), then the D-64 combination."""
    res = {}
    for d in DEFS:
        D = boot[d]["_scenario_draws"]
        tests = {}
        for m in ("B-RAY", "R1"):
            k = f"mean_delta_orig|{m}"
            v = D[k]
            tests[m] = {"point": point[d][k], "ci95_scenario": ci_of(v)["ci95"],
                        "ci95_block10": boot[d]["block10"][k]["ci95"], "k_le_0": int(np.sum(v <= 0)), "B": int(len(v)),
                        "p_one_sided": one_sided_p(v)}
        H = X.holm({m: tests[m]["p_one_sided"] for m in tests})
        for m in tests:
            tests[m]["holm"] = H[m]
        rl = {m: {"point": point[d][f"rel_loss|{m}"], "ci95_scenario": boot[d]["scenario"][f"rel_loss|{m}"]["ci95"],
                  "ci95_block10": boot[d]["block10"][f"rel_loss|{m}"]["ci95"]} for m in ("B-RAY", "R1", "B-NORM")}
        clean_ok = rl["B-RAY"]["ci95_scenario"][1] <= 0.01
        k = "paired_mean_orig|R1-B-RAY"
        ci = boot[d]["scenario"][k]["ci95"]
        res[d] = {"co_test_vs_no_defense": tests, "clean_rel_loss": rl, "B-RAY_clean_ci_hi_le_0.01": bool(clean_ok),
                  "pass": bool(tests["B-RAY"]["holm"]["reject"] and clean_ok),
                  "R1_holm_reject": bool(tests["R1"]["holm"]["reject"]),
                  "R1_minus_BRAY": {"point": point[d][k], "ci95_scenario": ci, "ci95_block10": boot[d]["block10"][k]["ci95"],
                                    "statement": X.paired_statement(ci)}}
    res["D-64"] = d64(res["frame"]["pass"], res["global"]["pass"])
    res["D-64"]["R1_minus_BRAY_statements"] = {d: res[d]["R1_minus_BRAY"]["statement"] for d in DEFS}
    s = {d: res[d]["R1_minus_BRAY"]["statement"] for d in DEFS}
    res["D-64"]["R1_minus_BRAY_AP_definition_dependent"] = s["frame"] != s["global"]
    return res


def d64(pass_frame, pass_global):
    """D-64: a success claim needs a pass under both AP definitions; disagreement -> AP-definition-dependent."""
    a, b = bool(pass_frame), bool(pass_global)
    return {"pass_frame_order": a, "pass_global": b, "success": a and b,
            "verdict": ("success under both AP definitions" if a and b else
                        "AP-definition-dependent" if a != b else "fails under both AP definitions"),
            "headline_AP": "global"}


def tables(point, boot, conds):
    """Per-family, mean-of-4, mean-of-3 tables (dAP@0.7 with both CIs) per AP definition."""
    T = {}
    for d in DEFS:
        p, bs, b10 = point[d], boot[d]["scenario"], boot[d]["block10"]
        row = lambda k: {"point": p.get(k), "ci95_scenario": bs.get(k, {}).get("ci95"), "ci95_block10": b10.get(k, {}).get("ci95")}
        T[d] = {"per_family": {c: {"attack_loss": row(f"attack_loss|{c}") if c != "clean" else None,
                                   **{m: dict(row(f"delta|{m}|{c}"), recovery=p.get(f"recovery|{m}|{c}"))
                                      for m in METHODS[1:]}} for c in conds},
                "mean_of_4_orig": {m: row(f"mean_delta_orig|{m}") for m in METHODS[1:]},
                "mean_of_3_excl_remove": {m: row(f"mean_delta_3|{m}") for m in METHODS[1:]},
                "R1_minus_BRAY": {"mean_of_4": row("paired_mean_orig|R1-B-RAY"), "mean_of_3": row("paired_mean_3|R1-B-RAY"),
                                  "per_family": {c: row(f"paired|R1-B-RAY|{c}") for c in conds}},
                "clean_rel_loss": {m: row(f"rel_loss|{m}") for m in METHODS[1:]}}
    return T


def realized_only(st, keys, conds, realized, n_boot):
    out = {}
    pos = {k: j for j, k in enumerate(keys)}
    for c, ks in realized.items():
        sub = sorted(pos[k] for k in ks)
        if not sub:
            out[c] = {"frames": 0}
            continue
        cc = ("clean", c)
        r = {"frames": len(sub)}
        for d in DEFS:
            g = d == "global"
            p = metrics(st, sub, cc, g)
            e = {"attack_loss": round(p[f"attack_loss|{c}"], 4)}
            for m in METHODS[1:]:
                rec = p[f"recovery|{m}|{c}"]
                e[m] = {"dAP@0.7": round(p[f"delta|{m}|{c}"], 4), "recovery": None if rec is None else round(rec, 3)}
            if n_boot and len(sub) >= 2 * Z.BLOCK:
                D, nb = draws(st, keys, cc, g, "block10", subset=sub, n_boot=n_boot,
                              want={f"delta|{m}|{c}" for m in METHODS[1:]} | {f"attack_loss|{c}"})
                for m in METHODS[1:]:
                    e[m]["ci95_block10"] = ci_of(D[f"delta|{m}|{c}"])["ci95"]
                e["attack_loss_ci95_block10"] = ci_of(D[f"attack_loss|{c}"])["ci95"]
            r[d] = e
        out[c] = r
    return out


def pgd_by_scenario(st, keys, real, conds):
    """Per PGD condition and scenario (D-68 amendment 2): frames with a sender, infeasible (stealth not applied),
    applied, realized, and attack loss AP@0.7 (both AP definitions) all-frame and realized-only."""
    out = {}
    pos = {k: j for j, k in enumerate(keys)}
    for c in conds:
        if not c.startswith("pgd_"):
            continue
        rows = {}
        for s in sorted({k[0] for k in keys}):
            R = [r for r in real.get(c, []) if r["scen"] == s]
            all_idx = [j for j, k in enumerate(keys) if k[0] == s]
            rz_idx = sorted(pos[(s, r["frame"])] for r in R if r.get("realized"))
            row = {"frames": len(all_idx), "frames_with_sender": len(R),
                   "infeasible": sum(r["ledger"].get("reason") == "stealth_infeasible" for r in R),
                   "applied": sum(bool(r.get("applied")) for r in R), "realized": len(rz_idx)}
            for d in DEFS:
                g = d == "global"
                for name, idx in (("all_frame", all_idx), ("realized_only", rz_idx)):
                    if idx:
                        row[f"attack_loss_{name}|{d}"] = round(st.ap(("clean", "undefended", 0.7), idx, g)
                                                             - st.ap((c, "undefended", 0.7), idx, g), 4)
            rows[s] = row
        tot = {k: sum(r[k] for r in rows.values()) for k in ("frames", "frames_with_sender", "infeasible", "applied", "realized")}
        out[c] = {"total": tot, "by_scenario": rows}
    return out


def pgd_selection(point, levels):
    """D-65 rule (plan.json): smallest r with all-frame global-AP attack loss >= 0.02, else 'too weak', r = 1.0."""
    sel = {}
    for fam, rs in levels.items():
        losses = {r: point["global"][f"attack_loss|{fam}@r{r}"] for r in rs}
        ok = [r for r in sorted(rs) if losses[r] >= PGD_LOSS_BAR]
        sel[fam] = {"attack_loss_global_by_r": losses, "selected_r": ok[0] if ok else 1.0,
                    "status": "selected" if ok else "too weak at realistic budgets (run on test at r = 1.0)"}
    return sel


def bnorm_stop(flags, levels):
    res = {}
    for fam, rs in levels.items():
        rates = {r: flags[f"{fam}@r{r}"]["catch_rate"] for r in rs}
        res[fam] = {"catch_rate_by_r": rates, "all_r_above_0.95": all(v is not None and v > BNORM_CATCH_STOP for v in rates.values())}
    res["stop"] = any(v["all_r_above_0.95"] for v in res.values() if isinstance(v, dict))
    return res


def expected_outcomes(point, conds):
    """Descriptive check of the D-65 expectations (B-RAY recovery ~ 0; R1 recovery on pgd_remove > 0)."""
    out = {}
    for c in conds:
        if not c.startswith("pgd_"):
            continue
        out[c] = {d: {m: point[d].get(f"recovery|{m}|{c}") for m in ("B-RAY", "R1", "B-NORM", "ego_only")} for d in DEFS}
    return out


# ------------------------------------------------------------------ drivers
def run_H(run_dir, n_boot):
    rd = os.path.join(ROOT, run_dir)
    plan = json.load(open(os.path.join(rd, "plan.json")))
    tau = plan["B-NORM"]["tau_k"]
    levels = {f: plan["threat_model"]["levels_r"] for f in ("pgd_untargeted", "pgd_remove")}
    conds = ("clean",) + ORIG + ("spoof_blind",) + tuple(f"{f}@r{r}" for f in levels for r in levels[f])
    meta = []
    out, _, _ = analyze(frames_H(rd, meta=meta), conds, tau, n_boot)
    res = {"label": "DEVELOPMENT, block H (exposed, D-53); 4 scenarios, n = 2; not a test",
           "plan": os.path.relpath(os.path.join(rd, "plan.json"), ROOT), "scenario_files": meta}
    res.update(out)
    res["pgd_selection"] = pgd_selection(out["point"], levels)
    res["B-NORM_stop_check"] = bnorm_stop(out["B-NORM_flags"], levels)
    res["expected_outcomes"] = expected_outcomes(out["point"], conds)
    # code-consistency check: the frame-order path with the E4 float16 rays must equal the frozen E5a-H numbers
    res["consistency_vs_e5a_H"] = consistency_e5a(rd, n_boot)
    p = os.path.join(rd, "pgd_H_results.json")
    json.dump(res, open(p, "w"), indent=1, default=str)
    return res


def consistency_e5a(rd, n_boot):
    ref = json.load(open(os.path.join(ROOT, "runs/20261024-E5/H/e5a_H.json")))
    conds = ("clean",) + ORIG + ("spoof_blind",)
    out, _, _ = analyze(frames_H(rd, inject_rays=False, with_pgd=False), conds, [np.inf] * 3, n_boot, realized_boot=False)
    chk = {}
    for m in ("B-RAY", "R1", "ego_only", "R1_noREMOVE"):
        for k in (f"mean_delta_orig|{m}", f"rel_loss|{m}"):
            chk[k] = {"point": [out["point"]["frame"][k], ref["point"][k]],
                      "ci95_scenario": [out["bootstrap"]["frame"]["scenario"][k]["ci95"], ref["bootstrap_scenario"][k]["ci95"]],
                      "ci95_block10": [out["bootstrap"]["frame"]["block10"][k]["ci95"], ref["bootstrap_block10"][k]["ci95"]]}
    k = "paired_mean_orig|R1-B-RAY"
    chk[k] = {"point": [out["point"]["frame"][k], ref["point"][k]],
              "ci95_scenario": [out["bootstrap"]["frame"]["scenario"][k]["ci95"], ref["bootstrap_scenario"][k]["ci95"]]}
    eq = all(a == b for v in chk.values() for a, b in v.values())
    return {"what": "v3_analyze frame-order path, E4 float16 rays (no injection), B-NORM disabled, vs frozen e5a_H.json",
            "identical": eq, "values_[v3, e5a_H]": chk,
            "B-NORM_disabled_equals_undefended": out["point"]["frame"]["mean_delta_orig|B-NORM"] == 0.0}


STEALTH_MIN_LOSS = 0.005


def stealth_constraint_check(run_dir, plan, sub="pgd_stealth"):
    """Independent re-check from the stored magnitudes (B-NORM's own computation): on every attacked frame and
    scale, ratio <= 0.95 tau_k (1 + 1e-6); |delta| <= eps_k and f + delta >= 0 from the attack ledger."""
    tau = np.asarray(plan["tau_k"], float)
    bound = 0.95 * tau
    R, bad, n = {}, [], 0
    for p in sorted(glob.glob(os.path.join(run_dir, sub, "20*_[0-9][0-9].pkl.gz"))):
        G = _load(p)
        for fr in G["frames"]:
            for c, rec in fr["conditions"].items():
                if "mabs" not in rec:
                    assert rec["ledger"].get("reason") == "stealth_infeasible", rec["ledger"]
                    continue
                m = np.asarray(rec["mabs"], float)
                r = m[1] / m[0]
                led = rec["ledger"]
                n += 1
                ok = bool(np.all(r <= bound * (1 + 1e-6))) and all(
                    l <= e * (1 + 1e-6) for l, e in zip(led["linf_delta"], led["eps"]))
                if not ok:
                    bad.append({"scen": G["scenario"], "frame": fr["frame"], "cond": c, "ratio": r.tolist()})
                R.setdefault(c, []).append(r)
    summ = {c: {"frames": len(v), "ratio_median": np.median(v, 0).round(4).tolist(), "ratio_max": np.max(v, 0).round(5).tolist(),
                "frac_above_tau": (np.asarray(v) > tau).mean(0).round(4).tolist()} for c, v in sorted(R.items())}
    return {"attacked_frame_conditions": n, "violations": bad[:20], "n_violations": len(bad), "holds": not bad,
            "bound_0.95tau": bound.tolist(), "by_condition": summ}


def run_H_stealth(run_dir, n_boot):
    rd = os.path.join(ROOT, run_dir)
    plan = json.load(open(os.path.join(rd, "plan_stealth.json")))
    tau = plan["tau_k"]
    lv = {f: plan["levels_r"] for f in plan["families"]}
    opt1 = ("pgd_untargeted@r0.25", "pgd_remove@r0.25")              # D-67
    st = tuple(f"{f}@r{r}" for f in lv for r in lv[f])
    conds = ("clean",) + ORIG + ("spoof_blind",) + opt1 + st
    meta = []
    out, _, _ = analyze(frames_H(rd, meta=meta, pgd_subs=("pgd", "pgd_stealth"), keep=set(opt1 + st)), conds, tau, n_boot)
    res = {"label": "DEVELOPMENT, block H (exposed, D-53); stealth PGD = attack design on exposed H, POST HOC (D-68 "
                    "as amended); 4 scenarios, n = 2; not a test",
           "plan": os.path.relpath(os.path.join(rd, "plan_stealth.json"), ROOT), "scenario_files": meta}
    res.update(out)
    res["pgd_selection"] = pgd_selection(out["point"], lv)
    res["stealth_stop_check"] = {f: {"attack_loss_global_r1.0": out["point"]["global"][f"attack_loss|{f}@r1.0"],
                                     "ineffective": out["point"]["global"][f"attack_loss|{f}@r1.0"] < STEALTH_MIN_LOSS}
                                 for f in lv}
    res["stealth_stop_check"]["stop"] = any(v["ineffective"] for v in res["stealth_stop_check"].values())
    res["constraint_check"] = stealth_constraint_check(rd, plan)
    res["expected_outcomes"] = expected_outcomes(out["point"], conds)
    json.dump(res, open(os.path.join(rd, "pgd_stealth_H_results.json"), "w"), indent=1, default=str)
    return res


def run_test(run_dir, prereg_p, n_boot, dry=False):
    rd = os.path.join(ROOT, run_dir)
    pr = json.load(open(os.path.join(ROOT, prereg_p)))
    tau = pr["B-NORM"]["tau_k"]
    conds = ("clean",) + ORIG + ("spoof_blind",) + tuple(pr["pgd_families"]["test_conditions"])
    meta = []
    out, _, _ = analyze(frames_test(rd, meta), conds, tau, n_boot)
    complete = {"scenarios": [len(meta), TEST_SCEN], "frames": [out["frames"], TEST_FRAMES],
                "pass": len(meta) == TEST_SCEN and out["frames"] == TEST_FRAMES}
    res = {"label": "DRY RUN (development dev slice; not results)" if dry else "FINAL TEST (one-time), v3 analysis",
           "preregistration": prereg_p, "scenario_files": meta, "completeness_check": complete}
    res.update(out)
    res["expected_outcomes"] = expected_outcomes(out["point"], conds)
    # consistency: frame-order v3 point/CIs of the v2 statistics must equal the frozen e5_analyze output
    v2p = os.path.join(rd, "e5_test.json")
    if os.path.exists(v2p):
        v2 = json.load(open(v2p))
        ks = ["mean_delta_orig|B-RAY", "mean_delta_orig|R1", "rel_loss|B-RAY", "paired_mean_orig|R1-B-RAY"]
        res["consistency_vs_frozen_v2"] = {
            k: {"point": [out["point"]["frame"][k], v2["point"][k]],
                "ci95_scenario": [out["bootstrap"]["frame"]["scenario"][k]["ci95"], v2["bootstrap_scenario"][k]["ci95"]]}
            for k in ks}
        res["consistency_vs_frozen_v2"]["identical"] = all(
            a == b for k in ks for a, b in res["consistency_vs_frozen_v2"][k].values())
    json.dump(res, open(os.path.join(rd, "e5_v3.json"), "w"), indent=1, default=str)
    if not dry and not complete["pass"]:
        sys.exit(f"STOP: completeness check failed {complete} (results written, flagged incomplete)")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("H", "H_stealth", "test", "dry"))
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--prereg", default="runs/20261024-E5/preregistration_v3.json")
    ap.add_argument("--n_boot", type=int, default=N_BOOT)
    a = ap.parse_args()
    if a.mode == "H":
        r = run_H(a.run_dir, a.n_boot)
    elif a.mode == "H_stealth":
        r = run_H_stealth(a.run_dir, a.n_boot)
    else:
        r = run_test(a.run_dir, a.prereg, a.n_boot, dry=a.mode == "dry")
    show = {k: r[k] for k in r if k in ("frames", "criteria_v3", "pgd_selection", "B-NORM_stop_check", "B-NORM_flags",
                                         "completeness_check", "consistency_vs_e5a_H", "consistency_vs_frozen_v2",
                                         "stealth_stop_check")}
    print(json.dumps(show, indent=1, default=str))


if __name__ == "__main__":
    main()
