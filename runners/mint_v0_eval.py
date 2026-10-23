"""MINT-v0.0 development evaluation from the E0 caches (block T only; uncalibrated; in-sample).

Decisions come only from cached receiver-side quantities (effects + receiver ray counts) via
mint.reliability.v0; GT is used afterwards for AP and harm labels. Gated outputs are composed
exactly from the cached per-subset decodes (verified equal to real masked passes).

  python runners/mint_v0_eval.py runs/20261023-E0 [--variant std|gnd]
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
from mint.reliability import v0  # noqa: E402

THETAS = (-1.0, -0.5, 0.0, 0.5, 1.0, 1.5)


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("run_dir")
    ap_.add_argument("--variant", default="std")
    ap_.add_argument("--glob", default="20*_[0-9][0-9].pkl.gz")
    a = ap_.parse_args()
    run_dir = a.run_dir if os.path.isabs(a.run_dir) else os.path.join(ROOT, a.run_dir)
    pp = A.post_processor()
    conds = ("clean",) + A.FAMILIES
    stats = {}                     # (cond, policy) -> [frame stat]
    units = {c: [] for c in conds}  # unit records with labels and v0 outputs at theta=0
    status_counts = {c: {} for c in conds}
    for fpath in sorted(glob.glob(os.path.join(run_dir, "cache", a.glob))):
        R = pickle.load(gzip.open(fpath))
        for fr in R["frames"]:
            n = fr["n_agents"]
            for cond in conds:
                use = cond if n >= 2 else "clean"
                pol, recs, applied, c = A.frame_policies(pp, fr, use, n)
                lab = {(r["sender"], r["tile"]): r for r in recs}
                stats.setdefault((cond, "undefended"), []).append(A.frame_stat(*pol["undefended"], fr["gt"]))
                stats.setdefault((cond, "vis_oracle_all"), []).append(A.frame_stat(*pol["vis_oracle_all"], fr["gt"]))
                for th in THETAS:
                    rel = v0.assess(c["effects"], v0.Params(theta=th, variant=a.variant))
                    ch = v0.gating_choice(rel)
                    yb, ys = finalize(pp, compose(c["cands"], ch)) if ch else pol["undefended"]
                    stats.setdefault((cond, f"mint_theta{th}"), []).append(A.frame_stat(yb, ys, fr["gt"]))
                    if th == 0.0:
                        for k, r in rel.items():
                            L = lab.get(k, {"D": 0.0, "touched": False})
                            units[cond].append({"sender": k[0], "status": r.status, "score": r.score, "gate": r.gate,
                                                "D": L["D"], "touched": L.get("touched", False), "applied": applied})
                            status_counts[cond][r.status] = status_counts[cond].get(r.status, 0) + 1
        print("done", R["scenario"], flush=True)

    out = {"variant": a.variant, "note": "development block T, in-sample, uncalibrated raw scores; not a probability"}
    ap = {k: A.ap(A.merge(v)) for k, v in stats.items()}
    clean = ap[("clean", "undefended")]
    tab = {}
    for cond in conds:
        row = {}
        for pol in ["undefended", "vis_oracle_all"] + [f"mint_theta{t}" for t in THETAS]:
            r = ap[(cond, pol)]
            row[pol] = {str(k): round(v, 4) for k, v in r.items()}
            if cond == "clean" and pol != "undefended":
                row[pol]["rel_loss_AP@0.7"] = round(1 - r[0.7] / clean[0.7], 4)
            if cond != "clean":
                loss = clean[0.7] - ap[(cond, "undefended")][0.7]
                row[pol]["recovery_AP@0.7"] = None if loss < 0.005 else round((r[0.7] - ap[(cond, "undefended")][0.7]) / loss, 3)
        tab[cond] = row
    out["AP"] = tab

    M = A.M
    disc = {}
    for cond in conds:
        U = units[cond]
        K = [u for u in U if u["status"] == "KNOWN"]
        H = [u for u in U if u["D"] > M]
        useful = [u for u in U if u["D"] < -M]
        d = {"units": len(U), "status": status_counts[cond],
             "known_frac": round(len(K) / len(U), 3) if U else None,
             "gated": sum(u["gate"] for u in U),
             "harmful_units": len(H), "harmful_known": sum(u["status"] == "KNOWN" for u in H),
             "gated_harmful": sum(u["gate"] for u in H),
             "precision": None if not sum(u["gate"] for u in U) else round(sum(u["gate"] for u in H) / sum(u["gate"] for u in U), 3),
             "recall_all_harmful": None if not H else round(sum(u["gate"] for u in H) / len(H), 3),
             "recall_known_harmful": None if not [u for u in H if u["status"] == "KNOWN"] else
             round(sum(u["gate"] for u in H) / sum(u["status"] == "KNOWN" for u in H), 3),
             "useful_units": len(useful), "useful_gated (false rejection)": sum(u["gate"] for u in useful),
             "auroc_known_score_vs_harmful": None}
        pos = [u["score"] for u in K if u["D"] > M]
        neg = [u["score"] for u in K if u["D"] <= M]
        au = A.auroc(pos, neg)
        d["auroc_known_score_vs_harmful"] = None if au is None else round(au, 3)
        if cond != "clean":
            T = [u for u in H if u["sender"] == 1 and u["touched"] and u["applied"]]
            d["attack_touched_harmful"] = len(T)
            d["attack_touched_harmful_known"] = sum(u["status"] == "KNOWN" for u in T)
            d["attack_touched_harmful_gated"] = sum(u["gate"] for u in T)
        disc[cond] = d
    out["units_theta0"] = disc
    path = os.path.join(run_dir, f"mint_v0_summary_{a.variant}.json")
    json.dump(out, open(path, "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
