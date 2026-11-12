"""T1.3 — merge CA + OR/WA inventories, apply logged coding rulings, write merged files.

Inputs : data/processed/{ports,facilities}_{ca,orwa}.csv (T1.1, T1.2; left unchanged)
Outputs: data/processed/ports.csv, data/processed/facilities.csv, outputs/tables/t13_changelog.csv
Rulings applied (decisions-log 2026-11-12 + T1.3 user answers 2026-11-12):
  hoist_crane = offload equipment; Travelifts / launch hoists -> notes only;
  dual-use launch+offload hoists at no-moorage harbors count as hoist_crane;
  retail bagged ice -> notes only; tribal operators -> public + "tribal" in notes;
  drop WA-aberdeen-hoquiam; CA ds3081 points that are town points replaced by harbor points.
Run from repo root:  python -I src/portgaps/clean/build_inventory_t13.py
"""
import pandas as pd
from pathlib import Path

P = Path("data/processed")
PORT_COLS = ["port_id", "port_name", "state", "county", "lat", "lon", "coord_source", "in_round1", "context_notes"]
FAC_COLS = ["port_id", "service", "status", "operator", "operator_type", "as_of_date", "source_url",
            "source_type", "confidence", "notes"]
T13 = "T1.3 (2026-11-12): "

ports = pd.concat([pd.read_csv(P / "ports_ca.csv", dtype=str), pd.read_csv(P / "ports_orwa.csv", dtype=str)],
                  ignore_index=True).fillna("")
fca = pd.read_csv(P / "facilities_ca.csv", dtype=str).fillna("")
fca["src"] = ["facilities_ca.csv:" + str(i + 2) for i in range(len(fca))]
fow = pd.read_csv(P / "facilities_orwa.csv", dtype=str).fillna("")
fow["src"] = ["facilities_orwa.csv:" + str(i + 2) for i in range(len(fow))]
fac = pd.concat([fca, fow], ignore_index=True)

log = []


def pick(port, service, as_of, status=None):
    m = (fac.port_id == port) & (fac.service == service) & (fac.as_of_date == as_of)
    if status:
        m &= fac.status == status
    idx = fac.index[m]
    assert len(idx) == 1, (port, service, as_of, status, len(idx))
    return idx[0]


def note(i, text):
    fac.at[i, "notes"] = (fac.at[i, "notes"].rstrip() + " " + T13 + text).strip()


def recode_not_found(i, rule, text):
    before = f"{fac.at[i,'status']}/{fac.at[i,'confidence']}/{fac.at[i,'as_of_date']}"
    old_op = fac.at[i, "operator"]
    fac.at[i, "status"] = "not_found"
    fac.at[i, "as_of_date"] = "2026-11"
    fac.at[i, "confidence"] = "low"
    fac.at[i, "operator"] = ""
    fac.at[i, "operator_type"] = "unknown"
    note(i, f"recoded {before} -> not_found ({rule}). {text}" + (f" Former operator field: {old_op}." if old_op else ""))
    log.append(dict(source_row=fac.at[i, "src"], port_id=fac.at[i, "port_id"], service=fac.at[i, "service"],
                    change=f"{before} -> not_found/low/2026-11", rule=rule, detail=text))


def drop_fold(i, keep, rule, text):
    note(keep, f"Folded in from removed row ({rule}): {text}")
    log.append(dict(source_row=fac.at[i, "src"], port_id=fac.at[i, "port_id"], service=fac.at[i, "service"],
                    change=f"row removed; content moved to notes of {fac.at[keep,'src']}", rule=rule, detail=text))
    fac.drop(index=i, inplace=True)


HOIST = "hoist_crane ruling: Travelift/launch hoist = notes only"
ICE = "ice ruling: retail bagged ice = notes only"

# ---- hoist_crane: Travelifts and launch hoists (T1.2 rows + same rule applied to CA) ----
drop_fold(pick("OR-astoria", "hoist_crane", "2024-06"), pick("OR-astoria", "hoist_crane", "2023-12"), HOIST,
          "Port of Astoria 2024/25 rate schedule lists an 88-ton Travelift for haul-out (not offload equipment).")
for port, txt in [
    ("WA-ilwaco", "WPPA 2026 'Hoist YES' is the launch-hoist column; port page lists two small boat hoists; boatyard Travelifts haul to 70 t. No current offload hoist/crane source located; port is seeking funds for a public fishermen's dock with crane(s) after the 2024-01-22 Ilwaco Landing fire."),
    ("WA-nahcotta", "WPPA 2026 'Hoist YES' is the launch-hoist column; no offload hoist/crane source located."),
    ("WA-port-townsend", "WPPA 2026 lists a Travelift (330-ton per Fishermen's News) — haul-out only; no offload hoist/crane source located."),
    ("WA-everett", "WPPA 2026 lists a Travelift — haul-out only; no offload hoist/crane source located."),
    ("WA-la-conner", "WPPA 2026 'Hoist NEARBY' is the launch-hoist column; no offload hoist/crane source located."),
    ("WA-anacortes", "WPPA 2026 'Hoist YES' is the launch-hoist column; no offload hoist/crane source located."),
]:
    recode_not_found(pick(port, "hoist_crane", "2026-04"), HOIST, txt)
for port in ["WA-tokeland", "WA-bay-center"]:
    recode_not_found(pick(port, "hoist_crane", "2026-04"), HOIST,
                     "WPPA 2026 'Hoist NO' refers to the launch-hoist column and says nothing about offload equipment; no offload hoist/crane source located.")
recode_not_found(pick("CA-redondo-beach", "hoist_crane", "2026-11"), HOIST + " (applied to CA for consistency)",
                 "The Log lists a 5-ton mechanical boat (launch) hoist; use for catch offloading not confirmed. No offload hoist located.")
recode_not_found(pick("CA-dana-point", "hoist_crane", "2018-11"), HOIST + " (applied to CA for consistency)",
                 "Former row recorded removal (~2018-11) of the Embarcadero Marina boat hoist, a launch hoist, so it is notes-only. No offload hoist found for the commercial fishing docks (2025 OC advisory: boat hoist 'not feasible' for new dock).")
i = pick("CA-port-san-luis", "hoist_crane", "2021-03-25")
fac.at[i, "operator"] = "Port San Luis Harbor District (Harford Pier hoists #1–#4)"
note(i, "Boatyard 50-ton mobile hoist moved from operator field to notes (haul-out, not counted).")
log.append(dict(source_row=fac.at[i, "src"], port_id="CA-port-san-luis", service="hoist_crane",
                change="operator text edited (status unchanged)", rule=HOIST, detail="50-ton boatyard mobile hoist removed from operator field"))
# dual-use launch/offload hoists at no-moorage harbors (user answer 2026-11-12): keep, label
for port, a in [("CA-point-arena", "2025-10-18"), ("CA-point-arena", "2026-01-29"), ("OR-port-orford", "2026-08-07")]:
    i = pick(port, "hoist_crane", a)
    note(i, "Dual-use launch/offload hoist at a harbor with no in-water moorage; counted as hoist_crane per user ruling (catch cannot be landed without it).")
    log.append(dict(source_row=fac.at[i, "src"], port_id=port, service="hoist_crane", change="note added (status unchanged)",
                    rule="dual-use hoist ruling (T1.3 user answer)", detail="labelled dual-use launch/offload"))
i = pick("OR-warrenton", "hoist_crane", "2026-11")
note(i, "Service-dock hydro-hoist; use for catch offload not confirmed (kept, low).")

# ---- ice: retail bagged ice ----
drop_fold(pick("OR-astoria", "ice", "2026-11"), pick("OR-astoria", "ice", "2023-12"), ICE,
          "Estuary Partnership launch-point page (undated) lists 'ice available' at West Basin; likely retail, not fleet ice.")
recode_not_found(pick("WA-nahcotta", "ice", "2026-11"), ICE,
                 "Only a marina amenity listing (PredictWind, undated) mentions ice, likely retail; no bulk/fleet ice source located.")
recode_not_found(pick("WA-everett", "ice", "2026-11"), ICE,
                 "Only a Dockwa amenity list (undated) mentions ice, likely retail; no bulk/fleet ice source located.")

# ---- tribal operators ----
for port, svc, a in [("WA-neah-bay", "cold_storage", "2026-11"), ("WA-neah-bay", "fuel", "2026-11"),
                     ("WA-neah-bay", "hoist_crane", "2014-10-10"), ("WA-neah-bay", "ice", "2014-10-10")]:
    i = pick(port, svc, a)
    note(i, "Operator is tribal (Makah Tribe); operator_type = public per tribal-operator ruling.")
    log.append(dict(source_row=fac.at[i, "src"], port_id=port, service=svc, change="'tribal' added to notes",
                    rule="tribal-operator ruling", detail="Makah Tribe"))
i = pick("CA-trinidad", "hoist_crane", "2010-08")
fac.at[i, "notes"] = fac.at[i, "notes"].replace("coded public pending T1.3 rule", "coded public per tribal-operator ruling (2026-11-12)")
log.append(dict(source_row=fac.at[i, "src"], port_id="CA-trinidad", service="hoist_crane", change="note wording updated",
                rule="tribal-operator ruling", detail="'pending T1.3 rule' -> ruling cited"))

# ---- listed source conflicts ----
i = pick("OR-florence", "ice", "2023-12")
note(i, "Conflict checked, NOT resolved. For ice: KCFM (Aug & Dec 2011) reports a port commercial ice machine serving the fleet, rebuilt after breakdowns; DOWL project page (undated; page metadata 2019–2020) says the new commercial dock added ice generation facilities. Against: Snapshot 2023 red, and the port's service-rates page (modified 2025-07-17) lists dock hoists but no ice. Status kept not_available/low; needs a call to the Port of Siuslaw.")
log.append(dict(source_row=fac.at[i, "src"], port_id="OR-florence", service="ice", change="note added (status unchanged, flagged)",
                rule="listed conflict", detail="unresolved: 2011/undated sources say port ice; 2023 Snapshot and 2025 rates say none"))
i = pick("WA-tokeland", "fuel", "2026-04")
fac.at[i, "notes"] = fac.at[i, "notes"].replace("Fuel column blank/N/A.", "Fuel column NO (hours N/A); WPPA 2025 guide also NO.")
note(i, "Conflict checked, NOT resolved. Marinas.com (updated 2022-10-18) lists fuel dock + diesel; the port facility text (via PredictWind, undated) says 'Marine fuel (diesel only)'. The two newest dated sources (WPPA 2025, 2026) say no fuel. Possibly a diesel service that ended after 2022; unconfirmed. Kept not_available/low as latest; 2022 row added.")
add = dict(port_id="WA-tokeland", service="fuel", status="available", operator="Port of Willapa Harbor", operator_type="public",
           as_of_date="2022-10", source_url="https://marinas.com/contact_marina_reservation?id=13111", source_type="other",
           confidence="low",
           notes=T13 + "Added while checking the listed Tokeland fuel conflict. Marinas.com services (last updated Oct 18, 2022): Fuel Dock Yes, Diesel Yes. Port facility text (via PredictWind, undated) also says diesel only. Superseded as latest by WPPA 2026 (no fuel).",
           src="added by T1.3")
fac = pd.concat([fac, pd.DataFrame([add])], ignore_index=True)
log.append(dict(source_row="added by T1.3", port_id="WA-tokeland", service="fuel", change="row added: available/low/2022-10",
                rule="listed conflict", detail="marinas.com 2022 fuel dock + diesel"))

# ---- date / operator conventions ----
i = pick("CA-port-san-luis", "cold_storage", "2026-09-08")
fac.at[i, "as_of_date"] = "2026-11"
note(i, "as_of moved 2026-09-08 -> 2026-11 (not_found rows carry the search month); the CEQA NOE date stays in notes.")
log.append(dict(source_row=fac.at[i, "src"], port_id="CA-port-san-luis", service="cold_storage", change="as_of 2026-09-08 -> 2026-11",
                rule="date convention: not_found = search month", detail=""))
for port, svc in [("CA-bodega-bay", "fuel"), ("CA-los-angeles-long-beach", "cold_storage"), ("CA-san-diego-bay", "hoist_crane")]:
    i = pick(port, svc, "2026-11")
    note(i, "Page undated; as_of = month accessed.")
    log.append(dict(source_row=fac.at[i, "src"], port_id=port, service=svc, change="'undated' added to notes",
                    rule="date convention: undated page = month accessed", detail=""))
i = pick("WA-seattle", "fuel", "2026-04")
fac.at[i, "operator_type"] = "unknown"
note(i, "operator_type private -> unknown (operator not named).")
log.append(dict(source_row=fac.at[i, "src"], port_id="WA-seattle", service="fuel", change="operator_type private -> unknown",
                rule="operator_type = unknown when operator not identified", detail=""))

# ---- drop WA-aberdeen-hoquiam ----
n = (fac.port_id == "WA-aberdeen-hoquiam").sum()
fac = fac[fac.port_id != "WA-aberdeen-hoquiam"]
ports = ports[ports.port_id != "WA-aberdeen-hoquiam"]
log.append(dict(source_row="ports_orwa.csv + facilities_orwa.csv", port_id="WA-aberdeen-hoquiam", service="all",
                change=f"port and {n} facility rows removed", rule="user ruling: fails harbor-core test",
                detail="PacFIN GRH; boat launches only"))

# ---- CA coordinates: replace town points with harbor points (user answer 2026-11-12) ----
NEW = {  # port_id: (lat, lon, source)
    "CA-vallejo": (38.1086, -122.2692, "Vallejo Municipal Marina listing (mastermariners/marinelink, 38.1086,-122.2692)"),
    "CA-berkeley": (37.8665, -122.3150, "Berkeley Marina listing (mastermariners 37.8665,-122.3150; Wikipedia 37.8677,-122.3125)"),
    "CA-santa-cruz": (36.9658, -122.0025, "USGS GNIS 'Santa Cruz Small Craft Harbor' (36.96578,-122.00246)"),
    "CA-ventura": (34.2494, -119.2648, "USGS GNIS 'Ventura Harbor' (34.24945,-119.26483)"),
    "CA-channel-islands": (34.1642, -119.2243, "USGS GNIS 'Channel Islands Harbor' (34.16417,-119.22428)"),
    "CA-huntington-harbour": (33.7210, -118.0640, "USGS GNIS populated place 'Huntington Harbour' (33.721,-118.064)"),
    "CA-san-diego-bay": (32.7126, -117.1756, "USGS GNIS 'Tuna Harbor' (32.71255,-117.17559)"),
    "CA-los-angeles-long-beach": (33.7361, -118.2676, "USGS GNIS 'Fish Harbor' (33.73613,-118.26757)"),
    "CA-point-arena": (38.9145, -123.7110, "NOAA tide station 9416841 Arena Cove pier benchmarks (~38.9145,-123.7110)"),
}
import math
coord_moves = []
for pid, (la, lo, s) in NEW.items():
    j = ports.index[ports.port_id == pid][0]
    ola, olo = float(ports.at[j, "lat"]), float(ports.at[j, "lon"])
    dkm = 6371 * 2 * math.asin(math.sqrt(math.sin(math.radians(la - ola) / 2) ** 2 +
                                         math.cos(math.radians(ola)) * math.cos(math.radians(la)) * math.sin(math.radians(lo - olo) / 2) ** 2))
    old_src = ports.at[j, "coord_source"]
    ports.at[j, "lat"], ports.at[j, "lon"] = f"{la:.4f}", f"{lo:.4f}"
    ports.at[j, "coord_source"] = f"placed manually on harbor (T1.3, approximate) from {s}; replaces ds3081 town point {ola:.4f},{olo:.4f} ({dkm:.1f} km away)"
    ports.at[j, "context_notes"] = ports.at[j, "context_notes"].replace(" Coords = CDFW Terminal Island point.", "").replace(" Coords = CDFW San Diego point.", "")
    coord_moves.append(dict(port_id=pid, old=f"{ola:.4f},{olo:.4f}", new=f"{la:.4f},{lo:.4f}", moved_km=round(dkm, 1), source=s))
    log.append(dict(source_row="ports_ca.csv", port_id=pid, service="(coords)", change=f"lat/lon moved {dkm:.1f} km to harbor",
                    rule="user answer: replace flagged ds3081 town points", detail=s))

# ---- order & write ----
ports["_o"] = range(len(ports))
order = dict(zip(ports.port_id, ports._o))
svc_o = {"fuel": 0, "ice": 1, "hoist_crane": 2, "cold_storage": 3}
fac = fac.assign(_p=fac.port_id.map(order), _s=fac.service.map(svc_o)).sort_values(["_p", "_s", "as_of_date"], kind="stable")
ports[PORT_COLS].to_csv(P / "ports.csv", index=False)
fac[FAC_COLS].to_csv(P / "facilities.csv", index=False)
Path("outputs/tables").mkdir(parents=True, exist_ok=True)
pd.DataFrame(log).to_csv("outputs/tables/t13_changelog.csv", index=False)
pd.DataFrame(coord_moves).to_csv("outputs/tables/t13_coord_moves.csv", index=False)
print(len(ports), "ports;", len(fac), "facility rows;", len(log), "changelog entries")
