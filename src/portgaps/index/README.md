# src/portgaps/index — T3.2 single-point-of-failure index

Run from the repo root (no network, ~10 s):

    python -I src/portgaps/index/run_t32.py

Inputs: `data/processed/{ports,facilities,distance_matrix,landings_monthly,port_unit_bridge}.csv`,
`outputs/tables/t21_annual_crosscheck.csv`, `data/interim/sea_routes.geojson`.

| Module | Role |
|---|---|
| `config.py` | Sweep, mid threshold, drop lists, FOSS↔harbor blocks, WA groups, route tests |
| `values.py` | Landed-value basis; `set_value()` = (lower, upper) for a set of cut-off harbors, deduplicated on unit_id |
| `simulate.py` | Current status, distance (×1.06), one-at-a-time removal, ranks |
| `run_index.py` | All runs × thresholds, flags, stability, route checks, checks C1–C9, writes tables |

Outputs (`outputs/tables/`): `index_ranking.csv` (main run, every threshold), `index_sensitivity.csv`,
`index_stability.csv`, `index_rank_by_threshold.csv`, `index_top10_mid.csv`, `index_harbor_values.csv`,
`index_backup_runs.csv`, `index_route_issues.csv`, `index_checks.csv`.
Method: `docs/methods/failure_index.md`.
