"""T3.2b target list: facility cells that drive the failure-index top 10.

Selection (task brief T3.2b):
  * Drivers = main-run facilities with stranded value > 0 (low or high) that sit
    in the per-service top 10 at any threshold 25-50 nm (25, 30, 40, 50).
  * (a) the driver's own cell if its confidence is low;
  * (b) every not_found or low-confidence not_available/closed cell for the same
    service at a harbor within the threshold of a harbor the driver cuts off
    (the cut harbor's own cell included) - the same test simulate.run() uses for
    n_cut_with_not_found_cell_in_reach / n_cut_with_lowconf_absence_in_reach.
Dependency ranking:
  * (b) cells: flip the one cell to "available", rerun the main simulation at
    each threshold, and sum the drop in stranded_low / stranded_high over the
    driver facilities linked to it; keep the largest threshold total.
  * (a) cells: the driver's own stranded value (max over 25-50 nm), since the
    whole entry disappears if the facility is not really there.
  * Also reported: whether the linked driver falls to $0 under s1.
Methods, thresholds and values are T3.2's, unchanged. Read-only: writes only
outputs/tables/t32b_targets.csv.

Run: python -I src/portgaps/index/targets_t32b.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from portgaps.index import config as C
from portgaps.index.simulate import load_status, load_distance, run
from portgaps.index.values import build_values

BAND = [25, 30, 40, 50]
KNOWN_OPEN = {  # brief: always include if they appear
    ("WA-westport", "hoist_crane"), ("OR-florence", "ice"), ("WA-tokeland", "fuel"),
    ("CA-noyo-harbor", "ice"), ("WA-chinook", "ice"), ("OR-bandon", "ice"),
    ("OR-bandon", "cold_storage"), ("OR-gold-beach", "ice"), ("OR-gold-beach", "cold_storage"),
}


def main() -> None:
    rk = pd.read_csv(C.TABLES / "index_ranking.csv")
    sens = pd.read_csv(C.TABLES / "index_sensitivity.csv")
    hv, units = build_values()
    cur = load_status()
    D = load_distance(list(hv.port_id))
    st = cur.set_index(["port_id", "service"])
    name = dict(zip(hv.port_id, hv.port_name))

    drv = rk[rk.threshold_nm.isin(BAND) & (rk.rank_service <= 10)
             & ((rk.stranded_low > 0) | (rk.stranded_high > 0))].copy()
    s1 = sens[sens.run == "s1_not_found_as_available"].set_index(["threshold_nm", "facility_id"])
    drv["s1_low"] = [s1.loc[(t, f), "stranded_low"] for t, f in zip(drv.threshold_nm, drv.facility_id)]
    drv["s1_high"] = [s1.loc[(t, f), "stranded_high"] for t, f in zip(drv.threshold_nm, drv.facility_id)]
    drv["s1_zero"] = (drv.s1_low == 0) & (drv.s1_high == 0)
    drivers = sorted(drv.facility_id.unique())

    # candidate cells -> linked driver facilities
    links: dict[tuple, set] = {}
    kind: dict[tuple, set] = {}
    for r in drv.itertuples():
        s, g, T = r.service, r.harbor, r.threshold_nm
        if r.cell_confidence == "low":
            links.setdefault((g, s), set()).add(r.facility_id)
            kind.setdefault((g, s), set()).add("a_removed_cell_low_conf")
        for h in filter(None, str(r.harbors_cut_off).split(";")):
            for p in D.index:
                if p == g or D.loc[h, p] > T + 1e-9:
                    continue
                stat, conf = st.loc[(p, s), "status"], st.loc[(p, s), "confidence"]
                if stat == "not_found" or (stat in ("not_available", "closed") and conf == "low"):
                    links.setdefault((p, s), set()).add(r.facility_id)
                    kind.setdefault((p, s), set()).add("b_backup_gap")

    # baseline main run at band thresholds
    base = {T: run(cur, D, hv, units, threshold=T).set_index("facility_id") for T in BAND}

    rows = []
    for (p, s), facs in links.items():
        kinds = kind[(p, s)]
        best_low = best_high = 0.0
        best_T = None
        if "b_backup_gap" in kinds:
            alt = cur.copy()
            m = (alt.port_id == p) & (alt.service == s)
            alt.loc[m, "status"] = "available"
            for T in BAND:
                a = run(alt, D, hv, units, threshold=T).set_index("facility_id")
                # only drivers that are top-10 at this T count
                top = set(drv.loc[drv.threshold_nm == T, "facility_id"]) & facs
                dl = sum(base[T].loc[f, "stranded_low"] - (a.loc[f, "stranded_low"] if f in a.index else 0) for f in top)
                dh = sum(base[T].loc[f, "stranded_high"] - (a.loc[f, "stranded_high"] if f in a.index else 0) for f in top)
                if (dl, dh) > (best_low, best_high):
                    best_low, best_high, best_T = dl, dh, T
        if "a_removed_cell_low_conf" in kinds:
            own = drv[drv.facility_id == f"{p}|{s}"]
            ol, oh = own.stranded_low.max(), own.stranded_high.max()
            if (ol, oh) > (best_low, best_high):
                best_low, best_high = ol, oh
                best_T = int(own.loc[own.stranded_low.idxmax(), "threshold_nm"])
        linked = drv[drv.facility_id.isin(facs)]
        s1z = sorted(linked.loc[linked.s1_zero, "facility_id"].unique())
        rows.append({
            "port_id": p, "port_name": name[p], "service": s,
            "target_type": ";".join(sorted(kinds)),
            "cell_status": st.loc[(p, s), "status"], "cell_confidence": st.loc[(p, s), "confidence"],
            "cell_as_of_date": st.loc[(p, s), "as_of_date"],
            "dependent_value_low": round(best_low), "dependent_value_high": round(best_high),
            "at_threshold_nm": best_T,
            "n_linked_drivers": len(facs), "linked_drivers": ";".join(sorted(facs)),
            "linked_drivers_zero_under_s1": ";".join(s1z),
            "known_open_cell": "Y" if (p, s) in KNOWN_OPEN else "",
        })
    # Known open cells that are top-10 drivers but miss rules (a)/(b) (medium
    # confidence), and cells the user added (T3.2b chat, 2026-11-14).
    extra = {("CA-noyo-harbor", "ice"): "c_known_open_driver",
             ("WA-chinook", "ice"): "c_user_added"}
    for (p, s), why in extra.items():
        if (p, s) in links:
            continue
        own = drv[drv.facility_id == f"{p}|{s}"]
        rows.append({
            "port_id": p, "port_name": name[p], "service": s, "target_type": why,
            "cell_status": st.loc[(p, s), "status"], "cell_confidence": st.loc[(p, s), "confidence"],
            "cell_as_of_date": st.loc[(p, s), "as_of_date"],
            "dependent_value_low": round(own.stranded_low.max()) if len(own) else 0,
            "dependent_value_high": round(own.stranded_high.max()) if len(own) else 0,
            "at_threshold_nm": int(own.loc[own.stranded_low.idxmax(), "threshold_nm"]) if len(own) else None,
            "n_linked_drivers": len(own.facility_id.unique()),
            "linked_drivers": ";".join(sorted(own.facility_id.unique())),
            "linked_drivers_zero_under_s1": ";".join(sorted(own.loc[own.s1_zero, "facility_id"].unique())),
            "known_open_cell": "Y",
        })
    out = pd.DataFrame(rows).sort_values(["dependent_value_low", "dependent_value_high"],
                                         ascending=False).reset_index(drop=True)
    out.insert(0, "target_rank", range(1, len(out) + 1))
    # User choice (T3.2b chat): check the top 40 by dependency plus the extras.
    out["selected_for_check"] = ["Y" if (r <= 40 or t.startswith("c_")) else ""
                                 for r, t in zip(out.target_rank, out.target_type)]
    out.to_csv(C.TABLES / "t32b_targets.csv", index=False)
    drv.to_csv(C.INTERIM / "t32b_drivers.csv", index=False)
    print(f"drivers: {len(drivers)} facilities; targets: {len(out)} cells")
    missing = [k for k in KNOWN_OPEN if k not in links]
    print("known open cells not in target list:", missing)


if __name__ == "__main__":
    main()
