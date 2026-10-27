#!/usr/bin/env python3
"""Forest plot for the paper (Fig. forest): mean Delta AP@0.7 over the 4 original attacks for B-RAY and
MINT, and the paired MINT - B-RAY, on the OPV2V test (primary) and on Culver City (unseen town, simulated
sensor; secondary), under both AP definitions. 95% scenario-bootstrap CIs. The two sets are never pooled: there is
no combined estimate.

Reads (read-only), keys in brackets:
  runs/20261024-E5v3/e5_v3.json, runs/20261026-CULVER/e5_v3.json
    [tables.<ap>.mean_of_4_orig.<method>.{point,ci95_scenario}]
    [tables.<ap>.R1_minus_BRAY.mean_of_4.{point,ci95_scenario}]
    [criteria_v3.<ap>.co_test_vs_no_defense.<method>.holm.reject], [criteria_v3.<ap>.R1_minus_BRAY.statement]
  and asserts they equal criteria_v3 and the report CSVs (01_headline.csv, both runs).
Writes paper/figures/forest.pdf (vector, for LaTeX) and forest.png (preview).
Nothing is recomputed: the only transformation is x100 to AP points.

Needs matplotlib: .venv-report/bin/python paper/figures/forest.py
"""
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SETS = [("OPV2V test (primary, 15 scenarios)", ROOT / "runs/20261024-E5v3"),
        ("Culver City (unseen town, same simulated sensor; 4 scenarios)", ROOT / "runs/20261026-CULVER")]
APS = [("global", "Global-ranking AP"), ("frame", "Frame-order AP")]
# MINT-noREMOVE is reported in the ablation subsection, not in this headline figure
ROWS = [("B-RAY", "B-RAY"), ("R1", "MINT"), ("RmB", "MINT $-$ B-RAY\n(paired)")]
# method colours as in src/mint/report/style.py (light theme); the paired row is neutral
COL = {"B-RAY": "#2a78d6", "R1": "#eb6834", "R1_noREMOVE": "#1baf7a", "RmB": "#52514e"}
SHORT = {"the counterfactual improves over the box-level filter": "MINT better",
         "the counterfactual performs worse than the box-level filter": "MINT worse",
         "the counterfactual's benefit over a box-level filter is not established": "not established"}


def load(run):
    v3 = json.load(open(run / "e5_v3.json"))
    with open(run / "report/tables/01_headline.csv") as f:
        head = {(r["ap_definition"], r["method"]): r for r in csv.DictReader(f)}
    data = {}
    for ap, _ in APS:
        t, cr = v3["tables"][ap], v3["criteria_v3"][ap]
        for m, _ in ROWS:
            if m == "RmB":
                s = t["R1_minus_BRAY"]["mean_of_4"]
                assert s["point"] == cr["R1_minus_BRAY"]["point"] and s["ci95_scenario"] == cr["R1_minus_BRAY"]["ci95_scenario"]
                note = SHORT[cr["R1_minus_BRAY"]["statement"]]
            else:
                s = t["mean_of_4_orig"][m]
                h = head[(ap, m)]
                assert abs(float(h["point"]) - s["point"]) < 1e-12
                assert [float(h["ci95_scenario_lo"]), float(h["ci95_scenario_hi"])] == s["ci95_scenario"]
                if m in cr["co_test_vs_no_defense"]:
                    c = cr["co_test_vs_no_defense"][m]
                    assert c["point"] == s["point"] and c["ci95_scenario"] == s["ci95_scenario"]
                    note = "significant" if c["holm"]["reject"] else "not significant"
                else:
                    note = ""
            data[(ap, m)] = (100 * s["point"], 100 * s["ci95_scenario"][0], 100 * s["ci95_scenario"][1], note)
    return data


def main():
    D = [load(run) for _, run in SETS]
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
                         "font.size": 7, "axes.linewidth": 0.6, "axes.spines.top": False,
                         "axes.spines.right": False, "xtick.labelsize": 6.5, "ytick.labelsize": 7,
                         "xtick.major.width": 0.5, "ytick.major.size": 0, "pdf.fonttype": 42})
    fig, axes = plt.subplots(1, 2, figsize=(3.5, 2.2), sharey=True)
    ypos = {m: -i * 1.25 for i, (m, _) in enumerate(ROWS)}
    ypos["RmB"] -= 0.45                      # small gap before the paired row
    off = (0.22, -0.22)                      # test above, Culver below
    for ax, (ap, title) in zip(axes, APS):
        ax.axvline(0, color="#898781", lw=0.6, zorder=1)
        for si, d in enumerate(D):
            for m, _ in ROWS:
                p, lo, hi, note = d[(ap, m)]
                y = ypos[m] + off[si]
                ax.plot([lo, hi], [y, y], color=COL[m], lw=1.1, solid_capstyle="butt", zorder=2)
                ax.plot(p, y, marker="o" if si == 0 else "s", ms=3.6, zorder=3,
                        mfc=COL[m] if si == 0 else "white", mec=COL[m], mew=0.9)
                if note:
                    ax.text(hi + 0.03, y, note, fontsize=5, va="center", ha="left", color="#52514e", clip_on=False)
        ax.set_title(title, fontsize=7, loc="left", fontweight="bold", pad=3)
        ax.set_xlabel(r"$\Delta$AP@0.7 (AP points)", fontsize=6.5, labelpad=1.5)
    lim = (min(min(d[k][1] for k in d) for d in D) - 0.1, max(max(d[k][2] for k in d) for d in D) + 1.45)
    for ax in axes:
        ax.set_xlim(*lim)
        ax.set_xticks([-1, 0, 1, 2])
    axes[0].set_yticks([ypos[m] for m, _ in ROWS])
    axes[0].set_yticklabels([lab for _, lab in ROWS])
    for tl, (m, _) in zip(axes[0].get_yticklabels(), ROWS):
        tl.set_color(COL[m])
    h = [plt.Line2D([], [], color="#52514e", marker="o", mfc="#52514e", ms=3.6, lw=1.1, label=SETS[0][0]),
         plt.Line2D([], [], color="#52514e", marker="s", mfc="white", ms=3.6, lw=1.1, label=SETS[1][0])]
    fig.legend(handles=h, loc="lower center", ncol=1, frameon=False, fontsize=6, bbox_to_anchor=(0.55, -0.01),
               handlelength=1.6)
    fig.subplots_adjust(left=0.235, right=0.985, top=0.92, bottom=0.3, wspace=0.08)
    fig.savefig(OUT / "forest.pdf")
    fig.savefig(OUT / "forest.png", dpi=300)
    for (name, _), d in zip(SETS, D):
        print(name, {k: tuple(round(x, 2) if isinstance(x, float) else x for x in v) for k, v in d.items()})


if __name__ == "__main__":
    main()
