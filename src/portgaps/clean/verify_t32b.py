"""T3.2b targeted facility verification: append dated rows and write the log.

Appends new evidence rows to data/processed/facilities.csv (never edits or
deletes existing rows; no new columns) and writes
outputs/tables/t32b_verification_log.csv (one row per selected target cell).
Idempotent: rows already present (same port, service, as_of_date, notes) are
not added twice.

Call answers: add them to NEW_ROWS (source_type "other", notes
"phone/email with <role>, YYYY-MM-DD", as_of_date = call date) and set the
cell's LOG entry result; then rerun this script, qa_inventory_t13.py,
build_join_t22.py and run_t32.py.

Run: python -I src/portgaps/clean/verify_t32b.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
FAC = ROOT / "data" / "processed" / "facilities.csv"
TABLES = ROOT / "outputs" / "tables"
P = "T3.2b (2026-11-14): "

NEW_ROWS = [
    dict(port_id="WA-westport", service="hoist_crane", status="available",
         operator="Upland seafood processors' docks (e.g., Pacific Seafood Westport)",
         operator_type="private", as_of_date="2026-11",
         source_url="https://pacificseafood.applytojob.com/apply/1idlWVu8lD/Dock-Worker-Seasonal-Night-Shift",
         source_type="other", confidence="low",
         notes=P + "Operator job posting (undated; accessed 2026-11) for a Westport dock worker: "
               "unloads product from vessels using dock equipment; crane/hoist operation experience "
               "preferred. Port page (2026 items) says vessels enter the marina to offload; port news "
               "(Nov 2022) lists 5 upland processors and 75-100 transient commercial vessels offloading. "
               "No port-owned offload hoist documented. Processor offload cranes inferred from the "
               "operator posting, so low; on call sheet for confirmation."),
    dict(port_id="CA-port-hueneme", service="cold_storage", status="not_found",
         operator="", operator_type="unknown", as_of_date="2026-11",
         source_url="https://www.portofhueneme.org/about/port-facts/",
         source_type="port_site", confidence="low",
         notes=P + "No cold storage for fishery use located. Port facts page lists on-dock "
               "refrigeration as 93,000 SF (Del Monte, produce); off-site temperature-controlled "
               "centers are produce/distribution firms. Commercial fishing page lists only the squid "
               "discharge system and on-dock ice. Supersedes the 2026-05 available/low row, which "
               "assumed the cargo cold storage served fishing. Squid offloading is moving to Ventura "
               "Harbor (CEQA SCH 2025050181; construction from 2027)."),
]

# One entry per selected target cell: what was searched, result, call needed?
S_WA = "WebSearch + port pages: WPPA 2026 guide, port sites, Chinook Observer/Astorian, PredictWind, marinas.com"
LOG = {
    ("WA-tokeland", "cold_storage"): (S_WA + "; Port of Willapa Harbor facilities pages", "unresolved: no source located", "Y"),
    ("WA-bay-center", "cold_storage"): (S_WA + "; Port of Willapa Harbor Bay Center page", "unresolved: no source located", "Y"),
    ("WA-nahcotta", "cold_storage"): (S_WA + "; Port of Peninsula listings", "unresolved: no source located", "Y"),
    ("WA-tokeland", "ice"): (S_WA + "; USCG WAMS Willapa 2021 (Coast Pilot text: ice 'at the basin or nearby', likely retail)", "unresolved: only generic/retail mentions", "Y"),
    ("WA-bay-center", "ice"): (S_WA, "unresolved: no source located", "Y"),
    ("WA-nahcotta", "ice"): (S_WA, "unresolved: no source located", "Y"),
    ("WA-ilwaco", "cold_storage"): (S_WA + "; Port of Ilwaco pages", "unresolved: processors hold own product only (2014/2025 sources)", "Y"),
    ("WA-chinook", "cold_storage"): (S_WA + "; dredgewire 2026-02, PNWA 2026 project lists", "unresolved: no source located", "Y"),
    ("WA-tokeland", "fuel"): (S_WA + "; slipstreamboating (undated), PredictWind (undated, 'diesel only')", "unresolved: WPPA 2025/2026 NO vs undated listings YES; conflict stands", "Y"),
    ("WA-ilwaco", "hoist_crane"): (S_WA + "; Astorian 2025-04 (Safe Coast Seafoods cranes 'not guaranteed'; port seeking a fishermen's dock with crane); Cantwell 2026 roundtable", "unresolved: processor cranes exist but public access unclear", "Y"),
    ("WA-tokeland", "hoist_crane"): (S_WA + "; Port of Willapa Harbor pages (high dock)", "unresolved: no offload hoist documented", "Y"),
    ("WA-bay-center", "hoist_crane"): (S_WA, "unresolved: no source located", "Y"),
    ("WA-nahcotta", "hoist_crane"): (S_WA, "unresolved: WPPA hoist = launch hoist only", "Y"),
    ("WA-westport", "hoist_crane"): (S_WA + "; Port of Grays Harbor Westport Marina and modernization pages; Pacific Seafood and Ocean Gold job postings", "resolved: available/low (processor offload equipment, operator posting); call to confirm", "Y"),
    ("OR-warrenton", "cold_storage"): ("WebSearch: City of Warrenton marina ordinances/rates, USACE Skipanon page, sail-the-net, news", "unresolved: no source located", "Y"),
    ("OR-warrenton", "ice"): ("WebSearch: City of Warrenton marina ordinances/rates, OSMB/Sea Grant guide, sail-the-net ('Ice - Not known')", "unresolved: no source located", "Y"),
    ("OR-depoe-bay", "ice"): ("WebSearch: City of Depoe Bay harbor code and moorage agreement, USACE page, news", "unresolved: no source located", "Y"),
    ("OR-florence", "ice"): ("WebSearch: Port of Siuslaw site (FAQ, news, 2025 agendas), news", "unresolved: no current source; Snapshot 2023 'unavailable' stands", "Y"),
    ("CA-port-hueneme", "cold_storage"): ("Port of Hueneme port-facts, about and commercial-fishing pages; CEQA SCH 2025050181", "resolved: not_found/low (on-dock refrigeration is a produce tenant's)", "Y"),
    ("CA-santa-barbara", "cold_storage"): ("WebSearch: City waterfront rate summary FY27, The Log, Independent 2026-09, SeafoodSource (Ocean Collective, no cold storage), CFSB", "unresolved: fleet still seeking cold storage; none located", "Y"),
    ("CA-ventura", "cold_storage"): ("Ventura Port District fish pier page; CEQA SCH 2025050181 (squid facility)", "unresolved: no source located", "Y"),
    ("CA-channel-islands", "cold_storage"): ("WebSearch; CEQA 1986 wharf/ice/hoist project; Port of Hueneme off-site list (produce)", "unresolved: no source located", "Y"),
    ("WA-la-conner", "cold_storage"): ("WebSearch: WPPA guide, Port of Skagit/La Conner listings", "unresolved: no source located", "Y"),
    ("WA-anacortes", "cold_storage"): ("WebSearch: Port of Anacortes pages, PNWA 2026 (T Dock = seafood landing dock), listings", "unresolved: no source located", "Y"),
    ("WA-bellingham", "ice"): ("WebSearch: Lineage facility pages (2700 and 2825 Roeder), Cascadia Daily 2025-03 (BCS ice plant since 1946), Lineage acquisition news 2025", "unresolved: post-sale ice sales not confirmed", "Y"),
    ("WA-la-conner", "ice"): ("WebSearch: WPPA guide, listings", "unresolved: no source located", "Y"),
    ("WA-anacortes", "ice"): ("WebSearch: marinas.com 2022 'Ice: Yes' (marina amenity, likely retail), Dockwa", "unresolved: only retail-type listing", "Y"),
    ("WA-blaine", "cold_storage"): ("WebSearch: Port of Bellingham pages, Ecology Blaine Harbor cleanup pages, Fishermen's News", "unresolved: processors present, no fleet cold storage located", "Y"),
    ("WA-blaine", "ice"): ("WebSearch: Port of Bellingham pages, Fishermen's News", "unresolved: no source located", "Y"),
    ("CA-marina-del-rey", "cold_storage"): ("WebSearch (county marina pages, news)", "unresolved: no source located", "Y"),
    ("CA-redondo-beach", "cold_storage"): ("WebSearch (King Harbor pages, news)", "unresolved: no source located", "Y"),
    ("OR-bandon", "cold_storage"): ("Port of Bandon site (marina, fuel/hoist, commercial vessel pages, 2026); OR Blue Book", "unresolved: port site silent on cold storage", "Y"),
    ("WA-port-townsend", "cold_storage"): ("WebSearch: port pages, PT Leader, listings", "unresolved: no source located", "Y"),
    ("WA-port-townsend", "ice"): ("WebSearch: marinas.com 'Ice: Nearby', The Log listing (retail-type)", "unresolved: only retail-type listings", "Y"),
    ("OR-winchester-bay", "cold_storage"): ("WebSearch: Salmon Harbor (Douglas County) listings, ODFW R&E 15-031 (ice machine)", "unresolved: no source located", "Y"),
    ("OR-florence", "cold_storage"): ("Port of Siuslaw site, news", "unresolved: no current source; Snapshot 2023 stands", "Y"),
    ("OR-port-orford", "cold_storage"): ("OPB/JPR 2026-08-07 (seafood hub incl. processing/live holding is a longer-term proposal; buyers run own seawater pumps); HB 2366 (2019) plan; Coastal Visitors Assoc. cold-storage program", "unresolved: hub not built; current cold storage unconfirmed", "Y"),
    ("OR-gold-beach", "cold_storage"): ("Port of Gold Beach site (commercial dock: fish buyer, fish/live fish processing, hoists); PNWA 2025", "unresolved: no cold storage named", "Y"),
    ("CA-ventura", "ice"): ("Ventura Port District fish pier page (two cranes, no ice named); CEQA SCH 2025050181; Ventura Harbor Village pages", "unresolved: no bulk ice located (Port Hueneme on-dock ice serves squid)", "Y"),
    ("CA-noyo-harbor", "ice"): ("Noyo Harbor District Jan 2025 and Feb 2026 packets; Mendocino Voice 2025-10; district page 2026-02", "unresolved (opening date): Feb 12 2026 packet says the office 'will begin to operate' the icehouse as it nears completion; no ice revenue in Jan 2026 P&L; current status available stands", "Y"),
    ("WA-chinook", "ice"): ("WebSearch: dredgewire 2026-02-09 (ice on pier two, goal May 2026), PNWA 2026 lists, WPPA 2026 guide", "unresolved: opening not confirmed", "Y"),
    ("CA-newport-beach", "ice"): ("WebSearch (harbor pages, dory fleet news)", "unresolved: no source located", "Y"),
}


def main() -> None:
    fac = pd.read_csv(FAC, dtype=str, keep_default_na=False)
    cols = list(fac.columns)
    n0 = len(fac)
    have = set(zip(fac.port_id, fac.service, fac.as_of_date, fac.notes))
    added = {}
    for r in NEW_ROWS:
        key = (r["port_id"], r["service"], r["as_of_date"], r["notes"])
        if key in have:
            idx = fac.index[(fac.port_id == key[0]) & (fac.service == key[1])
                            & (fac.as_of_date == key[2]) & (fac.notes == key[3])][0]
        else:
            fac = pd.concat([fac, pd.DataFrame([{c: r.get(c, "") for c in cols}])], ignore_index=True)
            idx = len(fac) - 1
        added[(r["port_id"], r["service"])] = int(idx) + 2  # CSV line number (header = line 1)
    fac.to_csv(FAC, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"facilities.csv: {n0} -> {len(fac)} rows")

    tg = pd.read_csv(TABLES / "t32b_targets.csv")
    tg = tg[tg.selected_for_check == "Y"]
    out = []
    for r in tg.itertuples():
        searched, result, call = LOG[(r.port_id, r.service)]
        out.append({"target_rank": r.target_rank, "port_id": r.port_id, "service": r.service,
                    "cell_status_before": r.cell_status, "cell_confidence_before": r.cell_confidence,
                    "checked_2026_11": searched, "result": result,
                    "new_row_line": added.get((r.port_id, r.service), ""),
                    "on_call_sheet": call, "call_answer": "", "call_row_line": ""})
    pd.DataFrame(out).to_csv(TABLES / "t32b_verification_log.csv", index=False)
    print(f"verification log: {len(out)} cells; resolved {sum(1 for o in out if o['new_row_line'])}")


if __name__ == "__main__":
    main()
