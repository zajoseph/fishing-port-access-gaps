"""Build the static data files for the T5.1 interactive map (outputs/map/data/).

Reads the frozen inputs only (results-frozen tag, v0.9-results-frozen) and
writes no new analysis. Cut-off harbor lists for runs s1 and s4 are not stored
in index_sensitivity.csv, so they are recovered by re-running the frozen index
code (portgaps.index.simulate.run) and every recovered row is asserted equal to
the committed table (stranded_low, stranded_high, n_harbors_cut_off,
rank_service); the main-run lists are also asserted equal to index_ranking.csv.
Backup = the nearest other working facility (same run rules) for the facility's
own harbor and each harbor it cuts off, from distance_matrix.csv in
charted-equivalent nm (sea_nm x 1.06), the same matrix the index uses.

    python -I src/portgaps/map/build_map_data.py        (from the repo root; ~15 s, no network)

Outputs (all small; see outputs/map/README.md):
    harbors.geojson  58 points; current status per service (latest as_of_date
                     row, tie rule docs/data_dictionary.md section 5)
    index.json       index results at 25/30/40/50 nm for runs main, s1, s4;
                     display range = main-s1 envelope; hold flags
    events.json      5 validation events (6 cells) with verdicts by threshold
    routes.geojson   only the harbor-pair routes used as backup routes
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo/src
from portgaps.index import config as C  # noqa: E402
from portgaps.index.simulate import load_distance, load_status, run  # noqa: E402
from portgaps.index.values import build_values  # noqa: E402

OUT = C.ROOT / "outputs" / "map" / "data"
THRESHOLDS = [25, 30, 40, 50]          # report language rule: selectable thresholds
DEFAULT_THRESHOLD = 40                 # headline threshold (decisions log 2026-11-16)
RUNS = {                               # display key -> (index run name, working statuses, s4 rule)
    "main": ("main", ("available",), False),
    "s1": ("s1_not_found_as_available", ("available", "not_found"), False),
    "s4": ("s4_no_moorage_hoist_no_substitute", ("available",), True),
}
EVENTS = [  # marker id, label, event cells in t33_event_check.csv
    ("crescent-city", "Crescent City ice", ["E1 Crescent City ice"]),
    ("charleston", "Charleston ice", ["E2 Charleston ice"]),
    ("ilwaco", "Ilwaco Landing hoist/cranes and ice", ["E3a Ilwaco Landing hoist/cranes", "E3b Ilwaco Landing ice"]),
    ("point-arena", "Point Arena hoist", ["E4 Point Arena hoist"]),
    ("humboldt", "Humboldt Bay fuel dock", ["E5 Humboldt Bay fuel dock"]),
]
INPUTS = [
    "data/processed/ports.csv", "data/processed/facilities.csv", "data/processed/distance_matrix.csv",
    "data/interim/sea_routes.geojson", "outputs/tables/index_ranking.csv",
    "outputs/tables/index_sensitivity.csv", "outputs/tables/t34_before_after.csv",
    "outputs/tables/t33_event_check.csv", "outputs/tables/index_harbor_values.csv",
    "outputs/tables/t13_latest_status.csv",
]


def _clean(v):
    return None if pd.isna(v) else v


def _git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=C.ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return ""


def write_json(name: str, obj) -> None:
    (OUT / name).write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    T = C.TABLES
    ports = pd.read_csv(C.PROC / "ports.csv")
    fac_all = pd.read_csv(C.PROC / "facilities.csv", dtype={"as_of_date": str})
    assert len(ports) == 58 and ports.port_id.is_unique
    assert len(fac_all) == 272, len(fac_all)

    # ---- current facility status (frozen rule) ---------------------------
    cur = load_status()
    t13 = pd.read_csv(T / "t13_latest_status.csv", dtype={"as_of_date": str})
    chk = cur.merge(t13, on=["port_id", "service"], suffixes=("", "_t13"))
    assert len(chk) == 232 and (chk.status == chk.status_t13).all() and (chk.as_of_date == chk.as_of_date_t13).all()

    harbor_names = dict(zip(ports.port_id, ports.port_name))
    feats = []
    st = cur.set_index(["port_id", "service"])
    for p in ports.itertuples():
        services = {}
        for s in C.SERVICES:
            r = st.loc[(p.port_id, s)]
            services[s] = {k: _clean(r[k]) for k in
                           ["status", "confidence", "as_of_date", "source_url", "source_type", "operator"]}
        feats.append({"type": "Feature",
                      "geometry": {"type": "Point", "coordinates": [round(p.lon, 5), round(p.lat, 5)]},
                      "properties": {"id": p.port_id, "name": p.port_name, "state": p.state,
                                     "county": p.county, "services": services}})
    (OUT / "harbors.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8")

    # ---- index: recover cut lists, assert equal to frozen tables ---------
    hv, units = build_values()
    D = load_distance(list(hv.port_id))
    sens = pd.read_csv(T / "index_sensitivity.csv")
    rank = pd.read_csv(T / "index_ranking.csv")
    rank_main = rank.set_index(["threshold_nm", "facility_id"])
    own_only = set(C.NO_MOORAGE_LAUNCH_HOIST)
    status_of = {(r.port_id, r.service): r.status for r in cur.itertuples()}
    n_checked = 0
    rec: dict[str, dict] = {}
    route_pairs: set[tuple[str, str]] = set()

    for key, (run_name, working, s4) in RUNS.items():
        for thr in THRESHOLDS:
            res = run(cur, D, hv, units, threshold=thr, working=working, run_name=run_name,
                      own_hoist_only=own_only if s4 else set())
            ref = sens[(sens.run == run_name) & (sens.threshold_nm == thr)].set_index("facility_id")
            assert len(res) == len(ref), (run_name, thr)
            for r in res.itertuples():
                f = ref.loc[r.facility_id]
                assert (r.stranded_low, r.stranded_high, r.n_harbors_cut_off, r.rank_service) == \
                       (f.stranded_low, f.stranded_high, f.n_harbors_cut_off, f.rank_service), (run_name, thr, r.facility_id)
                if key == "main":
                    m = rank_main.loc[(thr, r.facility_id)]
                    assert r.harbors_cut_off == ("" if pd.isna(m.harbors_cut_off) else m.harbors_cut_off)
                    assert r.rank_service == m.rank_service
                n_checked += 1
                if status_of[(r.harbor, r.service)] != "available":
                    continue  # not_found cells working only in s1 are not facilities on the map
                cut = [h for h in r.harbors_cut_off.split(";") if h]
                fac_working = [p for p in D.index if status_of[(p, r.service)] in working and p != r.harbor]
                backups = []
                for h in [r.harbor] + [h for h in cut if h != r.harbor]:
                    if s4 and r.service == "hoist_crane" and h in own_only:
                        backups.append([h, None, None])          # no backup hoist at any distance (s4 rule)
                        continue
                    b = min(fac_working, key=lambda p: D.loc[h, p])
                    nm = round(float(D.loc[h, b]), 1)
                    backups.append([h, b, nm])
                    route_pairs.add(tuple(sorted((h, b))))
                e = rec.setdefault(r.facility_id, {"harbor": r.harbor, "service": r.service, "t": {}})
                e["t"].setdefault(str(thr), {})[key] = {
                    "low": int(r.stranded_low), "high": int(r.stranded_high),
                    "rank": int(r.rank_service), "cut": cut, "backups": backups}

    # display range (report language rule): main-s1 envelope; hold flag from T3.4
    ba = pd.read_csv(T / "t34_before_after.csv")
    hold = set(ba[(ba.run == "main") & (ba.holds_both_runs_after == "Y")]
               .apply(lambda r: f"{int(r.threshold_nm)}|{r.facility_id}", axis=1))
    top10 = set(ba[(ba.run == "main") & (ba.in_top10_after == "Y")]
                .apply(lambda r: f"{int(r.threshold_nm)}|{r.facility_id}", axis=1))
    for fid, e in rec.items():
        for thr, d in e["t"].items():
            d["range"] = [min(d["main"]["low"], d["s1"]["low"]), max(d["main"]["high"], d["s1"]["high"])]
            d["hold"] = f"{thr}|{fid}" in hold
            # top 10 as in before_after_t34.top10: rank_service <= 10 and stranded_high > 0
            d["top10"] = d["main"]["rank"] <= 10 and d["main"]["high"] > 0
            assert d["top10"] == (f"{thr}|{fid}" in top10), (fid, thr)
    # spot-check logged hold list at 40 nm (decisions log, report language rule)
    logged = {"OR-charleston|cold_storage": (31.0, 36.0), "OR-brookings|cold_storage": (25.3, 25.3),
              "CA-humboldt-bay|fuel": (11.8, 11.8), "CA-humboldt-bay|ice": (11.8, 11.8),
              "CA-shelter-cove|fuel": (0.46, 0.46), "OR-florence|hoist_crane": (0.0, 6.3),
              "OR-garibaldi|fuel": (0.0, 8.2), "OR-garibaldi|hoist_crane": (0.0, 8.2)}
    logged.update({f"CA-bodega-bay|{s}": (9.1, 9.1) for s in C.SERVICES})
    assert {f for f, e in rec.items() if e["t"]["40"]["hold"]} == set(logged)
    for fid, (lo, hi) in logged.items():
        rg = rec[fid]["t"]["40"]["range"]
        nd = 2 if hi < 1 else 1
        assert (round(rg[0] / 1e6, nd), round(rg[1] / 1e6, nd)) == (lo, hi), (fid, rg)

    # ---- events ----------------------------------------------------------
    ev = pd.read_csv(T / "t33_event_check.csv")
    run_key = {v[0]: k for k, v in RUNS.items()}
    events = []
    for eid, label, cells in EVENTS:
        cell_out = []
        for c in cells:
            sub = ev[(ev.event == c) & ev.threshold_nm.isin(THRESHOLDS)]
            first = sub.iloc[0]
            cell_out.append({
                "event": c, "harbor": first.harbor, "service": first.service, "dates": first.event_dates,
                "documented_backup": _clean(first.documented_backup), "documented_backup_nm": _clean(first.documented_backup_nm),
                "restored_for_review": str(first.cell_in_index_run).startswith("N"),
                "verdicts": {str(int(t)): {run_key[r.run]: {"verdict": r.verdict, "reason": r.verdict_reason}
                                            for r in g.itertuples()} for t, g in sub.groupby("threshold_nm")}})
        events.append({"id": eid, "label": label, "harbor": cell_out[0]["harbor"], "cells": cell_out})
    write_json("events.json", {"events": events})

    # ---- routes: only backup pairs --------------------------------------
    g = json.load(open(C.INTERIM / "sea_routes.geojson"))
    rfeats = []
    for f in g["features"]:
        pa, pb = f["properties"]["port_a"], f["properties"]["port_b"]
        if tuple(sorted((pa, pb))) not in route_pairs:
            continue
        coords = []
        for x, y in f["geometry"]["coordinates"]:
            pt = [round(x, 4), round(y, 4)]
            if not coords or coords[-1] != pt:
                coords.append(pt)
        rfeats.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords},
                       "properties": {"a": pa, "b": pb}})
    found = {tuple(sorted((f["properties"]["a"], f["properties"]["b"]))) for f in rfeats}
    assert found == route_pairs, route_pairs - found
    (OUT / "routes.geojson").write_text(json.dumps({
        "type": "FeatureCollection",
        "license": "Route geometry derived from OpenStreetMap data, (c) OpenStreetMap contributors, ODbL 1.0 "
                   "(https://opendatacommons.org/licenses/odbl/1-0/). Subset of data/interim/sea_routes.geojson (T3.1).",
        "features": rfeats}, separators=(",", ":")) + "\n", encoding="utf-8")

    # ---- index.json with metadata ---------------------------------------
    sha = {p: hashlib.sha256((C.ROOT / p).read_bytes()).hexdigest()[:12] for p in INPUTS}
    meta = {
        "built_from_commit": _git("log", "-1", "--format=%h", "--", *INPUTS),
        "results_tag": "v0.9-results-frozen",
        "input_sha256_12": sha,
        "thresholds": THRESHOLDS, "default_threshold": DEFAULT_THRESHOLD,
        "chart_factor": C.CHART_FACTOR,
        "value_years": list(C.VALUE_YEARS),
        "facility_as_of_range": [cur.as_of_date.min(), cur.as_of_date.max()],
        "n_harbors": len(ports), "n_facility_rows": len(fac_all),
        "n_unverified_cells_t32b": 40,
        "s4_harbors": sorted(own_only),
        "checked_rows": n_checked,
    }
    write_json("index.json", {"meta": meta, "harbor_names": harbor_names, "facilities": rec})
    print(f"OK: {len(feats)} harbors, {len(rec)} facilities, {n_checked} index rows checked, "
          f"{len(rfeats)} routes, events {len(events)}")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name}: {f.stat().st_size/1024:.1f} KB")


if __name__ == "__main__":
    main()
