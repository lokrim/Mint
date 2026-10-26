"""Report figures. Every function returns (fig, rows): rows is the table of exactly what is plotted (written as
CSV next to the image). Values are copied from the analysis summaries; AP differences are shown in AP points
(x 100), relative losses and rates in percent. No statistic is recomputed here."""
import textwrap

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from .data import DEF_NAME, DEFS, METHOD_NAME, STATUS_TEXT

PTS = 100.0                      # AP fraction -> AP points
STATUS_INK = {"FINAL": "ink2", "DEVELOPMENT": "muted"}
CRITICAL = "#d03b3b"             # status palette: critical (INCOMPLETE banner), always with its text label


# ---------------------------------------------------------------------- labels
def cond_label(c, prereg=None):
    names = {"clean": "clean (no attack)", "spoof_feat": "spoof - feature", "remove_feat": "remove - feature",
             "shift_feat": "shift - feature", "spoof_pts": "spoof - points", "spoof_blind": "spoof in receiver-blind area"}
    if c in names:
        return names[c]
    if "@r" not in c:
        return c
    fam, r = c.split("@r")
    s = "PGD " + fam.replace("pgd_", "").replace("_stealth", " stealth").replace("untargeted", "untargeted") + f" r={r}"
    if prereg and c in d70_conditions(prereg):
        s += " †"
    return s


def d70_conditions(prereg):
    lv = ((prereg or {}).get("pgd_families") or {}).get("D-70_strong_level") or {}
    return {c["condition"] for c in lv.get("conditions", [])}


def _fmt(v, scale=1.0, nd=2, sign=True):
    if v is None:
        return "n/a"
    return f"{v * scale:+.{nd}f}" if sign else f"{v * scale:.{nd}f}"


def _ci(ci, scale):
    return (None, None) if ci is None else (ci[0] * scale, ci[1] * scale)


def footer(fig, inp, t):
    color = CRITICAL if inp.status == "INCOMPLETE" else t[STATUS_INK[inp.status]]
    txt = f"{STATUS_TEXT[inp.status]}  ·  {inp.label}"
    fig.text(0.01, 0.006, textwrap.shorten(txt, 150, placeholder=" ..."), fontsize=6.5, color=color, ha="left",
             va="bottom")


def _zero(ax, t, x=0.0):
    ax.axvline(x, color=t["axis"], lw=1.0, zorder=1)


def _xgrid(ax):
    ax.grid(axis="x")
    ax.set_axisbelow(True)


def _dot(ax, x, y, color, t, size=7, marker="o", z=4):
    ax.plot([x], [y], marker=marker, ms=size, color=color, mec=t["surface"], mew=1.6, zorder=z, ls="none")


def _ci_line(ax, lo, hi, y, color, lw, alpha=1.0, z=3):
    if lo is not None:
        ax.plot([lo, hi], [y, y], color=color, lw=lw, alpha=alpha, solid_capstyle="round", zorder=z)


def _ci_legend(ax, t, loc=None):
    h = [Line2D([], [], color=t["ink2"], lw=3.2, solid_capstyle="round", label="95% CI, scenario bootstrap"),
         Line2D([], [], color=t["ink2"], lw=1.1, alpha=0.6, label="95% CI, 10-frame-block bootstrap")]
    ax.figure.legend(handles=h, loc="upper left", ncol=2, bbox_to_anchor=(0.005, 0.955))


def _method_legend(fig, methods, t, ncol=None):
    h = [Line2D([], [], marker="o", ls="none", ms=7, color=t["method"][m], mec=t["surface"], mew=1.6,
                label=METHOD_NAME[m]) for m in methods]
    fig.legend(handles=h, loc="upper left", ncol=ncol or len(methods), bbox_to_anchor=(0.005, 0.965))


def _rows_ylim(ax, n, t, top=-0.5):
    """Row-axis limits; an empty section says so instead of drawing an empty axis."""
    if n == 0:
        ax.set_ylim(0.5, -0.5)
        ax.text(0.5, 0.5, "no data for this figure in this file", transform=ax.transAxes, ha="center", va="center",
                color=t["muted"], fontsize=9)
    else:
        ax.set_ylim(n - 0.5, top)


def _no_ego(inp):
    return [m for m in inp.methods if m != "ego_only"]


# ---------------------------------------------------------------------- 1 headline
def fig_headline(inp, t):
    """Mean dAP@0.7 over the 4 original attack families, per method, both AP definitions (the v2 primary family)."""
    methods = _no_ego(inp)
    fig, axes = plt.subplots(1, 2, figsize=(9, 0.55 * len(methods) + 1.9), sharey=True)
    rows = []
    for ax, d in zip(axes, DEFS):
        for i, m in enumerate(methods):
            s = inp.stat(d, f"mean_delta_orig|{m}")
            rows.append({"ap_definition": d, "method": m, **_rowstat(s)})
            if s["point"] is None:
                continue
            c = t["method"][m]
            _ci_line(ax, *_ci(s["ci_block10"], PTS), i, c, 1.1, 0.6)
            _ci_line(ax, *_ci(s["ci_scenario"], PTS), i, c, 3.2)
            _dot(ax, s["point"] * PTS, i, c, t)
            hi = max(x for x in (s["point"] * PTS, *(_ci(s["ci_block10"], PTS)), *(_ci(s["ci_scenario"], PTS)))
                     if x is not None)
            ax.text(hi, i - 0.28, f"{s['point'] * PTS:+.2f}", fontsize=8, color=t["ink2"], ha="left", va="bottom")
        _zero(ax, t)
        _xgrid(ax)
        ax.set_title(DEF_NAME[d])
        ax.set_xlabel("ΔAP@0.7 vs no defense (AP points)")
    axes[0].set_yticks(range(len(methods)), [METHOD_NAME[m] for m in methods])
    axes[0].set_ylim(len(methods) - 0.4, -0.6)
    _ci_legend(axes[1], t)
    ego = [inp.point(d, "mean_delta_orig|ego_only") for d in DEFS]
    for d, v in zip(DEFS, ego):
        rows.append({"ap_definition": d, "method": "ego_only", **_rowstat(inp.stat(d, "mean_delta_orig|ego_only"))})
    fig.suptitle("Mean effect over the 4 original attacks (higher is better)", x=0.01, y=0.995, va="top", ha="left",
                 fontweight="bold", fontsize=11)
    fig.tight_layout(rect=(0, 0.03, 1, 0.88))
    footer(fig, inp, t)
    return fig, rows


def _rowstat(s, scale=1.0):
    lo, hi = s["ci_scenario"] or (None, None)
    blo, bhi = s["ci_block10"] or (None, None)
    return {"point": s["point"], "ci95_scenario_lo": lo, "ci95_scenario_hi": hi, "ci95_block10_lo": blo,
            "ci95_block10_hi": bhi}


# ---------------------------------------------------------------------- 2 per family
def fig_per_family(inp, t, pgd=False):
    methods = _no_ego(inp)
    conds = inp.pgd_conditions if pgd else [c for c in inp.conditions if c not in inp.pgd_conditions]
    fig, axes = plt.subplots(1, 2, figsize=(10, 0.5 * len(conds) + 2.2), sharey=True)
    rows = []
    off = [(j - (len(methods) - 1) / 2) * 0.17 for j in range(len(methods))]
    for ax, d in zip(axes, DEFS):
        for i, c in enumerate(conds):
            if i % 2 == 0:
                ax.axhspan(i - 0.5, i + 0.5, color=t["grid"], alpha=0.35, lw=0, zorder=0)
            for j, m in enumerate(methods):
                s = inp.stat(d, f"delta|{m}|{c}")
                rows.append({"ap_definition": d, "condition": c, "method": m, **_rowstat(s)})
                if s["point"] is None:
                    continue
                y = i + off[j]
                _ci_line(ax, *_ci(s["ci_scenario"], PTS), y, t["method"][m], 2.0)
                _dot(ax, s["point"] * PTS, y, t["method"][m], t, size=5.5)
        _zero(ax, t)
        _xgrid(ax)
        ax.set_title(DEF_NAME[d])
        ax.set_xlabel("ΔAP@0.7 vs no defense (AP points); line = 95% CI, scenario bootstrap")
    axes[0].set_yticks(range(len(conds)), [cond_label(c, inp.prereg) for c in conds])
    _rows_ylim(axes[0], len(conds), t)
    _method_legend(fig, methods, t)
    fig.suptitle("Effect of each defense, " + ("optimized (PGD) attacks" if pgd else "original attacks and clean"),
                 x=0.01, y=0.995, ha="left", va="top",
                 fontweight="bold", fontsize=11)
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    footer(fig, inp, t)
    return fig, rows


# ---------------------------------------------------------------------- 3 clean cost
def fig_clean_cost(inp, t):
    methods = _no_ego(inp)
    fig, axes = plt.subplots(1, 2, figsize=(9, 0.55 * len(methods) + 1.9), sharey=True)
    rows = []
    for ax, d in zip(axes, DEFS):
        for i, m in enumerate(methods):
            s = inp.stat(d, f"rel_loss|{m}")
            rows.append({"ap_definition": d, "method": m, **_rowstat(s)})
            if s["point"] is None:
                continue
            c = t["method"][m]
            _ci_line(ax, *_ci(s["ci_block10"], 100), i, c, 1.1, 0.6)
            _ci_line(ax, *_ci(s["ci_scenario"], 100), i, c, 3.2)
            _dot(ax, s["point"] * 100, i, c, t)
        _zero(ax, t)
        ax.axvline(1.0, color=t["ink2"], lw=1.0, zorder=1)
        ax.text(1.0, -0.55, " 1% limit (B-RAY, scenario-CI high)", fontsize=7.5, color=t["ink2"], va="bottom")
        _xgrid(ax)
        ax.set_title(DEF_NAME[d])
        ax.set_xlabel("relative AP@0.7 loss on clean frames (%), lower is better")
    axes[0].set_yticks(range(len(methods)), [METHOD_NAME[m] for m in methods])
    axes[0].set_ylim(len(methods) - 0.4, -0.8)
    _ci_legend(axes[1], t)
    for d in DEFS:
        rows.append({"ap_definition": d, "method": "ego_only", **_rowstat(inp.stat(d, "rel_loss|ego_only"))})
    fig.suptitle("Cost on clean (unattacked) frames", x=0.01, y=0.995, va="top", ha="left", fontweight="bold",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0.03, 1, 0.88))
    footer(fig, inp, t)
    return fig, rows


# ---------------------------------------------------------------------- 4 R1 - B-RAY
def fig_r1_minus_bray(inp, t, pgd=False):
    if pgd:
        keys = [(f"paired|R1-B-RAY|{c}", cond_label(c, inp.prereg)) for c in inp.pgd_conditions]
    else:
        keys = [("paired_mean_orig|R1-B-RAY", "mean of 4 original attacks"),
                ("paired_mean_3|R1-B-RAY", "mean of 3 (excl. remove)")] + \
               [(f"paired|R1-B-RAY|{c}", cond_label(c, inp.prereg)) for c in inp.conditions
                if c not in inp.pgd_conditions]
    fig, axes = plt.subplots(1, 2, figsize=(10, 0.45 * len(keys) + 2.8), sharey=True)
    rows = []
    for ax, d in zip(axes, DEFS):
        for i, (k, _) in enumerate(keys):
            s = inp.stat(d, k)
            rows.append({"ap_definition": d, "statistic": k, **_rowstat(s)})
            if s["point"] is None:
                continue
            _ci_line(ax, *_ci(s["ci_block10"], PTS), i, t["neutral"], 1.1, 0.6)
            _ci_line(ax, *_ci(s["ci_scenario"], PTS), i, t["neutral"], 3.2)
            _dot(ax, s["point"] * PTS, i, t["neutral"], t, size=6.5 if (i < 2 and not pgd) else 5.5)
        if not pgd:
            ax.axhline(1.5, color=t["axis"], lw=0.8)
        _zero(ax, t)
        _xgrid(ax)
        st = None if pgd else ((inp.v3.get("criteria_v3") or {}).get(d) or {}).get("R1_minus_BRAY", {}).get("statement")
        ax.set_title(DEF_NAME[d] + ("\n" + "\n".join(textwrap.wrap(f"pre-registered statement: “{st}”", 60))
                                    if st else ""), fontsize=9)
        ax.set_xlabel("R1 − B-RAY, paired ΔAP@0.7 (AP points); > 0 favours R1")
    axes[0].set_yticks(range(len(keys)), [lab for _, lab in keys])
    _rows_ylim(axes[0], len(keys), t)
    _ci_legend(axes[1], t)
    fig.suptitle(("R1 − B-RAY under the optimized (PGD) attacks (descriptive)" if pgd else
                  "Key secondary: does the counterfactual (R1) beat the box-level ray filter (B-RAY)?"), x=0.01,
                 y=0.995, va="top", ha="left", fontweight="bold", fontsize=11)
    fig.tight_layout(rect=(0, 0.03, 1, 0.92))
    footer(fig, inp, t)
    return fig, rows


# ---------------------------------------------------------------------- 5 PGD recovery
def fig_pgd_recovery(inp, t, lim=(-1.5, 1.5)):
    conds = inp.pgd_conditions
    methods = [m for m in ("B-RAY", "R1", "R1_noREMOVE", "B-NORM") if m in inp.methods]
    fig, axes = plt.subplots(1, 2, figsize=(10, 0.5 * max(len(conds), 1) + 2.0), sharey=True)
    rows = []
    off = [(j - (len(methods) - 1) / 2) * 0.18 for j in range(len(methods))]
    for ax, d in zip(axes, DEFS):
        for i, c in enumerate(conds):
            if i % 2 == 0:
                ax.axhspan(i - 0.5, i + 0.5, color=t["grid"], alpha=0.35, lw=0, zorder=0)
            for j, m in enumerate(methods):
                v = inp.point(d, f"recovery|{m}|{c}")
                rows.append({"ap_definition": d, "condition": c, "method": m, "recovery": v,
                             "attack_loss": inp.point(d, f"attack_loss|{c}")})
                if v is None:
                    continue
                y = i + off[j]
                if v < lim[0] or v > lim[1]:
                    x = lim[0] if v < lim[0] else lim[1]
                    _dot(ax, x, y, t["method"][m], t, size=6, marker="<" if v < lim[0] else ">")
                    ax.text(x + (0.06 if v < lim[0] else -0.06), y, f"{v:.1f}", fontsize=7, color=t["ink2"],
                            va="center", ha="left" if v < lim[0] else "right")
                else:
                    _dot(ax, v, y, t["method"][m], t, size=6)
        _zero(ax, t)
        ax.axvline(1.0, color=t["ink2"], lw=0.8, zorder=1)
        ax.text(1.0, -0.6, " full recovery", fontsize=7.5, color=t["ink2"], va="bottom")
        ax.set_xlim(lim[0] - 0.05, lim[1] + 0.05)
        _xgrid(ax)
        ax.set_title(DEF_NAME[d])
        ax.set_xlabel("recovery = ΔAP@0.7 / attack loss (arrows: off-scale, value printed)")
    axes[0].set_yticks(range(len(conds)), [cond_label(c, inp.prereg) for c in conds])
    _rows_ylim(axes[0], len(conds), t, -0.9)
    _method_legend(fig, methods, t)
    fig.suptitle("Optimized (PGD) feature attacks: fraction of the damage undone", x=0.01, y=0.995, ha="left",
                 va="top", fontweight="bold", fontsize=11)
    fig.tight_layout(rect=(0, 0.03, 1, 0.92))
    footer(fig, inp, t)
    return fig, rows


# ---------------------------------------------------------------------- 6 B-NORM catch rate
def fig_bnorm_catch(inp, t):
    flags = inp.v3.get("B-NORM_flags") or {}
    conds = [c for c in inp.conditions if c in flags]
    fig, ax = plt.subplots(figsize=(8, 0.36 * len(conds) + 1.6))
    rows = []
    for i, c in enumerate(conds):
        f = flags[c]
        r = f.get("catch_rate")
        rows.append({"condition": c, **{k: f.get(k) for k in ("frames_n2", "applied", "sender1_flagged",
                                                                 "any_flagged", "catch_rate")}})
        if r is None:
            ax.text(0.5, i, "n/a (no attacked frame)", fontsize=7.5, color=t["muted"], va="center")
            continue
        ax.plot([0, r * 100], [i, i], color=t["method"]["B-NORM"], lw=9, solid_capstyle="butt", zorder=3)
        ax.text(max(r * 100, 5) + 1.5, i, f"{r * 100:.0f}%  ({f['sender1_flagged']}/{f['applied']})", fontsize=7.5,
                color=t["ink2"], va="center")
    ax.axvline(5, color=t["ink2"], lw=1.0, zorder=1)
    ax.text(5, -0.75, " 5%: expected ceiling on stealth attacks (D-68)", fontsize=7.5, color=t["ink2"], va="bottom")
    ax.set_xlim(0, 118)
    ax.set_yticks(range(len(conds)), [cond_label(c, inp.prereg) for c in conds])
    _rows_ylim(ax, len(conds), t, -1.0)
    _xgrid(ax)
    ax.set_xlabel("frames where the attacker (sender 1) is flagged by B-NORM (%); 'clean' = false-flag rate")
    ax.set_title("B-NORM catch rate per condition (frames with a sender)")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    footer(fig, inp, t)
    return fig, rows


# ---------------------------------------------------------------------- 7 attack strength
def fig_attack_strength(inp, t):
    conds = [c for c in inp.conditions if c != "clean"]
    ro = inp.v3.get("realized_only") or {}
    fig, axes = plt.subplots(1, 2, figsize=(10, 0.42 * len(conds) + 2.0), sharey=True)
    rows = []
    a, b = t["series"][0], t["series"][1]
    for ax, d in zip(axes, DEFS):
        for i, c in enumerate(conds):
            s = inp.stat(d, f"attack_loss|{c}")
            r = (ro.get(c) or {}).get(d, {}).get("attack_loss")
            rows.append({"ap_definition": d, "condition": c, **_rowstat(s), "realized_only_attack_loss": r,
                         "realized_frames": (ro.get(c) or {}).get("frames")})
            if s["point"] is not None:
                _ci_line(ax, *_ci(s["ci_scenario"], PTS), i - 0.12, a, 2.4)
                _dot(ax, s["point"] * PTS, i - 0.12, a, t, size=6)
            if r is not None:
                _dot(ax, r * PTS, i + 0.12, b, t, size=6, marker="D")
        _zero(ax, t)
        _xgrid(ax)
        ax.set_title(DEF_NAME[d])
        ax.set_xlabel("attack loss = AP@0.7 clean − attacked, no defense (AP points)")
    axes[0].set_yticks(range(len(conds)), [cond_label(c, inp.prereg) for c in conds])
    _rows_ylim(axes[0], len(conds), t)
    h = [Line2D([], [], marker="o", ls="-", lw=2.4, ms=6, color=a, mec=t["surface"], label="all frames (95% CI, scenario)"),
         Line2D([], [], marker="D", ls="none", ms=6, color=b, mec=t["surface"], label="frames where the attack was realized")]
    fig.legend(handles=h, loc="upper left", ncol=2, bbox_to_anchor=(0.005, 0.965))
    fig.suptitle("How much each attack hurts an undefended receiver", x=0.01, y=0.995, ha="left", va="top",
                 fontweight="bold", fontsize=11)
    fig.tight_layout(rect=(0, 0.03, 1, 0.92))
    footer(fig, inp, t)
    return fig, rows


# ---------------------------------------------------------------------- 8 B-RAY drops
def fig_bray_boxes(inp, t):
    src = inp.v3.get("B-RAY_boxes") or (inp.v2 or {}).get("B-RAY_boxes") or {}
    conds = [c for c in inp.conditions if c in src]
    fig, ax = plt.subplots(figsize=(8, 0.36 * max(len(conds), 1) + 1.8))
    rows = []
    a, b = t["series"][0], t["series"][1]
    for i, c in enumerate(conds):
        r = src[c]
        um, gm = r.get("dropped_unmatched", 0), r.get("dropped_gt_matched", 0)
        rows.append({"condition": c, **r})
        ax.barh(i, um, height=0.55, color=a, edgecolor=t["surface"], linewidth=2, zorder=3)
        ax.barh(i, gm, left=um, height=0.55, color=b, edgecolor=t["surface"], linewidth=2, zorder=3)
        ax.text(um + gm + 0.5, i, f"{um + gm} of {r.get('boxes')} boxes", fontsize=7.5, color=t["ink2"], va="center")
    ax.set_yticks(range(len(conds)), [cond_label(c, inp.prereg) for c in conds])
    _rows_ylim(ax, len(conds), t)
    xmax = max([src[c].get("drop", 0) for c in conds] + [1])
    ax.set_xlim(0, xmax * 1.35)
    _xgrid(ax)
    ax.set_xlabel("boxes removed by B-RAY (count)")
    ax.set_title("What B-RAY removes: fabricated/wrong boxes vs real cars")
    h = [Line2D([], [], lw=8, color=a, label="no matching ground-truth car (intended)"),
         Line2D([], [], lw=8, color=b, label="matched a real car (cost)")]
    ax.legend(handles=h, loc="lower right")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    footer(fig, inp, t)
    return fig, rows


# ---------------------------------------------------------------------- 9 R1 units
def fig_r1_units(inp, t):
    units = (inp.v2 or {}).get("units") or {}
    conds = [c for c in inp.conditions if f"R1|{c}" in units]
    fig, ax = plt.subplots(figsize=(8, 0.36 * max(len(conds), 1) + 1.8))
    rows = []
    parts = (("gated_harmful", "harmful contribution switched off (intended)"),
             ("gated_neutral", "neutral contribution switched off"),
             ("false_rejections_useful", "useful contribution switched off (cost)"))
    for i, c in enumerate(conds):
        u = units[f"R1|{c}"]
        rows.append({"condition": c, **{k: u.get(k) for k in ("units", "n_KNOWN", "frac_KNOWN", "gated",
                                                               "gated_harmful", "gated_neutral",
                                                               "false_rejections_useful", "precision",
                                                               "harmful_units", "harmful_KNOWN", "useful_units")}})
        left = 0
        for j, (k, _) in enumerate(parts):
            v = u.get(k) or 0
            ax.barh(i, v, left=left, height=0.55, color=t["series"][j], edgecolor=t["surface"], linewidth=2, zorder=3)
            left += v
        p = u.get("precision")
        ax.text(left + 0.5, i, f"precision {p:.2f}" if p is not None else "nothing gated", fontsize=7.5,
                color=t["ink2"], va="center")
    ax.set_yticks(range(len(conds)), [cond_label(c, inp.prereg) for c in conds])
    _rows_ylim(ax, len(conds), t)
    xmax = max([(units[f"R1|{c}"].get("gated") or 0) for c in conds] + [1])
    ax.set_xlim(0, xmax * 1.4)
    _xgrid(ax)
    ax.set_xlabel("sender × tile contributions switched off by R1 (count; frame-order analysis)")
    ax.set_title("What R1 switches off, judged against ground truth")
    ax.legend(handles=[Line2D([], [], lw=8, color=t["series"][j], label=lab) for j, (_, lab) in enumerate(parts)],
              loc="lower right")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    footer(fig, inp, t)
    return fig, rows


# ---------------------------------------------------------------------- 10 by agent count
def fig_by_agents(inp, t):
    ba = (inp.v2 or {}).get("by_agents") or {}
    ns = sorted(ba, key=lambda k: int(k.rstrip("+")))     # strata are "2", "3", "4+" (e5_analyze.STRATA)
    methods = [m for m in ("B-RAY", "R1", "R1_noREMOVE") if m in inp.methods]
    fig, ax = plt.subplots(figsize=(8, 3.4))
    rows = []
    off = [(j - (len(methods) - 1) / 2) * 0.16 for j in range(len(methods))]
    for i, n in enumerate(ns):
        g = ba[n]
        for j, m in enumerate(methods):
            k = f"mean_delta_orig|{m}"
            v = (g.get("point") or {}).get(k)
            ci = ((g.get("bootstrap_block10") or {}).get(k) or {}).get("ci95")
            rows.append({"n_agents": n, "frames": g.get("frames"), "scenarios": g.get("scenarios"), "method": m,
                         "point": v, "ci95_block10_lo": ci[0] if ci else None, "ci95_block10_hi": ci[1] if ci else None})
            if v is None:
                continue
            x = i + off[j]
            if ci:
                ax.plot([x, x], [ci[0] * PTS, ci[1] * PTS], color=t["method"][m], lw=2.0, solid_capstyle="round", zorder=3)
            _dot(ax, x, v * PTS, t["method"][m], t, size=6)
    ax.axhline(0, color=t["axis"], lw=1.0, zorder=1)
    ax.set_xlim(-0.6, len(ns) - 0.4)
    ax.set_xticks(range(len(ns)), [f"n = {n}\n{ba[n].get('frames')} frames, {ba[n].get('scenarios')} scen." for n in ns])
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.set_ylabel("ΔAP@0.7, mean of 4 attacks (AP points)")
    ax.set_title("By number of cars in the frame (frame-order AP; 95% CI, 10-frame blocks)")
    ax.legend(handles=[Line2D([], [], marker="o", ls="none", ms=7, color=t["method"][m], mec=t["surface"],
                              label=METHOD_NAME[m]) for m in methods], loc="best")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    footer(fig, inp, t)
    return fig, rows


FIGURES = [
    ("01_headline", "1", fig_headline, "Headline: mean \u0394AP@0.7 over the 4 original attacks",
     "Each defense's mean change in AP@0.7 against no defense, over spoof/remove/shift (feature) and spoof (points). "
     "Dot = point estimate; thick line = 95% CI from the scenario bootstrap (the pre-registered primary CI); thin "
     "line = 10-frame-block bootstrap. Ego-only is far off-scale and is listed in the table only."),
    ("02_per_family", "2a", fig_per_family, "\u0394AP@0.7 per condition: clean and original attacks",
     "Every non-PGD condition \u00d7 defense, both AP definitions, 95% CI from the scenario bootstrap. Ego-only in the "
     "table only."),
    ("02b_per_family_pgd", "2b", lambda inp, t: fig_per_family(inp, t, pgd=True),
     "\u0394AP@0.7 per condition: optimized (PGD) attacks",
     "As 2a for the PGD conditions, on its own scale (PGD effects are much larger than the original attacks')."),
    ("03_clean_cost", "3", fig_clean_cost, "Clean cost (relative AP@0.7 loss)",
     "Relative AP@0.7 loss on clean frames. The pre-registered success rule requires B-RAY's scenario-CI high "
     "\u2264 1% under both AP definitions."),
    ("04_r1_minus_bray", "4a", fig_r1_minus_bray, "Key secondary: R1 \u2212 B-RAY",
     "Paired difference R1 \u2212 B-RAY in \u0394AP@0.7, the pre-registered means and each non-PGD condition. Each "
     "panel quotes the statement the frozen analysis emitted."),
    ("04b_r1_minus_bray_pgd", "4b", lambda inp, t: fig_r1_minus_bray(inp, t, pgd=True),
     "R1 \u2212 B-RAY under PGD attacks",
     "Paired difference per PGD condition (descriptive; not part of the key secondary)."),
    ("05_pgd_recovery", "5", fig_pgd_recovery, "PGD attacks: recovery",
     "Recovery = \u0394AP@0.7 / attack loss per optimized-attack condition. n/a when the attack loss is < 0.005."),
    ("06_bnorm_catch", "6", fig_bnorm_catch, "B-NORM catch rate",
     "Share of frames with a sender in which B-NORM flags the attacker; on 'clean' this is the false-flag rate."),
    ("07_attack_strength", "7", fig_attack_strength, "Attack strength",
     "Attack loss per condition over all frames (with CI) and over the frames where the attack was realized."),
    ("08_bray_boxes", "8", fig_bray_boxes, "B-RAY removals",
     "Boxes B-RAY removed, split by whether they matched a real car."),
    ("09_r1_units", "9", fig_r1_units, "R1 gating against ground truth",
     "Contributions (sender \u00d7 6.4 m tile) R1 switched off, by their ground-truth label."),
    ("10_by_agents", "10", fig_by_agents, "Effect by number of cars",
     "Mean \u0394AP@0.7 over the 4 original attacks per agent count (frozen v2 analysis, frame-order AP)."),
]
