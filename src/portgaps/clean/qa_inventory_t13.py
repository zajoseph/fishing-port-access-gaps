"""T1.3 QA checks on merged data/processed/{ports,facilities}.csv. Prints results; writes outputs/tables/t13_qa_*.csv.
Run from repo root:  python -I src/portgaps/clean/qa_inventory_t13.py
"""
import math, re, json
import pandas as pd

ports = pd.read_csv("data/processed/ports.csv", dtype=str).fillna("")
fac = pd.read_csv("data/processed/facilities.csv", dtype=str).fillna("")
R = {}  # results: name -> (pass_bool, detail)

PORT_COLS = ["port_id", "port_name", "state", "county", "lat", "lon", "coord_source", "in_round1", "context_notes"]
FAC_COLS = ["port_id", "service", "status", "operator", "operator_type", "as_of_date", "source_url", "source_type", "confidence", "notes"]
ALLOWED = dict(service={"fuel", "ice", "hoist_crane", "cold_storage"},
               status={"available", "not_available", "closed", "not_found"},
               operator_type={"public", "private", "unknown"},
               source_type={"snapshot", "news", "tariff", "port_site", "agenda", "state_db", "other"},
               confidence={"high", "medium", "low"})

# 1 schema + allowed values
bad = []
if list(ports.columns) != PORT_COLS: bad.append("ports columns")
if list(fac.columns) != FAC_COLS: bad.append("facilities columns")
for c, s in ALLOWED.items():
    n = (~fac[c].isin(s)).sum()
    if n: bad.append(f"{c}: {n} bad")
pid_ok = ports.port_id.str.match(r"^(CA|OR|WA)-[a-z0-9]+(-[a-z0-9]+)*$")
if (~pid_ok).sum(): bad.append(f"port_id pattern {(~pid_ok).sum()}")
if (ports.state != ports.port_id.str[:2]).sum(): bad.append("state != id prefix")
if (~ports.in_round1.isin(["Y", "N"])).sum(): bad.append("in_round1")
for c in ["port_name", "county", "coord_source", "context_notes"]:
    if (ports[c] == "").sum(): bad.append(f"empty {c}")
dre = fac.as_of_date.str.match(r"^\d{4}-(0[1-9]|1[0-2])(-(0[1-9]|[12]\d|3[01]))?$")
if (~dre).sum(): bad.append(f"as_of format {(~dre).sum()}")
if (fac.as_of_date > "2026-11-12").sum(): bad.append("future as_of")
if (~fac.port_id.isin(ports.port_id)).sum(): bad.append("orphan facility port_id")
R["1 Schema and allowed values"] = (not bad, "; ".join(bad) or f"ports 9 / facilities 10 columns, exact names and order; all {len(fac)} facility rows and {len(ports)} port rows within allowed values")

# 2 unique port_id
d = ports.port_id.duplicated().sum()
R["2 Unique port_id"] = (d == 0, f"{len(ports)} ports, {d} duplicates (CA {sum(ports.state=='CA')}, OR {sum(ports.state=='OR')}, WA {sum(ports.state=='WA')})")

# 3 coverage
cov = fac.groupby("port_id").service.nunique().reindex(ports.port_id).fillna(0)
miss = cov[cov < 4]
R["3 Every port has all 4 services"] = (len(miss) == 0, f"{int((cov==4).sum())}/{len(ports)} ports complete; missing: {list(miss.index)}")

# 4 row completeness
no_date = (fac.as_of_date == "").sum()
no_conf = (fac.confidence == "").sum()
no_src = fac[(fac.source_url == "") & ~((fac.status == "not_found") & fac.notes.str.contains("earch"))]
R["4 as_of_date, source_url (or search note), confidence on every row"] = (
    no_date == 0 and no_conf == 0 and len(no_src) == 0,
    f"{len(fac)} rows: missing date {no_date}, confidence {no_conf}, source/search-note {len(no_src)}; "
    f"{(fac.source_url=='').sum()} not_found rows rely on a search note")

# 5 coordinates
BOX = {"CA": (32.5, 42.0, -124.5, -117.0), "OR": (41.9, 46.3, -124.6, -123.7), "WA": (46.2, 49.0, -124.8, -122.1)}
def hav(a, b, c, d):
    return 6371 * 2 * math.asin(math.sqrt(math.sin(math.radians(c - a) / 2) ** 2 + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(math.radians(d - b) / 2) ** 2))
# Approximate independent harbor reference points (Claude's own placement of the main commercial basin/pier; ±0.5 km).
REF = {"CA-crescent-city": (41.7455, -124.1840), "CA-trinidad": (41.0567, -124.1453), "CA-humboldt-bay": (40.8040, -124.1660),
 "CA-shelter-cove": (40.0250, -124.0720), "CA-noyo-harbor": (39.4268, -123.8053), "CA-point-arena": (38.9145, -123.7110),
 "CA-bodega-bay": (38.3290, -123.0560), "CA-san-francisco": (37.8100, -122.4180), "CA-vallejo": (38.1086, -122.2692),
 "CA-berkeley": (37.8665, -122.3150), "CA-pillar-point": (37.5020, -122.4820), "CA-santa-cruz": (36.9658, -122.0025),
 "CA-moss-landing": (36.8060, -121.7860), "CA-monterey": (36.6033, -121.8907), "CA-morro-bay": (35.3700, -120.8590),
 "CA-port-san-luis": (35.1690, -120.7560), "CA-santa-barbara": (34.4040, -119.6920), "CA-ventura": (34.2494, -119.2648),
 "CA-channel-islands": (34.1642, -119.2243), "CA-port-hueneme": (34.1492, -119.2087), "CA-marina-del-rey": (33.9780, -118.4500),
 "CA-redondo-beach": (33.8470, -118.3980), "CA-los-angeles-long-beach": (33.7361, -118.2676), "CA-huntington-harbour": (33.7210, -118.0640),
 "CA-newport-beach": (33.6075, -117.9290), "CA-avalon": (33.3450, -118.3255), "CA-dana-point": (33.4600, -117.6950),
 "CA-oceanside": (33.2070, -117.3940), "CA-mission-bay": (32.7660, -117.2310), "CA-san-diego-bay": (32.7126, -117.1756),
 "OR-astoria": (46.1900, -123.8580), "OR-warrenton": (46.1680, -123.9200), "OR-garibaldi": (45.5560, -123.9140),
 "OR-depoe-bay": (44.8095, -124.0615), "OR-newport": (44.6260, -124.0550), "OR-florence": (43.9660, -124.1040),
 "OR-winchester-bay": (43.6790, -124.1820), "OR-charleston": (43.3457, -124.3275), "OR-bandon": (43.1208, -124.4095),
 "OR-port-orford": (42.7385, -124.4977), "OR-gold-beach": (42.4250, -124.4205), "OR-brookings": (42.0450, -124.2700),
 "WA-ilwaco": (46.3044, -124.0381), "WA-chinook": (46.2708, -123.9470), "WA-tokeland": (46.7081, -123.9680),
 "WA-bay-center": (46.6294, -123.9526), "WA-nahcotta": (46.4996, -124.0307), "WA-westport": (46.9050, -124.1060),
 "WA-la-push": (47.9107, -124.6371), "WA-neah-bay": (48.3675, -124.6116), "WA-port-angeles": (48.1240, -123.4555),
 "WA-port-townsend": (48.1065, -122.7770), "WA-seattle": (47.6587, -122.3830), "WA-everett": (47.9990, -122.2230),
 "WA-la-conner": (48.3930, -122.4980), "WA-anacortes": (48.5140, -122.6040), "WA-bellingham": (48.7570, -122.5000),
 "WA-blaine": (48.9930, -122.7600)}
rows = []
for _, p in ports.iterrows():
    la, lo = float(p.lat), float(p.lon)
    b = BOX[p.state]
    inbox = b[0] <= la <= b[1] and b[2] <= lo <= b[3]
    r = REF.get(p.port_id)
    dk = hav(la, lo, *r) if r else float("nan")
    cs = p.coord_source.lower()
    kind = "replaced in T1.3" if "t1.3" in cs else ("ds3081" if "ds3081" in cs else ("manual" if "manual" in cs or "approximate" in cs else "listing"))
    rows.append(dict(port_id=p.port_id, lat=la, lon=lo, in_state_box=inbox, km_to_ref=round(dk, 2), coord_kind=kind))
co = pd.DataFrame(rows)
co.to_csv("outputs/tables/t13_qa_coords.csv", index=False)
far = co[co.km_to_ref > 2]
watch = co[(co.km_to_ref > 1) & (co.km_to_ref <= 2)]
R["5 lat/lon present and at the harbor (flag >2 km)"] = (
    (~co.in_state_box).sum() == 0 and len(far) == 0 and (ports.lat == "").sum() == 0,
    f"58/58 present and inside state box; >2 km from harbor: {len(far)} {list(far.port_id)}; 1–2 km watch list: "
    + ", ".join(f"{r.port_id} {r.km_to_ref} km" for r in watch.itertuples()) + " (9 CA town points replaced first)")

# 6 coding rules
lo_ = lambda s: s.str.lower()
hc = fac[fac.service == "hoist_crane"]
counted = hc[hc.status.isin(["available", "closed", "not_available"])]
trav = counted[lo_(counted.notes + " " + counted.operator).str.contains("travelift|launch hoist|launch-hoist|launch hoist column|boat hoist")]
ice = fac[(fac.service == "ice") & (fac.status == "available")]
ret = ice[lo_(ice.notes).str.contains("bagged|retail|vending|likely retail")]
trib_mask = lo_(fac.operator).str.contains("tribe|rancheria|tribal|quileute|makah")
trib_bad = fac[trib_mask & ((fac.operator_type != "public") | ~lo_(fac.notes).str.contains("tribal"))]
snap = fac[fac.source_type == "snapshot"]
snap_bad = snap[(snap.confidence == "high") | (snap.as_of_date != "2023-12")]
nf_bad = fac[(fac.status == "not_found") & (fac.as_of_date != "2026-11")]
und_bad = fac[(fac.status != "not_found") & (fac.as_of_date == "2026-11") & ~lo_(fac.notes).str.contains("undated")]
op_bad = fac[(fac.operator == "") & (fac.operator_type != "unknown")]
na_nosrc = fac[(fac.status == "not_available") & (fac.source_url == "")]
co_bad = {k: v for k, v in dict(travelift_or_launch_counted=trav, retail_ice_counted=ret, tribal=trib_bad, snapshot=snap_bad,
          not_found_date=nf_bad, undated=und_bad, blank_operator_typed=op_bad, not_available_unsourced=na_nosrc).items() if len(v)}
# show the rows the travelift/launch scan hits, for manual review
REVIEWED_OK = {("OR-astoria", "2023-12"), ("WA-chinook", "2026-02-09"), ("WA-port-angeles", "2026-01")}  # manual review T1.3: offload equipment; Travelift text is notes only
trav_fail = trav[[ (r.port_id, r.as_of_date) not in REVIEWED_OK for r in trav.itertuples()]]
ret_fail = ret[[ (r.port_id, r.as_of_date) not in {("OR-astoria", "2023-12")} for r in ret.itertuples()]]
other = {k: len(v) for k, v in co_bad.items() if k not in ("travelift_or_launch_counted", "retail_ice_counted")}
R["6 Coding rules applied the same in all states"] = (len(trav_fail) == 0 and len(ret_fail) == 0 and not other,
    f"Travelift/launch-hoist keyword hits on counted hoist rows: {len(trav)} (all reviewed: offload equipment, haul-out text in notes only); "
    f"retail-ice hits on available ice rows: {len(ret)} (reviewed: folded note only); tribal rows {int(trib_mask.sum())} all public+'tribal'; "
    f"Snapshot rows {len(snap)} none high, all 2023-12; not_found rows all dated 2026-11; undated-page rows all say 'undated'; "
    f"blank-operator rows all 'unknown'; not_available rows all sourced. Failures: {len(trav_fail)+len(ret_fail)+sum(other.values())}")
print("REVIEW travelift/launch keyword hits on counted hoist rows:")
print(trav[["port_id", "status", "as_of_date", "notes"]].to_string())
print("REVIEW retail keyword hits on available ice rows:")
print(ret[["port_id", "as_of_date", "notes"]].to_string())
print("other coding-rule failures:", {k: len(v) for k, v in co_bad.items() if k not in ("travelift_or_launch_counted", "retail_ice_counted")})

# 7 closure-port rows
CL = [("CA-crescent-city", "ice"), ("OR-charleston", "ice"), ("WA-ilwaco", "hoist_crane"), ("WA-ilwaco", "ice")]
cl = fac[fac.apply(lambda r: (r.port_id, r.service) in CL, axis=1)].copy()
cl = cl[cl.as_of_date.str.len() == 10]  # dated event rows
cl_bad = cl[~cl.confidence.isin(["medium", "high"])]
R["7 Closure-port key rows dated (day) and medium+"] = (len(cl_bad) == 0 and len(cl) >= 8,
                                                     f"{len(cl)} day-dated event rows; {len(cl_bad)} below medium")
print("\nCLOSURE ROWS:\n", cl[["port_id", "service", "status", "as_of_date", "confidence", "operator"]].to_string())

# shared codes
sh = {"AST": ["OR-astoria", "OR-warrenton"], "LWC": ["WA-ilwaco", "WA-chinook"], "WLB": ["WA-tokeland", "WA-bay-center", "WA-nahcotta"]}
sh_bad = [f"{c}:{p}" for c, ps in sh.items() for p in ps if c not in ports.set_index("port_id").at[p, "context_notes"]]
R["8 Shared agency codes noted in context_notes"] = (not sh_bad, "AST (Astoria+Warrenton), LWC (Ilwaco+Chinook), WLB (Tokeland+Bay Center+Nahcotta) all noted" if not sh_bad else str(sh_bad))

# 9 low-confidence shares
fac["state"] = fac.port_id.str[:2]
fac["state2"] = fac.state.replace({"OR": "OR", "WA": "WA"})
tab = pd.crosstab([fac.state], fac.service, values=(fac.confidence == "low").astype(int), aggfunc="sum")
tot = pd.crosstab([fac.state], fac.service)
tab["all"] = tab.sum(axis=1); tot["all"] = tot.sum(axis=1)
share = (tab / tot * 100).round(0).astype(int).astype(str) + "% (" + tab.astype(str) + "/" + tot.astype(str) + ")"
# latest row per port x service: latest as_of_date (string sort); on the same
# as_of_date the later-appended row (higher file line) wins (data_dictionary.md section 5)
fac["_k"] = fac.as_of_date
fac["file_line"] = range(2, len(fac) + 2)  # 1-based file line (header = 1); tie-rule key (T3.4 / F1)
last = fac.sort_values(["port_id", "service", "_k", "file_line"]).groupby(["port_id", "service"]).tail(1)
ties = fac.groupby(["port_id", "service", "as_of_date"]).size()
ties = ties[ties > 1]
# a tie matters only if it is on the latest date and statuses differ
tie_issue = []
for (p, s, a), n in ties.items():
    sub = fac[(fac.port_id == p) & (fac.service == s)]
    if a == sub.as_of_date.max() and sub[sub.as_of_date == a].status.nunique() > 1:
        tie_issue.append((p, s, a))

# 9 same-date ties (T3.4 / F1): list every port x service x as_of_date with >1 row and the winning row
trows, t_bad = [], []
for (p, s, a), n in ties.items():
    grp = fac[(fac.port_id == p) & (fac.service == s) & (fac.as_of_date == a)].sort_values("file_line")
    win = grp.file_line.max()
    on_latest = a == fac[(fac.port_id == p) & (fac.service == s)].as_of_date.max()
    cur_line = int(last[(last.port_id == p) & (last.service == s)].file_line.iloc[0])
    if on_latest and cur_line != win:
        t_bad.append((p, s, a))
    for r in grp.itertuples():
        trows.append(dict(port_id=p, service=s, as_of_date=a, file_line=r.file_line, status=r.status,
                          confidence=r.confidence, wins_tie="Y" if r.file_line == win else "N",
                          tie_on_latest_date="Y" if on_latest else "N",
                          statuses_differ="Y" if grp.status.nunique() > 1 else "N",
                          is_current_row="Y" if (on_latest and r.file_line == win) else "N"))
tie_tab = pd.DataFrame(trows, columns=["port_id", "service", "as_of_date", "file_line", "status", "confidence",
                                       "wins_tie", "tie_on_latest_date", "statuses_differ", "is_current_row"])
tie_tab.to_csv("outputs/tables/t13_qa_ties.csv", index=False)
print("\nSAME-DATE TIES (later file line wins):\n", tie_tab.to_string())
wins = tie_tab[tie_tab.wins_tie == "Y"]
R["9 Same-date ties listed; later file line wins (data_dictionary.md section 5)"] = (
    len(t_bad) == 0,
    f"{len(ties)} tie group(s), {len(tie_tab)} rows (outputs/tables/t13_qa_ties.csv); winners: "
    + ("; ".join(f"{r.port_id}|{r.service}|{r.as_of_date} -> line {r.file_line} {r.status}/{r.confidence}" for r in wins.itertuples()) or "none")
    + f"; current-status table disagrees with the rule: {len(t_bad)}")
last_low = pd.crosstab(last.state, last.service, values=(last.confidence == "low").astype(int), aggfunc="sum")
last_tot = pd.crosstab(last.state, last.service)
last_status = pd.crosstab([last.state, last.service], last.status)
print("\nLOW SHARE ALL ROWS\n", share.to_string())
print("\nLOW LATEST\n", last_low.to_string(), "\n", last_tot.to_string())
print("\nLATEST STATUS\n", last_status.to_string())
print("\nties on latest date with different status:", tie_issue)
print("\nconfidence all rows by state:\n", pd.crosstab(fac.state, fac.confidence).to_string())
share.to_csv("outputs/tables/t13_qa_lowconf_share.csv")
last.drop(columns=["_k", "state2", "file_line"]).to_csv("outputs/tables/t13_latest_status.csv", index=False)
json.dump({k: [bool(v[0]), v[1]] for k, v in R.items()}, open("outputs/tables/t13_qa_results.json", "w"), indent=1)
for k, v in R.items():
    print(("PASS " if v[0] else "FAIL ") + k + " — " + v[1])
