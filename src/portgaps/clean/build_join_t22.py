"""T2.2: join landings panel to harbor inventory; port-unit bridge, port-month panel, coverage tables.

Run from repo root:  python -I src/portgaps/clean/build_join_t22.py

Inputs : data/processed/{ports,facilities,landings_monthly}.csv
Outputs: data/processed/port_unit_bridge.csv, data/processed/port_month.csv,
         outputs/tables/t22_*.csv (join gaps, reconciliation, closure windows, status coverage)

Rules (decisions-log, do not change here):
- join on landings_monthly.port_ids split on ';'
- species_scheme = 'all', except WA = 'Dungeness crab'
- shared units carry the unit's values on every harbor row (shared_unit = Y); never sum them
- withheld cells stay null; flags passed through unchanged
- facility status for month M = latest facilities row with as_of_date[:7] <= M
  (string sort within a month, so a day-dated row beats a YYYY-MM row; i.e. end-of-month status);
  'no_observation' before the first row. Current status = latest row overall (data_dictionary.md).
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
P = ROOT / "data/processed"
T = ROOT / "outputs/tables"
SERVICES = ["fuel", "ice", "hoist_crane", "cold_storage"]
NOT_IN_SOURCE = "not_in_source"   # port-month after the state's source ends (no unit joined)


def ym(y, m):
    return f"{int(y):04d}-{int(m):02d}"


def month_range(a, b):
    return [str(p) for p in pd.period_range(a, b, freq="M")]


def main():
    ports = pd.read_csv(P / "ports.csv", dtype=str)
    fac = pd.read_csv(P / "facilities.csv", dtype=str)
    lm = pd.read_csv(P / "landings_monthly.csv", dtype={"port_ids": str})
    lm["ym"] = [ym(y, m) for y, m in zip(lm.year, lm.month)]

    # ---- series used in the join ----
    sel = ((lm.state != "WA") & (lm.species_scheme == "all")) | (
        (lm.state == "WA") & (lm.species_scheme == "Dungeness crab"))
    s = lm[sel].copy()
    assert not s.duplicated(["unit_id", "ym"]).any(), "unit x month not unique"

    first, last = "2016-01", s.ym.max()
    months = month_range(first, last)

    # ---- bridge ----
    u = (s.groupby(["unit_id", "unit_type", "species_scheme", "port_ids"])
           .ym.agg(valid_from="min", valid_to="max", n_months="count").reset_index())
    u["n_ports_in_unit"] = u.port_ids.str.split(";").str.len()
    for _, r in u.iterrows():   # units must be contiguous
        assert r.n_months == len(month_range(r.valid_from, r.valid_to)), r.unit_id
    bridge = u.assign(port_id=u.port_ids.str.split(";")).explode("port_id")
    bridge = bridge[["port_id", "unit_id", "unit_type", "species_scheme",
                     "valid_from", "valid_to", "n_ports_in_unit"]]
    order = {p: i for i, p in enumerate(ports.port_id)}
    bridge = bridge.sort_values(["port_id", "valid_from"], key=lambda c: c.map(order) if c.name == "port_id" else c)
    unknown = set(bridge.port_id) - set(ports.port_id)
    assert not unknown, f"port_ids not in inventory: {unknown}"
    bridge.to_csv(P / "port_unit_bridge.csv", index=False)

    # ---- port x month grid + landings ----
    grid = pd.MultiIndex.from_product([ports.port_id, months], names=["port_id", "month"]).to_frame(index=False)
    grid = grid.merge(ports[["port_id", "state"]], on="port_id")
    sx = s.assign(port_id=s.port_ids.str.split(";")).explode("port_id")
    sx = sx.merge(u[["unit_id", "n_ports_in_unit"]], on="unit_id")
    dup = sx.duplicated(["port_id", "ym"])
    assert not dup.any(), f"port mapped to >1 unit in a month: {sx[dup][['port_id','ym']].head()}"
    sx = sx.drop(columns="month").rename(columns={"ym": "month"})[["port_id", "month", "unit_id", "unit_type", "species_scheme",
                                             "n_ports_in_unit", "pounds", "value_usd", "withheld_flag"]]
    pm = grid.merge(sx, on=["port_id", "month"], how="left")
    pm["shared_unit"] = pm.n_ports_in_unit.map(lambda n: "" if pd.isna(n) else ("Y" if n > 1 else "N"))
    pm.loc[pm.unit_id.isna(), "withheld_flag"] = NOT_IN_SOURCE

    # ---- facility status by month ----
    fac = fac.sort_values(["port_id", "service", "as_of_date"])
    fac["m"] = fac.as_of_date.str[:7]
    cur = fac.groupby(["port_id", "service"]).tail(1).set_index(["port_id", "service"]).status
    for svc in SERVICES:
        f = fac[fac.service == svc]
        col = []
        lookup = {p: list(zip(g.m, g.status)) for p, g in f.groupby("port_id")}
        for p, m in zip(pm.port_id, pm.month):
            st = "no_observation"
            for rm, rs in lookup.get(p, []):   # rows sorted by as_of_date
                if rm <= m:
                    st = rs
                else:
                    break
            col.append(st)
        pm[f"status_{svc}"] = col
        pm[f"current_status_{svc}"] = [cur.get((p, svc), "no_observation") for p in pm.port_id]

    for c in ["pounds", "value_usd", "n_ports_in_unit"]:
        pm[c] = pm[c].astype("Int64")
    cols = ["port_id", "state", "month", "unit_id", "unit_type", "species_scheme", "shared_unit",
            "n_ports_in_unit", "pounds", "value_usd", "withheld_flag"] + \
           [f"status_{s_}" for s_ in SERVICES] + [f"current_status_{s_}" for s_ in SERVICES]
    pm = pm[cols]
    pm.to_csv(P / "port_month.csv", index=False)

    # ---- (a) join coverage / gaps ----
    g = pm[pm.unit_id.isna()]
    gaps = (g.groupby(["port_id", "state"]).month.agg(first_gap="min", last_gap="max", gap_months="count")
              .reset_index())
    gaps["reason"] = "state source ends before " + last + " (not yet published); no unit joined"
    gaps.to_csv(T / "t22_join_gaps.csv", index=False)
    cov = (pm.assign(joined=pm.unit_id.notna()).groupby(["port_id", "state"])
             .agg(months=("month", "count"), joined_months=("joined", "sum"),
                  first_joined=("month", lambda x: x[pm.loc[x.index, "unit_id"].notna()].min()),
                  last_joined=("month", lambda x: x[pm.loc[x.index, "unit_id"].notna()].max()),
                  units=("unit_id", lambda x: ";".join(dict.fromkeys(x.dropna()))))
             .reset_index())
    cov.to_csv(T / "t22_join_coverage.csv", index=False)

    # ---- (b) reconciliation ----
    j = pm[pm.unit_id.notna()]
    consistent = j.groupby(["unit_id", "month"]).agg(
        n=("port_id", "count"), np=("pounds", "nunique"), nv=("value_usd", "nunique"),
        nf=("withheld_flag", "nunique"), nports=("n_ports_in_unit", "first"))
    bad_dup = consistent[(consistent.np > 1) | (consistent.nv > 1) | (consistent.nf > 1)
                         | (consistent.n != consistent.nports)]
    once = j.drop_duplicates(["unit_id", "month"])[["unit_id", "month", "pounds", "value_usd", "withheld_flag"]]
    ref = s.drop(columns="month").rename(columns={"ym": "month"})[["unit_id", "month", "pounds", "value_usd", "withheld_flag"]]
    mm = ref.merge(once, on=["unit_id", "month"], how="outer", suffixes=("_lm", "_pm"), indicator=True)
    eq = lambda a, b: (a.isna() & b.isna()) | (a == b)
    mm["match"] = (mm._merge == "both") & eq(mm.pounds_lm.astype("Int64"), mm.pounds_pm) & \
        eq(mm.value_usd_lm.astype("Int64"), mm.value_usd_pm) & (mm.withheld_flag_lm == mm.withheld_flag_pm)
    rec = (mm.assign(state=mm.unit_id.str[:2]).groupby("state")
             .agg(unit_months=("match", "size"), matched=("match", "sum"),
                  pounds_landings_monthly=("pounds_lm", "sum"), pounds_port_month_once=("pounds_pm", "sum"),
                  value_landings_monthly=("value_usd_lm", "sum"), value_port_month_once=("value_usd_pm", "sum"))
             .reset_index())
    naive = j.groupby(j.state).value_usd.sum().rename("value_port_month_naive_sum_all_rows")
    rec = rec.merge(naive, left_on="state", right_index=True)
    tot = rec.drop(columns="state").sum().to_frame().T.assign(state="ALL")
    rec = pd.concat([rec, tot], ignore_index=True)
    rec["shared_unit_rows_inconsistent"] = [len(bad_dup[bad_dup.index.get_level_values(0).str[:2] == st])
                                            if st != "ALL" else len(bad_dup) for st in rec.state]
    rec.to_csv(T / "t22_reconciliation.csv", index=False)

    # ---- (c) closure windows ----
    events = [
        dict(port="CA-crescent-city", service="ice", event="Ice plant closed 2024-10-05; running by 2025-08-27",
             windows=[("before", first, "2024-09"), ("during", "2024-10", "2025-08"), ("after", "2025-09", last)]),
        dict(port="OR-charleston", service="ice", event="Ice plant fire 2019-12-20; reopened 2020-09-12",
             windows=[("before", first, "2019-11"), ("during", "2019-12", "2020-09"), ("after", "2020-10", last)]),
        dict(port="WA-ilwaco", service="hoist_crane", event="Ilwaco Landing dock/cranes burned 2024-01-22; not rebuilt",
             windows=[("before", first, "2023-12"), ("during", "2024-01", last), ("after", None, None)]),
        dict(port="OR-newport", service=None, event="Bornstein Bay Blvd processing closed by 2024-05-21 (processing only; no in-scope service)",
             windows=[("before", first, "2024-04"), ("during", "2024-05", last), ("after", None, None)]),
    ]
    dung = lm[lm.species_scheme == "Dungeness crab"].copy()
    rows = []
    for e in events:
        sub = pm[pm.port_id == e["port"]]
        for w, a, b in e["windows"]:
            if a is None:
                rows.append(dict(port_id=e["port"], event=e["event"], window=w, start="", end="",
                                 note="no reopening recorded; 'during' runs to end of panel"))
                continue
            ws = sub[(sub.month >= a) & (sub.month <= b)]
            seg = ws.assign(seg=ws.unit_id.fillna("(none)")).groupby("seg", sort=False)
            for unit, x in seg:
                fl = x.withheld_flag.value_counts()
                r = dict(port_id=e["port"], event=e["event"], window=w,
                         start=x.month.min(), end=x.month.max(), months=len(x),
                         unit_id=unit if unit != "(none)" else "",
                         level=(x.unit_type.iloc[0] if unit != "(none)" else "no data"),
                         species_scheme=(x.species_scheme.iloc[0] if unit != "(none)" else ""),
                         n_ports_in_unit=(x.n_ports_in_unit.iloc[0] if unit != "(none)" else pd.NA),
                         months_with_value=int(x.value_usd.notna().sum()),
                         withheld_months=";".join(x.month[x.withheld_flag.isin(
                             ["confidential", "pacfin_confidential"])]),
                         **{f"n_{k}": int(v) for k, v in fl.items()})
                if e["service"]:
                    r["closure_service"] = e["service"]
                    r["service_status_months_observed"] = int((x[f"status_{e['service']}"] != "no_observation").sum())
                    r["service_status_values"] = "; ".join(f"{k}:{v}" for k, v in
                                                          x[f"status_{e['service']}"].value_counts().items())
                if e["port"].startswith("OR") and unit != "(none)":
                    d = dung[(dung.unit_id == unit) & (dung.ym >= x.month.min()) & (dung.ym <= x.month.max())]
                    r["dungeness_row_blank_months"] = int(d.withheld_flag.eq("blank_assumed_zero").sum())
                    r["dungeness_row_part_blank_months"] = int(d.withheld_flag.eq("part_blank_assumed_zero").sum())
                rows.append(r)
    cw = pd.DataFrame(rows)
    flagcols = sorted(c for c in cw.columns if c.startswith("n_") and c != "n_ports_in_unit")
    cw[flagcols] = cw[flagcols].fillna(0).astype("Int64")
    cw.to_csv(T / "t22_closure_windows.csv", index=False)

    # ---- facility status coverage over time ----
    stc = []
    for svc in SERVICES:
        c = pm[f"status_{svc}"]
        stc.append(dict(service=svc, port_months=len(c), observed=int((c != "no_observation").sum()),
                        observed_share=round((c != "no_observation").mean(), 3),
                        ports_with_obs_by_2016_01=int(((pm.month == first) & (c != "no_observation")).sum()),
                        ports_with_obs_by_2024_01=int(((pm.month == "2024-01") & (c != "no_observation")).sum()),
                        ports_with_obs_by_last_month=int(((pm.month == last) & (c != "no_observation")).sum())))
    allobs = (pm[[f"status_{s_}" for s_ in SERVICES]] != "no_observation")
    stc.append(dict(service="any_of_4", port_months=len(pm), observed=int(allobs.any(axis=1).sum()),
                    observed_share=round(allobs.any(axis=1).mean(), 3)))
    stc.append(dict(service="all_4", port_months=len(pm), observed=int(allobs.all(axis=1).sum()),
                    observed_share=round(allobs.all(axis=1).mean(), 3)))
    pd.DataFrame(stc).to_csv(T / "t22_status_coverage.csv", index=False)

    print("months", first, last, len(months), "| port_month rows", len(pm),
          "| joined", int(pm.unit_id.notna().sum()), "| gaps", len(g))
    print(rec.to_string())
    print("inconsistent shared-unit groups:", len(bad_dup), "| unmatched unit-months:", int((~mm.match).sum()))


if __name__ == "__main__":
    main()
