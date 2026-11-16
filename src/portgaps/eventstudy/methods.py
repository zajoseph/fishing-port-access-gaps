"""Estimators: synthetic control on scaled monthly series, window-total DiD,
and permutation inference (placebo-in-space, placebo-in-time)."""
import numpy as np
import pandas as pd
from scipy.optimize import nnls

from . import config as C


def months_between(a: int, b: int, index) -> list:
    return [m for m in index if a <= m <= b]


def shift_ym(ym: int, years: int) -> int:
    return ym + 100 * years


# ---------------------------------------------------------------------------
# Synthetic control
# ---------------------------------------------------------------------------
def sc_weights(A: np.ndarray, b: np.ndarray, lam: float = 1e4) -> np.ndarray:
    """min ||A w - b||^2  s.t. w >= 0, sum(w) = 1  (NNLS with a heavily weighted
    adding-up row; exact enough for weights to 1e-6)."""
    scale = np.sqrt(lam) * max(1.0, np.abs(A).max())
    A2 = np.vstack([A, scale * np.ones((1, A.shape[1]))])
    b2 = np.concatenate([b, [scale]])
    w, _ = nnls(A2, b2, maxiter=50 * A.shape[1])
    s = w.sum()
    return w / s if s > 0 else np.full(A.shape[1], 1 / A.shape[1])


def sc_fit(y1: pd.Series, Y0: pd.DataFrame, pre_end: int, windows: dict,
           pre_start: int = C.PANEL_START, data_end: int = C.PANEL_END,
           exclude_months=()) -> dict:
    """Fit SC on months pre_start..pre_end where treated and every donor are
    observed. Each series is divided by its own mean over the fit months, so the
    weights match shape, not size; the counterfactual is rescaled to the treated
    unit's dollars (or pounds).

    windows: {"during": (a, b), "after": (a, b), ...} evaluated as sums.
    """
    idx = [m for m in y1.index if pre_start <= m <= data_end]
    y1 = y1.reindex(idx)
    Y0 = Y0.reindex(idx)
    pre = [m for m in idx if m <= pre_end and m not in exclude_months]
    fit = [m for m in pre if np.isfinite(y1[m]) and Y0.loc[m].notna().all()]
    m1 = y1[fit].mean()
    m0 = Y0.loc[fit].mean()
    keep = m0[m0 > 0].index  # a donor with zero mean has no shape to match
    Y0 = Y0[keep]
    m0 = m0[keep]
    s1 = y1 / m1
    S0 = Y0 / m0
    w = sc_weights(S0.loc[fit].values, s1[fit].values)
    wser = pd.Series(w, index=keep)
    used = wser[wser > 1e-6].index
    synth_s = (S0[used] * wser[used]).sum(axis=1, min_count=len(used))
    synth_s = synth_s.where(S0[used].notna().all(axis=1))
    cf = synth_s * m1
    gap_s = s1 - synth_s
    out = {
        "weights": wser,
        "n_fit_months": len(fit),
        "pre_mean": m1,
        "treated": y1,
        "counterfactual": cf,
        "pre_rmspe": float(np.sqrt(np.mean(gap_s[fit] ** 2))),
        "pre_months_excluded": len(pre) - len(fit),
    }
    for name, (a, b) in windows.items():
        ms = months_between(a, b, idx)
        obs, syn = y1[ms], cf[ms]
        ok = obs.notna() & syn.notna()
        out[f"{name}_n"] = int(ok.sum())
        out[f"{name}_n_missing"] = int((~ok).sum())
        out[f"{name}_obs"] = float(obs[ok].sum())
        out[f"{name}_cf"] = float(syn[ok].sum())
        out[f"{name}_gap"] = out[f"{name}_obs"] - out[f"{name}_cf"]
        out[f"{name}_pct"] = (out[f"{name}_obs"] / out[f"{name}_cf"] - 1
                              if out[f"{name}_cf"] > 0 else np.nan)
        out[f"{name}_rmspe"] = float(np.sqrt(np.mean(gap_s[ms][ok] ** 2))) if ok.any() else np.nan
        out[f"{name}_ratio"] = out[f"{name}_rmspe"] / out["pre_rmspe"]
    return out


def placebo_in_space(series: dict, treated: str, donors: list, pre_end: int,
                     windows: dict, **fit_kw) -> pd.DataFrame:
    """Refit with each donor as the 'treated' unit (the real treated unit is
    never a donor). p-values: share of units (incl. treated) whose statistic is
    at least as extreme as the treated unit's. ``fit_kw`` (pre_start, data_end,
    exclude_months) is passed to sc_fit; T4.1 passes none."""
    rows = []
    for u in [treated] + donors:
        pool = [d for d in donors if d != u]
        r = sc_fit(series[u], pd.DataFrame({d: series[d] for d in pool}), pre_end, windows,
                   **fit_kw)
        row = {"unit_id": u, "is_treated": u == treated, "pre_rmspe": r["pre_rmspe"]}
        for name in windows:
            row[f"{name}_pct"] = r[f"{name}_pct"]
            row[f"{name}_ratio"] = r[f"{name}_ratio"]
        rows.append(row)
    df = pd.DataFrame(rows)
    return df


def perm_p(stat_treated: float, stats_all: pd.Series, two_sided=True) -> float:
    s = stats_all.dropna()
    if two_sided:
        return float((s.abs() >= abs(stat_treated) - 1e-12).mean())
    return float((s >= stat_treated - 1e-12).mean())


def placebo_in_time_sc(y1, Y0, years, during_len_months=11, m_start=10, m_end=8,
                       exclude_months=()) -> pd.DataFrame:
    """Fake event in month ``m_start`` of each year in ``years`` (T4.1: October);
    fit on data before it, evaluate the window through month ``m_end`` (next
    year if m_end < m_start), use no data after the fake window. Months in
    ``exclude_months`` (e.g. a real closure, for fake events placed after it)
    are left out of the fit."""
    rows = []
    for y in years:
        a = y * 100 + m_start
        b = (y + 1 if m_end < m_start else y) * 100 + m_end
        pre_end = a - 1 if m_start > 1 else (y - 1) * 100 + 12
        r = sc_fit(y1, Y0, pre_end=pre_end, windows={"during": (a, b)}, data_end=b,
                   exclude_months=exclude_months)
        rows.append({"fake_event": f"{y}-{m_start:02d}", "pre_rmspe": r["pre_rmspe"],
                     "during_pct": r["during_pct"], "during_ratio": r["during_ratio"],
                     "n_fit_months": r["n_fit_months"]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Window-total DiD
# ---------------------------------------------------------------------------
def window_months(y: int, m_start=10, m_end=8) -> list:
    a, b = y * 100 + m_start, (y + 1 if m_end < m_start else y) * 100 + m_end
    out, m = [], a
    while m <= b:
        out.append(m)
        m = m + 1 if m % 100 < 12 else (m // 100 + 1) * 100 + 1
    return out


def paired_window_totals(t: pd.Series, k: pd.Series, start_years, m_start=10, m_end=8,
                         drop_months=()):
    """Window sums for treated t and control k over the months where BOTH are
    observed (pairwise deletion; nothing is imputed). Returns (T, K, n_dropped)."""
    T, K, N = {}, {}, {}
    for y in start_years:
        ms = [m for m in window_months(y, m_start, m_end) if m not in drop_months]
        tt, kk = t.reindex(ms), k.reindex(ms)
        ok = tt.notna() & kk.notna()
        T[y], K[y], N[y] = float(tt[ok].sum()), float(kk[ok].sum()), int((~ok).sum())
    return pd.Series(T), pd.Series(K), pd.Series(N)


def window_did(treated: pd.Series, control: pd.Series, pre_years=C.WINDOW_START_YEARS_PRE,
               event_year=C.EVENT_WINDOW_YEAR, m_start=10, m_end=8, drop_months=()) -> dict:
    """log(treated window total / control window total), event window minus the
    mean of pre windows. Inference = placebo-in-time over the pre windows."""
    yrs = list(pre_years) + [event_year]
    T, K, N = paired_window_totals(treated, control, yrs, m_start, m_end, drop_months)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.log(T / K).replace([np.inf, -np.inf], np.nan)
    pre = r[list(pre_years)].dropna()
    eff = r[event_year] - pre.mean()
    plac = pd.Series({k: pre[k] - pre.drop(k).mean() for k in pre.index})
    allstats = pd.concat([plac, pd.Series({event_year: eff})])
    cf = K[event_year] * np.exp(pre.mean())
    return {
        "effect_log": float(eff), "effect_pct": float(np.exp(eff) - 1),
        "obs": float(T[event_year]), "cf": float(cf), "gap": float(T[event_year] - cf),
        "n_pre_windows": int(len(pre)), "pre_sd_log": float(pre.std(ddof=1)),
        "p_time": perm_p(eff, allstats),
        "months_dropped_event": int(N[event_year]),
        "months_dropped_pre": int(N[list(pre_years)].sum()),
        "placebos": plac, "ratios": r, "treated_totals": T, "control_totals": K,
    }
