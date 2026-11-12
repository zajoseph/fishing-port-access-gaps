# QA report — merged port inventory (T1.3)

Date: 2026-11-12 · Inputs: T1.1 `ports_ca.csv` (30) / `facilities_ca.csv` (130); T1.2 `ports_orwa.csv` (29) / `facilities_orwa.csv` (145)
Outputs checked: `data/processed/ports.csv` (58 rows), `data/processed/facilities.csv` (270 rows)
Reproduce: `python -I src/portgaps/clean/build_inventory_t13.py`, then `python -I src/portgaps/clean/qa_inventory_t13.py` (tables in `outputs/tables/t13_*`).

## Verdict: Gate 1 PASSED

- All 8 checks pass: no schema or coverage failures, coding rules consistent across states, closure-port rows dated to the day and medium or high confidence.
- **The dataset is still weak in places, and those rows are listed rather than hidden (§7):**
  - 133 of 270 rows (49%) are low confidence.
  - 130 of the 232 current-status cells (58 ports × 4 services) are low, across 51 harbors.
  - Two listed source conflicts (Florence ice, Tokeland fuel) could not be resolved from public sources.

## 1. Check results

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Schema and allowed values | **PASS** | ports 9 / facilities 10 columns, exact names and order; all 270 facility rows and 58 port rows within allowed values |
| 2 | Unique port_id | **PASS** | 58 ports, 0 duplicates (CA 30, OR 12, WA 16) |
| 3 | Every port has all 4 services | **PASS** | 58/58 ports complete; missing: [] |
| 4 | as_of_date, source_url (or search note), confidence on every row | **PASS** | 270 rows: missing date 0, confidence 0, source/search-note 0; 66 not_found rows rely on a search note |
| 5 | lat/lon present and at the harbor (flag >2 km) | **PASS** | 58/58 present and inside state box; >2 km from harbor: 0 []; 1–2 km watch list: CA-crescent-city 1.7 km, CA-port-hueneme 1.26 km, CA-oceanside 1.55 km, CA-mission-bay 1.5 km (9 CA town points replaced first) |
| 6 | Coding rules applied the same in all states | **PASS** | Travelift/launch-hoist keyword hits on counted hoist rows: 3 (all reviewed: offload equipment, haul-out text in notes only); retail-ice hits on available ice rows: 1 (reviewed: folded note only); tribal rows 6 all public+'tribal'; Snapshot rows 40 none high, all 2023-12; not_found rows all dated 2026-11; undated-page rows all say 'undated'; blank-operator rows all 'unknown'; not_available rows all sourced. Failures: 0 |
| 7 | Closure-port key rows dated (day) and medium+ | **PASS** | 9 day-dated event rows; 0 below medium |
| 8 | Shared agency codes noted in context_notes | **PASS** | AST (Astoria+Warrenton), LWC (Ilwaco+Chinook), WLB (Tokeland+Bay Center+Nahcotta) all noted |

Also reported (no pass/fail threshold set): the share of low-confidence rows by state and service (§4) and the comparison of the CA value screen with the OR/WA facility screen (§6).

## 2. Changes made in T1.3

Row counts: 275 input facility rows → removed 4 (Aberdeen/Hoquiam) + 2 (folded into notes) → added 1 (Tokeland 2022 fuel) = **270**. Ports: 59 − 1 = **58**. Full log: `outputs/tables/t13_changelog.csv`.

**Recoded rows (the hoist_crane ruling, applied in all states):**
- **T1.2:** Astoria Travelift row folded into the Snapshot hoist row; Ilwaco, Nahcotta, Port Townsend, Everett, La Conner and Anacortes went from available to not_found; Tokeland and Bay Center went from not_available to not_found. The WPPA "Hoist" column is a launch hoist, so its YES/NO says nothing about offload equipment.
- **CA, for consistency:** Redondo Beach (launch hoist) and Dana Point (removed Embarcadero boat hoist) went to not_found; the Port San Luis operator field was cleaned up.
- **Dual-use hoists:** Point Arena and Port Orford stay available with a "dual-use" note (your answer).

**Ice ruling:**
- Astoria's likely-retail row was folded into notes.
- Nahcotta and Everett went from available to not_found (their only evidence was a marina amenity listing).
- CA already applied the rule (Shelter Cove, Santa Cruz, Monterey, Oceanside, Dana Point, Avalon, Mission Bay, Marina del Rey all treat bagged ice as notes only).

**Tribal ruling:** Trinidad, La Push and Neah Bay rows are public with "tribal" in notes.

| # | port_id | service | source row (input file:line) | change | rule |
|---|---|---|---|---|---|
| 1 | OR-astoria | hoist_crane | facilities_orwa.csv:6 | row removed; content moved to notes of facilities_orwa.csv:5 | hoist_crane ruling: Travelift/launch hoist = notes only |
| 2 | WA-ilwaco | hoist_crane | facilities_orwa.csv:80 | available/medium/2026-04 -> not_found/low/2026-11 | hoist_crane ruling: Travelift/launch hoist = notes only |
| 3 | WA-nahcotta | hoist_crane | facilities_orwa.csv:97 | available/medium/2026-04 -> not_found/low/2026-11 | hoist_crane ruling: Travelift/launch hoist = notes only |
| 4 | WA-port-townsend | hoist_crane | facilities_orwa.csv:121 | available/medium/2026-04 -> not_found/low/2026-11 | hoist_crane ruling: Travelift/launch hoist = notes only |
| 5 | WA-everett | hoist_crane | facilities_orwa.csv:129 | available/medium/2026-04 -> not_found/low/2026-11 | hoist_crane ruling: Travelift/launch hoist = notes only |
| 6 | WA-la-conner | hoist_crane | facilities_orwa.csv:133 | available/low/2026-04 -> not_found/low/2026-11 | hoist_crane ruling: Travelift/launch hoist = notes only |
| 7 | WA-anacortes | hoist_crane | facilities_orwa.csv:137 | available/medium/2026-04 -> not_found/low/2026-11 | hoist_crane ruling: Travelift/launch hoist = notes only |
| 8 | WA-tokeland | hoist_crane | facilities_orwa.csv:89 | not_available/low/2026-04 -> not_found/low/2026-11 | hoist_crane ruling: Travelift/launch hoist = notes only |
| 9 | WA-bay-center | hoist_crane | facilities_orwa.csv:93 | not_available/low/2026-04 -> not_found/low/2026-11 | hoist_crane ruling: Travelift/launch hoist = notes only |
| 10 | CA-redondo-beach | hoist_crane | facilities_ca.csv:97 | available/low/2026-11 -> not_found/low/2026-11 | hoist_crane ruling: Travelift/launch hoist = notes only (applied to CA for consistency) |
| 11 | CA-dana-point | hoist_crane | facilities_ca.csv:118 | closed/low/2018-11 -> not_found/low/2026-11 | hoist_crane ruling: Travelift/launch hoist = notes only (applied to CA for consistency) |
| 12 | CA-port-san-luis | hoist_crane | facilities_ca.csv:73 | operator text edited (status unchanged) | hoist_crane ruling: Travelift/launch hoist = notes only |
| 13 | CA-point-arena | hoist_crane | facilities_ca.csv:30 | note added (status unchanged) | dual-use hoist ruling (T1.3 user answer) |
| 14 | CA-point-arena | hoist_crane | facilities_ca.csv:31 | note added (status unchanged) | dual-use hoist ruling (T1.3 user answer) |
| 15 | OR-port-orford | hoist_crane | facilities_orwa.csv:62 | note added (status unchanged) | dual-use hoist ruling (T1.3 user answer) |
| 16 | OR-astoria | ice | facilities_orwa.csv:8 | row removed; content moved to notes of facilities_orwa.csv:7 | ice ruling: retail bagged ice = notes only |
| 17 | WA-nahcotta | ice | facilities_orwa.csv:98 | available/low/2026-11 -> not_found/low/2026-11 | ice ruling: retail bagged ice = notes only |
| 18 | WA-everett | ice | facilities_orwa.csv:130 | available/low/2026-11 -> not_found/low/2026-11 | ice ruling: retail bagged ice = notes only |
| 19 | WA-neah-bay | cold_storage | facilities_orwa.csv:111 | 'tribal' added to notes | tribal-operator ruling |
| 20 | WA-neah-bay | fuel | facilities_orwa.csv:112 | 'tribal' added to notes | tribal-operator ruling |
| 21 | WA-neah-bay | hoist_crane | facilities_orwa.csv:113 | 'tribal' added to notes | tribal-operator ruling |
| 22 | WA-neah-bay | ice | facilities_orwa.csv:114 | 'tribal' added to notes | tribal-operator ruling |
| 23 | CA-trinidad | hoist_crane | facilities_ca.csv:12 | note wording updated | tribal-operator ruling |
| 24 | OR-florence | ice | facilities_orwa.csv:37 | note added (status unchanged, flagged) | listed conflict |
| 25 | WA-tokeland | fuel | added by T1.3 | row added: available/low/2022-10 | listed conflict |
| 26 | CA-port-san-luis | cold_storage | facilities_ca.csv:74 | as_of 2026-09-08 -> 2026-11 | date convention: not_found = search month |
| 27 | CA-bodega-bay | fuel | facilities_ca.csv:33 | 'undated' added to notes | date convention: undated page = month accessed |
| 28 | CA-los-angeles-long-beach | cold_storage | facilities_ca.csv:102 | 'undated' added to notes | date convention: undated page = month accessed |
| 29 | CA-san-diego-bay | hoist_crane | facilities_ca.csv:130 | 'undated' added to notes | date convention: undated page = month accessed |
| 30 | WA-seattle | fuel | facilities_orwa.csv:124 | operator_type private -> unknown | operator_type = unknown when operator not identified |
| 31 | WA-aberdeen-hoquiam | all | ports_orwa.csv + facilities_orwa.csv | port and 4 facility rows removed | user ruling: fails harbor-core test |

## 3. Listed conflicts and caveats

| Item | Finding | Coding now |
|---|---|---|
| **Florence ice** (Snapshot R vs DOWL) | **Not resolved.** For port ice: KCFM (Aug and Dec 2011) reports a port commercial ice machine rebuilt for the fleet; DOWL (undated, page metadata 2019–20) says the new commercial dock added ice generation. Against: Snapshot 2023 red; the port's service-rates page (modified 2025-07-17) lists dock hoists but no ice. | not_available / low (2023-12), flagged in notes. **Needs a call to the Port of Siuslaw (541-997-3426).** |
| **Tokeland fuel** (WPPA none vs PredictWind diesel) | **Not resolved.** WPPA 2025 *and* 2026 parse as fuel NO. Marinas.com (updated 2022-10-18) shows fuel dock and diesel; port facility text (via PredictWind, undated) says "diesel only". Possibly a service that ended after 2022. | Latest not_available / low (2026-04); added available / low (2022-10) row. **Needs a call to the harbormaster (360-942-7693).** |
| Noyo district icehouse opening | Unchanged: district page (modified 2026-02-24) says open; a Summer 2026 magazine said permits were pending. | available / medium (2026-02-24); opening date unconfirmed. |
| Chinook ice (goal May 2026) | Unchanged: opening not confirmed. | not_available / medium (2026-02-09). |
| Bandon, Gold Beach ice/cold storage | Rest only on Snapshot "R". | not_available / low (2023-12). |
| Shared agency codes | AST, LWC, WLB noted on every harbor that shares them. | Pass (check 8). |
| Closure-port rows | Crescent City ice: 2024-10-04 available → **2024-10-05 closed** → **2025-08-27 available** (Ocean Gold lease ~2025-02 in notes) → 2026-08-26 available, all high. Charleston ice: **2019-12-20 closed → 2020-09-12 available**, high. Ilwaco: dock/cranes **closed 2024-01-22** (high); ice **closed 2024-01-22** (medium) → **not_available 2025-04-09** (medium). | Pass (check 7). The Ilwaco ice closure date rests on an inference that the Landing was the ice source (stated in notes). |

## 4. Low-confidence share by state and service

All rows:

| State | fuel | ice | hoist_crane | cold_storage | all |
|---|---|---|---|---|---|
| CA | 32% (11/34) | 56% (19/34) | 42% (13/31) | 77% (24/31) | 52% (67/130) |
| OR | 12% (3/24) | 35% (6/17) | 20% (4/20) | 75% (9/12) | 30% (22/73) |
| WA | 35% (6/17) | 71% (12/17) | 71% (12/17) | 88% (14/16) | 66% (44/67) |
| All | 27% (20/75) | 54% (37/68) | 43% (29/68) | 80% (47/59) | 49% (133/270) |

Current-status rows (latest row per port × service; 232 cells):

| State | fuel | ice | hoist_crane | cold_storage | all |
|---|---|---|---|---|---|
| CA | 37% (11/30) | 63% (19/30) | 43% (13/30) | 80% (24/30) | 56% (67/120) |
| OR | 17% (2/12) | 50% (6/12) | 25% (3/12) | 75% (9/12) | 42% (20/48) |
| WA | 31% (5/16) | 75% (12/16) | 75% (12/16) | 88% (14/16) | 67% (43/64) |
| All | 31% (18/58) | 64% (37/58) | 48% (28/58) | 81% (47/58) | 56% (130/232) |

Where the weakness sits:
- **Cold storage** is mostly low in every state.
- **WA hoist_crane and ice** are 71% low. After the hoist recode, 12 of 16 WA harbors have hoist_crane = not_found.
- **CA ice** is 56% low.
- **OR is the strongest state**, because Snapshot rows score medium when green.

Current status by state and service:

| State · service | available | not_available | closed | not_found |
|---|---|---|---|---|
| CA · fuel | 27 | 1 | 1 | 1 |
| CA · ice | 12 | 2 | 0 | 16 |
| CA · hoist_crane | 19 | 1 | 0 | 10 |
| CA · cold_storage | 3 | 3 | 1 | 23 |
| OR · fuel | 11 | 1 | 0 | 0 |
| OR · ice | 7 | 3 | 0 | 2 |
| OR · hoist_crane | 11 | 1 | 0 | 0 |
| OR · cold_storage | 3 | 7 | 0 | 2 |
| WA · fuel | 14 | 2 | 0 | 0 |
| WA · ice | 3 | 2 | 0 | 11 |
| WA · hoist_crane | 4 | 0 | 0 | 12 |
| WA · cold_storage | 3 | 0 | 0 | 13 |

Harbors with **no service found available** at the latest date: WA-tokeland, WA-bay-center. 22 harbors have exactly one available service.

## 5. Coordinates

- **Replaced (your answer):** 9 CA ds3081 town points moved onto the harbor.
  - Seven were more than 2 km off; Point Arena was a town centroid 1.7 km away; LA/LB was 2.2 km off.
  - After the moves, **no harbor point is more than 2 km from the harbor**.

| port_id | old (ds3081) | new | moved km | source |
|---|---|---|---|---|
| CA-vallejo | 38.1094,-122.2294 | 38.1086,-122.2692 | 3.5 | Vallejo Municipal Marina listing (mastermariners/marinelink, 38.1086,-122.2692) |
| CA-berkeley | 37.8788,-122.2747 | 37.8665,-122.3150 | 3.8 | Berkeley Marina listing (mastermariners 37.8665,-122.3150; Wikipedia 37.8677,-122.3125) |
| CA-santa-cruz | 36.9741,-122.0308 | 36.9658,-122.0025 | 2.7 | USGS GNIS 'Santa Cruz Small Craft Harbor' (36.96578,-122.00246) |
| CA-ventura | 34.2783,-119.2932 | 34.2494,-119.2648 | 4.1 | USGS GNIS 'Ventura Harbor' (34.24945,-119.26483) |
| CA-channel-islands | 34.1937,-119.1906 | 34.1642,-119.2243 | 4.5 | USGS GNIS 'Channel Islands Harbor' (34.16417,-119.22428) |
| CA-huntington-harbour | 33.6603,-117.9992 | 33.7210,-118.0640 | 9.0 | USGS GNIS populated place 'Huntington Harbour' (33.721,-118.064) |
| CA-san-diego-bay | 32.7151,-117.1341 | 32.7126,-117.1756 | 3.9 | USGS GNIS 'Tuna Harbor' (32.71255,-117.17559) |
| CA-los-angeles-long-beach | 33.7500,-118.2509 | 33.7361,-118.2676 | 2.2 | USGS GNIS 'Fish Harbor' (33.73613,-118.26757) |
| CA-point-arena | 38.9088,-123.6931 | 38.9145,-123.7110 | 1.7 | NOAA tide station 9416841 Arena Cove pier benchmarks (~38.9145,-123.7110) |

- **Method and limits:**
  - Every point is inside its state's coastal box.
  - Each point was compared with a reference harbor point (GNIS or listing values where looked up; otherwise my own placement of the main commercial basin, ±0.5 km).
  - No shoreline layer was available in this session (no network for package or data downloads), so "on the water" was not tested geometrically.
- **1–2 km watch list (ds3081 town points, left unchanged):** CA-crescent-city (1.7 km, ds3081), CA-port-hueneme (1.26 km, ds3081), CA-oceanside (1.55 km, ds3081), CA-mission-bay (1.5 km, ds3081).
- **Approximate manual points from T1.2 (15):** OR-depoe-bay, OR-newport, OR-florence, OR-charleston, OR-port-orford, OR-gold-beach, OR-brookings, WA-westport, WA-port-angeles, WA-port-townsend, WA-everett, WA-la-conner, WA-anacortes, WA-bellingham, WA-blaine. These check out against the reference points (all < 1 km), but nothing independent confirms them. T3.1 should snap all points to its shoreline or route network and report any that move more than 500 m.

## 6. CA value screen vs OR/WA facility screen at the margin

The two screens don't select the same kind of harbor at the margin. No ports were added or dropped; the coastwide count of 58 is accepted.

| Margin case | Under its own state's screen | Under the other state's screen |
|---|---|---|
| **CA harbors kept on value, 0.1–0.35%** | **In:** Avalon 0.13%, Berkeley 0.17%, Shelter Cove 0.26%, Vallejo 0.28%, Huntington Harbour 0.30%, Redondo Beach 0.33%, Point Arena 0.34%. | **Facility screen:** Shelter Cove (commercial tractor launch run by Shelter Cove Fishing Preservation Inc.) and Point Arena (commercial hoist pier) pass. Avalon is borderline (2-ton pier hoist, low). **Vallejo, Berkeley, Huntington Harbour and Redondo Beach would probably fail:** their only evidence is a recreational-marina fuel dock, with no landing facility, ice, offload hoist or cold storage found. That is the same evidence level that dropped WA-aberdeen-hoquiam. |
| **CA codes dropped below 0.1%** | **Out:** Sausalito, Richmond, Alameda, Seal Beach, Hermosa Beach, South SF, Albion, Orick, Marshall, San Rafael, Emeryville, Oakland, Redwood City, Mill Creek. Bolinas (0.12%) was dropped as "not a harbor", the facility test applied inside CA. | **Facility screen:** not assessed (no facility research was done for dropped codes, and it is out of scope here). Several are recreational marinas; Albion (river harbor) and Marshall (Tomales Bay) are the likeliest to have a small landing site. |
| **OR/WA ports dropped on facilities** | **Out:** OR beach/bay points, Nehalem, Waldport, Toledo, Columbia in-river; WA Copalis, Kingston, Langley, Roche Harbor, Oak Harbor, Sequim, Shelton, Olympia, Friday Harbor, Tacoma, Aberdeen/Hoquiam. | **Value screen:** can't be applied, because there are no public port-level values (ODFW publishes groups; PacFIN CODE015 has no landings). |
| **OR/WA ports kept on thin facility evidence** | **In:** La Conner (commercial use unverified), Everett (fleet "dwindled"), Bay Center and Tokeland (no service found available). | **Value screen:** unknown. |

**What this means:**
- The CA rule admits about 4 small recreational-marina harbors with landings but no fleet facilities. The OR/WA rule would exclude these, and has excluded their like (Aberdeen/Hoquiam).
- They add harbors whose cells are mostly not_found, which can make CA look more "gappy".
- **Suggestion for the PM (not acted on):** in T3.2, run a sensitivity check that drops harbors failing the other state's screen (Vallejo, Berkeley, Huntington Harbour, Redondo Beach; plus La Conner on the OR/WA side).

## 7. Remaining weak rows (listed, not hidden)

**Named weak points:**
- **Unresolved conflicts:** Florence ice, Tokeland fuel (§3).
- **Unconfirmed openings:** Noyo district icehouse (date), Chinook ice.
- **Snapshot-red-only rows (low):** Bandon ice/cold storage; Gold Beach ice/cold storage; Florence, Newport, Winchester Bay cold storage; Winchester Bay hoist. Winchester Bay's hoist conflicts with a 2021 addendum listing a 2,200-lb commercial dock crane (noted in the row).
- **Old sources driving current status** (pre-2020):
  - CA-trinidad, all four services (2010); CA-los-angeles-long-beach ice (2011); CA-san-francisco hoist (2016); CA-huntington-harbour fuel (2016); CA-newport-beach hoist (2018); CA-shelter-cove ice/cold storage (2019).
  - WA-neah-bay hoist and ice (2014).
- **WPPA 2026 recreational guide:** current status for 22 WA cells (12 low, 10 medium). Its columns were parsed from text, and fuel "NEARBY" is coded available for Seattle, La Conner and Blaine.
- **Processor-owned or cargo cold storage** with unknown access for independent boats: LA/LB, Port Hueneme, Westport, Bellingham.
- **WA offload hoists:** after the recode, only Neah Bay, Port Angeles, Seattle and Chinook have a documented offload hoist or crane. Westport (WA's top port) has none documented.

**All current-status cells at low confidence (130 cells, 51 harbors).** Format: service: status (as_of, source_type).

| port_id | low-confidence current cells |
|---|---|
| CA-trinidad | fuel: not_available (2010-08, other); ice: not_available (2010-08, other); cold_storage: not_available (2010-08, other) |
| CA-los-angeles-long-beach | ice: available (2011-11-28, agenda); fuel: available (2026-11, state_db) |
| CA-san-francisco | hoist_crane: available (2016-03-30, news); cold_storage: not_found (2026-11, agenda) |
| CA-huntington-harbour | fuel: available (2016-05-25, news); hoist_crane: not_found (2026-11, other); cold_storage: not_found (2026-11, other); ice: not_found (2026-11, other) |
| CA-newport-beach | hoist_crane: not_available (2018-02, port_site); fuel: available (2026-11, state_db); ice: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| WA-bellingham | ice: available (2020-09-18, other); hoist_crane: not_found (2026-11, other) |
| WA-la-push | fuel: available (2022-12, other); ice: not_found (2026-11, other); hoist_crane: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| OR-florence | cold_storage: not_available (2023-12, snapshot); ice: not_available (2023-12, snapshot) |
| OR-winchester-bay | hoist_crane: not_available (2023-12, snapshot); cold_storage: not_available (2023-12, snapshot) |
| OR-newport | cold_storage: not_available (2023-12, snapshot) |
| OR-garibaldi | cold_storage: not_available (2023-12, snapshot); ice: available (2026-11, other); hoist_crane: available (2026-11, other) |
| OR-gold-beach | cold_storage: not_available (2023-12, snapshot); ice: not_available (2023-12, snapshot) |
| OR-port-orford | cold_storage: not_available (2023-12, snapshot); fuel: available (2026-11, other) |
| OR-bandon | cold_storage: not_available (2023-12, snapshot); ice: not_available (2023-12, snapshot) |
| CA-noyo-harbor | fuel: available (2025-10, agenda); cold_storage: not_found (2026-11, port_site) |
| WA-blaine | fuel: available (2026-04, other); ice: not_found (2026-11, other); hoist_crane: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| WA-seattle | fuel: available (2026-04, other); ice: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| WA-la-conner | fuel: available (2026-04, other); ice: not_found (2026-11, other); cold_storage: not_found (2026-11, other); hoist_crane: not_found (2026-11, other) |
| WA-tokeland | fuel: not_available (2026-04, other); hoist_crane: not_found (2026-11, other); ice: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| CA-port-hueneme | cold_storage: available (2026-05, port_site) |
| WA-chinook | cold_storage: not_found (2026-11, other) |
| CA-shelter-cove | fuel: available (2026-11, state_db); hoist_crane: not_found (2026-11, port_site) |
| WA-ilwaco | hoist_crane: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| CA-point-arena | fuel: not_found (2026-11, other); ice: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| CA-redondo-beach | fuel: available (2026-11, news); ice: not_found (2026-11, other); hoist_crane: not_found (2026-11, news); cold_storage: not_found (2026-11, other) |
| WA-nahcotta | cold_storage: not_found (2026-11, other); ice: not_found (2026-11, other); hoist_crane: not_found (2026-11, other) |
| WA-port-townsend | cold_storage: not_found (2026-11, other); hoist_crane: not_found (2026-11, other); ice: not_found (2026-11, other) |
| WA-everett | ice: not_found (2026-11, other); hoist_crane: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| WA-anacortes | ice: not_found (2026-11, other); hoist_crane: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| WA-port-angeles | ice: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| WA-bay-center | ice: not_found (2026-11, other); hoist_crane: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| WA-neah-bay | cold_storage: available (2026-11, other) |
| WA-westport | hoist_crane: not_found (2026-11, other) |
| CA-oceanside | ice: not_found (2026-11, port_site); hoist_crane: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| CA-mission-bay | ice: not_found (2026-11, other); hoist_crane: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| CA-dana-point | cold_storage: not_found (2026-11, other); hoist_crane: not_found (2026-11, news); ice: not_found (2026-11, other) |
| CA-san-diego-bay | fuel: available (2026-11, port_site); cold_storage: not_found (2026-11, other); ice: available (2026-11, other) |
| CA-channel-islands | cold_storage: not_found (2026-11, other); ice: not_found (2026-11, other) |
| OR-warrenton | fuel: not_available (2026-11, other); ice: not_found (2026-11, other); cold_storage: not_found (2026-11, other); hoist_crane: available (2026-11, other) |
| CA-avalon | cold_storage: not_found (2026-11, other); ice: not_found (2026-11, other); hoist_crane: available (2026-11, other) |
| CA-marina-del-rey | hoist_crane: not_found (2026-11, other); ice: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| CA-moss-landing | ice: not_found (2026-11, other); cold_storage: not_found (2026-11, other) |
| CA-santa-cruz | cold_storage: not_found (2026-11, other); hoist_crane: not_found (2026-11, other); ice: not_found (2026-11, state_db) |
| CA-pillar-point | cold_storage: not_found (2026-11, other) |
| CA-berkeley | cold_storage: not_found (2026-11, other); hoist_crane: not_found (2026-11, state_db); fuel: available (2026-11, state_db); ice: not_found (2026-11, other) |
| CA-vallejo | cold_storage: not_found (2026-11, other); hoist_crane: not_found (2026-11, other); ice: not_found (2026-11, other) |
| CA-ventura | cold_storage: not_found (2026-11, other); ice: not_found (2026-11, other) |
| CA-santa-barbara | cold_storage: not_found (2026-11, other) |
| OR-depoe-bay | cold_storage: not_found (2026-11, other); ice: not_found (2026-11, other) |
| CA-morro-bay | cold_storage: not_found (2026-11, other); fuel: available (2026-11, state_db) |
| CA-monterey | cold_storage: not_found (2026-11, other); ice: not_found (2026-11, state_db) |
