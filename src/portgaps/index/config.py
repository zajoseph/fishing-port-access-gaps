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
# Units (ODFW table or PacFIN group) whose agency reporting group also holds
# landings from non-inventory ports. Literal shared-unit rule (decisions log
# 2026-11-14; applied literally from T3.4 / F2, 2026-11-16): such a unit
# contributes $0 to the lower bound unless the harbor has its own published
# value (FOSS sub-block); the whole-unit value is never a lower bound, whether
# the unit holds one inventory harbor or several. Derived systematically by
# values.derive_noninventory_units() from outputs/tables/t21_units.csv (unit
# agency codes) vs docs/port_crosswalk.md (inventory harbors' codes); the build
# asserts that this set equals the derived one. Non-inventory codes in brackets.
UNITS_WITH_NONINVENTORY_PORTS = {
    # used in the 2019-2024 value window
    "OR-ODFW-gearhart-garibaldi",         # [GSS Gearhart/Seaside, CNB Cannon Beach, NHL Nehalem Bay] (T3.4 addition)
    "OR-ODFW-netarts-depoe-bay",          # [NTR Netarts, PCC Pacific City, SLZ Siletz Bay, SRV Salmon River] (T3.4 addition)
    "OR-ODFW-waldport-winchester-bay",    # [WLD Waldport, YAC Yachats]
    "WA-PACFIN-CLW",                      # [OCR other Columbia River ports]
    "WA-PACFIN-CWA",                      # [CPL Copalis, GRH Grays Harbor, OWC other WA coast]
    "WA-PACFIN-NPS",                      # [FRI Friday Harbor, ONP other N Puget Sound, SEQ Sequim]
    "WA-PACFIN-SPS",                      # [OLY Olympia, OSP other S Puget Sound, SHL Shelton, TAC Tacoma]
    # 2025 ODFW regrouped tables (outside the 2019-2024 value window; listed for completeness)
    "OR-ODFW-gearhart-siletz-bay-2025",   # [GSS, CNB, NHL, NTR, PCC, SLZ, SRV]
    "OR-ODFW-depoe-bay-yachats-2025",     # [WLD, YAC]
}

# Sensitivity run s4 (T3.4 / R3): harbors whose only offload is a launch hoist
# with no in-water moorage. In s4 their hoist access comes only from their own
# hoist (no backup hoist at any distance). Main run unchanged. Sources are
# data/processed/facilities.csv rows (file line) and the logged dual-use hoist
# decision (decisions log 2026-11-12, user answer in T1.3).
NO_MOORAGE_LAUNCH_HOIST = {
    "CA-point-arena": "facilities.csv lines 30-31 (hoist_crane 2025-10-18 closed, 2026-01-29 available): "
                      "'Hoist-only launch: no harbor moorage'; 'Dual-use launch/offload hoist at a harbor with no "
                      "in-water moorage'; ports.csv context_notes: 'Hoist-launch pier, no moorage basin; hoist outage "
                      "Oct 2025-Jan 2026 stopped the fleet'; decisions log 2026-11-12 dual-use hoist ruling",
    "OR-port-orford": "facilities.csv line 190 (hoist_crane 2026-08-07 available): 'Electric cranes lower boats to "
                      "the ocean and lift them back onto the dolly dock'; 'Dual-use launch/offload hoist at a harbor "
                      "with no in-water moorage'; ports.csv context_notes: 'No in-water moorage: boats craned to "
                      "dollies, so a crane outage stops the fleet'; decisions log 2026-11-12 dual-use hoist ruling",
}

# Known intertidal crossing (T3.1): drying bar between Portage Island and the
# Lummi Peninsula. A route is flagged if a segment crosses this meridian
# within this latitude band.
INTERTIDAL_TESTS = {
    "Portage Island bar (Bellingham Bay)": {"lon": -122.61, "lat_min": 48.70, "lat_max": 48.755},
}
# Bays with extensive drying flats where routes are unverified for depth.
SHALLOW_BAY_HARBORS = {"WA-tokeland", "WA-bay-center", "WA-nahcotta"}
