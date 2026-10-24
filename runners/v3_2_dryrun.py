"""v3.2 no-network dry run (D-71): DEVELOPMENT smoke test on the block-T dev slice; numbers are not results.

1. The frozen v3_dryrun (n2 / forced n1 / forced n5) with the v3.2 stream installed, then a check that every
   record equals the committed v3.1 dry run (runs/20261024-E5/dryrun_v3_1) except wall-clock fields: the dev
   slice has no stealth-infeasible frame, so D-71 must change nothing there.
2. Forced-infeasible check (the D-71 branch on the real model and data): n2, first FORCED_FRAMES frames, with the
   stream's tau_k scaled by TAU_SCALE so every stealth condition is infeasible (real feasibility test, nothing
   stubbed). (a) the v3.1 v3_extra raises KeyError 'mabs' (the final-test crash, reproduced); (b) the v3.2 stream
   completes; stealth records are ledger-only with reason stealth_infeasible and absent from mabs, other records
   unchanged in shape; (c) the frozen v3_analyze.run_test (preregistration_v3_2, real tau_k) completes and counts
   every stealth frame as infeasible and not applied.

  python runners/v3_2_dryrun.py [--out runs/20261024-E5/dryrun_v3_2] [--n_boot 200]
"""
import copy
import gzip
import json
import os
import pickle
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import v3_1_stream as S31  # noqa: E402
import v3_2_stream as S32  # noqa: E402

V31_DRY = "runs/20261024-E5/dryrun_v3_1"
WALL = {"frame_s", "v3_s", "attack_s"}
FORCED_FRAMES = 4
TAU_SCALE = 1e-3
V31_V3_EXTRA = S31.v3_extra                     # the frozen v3.1 function, kept before install() replaces it


def _load(p):
    with gzip.open(p, "rb") as f:
        return pickle.load(f)


def _strip(x):
    if isinstance(x, dict):
        return {k: _strip(v) for k, v in x.items() if k not in WALL}
    if isinstance(x, list):
        return [_strip(v) for v in x]
    return x


def identical_vs_v31(out, tag, scen):
    import v3_common as V
    d32, d31 = os.path.join(ROOT, out, tag), os.path.join(ROOT, V31_DRY, tag)
    a, b = _load(os.path.join(d32, "cache", f"{scen}.pkl.gz")), _load(os.path.join(d31, "cache", f"{scen}.pkl.gz"))
    a.pop("timing"), b.pop("timing")
    x, y = _load(os.path.join(d32, "v3extra", f"{scen}.pkl.gz")), _load(os.path.join(d31, "v3extra", f"{scen}.pkl.gz"))
    return {"cache_v2_record_identical": bool(V.same(_strip(a), _strip(b))),
            "v3extra_frames_identical": bool(V.same(_strip(x["frames"]), _strip(y["frames"]))),
            "v3extra_levels_sigma_identical": bool(V.same(x["levels"], y["levels"]) and V.same(x["sigma"], y["sigma"])),
            "v3extra_preregistration": [x["preregistration"], y["preregistration"]],
            "infeasible_records": sum(r.get("ledger", {}).get("reason") == "stealth_infeasible"
                                      for f in x["frames"] for r in f["pgd"].values())}


def forced_infeasible(out, n_boot, scen, dev_root):
    import v3_analyze as Y
    import v3_stream as S3
    import torch
    from opencood.tools import train_utils
    import opencood.hypes_yaml.yaml_utils as yaml_utils
    from stage1_reproduce import CKPT

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    torch.set_num_threads(8)
    pr = json.load(open(os.path.join(ROOT, S32.PREREG_V32)))
    forced = copy.deepcopy(pr)
    forced["B-NORM"]["tau_k"] = [t * TAU_SCALE for t in pr["B-NORM"]["tau_k"]]
    rd = os.path.join(ROOT, out, "n2_forced_infeasible")
    for sub in ("cache", "v3extra"):
        os.makedirs(os.path.join(rd, sub), exist_ok=True)
    p, px = os.path.join(rd, "cache", f"{scen}.pkl.gz"), os.path.join(rd, "v3extra", f"{scen}.pkl.gz")
    res = {"frames": FORCED_FRAMES, "tau_scale_stream_only": TAU_SCALE}

    S31.v3_extra = V31_V3_EXTRA                                         # (a) v3.1 path
    try:
        S31.run_scenario(scen, dev_root, model, hyp, p + ".v31", px + ".v31", forced, reps=1, max_frames=1)
        res["v31_raises_keyerror_mabs"] = False
    except KeyError as e:
        res["v31_raises_keyerror_mabs"] = e.args == ("mabs",)
    finally:
        S31.v3_extra = S32.v3_extra
    for q in (p + ".v31", px + ".v31"):
        if os.path.exists(q):
            os.remove(q)

    t0 = time.time()                                                    # (b) v3.2 path
    _, extras = S31.run_scenario(scen, dev_root, model, hyp, p, px, forced, reps=1, max_frames=FORCED_FRAMES)
    res["stream_s"] = round(time.time() - t0)
    stealth = [c for c in pr["pgd_families"]["test_conditions"] if "_stealth@" in c]
    others = [c for c in pr["pgd_families"]["test_conditions"] if c not in stealth]
    ok_s = all(set(e["pgd"][c]) <= {"ledger", "attack_s"} and e["pgd"][c]["ledger"]["reason"] == "stealth_infeasible"
               and c not in e["mabs"] for e in extras for c in stealth)
    ok_o = all("mabs" in e["pgd"][c] and "cands" in e["pgd"][c] and c in e["mabs"] for e in extras for c in others)
    res["stealth_records_ledger_only_not_in_mabs"] = ok_s
    res["other_records_complete"] = ok_o

    v3 = Y.run_test(os.path.relpath(rd, ROOT), S32.PREREG_V32, n_boot, dry=True)   # (c) frozen analysis
    tot = {c: v3["pgd_by_scenario"][c]["total"] for c in pr["pgd_families"]["test_conditions"]}
    res["analysis_pgd_totals"] = tot
    res["analysis_stealth_all_infeasible_not_applied"] = all(
        tot[c]["infeasible"] == tot[c]["frames_with_sender"] == FORCED_FRAMES and tot[c]["applied"] == 0 for c in stealth)
    res["analysis_B-NORM_flags_stealth"] = {c: v3["B-NORM_flags"].get(c) for c in stealth}
    res["pass"] = all(res[k] for k in ("v31_raises_keyerror_mabs", "stealth_records_ledger_only_not_in_mabs",
                                       "other_records_complete", "analysis_stealth_all_infeasible_not_applied"))
    assert S3.PREREG == S32.PREREG_V32
    return res


def main():
    if "--out" not in sys.argv:
        sys.argv += ["--out", "runs/20261024-E5/dryrun_v3_2"]
    out = sys.argv[sys.argv.index("--out") + 1]
    n_boot = int(sys.argv[sys.argv.index("--n_boot") + 1]) if "--n_boot" in sys.argv else 200
    S32.install()
    import v3_dryrun as D
    D.main()                                                            # 1. frozen v3 dry run, v3.2 installed
    p = os.path.join(ROOT, out, "dryrun_v3.json")
    summ = json.load(open(p))
    summ["label"] = "DRY RUN v3.2 (D-71; development, block-T dev slice, no network); not results"
    summ["identical_vs_v3_1_dryrun"] = {tag: identical_vs_v31(out, tag, D.SCEN) for tag in summ["runs"]}
    print("identical vs v3.1:", json.dumps(summ["identical_vs_v3_1_dryrun"]), flush=True)
    json.dump(summ, open(p, "w"), indent=1, default=str)
    summ["forced_infeasible"] = forced_infeasible(out, n_boot, D.SCEN, D.DEV_ROOT)   # 2. the D-71 branch
    print("forced infeasible:", json.dumps(summ["forced_infeasible"], default=str), flush=True)
    import v3_stream as S3
    summ["frozen_check_after_run"] = S3.verify_frozen(json.load(open(os.path.join(ROOT, S32.PREREG_V32)))) or "OK"
    json.dump(summ, open(p, "w"), indent=1, default=str)
    print("v3.2 dry run done; frozen check after:", summ["frozen_check_after_run"], flush=True)


if __name__ == "__main__":
    main()
