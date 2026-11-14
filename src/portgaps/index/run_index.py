"""Run the T3.2 failure index: main run over the threshold sweep, three
sensitivity runs at every threshold, stability, flags and checks.

    python -I -m src.portgaps.index.run_index        (from the repo root)
    PORTGAPS_ROOT=/path/to/repo python -I -m src.portgaps.index.run_index
"""
from __future__ import annotations

import json
import random
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)  # spearman on all-zero columns

import numpy as np
import pandas as pd

from . import config as C
from .simulate import load_distance, load_status, run
from .values import build_values, set_value

RUNS = {
    "main": dict(working=("available",), drop_key=None),
    "s1_not_found_as_available": dict(working=("available", "not_found"), drop_key=None),
    "s2_no_marina_only": dict(working=("available",), drop_key="marina_only"),
    "s3_no_heavily_withheld": dict(working=("available",), drop_key="heavily_withheld"),
}

DOCUMENTED_BACKUPS = [
    # (harbor that lost or lacked the service, backup harbor, service, mode, what the inventory says)
    ("CA-crescent-city", "OR-brookings", "ice", "truck",
     "Oct 2024-Aug 2025 closure: ice trucked from Pacific Seafood's Brookings plant (facilities.csv notes)"),
    ("CA-santa-barbara", "CA-channel-islands", "ice", "truck",
     "Ice House overhaul (<4 weeks): ice deliveries from Oxnard (facilities.csv notes); Oxnard = Channel Islands/Port Hueneme"),
    ("CA-santa-barbara", "CA-port-hueneme", "ice", "truck", "as above (Oxnard)"),
    ("CA-trinidad", "CA-humboldt-bay", "fuel", "truck",
     "Pier fuel dock removed (2010 profile): nearest vendor Renner Petroleum, McKinleyville (road)"),
    ("CA-point-arena", "CA-noyo-harbor", "hoist_crane", "unknown",
     "Hoist out 2025-10-18 to 2026-01-29; nearest harbor with a hoist (no documented run; T3.3 validates)"),
    ("OR-charleston", "OR-winchester-bay", "ice", "unknown",
     "Ice plant fire 2019-12-20 to 2020-09-12; backup used not documented in the inventory"),
    ("OR-charleston", "OR-newport", "ice", "unknown", "as above"),
    ("WA-ilwaco", "WA-chinook", "hoist_crane", "unknown",
     "Ilwaco Landing dock and cranes closed 2024-01-22; backup used not documented in the inventory"),
    ("WA-ilwaco", "OR-astoria", "ice", "unknown", "Ilwaco ice closed 2024-01-22; backup used not documented"),
]


def bar_crossing_routes() -> set[frozenset]:
    g = json.load(open(C.INTERIM / "sea_routes.geojson"))
    hits = set()
    for f in g["features"]:
        c = f["geometry"]["coordinates"]
        for (x1, y1), (x2, y2) in zip(c[:-1], c[1:]):
            for t in C.INTERTIDAL_TESTS.values():
                lon = t["lon"]
                if (x1 - lon) * (x2 - lon) < 0:
                    y = y1 + (y2 - y1) * (lon - x1) / (x2 - x1)
                    if t["lat_min"] <= y <= t["lat_max"]:
                        hits.add(frozenset((f["properties"]["port_a"], f["properties"]["port_b"])))
    return hits


def brute_force_check(cur, D, hv, units, T, n=25, seed=7):
    """Independent re-implementation on random facilities (check C5)."""
    rnd = random.Random(seed)
    unit_of = dict(zip(hv.port_id, hv.unit_id))
    cand = cur[cur.status == "available"][["port_id", "service"]].values.tolist()
    res = []
    for g, s in rnd.sample(cand, n):
        work = set(cur[(cur.service == s) & (cur.status == "available")].port_id)
        acc0 = {h for h in D.index if any(D.loc[h, w] <= T for w in work)}
        acc1 = {h for h in D.index if any(D.loc[h, w] <= T for w in work - {g})}
        res.append((f"{g}|{s}", set_value(acc0 - acc1, units, unit_of)))
    return res


def main() -> None:
    C.TABLES.mkdir(parents=True, exist_ok=True)
    hv, units = build_values()
    cur = load_status()
    D = load_distance(list(hv.port_id))
    hv.to_csv(C.TABLES / "index_harbor_values.csv", index=False)

    drops = {k: set(hv.loc[hv[k] == "Y", "port_id"]) for k in ("marina_only", "heavily_withheld")}
    allruns = []
    for name, spec in RUNS.items():
        drop = drops[spec["drop_key"]] if spec["drop_key"] else set()
        for T in C.THRESHOLDS_NM:
            allruns.append(run(cur, D, hv, units, threshold=T, working=spec["working"],
                               drop=drop, run_name=name))
    allr = pd.concat(allruns, ignore_index=True)

    # ---- intertidal / shallow-route flags --------------------------------
    bar = bar_crossing_routes()

    def route_flag(r):
        flags = []
        for h in filter(None, r.harbors_cut_off.split(";")):
            if h != r.harbor and frozenset((h, r.harbor)) in bar:
                flags.append(f"{h}~{r.harbor}:portage_bar")
            elif h != r.harbor and ({h, r.harbor} & C.SHALLOW_BAY_HARBORS):
                flags.append(f"{h}~{r.harbor}:willapa_unverified")
        return ";".join(flags)

    allr["dependency_route_flags"] = allr.apply(route_flag, axis=1)

    # rescue routes: harbor keeps access only through a bar-crossing route
    st = cur.set_index(["port_id", "service"]).status
    resc = []
    for T in C.THRESHOLDS_NM:
        for s in C.SERVICES:
            work = [p for p in D.index if st[(p, s)] == "available"]
            for h in D.index:
                inreach = [w for w in work if D.loc[h, w] <= T]
                if inreach and all(frozenset((h, w)) in bar for w in inreach if w != h) and h not in inreach:
                    resc.append({"threshold_nm": T, "service": s, "harbor": h,
                                 "access_only_via": ";".join(inreach), "route_issue": "portage_bar"})
    rescue = pd.DataFrame(resc, columns=["threshold_nm", "service", "harbor", "access_only_via", "route_issue"])

    # ---- confidence flag string -------------------------------------------
    def flags(r):
        f = []
        if r.cell_confidence == "low":
            f.append("low_conf_cell")
        if r.cell_status == "not_found":
            f.append("not_found_cell")
        if r.n_cut_with_not_found_cell_in_reach:
            f.append(f"backup_not_found_x{r.n_cut_with_not_found_cell_in_reach}")
        if r.n_cut_with_lowconf_absence_in_reach:
            f.append(f"backup_lowconf_absence_x{r.n_cut_with_lowconf_absence_in_reach}")
        if r.n_cut_value_range:
            f.append("value_range_shared_unit")
        if r.n_cut_lower_bound_value:
            f.append("value_lower_bound_withheld")
        if r.n_cut_heavily_withheld:
            f.append("heavily_withheld_harbor")
        if r.dependency_route_flags:
            f.append("route_" + ("portage_bar" if "portage_bar" in r.dependency_route_flags else "willapa_unverified"))
        return ";".join(f)

    allr["confidence_flags"] = allr.apply(flags, axis=1)

    cols = ["threshold_nm", "service", "facility_id", "harbor", "harbor_name", "state",
            "stranded_low", "stranded_high", "n_harbors_cut_off", "harbors_cut_off",
            "rank_service", "rank_overall", "rank_service_by_high",
            "cell_status", "cell_confidence", "cell_as_of_date", "confidence_flags",
            "n_cut_lower_bound_value", "n_cut_heavily_withheld", "n_cut_value_range",
            "n_cut_with_not_found_cell_in_reach", "n_cut_with_lowconf_absence_in_reach",
            "dependency_route_flags", "n_harbors_without_access_baseline"]
    main_r = allr[allr.run == "main"][cols].sort_values(["threshold_nm", "rank_overall", "facility_id"])
    main_r.to_csv(C.TABLES / "index_ranking.csv", index=False)

    # ---- sensitivity table ------------------------------------------------
    base = main_r.set_index(["threshold_nm", "facility_id"])[["stranded_low", "stranded_high", "rank_service", "rank_overall"]]
    sens = allr[["run", "threshold_nm", "service", "facility_id", "harbor", "cell_status",
                 "stranded_low", "stranded_high", "n_harbors_cut_off", "rank_service", "rank_overall"]].copy()
    sens = sens.join(base.add_prefix("main_"), on=["threshold_nm", "facility_id"])
    sens["delta_rank_service"] = sens.rank_service - sens.main_rank_service
    sens["delta_rank_overall"] = sens.rank_overall - sens.main_rank_overall
    sens["note"] = np.where(sens.main_rank_service.isna(), "not_in_main_run (not_found cell)", "")
    # facilities removed by a drop run
    dropped = []
    for name, spec in RUNS.items():
        if not spec["drop_key"]:
            continue
        for T in C.THRESHOLDS_NM:
            for fid in main_r[(main_r.threshold_nm == T) & main_r.harbor.isin(drops[spec["drop_key"]])].facility_id:
                dropped.append({"run": name, "threshold_nm": T, "facility_id": fid,
                                "service": fid.split("|")[1], "harbor": fid.split("|")[0],
                                "note": "harbor dropped in this run"})
    sens = pd.concat([sens, pd.DataFrame(dropped)], ignore_index=True)
    # Facilities with zero stranded value share the bottom rank, so a rank
    # number alone can mislead when a value goes to or from zero.
    mz = sens.main_stranded_high.fillna(0) == 0
    rz = sens.stranded_high.fillna(0) == 0
    in_both = sens.main_rank_service.notna() & sens.rank_service.notna()
    sens["change_type"] = np.select(
        [~in_both, mz & rz, ~mz & rz, mz & ~rz,
         sens.delta_rank_service.abs() > C.RANK_FLAG_PLACES],
        ["", "zero_in_both", "drops_to_zero", "rises_from_zero", "rank_move"], default="small_move")
    sens["flag_rank_change"] = np.where(
        sens.change_type.isin(["rank_move", "drops_to_zero", "rises_from_zero"]), "Y", "")
    sens.loc[sens.note.str.startswith("not_in_main", na=False) & (sens.rank_service <= 10) & ~rz, "flag_rank_change"] = "new_top10"
    sens = sens.sort_values(["run", "threshold_nm", "service", "rank_service", "facility_id"])
    sens.to_csv(C.TABLES / "index_sensitivity.csv", index=False)

    # ---- stability across the sweep (main run) ----------------------------
    stab = []
    wide = main_r.pivot(index="facility_id", columns="threshold_nm", values="rank_service")
    lowv = main_r.pivot(index="facility_id", columns="threshold_nm", values="stranded_low")
    svc = main_r.drop_duplicates("facility_id").set_index("facility_id").service
    for s in C.SERVICES:
        ids = svc[svc == s].index
        mm = main_r[(main_r.threshold_nm == C.MID_THRESHOLD_NM) & (main_r.service == s)]
        top_mid = set(mm[mm.stranded_high > 0].nsmallest(10, "rank_service").facility_id)
        prev = None
        for T in C.THRESHOLDS_NM:
            sub = main_r[(main_r.threshold_nm == T) & (main_r.service == s)]
            top = set(sub[sub.stranded_high > 0].nsmallest(10, "rank_service").facility_id)
            rho_mid = lowv.loc[ids, T].rank().corr(lowv.loc[ids, C.MID_THRESHOLD_NM].rank())
            rho_prev = lowv.loc[ids, T].rank().corr(lowv.loc[ids, prev].rank()) if prev else np.nan
            stab.append({"service": s, "threshold_nm": T, "n_facilities": len(sub),
                         "n_nonzero_low": int((sub.stranded_low > 0).sum()),
                         "n_nonzero_high": int((sub.stranded_high > 0).sum()),
                         "total_stranded_low_sum": int(sub.stranded_low.sum()),
                         "max_stranded_low": int(sub.stranded_low.max()),
                         "top_facility": (sub.nsmallest(1, "rank_service").facility_id.iloc[0]
                                          if sub.stranded_high.max() > 0 else ""),
                         "n_top10_nonzero": len(top),
                         "spearman_vs_mid": round(rho_mid, 3) if pd.notna(rho_mid) else "",
                         "spearman_vs_previous": round(rho_prev, 3) if pd.notna(rho_prev) else "",
                         "top10_overlap_with_mid": len(top & top_mid)})
            prev = T
    pd.DataFrame(stab).to_csv(C.TABLES / "index_stability.csv", index=False)
    wide.columns = [f"rank_{c}nm" for c in wide.columns]
    span = wide[[f"rank_{t}nm" for t in C.THRESHOLDS_NM if t <= 100]]
    wide["rank_min_10_100"] = span.min(axis=1)
    wide["rank_max_10_100"] = span.max(axis=1)
    wide.insert(0, "service", svc)
    wide.reset_index().sort_values(["service", f"rank_{C.MID_THRESHOLD_NM}nm"]).to_csv(
        C.TABLES / "index_rank_by_threshold.csv", index=False)

    # ---- key figures: top 10 per service at mid threshold -----------------
    mid = main_r[main_r.threshold_nm == C.MID_THRESHOLD_NM]
    top10 = (mid[(mid.rank_service <= 10) & (mid.stranded_high > 0)].sort_values(["service", "rank_service"])
             [["service", "rank_service", "facility_id", "harbor_name", "state", "stranded_low",
               "stranded_high", "n_harbors_cut_off", "harbors_cut_off", "cell_confidence",
               "confidence_flags"]])
    s1 = sens[(sens.run == "s1_not_found_as_available") & (sens.threshold_nm == C.MID_THRESHOLD_NM)].set_index("facility_id")
    top10["rank_if_not_found_available"] = top10.facility_id.map(s1.rank_service)
    top10.to_csv(C.TABLES / "index_top10_mid.csv", index=False)

    # ---- documented backup runs -------------------------------------------
    bk = []
    for h, b, s, mode, note in DOCUMENTED_BACKUPS:
        bk.append({"harbor": h, "backup_harbor": b, "service": s, "mode": mode,
                   "sea_nm_model": round(D.loc[h, b] / C.CHART_FACTOR, 1),
                   "charted_equiv_nm": round(D.loc[h, b], 1),
                   "backup_current_status": st[(b, s)], "inventory_note": note})
    pd.DataFrame(bk).to_csv(C.TABLES / "index_backup_runs.csv", index=False)

    # ---- route-issue table --------------------------------------------------
    crit = allr[(allr.run == "main") & (allr.dependency_route_flags != "")][
        ["threshold_nm", "facility_id", "rank_service", "stranded_low", "stranded_high", "dependency_route_flags"]]
    crit = crit.assign(kind="dependency (cut-off harbor reached this facility via flagged route)")
    rescue2 = rescue.assign(kind="rescue (harbor keeps access only via a bar-crossing route)")
    pd.concat([crit, rescue2], ignore_index=True).to_csv(C.TABLES / "index_route_issues.csv", index=False)

    # ---- checks -------------------------------------------------------------
    chk = []
    unit_of = dict(zip(hv.port_id, hv.unit_id))
    allv = set_value(set(hv.port_id), units, unit_of)
    chk.append(("C1 every harbor has a value unit", len(hv) == 58 and hv.unit_id.notna().all(), "58 harbors"))
    chk.append(("C2 upper of all harbors = sum of unique unit values (dedup on unit_id)",
                abs(allv[1] - sum(u["value"] for u in units.values())) < 1, f"{allv[1]:,.0f}"))
    chk.append(("C3 stranded_low <= stranded_high everywhere", bool((allr.stranded_low <= allr.stranded_high).all()), ""))
    chk.append(("C4 no stranded value exceeds total upper", bool((allr.stranded_high <= allv[1] + 1).all()), ""))
    bf = brute_force_check(cur, D, hv, units, C.MID_THRESHOLD_NM)
    m = main_r[main_r.threshold_nm == C.MID_THRESHOLD_NM].set_index("facility_id")
    ok = all(abs(m.loc[fid, "stranded_low"] - round(v[0])) <= 1 and abs(m.loc[fid, "stranded_high"] - round(v[1])) <= 1 for fid, v in bf)
    chk.append(("C5 independent brute-force recompute, 25 random facilities at mid threshold", ok, ""))
    nmain = cur.status.eq("available").sum()
    chk.append(("C6 main run facilities = current 'available' cells", all(
        len(main_r[main_r.threshold_nm == T]) == nmain for T in C.THRESHOLDS_NM), f"{nmain} per threshold"))
    nb = cur.status.isin(["available", "not_found"]).sum()
    chk.append(("C7 bound run facilities = available + not_found", all(
        len(allr[(allr.run == "s1_not_found_as_available") & (allr.threshold_nm == T)]) == nb for T in C.THRESHOLDS_NM), f"{nb}"))
    chk.append(("C8 distance matrix symmetric", bool(np.allclose(D.values, D.values.T)), ""))
    chk.append(("C9 drop runs remove exactly the listed harbors",
                drops["marina_only"] == set(C.MARINA_ONLY) and drops["heavily_withheld"] ==
                {"CA-vallejo", "CA-avalon", "CA-huntington-harbour", "CA-port-hueneme"},
                f"s3 = {sorted(drops['heavily_withheld'])}"))
    pd.DataFrame(chk, columns=["check", "pass", "detail"]).to_csv(C.TABLES / "index_checks.csv", index=False)
    print(pd.DataFrame(chk, columns=["check", "pass", "detail"]).to_string())


if __name__ == "__main__":
    main()
