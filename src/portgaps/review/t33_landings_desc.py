import sys, pandas as pd, numpy as np
import os
WORK = os.environ.get("T33_WORK", "/tmp/t33"); os.makedirs(WORK, exist_ok=True)
lm = pd.read_csv(sys.argv[1] + "/data/processed/landings_monthly.csv")
lm["ym"] = lm.year * 100 + lm.month
def months(a, b):
    y, m = a; out = []
    while (y, m) <= b:
        out.append(y * 100 + m); m += 1
        if m > 12: y, m = y + 1, 1
    return out
def shift(ms, k): return [(x // 100 - k) * 100 + x % 100 for x in ms]
CASES = [
 ("E1 Crescent City ice", "event", "CA-crescent-city", "all", (2024,10), (2025,8)),
 ("E1 Crescent City ice", "backup (Brookings; ODFW Gold Beach-Brookings table to 2024-12, Bandon-Brookings table 2025)", ["OR-ODFW-gold-beach-brookings","OR-ODFW-bandon-brookings-2025"], "all", (2024,10), (2025,8)),
 ("E2 Charleston ice", "event", "OR-charleston", "all", (2019,12), (2020,9)),
 ("E2 Charleston ice", "backup (Winchester Bay; ODFW Waldport-Yachats-Florence-Winchester Bay table)", "OR-ODFW-waldport-winchester-bay", "all", (2019,12), (2020,9)),
 ("E3 Ilwaco Landing", "event (PacFIN CLW group, Dungeness crab only, group-level)", "WA-PACFIN-CLW", "Dungeness crab", (2024,1), (2024,12)),
 ("E3 Ilwaco Landing", "backup (Astoria; ODFW Astoria table, all species)", "OR-ODFW-astoria", "all", (2024,1), (2024,12)),
 ("E4 Point Arena hoist", "event (Oct 18-Dec 2025 only; 2026 not released)", "CA-point-arena", "all", (2025,10), (2025,12)),
 ("E4 Point Arena hoist", "backup (Noyo Harbor)", "CA-noyo-harbor", "all", (2025,10), (2025,12)),
]
rows = []
for ev, role, unit, sch, a, b in CASES:
    units = unit if isinstance(unit, list) else [unit]
    g = lm[lm.unit_id.isin(units) & (lm.species_scheme == sch)]
    dur = months(a, b)
    def stat(ms):
        x = g[g.ym.isin(ms)]
        pub = x.value_usd.notna().sum()
        return x.value_usd.sum() / max(pub, 1) if pub else np.nan, pub, len(ms), int((x.withheld_flag.isin(["confidential","partial_confidential","pacfin_confidential"])).sum())
    d = stat(dur)
    pre = [stat(shift(dur, k)) for k in (1, 2, 3)]
    pre_mean = np.nanmean([p[0] for p in pre])
    rows.append({"event": ev, "role": role, "unit_id": ";".join(units), "species": sch,
                 "during_window": f"{a[0]}-{a[1]:02d} to {b[0]}-{b[1]:02d}",
                 "during_mean_monthly_usd": round(d[0]) if pd.notna(d[0]) else "",
                 "during_months_published": f"{d[1]}/{d[2]}", "during_withheld_months": d[3],
                 "prior3_same_months_mean_usd": round(pre_mean),
                 "prior3_by_year_usd": "; ".join(f"{round(p[0]):,} ({p[1]}/{p[2]})" if pd.notna(p[0]) else "na" for p in pre),
                 "during_vs_prior3": f"{d[0]/pre_mean:.2f}" if pd.notna(d[0]) else ""})
out = pd.DataFrame(rows); out.to_csv(WORK+"/landings_desc.csv", index=False); out.to_csv(sys.argv[1]+"/outputs/tables/t33_landings_descriptive.csv", index=False)
pd.set_option("display.width", 300, "display.max_colwidth", 60); print(out.to_string())
# Crescent City monthly detail
cc = lm[(lm.unit_id=="CA-crescent-city")&(lm.species_scheme=="all")&(lm.ym>=202401)][["ym","value_usd","withheld_flag"]]
print(cc.to_string())
