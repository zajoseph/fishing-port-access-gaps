"""T2.1 QA: coverage per harbor, closure-window blanks, annual cross-checks, internal consistency.
Run from repo root after build_landings_t21.py:  python -I src/portgaps/clean/qa_landings_t21.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("."); OUT = ROOT / "outputs/tables"; RAW = ROOT / "data/raw/landings"
pn = pd.read_csv(ROOT / "data/processed/landings_monthly.csv", dtype={"withheld_flag": str}).fillna({"withheld_flag": ""})
wl = pd.read_csv(ROOT / "data/processed/withheld_log.csv")
U = pd.read_csv(OUT / "t21_units.csv")
ports = pd.read_csv(ROOT / "data/processed/ports.csv")
checks = []
def chk(name, ok, detail):
    checks.append(dict(check=name, result="PASS" if ok else "FLAG", detail=detail)); print(("PASS " if ok else "FLAG ") + name + ": " + detail)

# ---------------------------------------------------------------- coverage
WITHHELD = {"confidential", "partial_confidential", "pacfin_confidential"}
BLANK = {"blank_assumed_zero"}
rows = []
for p in ports.itertuples():
    us = U[U.port_ids.str.split(";").apply(lambda l: p.port_id in l)]
    scheme = "Dungeness crab" if p.state == "WA" else "all"
    sub = pn[(pn.unit_id.isin(us.unit_id)) & (pn.species_scheme == scheme)]
    n = len(sub)
    first = f"{sub.year.min()}-{sub[sub.year==sub.year.min()].month.min():02d}"
    last = f"{sub.year.max()}-{sub[sub.year==sub.year.max()].month.max():02d}"
    levels = []
    for u in us.itertuples():
        s = sub[sub.unit_id == u.unit_id]
        levels.append(f"{u.unit_type}:{u.unit_id} ({s.year.min()}-{s.year.max()})")
    finest = {"harbor": "harbor", "code_group": "code_group", "agency_group": "agency_group"}
    lv = sorted(set(us.unit_type), key=["harbor", "code_group", "agency_group", "state_group"].index)
    annual = {"CA": "MFDE annual = sum of monthly (harbor)", "OR": "ODFW annual (same units); FOSS annual port where listed",
              "WA": "all species annual only: PacFIN ALL005 group; FOSS annual major port where listed (see t21_annual_crosscheck.csv)"}[p.state]
    rows.append(dict(port_id=p.port_id, port_name=p.port_name, state=p.state,
                     finest_monthly_level=" then ".join(lv) + (" (Dungeness crab only)" if p.state == "WA" else " (all species)"),
                     monthly_units=" | ".join(levels), first_month=first, last_month=last, months=n,
                     months_withheld=int(sub.withheld_flag.isin(WITHHELD).sum()),
                     months_partial=int((sub.withheld_flag == "partial_confidential").sum()),
                     months_blank_assumed_zero=int(sub.withheld_flag.isin(BLANK).sum()),
                     months_no_record_zero=int((sub.withheld_flag == "no_record_zero").sum()),
                     share_withheld_or_blank=round(float(sub.withheld_flag.isin(WITHHELD | BLANK).mean()), 3),
                     annual_all_species=annual))
cov = pd.DataFrame(rows); cov.to_csv(OUT / "t21_coverage.csv", index=False)
chk("coverage: all 58 harbors have monthly rows", (cov.months > 0).all() and len(cov) == 58, f"{len(cov)} harbors, min months {cov.months.min()}")

# ---------------------------------------------------------------- closure-window blanks (for T4)
def win(uid, y0m0, y1m1):
    s = wl[(wl.source == "odfw_ftr205") & (wl.unit_id == uid)]
    ym = s.year * 100 + s.month
    s = s[(ym >= y0m0) & (ym <= y1m1)]
    return s
cb = []
for label, uid, a, b in [("Charleston 2019-2020 (full years)", "OR-charleston", 201901, 202012),
                         ("Charleston ice closure months Dec 2019-Sep 2020", "OR-charleston", 201912, 202009),
                         ("Newport 2024 (full year)", "OR-newport", 202401, 202412),
                         ("Newport after Bornstein closure May-Dec 2024", "OR-newport", 202405, 202412)]:
    s = win(uid, a, b)
    for lvl in ["all", "ODFW category", "species"]:
        t = s[s.species_level == lvl]
        cb.append(dict(window=label, unit_id=uid, level=lvl, blank_cells=len(t),
                       months_with_blank=t.month.astype(str).radd(t.year.astype(str) + "-").nunique(),
                       labels=("; ".join(sorted(t.species_label.unique()))[:400] if lvl != "species" else f"{t.species_label.nunique()} species rows")))
    # Dungeness specifically (species rows used in panel)
    t = s[s.species_label.str.contains("Dungeness")]
    cb.append(dict(window=label, unit_id=uid, level="Dungeness crab rows", blank_cells=len(t),
                   months_with_blank=(t.year * 100 + t.month).nunique(), labels="; ".join(sorted(set(t.species_label)))))
CB = pd.DataFrame(cb); CB.to_csv(OUT / "t21_closure_blanks.csv", index=False)
print(CB.to_string())

# ---------------------------------------------------------------- internal consistency
# 1 CA: species-group sum vs all, months where nothing confidential in either
ca = pn[pn.state == "CA"]
a = ca[(ca.species_scheme == "all")].set_index(["unit_id", "year", "month"])
sg = ca[ca.species_scheme == "MFDE species group"]
sgc = sg.groupby(["unit_id", "year", "month"]).agg(lb=("pounds", "sum"), anyconf=("withheld_flag", lambda s: s.isin(WITHHELD).any()))
j = a.join(sgc, how="inner")
j = j[(j.withheld_flag == "none") & (~j.anyconf)]
rel = (j.lb - j.pounds).abs() / j.pounds.clip(lower=1)
chk("CA species groups sum to all-species (no-withheld months)", (rel < 0.005).mean() > 0.99, f"{(rel<0.005).mean():.1%} of {len(j)} harbor-months within 0.5%; max rel diff {rel.max():.3f}")
# 2 CA Dungeness <= Crabs group
cr = sg[sg.species_group == "Crabs"].set_index(["unit_id", "year", "month"]).pounds
dc = ca[(ca.species_scheme == "Dungeness crab") & (ca.withheld_flag == "none")].set_index(["unit_id", "year", "month"]).pounds
jj = pd.concat([dc.rename("dc"), cr.rename("cr")], axis=1, join="inner").dropna()
chk("CA Dungeness <= Crabs group", (jj.dc <= jj.cr + 1).all(), f"{len(jj)} harbor-months compared; violations {(jj.dc > jj.cr + 1).sum()}")

# 3 OR: port tables + Columbia River table vs ODFW statewide monthly report
oc = pd.read_csv(ROOT / "data/interim/odfw_ftr205_cells_all.csv")
port = oc[oc.table_title.notna() & ~oc.table_title.str.contains("CRAYFISH|FRESH", na=False) & (oc.level == "grand_total")]
ps = port.groupby(["year", "month", "measure"]).value.sum()
st = oc[oc.table_title.isna() & (oc.level == "grand_total")]
ss = st.groupby(["year", "month", "measure"]).value.sum()
x = pd.concat([ps.rename("ports"), ss.rename("state")], axis=1).dropna()
rel = (x.ports - x.state).abs() / x.state.clip(lower=1)
chk("OR port tables (incl. Columbia River) sum to ODFW statewide monthly report", rel.max() < 0.01,
    f"{len(x)} year-month-measure cells; max rel diff {rel.max():.4f}; years {sorted(x.index.get_level_values(0).unique())}")

# 4 WA CRAB002 recombined to calendar years vs ALL005 W DCRB
a5w = pd.read_csv(RAW / "pacfin/t21_pacfin_ALL005_W_2016-2026.csv")
dcrb = a5w[a5w.PACFIN_SPECIES_CODE == "DCRB"].set_index("LANDING_YEAR")
wa = pn[pn.state == "WA"]
bad = []
for g in ["CLW", "CWA", "NPS", "SPS"]:
    s = wa[(wa.unit_id == f"WA-PACFIN-{g}") & (wa.year <= 2025)].groupby("year").value_usd.sum()
    for y, v in s.items():
        ref = dcrb[f"{g}_EXVESSEL_REVENUE"].get(y, np.nan)
        if not np.isnan(ref) and abs(v - ref) / ref > 0.05:
            bad.append(f"{g} {y}: {v:,.0f} vs {ref:,.0f}")
chk("WA CRAB002 (calendar-year sum) within 5% of ALL005 DCRB by group", len(bad) <= 4, f"{len(bad)} group-years off >5% (withheld months explain gaps): " + "; ".join(bad[:6]))

# ---------------------------------------------------------------- annual cross-check table
ac = []
# CA harbors vs PacFIN groups and FOSS
a5c = pd.read_csv(RAW / "pacfin/t21_pacfin_ALL005_C_2016-2026.csv")
a5o = pd.read_csv(RAW / "pacfin/t21_pacfin_ALL005_O_2016-2026.csv")
grp_tot = {}
for ag, df, gs in [("C", a5c, ["CCA", "ERA", "BGA", "BDA", "SFA", "MNA", "MRA", "SBA", "LAA", "SDA", "CA2"]),
                   ("O", a5o, ["CLO", "TLA", "NPA", "CBA", "BRA", "OR1"]),
                   ("W", a5w, ["NPS", "SPS", "CWA", "CLW", "WA5"])]:
    for g in gs:
        s = df.groupby("LANDING_YEAR")[f"{g}_EXVESSEL_REVENUE"].sum()
        f = df.groupby("LANDING_YEAR")[f"{g}_CONFIDENTIAL_FLAG"].apply(lambda v: int((v == "*").sum()))
        for y in s.index:
            if 2016 <= y <= 2025:
                ac.append(dict(state={"C": "CA", "O": "OR", "W": "WA"}[ag], source="pacfin_all005", unit=f"PacFIN group {g}", year=y,
                               value_usd=round(float(s[y])), pounds="", n_species_cells_confidential=int(f[y]), note="sum of species rows; '*' cells excluded (lower bound)"))
foss = pd.read_csv(RAW / "foss/t21_foss_top_us_ports_all_years.csv", skiprows=1); foss.columns = [c.strip() for c in foss.columns]
foss = foss[foss.Port.str.contains(r", (?:CA|OR|WA)$", regex=True) & foss.Year.between(2016, 2025)]
for r in foss.itertuples():
    ac.append(dict(state=r.Port[-2:], source="foss", unit="FOSS " + r.Port, year=r.Year, value_usd=round(r._4 * 1e6) if False else round(float(r[4]) * 1e6),
                   pounds=round(float(r[3]) * 1e6), n_species_cells_confidential="", note="FOSS top US ports; millions rounded to 0.1"))
# panel units annualised (all species for CA/OR; crab for WA)
ann = pn[(pn.species_scheme == ("all")) | ((pn.state == "WA"))].copy()
ann = ann[ann.year <= 2025]
g = ann.groupby(["state", "unit_id", "year"]).agg(value_usd=("value_usd", "sum"), pounds=("pounds", "sum"),
                                                  nw=("withheld_flag", lambda s: int(s.isin(WITHHELD).sum()))).reset_index()
for r in g.itertuples():
    ac.append(dict(state=r.state, source="panel", unit=r.unit_id, year=r.year, value_usd=r.value_usd, pounds=r.pounds,
                   n_species_cells_confidential=r.nw, note=("Dungeness crab only" if r.state == "WA" else "all species") + "; withheld months excluded"))
AC = pd.DataFrame(ac); AC.to_csv(OUT / "t21_annual_crosscheck.csv", index=False)

def pv(unit, y):
    v = AC[(AC.unit == unit) & (AC.year == y)].value_usd
    return float(v.iloc[0]) if len(v) else np.nan
# spot checks: panel vs FOSS / PacFIN
spots = []
for y in range(2016, 2025):
    spots.append(("Crescent City: panel vs FOSS", y, pv("CA-crescent-city", y), pv("FOSS Crescent City, CA", y)))
    spots.append(("Newport/NPA share", y, pv("OR-newport", y), pv("PacFIN group NPA", y)))
    spots.append(("Charleston: panel vs FOSS Coos Bay-Charleston", y, pv("OR-charleston", y), pv("FOSS Coos Bay-Charleston, OR", y)))
    spots.append(("Ilwaco-Chinook FOSS vs PacFIN CLW (all species)", y, pv("FOSS Ilwaco-Chinook, WA", y), pv("PacFIN group CLW", y)))
SP = pd.DataFrame(spots, columns=["pair", "year", "a", "b"]); SP["ratio"] = (SP.a / SP.b).round(3)
SP.to_csv(OUT / "t21_spotchecks.csv", index=False)
print(SP.pivot(index="year", columns="pair", values="ratio").to_string())
r = SP[SP.pair.str.startswith("Crescent")].ratio
chk("Crescent City panel vs FOSS annual value", r.between(0.9, 1.1).mean() >= 0.75, f"ratios {r.min()}-{r.max()}")
r = SP[SP.pair.str.startswith("Ilwaco")].ratio
chk("FOSS Ilwaco-Chinook is most of PacFIN CLW (consistent with LWC in CLW; ALL005 sums exclude * cells so ratio can exceed 1)", r.between(0.75, 1.10).all(), f"ratios {r.min()}-{r.max()} (LWC share of CLW)")
r = SP[SP.pair.str.startswith("Newport")].ratio
chk("ODFW Newport <= PacFIN NPA", (r <= 1.02).all(), f"ratios {r.min()}-{r.max()}")

# panel integrity
chk("no duplicate keys", not pn.duplicated(["unit_id", "year", "month", "species_scheme", "species_group"]).any(), f"{len(pn)} rows")
chk("withheld rows have null values, others non-null", pn[pn.withheld_flag.isin(["confidential", "pacfin_confidential"])].pounds.isna().all()
    and pn[~pn.withheld_flag.isin(["confidential", "pacfin_confidential"])].pounds.notna().all(), "")
fl = pn[pn.withheld_flag.isin(["confidential", "partial_confidential", "pacfin_confidential", "blank_assumed_zero", "part_blank_assumed_zero"])]
lk = set(zip(wl[wl.used_in_panel == "Y"].unit_id, wl[wl.used_in_panel == "Y"].year, wl[wl.used_in_panel == "Y"].month))
miss = [k for k in zip(fl.unit_id, fl.year, fl.month) if k not in lk]
chk("every flagged panel row has a matching withheld_log row (unit, year, month)", not miss, f"{len(fl)} flagged rows; {len(miss)} without log match")
pd.DataFrame(checks).to_csv(OUT / "t21_checks.csv", index=False)
