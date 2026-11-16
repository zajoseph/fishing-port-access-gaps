"""T3.3 known-closure check: apply the index's own removal logic to each event cell.
T3.4: adds run s4 (no-moorage launch-hoist harbors cannot substitute hoist)."""
import sys
sys.path.insert(0, sys.argv[1] + "/src")
import pandas as pd
from portgaps.index import config as C
from portgaps.index.simulate import load_status, load_distance
from portgaps.index.values import build_values, set_value
import os
WORK = os.environ.get("T33_WORK", "/tmp/t33"); os.makedirs(WORK, exist_ok=True)

hv, units = build_values(); cur = load_status(); D = load_distance(list(hv.port_id))
unit_of = dict(zip(hv.port_id, hv.unit_id)); name = dict(zip(hv.port_id, hv.port_name))
st0 = {(r.port_id, r.service): r.status for r in cur.itertuples()}
RUNS = {"main": {"available"}, "s1_not_found_as_available": {"available", "not_found"},
        "s4_no_moorage_hoist_no_substitute": {"available"}}   # T3.4 / R3
OWN_ONLY = {"s4_no_moorage_hoist_no_substitute": set(C.NO_MOORAGE_LAUNCH_HOIST)}
TH = [10, 15, 20, 25, 30, 40, 50, 60]
EVENTS = [
 dict(event="E1 Crescent City ice", harbor="CA-crescent-city", service="ice", dates="2024-10-05 to ~2025-08 (reopened by 2025-08-27)",
      pre="available", doc_backup="OR-brookings", doc_mode="truck (Pacific Seafood Brookings plant)", doc_note="facilities.csv 2024-10-05 row: ice trucked from Brookings"),
 dict(event="E2 Charleston ice", harbor="OR-charleston", service="ice", dates="2019-12-20 to 2020-09-12",
      pre="available", doc_backup="OR-winchester-bay", doc_mode="vessel/unknown (Charleston boats used Winchester Bay ice plant)", doc_note="facilities.csv OR-winchester-bay 2020-03-03 row; also Hallmark Fisheries (local processor, Charleston)"),
 dict(event="E3a Ilwaco Landing hoist/cranes", harbor="WA-ilwaco", service="hoist_crane", dates="closed 2024-01-22, not rebuilt",
      pre="available", doc_backup="", doc_mode="", doc_note="no backup documented in the inventory"),
 dict(event="E3b Ilwaco Landing ice", harbor="WA-ilwaco", service="ice", dates="lost 2024-01-22; 'no more ice' 2025-04-09",
      pre="available", doc_backup="", doc_mode="", doc_note="no backup documented in the inventory"),
 dict(event="E4 Point Arena hoist", harbor="CA-point-arena", service="hoist_crane", dates="2025-10-18 to 2026-01-29",
      pre="available", doc_backup="", doc_mode="none: fleet missed the 2026-01-12 crab opener", doc_note="facilities.csv 2025-10-18 row; hoist-only launch, no moorage"),
 dict(event="E5 Humboldt Bay fuel dock", harbor="CA-humboldt-bay", service="fuel", dates="2026-01-01 to 2026-01-16",
      pre="available", doc_backup="", doc_mode="", doc_note="2025-12-26 row notes; source calls it the only commercial fuel dock between Fort Bragg and Crescent City"),
]
idx = pd.read_csv(f"{sys.argv[1]}/outputs/tables/index_sensitivity.csv")
idx = idx[idx.stranded_low.notna()].set_index(["run", "threshold_nm", "facility_id"])
rows = []
for e in EVENTS:
    g, s = e["harbor"], e["service"]
    for run, W in RUNS.items():
        st = dict(st0); st[(g, s)] = e["pre"]          # event cell at its pre-event state
        F = [p for p in D.index if st[(p, s)] in W]
        others = sorted(((D.loc[g, p], p) for p in F if p != g))
        for T in TH:
            own = OWN_ONLY.get(run, set()) if s == "hoist_crane" else set()
            reach = {h: ({h} & set(F) if h in own else {f for f in F if D.loc[h, f] <= T + 1e-9}) for h in D.index}
            cut = sorted(h for h in D.index if reach[h] == {g})
            lo, hi = set_value(set(cut), units, unit_of) if cut else (0.0, 0.0)
            within = [] if g in own else [p for d, p in others if d <= T + 1e-9]
            fid = f"{g}|{s}"
            r_idx = idx.loc[(run, T, fid)] if (run, T, fid) in idx.index else None
            db = e["doc_backup"]
            rows.append({
                "event": e["event"], "harbor": g, "service": s, "event_dates": e["dates"],
                "threshold_nm": T, "run": run,
                "cell_current_status": st0[(g, s)],
                "cell_in_index_run": "Y" if r_idx is not None else "N (event cell restored to pre-event 'available' for this check)",
                "index_rank_service": int(r_idx.rank_service) if r_idx is not None else "",
                "predicted_stranded_harbors": ";".join(cut),
                "event_harbor_predicted_stranded": "Y" if g in cut else "N",
                "predicted_stranded_low": round(lo), "predicted_stranded_high": round(hi),
                "nearest_backup": others[0][1] if others else "", "nearest_backup_nm": round(others[0][0], 1) if others else "",
                "nearest_backup_status": st0[(others[0][1], s)] if others else "",
                "second_backup": others[1][1] if len(others) > 1 else "", "second_backup_nm": round(others[1][0], 1) if len(others) > 1 else "",
                "backups_within_threshold": ";".join(within),
                "documented_backup": db, "documented_backup_nm": round(D.loc[g, db], 1) if db else "",
                "documented_backup_mode": e["doc_mode"], "documented_note": e["doc_note"],
            })
out = pd.DataFrame(rows)
out.to_csv(WORK+"/events_raw.csv", index=False)
pd.set_option("display.width", 300, "display.max_colwidth", 70)
print(out[out.threshold_nm.isin([20,25,30,40,50])][["event","run","threshold_nm","cell_in_index_run","index_rank_service","predicted_stranded_harbors","predicted_stranded_low","predicted_stranded_high","nearest_backup","nearest_backup_nm","nearest_backup_status","second_backup","second_backup_nm","documented_backup_nm"]].to_string())
