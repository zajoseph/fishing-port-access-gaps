"""Fixed settings for T4.2, the Charleston ice-plant fire event study.

Every value traces to the T4.2 kickoff, the decisions log, or the user's answers
in the T4.2 chat (2026-11-16):
- case = Charleston ice closure only; closed 2019-12-20 (fire), reopened
  2020-09-12 (closure sequence, docs/data_dictionary.md section 5);
- Charleston = ODFW harbor-level series, species_scheme all, 2016-01..2024-12
  (Charleston is group-level from 2025; the 2025 group is not split);
- main donor pool = Oregon ODFW units only; northern CA harbors are a robustness
  check (user answer);
- crab "blanks as missing" follows the T4.1 rule: fully blank months -> null,
  part-blank months kept as flagged lower bounds (user answer);
- placebo-in-time: pre-period fake events give the main p-values; fake events in
  the after-period (fitted without the closure months) give a second, labeled
  p-value that assumes no lasting effect (user answer).
The T4.1 settings in config.py are untouched.
"""
from .config import ROOT, PROC, TABLES, FIGS, CRAB  # noqa: F401  (shared paths)

TREATED = "OR-charleston"
# Documented backup (facilities.csv, 23.4 nm): Winchester Bay, which sits in the
# ODFW group table Waldport-Winchester Bay (also Florence and non-inventory ports).
RECEIVER = "OR-ODFW-waldport-winchester-bay"
COMBINED = "charleston+winchester-bay-unit"

# Harbor-level Charleston series stops at 2024-12 (group-level from 2025).
PANEL_START, PANEL_END = 201601, 202412

# Event: closed 2019-12-20, reopened 2020-09-12. Event month 2019-12 counts as
# "during" (it holds only ~11 closed days); "after" starts 2020-10.
PRE_END = 201911
DURING = (201912, 202009)
AFTER = (202010, 202412)
AFTER_Y1 = (202010, 202109)      # required after-period split
AFTER_LATER = (202110, 202412)
WINDOWS = {"during": DURING, "after": AFTER, "after_y1": AFTER_Y1, "after_later": AFTER_LATER}

# Robustness windows
DURING_ALT_START = (202001, 202009)                 # excludes the partial December
COVID_MONTHS = [202003, 202004, 202005, 202006]     # excluded from "during" in one check

# Window-total DiD on Dec->Sep windows (same 10 months as the closure).
DID_M_START, DID_M_END = 12, 9
DID_PRE_YEARS = [2016, 2017, 2018]   # Dec 2015 is outside the panel
DID_EVENT_YEAR = 2019
# After-period DiD on Oct->Sep years: pre 2016-17..2018-19; after years 2020-21..2023-24.
AFTER_DID_PRE_YEARS = [2016, 2017, 2018]
AFTER_DID_YEARS = [2020, 2021, 2022, 2023]

# Placebo-in-time. Main = pre-period fake events only. SC: Dec 2017, Dec 2018
# (Dec 2016 leaves 11 fit months). Extra (labeled): fake events after the
# reopening, fitted with the closure months left out.
SC_PLACEBO_YEARS_PRE = [2017, 2018]
PLACEBO_YEARS_POST = [2021, 2022, 2023]
CLOSURE_MONTHS = [201912] + [202000 + m for m in range(1, 10)]

# ---------------------------------------------------------------------------
# Donor pool (2016-24 ODFW units). Distances = charted-equivalent nm
# (sea_nm x 1.06) from data/processed/distance_matrix.csv, computed in run.
# ---------------------------------------------------------------------------
OR_UNITS = [
    "OR-ODFW-astoria", "OR-ODFW-gearhart-garibaldi", "OR-ODFW-netarts-depoe-bay", "OR-newport",
    "OR-ODFW-waldport-winchester-bay", "OR-charleston", "OR-ODFW-bandon-port-orford",
    "OR-ODFW-gold-beach-brookings",
]
# A unit is excluded as a possible receiver if any of its inventory harbors is
# within the logged 40 nm threshold of Charleston (Bandon 17.7 nm).
RECEIVER_RADIUS_NM = 40.0
# Northern CA robustness pool: CA crab Fishing Zones 1-2 harbors (Oregon border to
# the Sonoma/Mendocino line) that pass the null screens and have no own event in
# 2016-01..2024-12. Crescent City is left out (its own ice closure starts 2024-10).
CA_ZONE12 = ["CA-crescent-city", "CA-trinidad", "CA-humboldt-bay", "CA-noyo-harbor",
             "CA-shelter-cove", "CA-point-arena"]
CA_OWN_EVENT = {"CA-crescent-city": "own ice closure from 2024-10 (T4.1 case) inside the after-window"}
HEAVY_NULL_SHARE = 0.30
CRAB_DONOR_MIN_ANNUAL_USD = 100_000

# Units in the shift/combined analyses must not be donors for each other.
OUT_PREFIX = "t42"
