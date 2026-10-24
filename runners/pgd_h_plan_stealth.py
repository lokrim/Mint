"""Write runs/<run>/plan_stealth.json (D-68 as amended) BEFORE any stealth PGD run on block H.

  python runners/pgd_h_plan_stealth.py --run_dir runs/20261024-PGD
"""
import argparse
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = ("src/mint/attacks/pgd_stealth.py", "src/mint/attacks/pgd_v3.py", "src/mint/reliability/bnorm.py",
        "runners/v3_common.py", "runners/pgd_h_run.py", "runners/v3_analyze.py", "runners/pgd_h_plan_stealth.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    a = ap.parse_args()
    rd = os.path.join(ROOT, a.run_dir)
    base = json.load(open(os.path.join(rd, "plan.json")))
    sig, tau = base["feature_scale_clean_H"]["sigma_k"], base["B-NORM"]["tau_k"]
    levels = [0.25, 0.5, 1.0]
    plan = {
        "id": "v3-PGD-stealth-H", "date": "2026-10-24",
        "label": "DEVELOPMENT, block H (exposed, D-53); attack design on exposed H, POST HOC (D-68 as amended); "
                 "committed before any stealth run on block H",
        "decisions": ["D-67", "D-68 + amendment", "D-69 (decision_log_proposed_appendix.md)"],
        "families": ["pgd_untargeted_stealth", "pgd_remove_stealth"],
        "levels_r": levels, "sigma_k": sig, "tau_k": tau,
        "eps_k_by_r": {str(r): [r * s for s in sig] for r in levels},
        "unchanged_from_D-65": "objectives (pgd_untargeted_stealth uses pgd_untargeted's, pgd_remove_stealth uses "
                               "pgd_remove's), 10 steps, step eps_k / 4, random start U(-eps_k, eps_k), sign-gradient "
                               "ascent, final iterate, no-GT pseudo-labels from the clean fused output",
        "stealth_projection": {
            "when": "after the random start and after every PGD step, per scale k",
            "box": "lo = max(-eps_k, -f_k), hi = eps_k (f + delta >= 0 everywhere)",
            "constraint": "mean(f_k + delta_k) <= 0.95 * tau_k * mean|f_receiver,k|",
            "bound_ratio_0.95tau_k": [0.95 * t for t in tau],
            "projection": "exact Euclidean projection onto box and constraint: delta_k <- clip(delta_k - lambda_k, lo, hi); "
                          "lambda_k = 0 if the constraint holds, else the smallest lambda_k >= 0 satisfying it, "
                          "bisection on [0, max(delta_k - lo)] to tolerance 1e-7 x bracket; sums in float64",
            "asserted_every_attacked_frame_and_scale": "f + delta >= 0, |delta| <= eps_k (1 + 1e-6), "
                                                       "ratio_k <= 0.95 tau_k (1 + 1e-6)",
            "unit_test": "tests/test_v3.py::test_stealth_projection_equals_qp (scipy SLSQP, 12 random cases)",
            "seed": "numpy default_rng(sha256('V3PGDS|family|r|scenario|frame')[:8], little endian)"},
        "selection_rule_for_test": "unchanged: per family, the smallest r with all-frame global-ranking AP@0.7 attack "
                                   "loss >= 0.02 on block H; if none, 'too weak under stealth' and r = 1.0 on test",
        "stop": "stealth attack loss < 0.005 at r = 1.0 (global AP) for a family -> 'stealth PGD ineffective on this "
                "model', stop and ask before v3; any frozen method file would need to change",
        "expected_outcomes_stated_before_run": {"B-NORM": "catch rate <= 5% (about the clean false-flag rate, 1.6%)",
                                                "B-RAY": "recovery approximately 0",
                                                "R1": "recovery on pgd_remove_stealth > 0"},
        "run": {"methods": ["no defense", "ego-only", "B-NORM", "B-RAY", "R1", "R1-noREMOVE"],
                "conditions": "clean, 5 E4 families, D-67 option-1 families at r = 0.25, stealth families at every r",
                "AP": "both (D-64)", "CIs": "scenario (4) and 10-frame, 2000 resamples, seed 0",
                "also": "realized-only (pgd_remove rule for *_remove_stealth, pgd_untargeted rule for *_untargeted_stealth), "
                        "B-NORM catch rate and per-scale ratios, attack loss per r"},
        "code_sha256": {p: hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest() for p in CODE},
    }
    json.dump(plan, open(os.path.join(rd, "plan_stealth.json"), "w"), indent=1)
    print(json.dumps(plan["stealth_projection"], indent=1))


if __name__ == "__main__":
    main()
