"""Write docs/port_crosswalk.md from ports.csv, t21_units.csv and t21_coverage.csv.
PacFIN port codes and groups: PacFIN pc_tree.txt (read 2026-11-13). Run from repo root after the QA script."""
from pathlib import Path
import pandas as pd

ROOT = Path(".")
ports = pd.read_csv(ROOT / "data/processed/ports.csv")
U = pd.read_csv(ROOT / "outputs/tables/t21_units.csv")
cov = pd.read_csv(ROOT / "outputs/tables/t21_coverage.csv").set_index("port_id")

# port_id -> (PacFIN port code(s), PacFIN group, FOSS annual port name or "")
# "~" marks an inferred assignment: CDFW code mapped to a PacFIN "Other ... County" code by county.
PF = {
 "CA-crescent-city": ("CRS", "CCA", "Crescent City"),
 "CA-trinidad": ("TRN", "ERA", "Trinidad (2023 only)"),
 "CA-humboldt-bay": ("ERK; FLN; ~OHB (Humboldt Bay, King Salmon, Arcata)", "ERA", "Eureka"),
 "CA-shelter-cove": ("~OHB", "ERA", ""),
 "CA-noyo-harbor": ("BRG", "BGA", "Fort Bragg"),
 "CA-point-arena": ("ARE", "BGA", ""),
 "CA-bodega-bay": ("BDG", "BDA", "Bodega Bay"),
 "CA-san-francisco": ("SF", "SFA", "San Francisco Area (group)"),
 "CA-vallejo": ("~OSF", "SFA", "San Francisco Area (group)"),
 "CA-berkeley": ("BKL", "SFA", "San Francisco Area (group)"),
 "CA-pillar-point": ("PRN", "SFA", "Princeton-Half Moon Bay"),
 "CA-santa-cruz": ("CRZ", "MNA", ""),
 "CA-moss-landing": ("MOS", "MNA", "Moss Landing"),
 "CA-monterey": ("MNT", "MNA", "Monterey"),
 "CA-morro-bay": ("MRO", "MRA", "Morro Bay"),
 "CA-port-san-luis": ("AVL", "MRA", "Avila Beach (2023 only)"),
 "CA-santa-barbara": ("SB", "SBA", "Santa Barbara"),
 "CA-ventura": ("VEN", "SBA", "Port Hueneme-Oxnard-Ventura (group)"),
 "CA-channel-islands": ("OXN", "SBA", "Port Hueneme-Oxnard-Ventura (group)"),
 "CA-port-hueneme": ("HNM", "SBA", "Port Hueneme-Oxnard-Ventura (group)"),
 "CA-marina-del-rey": ("~OLA", "LAA", ""),
 "CA-redondo-beach": ("~OLA", "LAA", ""),
 "CA-los-angeles-long-beach": ("TRM; SP; LGB; WLM; ~OLA (Los Angeles 744)", "LAA", "Los Angeles"),
 "CA-huntington-harbour": ("~OLA", "LAA", ""),
 "CA-newport-beach": ("NWB", "LAA", ""),
 "CA-avalon": ("~OLA", "LAA", ""),
 "CA-dana-point": ("DNA", "LAA", "Dana Point (2023 only)"),
 "CA-oceanside": ("OCN", "SDA", "Oceanside (2023 only)"),
 "CA-mission-bay": ("~OSD", "SDA", ""),
 "CA-san-diego-bay": ("SD; ~OSD (Point Loma)", "SDA", "San Diego"),
 "OR-astoria": ("AST (shared)", "CLO", "Astoria"),
 "OR-warrenton": ("AST (shared)", "CLO", "Astoria"),
 "OR-garibaldi": ("TLL", "TLA", "Tillamook"),
 "OR-depoe-bay": ("DPO", "NPA", ""),
 "OR-newport": ("NEW", "NPA", "Newport"),
 "OR-florence": ("FLR", "CBA", ""),
 "OR-winchester-bay": ("WIN", "CBA", "Winchester Bay"),
 "OR-charleston": ("COS", "CBA", "Coos Bay-Charleston"),
 "OR-bandon": ("BDN", "CBA", ""),
 "OR-port-orford": ("ORF", "BRA", "Port Orford"),
 "OR-gold-beach": ("GLD", "BRA", ""),
 "OR-brookings": ("BRK", "BRA", "Brookings"),
 "WA-ilwaco": ("LWC (shared Ilwaco/Chinook)", "CLW", "Ilwaco-Chinook"),
 "WA-chinook": ("LWC (shared Ilwaco/Chinook)", "CLW", "Ilwaco-Chinook"),
 "WA-tokeland": ("WLB (shared)", "CWA", "Willapa Bay"),
 "WA-bay-center": ("WLB (shared)", "CWA", "Willapa Bay"),
 "WA-nahcotta": ("WLB (shared)", "CWA", "Willapa Bay"),
 "WA-westport": ("WPT", "CWA", "Westport"),
 "WA-la-push": ("LAP", "CWA", "La Push"),
 "WA-neah-bay": ("NEA", "NPS", "Neah Bay"),
 "WA-port-angeles": ("PAG", "NPS", "Port Angeles (2019, 2023)"),
 "WA-port-townsend": ("TNS", "NPS", "Port Townsend (2019, 2023)"),
 "WA-seattle": ("SEA", "SPS", "Seattle"),
 "WA-everett": ("EVR", "SPS", "Everett (2016-2019)"),
 "WA-la-conner": ("LAC", "NPS", "Anacortes-La Conner (group)"),
 "WA-anacortes": ("ANA", "NPS", "Anacortes-La Conner (group)"),
 "WA-bellingham": ("BLL", "NPS", "Bellingham"),
 "WA-blaine": ("BLN", "NPS", "Blaine"),
}
assert set(PF) == set(ports.port_id)

def agency(r):
    us = U[U.port_ids.str.split(";").apply(lambda l: r.port_id in l)]
    if r.state == "CA":
        return us.agency_codes.iloc[0].replace("CDFW ", "")
    if r.state == "OR":
        return " / ".join(f"{u.unit_name.replace('ODFW ', '')} ({u.first_year}" + (f"-{u.last_year})" if u.last_year != u.first_year else ")") for u in us.itertuples())
    return "none public (WDFW)"

lines = []
for r in ports.itertuples():
    pc, grp, foss = PF[r.port_id]
    c = cov.loc[r.port_id]
    us = U[U.port_ids.str.split(";").apply(lambda l: r.port_id in l)]
    shares = [u for u in us.itertuples() if len(u.port_ids.split(";")) > 1]
    level = c.finest_monthly_level
    if r.state == "CA":
        report = "MFDE Port = " + "; ".join(x.split(" ", 2)[2].upper() for x in us.agency_codes.iloc[0].split(";"))
    elif r.state == "OR":
        report = "ODFW FTR205 table(s): " + agency(r)
    else:
        report = f"PacFIN CRAB002 group {grp}"
    lines.append(f"| {r.port_id} | {r.port_name} | {agency(r) if r.state != 'OR' else '(ODFW tables at right)'} | {pc} | {grp} | {report} | {level} | {'; '.join(us.unit_id)} | {foss or '-'} |")

hdr = """# Port crosswalk (T2.1)

As of 2026-11-13. Built by `src/portgaps/clean/write_crosswalk_t21.py` from `data/processed/ports.csv`, `outputs/tables/t21_units.csv` and `outputs/tables/t21_coverage.csv`.

**How to read it.** Each of the 58 inventory harbors (`port_id`) maps to:
- the agency port code(s) its landings are reported under;
- the PacFIN port code and **PacFIN port group**, from PacFIN's public port hierarchy (`pc_tree.txt`, https://pacfin.psmfc.org/pacfin_pub/data_rpts_pub/code_lists/pc_tree.txt, read 2026-11-13). A `~` marks an inferred assignment: a CDFW code with no PacFIN code of its own, placed in the PacFIN "Other ... County Ports" code for its county;
- the report name used in the panel (CDFW MFDE port name, ODFW FTR205 table, or PacFIN CRAB002 group);
- the **finest level the monthly panel has for it**, and the panel `unit_id`(s) that carry it (`data/processed/landings_monthly.csv`);
- the NOAA FOSS annual "top US ports" name, where one exists (annual cross-check only; see `outputs/tables/t21_annual_crosscheck.csv`).

**Unit types** (`unit_type` in the panel):
- `harbor`: the unit is this one harbor. CA multi-code harbors (Humboldt Bay, LA/LB, San Diego Bay) are the sum of their CDFW codes.
- `code_group`: one agency port code that covers several inventory harbors (ODFW Astoria = PacFIN AST, covers Astoria + Warrenton).
- `agency_group`: an agency's multi-port reporting group (ODFW combined-port tables; PacFIN port groups for WA). Values are the group total and are **never split** across harbors here.
- `state_group`: not used (no harbor relies on a statewide figure).

**Shared codes and groups.**
- AST (Astoria + Warrenton): ODFW "Astoria" table, 2016-2025. ODFW gives no Warrenton-only figure.
- LWC (Ilwaco + Chinook): no public all-species monthly data. Panel unit = PacFIN CRAB002 group **CLW**, Dungeness crab only. **Evidence for Ilwaco in CLW:** PacFIN `pc_tree.txt` lists LWC ILWACO/CHINOOK under CLW COLUMBIA RIVER PORTS (WASHINGTON), with OCR (other Columbia River ports) as the only other member. Consistent with this, FOSS annual "Ilwaco-Chinook" value is 0.82-1.05 x PacFIN ALL005 CLW (2016-2024) (`outputs/tables/t21_spotchecks.csv`).
- WLB (Tokeland + Bay Center + Nahcotta): in PacFIN group CWA with Westport and La Push; FOSS has an annual "Willapa Bay" row.
- ODFW 2025 break: tables were regrouped in 2025. Charleston moves into "Florence-Winchester Bay-Charleston"; Newport into "Depoe Bay-Newport-Waldport-Yachats"; Gold Beach-Brookings merges with Bandon-Port Orford; Garibaldi's group adds Netarts to Siletz Bay (Depoe Bay leaves it). Each composition has its own `unit_id`; no group is split by assumption.
- ODFW "Columbia River" table (in-river landings) maps to no inventory harbor and is not in the panel. It is used only in the statewide-sum check.

**WA.** No public port-level or all-species monthly landings. The finest monthly level is the PacFIN port group, for Dungeness crab only. All-species values exist only annually: PacFIN ALL005 by group, and FOSS by major port where listed.

| port_id | harbor | agency code(s) | PacFIN code | PacFIN group | report name in panel | finest monthly level | panel unit_id(s) | FOSS annual port |
|---|---|---|---|---|---|---|---|---|
"""
(ROOT / "docs/port_crosswalk.md").write_text(hdr + "\n".join(lines) + "\n")
print("wrote", len(lines), "rows")
