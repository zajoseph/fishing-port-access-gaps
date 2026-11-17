# outputs/map — interactive map (T5.1)

A static site deployed to GitHub Pages by `.github/workflows/pages.yml`. There's no build server, no API keys and no tracking.

Live: https://zajoseph.github.io/fishing-port-access-gaps/

## Files

| Path | What it is |
|---|---|
| `index.html`, `css/map.css`, `js/map.js` | The page. All numbers are read from `data/`; nothing is computed in the browser beyond picking a run and threshold. |
| `vendor/leaflet/` | Leaflet 1.9.4 (BSD-2), unmodified, from the official release zip (sha256 in `LICENSE`). |
| `data/harbors.geojson` | 58 harbors. Current status per service = the latest `as_of_date` row in `facilities.csv`; ties go to the later file line (`docs/data_dictionary.md` §5). |
| `data/index.json` | Index results at 25/30/40/50 nm for runs `main`, `s1` and `s4`: stranded low/high, per-service rank, cut-off harbors and nearest backups. `range` = the main–s1 envelope. `hold` = in the top 10 under both runs (`t34_before_after.csv`). `top10` = rank ≤ 10 with stranded_high > 0. |
| `data/events.json` | The five validation closures (six cells) with verdicts by threshold and run (`t33_event_check.csv`). |
| `data/routes.geojson` | Only the harbor-pair routes used as backup routes: 111 of the 1,653 in `data/interim/sea_routes.geojson`. Derived from OpenStreetMap: © OpenStreetMap contributors, ODbL 1.0. |

## Regenerate the data

```bash
python -I src/portgaps/map/build_map_data.py      # from the repo root, ~5 s, no network
```

The script reads only the frozen inputs (tag `v0.9-results-frozen`) and fails if anything disagrees with them:
- Current status must match `t13_latest_status.csv`.
- Every recovered index row (1,764 rows: 3 runs × 4 thresholds) must match `index_sensitivity.csv`, and the main-run cut-off lists must match `index_ranking.csv`.
- Top-10 flags must match `t34_before_after.csv`.
- The 40 nm hold list must match the logged report-language list.

## Display rules (decisions log, report language rule)

- Values are shown as the range across main and s1. s1 treats "no source located" cells as available, so it is a lower bound on stranding.
- Only "holds under both runs" entries carry no range caveat. Garibaldi is always a range.
- s4 (Point Arena and Port Orford can't use another harbor's hoist) is an opt-in, labelled sensitivity.
- "not_found" is labelled "no source located" and drawn differently from "not available".
- Backup = the nearest other working facility for the facility's own harbor and each harbor it cuts off. Distances are in charted-equivalent nm (model nm × 1.06), from the same matrix the index uses.

## Basemap

The basemap is OpenStreetMap standard tiles (`tile.openstreetmap.org`), shown in greyscale with a CSS filter. Use follows the [OSMF Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/): visible attribution, low traffic, the default browser Referer, and no prefetching. If the site's traffic ever grows beyond light use, switch the tile URL in `js/map.js` to a provider with a suitable plan.

Page weight is about 89 KB compressed, excluding basemap tiles. About 80 KB loads up front; the route file (about 10 KB) loads the first time a facility is selected.
