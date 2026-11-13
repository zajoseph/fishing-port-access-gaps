"""T2.1 build: monthly landings panel, withheld log, unit list, coverage and cross-checks.

Inputs (see data/manifest.csv):
  data/interim/odfw_ftr205_cells_all.csv      <- src/portgaps/ingest/odfw_ftr205.py over data/raw/landings/odfw
  data/raw/landings/cdfw/*.xlsx               MFDE Custom Queries exports (calendar year, 2016-01..2025-12)
  data/raw/landings/pacfin/*.csv              PacFIN APEX CRAB002 (monthly crab by port group), ALL005 (annual)
  data/raw/landings/foss/*.csv                NOAA FOSS landings by top US ports (annual)
  data/processed/ports.csv                    58-harbor inventory (agency codes in context_notes)
Outputs:
  data/processed/landings_monthly.csv, data/processed/withheld_log.csv
  outputs/tables/t21_units.csv, t21_coverage.csv, t21_annual_crosscheck.csv, t21_closure_blanks.csv, t21_checks.csv
Run from repo root:  python -I src/portgaps/clean/build_landings_t21.py
"""
import re, csv
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(".")
RAW = ROOT / "data/raw/landings"
OUT = ROOT / "outputs/tables"
LB_PER_MT = 2204.62262
WIN_START = (2016, 1)

ports = pd.read_csv(ROOT / "data/processed/ports.csv")
PORT_IDS = set(ports.port_id)

# ----------------------------------------------------------------------------
# Units
# ----------------------------------------------------------------------------
units = []  # dicts: unit_id, unit_type, unit_name, state, port_ids, agency_codes, source, first_year, last_year, notes

def add_unit(**k):
    for p in k["port_ids"].split(";"):
        assert p in PORT_IDS, p
    units.append(k)

# --- CA: one unit per harbor; multi-code harbors sum their CDFW codes
CA_CODES = {}
for r in ports[ports.state == "CA"].itertuples():
    m = re.search(r"CDFW port codes: (.+?); unit share", r.context_notes)
    codes = [(c.split(" ", 1)[0], c.split(" ", 1)[1].rsplit(" (", 1)[0]) for c in m.group(1).split("; ")]
    CA_CODES[r.port_id] = codes
    add_unit(unit_id=r.port_id, unit_type="harbor", unit_name=r.port_name, state="CA", port_ids=r.port_id,
             agency_codes=";".join(f"CDFW {c} {n}" for c, n in codes), source="cdfw_mfde",
             first_year=2016, last_year=2025,
             notes=("sum of CDFW codes" if len(codes) > 1 else "single CDFW code"))

# --- OR: ODFW FTR205 tables. Title patterns -> unit (composition changes in 2025)
OR_UNITS = [
    # unit_id, unit_type, name, port_ids, years, title regex, pacfin codes
    ("OR-ODFW-astoria", "code_group", "ODFW Astoria", "OR-astoria;OR-warrenton", (2016, 2025), r"^ASTORIA$|^ASTOIRA", "PacFIN AST"),
    ("OR-ODFW-gearhart-garibaldi", "agency_group", "ODFW Gearhart-Seaside-Cannon Beach-Nehalem Bay-Garibaldi", "OR-garibaldi", (2016, 2024), r"GEARHART", "PacFIN GSS;CNB;NHL;TLL"),
    ("OR-ODFW-netarts-depoe-bay", "agency_group", "ODFW Netarts-(Sand Lake)-Pacific City-Siletz Bay-Salmon River-Depoe Bay", "OR-depoe-bay", (2016, 2024), r"NETARTS", "PacFIN NTR;PCC;SLZ;SRV;DPO"),
    ("OR-newport", "harbor", "ODFW Newport", "OR-newport", (2016, 2024), r"^NEWPORT$", "PacFIN NEW"),
    ("OR-ODFW-waldport-winchester-bay", "agency_group", "ODFW Waldport-Yachats-Florence-Winchester Bay", "OR-florence;OR-winchester-bay", (2016, 2024), r"WALDPORT", "PacFIN WLD;YAC;FLR;WIN"),
    ("OR-charleston", "harbor", "ODFW Charleston", "OR-charleston", (2016, 2024), r"^CHARLESTON$", "PacFIN COS"),
    ("OR-ODFW-bandon-port-orford", "agency_group", "ODFW Bandon-Port Orford", "OR-bandon;OR-port-orford", (2016, 2024), r"BANDON", "PacFIN BDN;ORF"),
    ("OR-ODFW-gold-beach-brookings", "agency_group", "ODFW Gold Beach-Brookings", "OR-gold-beach;OR-brookings", (2016, 2024), r"GOLD BEACH", "PacFIN GLD;BRK"),
    # 2025 regrouping
    ("OR-ODFW-gearhart-siletz-bay-2025", "agency_group", "ODFW Gearhart-Cannon Beach-Nehalem Bay-Garibaldi-Netarts-Sand Lake-Pacific City-Salmon River-Siletz Bay", "OR-garibaldi", (2025, 2025), r"GEARHART", "PacFIN GSS;CNB;NHL;TLL;NTR;PCC;SRV;SLZ"),
    ("OR-ODFW-depoe-bay-yachats-2025", "agency_group", "ODFW Depoe Bay-Newport-Waldport-Yachats", "OR-depoe-bay;OR-newport", (2025, 2025), r"^DEPOE BAY", "PacFIN DPO;NEW;WLD;YAC"),
    ("OR-ODFW-florence-charleston-2025", "agency_group", "ODFW Florence-Winchester Bay-Charleston", "OR-florence;OR-winchester-bay;OR-charleston", (2025, 2025), r"^FLORENCE", "PacFIN FLR;WIN;COS"),
    ("OR-ODFW-bandon-brookings-2025", "agency_group", "ODFW Bandon-Port Orford-Gold Beach-Brookings", "OR-bandon;OR-port-orford;OR-gold-beach;OR-brookings", (2025, 2025), r"^BANDON", "PacFIN BDN;ORF;GLD;BRK"),
]
for uid, ut, nm, pids, yrs, rx, codes in OR_UNITS:
    add_unit(unit_id=uid, unit_type=ut, unit_name=nm, state="OR", port_ids=pids, agency_codes=codes,
             source="odfw_ftr205", first_year=yrs[0], last_year=yrs[1],
             notes="ODFW port table" + ("; composition changed in 2025 (ODFW regrouped tables)" if yrs[0] == 2025 else
                                       ("; ends 2024, ODFW regrouped in 2025" if yrs[1] == 2024 else "")))

# --- WA: PacFIN port groups (CRAB002, Dungeness crab only). Membership from PacFIN pc_tree.txt
WA_GROUPS = {
    "CLW": ("Columbia River Ports (Washington)", "WA-ilwaco;WA-chinook", "LWC;OCR"),
    "CWA": ("Washington Coastal Ports", "WA-westport;WA-tokeland;WA-bay-center;WA-nahcotta;WA-la-push", "CPL;GRH;LAP;OWC;WLB;WPT"),
    "NPS": ("North Puget Sound Ports", "WA-neah-bay;WA-port-angeles;WA-port-townsend;WA-la-conner;WA-anacortes;WA-bellingham;WA-blaine", "ANA;BLL;BLN;FRI;LAC;NEA;ONP;PAG;SEQ;TNS"),
    "SPS": ("South Puget Sound Ports", "WA-seattle;WA-everett", "EVR;OLY;OSP;SEA;SHL;TAC"),
}
for g, (nm, pids, codes) in WA_GROUPS.items():
    add_unit(unit_id=f"WA-PACFIN-{g}", unit_type="agency_group", unit_name=f"PacFIN {g} {nm}", state="WA", port_ids=pids,
             agency_codes=f"PacFIN group {g} (ports {codes})", source="pacfin_crab002", first_year=2016, last_year=2026,
             notes="Dungeness crab only; PacFIN port group; group also contains non-inventory ports")
U = pd.DataFrame(units)
U.to_csv(OUT / "t21_units.csv", index=False)

# ----------------------------------------------------------------------------
# Panel and withheld log
# ----------------------------------------------------------------------------
panel, wlog = [], []
FLAG_MEANING = {
    "confidential": "MFDE Confidential: withheld",
    "pacfin_confidential": "PacFIN -*: withheld",
    "blank_assumed_zero": "ODFW blank: zero or suppressed; set to 0 (assumption)",
    "dash_no_flag": "PacFIN - without *: no landings, 0",
}

def P(**k):
    panel.append(k)

# ---------------- CA (MFDE) ----------------
def load_mfde(fname, group_col=None):
    d = pd.read_excel(RAW / "cdfw" / fname)
    if group_col is None:
        d["species_group"] = "all"
    else:
        d["species_group"] = d[group_col]
    d["conf"] = d.Pounds.astype(str).eq("Confidential")
    assert (d.conf == d.Value.astype(str).eq("Confidential")).all()
    d["lb"] = pd.to_numeric(d.Pounds, errors="coerce")
    d["usd"] = pd.to_numeric(d.Value, errors="coerce")
    return d

mf_all = load_mfde("t21_cdfw_mfde_custom_year_month_port_2016-01_2025-12.xlsx")
mf_sg = load_mfde("t21_cdfw_mfde_custom_year_month_speciesgroup_port_2016-01_2025-12.xlsx", "Species Group")
mf_dc = load_mfde("t21_cdfw_mfde_custom_year_month_dungeness_port_2016-01_2025-12.xlsx", "Species Name")
mf_dc["species_group"] = "Dungeness crab"

name2harbor = {n.upper(): pid for pid, cs in CA_CODES.items() for c, n in cs}
name2code = {n.upper(): c for pid, cs in CA_CODES.items() for c, n in cs}
missing = set(name2harbor) - set(mf_all.Port)
assert not missing, missing

for d, scheme, fname in [(mf_all, "all", "t21_cdfw_mfde_custom_year_month_port_2016-01_2025-12.xlsx"),
                         (mf_sg, "MFDE species group", "t21_cdfw_mfde_custom_year_month_speciesgroup_port_2016-01_2025-12.xlsx"),
                         (mf_dc, "Dungeness crab", "t21_cdfw_mfde_custom_year_month_dungeness_port_2016-01_2025-12.xlsx")]:
    # withheld log: every Confidential cell in the export
    for r in d[d.conf].itertuples():
        hp = name2harbor.get(r.Port, "")
        wlog.append(dict(source="cdfw_mfde", source_file=fname, published_unit=r.Port,
                         agency_code=("CDFW " + name2code[r.Port]) if hp else "", unit_id=hp, port_ids=hp,
                         year=r.Year, month=r.Month, species_level=("all" if scheme == "all" else scheme),
                         species_label=r.species_group, measure="pounds+value", raw_cell="Confidential",
                         flag="confidential", flag_meaning=FLAG_MEANING["confidential"],
                         used_in_panel="Y" if hp else "N",
                         treatment=("null; excluded from harbor sum" if hp else "")))
    d = d[d.Port.isin(name2harbor)].copy()
    d["harbor"] = d.Port.map(name2harbor)
    groups = ["all"] if scheme == "all" else (["Dungeness crab"] if scheme == "Dungeness crab" else sorted(d.species_group.unique()))
    for pid, codes in CA_CODES.items():
        cnames = [n.upper() for c, n in codes]
        h = d[d.harbor == pid]
        for sg in groups:
            hs = h[h.species_group == sg]
            idx = {(r.Year, r.Month, r.Port): r for r in hs.itertuples()}
            months = [(y, m) for y in range(2016, 2026) for m in range(1, 13)]
            for y, m in months:
                comps = [idx.get((y, m, cn)) for cn in cnames]
                present = [c for c in comps if c is not None]
                if not present:
                    if scheme == "MFDE species group":
                        continue  # species-group rows are sparse: absent = no landings recorded
                    P(unit_id=pid, year=y, month=m, species_scheme=scheme, species_group=sg, pounds=0, value_usd=0,
                      withheld_flag="no_record_zero", n_components=len(cnames), n_withheld=0)
                    continue
                conf = [c for c in present if c.conf]
                num = [c for c in present if not c.conf]
                if conf and not num:
                    flag, lb, usd = "confidential", None, None
                else:
                    lb = float(sum(c.lb for c in num)); usd = float(sum(c.usd for c in num))
                    flag = "partial_confidential" if conf else ""
                P(unit_id=pid, year=y, month=m, species_scheme=scheme, species_group=sg, pounds=lb, value_usd=usd,
                  withheld_flag=flag, n_components=len(cnames), n_withheld=len(conf))

# ---------------- OR (ODFW FTR205) ----------------
oc = pd.read_csv(ROOT / "data/interim/odfw_ftr205_cells_all.csv")
oc = oc[oc.table_title.notna() & ~oc.table_title.str.contains("CRAYFISH|FRESH", na=False)].copy()
oc["title_n"] = oc.table_title.str.replace(r"^FOR (THE )?", "", regex=True).str.replace(" COMBINED", "").str.strip()

def or_unit(title, year):
    if title.startswith("COLUMBIA RIVER"):
        return None
    for uid, ut, nm, pids, yrs, rx, codes in OR_UNITS:
        if yrs[0] <= year <= yrs[1] and re.search(rx, title):
            return uid
    raise ValueError((title, year))

oc["unit_id"] = [or_unit(t, y) for t, y in zip(oc.title_n, oc.year)]
assert oc.groupby(["year", "unit_id"]).file.nunique().max() == 1
oc_files = oc.groupby("file").first()
uid2pids = dict(zip(U.unit_id, U.port_ids))

# withheld log: every blank cell (all levels; Columbia River table logged with used_in_panel=N)
ocb = oc[oc.value.isna()]
wide = ocb.groupby(["file", "page", "level", "category", "label", "month", "unit_id", "table_title", "year"], dropna=False).measure.apply(lambda s: "+".join(sorted(set(s)))).reset_index()
for r in wide.itertuples():
    used = isinstance(r.unit_id, str) and (r.level in ("grand_total", "category") or "Dungeness" in r.label)
    lvl = {"grand_total": "all", "category": "ODFW category", "species": "species"}[r.level]
    wlog.append(dict(source="odfw_ftr205", source_file=r.file, published_unit=r.table_title, agency_code="",
                     unit_id=r.unit_id if isinstance(r.unit_id, str) else "", port_ids=uid2pids.get(r.unit_id, "") if isinstance(r.unit_id, str) else "",
                     year=r.year, month=r.month, species_level=lvl,
                     species_label=(r.label if r.level != "species" else f"{r.category} > {r.label}"),
                     measure=r.measure.replace("value_usd", "value"), raw_cell="blank", flag="blank_assumed_zero",
                     flag_meaning=FLAG_MEANING["blank_assumed_zero"], used_in_panel="Y" if used else "N",
                     treatment="set to 0" if used else ("not in panel (Columbia River table)" if not isinstance(r.unit_id, str) else "species cell; panel uses total/category")))

op = oc[oc.unit_id.notna()].copy()
def or_rows(sel, scheme, sg_of):
    for (uid, y, m, sg), g in sel.groupby(["unit_id", "year", "month", sel.apply(sg_of, axis=1)]):
        lb = g[g.measure == "pounds"].value; usd = g[g.measure == "value_usd"].value
        allblank = lb.isna().all() and usd.isna().all()
        P(unit_id=uid, year=int(y), month=int(m), species_scheme=scheme, species_group=sg,
          pounds=float(lb.fillna(0).sum()), value_usd=float(usd.fillna(0).sum()),
          withheld_flag="blank_assumed_zero" if allblank else ("part_blank_assumed_zero" if (lb.isna().any() or usd.isna().any()) else ""),
          n_components=int(g.label.nunique()), n_withheld=int(g[g.value.isna()].label.nunique()))
or_rows(op[op.level == "grand_total"], "all", lambda r: "all")
or_rows(op[op.level == "category"], "ODFW category", lambda r: r.label)
dcr = op[op.label.str.contains("Dungeness")]
or_rows(dcr, "Dungeness crab", lambda r: "Dungeness crab")
# OR Dungeness: unit-years with no Dungeness row at all -> 0 (no_record_zero)
have = set(zip(dcr.unit_id, dcr.year))
for (uid, y) in set(zip(op.unit_id, op.year)) - have:
    for m in range(1, 13):
        P(unit_id=uid, year=int(y), month=m, species_scheme="Dungeness crab", species_group="Dungeness crab",
          pounds=0.0, value_usd=0.0, withheld_flag="no_record_zero", n_components=0, n_withheld=0)

# ---------------- WA (PacFIN CRAB002) ----------------
CRAB_F = "t21_pacfin_CRAB002_WOC_crabyear2015-2026.csv"
cr = pd.read_csv(RAW / "pacfin" / CRAB_F, dtype={"CRAB_YEAR": int})
MON = ["NOV", "DEC", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT"]
MNUM = [11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
for r in cr.to_dict("records"):
    for mn, mi in zip(MON, MNUM):
        y = r["CRAB_YEAR"] - 1 if mi >= 11 else r["CRAB_YEAR"]  # crab year Y = Nov(Y-1)..Oct(Y); verified vs ALL005
        mt, usd, fl = r[f"{mn}_ROUND_WEIGHT_MTONS"], r[f"{mn}_EXVESSEL_REVENUE"], r[f"{mn}_CONFIDENTIAL_FLAG"]
        star = isinstance(fl, str) and fl.strip() == "*"
        dash = pd.isna(mt) and pd.isna(usd)
        g = r["PACFIN_GROUP_PORT_CODE"]
        uid = f"WA-PACFIN-{g}" if (r["AGENCY_CODE"] == "W" and g in WA_GROUPS) else ""
        inwin = (y, mi) >= WIN_START
        if star or dash:
            wlog_flag = "pacfin_confidential" if star else "dash_no_flag"
            if star or uid:  # log every '*'; log bare '-' only where the panel uses it
                wlog.append(dict(source="pacfin_crab002", source_file=CRAB_F, published_unit=f"{r['AGENCY_CODE']} {g} {r['PORT_DESCRIPTION']}",
                                 agency_code=f"PacFIN group {g}", unit_id=uid, port_ids=uid2pids.get(uid, ""), year=y, month=mi,
                                 species_level="species", species_label="Dungeness crab", measure="pounds+value",
                                 raw_cell="-*" if star else "-", flag=wlog_flag, flag_meaning=FLAG_MEANING[wlog_flag],
                                 used_in_panel="Y" if (uid and inwin) else "N",
                                 treatment=("value withheld (null)" if star else "set to 0") if (uid and inwin) else ""))
        if not uid or not inwin:
            continue
        if star:
            P(unit_id=uid, year=y, month=mi, species_scheme="Dungeness crab", species_group="Dungeness crab",
              pounds=None, value_usd=None, withheld_flag="pacfin_confidential", n_components=1, n_withheld=1)
        else:
            P(unit_id=uid, year=y, month=mi, species_scheme="Dungeness crab", species_group="Dungeness crab",
              pounds=0.0 if dash else round(float(mt) * LB_PER_MT), value_usd=0.0 if dash else float(usd),
              withheld_flag="dash_assumed_zero" if dash else "", n_components=1, n_withheld=0)

# ---------------- assemble ----------------
pn = pd.DataFrame(panel)
pn = pn[(pn.year * 100 + pn.month) >= WIN_START[0] * 100 + WIN_START[1]]
pn = pn.merge(U[["unit_id", "unit_type", "unit_name", "state", "port_ids", "agency_codes", "source"]], on="unit_id", how="left")
assert pn.unit_type.notna().all()
SRC_FILE = {"cdfw_mfde": "data/raw/landings/cdfw/ (see species_scheme)", "odfw_ftr205": "data/raw/landings/odfw/ FTR205 PDFs",
            "pacfin_crab002": f"data/raw/landings/pacfin/{CRAB_F}"}
pn["vessels"] = ""  # not published in any export used (MFDE vessel counts are in the Visualize page only)
pn["pounds_basis"] = pn.source.map({"cdfw_mfde": "landed weight as published (MFDE)",
                                    "odfw_ftr205": "round weight; dealer purchase date",
                                    "pacfin_crab002": "round weight, converted from metric tons (x2204.62262)"})
for c in ["pounds", "value_usd"]:
    pn[c] = pn[c].round(0).astype("Int64")
cols = ["unit_id", "unit_type", "unit_name", "state", "port_ids", "agency_codes", "year", "month", "species_scheme",
        "species_group", "pounds", "value_usd", "vessels", "source", "withheld_flag", "n_components", "n_withheld", "pounds_basis"]
pn["withheld_flag"] = pn.withheld_flag.replace("", "none")
pn = pn[cols].sort_values(["state", "unit_id", "species_scheme", "species_group", "year", "month"])
assert not pn.duplicated(["unit_id", "year", "month", "species_scheme", "species_group"]).any()
pn.to_csv(ROOT / "data/processed/landings_monthly.csv", index=False)

wl = pd.DataFrame(wlog)
wl = wl[(wl.year * 100 + wl.month) >= 201601]
wl = wl.sort_values(["source", "published_unit", "year", "month", "species_level", "species_label"])
wl.to_csv(ROOT / "data/processed/withheld_log.csv", index=False)
print("panel rows", len(pn), "| withheld_log rows", len(wl))
print(pn.groupby(["state", "species_scheme"]).size())
print(pn.withheld_flag.value_counts(dropna=False))
print(wl.groupby(["source", "flag", "used_in_panel"]).size())
