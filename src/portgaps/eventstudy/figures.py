"""Static figures for T4.1 (PNG). Colors: validated default palette slots 1-2
(blue = observed, orange = counterfactual); gray for placebos and context."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config as C
from . import methods as M

BLUE, ORANGE, GRAY, INK, MUTED = "#2a78d6", "#eb6834", "#9a9a94", "#22221f", "#6b6b66"
plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e6e6e2", "grid.linewidth": 0.6, "figure.dpi": 150,
    "savefig.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
})


def _dates(idx):
    return pd.to_datetime([f"{m // 100}-{m % 100:02d}-01" for m in idx])


def _shade(ax):
    for (a, b), lab, a_ in [(C.DURING, "closure", 0.13), (C.AFTER, "after", 0.06)]:
        ax.axvspan(_dates([a])[0], _dates([b])[0] + pd.offsets.MonthEnd(1), color=GRAY, alpha=a_, lw=0)
        ax.text(_dates([a])[0], 1.0, f" {lab}", transform=ax.get_xaxis_transform(), va="top",
                fontsize=8, color=MUTED)


def treated_vs_counterfactual(r, path):
    fig, axes = plt.subplots(2, 1, figsize=(8, 6.2), gridspec_kw={"height_ratios": [1.3, 1]})
    ax = axes[0]
    idx = [m for m in r["treated"].index if m >= 202101]
    d = _dates(idx)
    ax.plot(d, r["treated"][idx] / 1e6, color=BLUE, lw=2, label="Crescent City (observed)")
    ax.plot(d, r["counterfactual"][idx] / 1e6, color=ORANGE, lw=2, ls="--", label="Synthetic control")
    _shade(ax)
    ax.set_ylabel("Monthly ex-vessel value ($M, nominal)")
    ax.set_title("Crescent City all-species landings vs synthetic control", loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.0, 0.93))
    # window totals
    ax = axes[1]
    yrs = C.WINDOW_START_YEARS_PRE + [C.EVENT_WINDOW_YEAR]
    T, K, N = M.paired_window_totals(r["treated"], r["counterfactual"], yrs)
    x = np.arange(len(yrs))
    ax.bar(x - 0.2, T / 1e6, 0.38, color=BLUE, label="Observed")
    ax.bar(x + 0.2, K / 1e6, 0.38, color=ORANGE, label="Synthetic control")
    ax.set_xticks(x, [f"{y}-{(y + 1) % 100:02d}" + ("*" if N[y] else "") for y in yrs])
    ax.set_ylabel("Oct-Aug total ($M)")
    ax.set_title("Oct-Aug window totals (pre windows in-sample; 2024-25 = closure)", loc="left",
                 fontsize=10, color=INK)
    ax.legend(frameon=False, ncol=2, loc="upper right")
    ax.text(0, -0.28, "* window has withheld month(s), dropped from both bars", transform=ax.transAxes,
            fontsize=7, color=MUTED)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def brookings_shift(shift_did, r_comb, path):
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8))
    ax = axes[0]
    for key, col, lab, mk in [("value_all", BLUE, "All species", "o"), ("value_crab", ORANGE, "Dungeness crab", "s")]:
        r = shift_did[key]["ratios"]
        yrs = list(r.index)
        ax.plot(yrs[:-1], np.exp(r.values[:-1]), color=col, lw=2, marker=mk, ms=6, label=lab)
        ax.plot(yrs[-1], np.exp(r.values[-1]), marker=mk, ms=9, color=col, mec=INK, mew=1.2, ls="none")
        ax.axhline(np.exp(r.values[:-1][~np.isnan(r.values[:-1])].mean()), color=col, lw=1, ls=":")
    ax.set_xticks(yrs, [f"{y}-{(y + 1) % 100:02d}" for y in yrs], rotation=45, ha="right")
    ax.set_ylabel("South-OR / Central-OR, Oct-Aug value")
    ax.set_title("Shift test: South-OR share vs Central-OR\n(outlined = closure window; dotted = pre mean)",
                 loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False)
    ax = axes[1]
    idx = [m for m in r_comb["treated"].index if m >= 202101]
    d = _dates(idx)
    ax.plot(d, r_comb["treated"][idx] / 1e6, color=BLUE, lw=2, label="Crescent City + South-OR")
    ax.plot(d, r_comb["counterfactual"][idx] / 1e6, color=ORANGE, lw=2, ls="--", label="Synthetic control")
    _shade(ax)
    ax.set_ylabel("Monthly value ($M, nominal)")
    ax.set_title("Combined receiving area vs synthetic control", loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, 0.93))
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def placebo_distribution(ps, tp, r_did, path):
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    ax = axes[0]
    p = ps.sort_values("during_ratio")
    y = np.arange(len(p))
    cols = [BLUE if t else GRAY for t in p.is_treated]
    ax.barh(y, p.during_ratio, color=cols, height=0.7)
    ax.set_yticks(y, [u.replace("CA-", "") for u in p.unit_id], fontsize=7)
    ax.set_xlabel("Post/pre RMSPE ratio (during)")
    ax.set_title("Placebo-in-space (SC)", loc="left", fontsize=10, color=INK)
    ax = axes[1]
    p = ps.sort_values("during_pct")
    ax.barh(np.arange(len(p)), p.during_pct * 100, color=[BLUE if t else GRAY for t in p.is_treated], height=0.7)
    ax.set_yticks(np.arange(len(p)), [u.replace("CA-", "") for u in p.unit_id], fontsize=7)
    ax.axvline(0, color=MUTED, lw=0.8)
    ax.set_xlabel("11-month gap vs synthetic (%)")
    ax.set_title("Placebo-in-space: gap", loc="left", fontsize=10, color=INK)
    ax = axes[2]
    labels = list(tp.fake_event) + ["2024-10\n(actual)"]
    vals = list(tp.during_pct * 100)
    actual = ps[ps.is_treated].during_pct.iloc[0] * 100
    ax.bar(range(len(vals)), vals, color=GRAY, width=0.7, label="SC fake event")
    ax.bar(len(vals), actual, color=BLUE, width=0.7, label="SC actual")
    did = [np.exp(r_did["placebos"].get(int(l[:4]), np.nan)) * 100 - 100 for l in tp.fake_event]
    ax.plot(range(len(did)), did, ls="none", marker="o", ms=6, color=INK, label="DiD fake window")
    ax.plot(len(vals), r_did["effect_pct"] * 100, ls="none", marker="o", ms=8, mfc=BLUE, mec=INK)
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=7)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_ylabel("11-month gap (%)")
    ax.set_title("Placebo-in-time", loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def make_all(S, r_main, ps_main, tp, r_did, shift_did, r_comb, comb):
    treated_vs_counterfactual(r_main, C.FIGS / "t41_treated_vs_counterfactual.png")
    brookings_shift(shift_did, r_comb, C.FIGS / "t41_brookings_shift.png")
    placebo_distribution(ps_main, tp, r_did, C.FIGS / "t41_placebo_distribution.png")
