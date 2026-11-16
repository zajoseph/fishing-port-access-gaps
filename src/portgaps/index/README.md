# src/portgaps/index — T3.2 single-point-of-failure index

Run from the repo root (no network, ~10 s):

    python -I src/portgaps/index/run_t32.py

Inputs: `data/processed/{ports,facilities,distance_matrix,landings_monthly,port_unit_bridge}.csv`,
`outputs/tables/{t21_annual_crosscheck,t21_units}.csv`, `docs/port_crosswalk.md` (non-inventory unit check), `data/interim/sea_routes.geojson`.

| Module | Role |
|---|---|
| `config.py` | Sweep, mid threshold, drop lists, FOSS↔harbor blocks, WA groups, non-inventory units, s4 no-moorage hoist harbors, route tests |
| `values.py` | Landed-value basis; `set_value()` = (lower, upper) for a set of cut-off harbors, deduplicated on unit_id; `derive_noninventory_units()` |
| `simulate.py` | Current status (same-date tie: later file line wins), distance (×1.06), one-at-a-time removal (s4 own-hoist-only option), ranks |
| `run_index.py` | All runs × thresholds, flags, stability, route checks, checks C1–C10 (C10 runs `review/t33_indep.py`), writes tables |
| `before_after_t34.py` | T3.4 before/after top 10 and hold list → `t34_before_after.csv` |

Outputs (`outputs/tables/`): `index_ranking.csv` (main run, every threshold), `index_sensitivity.csv`,
`index_stability.csv`, `index_rank_by_threshold.csv`, `index_top10_mid.csv`, `index_harbor_values.csv`,
`index_backup_runs.csv`, `index_route_issues.csv`, `index_checks.csv`.
Method: `docs/methods/failure_index.md`.
