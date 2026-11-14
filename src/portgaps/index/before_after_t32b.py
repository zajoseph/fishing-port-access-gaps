"""T3.2b before/after comparison of the failure index.

Before = T3.2 tables saved to data/interim/t32b_before/ (main after PR #6)
before facilities.csv was updated. After = current outputs/tables.
Top 10 per service (rank_service <= 10, stranded value > 0) at 25, 30, 40, 50 nm.
Writes outputs/tables/t32b_index_before_after.csv (entry level) and prints a
summary per threshold x service.

Run: python -I src/portgaps/index/before_after_t32b.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
T = ROOT / "outputs" / "tables"
B = ROOT / "data" / "interim" / "t32b_before"
BAND = [25, 30, 40, 50]


def top10(rk: pd.DataFrame, sens: pd.DataFrame) -> pd.DataFrame:
    s1 = sens[sens.run == "s1_not_found_as_available"].set_index(["threshold_nm", "facility_id"])
    d = rk[rk.threshold_nm.isin(BAND) & (rk.rank_service <= 10)
           & ((rk.stranded_low > 0) | (rk.stranded_high > 0))].copy()
    d["rests_on_weak_cell"] = ((d.cell_confidence == "low") | (d.n_cut_with_not_found_cell_in_reach > 0)
                               | (d.n_cut_with_lowconf_absence_in_reach > 0))
    d["zero_under_s1"] = [(s1.loc[(t, f), "stranded_low"] == 0) and (s1.loc[(t, f), "stranded_high"] == 0)
                          for t, f in zip(d.threshold_nm, d.facility_id)]
    return d[["threshold_nm", "service", "facility_id", "rank_service", "stranded_low", "stranded_high",
              "cell_confidence", "rests_on_weak_cell", "zero_under_s1"]]


def main() -> None:
    b = top10(pd.read_csv(B / "index_ranking.csv"), pd.read_csv(B / "index_sensitivity.csv"))
    a = top10(pd.read_csv(T / "index_ranking.csv"), pd.read_csv(T / "index_sensitivity.csv"))
    m = b.merge(a, on=["threshold_nm", "service", "facility_id"], how="outer", suffixes=("_before", "_after"))
    m["in_top10"] = m.rank_service_before.notna().map({True: "B", False: ""}) + \
        m.rank_service_after.notna().map({True: "A", False: ""})
    m["change"] = m.in_top10.map({"BA": "stays", "B": "drops_out", "A": "enters"})
    m = m.sort_values(["threshold_nm", "service", "rank_service_after", "rank_service_before"])
    m.to_csv(T / "t32b_index_before_after.csv", index=False)

    rows = []
    for (t, s), g in m.groupby(["threshold_nm", "service"]):
        gb, ga = g[g.in_top10.str.contains("B")], g[g.in_top10.str.contains("A")]
        rows.append({"threshold_nm": t, "service": s, "n_before": len(gb), "n_after": len(ga),
                     "weak_before": int(gb.rests_on_weak_cell_before.sum()),
                     "weak_after": int(ga.rests_on_weak_cell_after.sum()),
                     "s1_zero_before": int(gb.zero_under_s1_before.sum()),
                     "s1_zero_after": int(ga.zero_under_s1_after.sum()),
                     "entered": ";".join(g.loc[g.change == "enters", "facility_id"]),
                     "dropped": ";".join(g.loc[g.change == "drops_out", "facility_id"])})
    summ = pd.DataFrame(rows)
    tot = summ[["n_before", "n_after", "weak_before", "weak_after", "s1_zero_before", "s1_zero_after"]].sum()
    pd.set_option("display.width", 250, "display.max_colwidth", 80)
    print(summ.to_string(index=False))
    print("TOTAL", tot.to_dict())


if __name__ == "__main__":
    main()
