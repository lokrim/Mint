"""Write runs/20261024-E5/preregistration_v3.json (v1/v2 unchanged) from the committed PGD plan and the
block-H development results; sha256 of every frozen file is computed here, at the frozen commit.

  python runners/v3_prereg.py --pgd_run runs/20261024-PGD --frozen_commit <sha> [--dryrun runs/20261024-E5/dryrun_v3]
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2 = "runs/20261024-E5/preregistration_v2.json"
OUT = "runs/20261024-E5/preregistration_v3.json"
CKPT_FILE = "data/opv2v/ckpt/pointpillar_attentive_fusion/pointpillar_attentive_fusion/latest.pth"
EXTRA_FROZEN = ("src/mint/model/attfuse_parts.py", "src/mint/model/opencood_shims.py", "runners/stage1_spike.py",
                CKPT_FILE, "src/mint/attacks/pgd_v3.py", "src/mint/reliability/bnorm.py", "runners/v3_common.py",
                "runners/v3_stream.py", "runners/v3_analyze.py", "runners/v3_dryrun.py")


def sha(p):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, p), "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pgd_run", default="runs/20261024-PGD")
    ap.add_argument("--frozen_commit", required=True)
    ap.add_argument("--dryrun", default=None)
    ap.add_argument("--runtime", default=None, help="json file with the runtime estimate")
    a = ap.parse_args()
    v2 = json.load(open(os.path.join(ROOT, V2)))
    plan = json.load(open(os.path.join(ROOT, a.pgd_run, "plan.json")))
    H = json.load(open(os.path.join(ROOT, a.pgd_run, "pgd_H_results.json")))
    frozen = dict(v2["file_sha256"])
    for p in EXTRA_FROZEN:
        frozen[p] = sha(p)
    changed = {p: (v2["file_sha256"][p], sha(p)) for p in v2["file_sha256"] if sha(p) != v2["file_sha256"][p]}
    if changed:
        sys.exit(f"STOP: a v2-frozen file changed: {changed}")
    oc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=os.path.join(ROOT, "third_party/OpenCOOD"),
                        capture_output=True, text=True).stdout.strip()
    sel = H["pgd_selection"]
    levels = {f: {"r": s["selected_r"], "status": s["status"], "eps_k": [s["selected_r"] * x for x in plan["feature_scale_clean_H"]["sigma_k"]],
                  "attack_loss_global_H_by_r": s["attack_loss_global_by_r"]} for f, s in sel.items()}
    test_conds = [f"{f}@r{v['r']}" for f, v in levels.items()]
    pt = H["point"]
    dev = {"label": "DEVELOPMENT, block H (exposed, D-53; 4 scenarios, 371 frames, n = 2); not a test",
           "file": f"{a.pgd_run}/pgd_H_results.json",
           "criteria_v3_on_H": {d: {"B-RAY_p": H["criteria_v3"][d]["co_test_vs_no_defense"]["B-RAY"]["p_one_sided"],
                                    "R1_p": H["criteria_v3"][d]["co_test_vs_no_defense"]["R1"]["p_one_sided"],
                                    "pass": H["criteria_v3"][d]["pass"],
                                    "R1_minus_BRAY": H["criteria_v3"][d]["R1_minus_BRAY"]} for d in ("frame", "global")},
           "D-64_on_H": H["criteria_v3"]["D-64"],
           "mean_dAP0.7_orig": {d: {m: pt[d].get(f"mean_delta_orig|{m}") for m in ("B-NORM", "B-RAY", "R1", "ego_only")}
                                for d in ("frame", "global")},
           "pgd_recovery_H": H["expected_outcomes"], "B-NORM_flags_H": H["B-NORM_flags"],
           "frozen_after": "no method, attack or rule changed after these numbers were seen"}
    pr = {
        "id": "E5 v3 - one-time final test on the OPV2V test split: v2 plus dual-AP rule (D-64), PGD secondary families (D-65), B-NORM baseline (D-66), per-family / mean-of-3 / realized-only tables and procedural checks",
        "version": "v3 (supersedes v2 runs/20261024-E5/preregistration_v2.json; v1 and v2 kept unchanged)",
        "written": "2026-10-24, after the block-H PGD development run and before any test-scenario byte is downloaded. NOT RUN: the stream needs the user's explicit approval of the final test.",
        "base": "Every field of preregistration_v2.json holds as written unless changed below (data, allowlist, the 5 E4 families and seeds, B-RAY primary, R1 key secondary, Holm co-test, clean bound, strata, D-42 timing, stream safeguards, budget).",
        "user_decisions": "D-64, D-65, D-66 (decision_log_proposed_appendix.md, committed before any v3 computation); the user's approval of preregistration_v3 with the PGD families (chat, 2026-10-24)",
        "frozen_code_commit": a.frozen_commit,
        "frozen_sha256": frozen,
        "frozen_note": "v2's 19 files (unchanged, re-checked equal) + the model code, Stage-1 spike runner and checkpoint (audit e3) + the new v3 files. r1.py, baselines.py, pipeline.py unchanged (sha256 equal to v2). The v3 stream verifies every hash and the OpenCOOD commit before any network access and again after the run.",
        "opencood": {"commit": oc, "local_diff": "none (git status --porcelain --untracked-files=no empty); untracked directory in this repo (.gitignore)"},
        "D-64_dual_AP": {
            "definitions": {"frame": "OpenCOOD frame-order AP (global_sort_detections=False; frames concatenated in (scenario, frame) order; the v2 metric)",
                            "global": "detections of all selected frames ranked by score (stable sort), same AP integral"},
            "rule": "every primary and key-secondary statistic is computed under both definitions with the same bootstrap (seed 0, 2000 resamples, scenario and 10-frame). The v2 success rule (B-RAY Holm-rejected in the co-test with R1 vs no defense on the scenario bootstrap, and B-RAY clean relative loss scenario-CI high <= 1%) is evaluated separately per AP definition, Holm within each definition. A success/robustness claim requires a pass under BOTH. Headline numbers are quoted with global-ranking AP; frame-order AP is reported for comparability with OPV2V papers. If the two disagree the report states 'AP-definition-dependent'. R1 - B-RAY (statement by scenario CI, v2 wording) is reported under both, side by side.",
            "code": "runners/v3_analyze.criteria_v3 / d64; the frame-order path is checked to equal the frozen e5_analyze output (point and scenario CI) on the test caches (consistency_vs_frozen_v2)"},
        "comparison_set": ["no defense", "ego-only", "B-NORM (D-66, new)", "B-RAY (primary)", "R1 (key secondary)", "R1-noREMOVE (ablation)", "oracle bounds as v2 (frozen e5_analyze)"],
        "B-NORM": {"rule": plan["B-NORM"]["rule"], "tau_k": plan["B-NORM"]["tau_k"], "tau_definition": plan["B-NORM"]["tau_definition"],
                   "clean_H_flag_rate": plan["B-NORM"]["clean_flag_rate_at_tau"], "role": "comparison baseline; no criterion",
                   "code": "src/mint/reliability/bnorm.py (no GT, no ledger); magnitudes recorded per condition in the stream (v3extra)"},
        "pgd_families": {
            "role": "pre-registered SECONDARY attack families (D-65); reported per family; not part of the v2 primary mean",
            "threat_model": plan["threat_model"], "sigma_k": plan["feature_scale_clean_H"]["sigma_k"],
            "selection_rule": plan["selection_rule_for_test"], "test_levels": levels, "test_conditions": test_conds,
            "expected_outcomes": {"B-RAY": "recovery approximately 0 on both families (operational: point recovery < 0.10 under both AP definitions)",
                                  "R1": "recovery on pgd_remove > 0 (operational: R1 dAP@0.7 on pgd_remove scenario-CI low > 0 under both AP definitions)",
                                  "stated": "in D-65, before any PGD development run on block H"},
            "realized": plan["development_run"]["realized"]["pgd_remove"] + " (pgd_remove); " + plan["development_run"]["realized"]["pgd_untargeted"] + " (pgd_untargeted)",
            "attacker": "sender 1 at every n >= 2; n = 1 frames scored as clean"},
        "secondary_tables_v3": {
            "per_family": "every condition (clean, 4 original, spoof_blind, PGD at test levels) x every method: AP@0.7/0.5, dAP, recovery (None if attack loss < 0.005), attack loss; both AP definitions; scenario and 10-frame CIs",
            "mean_of_3": "mean dAP@0.7 over spoof_feat, shift_feat, spoof_pts (excluding remove_feat) per method, and R1 - B-RAY, with CIs, both AP definitions",
            "realized_only": "per family, frames where the attack was realized (E0-E5 definition; PGD as above): AP of clean and attacked on those frames, attack loss, dAP and recovery per method, 10-frame CIs, both AP definitions",
            "B-NORM_flags": "per condition: frames, sender-1 flagged (catch rate), any sender flagged; clean false-flag rate",
            "not_criteria": "descriptive; only D-64 + v2 success rule is a criterion"},
        "procedural_checks": {
            "before_stream": "sha256 of every frozen file and the OpenCOOD commit/clean tree (v3_stream.verify_frozen); refuse on any mismatch",
            "interrupted_download": "any ledger entry not 'complete' -> STOP and ask the user (no automatic restart)",
            "after_stream": "frozen hashes re-checked",
            "after_analysis": "15 scenarios and 2066 frames asserted (v3_analyze run_test completeness_check; STOP if not)",
            "consistency": "frame-order v3 numbers of the v2 statistics equal the frozen e5_analyze output"},
        "streaming": {"runner": "runners/v3_stream.py --run_dir runs/<date>-E5v3 --user_approved (refuses without it)",
                      "planned_bytes": v2["streaming"]["planning_size"]["total"], "planned_bytes_x1.01": v2["streaming"]["planning_size"]["total_x1.01"],
                      "byte_budget": v2["streaming"]["byte_budget"], "headroom_bytes": v2["streaming"]["byte_budget"] - v2["streaming"]["planning_size"]["total_x1.01"],
                      "other": "as v2 (one scenario on disk, raw <= 3e9, free disk >= member + 5e9, raw deleted after both cache files are re-read)"},
        "estimated_runtime": json.load(open(os.path.join(ROOT, a.runtime))) if a.runtime else None,
        "analysis": ["python runners/e5_analyze.py test --run_dir runs/<date>-E5v3   (frozen v2 analysis -> e5_test.json)",
                     "python runners/v3_analyze.py test --run_dir runs/<date>-E5v3   (v3 -> e5_v3.json: criteria_v3 per AP definition, D-64 verdict, tables)"],
        "outcome": {"success": "only if the v2 rule passes under both AP definitions (D-64); headline in global-ranking AP",
                    "disagreement": "report 'AP-definition-dependent'",
                    "failure": "report as the result; no rescue analysis presented as confirmatory",
                    "no_rule_changes": "no change to any method, attack, level, threshold, metric or criterion after this file is committed"},
        "development_check_v3_H": dev,
        "scope_limits": "D-54 and D-63 (single attacker; random placement for the E4 families; spoof_blind bypass; ray-consistent / low-ray spoofs; B-RAY cannot restore removed objects; receiver sensor trusted; CARLA LiDAR; method chosen on exposed H), plus: PGD is white-box on this checkpoint with budgets relative to its clean H feature scale; B-NORM's threshold is fitted on clean H",
        "labelling": v2["labelling"], "no_changes": v2["no_changes"],
        "dry_run_v3": json.load(open(os.path.join(ROOT, a.dryrun, "dryrun_v3.json"))) if a.dryrun else "pending",
    }
    json.dump(pr, open(os.path.join(ROOT, OUT), "w"), indent=1, default=str)
    print("written", OUT, "test levels", levels)


if __name__ == "__main__":
    main()
