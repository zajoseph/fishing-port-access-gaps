"""Fixed settings for T4.1, the Crescent City ice-closure event study.

Every value traces to the T4.1 kickoff, the decisions log, or the user's
answers in the T4.1 chat (2026-11-16): synthetic control (SC) is the main
method with a window-total DiD alongside it; Trinidad and Humboldt Bay are
excluded from the main donor pool; the shift test uses the consistent South-OR
unit against Central-OR.
"""
from pathlib import Path
import os

ROOT = Path(os.environ.get("PORTGAPS_ROOT", Path(__file__).resolve().parents[3]))
PROC = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"
FIGS = ROOT / "outputs" / "figures"

TREATED = "CA-crescent-city"

# Panel window for CA/OR (decision log: Jan 2016 - Dec 2025; not_in_source filtered).
PANEL_START, PANEL_END = 201601, 202512

# Event dates come from the closure sequence in docs/data_dictionary.md section 5,
# not from status_* columns. Closed 2024-10-05; Ocean Gold lease ~2025-02;
# running by 2025-08-27 (exact restart day unknown). Event month counts as during.
PRE_END = 202409
DURING = (202410, 202508)
AFTER = (202509, 202512)
# Alternative event end (required robustness): lease month 2025-02 ends "during".
DURING_ALT = (202410, 202502)
AFTER_ALT = (202503, 202512)

# Window-total DiD and placebo-in-time use the same 11-month span (Oct y -> Aug y+1).
# Oct 2015 is outside the panel, so the first full window starts Oct 2016.
WINDOW_START_YEARS_PRE = list(range(2016, 2024))  # 8 windows: 2016-17 ... 2023-24
EVENT_WINDOW_YEAR = 2024
# SC placebo-in-time: fake events in Oct 2017 ... Oct 2023 (Oct 2016 leaves only
# 9 pre months, too few to fit weights).
SC_PLACEBO_YEARS = list(range(2017, 2024))

# ---------------------------------------------------------------------------
# Donor pool (user answer: exclude Trinidad and Humboldt Bay as possible receivers)
# ---------------------------------------------------------------------------
# Possible receivers / spillover buffer: Brookings is the only harbor within the
# logged 40 nm threshold (20.5 nm charted-equivalent; it is in Oregon and not a CA
# donor anyway); Trinidad (45.0) and Humboldt Bay (67.7) are the next CA harbors,
# in the same crab fishing zone (Zone 1).
EXCLUDE_RECEIVERS = ["CA-trinidad", "CA-humboldt-bay"]
# Own treatment inside the window: Point Arena hoist out 2025-10-18 -> 2026-01-29.
EXCLUDE_OWN_EVENT = ["CA-point-arena"]
# Heavily withheld: >= 30% of pre-period months null (same 30% rule as the index
# s3 run, applied to 2016-01..2024-09) -> Vallejo, Avalon, Huntington Harbour,
# Port Hueneme, Marina del Rey, Redondo Beach.
HEAVY_NULL_SHARE = 0.30
# Any null month inside 2024-10..2025-12 also excludes a donor (the counterfactual
# would be undefined in that month; no imputation).

# Crab donors: mean annual Dungeness value in the pre-period >= this.
CRAB_DONOR_MIN_ANNUAL_USD = 100_000
# Crab donors follow the same rule as all-species donors: no null crab month in
# 2024-10..2025-12 (a null in a weighted donor would drop that month from the
# window; tried with <=2 nulls allowed and it dropped Jan 2025, the opener month).

# Same-zone robustness control (CA crab Fishing Zones 1-2, Oregon border to the
# Sonoma/Mendocino line), accepting spillover risk. Point Arena is left out
# (own event in the after-window).
SAME_ZONE = ["CA-trinidad", "CA-humboldt-bay", "CA-noyo-harbor", "CA-shelter-cove"]

# ---------------------------------------------------------------------------
# Oregon units that stay consistent across the 2025 ODFW regrouping
# ---------------------------------------------------------------------------
# South-OR = Bandon, Port Orford, Gold Beach, Brookings (Brookings has no
# harbor-level ODFW series).
SOUTH_OR = {
    "pre2025": ["OR-ODFW-bandon-port-orford", "OR-ODFW-gold-beach-brookings"],
    "2025": ["OR-ODFW-bandon-brookings-2025"],
}
# Central-OR = every ODFW table from Gearhart down to Charleston (the 2016-24
# tables and the 2025 tables cover the same ports). Same agency, date basis,
# weight basis and crab opener as South-OR. Astoria (north of Cape Falcon,
# different opener) is not included.
CENTRAL_OR = {
    "pre2025": ["OR-ODFW-gearhart-garibaldi", "OR-ODFW-netarts-depoe-bay", "OR-newport",
                "OR-ODFW-waldport-winchester-bay", "OR-charleston"],
    "2025": ["OR-ODFW-gearhart-siletz-bay-2025", "OR-ODFW-depoe-bay-yachats-2025",
             "OR-ODFW-florence-charleston-2025"],
}

CRAB = "Dungeness crab"
