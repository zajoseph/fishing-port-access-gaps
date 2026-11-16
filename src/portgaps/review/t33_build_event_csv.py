import sys, pandas as pd
import os
WORK = os.environ.get("T33_WORK", "/tmp/t33"); os.makedirs(WORK, exist_ok=True)
R = sys.argv[1]
ev = pd.read_csv(WORK+"/events_raw.csv")
ev = ev[ev.threshold_nm.isin([20, 25, 30, 40, 50])].copy()
ld = pd.read_csv(WORK+"/landings_desc.csv")
def lsum(key, role):
    r = ld[ld.event.str.startswith(key) & ld.role.str.startswith(role)]
    return "" if r.empty else f"{r.during_vs_prior3.iloc[0]}x ({r.during_months_published.iloc[0]} months published)"
STATE = {
 "E1": "Brookings ice available (Snapshot 2023-12; Dec 2025 price note): covers the event.",
 "E2": "Winchester Bay ice in use by Charleston boats (2020-03-03 row): covers the event. Port Orford/Newport ice from 2023 Snapshot; state in 2019-20 not documented.",
 "E3a": "Ilwaco hoist is current not_found (only launch hoists/Travelifts) -> not a facility in main; restored to available for this check. Chinook 'wharf hoists' row is 2026-02-09; 2024 state not documented. s1 counts the Ilwaco not_found row as a working hoist.",
 "E3b": "Ilwaco ice current not_available -> restored to available for this check. Astoria ice from 2023 Snapshot (pre-event). Chinook ice not available (planned 2026), as at event time. Warrenton ice not_found (counts only in s1).",
 "E4": "Noyo hoist available since 2020 reopening; Bodega hoist 2025 rate schedule: both cover the event.",
 "E5": "Nearest other fuel: Shelter Cove (available/low, undated recreational listing) 60.8 nm; Crescent City 67.7 nm.",
}
def verdict(r):
    k = r.event.split()[0]; T = r.threshold_nm
    if k == "E1":
        return ("agree", "Index: no harbor stranded; nearest backup Brookings 20.5 nm = documented backup (ice trucked). CC landings during closure 0.95x prior 3 yrs.") if T >= 25 else \
               ("disagree", "Index strands Crescent City, but ice came from Brookings (20.5 nm) and landings held (0.95x).")
    if k == "E2":
        if T >= 30: return ("agree", "Index: none stranded; nearest backup Winchester Bay 23.4 nm = documented backup. Charleston landings 0.66x prior (2020 COVID overlaps; no causal reading).")
        if T == 25: return ("agree (Charleston); can't tell (Bandon)", "Charleston covered by Winchester Bay 23.4 nm as documented; Bandon ($0-4.8M) predicted stranded, no Bandon evidence either way.")
        return ("disagree", "Index strands Charleston (and Bandon), but Charleston boats used Winchester Bay ice at 23.4 nm.")
    if k == "E3a": return ("can't tell", "Index: none stranded (Chinook hoist 4.6 nm). No documented backup; Ilwaco landings only as CLW group crab-only (0.87x, 4 months withheld); Chinook hoist state in 2024 undocumented.")
    if k == "E3b": return ("can't tell", "Index: none stranded (Astoria ice 11.1 nm). No documented backup; group-level crab-only landings can't isolate Ilwaco.")
    if k == "E4":
        return ("agree", "Index strands Point Arena ($0.58M): no hoist within threshold; fleet missed the crab opener.") if T <= 30 else \
               ("disagree", "Index says Noyo hoist (34.5 nm) covers Point Arena; the harbor closed to all vessels and the fleet missed the opener. No-moorage launch hoist is not substitutable by a vessel run.")
    if k == "E5": return ("can't tell (outcome); structure consistent", "Index ranks Humboldt fuel #1-2 (strands Humboldt Bay" + (" + Trinidad" if "trinidad" in r.predicted_stranded_harbors else "") + "); source calls it the only commercial fuel dock between Fort Bragg and Crescent City. 16-day closure; Jan 2026 CA landings not released; no documented backup.")
ev[["verdict", "verdict_reason"]] = ev.apply(lambda r: pd.Series(verdict(r)), axis=1)
ev["in_headline_band_25_50"] = (ev.threshold_nm >= 25).map({True: "Y", False: "N (context)"})
ev["headline_threshold"] = (ev.threshold_nm == 40).map({True: "Y", False: ""})
ev["facility_state_at_event"] = ev.event.str.split().str[0].map(STATE)
k = ev.event.str.split().str[0]
ev["landings_event_unit_during_vs_prior3"] = [lsum({"E1":"E1","E2":"E2","E3a":"E3","E3b":"E3","E4":"E4"}.get(x,"none"), "event") for x in k]
ev["landings_backup_unit_during_vs_prior3"] = [lsum({"E1":"E1","E2":"E2","E3a":"E3","E3b":"E3","E4":"E4"}.get(x,"none"), "backup") for x in k]
cols = ["event","harbor","service","event_dates","threshold_nm","in_headline_band_25_50","headline_threshold","run",
        "cell_current_status","cell_in_index_run","index_rank_service","predicted_stranded_harbors","event_harbor_predicted_stranded",
        "predicted_stranded_low","predicted_stranded_high","nearest_backup","nearest_backup_nm","nearest_backup_status",
        "second_backup","second_backup_nm","backups_within_threshold","documented_backup","documented_backup_nm","documented_backup_mode",
        "documented_note","facility_state_at_event","landings_event_unit_during_vs_prior3","landings_backup_unit_during_vs_prior3","verdict","verdict_reason"]
ev[cols].to_csv(f"{R}/outputs/tables/t33_event_check.csv", index=False)
print(len(ev)); print(ev.groupby(["event","threshold_nm"]).verdict.first().unstack().to_string())
