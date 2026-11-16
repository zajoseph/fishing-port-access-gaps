# T3.3 Independent review of the failure index (post-T3.2b)

Date: 2026-11-16 · Reviewed: `main` at 933044e (PR #7 merge) · Branch: `t3.3-review`
Scripts: `src/portgaps/review/` (run `bash src/portgaps/review/run_t33.sh` from the repo root, ~15 s).
Tables: `outputs/tables/t33_event_check.csv` (one row per event × threshold × run), `outputs/tables/t33_landings_descriptive.csv`.

**Gate 3 verdict: PASS, with conditions (§5).** The index reproduces exactly, and an independent reimplementation matches every row. No code bug changes the top 10. Against the five known closures:
- Two agree across 25–50 nm in both runs: Crescent City ice and Charleston ice.
- One disagrees at the headline 40 nm, for a structural reason the method can't represent: Point Arena's launch hoist.
- Two can't be judged on outcome: Ilwaco and Humboldt fuel. Humboldt fuel's structure matches the source.

The events test whether the index finds the backup fleets actually used. They do **not** test the large stranded-value claims (Westport, Astoria, Newport, Bellingham, LA/LB), which still rest on unverified facility cells.

The logged decisions were taken as fixed: 40 nm headline, 25–50 nm stable band, stranded_low rank, current status, the not_found rule and the value basis. Nothing here retunes them.

---

## 1. Reproduction

| Check | Result |
|---|---|
| `python -I src/portgaps/index/run_t32.py` on 933044e (Python 3.10, pandas 3.0.5) | Ran in ~9 s; checks C1–C9 all pass |
| 9 regenerated `index_*.csv` vs committed | **Byte-identical** (all 9) |
| `facilities.csv` | 272 rows, as stated |
| Independent recompute (`t33_indep.py`; imports nothing from `portgaps`; rebuilds current status, ×1.06 distances, access, unit values from `landings_monthly.csv` / `t21_annual_crosscheck.csv`, and the shared-unit arithmetic from scratch) | **6,564 / 6,564** run × threshold × facility rows match `index_sensitivity.csv` on stranded_low and stranded_high (±$1); 0 missing either side |

The independent recompute matters because check C5 in `run_index.py` re-implements access only. It calls the same `set_value()` for the dollars, so it doesn't test the value arithmetic. The recompute above does.

## 2. Code and method review

Reviewed against the logged decisions: `simulate.py`, `values.py`, `run_index.py`, `config.py`, `docs/methods/failure_index.md`.

| Area | Logged decision | Code | Finding |
|---|---|---|---|
| Core simulation | Remove one facility at a time; a harbor is cut off if it had access and loses it | `n_reach == 1 & reach[:, j]` among harbors with baseline access; a harbor is at 0 nm from itself | Correct. Harbors with no baseline access are not attributed to any facility (documented). |
| Distance / threshold | Charted-equivalent nm = sea_nm × 1.06 | `D = sea_nm * 1.06`, compared `<= T + 1e-9` | Correct direction and factor. Matrix symmetric (C8). |
| Value basis | 2019–24 mean annual all-species value, nominal; CA withheld → lower bound; OR harbor where published else unit; WA ALL005 group + FOSS blocks | As logged; 6 calendar years; withheld months → 0 and flagged | Correct. |
| Shared units | Never split; upper = every unit touched (dedup on unit_id); lower = own FOSS/harbor values; joint FOSS ports only when all cut; whole unit only if all inventory harbors cut and no non-inventory ports | `set_value()` | Correct for the multi-harbor units. No double counting: the dedup passes C2, and my recompute agrees. **See finding F2 for single-inventory-harbor ODFW units.** |
| not_found | Main: not_found = absent; s1: not_found = available | `working=("available",)` vs `("available","not_found")` | Correct (C6, C7). |
| Sensitivity s2/s3 | Drop the harbor as both value and backup | `keep` excludes dropped harbors | Correct (C9). All dropped harbors are CA single-harbor units, so no shared-unit side effects. |
| Rank | stranded_low, then stranded_high; $0 ties at the bottom | `_rank_min` | Correct. |

**Bugs:** none that change any number.

**Deviations and fragilities.** Each is listed with its effect on the top 10 at 40 nm.

- **F1: Westport hoist depends on a same-date tie (data, not code).** `facilities.csv` has two `WA-westport · hoist_crane` rows dated `2026-11`: the T1.3 `not_found` row (line 228) and the T3.2b `available/low` row (line 270).
  - Current status is the latest `as_of_date` with a stable sort, so the T3.2b row wins **only because it comes later in the file**. `docs/data_dictionary.md` §5 still says no same-date ties exist.
  - *Effect now:* none, because the result matches the confirmed T3.2b reading.
  - *Effect if the file were re-sorted:* Westport hoist ($65.7–72.0M, hoist #1 at 25–40 nm) would leave the main-run hoist top 10, and Chinook hoist would return. This is the T3.2 "before" state in `t32b_index_before_after.csv`.
  - *Recommendation:* give the T3.2b row a day-level date (2026-11-14) or add an explicit tie rule (later file row wins), and update §5. Editing processed data is out of scope here.
- **F2: Garibaldi and Depoe Bay lower bounds use the whole ODFW table.** Each has its own ODFW unit (`OR-ODFW-gearhart-garibaldi`, `OR-ODFW-netarts-depoe-bay`). Both tables also hold non-inventory ports (Gearhart/Seaside, Cannon Beach, Nehalem, Tillamook; Netarts, Pacific City, Siletz Bay, Salmon River).
  - The code treats a one-harbor unit as harbor value (lower = upper = table value). This is disclosed in the method table ("unit_level = Y … the whole table is used") and fits "OR … else unit-level".
  - However, the logged shared-unit rule says a whole unit counts in the lower bound only if it "has no non-inventory ports". Read literally, Garibaldi's lower bound is $0 (it has no FOSS row), and Depoe Bay's share of any lower bound is $0.
  - *Effect at 40 nm, main:* Garibaldi fuel, hoist and ice go from $8.2M to a range of $0–8.2M. In ice, Garibaldi (#9) leaves the top 10 and Neah Bay ($5.6–124.2M) enters. Newport ice's lower bound goes from $60.7M to $60.3M, with the same rank.
  - *Effect across 25–50 nm:* 1–3 top-10 swaps per threshold in main; none in s1 at 30–50 nm. 129 of 6,564 rows change.
  - *Recommendation:* PM ruling on which reading applies. The code and the method doc are consistent with each other, so this is a decision tension, not a coding error.
- **F3: Check C5 isn't fully independent.** It reuses `set_value()`. Now covered by `t33_indep.py`. Optional: fold it into the index checks.
- **F4: s1 can hide a documented loss.** Ilwaco hoist's current row is `not_found`, recoded in T1.3 because only launch hoists and Travelifts are documented. s1 therefore treats Ilwaco as having a working hoist even though its offload cranes burned in 2024. This is a general property of s1, and the same applies to any other recoded not_found cell. s1 is a lower bound on stranding, not a plausible state.
- **F5: Documentation inconsistencies in the backup-run list** (`DOCUMENTED_BACKUPS` → `index_backup_runs.csv`, method §4).
  - Charleston → Winchester Bay ice is labelled "backup used not documented". In fact `facilities.csv` documents it twice: the Charleston 2019-12-20 row ("interim ice from Hallmark Fisheries and Winchester Bay") and the Winchester Bay 2020-03-03 row.
  - Point Arena → Noyo (34.5 nm, mode "unknown") is not a documented run. It is the nearest-hoist distance, yet the 11–35 nm "documented runs" range quoted for the threshold choice tops out with it. §3 (E4) shows that run was **not** made.
  - Ilwaco → Astoria (11.1 nm) is also a nearest-facility distance, not a documented run.
  - The genuinely documented runs are 20.5–30.9 nm: Crescent City → Brookings, Charleston → Winchester Bay, Trinidad → Humboldt Bay by road, and Santa Barbara → Oxnard. The 40 nm headline still sits above all of them, so the rationale holds. The table labels should be corrected.

## 3. Known-closure check

Method: each event cell goes through the index's own removal logic (`simulate.py` functions, current statuses, both runs) at 20 (context), 25, 30, 40 and 50 nm.
- Ilwaco's cells are no longer `available` (post-fire), so for E3 the event cell is set back to its pre-event `available` before removal. This is a review step only; the index is unchanged.
- Landings comparisons are descriptive: mean monthly value during the event window vs the same calendar months in the three prior years. They are not causal estimates.

### Event table (headline 40 nm; band 25–50 nm; both runs agree unless noted)

| Event | Index says at 40 nm (main = s1) | Across 25–50 nm | Nearest backup (charted-eq. nm) | Documented backup used | Descriptive landings (during ÷ prior-3-yr same months) | Verdict at 40 | Reason |
|---|---|---|---|---|---|---|---|
| **E1 Crescent City ice**, 2024-10-05 → ~2025-08 | Strands nothing (rank 15 main / 6 s1, $0) | Same at 25–50; at ≤20 nm it would strand Crescent City ($15.5M) | Brookings 20.5 (2nd: Humboldt Bay 67.7) | **Brookings**, ice trucked from Pacific Seafood's plant | Crescent City 0.95× (11/11 months published); Brookings tables 1.19× | **Agree** | Predicted backup = actual backup; landings held. Trucked, so this bounds distance; it's not a vessel run. The 20.5 nm run was one input to the threshold choice, so agreement is partly built in. |
| **E2 Charleston ice**, 2019-12-20 → 2020-09-12 | Strands nothing (rank 15 / 6, $0) | 30–50: none. 25: Bandon ($0–4.8M) only | Winchester Bay 23.4 (2nd: Port Orford 44.4) | **Winchester Bay** ice plant (2020-03-03 row); also Hallmark Fisheries in Charleston | Charleston 0.66× (10/10); Winchester Bay table 0.97× | **Agree** (25 nm: agree for Charleston, can't tell for Bandon) | Predicted backup = documented backup. Landings fell a third, but the window overlaps COVID-2020, so it can't be read as an access effect. Also an input to the threshold choice. |
| **E3a Ilwaco Landing dock/cranes**, closed 2024-01-22 | Strands nothing | Same | Chinook 4.6 (2nd: Warrenton 10.9, low) | None documented | CLW group, Dungeness only: 0.87× (8/12 published, 4 withheld); Astoria table 1.47× | **Can't tell** | No documented backup. Chinook's "wharf hoists" row is dated 2026-02; its 2024 state is undocumented. Landings are group-level crab-only and can't isolate Ilwaco. |
| **E3b Ilwaco ice** (lost 2024-01-22; "no more ice" 2025-04-09) | Strands nothing | Same | Astoria 11.1 (s1: Warrenton 10.9, not_found) | None documented | as E3a | **Can't tell** | As E3a. Chinook ice was planned (2026), not available, which matches the event-time state. |
| **E4 Point Arena hoist**, 2025-10-18 → 2026-01-29 | Strands nothing (Noyo hoist in reach) | 25–30: strands Point Arena ($0.58M); 40–50: nothing | Noyo 34.5 (2nd: Bodega 54.0) | **None**: pier closed to all vessels; fleet missed the 2026-01-12 crab opener | Oct 2025 $53k (published); Nov–Dec 2025 withheld (often withheld in 2016–20 too, so uninformative); Noyo 1.17× Oct–Dec | **Disagree** (agree at 25–30) | Point Arena has no moorage. Boats are launched and recovered by the hoist, so when it fails the fleet can't get on the water at all. A 34.5 nm open-coast run to Noyo isn't a substitute for a hoist-launched small-boat fleet. The index models offload by vessel run and can't represent this. Low value ($0.58M); no top-10 effect. |
| **E5 Humboldt Bay fuel dock**, 2026-01-01 → 01-16 | Fuel **#1**: strands Humboldt Bay + Trinidad ($11.8M), main and s1 | 25–40: same ($11.8M, #1–2); 50: Humboldt Bay only ($9.9M) | Shelter Cove 60.8 (low, recreational listing); Crescent City 67.7 | None documented | CA 2026 months not yet released | **Can't tell (outcome); structure consistent** | The source calls it "the only commercial refueling dock between Fort Bragg and Crescent City", which matches the index. The 16-day closure has no documented response and no landings data yet. |

Full detail, with every threshold and both runs, is in `outputs/tables/t33_event_check.csv` (60 rows: 6 event cells × 5 thresholds × 2 runs).

### Facility state at event time vs current status
- **E1, E2, E4:** the backups the index uses were in place at event time: Brookings ice, Winchester Bay ice (documented in use 2020-03), and Noyo hoist (reopened 2020).
- **E3:** Chinook hoist's state in 2024 is undocumented (its only row is dated 2026-02). Astoria ice comes from the 2023 Snapshot, so it predates the event.
- **E5:** Shelter Cove fuel is an undated recreational listing (low confidence).
- **Crescent City ice today is `available`.** Ocean Gold restarted the plant by 2025-08-27, so the index's current status matches the post-event state, not the event.

### What the events do and don't test
- **E1 and E2 test** whether the index picks the backup fleets actually used, and whether a harbor with a backup at ~20–25 nm is treated as not stranded. It does both, at every threshold in the band and in both runs. Both runs were also among the inputs used to set the threshold above 25 nm, so this is a consistency check rather than out-of-sample validation.
- **E4 tests** the vessel-run assumption at a harbor without moorage, and it fails at 40 nm. The same structure applies to Port Orford, the other harbor where the dual-use launch hoist counts as hoist_crane.
- **None of the five events** removes a facility behind the large top-10 values except Humboldt fuel, which has no outcome data yet. The magnitudes behind Westport, Astoria, Newport, Bellingham and LA/LB are untested by any closure.

## 4. Headline claims under both main and s1

At 40 nm, 33 top-10 entries carry value > 0 in main. **13 keep value under s1; 20 fall to $0.** Across 25–50 nm, 65 of 137 keep value and 72 fall to $0.

**Claims that hold in both runs at 40 nm and across 25–50 nm** ($M/yr, low–high):
- **Charleston cold storage** 31.0–36.0 (cuts Charleston, Winchester Bay, Bandon): rank 4 main, 2 s1.
- **Brookings cold storage** 24.5–25.3 (includes Crescent City): rank 6 main, 3 s1.
- **Humboldt Bay fuel and ice** 9.9–11.8 (Humboldt Bay; plus Trinidad at 25–40): fuel #1 in both runs at 40.
- **Bodega Bay**, all four services: 9.1 (a single-harbor dependency; ice from 30 nm).
- **Garibaldi** fuel and hoist (25–50), ice (40–50): 8.2. **Subject to F2:** under the literal non-inventory reading these become $0–8.2M.
- **Shelter Cove fuel** 0.46 (30–40), and **Florence hoist** $0–6.3M (40).

**Claims that do not hold under s1 at 40 nm** (main-run values drop to $0 when not_found cells count as available): Westport ice, cold storage and hoist (72.0 / 72.0 / 65.7–72.0); Astoria ice and cold storage (65.4–66.8); Newport ice (60.7); Bellingham ice and cold storage (39.7–52.2); LA/LB ice and cold storage (26.4); San Diego Bay; Neah Bay; Seattle; Port Angeles; Noyo. These should be stated only as "up to" values, conditional on the unverified cells (largest: Willapa, Ilwaco and Chinook cold storage and ice; Westport hoist itself is low confidence).

## 5. Gate 3 verdict

**PASS, with conditions.** Against the known closures, the index behaves sensibly within its stated limits:
- It reproduces exactly, and no code error affects the top 10.
- Where a closure had a documented backup, the index names that backup as the nearest facility (E1, E2).
- Its one clear miss at the headline (E4) comes from a structural limit (launch-hoist harbors) on a small dollar value. It doesn't point to an error in distances, values or arithmetic.

Conditions for using the index in the report:
1. State the headline as ranges between main and s1. Only the §4 "hold" list may be stated without the "up to / if unverified cells are absent" qualifier.
2. Disclose that the closures validate backup identification, not stranded-value magnitudes. They are also partly in-sample for the threshold (E1, E2).
3. Disclose the launch-hoist limit (Point Arena, Port Orford). The index understates hoist dependency at harbors without moorage.
4. Resolve F1 (Westport same-date tie) before the dataset is released, so the headline hoist result doesn't depend on row order.
5. PM ruling on F2 (Garibaldi/Depoe Bay lower bound) before the report quotes Garibaldi as a holding claim.

**What would change the verdict:**
- **Toward FAIL:**
  - T4.1 finding that Crescent City landings disappeared rather than held or shifted during the closure. The descriptive 0.95× argues against this, but T4.1 is the test.
  - Evidence that Charleston didn't actually rely on Winchester Bay ice.
  - A further closure at a *moored* harbor where a backup sat within 25–50 nm but the fleet stopped. That would mean the vessel-run threshold is too generous, not just the launch-hoist case.
- **Toward a stronger PASS:**
  - Calls on the 40 unverified T3.2b cells, which would turn the main-vs-s1 brackets into point results.
  - CDFW 2026 data for Humboldt Bay and Trinidad in January 2026 (E5) and Point Arena Nov 2025–Jan 2026 (E4).
  - A documented backup for Ilwaco (E3).

## 6. Recommendations (report only; method, threshold and rank are not changed here)

- **R1:** Fix F1 in the data: day-date the T3.2b Westport row or add a tie rule, then update dictionary §5. Then rerun.
- **R2:** PM ruling on F2. If the literal reading is chosen, set the two units' `noninv` flag. That is a one-line config change, but it changes a logged-method reading, so it needs approval.
- **R3:** Add a flag (not a method change) for no-moorage launch-hoist harbors in the ranking tables, so readers see that hoist backups there aren't real substitutes.
- **R4:** Correct `DOCUMENTED_BACKUPS` labels (F5): Charleston → Winchester Bay = documented; Point Arena → Noyo = not a run. Optionally add `t33_indep.py` as check C10 (F3).
- **R5:** In the report, describe s1 as a lower bound on stranding, not a plausible state (F4).
