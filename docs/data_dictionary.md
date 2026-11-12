# Data dictionary — Pacific Coast fishing-port infrastructure inventory

Project: Fishing Port Access Gaps · Files: `data/processed/ports.csv`, `data/processed/facilities.csv`
Version: T1.3 merge, 2026-11-12 (built from T1.1 `ports_ca`/`facilities_ca` and T1.2 `ports_orwa`/`facilities_orwa` by `src/portgaps/clean/build_inventory_t13.py`; QA in `docs/qa_inventory.md`).

## 1. Scope and unit

- **Unit = one physical coastal commercial fishing harbor**, San Diego to Bellingham (amended inclusion rule, decisions-log 2026-11-12):
  - Agency port codes are grouped into harbors (e.g., the five LA/LB codes form one harbor) or split when one code covers several harbors (e.g., PacFIN WLB → Tokeland, Bay Center, Nahcotta).
  - Dropped: inland/Delta sites, "Unknown"/"Confidential" codes, and beach/bay landing points with no harbor or landing facility.
  - Size screens differ by state:
    - **CA:** at least 0.1% of 2019–24 state ex-vessel value (CDFW MFDE).
    - **OR/WA:** "harbor core", meaning the harbor has a harbor or landing facility used by a commercial fleet. OR/WA has no public port-level landings to screen on.
- **58 harbors**: CA 30, OR 12, WA 16. The count is accepted below the ~65–70 target, and dropped ports are not reinstated (decisions-log 2026-11-12). Dropped lists are in the T1.1 and T1.2 handoffs; WA-aberdeen-hoquiam was dropped in T1.3 (fails harbor-core test).
- **Services in scope (4):** fuel, ice, hoist_crane, cold_storage. Processing, dredging and bar conditions are context only: they go in `context_notes` or `notes` and never become a facility row.

## 2. `ports.csv` — one row per harbor (58 rows)

| Column | Type | Allowed values / format | Meaning and conventions |
|---|---|---|---|
| `port_id` | string, unique key | `<STATE>-<slug>`, regex `^(CA\|OR\|WA)-[a-z0-9]+(-[a-z0-9]+)*$` | Stable harbor ID used by every downstream file. The slug is the harbor's common name (e.g., `CA-los-angeles-long-beach`, `OR-winchester-bay`). |
| `port_name` | string | free text | Display name. Parentheses give the operator, basin or included sub-harbors. |
| `state` | string | `CA`, `OR`, `WA` | Always equals the `port_id` prefix. |
| `county` | string | county name, without "County" | County of the harbor point. |
| `lat`, `lon` | decimal degrees (WGS84) | CA 32.5–42.0 / OR 41.9–46.3 / WA 46.2–49.0 N; negative longitudes | One point on the harbor's main commercial basin or pier, used for T3.1 sea-route distances. CA points have 4 decimals; OR/WA points have 4–5. |
| `coord_source` | string | free text, one of three families (below) | Where the point came from. **Approximate** points carry the word "approximate". |
| `in_round1` | string | `Y`, `N` | Y = harbor was in the round-1 inventory (`claude/infrastructure-inventory-round1.md`); 22 harbors are Y. |
| `context_notes` | string | free text, required | **Agency port codes come first.** These are required for the T2.1 crosswalk (details below). Context-only items (processing, dredging, bar, closures of out-of-scope services) follow. |

**`context_notes` code formats:**
- **CA:** `CDFW port codes: <code> <name> (<share>%); …; unit share X% of CA ex-vessel value 2019–2024 (MFDE Landings by Port, read 2026-11-12)`.
- **OR:** `PacFIN <code>` plus the ODFW report table or group name.
- **WA:** `PacFIN <code>`.
- **Shared codes are stated on every harbor that shares them:**
  - AST (OR-astoria + OR-warrenton)
  - LWC "Ilwaco/Chinook" (WA-ilwaco + WA-chinook)
  - WLB "Willapa Bay" (WA-tokeland + WA-bay-center + WA-nahcotta)

**`coord_source` families:**
1. `CDFW MLDS Ports ds3081 point for port code <n> (BIOS FeatureServer biosds3081_fpu, retrieved 2026-11-12)`. These are 21 CA harbors; the source was accepted by the PM. Some ds3081 points are town points within 2 km of the harbor (Crescent City, Morro Bay, Oceanside, Port Hueneme, Mission Bay); see the QA watch list.
2. `placed manually on harbor (T1.3, approximate) from <USGS GNIS / marina listing / NOAA benchmark>; replaces ds3081 town point …`. These are 9 CA harbors: Vallejo, Berkeley, Santa Cruz, Ventura, Channel Islands, Huntington Harbour, San Diego Bay, LA/LB, and Point Arena. They were replaced on the user's instruction because the ds3081 point was a town point 1.7–9.0 km from the harbor.
3. OR/WA come from T1.2: a marinas.com, PredictWind, sail-the-net or Wikipedia listing (named), or `approximate, placed manually on <basin>`.

## 3. `facilities.csv` — one row per port × service × dated observation (270 rows)

A harbor can have several rows for one service: a history of openings and closures, or independent observations from different sources. Rows are never averaged; see §5 for how to read current status.

| Column | Type | Allowed values / format | Meaning and conventions |
|---|---|---|---|
| `port_id` | string, FK → `ports.port_id` | any `port_id` in ports.csv | Every port has ≥1 row for each of the 4 services. |
| `service` | string | `fuel`, `ice`, `hoist_crane`, `cold_storage` | Definitions in §4. |
| `status` | string | `available`, `not_available`, `closed`, `not_found` | **available**: a source shows the service operating at the harbor on `as_of_date`. **not_available**: a source says the service is absent at the harbor (or the port district says so: Snapshot teal/red). **closed**: a source dates a stop, shutdown or removal of a service that existed; `as_of_date` = the closure date. **not_found**: **no source was located. This does not mean the service is absent** (decisions-log 2026-11-11). Every not_found row says what was searched. |
| `operator` | string | free text or empty | Who runs the service, as named in the source. Empty or "unknown" when the source names no one. Owner and operator are both given when they differ (e.g., "Morro Bay Seafood Co. (operates City-owned industrial ice machine)"). |
| `operator_type` | string | `public`, `private`, `unknown` | **public** = port district, city, county, state or **tribal government** (tribal is coded public, and `notes` contain "tribal"). **private** = company, marina lessee or fish buyer. **unknown** = operator not identified (always when `operator` is empty). |
| `as_of_date` | string (date) | `YYYY-MM-DD` or `YYYY-MM` | Date the observation refers to (conventions in §5). Day precision is required for closure-event rows. |
| `source_url` | string (URL) or empty | `https://…` | The source for the row. Empty only on `not_found` rows, whose `notes` list the searches. Some not_found rows keep the URL of the page that was checked. |
| `source_type` | string | `tariff`, `port_site`, `agenda`, `news`, `state_db`, `snapshot`, `other` | **tariff** = rate/fee schedule or tariff. **port_site** = port, district or city web page or notice. **agenda** = board/commission packet, staff report or memo. **news** = dated news article. **state_db** = state database or filing (DBW BoatingFacilities, CEQAnet, CDFW-OSPR ACP sheet). **snapshot** = Oregon Coastal Ports Biennial Snapshot 2024, Fig. 5. **other** = everything else: marina aggregators (marinas.com, PredictWind, Dockwa), tourism/visitor guides, the WPPA recreational guide, academic reports and profiles, and "no source" for not_found. |
| `confidence` | string | `high`, `medium`, `low` | **high** = dated primary source specific to this harbor and service (tariff, port notice, staff report, dated news of the event). **medium** = secondary or port-district-level source, a primary source that is indirect, or a dated aggregator. **low** = undated aggregator/listing, old source (roughly >5 years), inferred fact, or not_found. Caps: Snapshot rows are never high; not_found rows are low, except one (CA-port-san-luis cold_storage, medium, where a 2026 CEQA filing describes the freezer as planned). |
| `notes` | string | free text | The evidence in brief, conflicts, prices (kept here only), and any convention applied. Changes made in T1.3 start with "T1.3 (2026-11-12):". |

## 4. Service definitions (coding rules)

| Service | Counts as the service | Notes only (does not count) |
|---|---|---|
| `fuel` | A marine fuel dock or fuel service at the harbor (diesel and/or gas), including port-contracted truck or barge delivery when that is the harbor's fuel service (e.g., Port Hueneme). | Fuel "nearby" counts as available only when the source says so, and the note records it (e.g., WA-seattle, WA-la-conner). These are weak rows. |
| `ice` | **Bulk / fleet ice** (flake or block ice sold to fishing vessels by the ton or by the load). | **Retail bagged-ice vending** at a fuel dock, store or marina, in all states (user ruling 2026-11-12). |
| `hoist_crane` | **Equipment used to offload catch**: dock hoists, cranes, wharf derricks, squid pump/discharge systems, buyers' receiving hoists. **Dual-use launch/offload hoists at harbors with no in-water moorage count** (CA-point-arena, OR-port-orford), because catch cannot be landed without them (user answer, T1.3). | **Travel-lifts / haul-out lifts and launch hoists** (WPPA guide "Hoist" column = launch hoist) (user ruling 2026-11-12). |
| `cold_storage` | Freezer or cold-storage space usable by or for the fishing fleet at the harbor, including processor-owned space. Access limits go in notes (e.g., LA/LB processors; Port Hueneme cargo cold storage coded available/low). | Out-of-scope processing closures (e.g., Newport Bornstein 2024, Eureka Pacific Seafood processing halt). |

## 5. Date conventions and reading the data

- **Undated web page** → `as_of_date` = month accessed (`2026-11`), and `notes` contain "undated".
- **not_found** → `as_of_date` = month of the search (`2026-11`).
- **Oregon Snapshot Fig. 5** → `as_of_date` = `2023-12` (interview year 2023, month unknown). Confidence is never high.
  - Colours: green → available (green also covers "funded project"); teal → not_available (planned, needs funds); red → not_available at **low** confidence.
  - It is a port-district-level fact applied to the harbor.
- **Dated events** (openings, closures, reopenings) → the day of the event when the source gives it. When a source reports that a service was running by a meeting date, `as_of_date` = that meeting date (e.g., Crescent City ice 2025-08-27; exact restart day unknown).
- **Inferred months** say so in `notes` (e.g., CA-dana-point ~2018-11).
- **Current status of a port × service** = the row with the latest `as_of_date`, compared as strings. At equal precision this is chronological; a `YYYY-MM` row sorts before day-dated rows in the same month.
  - T1.3 checked that no port × service has two rows with different statuses on its latest date.
  - The latest-row table is `outputs/tables/t13_latest_status.csv`.
- **Event histories** (for T3.3/T4) come from day-dated `closed` / `available` / `not_available` sequences. Closure-port key rows:

| Harbor · service | Sequence in facilities.csv |
|---|---|
| CA-crescent-city · ice | available 2024-10-04 → closed 2024-10-05 → available 2025-08-27 (Ocean Gold; lease ~2025-02 in notes) → available 2026-08-26 |
| OR-charleston · ice | closed 2019-12-20 (fire) → available 2020-09-12 |
| WA-ilwaco · hoist_crane | closed 2024-01-22 (Ilwaco Landing dock and cranes) → not_found 2026-11 (only launch hoists and Travelifts documented) |
| WA-ilwaco · ice | closed 2024-01-22 → not_available 2025-04-09 ("no more ice") |

Other dated outages are in the file (Point Arena hoist 2025-10-18 → 2026-01-29; SF Wharf fuel closed since 2021). Humboldt Bay's fuel-dock closure (Jan 1–16, 2026) is described only in the notes of a 2025-12-26 row.

## 6. Sources (main families)

- **Port, district and city pages, tariffs and agenda packets:** e.g., Port of Brookings Harbor FY2026-27 rates; Port of Coos Bay 2025/26 rate schedule; Crescent City Harbor District staff reports; Port of SF Commission items; Santa Barbara FY26 rates; San Mateo County Harbor District FY2026-27 rates.
- **Oregon Coastal Ports: A Biennial Snapshot (OCVA), 2024 ed., Fig. 5, p. 15:** read method in `docs/methods/snapshot_fig5_read.md`; 2021 ed. used as a check.
- **California Division of Boating & Waterways BoatingFacilities listings** (undated) and **CEQAnet** filings.
- **WPPA 2026 Recreational Boating Facilities Guide** (Apr 2026). The column alignment was parsed from text; its "Hoist" column is a launch hoist. Medium at best.
- **News:** Redwood Voice, Triplicate, Mendo Voice, OPB, Chinook Observer, Peninsula Daily News, The Log, Lost Coast Outpost, Estero Bay News, KCFM.
- **Profiles:** NOAA/Sea Grant community profiles (Trinidad 2010), Sustainability 11:1904 (2019).
- **Aggregators:** marinas.com, PredictWind, Dockwa, US Harbors (low or medium only).
- **Coordinates:** CDFW MLDS Ports ds3081; USGS GNIS harbor features; NOAA tide-station benchmarks; marina listings.

## 7. Keys for downstream tasks

- **T2.1 landings join:** `port_id` ↔ agency codes listed in `ports.context_notes` (CDFW port codes; PacFIN codes; ODFW tables/groups, which change in 2025). Shared codes (AST, LWC, WLB) need group-level handling.
- **T3.1 distances:** `ports.lat/lon`. Treat "approximate" points as ±0.5 km.
- **Index (T3.2):** `not_found` must not be read as absence without a stated assumption. Use the latest-row status plus `confidence`.
