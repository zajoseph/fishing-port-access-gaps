"""Monthly series for the event study, read from data/processed/landings_monthly.csv.

Rules (decisions log): withheld cells stay null and are never imputed;
no_record_zero = 0; ODFW blanks = 0 by documented assumption unless
``blanks_missing=True`` (then blank_assumed_zero -> null and
part_blank_assumed_zero kept as a lower bound, flagged). Shared/group units are
never split; aggregates are sums of whole agency units and are null in any month
where a component is null.
"""
from functools import lru_cache
import numpy as np
import pandas as pd

from . import config as C

MONTHS = [y * 100 + m for y in range(2016, 2026) for m in range(1, 13)]


@lru_cache(maxsize=1)
def landings() -> pd.DataFrame:
    df = pd.read_csv(C.PROC / "landings_monthly.csv")
    df["ym"] = df.year * 100 + df.month
    df = df[(df.ym >= C.PANEL_START) & (df.ym <= C.PANEL_END)]
    return df


def _unit_rows(unit: str, scheme: str) -> pd.DataFrame:
    df = landings()
    q = df[df.unit_id == unit]
    if scheme == "all":
        q = q[q.species_scheme == "all"]
    elif scheme == "crab":
        q = q[(q.species_scheme == C.CRAB) & (q.species_group == C.CRAB)]
    else:
        raise ValueError(scheme)
    if q.ym.duplicated().any():
        raise AssertionError(f"duplicate months for {unit} {scheme}")
    return q.set_index("ym")


def unit_series(unit: str, measure: str = "value_usd", scheme: str = "all",
                blanks_missing: bool = False) -> tuple[pd.Series, pd.Series]:
    """Return (values, flags) for one agency unit; months outside the unit's
    coverage are NaN with flag 'not_covered'."""
    if scheme == "noncrab":
        a, fa = unit_series(unit, measure, "all", blanks_missing)
        c, fc = unit_series(unit, measure, "crab", blanks_missing)
        v = a - c  # NaN if either is NaN
        f = fa.where(fa != "none", fc)
        return v, f
    q = _unit_rows(unit, scheme)
    v = q[measure].astype(float).reindex(MONTHS)
    f = q["withheld_flag"].reindex(MONTHS).fillna("not_covered")
    if blanks_missing:
        v = v.mask(f == "blank_assumed_zero")
    return v, f


def agg_series(spec, measure="value_usd", scheme="all", blanks_missing=False):
    """Sum of whole units. ``spec`` is a list of unit_ids or a dict
    {'pre2025': [...], '2025': [...]} for units that change in 2025."""
    if isinstance(spec, str):
        return unit_series(spec, measure, scheme, blanks_missing)
    if isinstance(spec, dict):
        parts = []
        for key, units in spec.items():
            months = [m for m in MONTHS if (m < 202501) == (key == "pre2025")]
            v, f = agg_series(list(units), measure, scheme, blanks_missing)
            parts.append((v.reindex(months), f.reindex(months)))
        v = pd.concat([p[0] for p in parts]).reindex(MONTHS)
        f = pd.concat([p[1] for p in parts]).reindex(MONTHS)
        return v, f
    vs, fs = zip(*(unit_series(u, measure, scheme, blanks_missing) for u in spec))
    V = pd.concat(vs, axis=1)
    v = V.sum(axis=1, min_count=len(spec)).where(V.notna().all(axis=1))
    F = pd.concat(fs, axis=1)

    def worst(row):
        s = [x for x in row if x != "none"]
        return ";".join(sorted(set(s))) if s else "none"
    f = F.apply(worst, axis=1)
    return v, f


def ca_harbors() -> list[str]:
    df = landings()
    return sorted(df[(df.state == "CA") & (df.unit_type == "harbor")].unit_id.unique())


def pre_null_share(unit: str) -> float:
    v, _ = unit_series(unit)
    pre = v[v.index <= C.PRE_END]
    return float(pre.isna().mean())


def donor_pool(scheme: str = "all", log: list | None = None) -> list[str]:
    """Main CA donor pool with documented exclusions (reasons appended to log)."""
    out = []
    for u in ca_harbors():
        reason = None
        if u == C.TREATED:
            continue
        if u in C.EXCLUDE_RECEIVERS:
            reason = "possible receiver (spillover buffer; user answer)"
        elif u in C.EXCLUDE_OWN_EVENT:
            reason = "own facility outage in window (hoist 2025-10-18 to 2026-01-29)"
        elif pre_null_share(u) >= C.HEAVY_NULL_SHARE:
            reason = f"heavily withheld ({pre_null_share(u):.0%} of pre months null)"
        else:
            v, _ = unit_series(u)
            win = v[(v.index >= C.DURING[0]) & (v.index <= C.AFTER[1])]
            if win.isna().any():
                reason = f"null month(s) in 2024-10..2025-12: {list(win[win.isna()].index)}"
        if reason is None and scheme == "crab":
            c, _ = unit_series(u, scheme="crab")
            pre = c[c.index <= C.PRE_END]
            annual = pre.mean() * 12
            if not np.isfinite(annual) or annual < C.CRAB_DONOR_MIN_ANNUAL_USD:
                reason = f"crab donor screen: mean annual pre crab ${annual:,.0f} < $100k"
            else:
                win = c[(c.index >= C.DURING[0]) & (c.index <= C.AFTER[1])]
                if win.isna().any():
                    reason = f"null crab month(s) in 2024-10..2025-12: {list(win[win.isna()].index)}"
        if reason:
            if log is not None:
                log.append({"scheme": scheme, "unit_id": u, "excluded_reason": reason})
        else:
            out.append(u)
    return out
