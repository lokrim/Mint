"""CULVER no-network dry run (D-72): the Culver pipeline end to end on the local block-T dev slice. Not results.

1. culver_stream checks without network: allowlist refusals, --dry_run (frozen hashes + budget from plan.json).
2. The exact per-scenario call culver_stream makes (v3_2_stream.install(), then v3_1_stream.run_scenario) on the
   first NF frames of the dev slice (2021_08_22_13_37_16, n = 2), and a check that every record equals the
   committed v3.2 dry run (runs/20261024-E5/dryrun_v3_2/n2) on those frames, wall-clock fields excepted.
3. culver_stream.sanity_clean_ap on the dev slice (the clean-detector sanity path).
4. culver_analyze --dry and culver_report (status DEVELOPMENT) on the dry-run outputs.
5. Frozen hashes re-checked.

  python runners/culver_dryrun.py [--out runs/20261026-CULVER/dryrun] [--frames 12] [--n_boot 200]
"""
import argparse
import gzip
import json
import os
import pickle
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import culver_stream as C  # noqa: E402
import v3_1_stream as S31  # noqa: E402
import v3_2_stream as S32  # noqa: E402
import v3_common as V  # noqa: E402
import v3_stream as S3  # noqa: E402
from stage1_reproduce import CKPT  # noqa: E402

import torch  # noqa: E402

SCEN = "2021_08_22_13_37_16"
DEV_ROOT = os.path.join(ROOT, "data/opv2v/devslice/validate")
V32_DRY = "runs/20261024-E5/dryrun_v3_2/n2"
WALL = {"frame_s", "v3_s", "attack_s"}
PY = os.path.join(ROOT, ".venv/bin/python")


def _load(p):
    with gzip.open(p, "rb") as f:
        return pickle.load(f)


def _strip(x):
    if isinstance(x, dict):
        return {k: _strip(v) for k, v in x.items() if k not in WALL}
    if isinstance(x, list):
        return [_strip(v) for v in x]
    return x


def sh(*args):
    r = subprocess.run([PY, *args], cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/20261026-CULVER/dryrun")
    ap.add_argument("--frames", type=int, default=12)
    ap.add_argument("--n_boot", type=int, default=200)
    a = ap.parse_args()
    out = os.path.join(ROOT, a.out)
    summ = {"label": "DRY RUN of the CULVER pipeline (development, block-T dev slice, no network); not results",
            "scenario": SCEN, "frames": a.frames}

    rc, txt = sh("runners/culver_stream.py", "--run_dir", a.out, "--scenarios", SCEN, "--dry_run")      # 1.
    summ["refuses_non_culver_scenario"] = rc != 0 and "allowlist" in txt
    rc, txt = sh("runners/culver_stream.py", "--run_dir", a.out, "--byte_budget", "8000000000", "--dry_run")
    summ["refuses_budget_above_7e9"] = rc != 0 and "budget" in txt
    rc, txt = sh("runners/culver_stream.py", "--run_dir", a.out)
    summ["refuses_without_user_approved"] = rc != 0 and "approval" in txt
    rc, txt = sh("runners/culver_stream.py", "--run_dir", a.out, "--dry_run")
    summ["culver_stream_dry_run"] = json.loads(txt[txt.index("{"):]) if rc == 0 else txt
    print(json.dumps(summ, indent=1), flush=True)

    S32.install()                                                                               # 2.
    pr = json.load(open(os.path.join(ROOT, S3.PREREG)))
    summ["frozen_check_before_run"] = S3.verify_frozen(pr) or "OK"
    from opencood.tools import train_utils
    import opencood.hypes_yaml.yaml_utils as yaml_utils
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    for sub in ("cache", "v3extra"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    p, px = os.path.join(out, "cache", f"{SCEN}.pkl.gz"), os.path.join(out, "v3extra", f"{SCEN}.pkl.gz")
    t0 = time.time()
    S31.run_scenario(SCEN, DEV_ROOT, model, hyp, p, px, pr, reps=1, max_frames=a.frames, block="DRYRUN")
    summ["stream_s"] = round(time.time() - t0)
    mine, ref = _load(p), _load(os.path.join(ROOT, V32_DRY, "cache", f"{SCEN}.pkl.gz"))
    mx, rx = _load(px), _load(os.path.join(ROOT, V32_DRY, "v3extra", f"{SCEN}.pkl.gz"))
    k = len(mine["frames"])
    summ["identical_vs_v3_2_dryrun"] = {
        "frames_compared": k,
        "cache_frames": bool(V.same(_strip(mine["frames"]), _strip(ref["frames"][:k]))),
        "v3extra_frames": bool(V.same(_strip(mx["frames"]), _strip(rx["frames"][:k]))),
        "levels_sigma_prereg": bool(V.same(mx["levels"], rx["levels"]) and V.same(mx["sigma"], rx["sigma"])
                                    and mx["preregistration"] == rx["preregistration"] == S32.PREREG_V32),
        "compose_all_identical": all(c["same_candidates"] and c["same_final"] for c in mine["compose_checks"])}
    print("identical vs v3.2 dry run:", json.dumps(summ["identical_vs_v3_2_dryrun"]), flush=True)

    sp = os.path.join(out, "sanity_dev_slice.json")                                              # 3.
    s = C.sanity_clean_ap(SCEN, DEV_ROOT, model, hyp, sp)
    summ["sanity_path_dev_slice"] = {k2: s[k2] for k2 in ("frames", "ap_frame_order_opencood_default", "seconds")}

    rc, txt = sh("runners/culver_analyze.py", "--run_dir", a.out, "--dry", "--n_boot", str(a.n_boot))  # 4.
    summ["culver_analyze_rc"] = rc
    v3 = json.load(open(os.path.join(out, "e5_v3.json")))
    summ["analysis_label"] = v3["label"]
    summ["analysis_conditions"] = v3["conditions"]
    summ["analysis_consistency_vs_frozen_v2"] = (v3.get("consistency_vs_frozen_v2") or {}).get("identical")
    rc2, txt2 = sh("runners/culver_report.py", "--run_dir", a.out, "--out", os.path.join(a.out, "report"))
    summ["culver_report_rc"] = rc2
    summ["culver_report_out"] = txt2.splitlines()[-1] if txt2 else ""
    summ["frozen_check_after_run"] = S3.verify_frozen(pr) or "OK"                                 # 5.
    json.dump(summ, open(os.path.join(out, "dryrun_culver.json"), "w"), indent=1, default=str)
    print(json.dumps(summ, indent=1, default=str), flush=True)
    if rc or rc2:
        print(txt[-3000:], txt2[-3000:], sep="\n")


if __name__ == "__main__":
    main()
