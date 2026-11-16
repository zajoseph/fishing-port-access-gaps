"""T3.3 independent recompute of the failure index (imports nothing from portgaps).
Updated in T3.4: implements the F1 tie rule, the literal F2 non-inventory rule
(derived here from t21_units.csv + port_crosswalk.md, not from config.py) and
run s4 (no-moorage launch-hoist harbors cannot substitute hoist; harbor list
derived here from the T1.3 dual-use hoist tag in facilities.csv notes).
Used as index check C10. Writes $T33_WORK/indep_all.csv and indep_summary.json;
exits 1 on any mismatch.  Usage: python3 -I t33_indep.py <repo_root>"""
import sys, os, re, json
import pandas as pd
WORK = os.environ.get("T33_WORK", "/tmp/t33"); os.makedirs(WORK, exist_ok=True)
R = sys.argv[1]
P = f"{R}/data/processed"; T = f"{R}/outputs/tables"
fac = pd.read_csv(f"{P}/facilities.csv", dtype=str).fillna("")
fac["line"] = [i + 2 for i in range(len(fac))]            # file line, header = line 1
dd = fac.groupby(["port_id","service","as_of_date"]).status.nunique()
print("same-date conflicting status:", dd[dd>1].to_dict())
# F1: latest as_of_date; same date -> higher file line wins (explicit, no reliance on sort stability)
st = {}
best = {}
for r in fac.itertuples():
    k = (r.port_id, r.service); key = (r.as_of_date, r.line)
    if k not in best or key > best[k]:
        best[k] = key; st[k] = r.status
dm = pd.read_csv(f"{P}/distance_matrix.csv")
ports = sorted(pd.read_csv(f"{P}/ports.csv").port_id)
dist = {(r.from_port_id, r.to_port_id): r.sea_nm*1.06 for r in dm.itertuples()}
for p in ports: dist[(p,p)] = 0.0
# ---- values from raw panel / crosscheck -------------------------------
br = pd.read_csv(f"{P}/port_unit_bridge.csv")
br = br[(br.valid_from<="2019-01")&(br.valid_to>="2024-12")]
unit = dict(zip(br.port_id, br.unit_id))
members = br.groupby("unit_id").port_id.apply(set).to_dict()
lm = pd.read_csv(f"{P}/landings_monthly.csv")
lm = lm[(lm.species_scheme=="all")&lm.year.between(2019,2024)]
uval = (lm.groupby("unit_id").value_usd.sum()/6).to_dict()
ann = pd.read_csv(f"{T}/t21_annual_crosscheck.csv")
def m6(g): return g.set_index("year").value_usd.reindex(range(2019,2025)).fillna(0).mean()
for u,gname in {"WA-PACFIN-CLW":"CLW","WA-PACFIN-CWA":"CWA","WA-PACFIN-NPS":"NPS","WA-PACFIN-SPS":"SPS"}.items():
    uval[u] = m6(ann[(ann.source=="pacfin_all005")&(ann.unit==f"PacFIN group {gname}")])
foss = {"Astoria, OR":["OR-astoria"],"Winchester Bay, OR":["OR-winchester-bay"],"Port Orford, OR":["OR-port-orford"],
 "Brookings, OR":["OR-brookings"],"Ilwaco-Chinook, WA":["WA-ilwaco","WA-chinook"],"Westport, WA":["WA-westport"],
 "Willapa Bay, WA":["WA-tokeland","WA-bay-center","WA-nahcotta"],"La Push, WA":["WA-la-push"],"Neah Bay, WA":["WA-neah-bay"],
 "Port Angeles, WA":["WA-port-angeles"],"Port Townsend, WA":["WA-port-townsend"],"Anacortes-La Conner, WA":["WA-anacortes","WA-la-conner"],
 "Bellingham, WA":["WA-bellingham"],"Blaine, WA":["WA-blaine"],"Seattle, WA":["WA-seattle"],"Everett, WA":["WA-everett"]}
blocks = {}
for n,mem in foss.items():
    v = m6(ann[(ann.source=="foss")&(ann.unit==f"FOSS {n}")])
    blocks.setdefault(unit[mem[0]], []).append((set(mem), min(v, uval[unit[mem[0]]])))
# F2 (literal): a unit holds non-inventory ports if its agency member codes include
# any code not carried by one of its inventory harbors in the crosswalk table.
xw = {}
for line in open(f"{R}/docs/port_crosswalk.md", encoding="utf-8"):
    cells = [c.strip() for c in line.split("|")]
    if len(cells) > 4 and cells[1][:3] in ("CA-", "OR-", "WA-"):
        xw[cells[1]] = cells[3] + " " + cells[4]           # agency code(s) + PacFIN code columns
def codeset(s):
    if "(ports " in s: s = s.split("(ports ", 1)[1].split(")")[0]
    return {t for t in re.split(r"[^A-Za-z0-9]+", s) if re.fullmatch(r"\d{3}|[A-Z]{2,3}", t)}
tu = pd.read_csv(f"{T}/t21_units.csv", dtype=str).fillna("")
NONINV = set()
for r in tu.itertuples():
    inv = set().union(*(codeset(xw[p]) for p in r.port_ids.split(";")))
    if codeset(r.agency_codes) - inv: NONINV.add(r.unit_id)
print("non-inventory units (derived):", sorted(NONINV))
def value(cut):
    lo=hi=0.0
    for u in {unit[h] for h in cut}:
        hi += uval[u]; mem = members[u]
        if mem <= cut and u not in NONINV: lo += uval[u]
        else: lo += min(uval[u], sum(v for m,v in blocks.get(u,[]) if m <= cut))
    return lo, hi
# s4: harbors carrying the T1.3 dual-use (no in-water moorage) hoist tag
TAG = "dual-use launch/offload hoist at a harbor with no in-water moorage"
NOMOOR = set(fac[(fac.service=="hoist_crane") & fac.notes.str.lower().str.contains(TAG, regex=False)].port_id)
print("s4 no-moorage launch-hoist harbors (derived):", sorted(NOMOOR))
hv = pd.read_csv(f"{T}/index_harbor_values.csv")
drop = {"main":set(),"s1_not_found_as_available":set(),
        "s2_no_marina_only":{"CA-vallejo","CA-berkeley","CA-huntington-harbour","CA-redondo-beach"},
        "s3_no_heavily_withheld":set(hv.port_id[hv.heavily_withheld=="Y"]),
        "s4_no_moorage_hoist_no_substitute":set()}
work = {"s1_not_found_as_available":{"available","not_found"}}
SV = ["fuel","ice","hoist_crane","cold_storage"]; TH=[10,15,20,25,30,40,50,60,75,100,125,150]
rows=[]
for run,dr in drop.items():
    keep=[p for p in ports if p not in dr]; W = work.get(run,{"available"})
    own = NOMOOR if run.startswith("s4") else set()
    for s in SV:
        F=[p for p in keep if st[(p,s)] in W]
        for t in TH:
            acc = {}
            for h in keep:
                if s == "hoist_crane" and h in own:
                    acc[h] = {h} & set(F)
                else:
                    acc[h] = {f for f in F if dist[(h,f)]<=t+1e-9}
            for g in F:
                cut={h for h in keep if acc[h]=={g}}
                lo,hi = value(cut) if cut else (0,0)
                rows.append((run,t,f"{g}|{s}",round(lo),round(hi),";".join(sorted(cut))))
mine = pd.DataFrame(rows, columns=["run","threshold_nm","facility_id","lo","hi","cut"])
mine.to_csv(WORK+"/indep_all.csv", index=False)
sens = pd.read_csv(f"{T}/index_sensitivity.csv")
sens = sens[sens.stranded_low.notna()]
m = mine.merge(sens[["run","threshold_nm","facility_id","stranded_low","stranded_high"]], on=["run","threshold_nm","facility_id"], how="outer", indicator=True)
print(m._merge.value_counts().to_dict())
bad = m[(m._merge=="both")&(((m.lo-m.stranded_low).abs()>1)|((m.hi-m.stranded_high).abs()>1))]
summ = {"compared": int((m._merge=="both").sum()), "mismatches": int(len(bad)),
        "only_index": int((m._merge=="right_only").sum()), "only_indep": int((m._merge=="left_only").sum()),
        "noninventory_units": sorted(NONINV), "s4_harbors": sorted(NOMOOR),
        "rows_by_run": mine.groupby("run").size().to_dict()}
json.dump(summ, open(WORK+"/indep_summary.json","w"), indent=1)
print("rows compared:", summ["compared"], "mismatches:", summ["mismatches"],
      "only in index:", summ["only_index"], "only in recompute:", summ["only_indep"])
print(bad.head(10).to_string())
sys.exit(0 if summ["mismatches"] == 0 and summ["only_index"] == 0 and summ["only_indep"] == 0 else 1)
