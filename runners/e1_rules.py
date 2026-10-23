"""E1 Parts B and C from the E0 caches (development block T; in-sample; no new data).

Part B: rule R1 (mint.reliability.r1, Wilson resolvability) vs MINT-v0.0 theta = 0
(mint.reliability.v0) on clean + 4 attack families: AP@0.5/0.7, recovery of attack loss, clean
relative loss, gated units and false rejections of USEFUL units by effect type, SHIFT displacement.
Part C: on UNKNOWN_NO_EVIDENCE units, AUROC of the cached per-tile attention share (attn_tile) vs
HARMFUL, per condition, with a scenario block bootstrap. Attention is attacker-influenced: this
tests a non-adaptive attacker only.

Decisions use cached receiver-side quantities only; GT is used afterwards for AP and labels.
Pre-registration: runs/20261023-E1/preregistration.json.

  python runners/e1_rules.py runs/20261023-E0 --out runs/20261023-E1
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

RULES = {"theta0": (v0, v0.Params(theta=0.0)), "R1": (r1, v0.Params())}
TYPES = ("ADD", "REMOVE", "SHIFT")
D_BINS = ((0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 1e9))


def gating_effects(rule, rel):
    """Effects that push a gated unit towards removal (attribution for the breakdown).

    theta0: effects with h_keep > h_remove (v0's h_keep is the raw harm-of-keeping score, so these
    push the unit score towards gating); R1: effects whose verdict is 'gate'."""
    if rule == "R1":
        return [e for e, v in zip(rel.effects, rel.verdicts) if v == "gate"]
    out = []
    for e in rel.effects:
        hk, hr = v0.effect_scores(e)
        if hk > hr:
            out.append(e)
    return out


def shift_d(e):
    return float(np.linalg.norm(np.asarray(e["plus"]).mean(0)[:2] - np.asarray(e["minus"]).mean(0)[:2]))


def boot_auroc(recs, n_boot=2000, seed=0):
    scen = sorted({r["scen"] for r in recs})
    by = {s: [r for r in recs if r["scen"] == s] for s in scen}
    rng = np.random.default_rng(seed)
    vals, dropped = [], 0
    for _ in range(n_boot):
        pick = [r for s in rng.choice(scen, len(scen)) for r in by[s]]
        a = A.auroc([r["attn"] for r in pick if r["harmful"]], [r["attn"] for r in pick if not r["harmful"]])
        if a is None:
            dropped += 1
        else:
            vals.append(a)
    ci = None if not vals else [round(float(np.percentile(vals, 2.5)), 3), round(float(np.percentile(vals, 97.5)), 3)]
    return ci, dropped


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("run_dir")
    ap_.add_argument("--out", default=os.path.join(ROOT, "runs/20261023-E1"))
    ap_.add_argument("--glob", default="20*_[0-9][0-9].pkl.gz")
    a = ap_.parse_args()
    run_dir = a.run_dir if os.path.isabs(a.run_dir) else os.path.join(ROOT, a.run_dir)
    out_dir = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    pp = A.post_processor()
    conds = ("clean",) + A.FAMILIES
    stats = {}
    units = {(c, r): [] for c in conds for r in RULES}
    blind = {c: [] for c in conds}
    files = sorted(glob.glob(os.path.join(run_dir, "cache", a.glob)))
    for fpath in files:
        R = pickle.load(gzip.open(fpath))
        scen = R["scenario"]
        for fr in R["frames"]:
            n = fr["n_agents"]
            for cond in conds:
                use = cond if n >= 2 else "clean"
                pol, recs, applied, c = A.frame_policies(pp, fr, use, n)
                lab = {(r["sender"], r["tile"]): r["D"] for r in recs}
                stats.setdefault((cond, "undefended"), []).append(A.frame_stat(*pol["undefended"], fr["gt"]))
                for rname, (mod, prm) in RULES.items():
                    rel = mod.assess(c["effects"], prm)
                    ch = v0.gating_choice(rel)
                    yb, ys = finalize(pp, compose(c["cands"], ch)) if ch else pol["undefended"]
                    stats.setdefault((cond, rname), []).append(A.frame_stat(yb, ys, fr["gt"]))
                    for k, r in rel.items():
                        ge = gating_effects(rname, r) if r.gate else []
                        units[(cond, rname)].append({
                            "scen": scen, "frame": fr["frame"], "sender": k[0], "status": r.status, "gate": r.gate,
                            "D": lab.get(k, 0.0), "types": sorted({e["type"] for e in r.effects}),
                            "gating_types": sorted({e["type"] for e in ge}),
                            "gating_shift_d": [shift_d(e) for e in ge if e["type"] == "SHIFT"]})
                # Part C population: blind units; families only where the attack was applied
                if n >= 2 and (cond == "clean" or applied):
                    at = c["attn_tile"]
                    rel = v0.assess(c["effects"], v0.Params())
                    for k, r in rel.items():
                        if r.status != "UNKNOWN_NO_EVIDENCE":
                            continue
                        i, (tr, tc) = k
                        if not (0 <= tr < at.shape[1] and 0 <= tc < at.shape[2]):
                            continue
                        blind[cond].append({"scen": scen, "sender": i, "attn": float(at[i, tr, tc]),
                                            "harmful": lab.get(k, 0.0) > A.M})
        print("done", scen, flush=True)

    M = A.M
    out = {"note": "E1 development evaluation, block T (3 scenarios), in-sample; R1 is a resolvability margin on "
                   "spatially correlated ray counts, not a calibrated probability; theta0 = MINT-v0.0 raw score",
           "preregistration": "runs/20261023-E1/preregistration.json"}
    ap = {k: A.ap(A.merge(v)) for k, v in stats.items()}
    clean = ap[("clean", "undefended")]
    tab = {}
    for cond in conds:
        row = {}
        for pol in ("undefended",) + tuple(RULES):
            r = ap[(cond, pol)]
            row[pol] = {f"AP@{k}": round(v, 4) for k, v in r.items() if k in (0.5, 0.7)}
            if cond == "clean" and pol != "undefended":
                for k in (0.5, 0.7):
                    row[pol][f"rel_loss_AP@{k}"] = round(1 - r[k] / clean[k], 4)
            if cond != "clean":
                for k in (0.5, 0.7):
                    loss = clean[k] - ap[(cond, "undefended")][k]
                    row[pol][f"attack_loss_AP@{k}"] = round(loss, 4)
                    if pol != "undefended":
                        row[pol][f"recovery_AP@{k}"] = None if loss < 0.005 else \
                            round((r[k] - ap[(cond, "undefended")][k]) / loss, 3)
        tab[cond] = row
    out["AP"] = tab

    brk = {}
    for cond in conds:
        for rname in RULES:
            U = units[(cond, rname)]
            G = [u for u in U if u["gate"]]
            H = [u for u in U if u["D"] > M]
            Us = [u for u in U if u["D"] < -M]
            FR = [u for u in Us if u["gate"]]
            d = {"units": len(U), "known": sum(u["status"] == "KNOWN" for u in U), "gated": len(G),
                 "gated_harmful": sum(u["D"] > M for u in G), "gated_neutral": sum(-M <= u["D"] <= M for u in G),
                 "false_rejections_useful": len(FR), "useful_units": len(Us), "harmful_units": len(H),
                 "harmful_known": sum(u["status"] == "KNOWN" for u in H),
                 "precision": None if not G else round(sum(u["D"] > M for u in G) / len(G), 3),
                 "recall_known_harmful": None if not [u for u in H if u["status"] == "KNOWN"] else
                 round(sum(u["gate"] for u in H) / sum(u["status"] == "KNOWN" for u in H), 3)}
            for typ in TYPES:
                d[f"gated_by_{typ}"] = sum(typ in u["gating_types"] for u in G)
                d[f"gated_harmful_by_{typ}"] = sum(typ in u["gating_types"] for u in G if u["D"] > M)
                d[f"false_rej_by_{typ}"] = sum(typ in u["gating_types"] for u in FR)
            for name, grp in (("harmful", [u for u in G if u["D"] > M]), ("false_rej", FR),
                              ("neutral", [u for u in G if -M <= u["D"] <= M])):
                ds = [x for u in grp for x in u["gating_shift_d"]]
                d[f"shift_d_{name}"] = {"n": len(ds), "median": None if not ds else round(float(np.median(ds)), 2),
                                        **{f"{lo}-{hi if hi < 1e8 else 'inf'}m": sum(lo <= x < hi for x in ds)
                                           for lo, hi in D_BINS}}
            brk[f"{cond}/{rname}"] = d
    out["units"] = brk

    fam_rec = [tab[f]["R1"]["recovery_AP@0.7"] for f in A.FAMILIES]
    used = [x for x in fam_rec if x is not None]
    out["R1_criteria"] = {"mean_recovery_AP@0.7": None if not used else round(float(np.mean(used)), 3),
                          "per_family": dict(zip(A.FAMILIES, fam_rec)),
                          "clean_rel_loss_AP@0.7": tab["clean"]["R1"]["rel_loss_AP@0.7"],
                          "pass_mean>=0.10": bool(used) and float(np.mean(used)) >= 0.10,
                          "pass_clean_loss<=0.01": tab["clean"]["R1"]["rel_loss_AP@0.7"] <= 0.01,
                          "pass_no_family<-0.05": all(x is None or x >= -0.05 for x in fam_rec)}
    out["R1_criteria"]["R1_part_passes"] = bool(out["R1_criteria"]["pass_mean>=0.10"] and
                                                out["R1_criteria"]["pass_clean_loss<=0.01"] and
                                                out["R1_criteria"]["pass_no_family<-0.05"])

    pc = {"population": "UNKNOWN_NO_EVIDENCE units (MINT-v0.0 status), all senders; clean: frames with >= 2 agents; "
                        "families: frames where the attack was applied",
          "score": "attn_tile[sender, tile] (mean attention share, fusion scale 0); higher -> HARMFUL",
          "caveat": "attention is attacker-influenced; non-adaptive attacker only",
          "bootstrap": "scenario blocks (3), 2000 resamples, percentile 95% CI; coarse with 3 blocks"}
    for cond in conds:
        B = blind[cond]
        pos = [r["attn"] for r in B if r["harmful"]]
        neg = [r["attn"] for r in B if not r["harmful"]]
        au = A.auroc(pos, neg)
        ci, dropped = boot_auroc(B)
        att = [r for r in B if r["sender"] == 1]
        au1 = A.auroc([r["attn"] for r in att if r["harmful"]], [r["attn"] for r in att if not r["harmful"]])
        pc[cond] = {"n_units": len(B), "n_harmful": len(pos), "auroc": None if au is None else round(au, 3),
                    "ci95_scenario_bootstrap": ci, "bootstrap_dropped": dropped,
                    "per_scenario": {s: (lambda q: None if q is None else round(q, 3))(A.auroc(
                        [r["attn"] for r in B if r["scen"] == s and r["harmful"]],
                        [r["attn"] for r in B if r["scen"] == s and not r["harmful"]]))
                        for s in sorted({r["scen"] for r in B})},
                    "secondary_sender1_only_auroc": None if au1 is None else round(au1, 3),
                    "meets": bool(au is not None and au >= 0.70 and ci is not None and ci[0] > 0.60)}
    nfam = sum(pc[f]["meets"] for f in A.FAMILIES)
    pc["families_meeting"] = nfam
    pc["follow_up"] = nfam >= 3
    out["partC"] = pc
    os.makedirs(out_dir, exist_ok=True)
    json.dump(out, open(os.path.join(out_dir, "rules_and_blind.json"), "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in out.items()}, indent=1, default=str))


if __name__ == "__main__":
    main()
