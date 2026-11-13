# Monthly landings panel (T2.1): notes and README

As of 2026-11-13. Files: `data/processed/landings_monthly.csv` (35,123 rows), `data/processed/withheld_log.csv` (46,436 rows), `docs/port_crosswalk.md`, `data/manifest.csv`. Rebuild from the repo root:

```
python -I src/portgaps/ingest/odfw_ftr205.py data/raw/landings/odfw data/interim/odfw_ftr205_cells_all.csv
python -I src/portgaps/clean/build_landings_t21.py
python -I src/portgaps/clean/qa_landings_t21.py
python -I src/portgaps/clean/write_crosswalk_t21.py
```
Raw files sit under `data/raw/landings/{cdfw,odfw,pacfin,foss}/` (not committed; listed with sha256 in `data/manifest.csv`).

## Window and sources
| State | Source | Months | Level | Species |
|---|---|---|---|---|
| CA | CDFW MFDE Custom Queries export, calendar year | 2016-01 to 2025-12 (MFDE runs to the last complete year) | harbor (CDFW codes summed per harbor) | all; 22 MFDE species groups; Dungeness crab |
| OR | ODFW FTR205 "Pounds and values by port" PDFs, all FINAL | 2016-01 to 2025-12 | ODFW port or port-group table | all; 4 ODFW categories; Dungeness crab (ocean + bay rows) |
| WA | PacFIN APEX CRAB002, Dungeness crab by port group | 2016-01 to 2026-10 | PacFIN port group (CLW, CWA, NPS, SPS) | Dungeness crab only |

PacFIN ALL005 (annual, by port group) and NOAA FOSS (annual, by major port) are cross-checks only, in `outputs/tables/t21_annual_crosscheck.csv`.

Values are nominal dollars as published, with no inflation adjustment. Pounds: MFDE as published; ODFW round weight by dealer purchase date; CRAB002 round weight converted from metric tons (x 2204.62262; the source rounds to 0.01 t, about 22 lb).

## Columns (`landings_monthly.csv`)
| column | meaning |
|---|---|
| unit_id | reporting unit. CA harbors and the two ODFW single-harbor tables use the inventory `port_id`; groups use `OR-ODFW-…` or `WA-PACFIN-<group>` |
| unit_type | `harbor` / `code_group` / `agency_group` (see crosswalk). `state_group` is not used |
| unit_name, state | as published (ODFW table name, PacFIN group) |
| port_ids | inventory harbors the unit covers, `;`-separated. Join to `ports.csv` on these |
| agency_codes | CDFW codes, PacFIN codes or PacFIN group behind the unit |
| year, month | calendar month. CRAB002 crab year Y = Nov Y-1 to Oct Y (checked against ALL005 calendar years) |
| species_scheme | `all`, `MFDE species group`, `ODFW category`, `Dungeness crab` |
| species_group | `all`, the group or category name, or `Dungeness crab`. Names differ by state; only `all` and `Dungeness crab` compare across states |
| pounds, value_usd | integers; null when withheld |
| vessels | blank everywhere. MFDE shows vessel counts only on its Visualize page, one port at a time; no export used here carries them. ODFW and PacFIN publish none |
| source | `cdfw_mfde`, `odfw_ftr205`, `pacfin_crab002` |
| withheld_flag | see below |
| n_components, n_withheld | for summed units: number of codes/rows summed, and how many were withheld or blank |
| pounds_basis | weight convention |

**Row density.** `all` and `Dungeness crab` rows are complete: every unit × month in the window has a row. `MFDE species group` and `ODFW category` rows are sparse. A missing row means the source printed no row, which is read as no landings recorded.

## withheld_flag
| flag | meaning | values |
|---|---|---|
| none | published number | as published |
| confidential | MFDE "Confidential" for every reporting code of the harbor | null |
| partial_confidential | multi-code CA harbor: some codes "Confidential", others published | sum of published codes = **lower bound** |
| pacfin_confidential | PacFIN "-" with "*" in the Confidential column | null |
| blank_assumed_zero | ODFW cell printed blank | **0 by assumption** (see below) |
| part_blank_assumed_zero | ODFW sum of rows (Dungeness ocean + bay) or measures where some cells are blank | blanks counted as 0 |
| no_record_zero | MFDE has no row for that port-month, or ODFW printed no Dungeness row that year | 0 (no landings recorded; not a withheld cell, so not in the log) |
| dash_assumed_zero | PacFIN "-" without "*" | 0. None occur in the WA window |

## ODFW blank-cell assumption (decision 2026-11-12)
ODFW FTR205 tables print no suppression flag, so a blank cell may be a true zero or a suppressed value. **This panel sets ODFW blanks to 0.** That is a documented assumption; ODFW was not asked. Every blank cell is still logged in `withheld_log.csv` (`flag = blank_assumed_zero`). To rerun with blanks as missing, set `pounds`/`value_usd` to null where `withheld_flag` is `blank_assumed_zero` (and treat `part_blank_assumed_zero` as a lower bound), or rebuild from the log.

How much this matters: **no ODFW all-species (`Total`) cell for any inventory table is blank** in 2016–2025. The only blank Total cells (20 month-rows) are in the Columbia River table, which is not in the panel. Blanks in the panel fall in:
- category rows: 596 (Molluscs 277, Other Invertebrates 257, Fish 36, Crustaceans 26);
- Dungeness crab rows: 70 fully blank, plus 637 rows where only one of the ocean or bay rows is blank (`part_blank_assumed_zero`; usually the bay row).

## withheld_log.csv
One row per withheld or blank cell: MFDE "Confidential" (all three exports, every port, inventory or not); ODFW blanks (all levels: total, category, species; Columbia River table included); every PacFIN CRAB002 "*". A PacFIN "-" without "*" is logged only where the panel uses it. ODFW cells blank in both measures are one row (`measure = pounds+value`). `used_in_panel = Y` marks cells behind a panel value. ALL005 cells are not logged (cross-check only). Window: 2016-01 onward.

## Known limits
- **WA is crab-only and group-level.** CLW (Ilwaco + Chinook + other Columbia River WA ports) is withheld in 34 of 130 months, including most Oct–Dec periods, **Jan 2024 (the month of the Ilwaco Landing fire), Jun 2024 and Nov–Dec 2024.**
- **CA multi-code harbors.** Humboldt Bay (84 months) and LA/LB (98 months) are mostly `partial_confidential`: small codes such as King Salmon, Arcata or Wilmington are withheld while the main codes are published. Treat these months as lower bounds.
- **Small CA harbors are often fully withheld:** Vallejo 80/120 months, Avalon 72, Huntington Harbour 52, Port Hueneme 42, Marina del Rey 33, Redondo Beach 33, Point Arena 28.
- **ODFW 2025 regrouping:** Newport and Charleston are not available alone after Dec 2024.
- **ODFW Astoria table** = PacFIN AST (Astoria + Warrenton). No Warrenton-only figure exists publicly.
- The 2019 ODFW statewide monthly report did not parse, so the statewide-sum check covers 2016–2018 and 2020–2025. The 2019 port tables pass their own row-total checks.
- PacFIN WA coastal crab shows prices of $0.01–0.17/lb in some Nov–Jan months (e.g., Nov 2025). Kept as published.
- 2026 PacFIN months may still be revised.
