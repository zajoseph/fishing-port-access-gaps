#!/usr/bin/env bash
# T3.3 review: independent recompute, event check, descriptive landings.  Run from the repo root.
set -euo pipefail
R="$(pwd)"; export T33_WORK="${T33_WORK:-/tmp/t33}"
python3 -I src/portgaps/review/t33_indep.py "$R"          # all runs x thresholds vs index_sensitivity.csv
python3 -I src/portgaps/review/t33_events.py "$R"         # event cells through the index's own removal logic
python3 -I src/portgaps/review/t33_landings_desc.py "$R"  # descriptive before/during means (no causal estimates)
python3 -I src/portgaps/review/t33_build_event_csv.py "$R" # -> outputs/tables/t33_event_check.csv
