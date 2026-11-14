# Sea-route distances (T3.1)

Harbor-to-harbor distances by water for the 58 inventory harbors in `data/processed/ports.csv`.
Outputs:
- `data/processed/distance_matrix.csv`: 3,306 ordered pairs
- `data/interim/snapped_ports.csv`
- `data/interim/sea_routes.geojson`: 1,653 route lines
- `outputs/tables/t31_checks.csv`, `t31_validation.csv`, `t31_burn_spots.csv`, `t31_landcheck_routes.csv`
- `outputs/figures/t31_route_insets.png`

Code: `src/portgaps/distances/` (run order in its README.md). As of 2026-11-13.

## What the distance means

`sea_km` is the length of the shortest water path between the two harbors' **snapped points**. It's measured on the WGS84 ellipsoid and follows mapped water (OSM shoreline at mean high water) through the real entrances of bays, rivers and sounds. `sea_nm = sea_km / 1.852`. The matrix is symmetric: each value is the mean of the a→b and b→a route lengths, which are smoothed independently (see check C2).

It is **not** a sailing distance. It ignores depth, dredged channels, traffic lanes, buoyed approaches, clearance off headlands, bar conditions, weather and vessel size. Bar conditions and weather are out of scope by decision. A boat follows charted tracks, so real runs are longer. Against NOAA's published distances (below) the gap is a median of about –6%. **Treat sea_km as a lower bound on the run between two harbors.** The bias is fairly uniform, so rankings and backup-distance comparisons in T3.2 hold up. A T3.2 threshold stated in "charted miles" should be divided by about 1.06 before it's applied to this matrix, or the matrix multiplied by about 1.06. That's a PM decision for T3.2; nothing is scaled here.

The snap leg (inventory point → nearest connected water cell) is **not** included. Snap distances are in `snapped_ports.csv`; every one is under 1 km. `ports.csv` is unchanged.

## Geometry: choice and why

| Option | Tested? | Outcome |
|---|---|---|
| GSHHG v2.3.6 full resolution (via basemap-data-hires on GitHub) | Yes, rasterized at 100 m | **Rejected.** No Mission Bay or Bodega Harbor; Humboldt Bay is a fragment; Morro Bay entrance closed; Oregon river harbors missing. Snaps up to 2.9 km. |
| Natural Earth 10m | No | ~1:10M; coarser than GSHHG. |
| NOAA Medium Resolution Shoreline (1:70k) | No | Download site refused access (HTTP 403) from the browser used for fetching; lines only (would need polygon assembly). |
| **OSM land polygons (osmdata.openstreetmap.de, split, WGS84) + OSM inland-water polygons near harbors (Overpass)** | **Yes, used** | Mapped at harbor scale (marina basins, jetties, river mouths); current (2026-11-13); polygons, not lines; ODbL. |

**Chosen: OpenStreetMap.** The land polygons come from OSM's `natural=coastline`, which in many places closes off estuaries at the river mouth. So I added OSM water areas (`natural=water`, `waterway=riverbank`) within ±0.12° of each harbor. Those cover the Siuslaw, Umpqua, Coquille, Rogue, Yaquina, Skipanon, Napa/Mare Island Strait, Swinomish Channel, Salmon Bay above the Ballard Locks, and Marina del Rey basins. Marina polygons were downloaded but not used, since they often include parking and docks.

How it was fetched: the analysis workspace has no access to these hosts, so both downloads ran as scripts in a web browser (`src/portgaps/distances/fetch_osm_browser.js`). The 926 MB land-polygon zip was streamed with byte-range requests and only the 7,022 shapefile records intersecting lon −126.6…−116.4, lat 31.9…49.6 were kept (of 875,164). File hashes are in `data/manifest.csv`. Raw files go in `data/raw/geometry/shoreline/` (not committed).

## Method

1. **Projection.** A coast-aligned oblique frame: the sphere is rotated so the great circle from San Diego (32.6 N, 117.2 W) to Bellingham (48.9 N, 123.0 W) becomes the equator. x = distance along the coast, y = distance across. Within the ±450 km band the scale error is <0.1%. Final lengths are geodesic anyway.
2. **Raster.** Three overlapping tiles at **100 m** cells: S (x −30…480 km), M (420…1,300), N (1,240…1,920). Land polygons are rasterized at 25 m (4×4 supersample), fills plus outlines so thin jetties and spits stay continuous, and OSM water polygons are carved out. A cell is water if it is <50% land.
3. **Thin barriers.** Jetties, breakwaters and spits narrower than a cell can disappear under the 50% rule. Three fixes:
   - (a) A cell becomes land if its 25 m land pixels split its water into separate parts.
   - (b) Diagonal-only water connections across land corners are removed.
   - (c) **Burn-in:** at every place where the topological crossing test (check C4) found a route crossing land, all cells within 1 km that contain any 25 m land pixel become land. Then routing is rerun until the test finds no crossings. Four iterations; 16 spots in `outputs/tables/t31_burn_spots.csv` (LA/LB Middle Breakwater, Columbia south jetty, Grays Harbor south jetty, Ediz Hook base, Dungeness Spit root, Semiahmoo Spit, Blaine and Bellingham breakwaters, Port Hueneme west jetty). The Port Hueneme spot overrides the Channel Islands harbor zone.
4. **Harbor zones.** Some harbors sit on channels narrower than a cell. Within 3 km of those harbors only, a cell counts as water if it is <75% land, and fixes 3(a)–(c) don't apply. A zone is added only where the strict raster disconnects the harbor, meaning the zone reduces its snap by >300 m. Zones (8): Channel Islands, Huntington Harbour, Newport Beach, Santa Cruz, Noyo, Brookings, Seattle (Ballard Locks), La Conner (Swinomish Channel). Routing cost in relaxed cells is 1.5× so routes don't run along beaches through them; length is still measured on the geometry.
5. **Connected water.** Only the largest 8-connected water component (the ocean) is routable. Disconnected lakes and ponds are ignored.
6. **Snapping.** Each harbor point moves to the nearest ocean-connected cell centre (Euclidean distance transform). This is for routing only.
7. **Least-cost paths.** `skimage.graph.MCP_Geometric`, 8-connected, run from every harbor in its home tile. Tiles are stitched at portal lines (x = 450 km and x = 1,270 km), with one portal every 2 km across the overlap. Harbor↔harbor, harbor↔portal and portal↔portal segments are smoothed (step 8). A Dijkstra search then runs on their **geodesic lengths**, not grid costs. Grid costs tie across many portal choices, and picking by cost had left kinks of up to 60 km.
8. **Any-angle smoothing.** Grid paths are string-pulled. A vertex is skipped wherever the straight segment stays in cells that are ≥75% water; bend points are then refined along the raw path. Each segment is smoothed from both ends and the shorter result is kept. The greedy pass is direction-sensitive (median 2.6 km gap between directions). An exact dynamic-programming search over raw-path vertices, run on two long segments, came within 0.1–0.2% of the kept value. Smoothing removes the 8-direction zig-zag, which overstates length by up to ~8%.
9. **Length.** Smoothed vertices go back to lat/lon, and segment lengths are summed with Vincenty's inverse formula on WGS84.

Resolution: 100 m cells, 25 m land test. After smoothing, the grid adds an expected length error of under ~0.5% per route.

## Entrance handling

No hand-placed waypoints are used: routes go through entrances because that is where the water is. The inset figure (`outputs/figures/t31_route_insets.png`) shows routes from every enclosed-water harbor:
- SF Bay through the Golden Gate (Vallejo via San Pablo Bay and Mare Island Strait)
- Humboldt Bay through the bar
- Columbia River harbors (Astoria, Warrenton, Ilwaco, Chinook) through the river mouth between the jetties
- Willapa Bay harbors through the Willapa entrance
- Puget Sound harbors through Admiralty Inlet and the Strait of Juan de Fuca
- LA/LB through the breakwater gaps
- San Diego Bay and Mission Bay through their entrances
- Avalon by open water

Check C4 tests every route.

## Checks (outputs/tables/t31_checks.csv)

| ID | Check | Result |
|---|---|---|
| C1 | 58×58 complete, no nulls | PASS: 3,306 ordered pairs, 0 null |
| C2 | Symmetric | PASS: exact (max difference 0.0000 km) |
| C2b | Smoothing audit | Shorter direction kept; other direction longer by median 2.6 km; DP spot check within 0.2% |
| C3 | Triangle inequality, all 58³ triples | PASS: 0 violations >0.5 km (worst 0.001 km) |
| C4 | No route crosses land (every route, 25 m vector mask, topological test) | PASS: 0 crossings in 1,653 harbor routes and 30 NOAA reference routes; corner grazes ≤225 m |
| C5 | Snap moves >500 m | 4 listed above |
| C6 | ≥10 published pairs | 33 pairs; median –5.9%; 8 flagged >10%, all explained below |

## Comparison with published distances

Source: NOAA Office of Coast Survey, *Distances Between United States Ports*, 2025 (14th) ed., Tables 28–31. Model distances are routed between NOAA's own listed endpoint coordinates, so the comparison is like-for-like rather than between inventory harbors.

33 pairs (30 using NOAA's own endpoint coordinates, 3 Columbia River pairs using inventory points as proxies). NOAA-coordinate pairs: median error -5.7%, mean |error| 7.7%. All pairs: median -5.9%, 8 flagged above 10%.

| Pair | NOAA table | Type | Published nm | Model nm | Error | Note |
|---|---|---|---|---|---|---|
| san-diego – los-angeles | T28 | coastwise | 95 | 89.0 | -6.3% |  |
| san-diego – newport-beach | T28 | coastwise | 78 | 72.5 | -7.1% |  |
| long-beach – newport-beach | T28 | coastwise | 25 | 28.3 | +13.2% | **>10%** NOAA Long Beach point is in an inner-harbor slip; its link south to Queen's Gate is narrower than a cell, so the model exits west via Angel's Gate (model longer). |
| los-angeles – santa-barbara | T28 | coastwise | 90 | 85.0 | -5.6% |  |
| port-hueneme – santa-barbara | T28 | coastwise | 29 | 28.8 | -0.7% |  |
| santa-barbara – port-san-luis | T28 | coastwise (Pt Conception) | 91 | 87.5 | -3.8% |  |
| port-san-luis – monterey | T28 | coastwise | 121 | 114.5 | -5.4% |  |
| monterey – san-francisco | T28 | cross-entrance (Golden Gate) | 96 | 85.8 | -10.6% | **>10%** NOAA runs to the Golden Gate traffic-lane approach and Monterey sea buoy; model hugs the coast past Pt Año Nuevo and Pt San Pedro. |
| san-diego – san-francisco | T28 | long coastwise + entrance | 455 | 433.9 | -4.6% |  |
| san-francisco – eureka | T28 | cross-entrance (Golden Gate, Humboldt Bar) | 232 | 218.2 | -5.9% |  |
| eureka – crescent-city | T28 | cross-entrance (Humboldt Bar) | 64 | 62.3 | -2.7% |  |
| crescent-city – coos-bay | T28 | cross-entrance (Coos Bay) | 125 | 112.6 | -9.9% |  |
| coos-bay – newport-or | T28 | cross-entrance (2 bars) | 92 | 87.8 | -4.6% |  |
| florence – newport-or | T28 | cross-entrance (2 bars) | 43 | 41.4 | -3.7% |  |
| depoe-bay – newport-or | T28 | short coastwise | 16 | 12.9 | -19.4% | **>10%** Short pair; NOAA includes the run out to and back from both approach buoys (~1.5 nm each). |
| newport-or – astoria | T28 | cross-entrance (Columbia) | 115 | 108.5 | -5.7% |  |
| garibaldi – astoria | T28 | cross-entrance (Tillamook, Columbia) | 58 | 52.4 | -9.7% |  |
| astoria – cape-flattery | T28 | cross-entrance (Columbia) | 153 | 144.5 | -5.6% |  |
| san-francisco – astoria | T28 | long coastwise + 2 entrances | 567 | 553.0 | -2.5% |  |
| san-francisco – vallejo | T29 | in-bay | 23 | 21.4 | -7.0% |  |
| cape-flattery – neah-bay | T31 | short | 10 | 7.9 | -21.0% | **>10%** Short pair; NOAA reference point is offshore of the cape and uses the buoyed approach round Waadah Island. |
| neah-bay – port-angeles | T31 | Strait of Juan de Fuca | 54 | 53.0 | -1.9% |  |
| port-angeles – port-townsend | T31 | Strait | 32 | 30.3 | -5.3% |  |
| port-townsend – seattle | T31 | in-sound | 40 | 36.8 | -8.0% |  |
| seattle – everett | T31 | in-sound | 30 | 27.9 | -7.0% |  |
| everett – anacortes | T31 | in-sound (Saratoga/Deception?) | 49 | 45.9 | -6.3% |  |
| anacortes – bellingham | T31 | in-sound | 17 | 15.6 | -8.2% |  |
| bellingham – blaine | T31 | in-sound | 38 | 26.0 | -31.6% | **>10%** Model uses Hale Passage (east of Lummi Island) and the drying bar off Portage Island; NOAA track goes round Lummi Island. Real difference in route choice; depth not modeled. |
| neah-bay – seattle | T31 | Strait + sound | 116 | 113.4 | -2.2% |  |
| seattle – bellingham | T31 | in-sound | 80 | 76.5 | -4.4% |  |
| WA-ilwaco – OR-astoria | T30 | in-estuary (Columbia) | 13 | 10.5 | -19.2% | **>10%** Proxy endpoints (inventory harbor points; Table 30 gives no coordinates); NOAA follows the dredged channel. |
| OR-warrenton – OR-astoria | T30 | in-estuary (Columbia) | 4 | 3.3 | -17.5% | **>10%** Proxy endpoints; 4 nm pair, so a 0.7 nm difference is 18%. |
| WA-ilwaco – OR-warrenton | T30 | in-estuary (Columbia) | 12 | 10.3 | -14.2% | **>10%** Proxy endpoints; NOAA follows the dredged channel across the estuary. |


Pattern: the model is shorter on nearly every pair, by 2–10% on most. That fits a shortest-water-path model set against charted track lines that run out to sea buoys, follow traffic lanes and dredged channels, and keep off headlands. The largest gaps are short pairs (approach buoys add a fixed 2–3 nm), proxy endpoints, and Bellingham–Blaine (a real difference in route choice).

## Known limits

- **No depth or tide.** Intertidal flats mapped as water at mean high water can be crossed. Example: Bellingham↔Blaine cuts the drying bar between Portage Island and Lummi Peninsula, then goes through Hale Passage. NOAA's 38 nm track goes round Lummi Island; the model gives 26.5 nm.
- **No clearance.** Routes graze headlands and jetty tips. NOAA tracks run to sea buoys (Columbia "CR", Yaquina, Humboldt, Golden Gate traffic lanes). That accounts for most of the negative bias.
- **Sub-cell channels.** In the 7 harbor zones the channel is narrower than 100 m. Routes there can cross up to ~200 m of mapped land (the raster's resolution limit), adding or removing <0.3 km.
- **Snap distances**: 4 harbors over 500 m. Humboldt Bay 880 m (inventory point on land 0.9 km from the bay; snaps into the bay), Redondo Beach 762 m, Port Hueneme 707 m (basin closed by burn-in; snaps to the harbor entrance), Dana Point 670 m. All were checked visually and land in the right harbor's water. Bellingham (361 m) and Blaine (283 m) snap just outside their breakwaters after burn-in.
- **Sub-cell harbor channels.** Some inner basins are narrower than a cell: Long Beach inner harbor, Port Hueneme, Blaine, the Squalicum basin. Routes enter at the nearest resolved water, a <1 km error.
- **OSM coastline** is a crowd-sourced, current shoreline, not a charted one. Breakwaters and jetties are included where OSM maps them as land.
