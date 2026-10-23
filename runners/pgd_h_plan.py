"""v3 step 2a: write runs/<run>/plan.json BEFORE any PGD run on block H.

Computes, from the clean block-H frames of the re-stream side records (no attack, no AP, no PGD):
  sigma_k  pooled std of all elements of the sender (agent >= 1) scale-k feature maps over clean frames
  tau_k    99.5th percentile (numpy linear interpolation) over clean frames and senders of
           mean |feature_i,k| / mean |feature_receiver,k|   (B-NORM threshold, D-66)
and records every rule of the development run and the test-level selection rule (fixed here).

  python runners/pgd_h_plan.py --run_dir runs/20261024-PGD
"""
import argparse
import glob
import gzip
import hashlib
import json
import os
import pickle
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))

import numpy as np  # noqa: E402

LEVELS = (0.25, 0.5, 1.0)
FAMILIES = ("pgd_untargeted", "pgd_remove")
TAU_PCT = 99.5
CODE = ("src/mint/attacks/pgd_v3.py", "src/mint/reliability/bnorm.py", "runners/v3_common.py",
        "runners/pgd_h_stream.py", "runners/pgd_h_plan.py", "runners/pgd_h_run.py", "runners/v3_analyze.py")


def sha(p):
    return hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()


def clean_stats(extra_dir):
    mom, rat, frames, nsend = None, [], 0, 0
    for p in sorted(glob.glob(os.path.join(extra_dir, "20*_[0-9][0-9].pkl.gz"))):
        X = pickle.load(gzip.open(p))
        for fr in X["frames"]:
            m = np.asarray(fr["moments"], np.float64)            # [n, K, 4]
            if m.shape[0] < 2:
                continue
            frames += 1
            nsend += m.shape[0] - 1
            s = m[1:].sum(0)                                      # senders only: [K, 4]
            mom = s if mom is None else mom + s
            ma = np.asarray(fr["mabs"]["clean"], np.float64)
            rat.append(ma[1:] / ma[0][None])
    cnt, sm, sq, sa = mom[:, 0], mom[:, 1], mom[:, 2], mom[:, 3]
    mean = sm / cnt
    sigma = np.sqrt(sq / cnt - mean ** 2)
    R = np.concatenate(rat, 0)                                    # [senders x frames, K]
    tau = np.percentile(R, TAU_PCT, axis=0)
    flag = np.any(R > tau[None], axis=1)
    return {"frames_with_sender": frames, "sender_maps": int(nsend), "sigma": sigma.tolist(), "mean": mean.tolist(),
            "mean_abs": (sa / cnt).tolist(), "tau": tau.tolist(),
            "ratio_quantiles": {q: np.percentile(R, q, axis=0).round(4).tolist() for q in (0, 1, 50, 99, 99.5, 100)},
            "clean_flag_rate": float(flag.mean()), "clean_flagged_sender_frames": int(flag.sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    a = ap.parse_args()
    rd = os.path.join(ROOT, a.run_dir)
    chk = json.load(open(os.path.join(rd, "reproduction_check.json")))
    assert chk["reproduces_exactly"], "STOP: re-streamed H does not reproduce E4/E5a-H"
    st = clean_stats(os.path.join(rd, "extra"))
    sig = st["sigma"]
    plan = {
        "id": "v3-PGD-H", "date": "2026-10-24",
        "label": "DEVELOPMENT, block H (exposed, D-53); committed before any PGD run on block H",
        "decisions": ["D-64", "D-65", "D-66 (decision_log_proposed_appendix.md)"],
        "data": {"block": "H", "scenarios": 4, "frames_with_sender": st["frames_with_sender"],
                 "cache": f"{a.run_dir}/cache (E4 format, reproduces E4/E5a-H exactly: reproduction_check.json)",
                 "side_records": f"{a.run_dir}/extra (exact model inputs, float64 Y+ rays, feature moments, B-NORM magnitudes)"},
        "feature_scale_clean_H": {
            "what": "pooled over all elements of sender (agent 1) maps, clean frames with n >= 2, per fusion scale k "
                    "(scale shapes [64,100,352], [128,50,176], [256,25,88])",
            "sigma_k": sig, "mean_k": st["mean"], "mean_abs_k": st["mean_abs"],
            "frames": st["frames_with_sender"], "sender_maps": st["sender_maps"]},
        "threat_model": {
            "attacker": "white-box (model weights, receiver features, fusion and heads known), single attacker = sender 1, "
                        "perturbs only its own intermediate features at all 3 fusion scales; n = 1 frames: no attack "
                        "(scored as clean, as every family)",
            "bound": "L-inf per scale: |delta_k| <= eps_k = r * sigma_k; perturbed features projected onto >= 0 "
                     "(the backbone blocks end in ReLU)",
            "levels_r": list(LEVELS),
            "eps_k_by_r": {str(r): [r * s for s in sig] for r in LEVELS},
            "pgd": {"steps": 10, "step_size": "eps_k / 4", "random_start": "U(-eps_k, eps_k), then projected",
                    "update": "sign of the gradient, ascent, projection after every step", "returned": "final iterate",
                    "seed": "numpy default_rng(sha256('V3PGD|family|r|scenario|frame')[:8], little endian)"},
            "pseudo_labels": "no ground truth. Positive anchors = anchors whose clean fused score >= the post-processor "
                             "score threshold (0.2; the pre-NMS set Y+ is selected from); the clean regression map at "
                             "those anchors is the regression target",
            "objectives": {
                "pgd_untargeted": "maximise mean BCE(score, 1) over positives + mean BCE(score, 0) over negatives + "
                                  "mean smooth-L1(reg - reg_clean) over positive anchors' 7 regression values",
                "pgd_remove": "maximise mean BCE(score, 1) over positives (= minimise the scores of Y+ boxes)"},
            "code": "src/mint/attacks/pgd_v3.py (differentiable path asserted bitwise equal to the frozen decode on clean features)"},
        "selection_rule_for_test": {
            "rule": "for each family, the smallest r in {0.25, 0.5, 1.0} whose all-frame attack loss "
                    "AP@0.7(clean, no defense) - AP@0.7(attacked, no defense) under GLOBAL-ranking AP is >= 0.02 on block H; "
                    "if no r reaches 0.02 the family is reported as 'too weak at realistic budgets' and run on the test "
                    "at r = 1.0 anyway",
            "fixed": "before any PGD run on block H"},
        "B-NORM": {
            "rule": "drop sender i entirely in a frame iff, at any scale k, mean|feature_i,k| / mean|feature_receiver,k| "
                    "> tau_k; output = candidates decoded without the dropped senders",
            "tau_k": st["tau"], "tau_definition": f"{TAU_PCT}th percentile (numpy linear) over clean block-H sender-frames",
            "clean_ratio_quantiles": st["ratio_quantiles"],
            "clean_flag_rate_at_tau": st["clean_flag_rate"], "clean_flagged_sender_frames": st["clean_flagged_sender_frames"],
            "no_other_tuning": True, "code": "src/mint/reliability/bnorm.py"},
        "development_run": {
            "methods": ["no defense", "ego-only", "B-NORM", "B-RAY", "R1", "R1-noREMOVE"],
            "conditions": ["clean", "spoof_feat", "remove_feat", "shift_feat", "spoof_pts", "spoof_blind"]
                          + [f"{f}@r{r}" for f in FAMILIES for r in LEVELS],
            "AP": ["frame-order (OpenCOOD global_sort_detections=False, frozen)", "global score ranking"],
            "iou": [0.7, 0.5],
            "CIs": "95% percentile bootstrap, 2000 resamples, seed 0: 10-frame blocks within scenario (stratified) and "
                   "whole scenarios (4, coarse)",
            "statistics": ["per family dAP and recovery per method", "mean of 4 original families (v2 primary statistic)",
                           "mean of 3 (excluding remove_feat)", "R1 - B-RAY paired", "clean relative loss",
                           "Holm co-test of B-RAY and R1 vs no defense per AP definition (scenario bootstrap)",
                           "B-NORM catch rate (sender 1 flagged) per condition and clean false-flag rate",
                           "realized-only tables"],
            "realized": {"spoof_feat/spoof_pts/spoof_blind/remove_feat/shift_feat": "as E0-E5 (e0_analyze.realization)",
                         "pgd_remove": "n >= 2 and some clean Y+ box has no attacked Y+ box at BEV IoU >= 0.5",
                         "pgd_untargeted": "n >= 2 and (some clean Y+ box has no attacked match, or some attacked Y+ box "
                                           "has no clean match) at BEV IoU >= 0.5"},
            "B-RAY_rays": "float64 receiver scan for every condition (as the final test); the E5a-H float16 numbers are "
                          "reported alongside for the original families",
            "label": "development, exposed block H"},
        "stop_conditions": ["re-stream over budget", "H not reproduced",
                            "PGD far outside realistic scale: B-NORM catches > 95% of attacked frames at every r "
                            "(for a family) -> report it as a finding and stop before v3",
                            "any frozen method file (r1.py, baselines.py, pipeline.py) would need to change"],
        "expected_outcomes_stated_before_development": {
            "B-RAY": "recovery approximately 0 on pgd_untargeted and pgd_remove",
            "R1": "recovery on pgd_remove > 0"},
        "code_sha256": {p: sha(p) for p in CODE if os.path.exists(os.path.join(ROOT, p))},
    }
    json.dump(plan, open(os.path.join(rd, "plan.json"), "w"), indent=1)
    print(json.dumps({k: plan[k] for k in ("feature_scale_clean_H", "B-NORM")}, indent=1))


if __name__ == "__main__":
    main()
