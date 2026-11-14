"""Fixed settings for the T3.2 failure index. Every value here traces to the
decisions log (2026-11-14 entries) or to the user's answers in the T3.2 chat."""
from pathlib import Path
import os

ROOT = Path(os.environ.get("PORTGAPS_ROOT", Path(__file__).resolve().parents[3]))
PROC = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"
INTERIM = ROOT / "data" / "interim"

SERVICES = ["fuel", "ice", "hoist_crane", "cold_storage"]

# Charted-equivalent nm = model sea_nm x 1.06 (T3.1: model ~6% under NOAA).
CHART_FACTOR = 1.06
# Sweep approved by user 2026-11-14 (T3.2 chat).
THRESHOLDS_NM = [10, 15, 20, 25, 30, 40, 50, 60, 75, 100, 125, 150]
MID_THRESHOLD_NM = 40  # threshold used for handoff key figures (user choice)

VALUE_YEARS = (2019, 2024)  # mean annual all-species ex-vessel value, nominal

# Sensitivity run 2: CA harbors with only a recreational-marina fuel dock.
MARINA_ONLY = ["CA-vallejo", "CA-berkeley", "CA-huntington-harbour", "CA-redondo-beach"]
# Sensitivity run 3: heavily withheld = >=30% of 2019-2024 months "confidential".
HEAVY_WITHHELD_SHARE = 0.30

# A rank move of more than this many places (per-service rank) is flagged.
RANK_FLAG_PLACES = 3

# WA / OR FOSS annual ports -> inventory harbors (sub-blocks inside a shared unit).
# A joint FOSS port (several harbors) is never split: it counts toward the lower
# bound only when all of its harbors are cut off together.
FOSS_BLOCKS = {
    "FOSS Astoria, OR": ["OR-astoria"],
    "FOSS Winchester Bay, OR": ["OR-winchester-bay"],
    "FOSS Port Orford, OR": ["OR-port-orford"],
    "FOSS Brookings, OR": ["OR-brookings"],
    "FOSS Ilwaco-Chinook, WA": ["WA-ilwaco", "WA-chinook"],
    "FOSS Westport, WA": ["WA-westport"],
    "FOSS Willapa Bay, WA": ["WA-tokeland", "WA-bay-center", "WA-nahcotta"],
    "FOSS La Push, WA": ["WA-la-push"],
    "FOSS Neah Bay, WA": ["WA-neah-bay"],
    "FOSS Port Angeles, WA": ["WA-port-angeles"],
    "FOSS Port Townsend, WA": ["WA-port-townsend"],
    "FOSS Anacortes-La Conner, WA": ["WA-anacortes", "WA-la-conner"],
    "FOSS Bellingham, WA": ["WA-bellingham"],
    "FOSS Blaine, WA": ["WA-blaine"],
    "FOSS Seattle, WA": ["WA-seattle"],
    "FOSS Everett, WA": ["WA-everett"],
}
# WA all-species unit value = PacFIN ALL005 group (annual); panel unit -> group name.
WA_GROUPS = {
    "WA-PACFIN-CLW": "PacFIN group CLW",
    "WA-PACFIN-CWA": "PacFIN group CWA",
    "WA-PACFIN-NPS": "PacFIN group NPS",
    "WA-PACFIN-SPS": "PacFIN group SPS",
}
# Multi-harbor units whose agency group also holds landings from non-inventory
# ports (from outputs/tables/t21_units.csv). For these, the whole-unit value is
# never a lower bound even when every inventory harbor in it is cut off.
UNITS_WITH_NONINVENTORY_PORTS = {
    "OR-ODFW-waldport-winchester-bay",  # also Waldport, Yachats
    "WA-PACFIN-CLW", "WA-PACFIN-CWA", "WA-PACFIN-NPS", "WA-PACFIN-SPS",
}

# Known intertidal crossing (T3.1): drying bar between Portage Island and the
# Lummi Peninsula. A route is flagged if a segment crosses this meridian
# within this latitude band.
INTERTIDAL_TESTS = {
    "Portage Island bar (Bellingham Bay)": {"lon": -122.61, "lat_min": 48.70, "lat_max": 48.755},
}
# Bays with extensive drying flats where routes are unverified for depth.
SHALLOW_BAY_HARBORS = {"WA-tokeland", "WA-bay-center", "WA-nahcotta"}
