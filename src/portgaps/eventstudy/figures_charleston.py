"""Static figures for T4.2 (PNG), same style and palette as the T4.1 figures
(blue = observed, orange = counterfactual, gray = placebos and context)."""
import numpy as np

from . import config_charleston as K
from . import methods as M
from .figures import plt, BLUE, ORANGE, GRAY, INK, MUTED, _dates


def _shade(ax):
    for (a, b), lab, al, yy in [(K.DURING, "closure", 0.13, 1.0), (K.AFTER_Y1, "after yr 1", 0.06, 0.94)]:
        ax.axvspan(_dates([a])[0], _dates([b])[0] + np.timedelta64(31, "D"), color=GRAY, alpha=al, lw=0)
        ax.text(_dates([a])[0], yy, f" {lab}", transform=ax.get_xaxis_transform(), va="top",
                fontsize=7, color=MUTED)


def _obs_cf(ax, r, label, start=201701):
    idx = [m for m in r["treated"].index if m >= start]
    d = _dates(idx)
    ax.plot(d, r["treated"][idx] / 1e6, color=BLUE, lw=1.8, label=f"{label} (observed)")
    ax.plot(d, r["counterfactual"][idx] / 1e6, color=ORANGE, lw=1.8, ls="--", label="Synthetic control")
    _shade(ax)
    ax.set_ylabel("Monthly value ($M, nominal)")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.0, 0.93), fontsize=8)


def treated_vs_counterfactual(r, r_did, path):
    fig, axes = plt.subplots(2, 1, figsize=(8, 6.2), gridspec_kw={"height_ratios": [1.3, 1]})
    ax = axes[0]
    _obs_cf(ax, r, "Charleston")
    ax.set_title("Charleston all-species landings vs synthetic control (OR donors)", loc="left",
                 fontsize=10, color=INK)
    ax = axes[1]
    yrs = K.DID_PRE_YEARS + [K.DID_EVENT_YEAR] + K.PLACEBO_YEARS_POST
    T, C, _ = M.paired_window_totals(r["treated"], r["counterfactual"], yrs, K.DID_M_START, K.DID_M_END)
    x = np.arange(len(yrs))
    ax.bar(x - 0.2, T / 1e6, 0.38, color=BLUE, label="Observed")
    ax.bar(x + 0.2, C / 1e6, 0.38, color=ORANGE, label="Synthetic control")
    ax.set_xticks(x, [f"Dec {y}-Sep {(y + 1) % 100:02d}" for y in yrs], fontsize=7)
    ax.get_xticklabels()[len(K.DID_PRE_YEARS)].set_fontweight("bold")
    ax.set_ylabel("Dec-Sep total ($M)")
    ax.set_title("Dec-Sep window totals (bold = closure; earlier windows in-sample)", loc="left",
                 fontsize=10, color=INK)
    ax.legend(frameon=False, ncol=2, loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def winchester_shift(r5, r6, path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9))
    _obs_cf(axes[0], r5, "Waldport-Winchester Bay unit")
    axes[0].set_title("Receiver unit vs synthetic control", loc="left", fontsize=10, color=INK)
    _obs_cf(axes[1], r6, "Charleston + WB unit")
    axes[1].set_title("Charleston + receiver unit combined", loc="left", fontsize=10, color=INK)
    for ax in axes:
        ax.tick_params(axis="x", labelsize=7)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def placebo_distribution(ps1, tp1, r_did, ps5, ps6, path):
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    for ax, ps, title in [(axes[0], ps1, "Charleston (E1)"), (axes[1], ps5, "WB unit (E5) / combined (E6)")]:
        p = ps.sort_values("during_pct")
        ax.barh(np.arange(len(p)), p.during_pct * 100, height=0.7,
                color=[BLUE if t else GRAY for t in p.is_treated])
        ax.set_yticks(np.arange(len(p)), [u.replace("OR-ODFW-", "").replace("OR-", "") for u in p.unit_id],
                      fontsize=7)
        ax.axvline(0, color=MUTED, lw=0.8)
        ax.set_xlabel("Dec-Sep gap vs synthetic (%)")
        ax.set_title(f"Placebo-in-space: {title}", loc="left", fontsize=10, color=INK)
    a6 = ps6[ps6.is_treated].during_pct.iloc[0] * 100
    axes[1].axvline(a6, color=ORANGE, lw=1.5, ls="--")
    axes[1].text(a6, 1.0, " combined", transform=axes[1].get_xaxis_transform(), va="top", fontsize=7,
                 color=ORANGE)
    ax = axes[2]
    labels = list(tp1.fake_event) + ["2019-12\n(actual)"]
    vals = list(tp1.during_pct * 100)
    actual = ps1[ps1.is_treated].during_pct.iloc[0] * 100
    ax.bar(range(len(vals)), vals, width=0.7,
           color=[GRAY if t == "pre" else "#c9c9c4" for t in tp1.timing], label="SC fake event")
    ax.bar(len(vals), actual, color=BLUE, width=0.7, label="SC actual")
    did = {**{y: v for y, v in r_did["placebos"].items()}, **{y: v for y, v in r_did["post_placebos"].items()}}
    dv = [np.exp(did.get(int(l[:4]), np.nan)) * 100 - 100 for l in tp1.fake_event]
    ax.plot(range(len(dv)), dv, ls="none", marker="o", ms=6, color=INK, label="DiD fake window")
    ax.plot(len(vals), r_did["effect_pct"] * 100, ls="none", marker="o", ms=8, mfc=BLUE, mec=INK)
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=7)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_ylabel("Dec-Sep gap (%)")
    ax.set_title("Placebo-in-time\n(light = after-period fake events)", loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, fontsize=7, loc="lower left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def make_all(S, r1, ps1, tp1, r2, r5, r6, ps5, ps6):
    pre = K.OUT_PREFIX
    treated_vs_counterfactual(r1, r2, K.FIGS / f"{pre}_treated_vs_counterfactual.png")
    winchester_shift(r5, r6, K.FIGS / f"{pre}_winchester_shift.png")
    placebo_distribution(ps1, tp1, r2, ps5, ps6, K.FIGS / f"{pre}_placebo_distribution.png")
