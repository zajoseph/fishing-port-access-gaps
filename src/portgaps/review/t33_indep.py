"""T3.3 independent recompute of the failure index (imports nothing from portgaps). Usage: python3 -I t33_indep.py <repo_root>"""
import sys, itertools
import pandas as pd, numpy as np
import os
WORK = os.environ.get("T33_WORK", "/tmp/t33"); os.makedirs(WORK, exist_ok=True)
R = sys.argv[1]
P = f"{R}/data/processed"; T = f"{R}/outputs/tables"
fac = pd.read_csv(f"{P}/facilities.csv", dtype=str)
# same-date ties per port x service?
dd = fac.groupby(["port_id","service","as_of_date"]).status.nunique()
print("same-date conflicting status:", dd[dd>1].to_dict())
cur = fac.sort_values("as_of_date", kind="stable").groupby(["port_id","service"]).tail(1)
st = {(r.port_id, r.service): r.status for r in cur.itertuples()}
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
NONINV = {"OR-ODFW-waldport-winchester-bay","WA-PACFIN-CLW","WA-PACFIN-CWA","WA-PACFIN-NPS","WA-PACFIN-SPS"}
def value(cut, strict_noninv=False):
    lo=hi=0.0
    for u in {unit[h] for h in cut}:
        hi += uval[u]; mem = members[u]
        noninv = u in NONINV or (strict_noninv and u in ("OR-ODFW-gearhart-garibaldi","OR-ODFW-netarts-depoe-bay"))
        if mem <= cut and not noninv: lo += uval[u]
        else: lo += min(uval[u], sum(v for m,v in blocks.get(u,[]) if m <= cut))
    return lo, hi
hv = pd.read_csv(f"{T}/index_harbor_values.csv")
drop = {"main":set(),"s1_not_found_as_available":set(),
        "s2_no_marina_only":{"CA-vallejo","CA-berkeley","CA-huntington-harbour","CA-redondo-beach"},
        "s3_no_heavily_withheld":set(hv.port_id[hv.heavily_withheld=="Y"])}
work = {"s1_not_found_as_available":{"available","not_found"}}
SV = ["fuel","ice","hoist_crane","cold_storage"]; TH=[10,15,20,25,30,40,50,60,75,100,125,150]
rows=[]
for run,dr in drop.items():
    keep=[p for p in ports if p not in dr]; W = work.get(run,{"available"})
    for s in SV:
        F=[p for p in keep if st[(p,s)] in W]
        for t in TH:
            acc = {h:{f for f in F if dist[(h,f)]<=t+1e-9} for h in keep}
            for g in F:
                cut={h for h in keep if acc[h]=={g}}
                lo,hi = value(cut) if cut else (0,0)
                lo2,_ = value(cut, True) if cut else (0,0)
                rows.append((run,t,f"{g}|{s}",round(lo),round(hi),round(lo2),";".join(sorted(cut))))
mine = pd.DataFrame(rows, columns=["run","threshold_nm","facility_id","lo","hi","lo_strict","cut"])
mine.to_csv(WORK+"/indep_all.csv", index=False)
sens = pd.read_csv(f"{T}/index_sensitivity.csv")
sens = sens[sens.stranded_low.notna()]
m = mine.merge(sens[["run","threshold_nm","facility_id","stranded_low","stranded_high"]], on=["run","threshold_nm","facility_id"], how="outer", indicator=True)
print(m._merge.value_counts().to_dict())
bad = m[(m._merge=="both")&(((m.lo-m.stranded_low).abs()>1)|((m.hi-m.stranded_high).abs()>1))]
print("rows compared:", (m._merge=="both").sum(), "mismatches:", len(bad)); print(bad.head(10).to_string())
print("rows where strict non-inventory rule changes lower:", (mine.lo!=mine.lo_strict).sum())
