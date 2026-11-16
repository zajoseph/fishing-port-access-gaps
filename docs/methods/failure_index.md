# Single-point-of-failure index (T3.2)

Code: `src/portgaps/index/` (run `python -I src/portgaps/index/run_t32.py` from the repo root; ~10 s).
Decisions: `claude/decisions-log.md`, 2026-11-14 entries; sweep, mid threshold and drop scope approved by the user in the T3.2 chat (2026-11-14).

## 1. Definitions

- **Facility** = harbor × service whose *current* status (latest `as_of_date` row in `facilities.csv`, string sort; `docs/data_dictionary.md` §5) is `available`. Main run: 117 facilities (fuel 52, ice 22, hoist_crane 34, cold_storage 9). Monthly `status_*` and history are not used.
- **Distance** = `distance_matrix.csv` `sea_nm × 1.06` = charted-equivalent nm (T3.1: model is a lower bound, median 5.9% under NOAA). A harbor is at 0 nm from itself. Routes are used as given; nothing is re-routed.
- **Access**: harbor *h* has service *s* at threshold *T* if a working *s* facility lies within *T* (including *h* itself).
- **Removal**: remove one facility at a time. A harbor is **cut off** if it had access before and has none after. Harbors with no access at baseline are already cut off and are not attributed to any facility (`n_harbors_without_access_baseline`).
- **Stranded value** of a facility = baseline landed value of the harbors it cuts off, as a range (§2). The four services are ranked separately; there is no combined weighting. An overall rank across all 4 services is also given, using the same $ scale.
- **Rank**: `rank_service` and `rank_overall` sort by `stranded_low` descending, then `stranded_high`. Equal pairs share the lowest rank number, so all zero-value facilities tie at the bottom. `rank_service_by_high` sorts on the upper bound first.
  - **Ranking on the lower bound is a choice made in this task** (it uses only published values). The PM should confirm it or switch to `rank_service_by_high` / a midpoint.

## 2. Value basis (mean annual all-species ex-vessel value 2019–2024, nominal)

Per-harbor table: `outputs/tables/index_harbor_values.csv`.

| State | Source | Level | Range? |
|---|---|---|---|
| CA (30) | `landings_monthly.csv`, `species_scheme = all`, CDFW MFDE | harbor | No. Confidential months are omitted, so the value is a lower bound (`lower_bound_withheld = Y`). |
| OR Newport, Charleston | ODFW FTR205 harbor tables (2016–2024 units) | harbor | No |
| OR Garibaldi, Depoe Bay | ODFW table with one inventory harbor plus non-inventory ports | unit (`unit_level = Y`) | No. The whole table is used. |
| OR Astoria/Warrenton, Florence/Winchester Bay, Bandon/Port Orford, Gold Beach/Brookings | shared ODFW table; FOSS port value where listed | shared unit | Yes |
| WA (16) | PacFIN ALL005 group (CLW, CWA, NPS, SPS) = unit; FOSS annual port values = sub-blocks | shared unit | Yes |

**Shared units are never split.** A harbor's own range runs from its own FOSS value (else 0) up to the whole unit value. For a set *S* of cut-off harbors:
- **upper(S)** = the sum of whole-unit values over every unit that *S* touches. Units are deduplicated on `unit_id`, so no unit is counted twice.
- **lower(S)** is computed per unit:
  - **Whole unit:** counted when every inventory harbor in it is in *S* and the unit holds no non-inventory ports. This applies only to the OR Astoria, Bandon–Port Orford and Gold Beach–Brookings tables.
  - **Otherwise:** the sum of the unit's FOSS sub-blocks whose harbors are all in *S*, capped at the unit value.
  - **Joint FOSS ports** count only when all their harbors are cut off together: "Ilwaco-Chinook", "Anacortes-La Conner", and "Willapa Bay" (Tokeland, Bay Center, Nahcotta).
- **FOSS gaps:** FOSS lists only top ports, so a year where a port isn't listed counts as $0 in the lower-bound mean. `foss_years_listed` gives the count, e.g. La Push 2/6, Everett 1/6.
- **ALL005 group values** exclude "*" confidential cells, so the WA upper bound is itself a lower bound on group landings. WA groups also include non-inventory ports (e.g., OCR, Grays Harbor, Tacoma, Olympia), so the upper bound overstates what the inventory harbors land.
- **CWA cap:** in CWA, FOSS Westport + Willapa Bay ($77.3M) exceeds the ALL005 group mean ($72.0M). Any cut set holding Westport and the Willapa harbors therefore has lower = upper = $72.0M.
- **Heavily withheld** = CA harbors with ≥30% of 2019–24 months marked confidential: Vallejo 76%, Avalon 58%, Huntington Harbour 49%, Port Hueneme 40%. The next harbor is Redondo at 22%. Humboldt Bay (61%) and LA/LB (82%) are `partial_confidential`: their values are lower bounds, flagged but not dropped.
- **No vessel-count proxy** is used.

## 3. Runs

| Run | Working cells | Harbors |
|---|---|---|
| `main` | `available` | 58 |
| `s1_not_found_as_available` | `available` + `not_found` (207 facilities) | 58 |
| `s2_no_marina_only` | `available` | drop Vallejo, Berkeley, Huntington Harbour, Redondo Beach |
| `s3_no_heavily_withheld` | `available` | drop Vallejo, Avalon, Huntington Harbour, Port Hueneme |

- **Dropped harbors** leave the network entirely: their value goes, and they stop serving as backups (user choice).
- **Every run** is computed at all 12 thresholds.
- **Rank-change flag** (`flag_rank_change = Y`) is set when any of these hold:
  - the per-service rank moves by more than 3 places;
  - a facility's stranded value drops to $0;
  - a facility's stranded value rises from $0.

  Zero-value facilities share the bottom rank, so a rank number alone can mislead.
- **`new_top10`** marks a `not_found` cell that enters the top 10 with non-zero value in s1.

## 4. Threshold sweep

10, 15, 20, 25, 30, 40, 50, 60, 75, 100, 125, 150 charted-equivalent nm. The mid-sweep threshold for the key figures is 40 nm.

Why this range:
- A harbor can be stranded at *T* only if *T* falls between its nearest and second-nearest working facility.
- Second-nearest distance (median / max over harbors):
  - fuel 21 / 61 nm
  - hoist 30 / 93 nm
  - ice 54 / 116 nm
  - cold storage 93 / 327 nm
- So fuel goes to $0 by 75 nm, hoist by 100 nm, and ice by 125 nm. Cold storage still has stranded value at 150 nm.

**Documented backup runs** (`outputs/tables/index_backup_runs.csv`) are listed to inform the headline choice; they are not a validation:

| Run | Charted-equivalent nm |
|---|---|
| Ilwaco → Astoria (ice) | 11.1 |
| Crescent City → Brookings (ice, trucked) | 20.5 |
| Charleston → Winchester Bay (ice) | 23.4 |
| Trinidad → Humboldt Bay (fuel, by road from McKinleyville) | 24.4 |
| Santa Barbara → Channel Islands (ice, from Oxnard) | 29.6 |
| Santa Barbara → Port Hueneme (ice, from Oxnard) | 30.9 |
| Point Arena → Noyo (hoist) | 34.5 |

- **Truck runs:** most documented backups moved by road. They show how far a backup can be, not how far vessels ran.
- **No vessel-size classes; one distance for all vessels.**

## 5. Stability across the sweep

`outputs/tables/index_stability.csv` (per service × threshold) and `index_rank_by_threshold.csv` (each facility's rank at every threshold, plus its min/max over 10–100 nm). Main run.

| Service | Facilities with value > 0 at 10 / 40 / 100 nm | Spearman vs 40 nm at 25 / 30 / 50 / 60 nm | Top-10 overlap with 40 nm at 30 / 50 nm |
|---|---|---|---|
| fuel | 44 / 5 / 0 | 0.58 / 0.74 / 0.90 / 0.65 | 5 of 5 / 4 of 4 (all of 50 nm's 4 are in 40 nm's 5) |
| ice | 22 / 14 / 2 | 0.74 / 0.85 / 0.94 / 0.50 | 8 / 10 |
| hoist_crane | 29 / 10 / 0 | 0.72 / 0.88 / 0.72 / 0.58 | 8 / 7 of 8 |
| cold_storage | 9 / 9 / 6 | 0.88 / 0.88 / 0.98 / 0.05 | 9 of 9 / 9 of 9 |

- **25–50 nm band:** rankings hold reasonably well here.
- **Below ~20 nm:** each facility mostly strands its own harbor, so the ranking tracks harbor value. Westport ranks #1 for fuel and ice, and Newport for hoist at 10 nm.
- **Above 60 nm:** results are driven by the few harbors with no second backup, e.g. Bellingham ice and cold storage, and Charleston cold storage at 100 nm.

## 6. Confidence flags (`confidence_flags` in `index_ranking.csv`)

| Flag | Meaning |
|---|---|
| `low_conf_cell` | The removed facility's current cell is low confidence |
| `not_found_cell` | Removed facility is a `not_found` cell (s1 only) |
| `backup_not_found_xN` | N cut-off harbors have a `not_found` cell for this service within *T*. Their loss of access rests on missing evidence. |
| `backup_lowconf_absence_xN` | N cut-off harbors have a low-confidence `not_available`/`closed` cell within *T* |
| `value_range_shared_unit` | At least one cut-off harbor is in a shared unit |
| `value_lower_bound_withheld` | At least one cut-off harbor's value omits withheld cells |
| `heavily_withheld_harbor` | At least one cut-off harbor is in the s3 drop list |
| `route_portage_bar` / `route_willapa_unverified` | A cut-off harbor reaches the removed facility by a flagged route (§7) |

## 7. Route checks (depth and tide not modelled)

`outputs/tables/index_route_issues.csv`.

- **Portage Island drying bar.** Detected as route segments crossing 122.61°W between 48.70 and 48.755°N in `sea_routes.geojson`. Only the Bellingham–Blaine route is index-critical.
  - **What depends on it:** Blaine's only ice and cold-storage access is Bellingham, via the bar route (28.1 nm charted-equivalent; NOAA charted 38 nm). This holds at 30–100 nm.
  - **Rerun with 38 nm:**
    - At 30 nm, Blaine has no access at baseline. Bellingham ice and cold storage then strand $16.5M instead of $22.0M (lower bound); ranks are unchanged (5 and 7).
    - At ≥40 nm, nothing changes.
- **Willapa Bay** (Tokeland, Bay Center, Nahcotta) routes cross a bay with wide drying flats. Depth is unverified. These routes feed Westport ice and cold storage (rank #1 at 20–50 nm) and Chinook hoist.
  - **Why it matters little:** Westport's lower bound is mostly Westport's own $65.7M FOSS value, so the Willapa routes move the lower bound by at most $6.2M (the cap at the CWA group).
- **No other route** was checked for depth.

## 8. Limits

- **Missing facility evidence:** 130/232 current cells are low confidence. In the bound run (s1), 23 of the 34 top-10 entries at 40 nm fall to $0 stranded value (§9 of the handoff). The index ranks missing evidence as much as fragility.
- **Old facts and data gaps:** current status uses old sources in places (Trinidad 2010, Neah Bay 2014, LA/LB ice 2011, SF hoist 2016). Westport has no documented offload hoist. Tokeland and Bay Center have no available services, so they count as "without access" at baseline.
- **Unconfirmed cells** (not altered): Noyo icehouse opening, Chinook ice; conflicts at Florence ice and Tokeland fuel.
- **WA values** rest on annual group/FOSS data; WA lower bounds can be $0 for harbors without their own FOSS row.
- **What distance leaves out:** sea distance ignores bar conditions, weather, vessel size and trucking. Several real backups were trucked.
- **Validation** against known closures is T3.3; not done here.

## T3.2b verification, 2026-11

*Final (2026-11-16). Public-source pass only. Phone checks were not made, by user decision (2026-11-16). Method, thresholds, sweep, value basis and rank statistic are unchanged from T3.2.*

**Targets.** `src/portgaps/index/targets_t32b.py` builds the list in three steps:
- **Drivers:** every main-run facility with stranded value > 0 that ranks in its service's top 10 at 25, 30, 40 or 50 nm. There are 48.
- **(a)** the driver's own cell, if its confidence is low.
- **(b)** every not_found or low-confidence not_available/closed cell for the same service within the threshold of a harbor the driver cuts off. This is the same test as the `backup_*` flags.

Each (b) cell is ranked by the drop in top-10 stranded value when that one cell is set to available. Each (a) cell is ranked by its driver's own stranded value. This gives 97 cells. Two known open cells were added: Noyo ice (a medium-confidence driver) and Chinook ice (added by the user). The user chose to check the top 40 plus those 2, which is 42 cells at 26 harbors (`selected_for_check = Y` in `outputs/tables/t32b_targets.csv`).

**Public-source pass (2026-11-14).** All 42 cells were searched, and every search is recorded in `outputs/tables/t32b_verification_log.csv`. Two cells were resolved with new dated rows in `data/processed/facilities.csv`:
- **WA-westport hoist_crane: not_found → available, low.** An undated operator job posting shows processor dock offload equipment. The cell remains low confidence.
- **CA-port-hueneme cold_storage: available, low → not_found, low.** The on-dock refrigeration belongs to a produce tenant. No cold storage for fishery use was located.

**Unverified cells.** These 40 cells were searched without result and not called. Their current status is still not_found or a low-confidence absence. Each is listed in `t32b_verification_log.csv` (blank `new_row_line`), with its dependency value in `t32b_targets.csv`.
- **Cold storage (20):** Tokeland, Bay Center, Nahcotta, Ilwaco, Chinook, Warrenton, Santa Barbara, Ventura, Channel Islands, La Conner, Anacortes, Blaine, Marina del Rey, Redondo Beach, Bandon, Port Townsend, Winchester Bay, Florence, Port Orford, Gold Beach.
- **Ice (15):** Tokeland, Bay Center, Nahcotta, Warrenton, Depoe Bay, Florence, Bellingham, La Conner, Anacortes, Blaine, Port Townsend, Ventura, Newport Beach, Noyo Harbor (opening date only; current status available), Chinook.
- **Hoist (4):** Ilwaco, Tokeland, Bay Center, Nahcotta.
- **Fuel (1):** Tokeland.

Two more groups are unverified:
- Cells ranked 41–97 in `t32b_targets.csv`, which were not selected for checking.
- Bandon and Gold Beach ice, which were not in the list.

`docs/t32b_call_sheet.md` is kept for any later phone checks.

**How to read the results.** Most top-10 entries still rest on unverified cells, so the index should be read as a bound:
- **Main run** (not_found = absent): the upper end of stranded value.
- **s1** (not_found = available): the lower end.

s1 does not flip low-confidence not_available/closed cells or low-confidence available cells. Entries resting on those cells, including Westport hoist, carry extra uncertainty beyond this bracket.

**Final before/after.** Source: `outputs/tables/t32b_index_before_after.csv`, from `src/portgaps/index/before_after_t32b.py`. Counts are top-10 entries with value > 0, summed over 25/30/40/50 nm × 4 services.

| | Before (T3.2) | After (T3.2b) |
|---|---|---|
| Top-10 entries (value > 0) | 142 | 137 |
| Resting on a not_found or low-confidence cell | 109 | 106 |
| Fall to $0 under s1 | 75 | 72 |

- **Hoist:** Westport hoist enters the top 10 at 25–40 nm ($65.7–72.0M), as a single point of failure for Westport itself. Chinook hoist drops out at 40–50 nm because Westport is now its backup.
- **Cold storage:** Port Hueneme drops out at every band threshold. Santa Barbara, Ventura and Channel Islands now have no cold storage within reach.
- No other top-10 entry moved.
