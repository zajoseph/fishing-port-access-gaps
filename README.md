# Fishing Port Access Gaps

> **Status:** in progress. Sections marked _TBD_ are filled in at later project phases.

## Project question

_TBD — one paragraph:_ where along the U.S. Pacific Coast could the loss of a single shoreside service (fuel, ice, hoist/crane, or cold storage) at a small harbor end a fishing fleet's practical access to that port?

**Headline finding:** _TBD (Phase 5)._

## Scope

- **Geography:** harbors from San Diego, CA to Bellingham, WA (California, Oregon, Washington).
- **Core services inventoried:** fuel, ice, hoist/crane, cold storage.
- **Context-only items:** _TBD — items recorded for context but not scored in the index._

## Repository map

```
fishing-port-access-gaps/
├── data/
│   ├── manifest.csv      # one row per downloaded file (source, URL, retrieval time, sha256, license)
│   ├── raw/              # untouched downloads, by source (not committed; manifest is)
│   ├── interim/          # parsed but not final
│   └── processed/        # ports, facilities, landings_monthly, withheld_log, distance_matrix
├── docs/                 # data dictionary, data access, port crosswalk, methods
├── src/portgaps/         # ingest, clean, distances, index (failure simulation), eventstudy
├── notebooks/            # 01_inventory_qa → 04_event_study
├── tests/
├── outputs/              # figures, tables, map
└── report/               # report + 2-page brief sources
```

## Data sources and access

See [`docs/data_access.md`](docs/data_access.md) for full access notes.

| Source | Category | Access | License | Notes |
|---|---|---|---|---|
| PacFIN | Landings | _TBD_ | _TBD_ | |
| ODFW | Landings | _TBD_ | _TBD_ | |
| CDFW | Landings | _TBD_ | _TBD_ | |
| WDFW | Landings | _TBD_ | _TBD_ | |
| NOAA FOSS | Landings | _TBD_ | _TBD_ | |
| Port websites / agenda packets / news | Facilities | _TBD_ | _TBD_ | |
| Oregon snapshot | Facilities | _TBD_ | _TBD_ | |
| CA Division of Boating & Waterways | Facilities | _TBD_ | _TBD_ | |
| NOAA CSVI | Community | _TBD_ | _TBD_ | |
| Census ACS | Community | _TBD_ | _TBD_ | |
| USACE eHydro | Channels | _TBD_ | _TBD_ | |
| NDBC | Weather (stretch) | _TBD_ | _TBD_ | |
| Shoreline geometry | Geometry | _TBD_ | _TBD_ | |

**Confidentiality and missing data:**
- In the facilities inventory, **"not found" means no source was located**. It does not mean the service is confirmed absent.
- Landings cells withheld for confidentiality are recorded in `data/processed/withheld_log.csv` with their source flag. They are **never imputed silently**.

## Reproduce

1. **Environment:** _TBD_ (`requirements.txt` or `environment.yml`).
   ```bash
   # TBD
   ```
2. **Download data:** use `data/manifest.csv` to fetch each source into `data/raw/` and check the sha256 checksums. _TBD: script/command._
3. **Run order:**
   1. `src/portgaps/ingest` → `src/portgaps/clean`
   2. `notebooks/01_inventory_qa`
   3. `notebooks/02_landings_panel`
   4. `src/portgaps/distances` → `notebooks/03_index`
   5. `notebooks/04_event_study`

## Outputs

- **Dataset:** _TBD (Zenodo DOI)_
- **Access-gap index:** _TBD_
- **Event study:** _TBD_
- **Map:** _TBD_
- **Report and 2-page brief:** _TBD_

## Citation

See [`CITATION.cff`](CITATION.cff). _TBD._

## Licenses

- **Code:** see [`LICENSE`](LICENSE). _TBD._
- **Data:** see [`LICENSE-data`](LICENSE-data). _TBD._

## Contact

_TBD._
