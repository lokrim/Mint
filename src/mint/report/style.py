"""Chart style. Method colours are fixed per method (never by rank) and were validated as a categorical set
(dataviz validate_palette.js, adjacent pairs): light worst CVD dE 9.1, normal-vision 19.6; dark 8.4 / 19.3.
Light-mode aqua/yellow/magenta are below 3:1 contrast, so every chart names each method in text (axis labels or
legend) and writes a CSV table of everything it plots (the relief rule)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

THEMES = {
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781", "grid": "#e1e0d9",
              "axis": "#c3c2b7",
              "method": {"B-RAY": "#2a78d6", "R1": "#eb6834", "R1_noREMOVE": "#1baf7a", "B-NORM": "#eda100",
                         "ego_only": "#e87ba4"},
              "series": ["#2a78d6", "#eb6834", "#1baf7a"], "neutral": "#52514e"},
    "dark": {"surface": "#1a1a19", "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#898781", "grid": "#2c2c2a",
             "axis": "#383835",
             "method": {"B-RAY": "#3987e5", "R1": "#d95926", "R1_noREMOVE": "#199e70", "B-NORM": "#c98500",
                        "ego_only": "#d55181"},
             "series": ["#3987e5", "#d95926", "#199e70"], "neutral": "#c3c2b7"},
}
FONT = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]


def apply(theme):
    t = THEMES[theme]
    plt.rcParams.update({
        "figure.facecolor": t["surface"], "axes.facecolor": t["surface"], "savefig.facecolor": t["surface"],
        "font.family": "sans-serif", "font.sans-serif": FONT, "font.size": 9,
        "text.color": t["ink"], "axes.labelcolor": t["ink2"], "axes.titlecolor": t["ink"],
        "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "xtick.color": t["muted"], "ytick.color": t["ink2"], "xtick.labelsize": 8, "ytick.labelsize": 8.5,
        "axes.edgecolor": t["axis"], "axes.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "grid.color": t["grid"], "grid.linewidth": 0.8, "grid.linestyle": "-",
        "legend.frameon": False, "legend.fontsize": 8.5, "legend.labelcolor": t["ink2"],
        "lines.solid_capstyle": "round", "svg.fonttype": "none", "svg.hashsalt": "mint-report",
    })
    return t
