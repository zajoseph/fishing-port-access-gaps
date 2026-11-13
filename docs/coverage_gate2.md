# T2.2 Join and coverage check (Gate 2)

As of 2026-11-13. Built by `src/portgaps/clean/build_join_t22.py` (run from the repo root: `python -I src/portgaps/clean/build_join_t22.py`). Inputs are `data/processed/ports.csv` (58 harbors), `data/processed/facilities.csv` (270 rows) and `data/processed/landings_monthly.csv` (T2.1, merged to main in PR #3).

**Verdict: Gate 2 PASSES.** All 58 harbors are joined to a landings unit for every month their state source publishes. Unit totals reconcile exactly to `landings_monthly.csv`. All 4 closure ports have data before, during and after their events, except where no reopening exists, and the gaps are listed. Details are in §(d).

## Outputs
| file | contents |
|---|---|
| `data/processed/port_unit_bridge.csv` | 68 rows. Columns: port_id, unit_id, unit_type, species_scheme, valid_from, valid_to, n_ports_in_unit. There is one row per harbor × unit period, so 10 OR harbors have two rows (2016–2024 and 2025); Astoria and Warrenton have one. |
| `data/processed/port_month.csv` | 7,540 rows = 58 harbors × 130 months (2016-01 to 2026-10). Columns: port_id, state, month, unit_id, unit_type, species_scheme, shared_unit, n_ports_in_unit, pounds, value_usd, withheld_flag, then `status_<service>` and `current_status_<service>` for fuel, ice, hoist_crane and cold_storage. |
| `outputs/tables/t22_join_coverage.csv` | Joined months, first/last joined month and units for each harbor. |
| `outputs/tables/t22_join_gaps.csv` | Port-months with no unit joined, with the reason. |
| `outputs/tables/t22_reconciliation.csv` | Unit totals in port_month (each unit counted once) vs landings_monthly, by state, plus the naive all-rows sum to show the cost of double counting. |
| `outputs/tables/t22_closure_windows.csv` | Closure-port windows by level segment: months, unit, level, scheme, withheld and blank counts, and the facility status of the closed service. |
| `outputs/tables/t22_status_coverage.csv` | How many port-months have an observed facility status. |

### How port_month is built
- **Series.** `species_scheme = all` (CA, OR). For WA, `Dungeness crab`, the only WA monthly series.
- **Join.** `landings_monthly.port_ids` is split on `;`. Every harbor in a unit gets the unit's full pounds, value_usd and withheld_flag.
  - `shared_unit = Y` when the unit covers more than one inventory harbor (`n_ports_in_unit` > 1). **Never sum these rows across harbors.** To aggregate, deduplicate on `unit_id × month` first.
  - `unit_type` ≠ `harbor` means the value is not harbor-level even when `shared_unit = N`. Examples: ODFW groups with one inventory harbor (Garibaldi, Depoe Bay) also include non-inventory places, and the WA PacFIN groups include non-inventory ports.
- **Withheld rules.** Flags pass through unchanged from T2.1. `confidential` and `pacfin_confidential` rows have null values. `partial_confidential` is a lower bound. `no_record_zero` is 0.
  - OR all-species rows have no `blank_assumed_zero` cells, so that flag does not occur in port_month.
  - A new flag, **`not_in_source`**, marks port-months after the state source ends, where no unit is joined. These rows have a blank unit_id and null values.
- **Facility status by month.** `status_<service>` for month M is the latest facilities.csv row whose `as_of_date[:7]` ≤ M, sorted by `as_of_date` as a string. A day-dated row therefore outranks a `YYYY-MM` row in the same month, so the column is the **end-of-month status**.
  - Example: Crescent City ice is `closed` in 2024-10, after the 2024-10-04 and 2024-10-05 rows.
  - Months before the first row are `no_observation`. Current status is never back-filled.
  - `current_status_<service>` is the latest row overall, per `docs/data_dictionary.md`. It is repeated on every row of the harbor.
  - `not_found` ≠ absent.

## (a) Join coverage: every harbor × month
| state | harbors | months joined per harbor | joined window | unjoined months |
|---|---|---|---|---|
| CA | 30 | 120 of 130 | 2016-01 to 2025-12 | 2026-01 to 2026-10 (10 per harbor) |
| OR | 12 | 120 of 130 | 2016-01 to 2025-12 (OR unit change 2025-01) | 2026-01 to 2026-10 (10 per harbor) |
| WA | 16 | 130 of 130 | 2016-01 to 2026-10 | none |

- **Join failures inside source windows: 0.** Every one of the 7,120 port-months in a published window has exactly one unit. The script asserts that no harbor maps to two units in the same month and that each unit's months are contiguous.
- **Gaps: 420 port-months**, all `not_in_source` (42 CA/OR harbors × 2026-01 to 2026-10). CDFW MFDE runs to the last complete calendar year, and ODFW 2026 FINAL tables are not published. These gaps come from source lag, not from the join. They are listed in `t22_join_gaps.csv`.
  - The grid ends at 2026-10, the latest month in the panel (WA). If later tasks prefer a CA/OR panel that ends at 2025-12, filter out `withheld_flag = not_in_source`.
- **OR unit changes in 2025:** each OR harbor has one unit for 2016–2024 and another for 2025, as shown in the bridge.
  - Charleston: harbor → "Florence-Winchester Bay-Charleston" (3 inventory harbors).
  - Newport: harbor → "Depoe Bay-Newport-Waldport-Yachats" (2).
  - Florence and Winchester Bay → the Charleston group (3).
  - Bandon, Port Orford, Gold Beach, Brookings → one group (4).
  - Garibaldi → the 2025 Gearhart–Siletz Bay group (1).
  - Depoe Bay → the Newport group (2).
  - Astoria and Warrenton stay in ODFW Astoria (2) throughout.
- **WA:** 16 harbors in 4 PacFIN groups. CLW holds Ilwaco and Chinook (2), CWA 5, NPS 7 and SPS 2. All WA rows are group-level and crab-only.

## (b) Reconciliation
Each unit × month in port_month is counted once and compared with the joined series in landings_monthly.csv (`t22_reconciliation.csv`).

| state | unit-months | matched (pounds, value, flag) | value_usd, landings_monthly | value_usd, port_month (once) | value_usd if all harbor rows were summed |
|---|---|---|---|---|---|
| CA | 3,600 | 3,600 | 1,789,065,811 | 1,789,065,811 | 1,789,065,811 |
| OR | 924 | 924 | 1,654,058,632 | 1,654,058,632 | 2,537,839,726 |
| WA | 520 | 520 | 946,325,059 | 946,325,059 | 4,896,828,009 |
| **All** | **5,044** | **5,044** | **4,389,449,502** | **4,389,449,502** | 9,223,733,546 |

- Pounds also match exactly: 4,828,992,328 in both.
- Within every shared unit × month, all harbor rows carry identical values and flags, and the row count equals n_ports_in_unit. There are 0 inconsistent groups.
- The last column shows why shared rows must not be summed: summing every harbor row would double-count OR value (1.5×) and inflate WA value 5.2×.

## (c) Closure ports
Windows are set from the event dates in facilities.csv and ports.csv. The event month is counted in "during". "After" starts the month after the reopening date. Counts are from `t22_closure_windows.csv`, using the joined series.

### Crescent City: ice, closed 2024-10-05, running by 2025-08-27
| window | months | level / unit | scheme | with value | withheld / no-record |
|---|---|---|---|---|---|
| before 2016-01 to 2024-09 | 105 | harbor, CA-crescent-city | all | 103 | 2 confidential (2016-01, 2023-12); 1 no_record_zero (2016-11) |
| during 2024-10 to 2025-08 | 11 | harbor | all | 11 | 0 |
| after 2025-09 to 2025-12 | 4 | harbor | all | 4 | 0 |
| after 2026-01 to 2026-10 | 10 | — | — | 0 | 10 not_in_source |

- Ice status by month: before = no_observation (first ice row is 2024-10-04); during = closed in 10 months, available in 2025-08 (end-of-month); after = available.
- Only 4 published post-reopening months so far (MFDE 2026 not yet released).

### Charleston: ice, 2019-12-20 to 2020-09-12
| window | months | level / unit | scheme | with value | withheld / blank (all species) | Dungeness-row months: blank / part blank |
|---|---|---|---|---|---|---|
| before 2016-01 to 2019-11 | 47 | harbor, OR-charleston | all | 47 | 0 | 1 / 41 |
| during 2019-12 to 2020-09 | 10 | harbor | all | 10 | 0 | 0 / 10 |
| after 2020-10 to 2024-12 | 51 | harbor | all | 51 | 0 | 3 / 39 |
| after 2025-01 to 2025-12 | 12 | agency group, OR-ODFW-florence-charleston-2025 (3 harbors) | all | 12 | 0 | 0 / 10 |
| after 2026-01 to 2026-10 | 10 | — | — | 0 | 10 not_in_source | — |

- Ice status: before = no_observation; during = closed 9, available in 2020-09; after = available.
- Part-blank Dungeness months are mostly the small bay row (T2.1). The all-species series has no blanks in any window.

### Ilwaco: Landing dock/cranes burned 2024-01-22, not rebuilt
| window | months | level / unit | scheme | with value | withheld (pacfin_confidential) |
|---|---|---|---|---|---|
| before 2016-01 to 2023-12 | 96 | agency group, WA-PACFIN-CLW (Ilwaco + Chinook + non-inventory OCR) | Dungeness crab | 70 | 26, mostly Oct–Jan |
| during 2024-01 to 2026-10 | 34 | same | Dungeness crab | 26 | 8: 2024-01, 2024-06, 2024-11, 2024-12, 2025-07, 2025-09, 2025-11, 2025-12 |
| after | — | no reopening recorded | — | — | — |

- Hoist_crane status: before = no_observation; during = closed in all 34 months. The current status is `not_found` (2026-11 row, low confidence).
- Counted as covered under the logged Gate 2 wording: CLW group, crab only, clearly labeled.
- The fire month itself is withheld. The first published post-fire month is 2024-02.

### Newport: Bornstein processing closure, 2024 (context only)
| window | months | level / unit | scheme | with value | withheld / blank (all species) | Dungeness-row months: blank / part blank |
|---|---|---|---|---|---|---|
| before 2016-01 to 2024-04 | 100 | harbor, OR-newport | all | 100 | 0 | 3 / 83 |
| during 2024-05 to 2024-12 | 8 | harbor | all | 8 | 0 | 0 / 4 |
| during 2025-01 to 2025-12 | 12 | agency group, OR-ODFW-depoe-bay-yachats-2025 (2 harbors) | all | 12 | 0 | 0 / 10 |
| during 2026-01 to 2026-10 | 10 | — | — | 0 | 10 not_in_source | — |

- No in-scope service was lost, so no status column applies.
- **Event month assumption:** the inventory says the plant was closed "by 2024-05-21". The exact closure date is not established, so 2024-05 is used as the window start. T4 may move it.
- Harbor-level data cover only 8 post-event months (May–Dec 2024). After that the series is group-level.

### Facility status before 2026: how much is observed
`t22_status_coverage.csv` gives these counts.
- **Observed status:** 2,198 of 7,540 port-months (29%) have at least one of the 4 services observed, and 510 (7%) have all 4.
  - Fuel 1,241 (16.5%), ice 1,154 (15.3%), hoist_crane 1,193 (15.8%), cold storage 655 (8.7%).
  - In 2016-01, only 1–3 harbors have an observed status for any service. By 2026-10, 17–41 harbors do, depending on the service.
- **127 of 270 facility rows** are dated 2026-11, the month accessed, which is after the panel ends. They set `current_status_*` but never a month in the panel.
- **Pre-closure status is not observed for any closure port.** The first rows are the closure rows themselves (Crescent City 2024-10-04, Charleston 2019-12-20, Ilwaco 2024-01-22). T4 should take event dates from the closure sequences in `docs/data_dictionary.md`, not infer "open" from `status_*` before the event.

## (d) Gate 2 verdict: PASS
| criterion | result | evidence |
|---|---|---|
| Panel joined for all 58 harbors | **Pass.** 58/58 harbors, 7,120/7,120 published port-months joined, 0 failures; 420 not_in_source months listed | §(a); `t22_join_coverage.csv`, `t22_join_gaps.csv` |
| Join does not alter values | **Pass.** 5,044/5,044 unit-months match on pounds, value and flag; totals equal | §(b); `t22_reconciliation.csv` |
| Crescent City covered | **Pass.** Harbor-level, all species; every month before, during and after is published except 2 pre-event months | §(c) |
| Charleston covered | **Pass.** Harbor-level, all species, through 2024; no all-species blanks; group-level in 2025 | §(c) |
| Ilwaco covered | **Pass under the logged wording.** CLW group, crab only, labeled; 8 of 34 post-fire months withheld, including the fire month | §(c) |
| Newport covered | **Pass.** Harbor-level through 2024; group-level in 2025; processing-only event | §(c) |

Limits carried forward: Ilwaco is group-level and crab-only, with the fire month withheld. Newport and Charleston become group-level from 2025. CA and OR have no 2026 months yet. Facility status is mostly unobserved before 2024.
