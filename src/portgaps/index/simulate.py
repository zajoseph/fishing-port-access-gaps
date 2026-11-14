"""Facility-removal simulation for the T3.2 index.

Facility = harbor x service whose current status counts as working.
Access: harbor h has service s at threshold T if some working s-facility lies
within T charted-equivalent nm (h itself at distance 0).
Remove one facility at a time; the harbors that had access and lose it are
"cut off"; their landed value (lower, upper; see values.set_value) is the
facility's stranded value.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C
from .values import set_value


def load_status() -> pd.DataFrame:
    f = pd.read_csv(C.PROC / "facilities.csv", dtype={"as_of_date": str})
    # current status = latest as_of_date row per port x service (string sort;
    # docs/data_dictionary.md section 5)
    cur = (f.assign(_k=f.as_of_date).sort_values("_k", kind="mergesort")
             .groupby(["port_id", "service"], as_index=False).tail(1)
             .drop(columns="_k").reset_index(drop=True))
    assert len(cur) == 58 * 4
    return cur


def load_distance(port_ids: list[str]) -> pd.DataFrame:
    d = pd.read_csv(C.PROC / "distance_matrix.csv")
    d["cnm"] = d.sea_nm * C.CHART_FACTOR
    D = d.pivot(index="from_port_id", columns="to_port_id", values="cnm").reindex(index=port_ids, columns=port_ids)
    D = D.copy()
    for p in port_ids:
        D.loc[p, p] = 0.0
    assert not D.isna().any().any()
    return D


def run(cur: pd.DataFrame, D: pd.DataFrame, hv: pd.DataFrame, units: dict, *,
        threshold: float, working: tuple[str, ...] = ("available",),
        drop: set[str] = frozenset(), run_name: str = "main") -> pd.DataFrame:
    keep = [p for p in D.index if p not in drop]
    Dk = D.loc[keep, keep]
    unit_of = dict(zip(hv.port_id, hv.unit_id))
    hvi = hv.set_index("port_id")
    st = cur.set_index(["port_id", "service"])
    rows = []
    for s in C.SERVICES:
        stat = {p: st.loc[(p, s), "status"] for p in keep}
        conf = {p: st.loc[(p, s), "confidence"] for p in keep}
        fac = [p for p in keep if stat[p] in working]
        reach = Dk.loc[:, fac].values <= threshold + 1e-9          # harbors x facilities
        n_reach = reach.sum(axis=1)
        has = n_reach > 0
        for j, g in enumerate(fac):
            cut_mask = has & reach[:, j] & (n_reach == 1)
            cut = [keep[i] for i in np.where(cut_mask)[0]]
            low, high = set_value(set(cut), units, unit_of) if cut else (0.0, 0.0)
            # does any cut harbor's lost access rest on a missing-evidence cell?
            nf_backup = lc_backup = it_pairs = 0
            for h in cut:
                near = [p for p in keep if p != g and Dk.loc[h, p] <= threshold + 1e-9]
                if any(stat[p] == "not_found" for p in near):
                    nf_backup += 1
                if any(stat[p] in ("not_available", "closed") and conf[p] == "low" for p in near):
                    lc_backup += 1
            rows.append({
                "run": run_name, "threshold_nm": threshold, "service": s,
                "facility_id": f"{g}|{s}", "harbor": g,
                "harbor_name": hvi.loc[g, "port_name"], "state": hvi.loc[g, "state"],
                "cell_status": stat[g], "cell_confidence": conf[g],
                "cell_as_of_date": st.loc[(g, s), "as_of_date"],
                "stranded_low": round(low), "stranded_high": round(high),
                "n_harbors_cut_off": len(cut), "harbors_cut_off": ";".join(cut),
                "n_cut_lower_bound_value": int(sum(hvi.loc[h, "lower_bound_withheld"] == "Y" for h in cut)),
                "n_cut_heavily_withheld": int(sum(hvi.loc[h, "heavily_withheld"] == "Y" for h in cut)),
                "n_cut_value_range": int(sum(hvi.loc[h, "shared_unit"] == "Y" for h in cut)),
                "n_cut_with_not_found_cell_in_reach": nf_backup,
                "n_cut_with_lowconf_absence_in_reach": lc_backup,
                "n_harbors_without_access_baseline": int((~has).sum()),
            })
    out = pd.DataFrame(rows)
    return add_ranks(out)


def _rank_min(df: pd.DataFrame, a: str, b: str) -> np.ndarray:
    """Rank rows by (a desc, b desc); equal (a, b) pairs share the lowest rank."""
    key = list(zip(df[a], df[b]))
    srt = sorted(set(key), reverse=True)
    counts = pd.Series(key).value_counts()
    pos, n = {}, 0
    for k in srt:
        pos[k] = n + 1
        n += int(counts[k])
    return np.array([pos[k] for k in key], dtype=int)


def add_ranks(df: pd.DataFrame) -> pd.DataFrame:
    """Primary rank: stranded_low desc, ties broken by stranded_high desc; equal
    pairs share the lowest rank number ('min'). rank_service_by_high ranks on
    stranded_high first."""
    df = df.copy()
    for col, grp, a, b in [("rank_overall", ["run", "threshold_nm"], "stranded_low", "stranded_high"),
                           ("rank_service", ["run", "threshold_nm", "service"], "stranded_low", "stranded_high"),
                           ("rank_service_by_high", ["run", "threshold_nm", "service"], "stranded_high", "stranded_low")]:
        df[col] = 0
        for _, idx in df.groupby(grp).groups.items():
            df.loc[idx, col] = _rank_min(df.loc[idx], a, b)
    return df
