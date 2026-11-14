# Sea-route distances (T3.1): run order

All scripts run from one working folder that holds the raw inputs (see data/manifest.csv for sources and hashes):
`osm_uswest.bin` (OSM land polygon records; fetch_osm_browser.js), `osm_water.json` (Overpass), and
`noaa_refs.csv` / `noaa_pairs.csv` (validation endpoints and published distances, in this folder).
They need numpy, scipy, scikit-image, pandas, Pillow and matplotlib, plus repo data/processed/ports.csv (path set in common.py).

1. `python raster_osm.py osm_uswest.bin osm_water.json S M N`, then rename tile_*.npz to base_*.npz
   (builds 100 m tiles and the 25 m land masks land25_*.npy)
2. `python build_tiles.py`: harbor zones where needed, thin-barrier fixes (barriers.py), burn-in from burn_spots.csv
3. `python route.py noaa_refs.csv`: least-cost paths per tile plus portals (~20 min, ~2.5 GB RAM). Writes route_raw_noaa_refs.pkl
4. `python outputs.py`: smoothing, graph search on geodesic lengths, matrix and snapped ports (~12 min)
5. Checks: `crosscheck.py` (land crossings), `landcheck.py` (land-run stats), `validate.py` (NOAA), `checks.py` (t31_checks.csv)
6. `python geo_fig.py` (sea_routes.geojson) and `python plotroutes.py routes_h.pkl t31_route_insets.png`

If crosscheck.py reports a CROSSING, add its lat/lon to burn_spots.csv (half_km 1–2.5; force=True only to override a
harbor zone) and repeat from step 2. Method and limits: docs/methods/sea_routes.md.
