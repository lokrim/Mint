#!/usr/bin/env python3
"""Generate every result number used in the paper from the frozen MINT outputs.

Reads (read-only):
  runs/20261024-E5v3/e5_v3.json, e5_test.json            final test (one-time)
  runs/20261024-E5v3/report/tables/*.csv                  report tables (copied from e5_v3/e5_test)
  runs/20261024-E5/preregistration_v3_2.json              governing pre-registration (B-NORM tau, PGD eps)
  runs/20261024-E5/dev/e5a_dev.json, H/e5a_H.json         development blocks T and H (metadata only)
  runs/20261024-AUDIT/X0_global_sort_bootstrap.json       development T/H under both AP definitions
  planning/e4_report.md                                   timing machine string (not stored in any JSON)
  runs/20261026-CULVER/e5_v3.json, e5_test.json, plan.json, sanity_first_scenario.json
                                                          Culver City (D-72; secondary, held-out domain shift;
                                                          unseen town, simulated sensor): macros prefixed Cul

Writes:
  paper/numbers.tex          \\newcommand macros (AP points = AP x 100)
  paper/tables/*.tex         tabular bodies (tab_verdict_both, tab_conditions, tab_clean_both, tab_runtime_both:
                             OPV2V test next to Culver City, never pooled; appendix tables; older tables kept)

Run from anywhere:  python3 paper/gen_numbers.py
Standard library only. Nothing is recomputed except unit conversion (x100), recovery bounds for the
oracle rows (dAP / attack loss, both read from e5_test.json), and simple sums/ratios of counts.
"""
import csv
import os
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "runs/20261024-E5v3"
TAB = RUN / "report/tables"
OUT = ROOT / "paper"
(OUT / "tables").mkdir(parents=True, exist_ok=True)

V3 = json.load(open(RUN / "e5_v3.json"))
TEST = json.load(open(RUN / "e5_test.json"))
PREREG = json.load(open(ROOT / "runs/20261024-E5/preregistration_v3_2.json"))
DEV_T = json.load(open(ROOT / "runs/20261024-E5/dev/e5a_dev.json"))
DEV_H = json.load(open(ROOT / "runs/20261024-E5/H/e5a_H.json"))
X0 = json.load(open(ROOT / "runs/20261024-AUDIT/X0_global_sort_bootstrap.json"))
E4MD = (ROOT / "planning/e4_report.md").read_text()


def rcsv(name):
    with open(TAB / name) as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- naming
CONDS = ["clean", "spoof_feat", "remove_feat", "shift_feat", "spoof_pts", "spoof_blind",
         "pgd_untargeted@r0.25", "pgd_remove@r0.25", "pgd_untargeted_stealth@r0.5",
         "pgd_remove_stealth@r0.25", "pgd_untargeted_stealth@r1.0", "pgd_remove_stealth@r1.0"]
assert CONDS == V3["conditions"], V3["conditions"]
CTAG = {"clean": "Clean", "spoof_feat": "SpoofFeat", "remove_feat": "RemoveFeat", "shift_feat": "ShiftFeat",
        "spoof_pts": "SpoofPts", "spoof_blind": "SpoofBlind", "pgd_untargeted@r0.25": "PgdUnt",
        "pgd_remove@r0.25": "PgdRem", "pgd_untargeted_stealth@r0.5": "PgdUntSt",
        "pgd_remove_stealth@r0.25": "PgdRemSt", "pgd_untargeted_stealth@r1.0": "PgdUntStStrong",
        "pgd_remove_stealth@r1.0": "PgdRemStStrong"}
CNAME = {"clean": "clean (no attack)", "spoof_feat": "spoof (feature)", "remove_feat": "remove (feature)",
         "shift_feat": "shift (feature)", "spoof_pts": "spoof (points)", "spoof_blind": "spoof, receiver-blind",
         "pgd_untargeted@r0.25": "PGD untargeted, $r{=}0.25$", "pgd_remove@r0.25": "PGD remove, $r{=}0.25$",
         "pgd_untargeted_stealth@r0.5": "stealth PGD untarg., $r{=}0.5$",
         "pgd_remove_stealth@r0.25": "stealth PGD remove, $r{=}0.25$",
         "pgd_untargeted_stealth@r1.0": "stealth PGD untarg., $r{=}1.0^\\dagger$",
         "pgd_remove_stealth@r1.0": "stealth PGD remove, $r{=}1.0^\\dagger$"}
METHODS = ["B-RAY", "R1", "R1_noREMOVE", "B-NORM", "ego_only"]
MTAG = {"B-RAY": "BRAY", "R1": "MINT", "R1_noREMOVE": "MINTNoRem", "B-NORM": "BNORM", "ego_only": "Ego"}
MNAME = {"B-RAY": "B-RAY", "R1": "MINT", "R1_noREMOVE": "MINT-noREM", "B-NORM": "B-NORM", "ego_only": "Ego-only"}
DTAG = {"global": "Glob", "frame": "Frame"}

macros = []


def M(name, val, comment=None):
    assert re.fullmatch(r"[A-Za-z]+", name), name
    macros.append((name, str(val), comment))


def sgn(x, nd=2):
    """Signed number for LaTeX; minus as a math minus."""
    s = f"{x:+.{nd}f}"
    return s.replace("-", "$-$")


def pts(x, nd=2):          # AP fraction -> signed AP points
    return sgn(100.0 * x, nd)


def ci(lo, hi, scale=100.0, nd=2):
    return f"[{sgn(scale * lo, nd)}, {sgn(scale * hi, nd)}]"


def pct(x, nd=1):
    return f"{100.0 * x:.{nd}f}\\%".replace("-", "$-$")


def plain(x, nd=2):
    return f"{x:.{nd}f}".replace("-", "$-$")


# ---------------------------------------------------------------- data set and splits
M("TestScenarios", V3["scenarios"])
M("TestFrames", f"{V3['frames']:,}".replace(",", "{,}"))
M("TestFramesRaw", V3["frames"])
hist = V3["n_agents_hist"]
M("TestNOne", hist["1"]); M("TestNTwo", hist["2"]); M("TestNThree", hist["3"])
M("TestNFourPlus", hist["4"] + hist["5"])
M("TestNmin", min(int(k) for k in hist)); M("TestNmax", max(int(k) for k in hist))
M("DevTScenarios", len(DEV_T["scenarios"])); M("DevTFrames", DEV_T["frames"])
M("DevHScenarios", len(DEV_H["scenarios"])); M("DevHFrames", DEV_H["frames"])
tn = sorted(int(k) for k in DEV_T["n_agents_hist"]); hn = sorted(int(k) for k in DEV_H["n_agents_hist"])
M("DevTNmin", tn[0]); M("DevTNmax", tn[-1]); M("DevHN", hn[0])
assert hn[0] == hn[-1]
M("NumConditions", len(CONDS))
M("BootB", 2000)
M("NumpyOpencoodDiff", f"{TEST['numpy_ap_vs_opencood_max_abs_diff']:.1e}".replace("e-", "\\times 10^{-") + "}")

with open(OUT / "tables/tab_splits.tex", "w") as f:
    f.write("% generated by gen_numbers.py -- do not edit\n")
    f.write("Set & Scen. & Frames & $n$ & Role \\\\\n\\midrule\n")
    f.write(f"Design & {len(DEV_T['scenarios'])} & {DEV_T['frames']} & {tn[0]}--{tn[-1]} & "
            "development; MINT designed here \\\\\n")
    f.write(f"Validation & {len(DEV_H['scenarios'])} & {DEV_H['frames']} & {hn[0]} & "
            "held out to check the frozen MINT; B-RAY chosen here \\\\\n")
    f.write(f"Test & {V3['scenarios']} & {V3['frames']} & {min(int(k) for k in hist)}--{max(int(k) for k in hist)} & "
            "primary, one-time; only clean detector outputs seen before \\\\\n")

# ---------------------------------------------------------------- per-condition deltas (Table III)
per = {}
for row in rcsv("02_per_family.csv") + rcsv("02b_per_family_pgd.csv"):
    per[(row["ap_definition"], row["condition"], row["method"])] = row
# Ego-only is not in the report CSVs: take it from e5_v3.json tables (same source the CSVs were built from),
# after checking that the CSV rows equal the JSON for every method that is in both.
for d in ("global", "frame"):
    for c in CONDS:
        for m in METHODS:
            t = V3["tables"][d]["per_family"][c][m]
            if (d, c, m) in per:
                r = per[(d, c, m)]
                assert abs(float(r["point"]) - t["point"]) < 1e-9 and \
                    [float(r["ci95_scenario_lo"]), float(r["ci95_scenario_hi"])] == t["ci95_scenario"], (d, c, m)
            else:
                per[(d, c, m)] = {"point": t["point"], "ci95_scenario_lo": t["ci95_scenario"][0],
                                  "ci95_scenario_hi": t["ci95_scenario"][1]}
for d in ("global", "frame"):
    for c in CONDS:
        for m in METHODS:
            r = per[(d, c, m)]
            p, lo, hi = float(r["point"]), float(r["ci95_scenario_lo"]), float(r["ci95_scenario_hi"])
            base = f"d{DTAG[d]}{CTAG[c]}{MTAG[m]}"
            M(base, pts(p)); M("ci" + base[1:], ci(lo, hi))
# unsigned copy for running text ("restores 22.50 of 40.41 points")
_r = float(per[("global", "pgd_remove_stealth@r1.0", "R1")]["point"])
assert _r > 0
M("RestoredGlobPgdRemStStrongMINT", plain(100.0 * _r))


def main_table(d):
    lines = ["% generated by gen_numbers.py -- do not edit",
             "Condition & " + " & ".join(MNAME[m] for m in METHODS) + " \\\\", "\\midrule"]
    for c in CONDS:
        if c == "pgd_untargeted@r0.25":
            lines.append("\\midrule")
        cells = []
        for m in METHODS:
            r = per[(d, c, m)]
            p, lo, hi = float(r["point"]), float(r["ci95_scenario_lo"]), float(r["ci95_scenario_hi"])
            cell = f"{pts(p)} {{\\tiny {ci(lo, hi)}}}"
            if lo > 0:
                cell = f"\\textbf{{{pts(p)}}} {{\\tiny {ci(lo, hi)}}}"
            elif hi < 0:
                cell = f"\\textit{{{pts(p)}}} {{\\tiny {ci(lo, hi)}}}"
            cells.append(cell)
        lines.append(f"{CNAME[c]} & " + " & ".join(cells) + " \\\\")
    return "\n".join(lines) + "\n"


for d, fn in (("global", "tab_main_global.tex"), ("frame", "tab_main_frame.tex")):
    (OUT / "tables" / fn).write_text(main_table(d))

# ---------------------------------------------------------------- headline mean of 4 original attacks
for row in rcsv("01_headline.csv"):
    d, m = row["ap_definition"], row["method"]
    if m not in MTAG:
        continue
    base = f"Head{DTAG[d]}{MTAG[m]}"
    M(base, pts(float(row["point"])))
    M(base + "CI", ci(float(row["ci95_scenario_lo"]), float(row["ci95_scenario_hi"])))
    M(base + "CIblock", ci(float(row["ci95_block10_lo"]), float(row["ci95_block10_hi"])))

# ---------------------------------------------------------------- pre-registered verdict (Table IV)
crit = V3["criteria_v3"]
for d in ("global", "frame"):
    cd = crit[d]
    D = DTAG[d]
    for m in ("B-RAY", "R1"):
        t = cd["co_test_vs_no_defense"][m]
        b = f"V{D}{MTAG[m]}"
        M(b + "Delta", pts(t["point"]))
        M(b + "CI", ci(*t["ci95_scenario"]))
        M(b + "CIblock", ci(*t["ci95_block10"]))
        M(b + "P", f"{t['p_one_sided']:.4f}")
        M(b + "HolmRank", t["holm"]["rank"])
        M(b + "HolmThr", f"{t['holm']['threshold']:.3f}")
        M(b + "Reject", "yes" if t["holm"]["reject"] else "no")
        M(b + "K", t["k_le_0"])
    cl = cd["clean_rel_loss"]["B-RAY"]
    M(f"V{D}BRAYCleanLoss", pct(cl["point"], 2))
    M(f"V{D}BRAYCleanCI", f"[{sgn(100 * cl['ci95_scenario'][0])}, {sgn(100 * cl['ci95_scenario'][1])}]\\%")
    M(f"V{D}CleanOK", "yes" if cd["B-RAY_clean_ci_hi_le_0.01"] else "no")
    M(f"V{D}Pass", "passes" if cd["pass"] else "fails")
    rb = cd["R1_minus_BRAY"]
    M(f"V{D}RmB", pts(rb["point"])); M(f"V{D}RmBCI", ci(*rb["ci95_scenario"]))
    M(f"V{D}RmBCIblock", ci(*rb["ci95_block10"]))
    M(f"V{D}RmBStatement", rb["statement"])
M("BothPass", "yes" if (crit["global"]["pass"] and crit["frame"]["pass"]) else "no")
assert crit["global"]["pass"] and crit["frame"]["pass"]

with open(OUT / "tables/tab_verdict.tex", "w") as f:
    g, fr = crit["global"], crit["frame"]
    f.write("% generated by gen_numbers.py -- do not edit\n")
    f.write("Statistic & Global-ranking AP & Frame-order AP \\\\\n\\midrule\n")
    f.write("\\multicolumn{3}{l}{\\emph{Primary: B-RAY vs.\\ no defense (mean of 4 original attacks)}}\\\\\n")
    for lab, key in (("$\\Delta$AP@0.7 (pts)", "point"),):
        f.write(f"$\\Delta$AP@0.7 (pts) & {pts(g['co_test_vs_no_defense']['B-RAY']['point'])} & "
                f"{pts(fr['co_test_vs_no_defense']['B-RAY']['point'])} \\\\\n")
    f.write(f"95\\% CI, scenario & {ci(*g['co_test_vs_no_defense']['B-RAY']['ci95_scenario'])} & "
            f"{ci(*fr['co_test_vs_no_defense']['B-RAY']['ci95_scenario'])} \\\\\n")
    f.write(f"one-sided $p$ (Holm thr.) & {g['co_test_vs_no_defense']['B-RAY']['p_one_sided']:.4f} "
            f"({g['co_test_vs_no_defense']['B-RAY']['holm']['threshold']:.3f}) & "
            f"{fr['co_test_vs_no_defense']['B-RAY']['p_one_sided']:.4f} "
            f"({fr['co_test_vs_no_defense']['B-RAY']['holm']['threshold']:.3f}) \\\\\n")
    f.write(f"Holm reject & {'yes' if g['co_test_vs_no_defense']['B-RAY']['holm']['reject'] else 'no'} & "
            f"{'yes' if fr['co_test_vs_no_defense']['B-RAY']['holm']['reject'] else 'no'} \\\\\n")
    f.write(f"Clean rel.\\ loss CI (\\%) & "
            f"[{sgn(100 * g['clean_rel_loss']['B-RAY']['ci95_scenario'][0])}, {sgn(100 * g['clean_rel_loss']['B-RAY']['ci95_scenario'][1])}] & "
            f"[{sgn(100 * fr['clean_rel_loss']['B-RAY']['ci95_scenario'][0])}, {sgn(100 * fr['clean_rel_loss']['B-RAY']['ci95_scenario'][1])}] \\\\\n")
    f.write(f"CI high $\\le 1\\%$ & {'yes' if g['B-RAY_clean_ci_hi_le_0.01'] else 'no'} & "
            f"{'yes' if fr['B-RAY_clean_ci_hi_le_0.01'] else 'no'} \\\\\n")
    f.write(f"\\textbf{{success rule}} & \\textbf{{{'pass' if g['pass'] else 'fail'}}} & "
            f"\\textbf{{{'pass' if fr['pass'] else 'fail'}}} \\\\\n\\midrule\n")
    f.write("\\multicolumn{3}{l}{\\emph{Co-test: MINT vs.\\ no defense}}\\\\\n")
    f.write(f"$\\Delta$AP@0.7 (pts) & {pts(g['co_test_vs_no_defense']['R1']['point'])} & "
            f"{pts(fr['co_test_vs_no_defense']['R1']['point'])} \\\\\n")
    f.write(f"95\\% CI, scenario & {ci(*g['co_test_vs_no_defense']['R1']['ci95_scenario'])} & "
            f"{ci(*fr['co_test_vs_no_defense']['R1']['ci95_scenario'])} \\\\\n")
    f.write(f"one-sided $p$ (Holm thr.) & {g['co_test_vs_no_defense']['R1']['p_one_sided']:.4f} "
            f"({g['co_test_vs_no_defense']['R1']['holm']['threshold']:.3f}) & "
            f"{fr['co_test_vs_no_defense']['R1']['p_one_sided']:.4f} "
            f"({fr['co_test_vs_no_defense']['R1']['holm']['threshold']:.3f}) \\\\\n")
    f.write(f"Holm reject & {'yes' if g['co_test_vs_no_defense']['R1']['holm']['reject'] else 'no'} & "
            f"{'yes' if fr['co_test_vs_no_defense']['R1']['holm']['reject'] else 'no'} \\\\\n\\midrule\n")
    f.write("\\multicolumn{3}{l}{\\emph{Key secondary: MINT $-$ B-RAY (paired)}}\\\\\n")
    f.write(f"$\\Delta$AP@0.7 (pts) & {pts(g['R1_minus_BRAY']['point'])} & {pts(fr['R1_minus_BRAY']['point'])} \\\\\n")
    f.write(f"95\\% CI, scenario & {ci(*g['R1_minus_BRAY']['ci95_scenario'])} & {ci(*fr['R1_minus_BRAY']['ci95_scenario'])} \\\\\n")
    f.write(f"Statement & MINT better & MINT worse \\\\\n")
assert crit["global"]["R1_minus_BRAY"]["statement"].startswith("the counterfactual improves")
assert crit["frame"]["R1_minus_BRAY"]["statement"].startswith("the counterfactual performs worse")

# ---------------------------------------------------------------- clean cost (Table V)
cc = {(r["ap_definition"], r["method"]): r for r in rcsv("03_clean_cost.csv")}
for (d, m), r in cc.items():
    if m in MTAG:
        b = f"Clean{DTAG[d]}{MTAG[m]}"
        M(b, pct(float(r["point"]), 2))
        M(b + "CI", f"[{sgn(100 * float(r['ci95_scenario_lo']))}, {sgn(100 * float(r['ci95_scenario_hi']))}]\\%")
units = TEST["units"]
u, un = units["R1|clean"], units["R1_noREMOVE|clean"]
M("MintCleanUnits", u["units"]); M("MintCleanKnown", pct(u["frac_KNOWN"], 0))
M("MintCleanGated", u["gated"]); M("MintCleanGatedHarmful", u["gated_harmful"])
M("MintCleanFalseSwitch", u["false_rejections_useful"]); M("MintCleanFalseSwitchRemove", u["false_rej_by_REMOVE"])
M("MintCleanGatedRemove", u["gated_by_REMOVE"]); M("MintCleanPrecision", plain(u["precision"]))
M("MintNoRemCleanGated", un["gated"]); M("MintNoRemCleanFalseSwitch", un["false_rejections_useful"])
M("MintNoRemCleanPrecision", plain(un["precision"]))
bb = V3["B-RAY_boxes"]["clean"]
M("BrayCleanBoxes", f"{bb['boxes']:,}".replace(",", "{,}")); M("BrayCleanDrop", bb["drop"])
M("BrayCleanDropGT", bb["dropped_gt_matched"]); M("BrayCleanKnown", pct(bb["frac_KNOWN"], 0))
bn = V3["B-NORM_flags"]["clean"]
M("BnormFalseFlag", pct(bn["catch_rate"], 1)); M("BnormFalseFlagN", bn["sender1_flagged"])
M("BnormFramesWithSender", bn["frames_n2"])
M("BnormFalseFlagH", pct(PREREG["B-NORM"]["clean_H_flag_rate"], 1))
M("BnormTauOne", plain(PREREG["B-NORM"]["tau_k"][0], 3)); M("BnormTauThree", plain(PREREG["B-NORM"]["tau_k"][2], 3))

with open(OUT / "tables/tab_clean.tex", "w") as f:
    f.write("% generated by gen_numbers.py -- do not edit\n")
    f.write("Method & Rel.\\ loss, global & Rel.\\ loss, frame-order \\\\\n\\midrule\n")
    for m in METHODS:
        rg, rf = cc[("global", m)], cc[("frame", m)]
        f.write(f"{MNAME[m]} & {sgn(100 * float(rg['point']))}\\% {{\\tiny [{sgn(100 * float(rg['ci95_scenario_lo']))}, {sgn(100 * float(rg['ci95_scenario_hi']))}]}} & "
                f"{sgn(100 * float(rf['point']))}\\% {{\\tiny [{sgn(100 * float(rf['ci95_scenario_lo']))}, {sgn(100 * float(rf['ci95_scenario_hi']))}]}} \\\\\n")
    f.write("\\midrule\n\\multicolumn{3}{l}{\\emph{What each defense removes on clean frames}}\\\\\n")
    f.write(f"B-RAY & \\multicolumn{{2}}{{l}}{{{bb['drop']} of {bb['boxes']:,} boxes dropped; {bb['dropped_gt_matched']} matched a real car}} \\\\\n")
    f.write(f"MINT & \\multicolumn{{2}}{{l}}{{{u['gated']} of {u['units']:,} units gated; {u['false_rejections_useful']} USEFUL ({u['false_rej_by_REMOVE']} via REMOVE)}} \\\\\n")
    f.write(f"MINT-noREM & \\multicolumn{{2}}{{l}}{{{un['gated']} units gated; {un['false_rejections_useful']} USEFUL}} \\\\\n")
    f.write(f"B-NORM & \\multicolumn{{2}}{{l}}{{attacker flagged in {bn['sender1_flagged']}/{bn['frames_n2']} sender-frames ({100 * bn['catch_rate']:.1f}\\%)}} \\\\\n")

# ---------------------------------------------------------------- R1 - B-RAY per condition
rmb = {(r["ap_definition"], r["statistic"]): r for r in rcsv("04_r1_minus_bray.csv") + rcsv("04b_r1_minus_bray_pgd.csv")}
for (d, s), r in rmb.items():
    if s.startswith("paired|R1-B-RAY|"):
        c = s.split("|")[2]
        b = f"RmB{DTAG[d]}{CTAG[c]}"
        M(b, pts(float(r["point"]))); M(b + "CI", ci(float(r["ci95_scenario_lo"]), float(r["ci95_scenario_hi"])))
    if s == "paired_mean_3|R1-B-RAY":
        M(f"RmB{DTAG[d]}MeanThree", pts(float(r["point"])))
        M(f"RmB{DTAG[d]}MeanThreeCI", ci(float(r["ci95_scenario_lo"]), float(r["ci95_scenario_hi"])))

# ---------------------------------------------------------------- attack loss, realization, recovery (Table II)
for d in ("global", "frame"):
    for c in CONDS[1:]:
        M(f"Loss{DTAG[d]}{CTAG[c]}", plain(100 * V3["point"][d][f"attack_loss|{c}"]))
real = V3["realization"]
pgdtot = {c: V3["pgd_by_scenario"][c]["total"] for c in V3["pgd_by_scenario"]}
for c in CONDS[1:]:
    r = real[c]
    M(f"Applied{CTAG[c]}", r["applied"]); M(f"Realized{CTAG[c]}", r["realized"])
    M(f"WithSender{CTAG[c]}", r["frames_with_sender"])
    if c in pgdtot:
        M(f"Infeasible{CTAG[c]}", pgdtot[c]["infeasible"])
sb = real["spoof_blind"]
M("BlindRealizedLowRay", sb["realized_dst_rays_lt3_or_self"]); M("BlindRealizedKnownHit", sb["realized_hit_unit_KNOWN"])

ATK = {"spoof_feat": ("copy", "3.2\\,m feature patch to empty cell"),
       "remove_feat": ("copy", "background over a car's patch"),
       "shift_feat": ("copy", "remove + paste one cell away"),
       "spoof_pts": ("points", "car points copied, re-encoded"),
       "spoof_blind": ("copy", "as spoof, receiver $<3$ rays"),
       "pgd_untargeted@r0.25": ("PGD", "$L_\\infty$, $\\epsilon_k{=}0.25\\sigma_k$"),
       "pgd_remove@r0.25": ("PGD", "$L_\\infty$, $\\epsilon_k{=}0.25\\sigma_k$"),
       "pgd_untargeted_stealth@r0.5": ("stealth", "$+$ B-NORM bound, $0.5\\sigma_k$"),
       "pgd_remove_stealth@r0.25": ("stealth", "$+$ B-NORM bound, $0.25\\sigma_k$"),
       "pgd_untargeted_stealth@r1.0": ("stealth", "$+$ B-NORM bound, $1.0\\sigma_k$"),
       "pgd_remove_stealth@r1.0": ("stealth", "$+$ B-NORM bound, $1.0\\sigma_k$")}
with open(OUT / "tables/tab_attacks.tex", "w") as f:
    f.write("% generated by gen_numbers.py -- do not edit\n")
    f.write("Condition & Mechanism & Appl. & Real. & Loss G & Loss F \\\\\n\\midrule\n")
    for c in CONDS[1:]:
        r = real[c]
        if c == "pgd_untargeted@r0.25":
            f.write("\\midrule\n")
        f.write(f"{CNAME[c]} & {ATK[c][1]} & {r['applied']} & {r['realized']} & "
                f"{100 * V3['point']['global'][f'attack_loss|{c}']:.2f} & {100 * V3['point']['frame'][f'attack_loss|{c}']:.2f} \\\\\n")

rec = {(r["ap_definition"], r["condition"], r["method"]): r for r in rcsv("05_pgd_recovery.csv")}
for (d, c, m), r in rec.items():
    if m in MTAG and r["recovery"] not in ("", "None"):
        M(f"Rec{DTAG[d]}{CTAG[c]}{MTAG[m]}", plain(float(r["recovery"])))

# expected outcomes (descriptive)
exp = V3["expected_outcomes"]
M("RecGlobPgdRemStStrongMINTexp", plain(exp["pgd_remove_stealth@r1.0"]["global"]["R1"]))

# ---------------------------------------------------------------- B-NORM catch rates
for c in CONDS:
    M(f"Catch{CTAG[c]}", pct(V3["B-NORM_flags"][c]["catch_rate"], 0 if c.startswith("pgd") else 1))

# ---------------------------------------------------------------- B-RAY drops under attack
for c in CONDS:
    b = V3["B-RAY_boxes"][c]
    M(f"BrayDrop{CTAG[c]}", b["drop"]); M(f"BrayDropUnmatched{CTAG[c]}", b["dropped_unmatched"])

# ---------------------------------------------------------------- R1 units under attacks (E4 families)
for c in ("spoof_feat", "remove_feat", "shift_feat", "spoof_pts", "spoof_blind"):
    uu = units[f"R1|{c}"]
    M(f"MintUnitsKnown{CTAG[c]}", pct(uu["frac_KNOWN"], 0)); M(f"MintUnitsPrec{CTAG[c]}", plain(uu["precision"]))

# ---------------------------------------------------------------- oracle bounds (frame-order, frozen v2)
ap = TEST["AP"]
for c in ("spoof_feat", "remove_feat", "shift_feat", "spoof_pts", "spoof_blind"):
    loss = V3["point"]["frame"][f"attack_loss|{c}"]
    o, vo = ap[c]["oracle_attacker"]["dAP@0.7"], ap[c]["vis_oracle_attacker"]["dAP@0.7"]
    M(f"Oracle{CTAG[c]}", pts(o)); M(f"VisOracle{CTAG[c]}", pts(vo))
    M(f"OracleRec{CTAG[c]}", plain(o / loss)); M(f"VisOracleRec{CTAG[c]}", plain(vo / loss))

# ---------------------------------------------------------------- absolute AP (clean, no defense)
M("APCleanGlob", plain(100 * V3["AP"]["global"]["clean"]["undefended"]["AP@0.7"], 2))
M("APCleanFrame", plain(100 * V3["AP"]["frame"]["clean"]["undefended"]["AP@0.7"], 2))
M("APStrongRemGlobNoDef", plain(100 * V3["AP"]["global"]["pgd_remove_stealth@r1.0"]["undefended"]["AP@0.7"], 2))
M("APStrongRemGlobMINT", plain(100 * V3["AP"]["global"]["pgd_remove_stealth@r1.0"]["R1"]["AP@0.7"], 2))
M("APGlobEgo", plain(100 * V3["AP"]["global"]["clean"]["ego_only"]["AP@0.7"], 2))

# ---------------------------------------------------------------- by number of agents (frame-order, frozen v2)
for r in rcsv("10_by_agents.csv"):
    n = {"2": "Two", "3": "Three", "4+": "FourPlus"}[r["n_agents"]]
    if r["method"] in MTAG:
        M(f"ByN{n}{MTAG[r['method']]}", pts(float(r["point"])))
        M(f"ByN{n}{MTAG[r['method']]}CI", ci(float(r["ci95_block10_lo"]), float(r["ci95_block10_hi"])))
    if r["method"] == "B-RAY":
        M(f"ByN{n}Scen", r["scenarios"]); M(f"ByN{n}Frames", r["frames"])

# ---------------------------------------------------------------- runtime (Table VI)
ov = TEST["overhead"]
m_ = re.search(r"Apple M1, 8 threads", E4MD)
assert m_, "timing machine string not found in e4_report.md"
M("TimingMachine", "Apple M1 CPU, 8 threads")
M("EncodeIsolatedP", plain(ov["encode_isolated_p50_s"], 3))
with open(OUT / "tables/tab_runtime.tex", "w") as f:
    f.write("% generated by gen_numbers.py -- do not edit\n")
    f.write("$n$ & Frames & Base (s) & MINT full & MINT triggered & B-RAY \\\\\n\\midrule\n")
    for k in ("1", "2", "3", "4+"):
        s = ov["by_stratum"][k]
        base = next(iter(v for kk, v in s.items() if kk != "frames"))["baseline_s"]["p50"]

        def cell(mode):
            if mode not in s:
                return "--"
            o = s[mode]["overhead"]
            return f"{100 * o['p50']:.0f} / {100 * o['p95']:.0f}"
        f.write(f"{k} & {s['frames']} & {base:.2f} & {cell('dense')} & {cell('trigger_0.05')} & {cell('B-RAY')} \\\\\n")
        tag = {"1": "One", "2": "Two", "3": "Three", "4+": "FourPlus"}[k]
        for mode, mt in (("dense", "Dense"), ("trigger_0.05", "Trig"), ("B-RAY", "Bray")):
            if mode in s:
                M(f"Ov{mt}{tag}Pfifty", f"{100 * s[mode]['overhead']['p50']:.0f}\\%")
                M(f"Ov{mt}{tag}Pninetyfive", f"{100 * s[mode]['overhead']['p95']:.0f}\\%")
                M(f"Ov{mt}{tag}Extra", plain(s[mode]["extra_s"]["p50"], 3))
                M(f"Ov{mt}{tag}Iso", f"{100 * s[mode]['overhead_isolated_encode']['p50']:.0f}\\%")
        M(f"OvBase{tag}", plain(base, 2))

# ---------------------------------------------------------------- development vs test (Table VII)
def dev_row(block, defn):
    blk = X0[block]["nonglobal_frozen" if defn == "frame" else "global_sort"]
    p, sc = blk["point"], blk["scenario"]
    return [(p[k], sc[k]["ci95"]) for k in ("B-RAY", "R1", "R1-B-RAY")]


def test_row(defn):
    cd = crit[defn]
    return [(cd["co_test_vs_no_defense"]["B-RAY"]["point"], cd["co_test_vs_no_defense"]["B-RAY"]["ci95_scenario"]),
            (cd["co_test_vs_no_defense"]["R1"]["point"], cd["co_test_vs_no_defense"]["R1"]["ci95_scenario"]),
            (cd["R1_minus_BRAY"]["point"], cd["R1_minus_BRAY"]["ci95_scenario"])]


with open(OUT / "tables/tab_dev_vs_test.tex", "w") as f:
    f.write("% generated by gen_numbers.py -- do not edit\n")
    f.write("Set (AP) & B-RAY & MINT & MINT $-$ B-RAY \\\\\n\\midrule\n")
    rows = [("Design (G)", dev_row("T", "global")), ("Design (F)", dev_row("T", "frame")),
            ("Validation (G)", dev_row("H", "global")), ("Validation (F)", dev_row("H", "frame")),
            ("\\textbf{Test} (G)", test_row("global")), ("\\textbf{Test} (F)", test_row("frame"))]
    for i, (lab, vals) in enumerate(rows):
        if i == 4:
            f.write("\\midrule\n")
        f.write(lab + " & " + " & ".join(f"{pts(p)} {{\\tiny {ci(*c)}}}" for p, c in vals) + " \\\\\n")
for block in ("T", "H"):
    for defn, D in (("global", "Glob"), ("frame", "Frame")):
        vals = dev_row(block, defn)
        for (p, c), k in zip(vals, ("BRAY", "MINT", "RmB")):
            M(f"Dev{block}{D}{k}", pts(p)); M(f"Dev{block}{D}{k}CI", ci(*c))

# ---------------------------------------------------------------- Culver City (D-72; secondary, held-out domain shift)
# Unseen town, simulated sensor. Separate evaluation of the same frozen code; never pooled with the test. Prefix Cul.
CUL_RUN = ROOT / os.environ.get("MINT_CULVER_RUN", "runs/20261026-CULVER")
CV3 = json.load(open(CUL_RUN / "e5_v3.json"))
CTEST = json.load(open(CUL_RUN / "e5_test.json"))
CPLAN = json.load(open(ROOT / "runs/20261026-CULVER/plan.json"))
CSAN = json.load(open(CUL_RUN / "sanity_first_scenario.json"))
if "MINT_CULVER_RUN" not in os.environ:
    assert CV3["label"].startswith("CULVER CITY") and CV3["completeness_check"]["pass"], CV3["label"]
assert CV3["conditions"] == CONDS and CV3["preregistration"] == V3["preregistration"]
ccrit = CV3["criteria_v3"]
with open(OUT / "tables/tab_splits.tex", "a") as f:
    f.write("\\midrule\n")
    f.write(f"Culver City & {CV3['scenarios']} & {CV3['frames']} & "
            f"{min(int(k) for k in CV3['n_agents_hist'])}--{max(int(k) for k in CV3['n_agents_hist'])} & "
            "secondary; unseen town, simulated sensor \\\\\n")
M("CulScenarios", CV3["scenarios"]); M("CulFrames", CV3["frames"])
chist = CV3["n_agents_hist"]
M("CulNmin", min(int(k) for k in chist)); M("CulNmax", max(int(k) for k in chist))
M("CulArchiveGB", plain(CPLAN["data"]["archive_bytes"] / 1e9, 1))
M("CulPublishedAP", plain(100 * CPLAN["checkpoint"]["published_culver_ap07"], 1))
M("CulSanityAP", plain(100 * CSAN["ap_frame_order_opencood_default"]["AP@0.7"], 2))
M("CulSanityFrames", CSAN["frames"])
M("CulAPCleanGlob", plain(100 * CV3["AP"]["global"]["clean"]["undefended"]["AP@0.7"], 2))
M("CulAPCleanFrame", plain(100 * CV3["AP"]["frame"]["clean"]["undefended"]["AP@0.7"], 2))
for d in ("global", "frame"):
    D = DTAG[d]
    for m in METHODS:
        t = CV3["tables"][d]["mean_of_4_orig"][m]
        M(f"CulHead{D}{MTAG[m]}", pts(t["point"])); M(f"CulHead{D}{MTAG[m]}CI", ci(*t["ci95_scenario"]))
        M(f"CulHead{D}{MTAG[m]}CIblock", ci(*t["ci95_block10"]))
        cl = CV3["tables"][d]["clean_rel_loss"][m]
        M(f"CulClean{D}{MTAG[m]}", pct(cl["point"], 2))
        M(f"CulClean{D}{MTAG[m]}CI", f"[{sgn(100 * cl['ci95_scenario'][0])}, {sgn(100 * cl['ci95_scenario'][1])}]\\%")
    cd = ccrit[d]
    for m in ("B-RAY", "R1"):
        t = cd["co_test_vs_no_defense"][m]
        M(f"CulV{D}{MTAG[m]}P", f"{t['p_one_sided']:.4f}")
        M(f"CulV{D}{MTAG[m]}Reject", "yes" if t["holm"]["reject"] else "no")
    M(f"CulV{D}CleanOK", "yes" if cd["B-RAY_clean_ci_hi_le_0.01"] else "no")
    M(f"CulV{D}Pass", "passes" if cd["pass"] else "does not pass")
    rb = cd["R1_minus_BRAY"]
    M(f"CulV{D}RmB", pts(rb["point"])); M(f"CulV{D}RmBCI", ci(*rb["ci95_scenario"]))
    M(f"CulV{D}RmBCIblock", ci(*rb["ci95_block10"])); M(f"CulV{D}RmBStatement", rb["statement"])
    for c in CONDS[1:]:
        M(f"CulLoss{D}{CTAG[c]}", plain(100 * CV3["point"][d][f"attack_loss|{c}"]))
        for m in METHODS:
            M(f"CulD{D}{CTAG[c]}{MTAG[m]}", pts(CV3["point"][d][f"delta|{m}|{c}"]))
            r = CV3["point"][d].get(f"recovery|{m}|{c}")
            if r is not None:
                M(f"CulRec{D}{CTAG[c]}{MTAG[m]}", plain(r))
M("CulVerdict", ccrit["D-64"]["verdict"])
M("CulRmBDependent", "yes" if ccrit["D-64"].get("R1_minus_BRAY_AP_definition_dependent") else "no")
for c in CONDS:
    M(f"CulCatch{CTAG[c]}", pct(CV3["B-NORM_flags"][c]["catch_rate"], 0 if c.startswith("pgd") else 1))
cpg = {c: CV3["pgd_by_scenario"][c]["total"] for c in CV3["pgd_by_scenario"]}
for c in cpg:
    M(f"CulInfeasible{CTAG[c]}", cpg[c]["infeasible"])
cbb = CV3["B-RAY_boxes"]["clean"]
M("CulBrayCleanDrop", cbb["drop"]); M("CulBrayCleanDropGT", cbb["dropped_gt_matched"])
M("CulBrayCleanBoxes", f"{cbb['boxes']:,}".replace(",", "{,}"))
cov = CTEST["overhead"]["by_stratum"]
NTAG = {"1": "One", "2": "Two", "3": "Three", "4+": "FourPlus"}
for k in cov:
    for mode, mt in (("dense", "Dense"), ("trigger_0.05", "Trig"), ("B-RAY", "Bray")):
        if mode in cov[k]:
            M(f"CulOv{mt}{NTAG[k]}Pfifty", f"{100 * cov[k][mode]['overhead']['p50']:.0f}\\%")
            M(f"CulOv{mt}{NTAG[k]}Pninetyfive", f"{100 * cov[k][mode]['overhead']['p95']:.0f}\\%")
    M(f"CulOvBase{NTAG[k]}", plain(next(v for kk, v in cov[k].items() if kk != "frames")["baseline_s"]["p50"], 2))

# per-condition Delta AP with scenario CI (clean included), from CV3 tables (same source as the Culver report CSVs)
for d in ("global", "frame"):
    for c in CONDS:
        for m in METHODS:
            t = CV3["tables"][d]["per_family"][c][m]
            if c != "clean":
                assert abs(t["point"] - CV3["point"][d][f"delta|{m}|{c}"]) < 1e-9, (d, c, m)
            else:
                M(f"CulD{DTAG[d]}Clean{MTAG[m]}", pts(t["point"]))
            M(f"CulCi{DTAG[d]}{CTAG[c]}{MTAG[m]}", ci(*t["ci95_scenario"]))

# receiver-blind spoof: placement counts (Culver) and recoveries (both sets; all-frame and realized-only)
csb = CV3["realization"]["spoof_blind"]
M("CulRealizedSpoofBlind", csb["realized"]); M("CulBlindRealizedLowRay", csb["realized_dst_rays_lt3_or_self"])
M("CulBlindRealizedKnownHit", csb["realized_hit_unit_KNOWN"])
for pre, v in (("", V3), ("Cul", CV3)):
    for d in ("global", "frame"):
        for m in METHODS:
            ro = v["realized_only"]["spoof_blind"][d][m]
            M(f"{pre}RealRec{DTAG[d]}SpoofBlind{MTAG[m]}", plain(ro["recovery"]))
            if pre == "":
                M(f"Rec{DTAG[d]}SpoofBlind{MTAG[m]}", plain(v["point"][d][f"recovery|{m}|spoof_blind"]))

# R1 units on clean frames (Culver), same fields as the test macros
cu, cun = CTEST["units"]["R1|clean"], CTEST["units"]["R1_noREMOVE|clean"]
M("CulMintCleanUnits", f"{cu['units']:,}".replace(",", "{,}")); M("CulMintCleanGated", cu["gated"])
M("CulMintCleanFalseSwitch", cu["false_rejections_useful"]); M("CulMintCleanFalseSwitchRemove", cu["false_rej_by_REMOVE"])
M("CulMintCleanPrecision", plain(cu["precision"]))
M("CulMintNoRemCleanGated", cun["gated"]); M("CulMintNoRemCleanFalseSwitch", cun["false_rejections_useful"])
M("CulBnormFalseFlagN", CV3["B-NORM_flags"]["clean"]["sender1_flagged"])
M("CulBnormFramesWithSender", CV3["B-NORM_flags"]["clean"]["frames_n2"])
M("CulWithSender", CV3["realization"]["spoof_feat"]["frames_with_sender"])

# by number of agents (frame-order, frozen v2, 10-frame CIs), Culver report CSV
with open(CUL_RUN / "report/tables/10_by_agents.csv") as fh:
    for r in csv.DictReader(fh):
        n = NTAG[r["n_agents"]]
        if r["method"] in MTAG:
            M(f"CulByN{n}{MTAG[r['method']]}", pts(float(r["point"])))
            M(f"CulByN{n}{MTAG[r['method']]}CI", ci(float(r["ci95_block10_lo"]), float(r["ci95_block10_hi"])))
        if r["method"] == "B-RAY":
            M(f"CulByN{n}Scen", r["scenarios"]); M(f"CulByN{n}Frames", r["frames"])

SETS = (("Test", V3), ("Culver", CV3))


def mark(t):
    """Point estimate in AP points; bold if the scenario CI is above zero, italic if below."""
    p, (lo, hi) = pts(t["point"]), t["ci95_scenario"]
    return f"\\textbf{{{p}}}" if lo > 0 else (f"\\textit{{{p}}}" if hi < 0 else p)


# Short condition names for single-column tables (r is the PGD level; "st." = B-NORM-aware stealth PGD)
CSHORT = {"clean": "clean", "spoof_feat": "spoof (feature)", "remove_feat": "remove (feature)",
          "shift_feat": "shift (feature)", "spoof_pts": "spoof (points)", "spoof_blind": "spoof, rec.-blind",
          "pgd_untargeted@r0.25": "PGD untarg., 0.25", "pgd_remove@r0.25": "PGD remove, 0.25",
          "pgd_untargeted_stealth@r0.5": "st.\\ PGD untarg., 0.5", "pgd_remove_stealth@r0.25": "st.\\ PGD remove, 0.25",
          "pgd_untargeted_stealth@r1.0": "st.\\ PGD untarg., 1.0$^\\dagger$",
          "pgd_remove_stealth@r1.0": "st.\\ PGD remove, 1.0$^\\dagger$"}
STMT = {"the counterfactual improves over the box-level filter": "improves",
        "the counterfactual performs worse than the box-level filter": "performs worse",
        "the counterfactual's benefit over a box-level filter is not established": "not established"}
SETCOLS = [(v, d) for _, v in SETS for d in ("global", "frame")]      # Test G, Test F, Culver G, Culver F
SETHEAD = ("& \\multicolumn{2}{c}{OPV2V test (primary)} & \\multicolumn{2}{c}{Culver City (secondary)} \\\\\n"
           "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\n")


def pci(t):
    return f"{pts(t['point'])} {ci(*t['ci95_scenario'])}"


# Table (full width): pre-registered verdict on the test (confirmatory), same rule on Culver (descriptive)
with open(OUT / "tables/tab_verdict_both.tex", "w") as f:
    f.write("% generated by gen_numbers.py -- do not edit\n" + SETHEAD)
    f.write("Statistic & Global-ranking & Frame-order & Global-ranking & Frame-order \\\\\n\\midrule\n")

    def row(label, fn):
        f.write(label + " & " + " & ".join(fn(v["criteria_v3"][d]) for v, d in SETCOLS) + " \\\\\n")

    def co(m):
        return lambda c: c["co_test_vs_no_defense"][m]

    f.write("\\multicolumn{5}{l}{\\emph{Primary: B-RAY vs.\\ no defense, mean of the 4 original attacks}}\\\\\n")
    row("\\quad $\\Delta$AP@0.7, pts [95\\% CI]", lambda c: pci(co("B-RAY")(c)))
    row("\\quad one-sided $p$ (Holm threshold)",
        lambda c: f"{co('B-RAY')(c)['p_one_sided']:.4f} ({co('B-RAY')(c)['holm']['threshold']:.3f})")
    row("\\quad Holm reject", lambda c: "yes" if co("B-RAY")(c)["holm"]["reject"] else "no")
    row("\\quad clean rel.\\ loss, \\% [95\\% CI]", lambda c: pci(c["clean_rel_loss"]["B-RAY"]))
    row("\\quad \\textbf{success rule}", lambda c: "\\textbf{pass}" if c["pass"] else "\\textbf{fail}")
    f.write("\\midrule\n\\multicolumn{5}{l}{\\emph{Co-test: MINT vs.\\ no defense}}\\\\\n")
    row("\\quad $\\Delta$AP@0.7, pts [95\\% CI]", lambda c: pci(co("R1")(c)))
    row("\\quad one-sided $p$ (Holm threshold)",
        lambda c: f"{co('R1')(c)['p_one_sided']:.4f} ({co('R1')(c)['holm']['threshold']:.3f})")
    row("\\quad Holm reject", lambda c: "yes" if co("R1")(c)["holm"]["reject"] else "no")
    f.write("\\midrule\n\\multicolumn{5}{l}{\\emph{Key secondary: MINT $-$ B-RAY (paired)}}\\\\\n")
    row("\\quad $\\Delta$AP@0.7, pts [95\\% CI]", lambda c: pci(c["R1_minus_BRAY"]))
    row("\\quad pre-registered statement$^\\ast$", lambda c: STMT[c["R1_minus_BRAY"]["statement"]])
    f.write("\\midrule\n")
    f.write("Overall verdict & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{v['criteria_v3']['D-64']['verdict']}}}"
                                          for _, v in SETS) + " \\\\\n")

# Table (full width): Delta AP per condition, B-RAY and R1, test and Culver, both AP definitions
with open(OUT / "tables/tab_conditions.tex", "w") as f:
    f.write("% generated by gen_numbers.py -- do not edit\n")
    f.write("& \\multicolumn{4}{c}{Global-ranking AP} & \\multicolumn{4}{c}{Frame-order AP} \\\\\n")
    f.write("\\cmidrule(lr){2-5}\\cmidrule(lr){6-9}\n")
    f.write("& \\multicolumn{2}{c}{B-RAY} & \\multicolumn{2}{c}{MINT} & \\multicolumn{2}{c}{B-RAY} & \\multicolumn{2}{c}{MINT} \\\\\n")
    f.write("\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\\cmidrule(lr){8-9}\n")
    f.write("Condition & Test & Culver & Test & Culver & Test & Culver & Test & Culver \\\\\n\\midrule\n")
    for c in CONDS:
        if c == "pgd_untargeted@r0.25":
            f.write("\\midrule\n")
        cells = [mark(v["tables"][d]["per_family"][c][m]) for d in ("global", "frame") for m in ("B-RAY", "R1")
                 for _, v in SETS]
        f.write(f"{CNAME[c]} & " + " & ".join(cells) + " \\\\\n")

# Table (single column): attack conditions, both sets (realized frames, attack loss G / F)
with open(OUT / "tables/tab_attacks_both.tex", "w") as f:
    f.write("% generated by gen_numbers.py -- do not edit\n")
    f.write("& \\multicolumn{3}{c}{OPV2V test} & \\multicolumn{3}{c}{Culver City} \\\\\n")
    f.write("\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\n")
    f.write("Condition & Real. & Loss G & Loss F & Real. & Loss G & Loss F \\\\\n\\midrule\n")
    for c in CONDS[1:]:
        if c == "pgd_untargeted@r0.25":
            f.write("\\midrule\n")
        cells = []
        for _, v in SETS:
            cells += [str(v["realization"][c]["realized"])] + \
                     [f"{100 * v['point'][d][f'attack_loss|{c}']:.2f}" for d in ("global", "frame")]
        f.write(f"{CSHORT[c]} & " + " & ".join(cells) + " \\\\\n")

# Table (single column): clean cost, both sets, both AP definitions; CI on its own line
with open(OUT / "tables/tab_clean_both.tex", "w") as f:
    f.write("% generated by gen_numbers.py -- do not edit\n" + SETHEAD)
    f.write("Method & G & F & G & F \\\\\n\\midrule\n")
    for m in ("B-RAY", "R1", "R1_noREMOVE", "B-NORM"):
        ts = [v["tables"][d]["clean_rel_loss"][m] for v, d in SETCOLS]
        f.write(f"{MNAME[m]} & " + " & ".join(f"{sgn(100 * t['point'])}\\%" for t in ts) + " \\\\\n")
        f.write(" & " + " & ".join(f"{{\\tiny {ci(*t['ci95_scenario'])}}}" for t in ts) + " \\\\[1pt]\n")
    cbn = CV3["B-NORM_flags"]["clean"]
    f.write("\\midrule\n\\multicolumn{5}{l}{\\emph{Removed on clean frames}}\\\\\n")
    f.write(f"B-RAY & \\multicolumn{{2}}{{c}}{{{bb['drop']}/{bb['boxes']:,} ({bb['dropped_gt_matched']})}} & "
            f"\\multicolumn{{2}}{{c}}{{{cbb['drop']}/{cbb['boxes']:,} ({cbb['dropped_gt_matched']})}} \\\\\n")
    f.write(f"MINT & \\multicolumn{{2}}{{c}}{{{u['gated']}/{u['units']:,} ({u['false_rejections_useful']})}} & "
            f"\\multicolumn{{2}}{{c}}{{{cu['gated']}/{cu['units']:,} ({cu['false_rejections_useful']})}} \\\\\n")
    f.write(f"MINT-noREM & \\multicolumn{{2}}{{c}}{{{un['gated']}/{un['units']:,} ({un['false_rejections_useful']})}} & "
            f"\\multicolumn{{2}}{{c}}{{{cun['gated']}/{cun['units']:,} ({cun['false_rejections_useful']})}} \\\\\n")
    f.write(f"B-NORM & \\multicolumn{{2}}{{c}}{{{bn['sender1_flagged']}/{bn['frames_n2']:,} ({100 * bn['catch_rate']:.1f}\\%)}} & "
            f"\\multicolumn{{2}}{{c}}{{{cbn['sender1_flagged']}/{cbn['frames_n2']} ({100 * cbn['catch_rate']:.1f}\\%)}} \\\\\n")

# Table (single column): runtime, both sets
with open(OUT / "tables/tab_runtime_both.tex", "w") as f:
    f.write("% generated by gen_numbers.py -- do not edit\n")
    f.write("Set & $n$ & Frames & Base (s) & Full & Triggered & B-RAY \\\\\n\\midrule\n")
    for si, (name, tj) in enumerate((("Test", TEST), ("Culver", CTEST))):
        if si:
            f.write("\\midrule\n")
        st = tj["overhead"]["by_stratum"]
        for k in ("1", "2", "3", "4+"):
            if k not in st:
                continue
            s = st[k]
            base = next(v for kk, v in s.items() if kk != "frames")["baseline_s"]["p50"]

            def cell(mode):
                if mode not in s:
                    return "--"
                o = s[mode]["overhead"]
                return f"{100 * o['p50']:.0f} / {100 * o['p95']:.0f}"
            f.write(f"{name if k == '1' else ''} & {k} & {s['frames']} & {base:.3f} & {cell('dense')} & "
                    f"{cell('trigger_0.05')} & {cell('B-RAY')} \\\\\n")


# Appendix tables (full width): every defense, every condition, with CIs; test block, then Culver block
def full_rows(v, d):
    rows = []
    for c in CONDS:
        if c == "pgd_untargeted@r0.25":
            rows.append("\\cmidrule(l){1-6}")
        cells = [f"{mark(v['tables'][d]['per_family'][c][m])} {ci(*v['tables'][d]['per_family'][c][m]['ci95_scenario'])}"
                 for m in METHODS]
        rows.append(f"{CSHORT[c]} & " + " & ".join(cells) + " \\\\")
    return rows


for d in ("global", "frame"):
    lines = ["% generated by gen_numbers.py -- do not edit",
             "Condition & " + " & ".join(MNAME[m] for m in METHODS) + " \\\\", "\\midrule",
             "\\multicolumn{6}{l}{\\emph{OPV2V test (primary, 15 scenarios)}}\\\\"] + full_rows(V3, d) + \
            ["\\midrule", "\\multicolumn{6}{l}{\\emph{Culver City (unseen town, simulated sensor; secondary, 4 scenarios)}}\\\\"] + \
            full_rows(CV3, d)
    (OUT / "tables" / f"tab_full_{d}.tex").write_text("\n".join(lines) + "\n")
    # the test block equals the frozen per-condition table built from the report CSVs
    old = [l for l in (OUT / "tables" / f"tab_main_{d}.tex").read_text().splitlines()[3:] if l != "\\midrule"]
    new_ = [l for l in full_rows(V3, d) if not l.startswith("\\cmidrule")]  # compares values only
    assert len(old) == len(new_) == len(CONDS)
    for a, b in zip(old, new_):
        assert [x.replace("{\\tiny ", "").replace("]}", "]") for x in a.split(" & ")[1:]] == b.split(" & ")[1:], (a, b)

with open(OUT / "tables/tab_culver.tex", "w") as f:
    f.write("% generated by gen_numbers.py -- do not edit\n")
    f.write("& \\multicolumn{2}{c}{Global-ranking AP} & \\multicolumn{2}{c}{Frame-order AP} \\\\\n")
    f.write("\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\n")
    f.write("Statistic & Test & Culver & Test & Culver \\\\\n\\midrule\n")
    f.write("No-defense clean AP@0.7 & " + " & ".join(
        f"{100 * v['AP'][d]['clean']['undefended']['AP@0.7']:.2f}" for d in ("global", "frame") for v in (V3, CV3)) + " \\\\\n")
    f.write("\\midrule\n\\multicolumn{5}{l}{\\emph{Mean $\\Delta$AP@0.7 over the 4 original attacks (pts, 95\\% scenario CI)}}\\\\\n")
    for m in METHODS:
        cells = []
        for d in ("global", "frame"):
            for v in (V3, CV3):
                t = v["tables"][d]["mean_of_4_orig"][m]
                cells.append(f"{pts(t['point'])} {{\\tiny {ci(*t['ci95_scenario'])}}}")
        f.write(f"{MNAME[m]} & " + " & ".join(cells) + " \\\\\n")
    f.write("\\midrule\n")
    f.write("B-RAY clean rel.\\ loss & " + " & ".join(
        f"{pct(v['criteria_v3'][d]['clean_rel_loss']['B-RAY']['point'], 2)}" for d in ("global", "frame") for v in (V3, CV3)) + " \\\\\n")
    f.write("Holm reject B-RAY / MINT & " + " & ".join(
        "/".join("yes" if v["criteria_v3"][d]["co_test_vs_no_defense"][m]["holm"]["reject"] else "no" for m in ("B-RAY", "R1"))
        for d in ("global", "frame") for v in (V3, CV3)) + " \\\\\n")
    f.write("Success rule & " + " & ".join("pass" if v["criteria_v3"][d]["pass"] else "fail"
                                      for d in ("global", "frame") for v in (V3, CV3)) + " \\\\\n")
    f.write("MINT $-$ B-RAY (pts) & " + " & ".join(
        f"{pts(v['criteria_v3'][d]['R1_minus_BRAY']['point'])} {{\\tiny {ci(*v['criteria_v3'][d]['R1_minus_BRAY']['ci95_scenario'])}}}"
        for d in ("global", "frame") for v in (V3, CV3)) + " \\\\\n")
    f.write("\\midrule\n\\multicolumn{5}{l}{\\emph{Strong stealth PGD remove ($r{=}1.0^\\dagger$): attack loss; MINT recovery}}\\\\\n")
    c = "pgd_remove_stealth@r1.0"
    f.write("Attack loss (pts) & " + " & ".join(plain(100 * v["point"][d][f"attack_loss|{c}"]) for d in ("global", "frame") for v in (V3, CV3)) + " \\\\\n")
    f.write("MINT recovery & " + " & ".join(plain(v["point"][d][f"recovery|R1|{c}"]) for d in ("global", "frame") for v in (V3, CV3)) + " \\\\\n")
    f.write("B-RAY recovery & " + " & ".join(plain(v["point"][d][f"recovery|B-RAY|{c}"]) for d in ("global", "frame") for v in (V3, CV3)) + " \\\\\n")

# ---------------------------------------------------------------- write numbers.tex
with open(OUT / "numbers.tex", "w") as f:
    f.write("% generated by paper/gen_numbers.py -- DO NOT EDIT BY HAND\n")
    f.write("% AP values in AP points (AP x 100); CIs are 95% scenario-bootstrap unless the macro ends in CIblock\n")
    seen = set()
    for name, val, com in macros:
        assert name not in seen, f"duplicate macro {name}"
        seen.add(name)
        f.write(f"\\newcommand{{\\{name}}}{{{val}}}\n")
print(f"wrote {len(macros)} macros and {len(list((OUT / 'tables').glob('*.tex')))} tables")
