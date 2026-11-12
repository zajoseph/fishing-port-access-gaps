# Oregon Coastal Ports Snapshot, Fig. 5: how the cells were read (T1.2)

Read on 2026-11-12 in chat T1.2. These are the working notes behind the `source_type = snapshot` rows in `data/processed/facilities_orwa.csv`.

## Sources
- **Primary:** *Oregon Coastal Ports: A Biennial Snapshot*, 2024 ed., **Fig. 5 "Blue Economy Indicators and Infrastructure for Oregon Coastal Ports", p. 15** (PDF page 15 of 38).
  https://visittheoregoncoast.com/wp-content/uploads/2024/05/Oregon-Coast-Ports-A-Biennial-Snapshot-Report.pdf
  The facts are dated 2023 (interview year; decisions log 2026-11-11). They describe port districts, not individual harbors.
- **Cross-check:** 2021 ed., **Summary Chart 2 "Infrastructure Development and Port Services", p. 5**, rows "Crane Dock Service", "Ice" and "Fuel". This chart has no cold storage row.
  https://visittheoregoncoast.com/wp-content/uploads/2021/04/Oregon-Coastal-Ports-A-Biennial-Snapshot-.pdf

## Why the reading was needed
The Fig. 5 cells are coloured squares with no text, so text extraction returns nothing for them.

## How cells were read
1. I opened the PDF in the Claude desktop built-in browser, using `#page=15&zoom=page-fit` with a 1400×1800 viewport. The pane renders at about 800 px wide, so each cell is about 14 px.
2. I took a zoomed crop of the table with the header and the 14 district rows. The crop covers screenshot region x 328–645, y 85–425 and is 317×340 px, saved as a lossless PNG.
3. I classified the pixels in Python (Pillow):
   - **Grid lines:** found as columns and rows of dark pixels (R+G+B < 200), then merged. This gave 14 column cells starting at x≈112 (about 14.4 px wide) and row cells about 17.5 px tall. The last (Umpqua) row ran past the detected bottom line, so I sampled it at y = 330 and 334.
   - **Cell colour:** the mean of a 3×3 sample (±2 px) at each cell centre, classified with these rules:
     - **R (red):** r > 150 and g < 130, around (200, 100, 85).
     - **P (pale):** r > 170 and g > 200.
     - **T (teal):** g > 130, around (90, 150, 143).
     - **G (dark green):** everything else, around (57, 102, 92).
4. **Check:** the classified Astoria row (G G G G G G R G G R G G T G across all 14 columns) matched the image by eye. The bottom rows were checked by eye against a second crop. Eye reading alone is unreliable at this resolution, so trust the pixel classes over eye impressions.
5. **Column order** in Fig. 5: 1 Cold Storage, 2 Dry Storage, 3 Ice Infrastructure, 4 Hoist, 5 Commercial Filet Station, 6 Recreational Filet Station, 7 Live Tanks, 8 Fish Grinders, 9 Public Fish Market, 10 Aquaculture Activities, 11 Commercial Fishing Fleet, 12 Product Manufacturing, 13 Boat Yard & Repair, 14 Marine Fuel Station. Only columns 1, 3, 4 and 14 are used.

The same method was used for the 2021 chart: crop region x 210–762, y 165–215 (552×50 px), with rows found by scanning a column.
- **Column bounds** (in the screenshot) came from the header cells.
- **Rows sampled** at crop y = 23 (crane), 31 (ice) and 40 (fuel).
- **Classes:** N (navy, r < 60) means "in place with funding"; M (mid-blue) means "partially established, requires funding"; G (grey, r > 190) means "no plan". Every sampled cell came out N or G; there was no M.

## Colour → status legend used
| Fig. 5 colour | Fig. 5 legend text | status | confidence |
|---|---|---|---|
| Dark green (G) | Installed, currently available at port, or funded project | `available` | medium |
| Teal (T) | Port is interested or planning project but needs funds | `not_available` | low |
| Pale (P) | Unplanned or unclear if service is available at port | (no P in the 4 used columns) | — |
| Red (R) | Not relevant or unavailable at port | `not_available` | low |

Caveats written into each row's notes:
- G also covers funded projects that are not yet built.
- R is a port-district judgment; private providers may still exist.
- Snapshot rows are capped at medium confidence (decisions log).
- `as_of_date` = `2023-12` by convention, because the interview year is 2023 and the month is unknown.

## Cell reads, 2024 Fig. 5 (cold / ice / hoist / fuel)
| Port district | Cold | Ice | Hoist | Fuel |
|---|---|---|---|---|
| Port of Alsea | R | R | R | R |
| Port of Astoria | G | G | G | G |
| Port of Bandon | R | R | G | G |
| Port of Brookings Harbor | G | G | G | G |
| Port of Coos Bay | G | G | G | G |
| Port of Garibaldi | T | G | G | G |
| Port of Gold Beach | R | R | G | G |
| Port of Nehalem | R | R | R | R |
| Port of Newport | R | G | G | G |
| Port of Port Orford | T | G | T | G |
| Port of Siuslaw | R | R | G | G |
| Port of Tillamook Bay | T | R | R | R |
| Port of Toledo | R | R | G | G |
| Port of Umpqua | R | G | R | G |

## Check against 2021 Summary Chart 2 (crane / ice / fuel; Y = in place, – = no plan)
| Port district | 2021 crane | 2021 ice | 2021 fuel | Agrees with 2024? |
|---|---|---|---|---|
| Alsea | – | – | – | yes |
| Astoria | Y | Y | Y | yes |
| Bandon | – | – | Y | **hoist differs** (2021 –, 2024 G) |
| Brookings Harbor | – | Y | Y | **hoist differs** (2021 –, 2024 G) |
| Coos Bay | Y | Y | Y | yes |
| Garibaldi | – | Y | Y | **hoist differs** (2021 –, 2024 G) |
| Gold Beach | – | – | Y | **hoist differs** (2021 –, 2024 G) |
| Nehalem | – | – | – | yes |
| Newport | Y | Y | Y | yes |
| Port Orford | Y | Y | Y | **hoist differs** (2021 Y, 2024 T: crane replacement project) |
| Siuslaw | – | – | Y | **hoist differs** (2021 –, 2024 G) |
| Tillamook Bay | – | – | – | yes |
| Toledo | Y | – | – | **fuel differs** (2021 –, 2024 G) |
| Umpqua | – | Y | Y | yes (2021 addendum notes a 2,200-lb dock crane, but the chart cell is –) |

Ice and fuel agree everywhere except Toledo fuel. The hoist disagreements may mean the 2021 "Crane Dock Service" row was narrower than the 2024 "Hoist" column, or that hoists were added. Each difference is noted in the matching snapshot row.

## Which harbor rows each district read was applied to
| Port district | Applied to `port_id` |
|---|---|
| Port of Astoria | OR-astoria (not OR-warrenton; Warrenton's basin belongs to the city, not the Port) |
| Port of Garibaldi | OR-garibaldi |
| Port of Newport | OR-newport |
| Port of Siuslaw | OR-florence |
| Port of Umpqua | OR-winchester-bay (Salmon Harbor is run by Douglas County, not the Port of Umpqua, so low weight) |
| Port of Coos Bay | OR-charleston |
| Port of Bandon | OR-bandon |
| Port of Port Orford | OR-port-orford |
| Port of Gold Beach | OR-gold-beach |
| Port of Brookings Harbor | OR-brookings |
| Port of Alsea, Port of Nehalem | not applied (Waldport and Nehalem were dropped from the port list) |
| Port of Tillamook Bay | not applied (no harbor in the list; Garibaldi is its own district) |
| Port of Toledo | not applied (boatyard; Toledo was dropped, and its landings fall under NEW) |
| (none) | OR-depoe-bay has no snapshot rows (city harbor, no port district) |
