"""T4.2 Charleston ice-plant fire event study (closed 2019-12-20, reopened
2020-09-12): main estimates, shift test to the Winchester Bay unit, robustness,
placebos, donors, figures.

Run from the repo root:  python -I src/portgaps/eventstudy/run_charleston.py
Writes outputs/tables/t42_{estimates,robustness,placebos,donors}.csv and
outputs/figures/t42_*.png. Deterministic. Reuses eventstudy/methods.py; the
T4.1 entry point (run.py) and its config are untouched.
"""
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "portgaps.eventstudy"

import numpy as np
import pandas as pd

from portgaps.eventstudy import config_charleston as K, data as D, methods as M

CH, WB, CB = K.TREATED, K.RECEIVER, K.COMBINED
MONTHS = [m for m in D.MONTHS if K.PANEL_START <= m <= K.PANEL_END]
FIT = dict(pre_start=K.PANEL_START, data_end=K.PANEL_END)
DID = dict(pre_years=K.DID_PRE_YEARS, event_year=K.DID_EVENT_YEAR,
           m_start=K.DID_M_START, m_end=K.DID_M_END)
W = K.WINDOWS
W_MAIN = {"during": K.DURING, "after": K.AFTER}


# ---------------------------------------------------------------------------
# Series and donors
# ---------------------------------------------------------------------------
def ser(unit, measure="value_usd", scheme="all", blanks_missing=False):
    if unit == CB:
        a = ser(CH, measure, scheme, blanks_missing)
        b = ser(WB, measure, scheme, blanks_missing)
        return a + b
    return D.unit_series(unit, measure, scheme, blanks_missing)[0].reindex(MONTHS)


def flags(unit, scheme="all"):
    return D.unit_series(unit, scheme=scheme)[1].reindex(MONTHS)


def series_dict(units, measure="value_usd", scheme="all", blanks_missing=False):
    return {u: ser(u, measure, scheme, blanks_missing) for u in units}


def charted_nm_to_treated():
    d = pd.read_csv(K.PROC / "distance_matrix.csv")
    d = d[d.from_port_id == "OR-charleston"].set_index("to_port_id")
    return (d.sea_nm * 1.06).to_dict()


def unit_harbors():
    b = pd.read_csv(K.PROC / "port_unit_bridge.csv")
    b = b[(b.valid_from <= "2024-12") & (b.valid_to >= "2016-01")]
    return b.groupby("unit_id").port_id.apply(list).to_dict()


def build_donors(log):
    """Main OR pool, northern-CA check pool and crab pools, with every exclusion
    reason logged (t42_donors.csv)."""
    nm = charted_nm_to_treated()
    harbors = unit_harbors()
    or_pool = []
    for u in K.OR_UNITS:
        hs = harbors.get(u, [])
        dist = {h: round(nm[h], 1) for h in hs if h in nm}
        near = min(dist.values()) if dist else np.nan
        reason = ""
        if u == CH:
            reason = "treated unit"
        elif u == WB:
            reason = "receiver: documented backup Winchester Bay (23.4 nm); used as the shift-test unit"
        elif near < K.RECEIVER_RADIUS_NM:
            close = [f"{h} {v} nm" for h, v in dist.items() if v < K.RECEIVER_RADIUS_NM]
            reason = f"possible receiver: harbor within {K.RECEIVER_RADIUS_NM:.0f} nm ({'; '.join(close)})"
        else:
            v = ser(u)
            if v.isna().any():
                reason = f"null months in 2016-01..2024-12: {int(v.isna().sum())}"
        if not reason:
            or_pool.append(u)
        log.append({"pool": "main_OR", "scheme": "all", "unit_id": u,
                    "inventory_harbors_nm": "; ".join(f"{h} {v}" for h, v in sorted(dist.items(), key=lambda x: x[1])),
                    "nearest_nm": near, "excluded_reason": reason, "used": not reason})
    ca_pool = []
    for u in K.CA_ZONE12:
        v = ser(u)
        pre = v[v.index <= K.PRE_END]
        win = v[v.index > K.PRE_END]
        reason = ""
        if u in K.CA_OWN_EVENT:
            reason = K.CA_OWN_EVENT[u]
        elif pre.isna().mean() >= K.HEAVY_NULL_SHARE:
            reason = f"heavily withheld ({pre.isna().mean():.0%} of pre months null)"
        elif win.isna().any():
            reason = f"null month(s) in 2019-12..2024-12: {list(win[win.isna()].index)}"
        if not reason:
            ca_pool.append(u)
        fl = flags(u)
        log.append({"pool": "check_northern_CA", "scheme": "all", "unit_id": u,
                    "inventory_harbors_nm": f"{u} {nm.get(u, np.nan):.1f}",
                    "nearest_nm": nm.get(u, np.nan), "excluded_reason": reason, "used": not reason,
                    "notes": ("partial_confidential months (lower bound): "
                              f"{int((fl == 'partial_confidential').sum())}" if (fl == "partial_confidential").any() else "")})

    def crab_screen(units, pool_name):
        out = []
        for u in units:
            c = ser(u, scheme="crab")
            annual = c[c.index <= K.PRE_END].mean() * 12
            reason = ""
            if not np.isfinite(annual) or annual < K.CRAB_DONOR_MIN_ANNUAL_USD:
                reason = f"crab screen: mean annual pre crab ${annual:,.0f} < $100k"
            elif c.isna().any():
                reason = f"null crab month(s): {list(c[c.isna()].index)}"
            if not reason:
                out.append(u)
            log.append({"pool": pool_name, "scheme": "crab", "unit_id": u, "nearest_nm": np.nan,
                        "excluded_reason": reason, "used": not reason,
                        "notes": f"pre mean annual crab ${annual:,.0f}"})
        return out

    or_crab = crab_screen(or_pool, "main_OR")
    ca_crab = crab_screen(ca_pool, "check_northern_CA")
    return or_pool, ca_pool, or_crab, ca_crab


# ---------------------------------------------------------------------------
# Rows
# ---------------------------------------------------------------------------
def fit(treated, S, donors, windows=W, **kw):
    return M.sc_fit(treated, pd.DataFrame({d: S[d] for d in donors}), K.PRE_END, windows,
                    **{**FIT, **kw})


def sc_rows(est_id, label, outcome, treated, S, donors, windows=W, p_space=None, notes="", **kw):
    r = fit(treated, S, donors, windows, **kw)
    w = r["weights"]
    top = ";".join(f"{k}:{v:.2f}" for k, v in w[w > 0.01].sort_values(ascending=False).items())
    rows = []
    for win, (a, b) in windows.items():
        row = {"estimate_id": est_id, "label": label, "outcome": outcome, "method": "synthetic_control",
               "window": win, "period": f"{a}-{b}",
               "observed": r[f"{win}_obs"], "counterfactual": r[f"{win}_cf"], "gap": r[f"{win}_gap"],
               "pct_change": r[f"{win}_pct"], "n_months": r[f"{win}_n"],
               "n_months_missing": r[f"{win}_n_missing"], "pre_rmspe_scaled": r["pre_rmspe"],
               "post_pre_rmspe_ratio": r[f"{win}_ratio"], "n_fit_months": r["n_fit_months"],
               "n_donors": len(donors), "weights_gt_0.01": top, "notes": notes}
        if p_space is not None and win in p_space:
            row.update(p_space[win])
        rows.append(row)
    return rows, r


def space_inference(S, treated, donors, windows, tag, outcome, plc, **kw):
    ps = M.placebo_in_space(S, treated, donors, K.PRE_END, windows, **{**FIT, **kw})
    t = ps[ps.is_treated].iloc[0]
    res = {}
    for w in windows:
        res[w] = {"p_space_ratio": M.perm_p(t[f"{w}_ratio"], ps[f"{w}_ratio"], two_sided=False),
                  "p_space_pct": M.perm_p(t[f"{w}_pct"], ps[f"{w}_pct"]),
                  "n_placebo_units": len(ps)}
        for _, x in ps.iterrows():
            plc.append({"placebo_type": "space", "analysis": tag, "outcome": outcome,
                        "unit_or_date": x.unit_id, "is_actual": bool(x.is_treated), "window": w,
                        "pct_gap": x[f"{w}_pct"], "post_pre_rmspe_ratio": x[f"{w}_ratio"],
                        "pre_rmspe_scaled": x.pre_rmspe})
    return res, ps


def time_inference_sc(treated, S, donors, actual_pct, tag, outcome, plc):
    """Fake Dec->Sep events: pre-period (main p) and after-period (extra p,
    fitted without the closure months; assumes no lasting effect)."""
    Y0 = pd.DataFrame({d: S[d] for d in donors})
    kw = dict(m_start=K.DID_M_START, m_end=K.DID_M_END)
    tp = M.placebo_in_time_sc(treated, Y0, K.SC_PLACEBO_YEARS_PRE, **kw)
    tq = M.placebo_in_time_sc(treated, Y0, K.PLACEBO_YEARS_POST, exclude_months=K.CLOSURE_MONTHS, **kw)
    tp["timing"], tq["timing"] = "pre", "post (closure months excluded from fit)"
    allp = pd.concat([tp, tq], ignore_index=True)
    for _, x in allp.iterrows():
        plc.append({"placebo_type": "time", "analysis": tag, "outcome": outcome,
                    "unit_or_date": x.fake_event, "timing": x.timing, "is_actual": False,
                    "window": "during", "pct_gap": x.during_pct,
                    "post_pre_rmspe_ratio": x.during_ratio, "pre_rmspe_scaled": x.pre_rmspe})
    p_pre = M.perm_p(actual_pct, pd.concat([tp.during_pct, pd.Series([actual_pct])]))
    p_all = M.perm_p(actual_pct, pd.concat([allp.during_pct, pd.Series([actual_pct])]))
    return {"p_time": p_pre, "p_time_incl_post": p_all,
            "placebo_time_pct_range": f"{tp.during_pct.min():+.0%} to {tp.during_pct.max():+.0%}",
            "placebo_time_post_pct_range": f"{tq.during_pct.min():+.0%} to {tq.during_pct.max():+.0%}"}, allp


def did_post_placebos(t, k, r, m_start=K.DID_M_START, m_end=K.DID_M_END, drop_months=()):
    """Extra placebos: after-period windows against the pre-window baseline."""
    T, Kk, _ = M.paired_window_totals(t, k, K.PLACEBO_YEARS_POST, m_start, m_end, drop_months)
    base = r["ratios"][list(K.DID_PRE_YEARS)].dropna().mean()
    return pd.Series({y: np.log(T[y] / Kk[y]) - base for y in K.PLACEBO_YEARS_POST})


def did_row(est_id, label, outcome, t, k, control, window="during", notes="", post_placebos=True,
            plc=None, tag=None, **kw):
    kw = {**DID, **kw}
    r = M.window_did(t, k, **kw)
    row = {"estimate_id": est_id, "label": label, "outcome": outcome, "method": "window_DiD",
           "window": window, "control": control, "observed": r["obs"], "counterfactual": r["cf"],
           "gap": r["gap"], "pct_change": r["effect_pct"], "effect_log": r["effect_log"],
           "pre_sd_log": r["pre_sd_log"], "n_pre_windows": r["n_pre_windows"], "p_time": r["p_time"],
           "placebo_time_pct_range": (f"{np.exp(r['placebos'].min()) - 1:+.0%} to {np.exp(r['placebos'].max()) - 1:+.0%}"
                                      if len(r["placebos"]) else ""),
           "placebo_windows": "; ".join(f"{y}:{np.exp(v) - 1:+.0%}" for y, v in r["placebos"].items()),
           "months_dropped_event": r["months_dropped_event"],
           "months_dropped_pre": r["months_dropped_pre"], "notes": notes}
    if post_placebos and kw.get("m_start") == K.DID_M_START and kw.get("event_year") == K.DID_EVENT_YEAR:
        pp = did_post_placebos(t, k, r, kw["m_start"], kw["m_end"], kw.get("drop_months", ()))
        allst = pd.concat([r["placebos"], pp, pd.Series({K.DID_EVENT_YEAR: r["effect_log"]})])
        row["p_time_incl_post"] = M.perm_p(r["effect_log"], allst)
        row["placebo_time_post_pct_range"] = f"{np.exp(pp.min()) - 1:+.0%} to {np.exp(pp.max()) - 1:+.0%}"
        r["post_placebos"] = pp
        if plc is not None:
            for y, v in list(r["placebos"].items()) + list(pp.items()):
                plc.append({"placebo_type": "time", "analysis": tag, "outcome": outcome,
                            "unit_or_date": f"{y}-12", "timing": "pre" if y in r["placebos"].index else "post",
                            "is_actual": False, "window": "during", "effect_log": v, "pct_gap": np.exp(v) - 1})
    return row, r


def after_did_rows(est_id, label, outcome, t, k, control, notes=""):
    """After-period DiD: each Oct->Sep year 2020-21..2023-24 against 2016-17..2018-19,
    plus the later years pooled (mean log effect of 2021-22..2023-24)."""
    rows, effs = [], {}
    for y in K.AFTER_DID_YEARS:
        row, r = did_row(est_id, label, outcome, t, k, control,
                         window="after_y1" if y == 2020 else f"after_{y}-{(y + 1) % 100:02d}",
                         notes=notes, post_placebos=False, pre_years=K.AFTER_DID_PRE_YEARS,
                         event_year=y, m_start=10, m_end=9)
        rows.append(row)
        effs[y] = r["effect_log"]
    later = np.mean([effs[y] for y in K.AFTER_DID_YEARS[1:]])
    rows.append({"estimate_id": est_id, "label": label, "outcome": outcome, "method": "window_DiD",
                 "window": "after_later", "control": control, "pct_change": float(np.exp(later) - 1),
                 "effect_log": float(later), "n_pre_windows": len(K.AFTER_DID_PRE_YEARS),
                 "notes": "mean log effect of the Oct-Sep years 2021-22, 2022-23, 2023-24 (Oct-Dec 2024 not in a full year)"})
    return rows


# ---------------------------------------------------------------------------
def main():
    K.TABLES.mkdir(parents=True, exist_ok=True)
    K.FIGS.mkdir(parents=True, exist_ok=True)
    est, rob, plc, dlog = [], [], [], []
    pool, ca_pool, cpool, ca_cpool = build_donors(dlog)
    for u in [CH] + pool + [WB]:
        assert not ser(u).isna().any(), u  # all-species ODFW series are complete

    units = [CH, WB, CB] + pool + ca_pool
    S = series_dict(units)
    Sp = series_dict(units, "pounds")
    Sc = series_dict([CH, WB, CB] + cpool + ca_cpool, scheme="crab")
    Scp = series_dict([CH, WB, CB] + cpool, "pounds", scheme="crab")
    Sn = series_dict([CH, WB, CB] + pool, scheme="noncrab")
    Sb = series_dict([CH, WB, CB] + cpool, scheme="crab", blanks_missing=True)
    Kall = D.agg_series(pool)[0].reindex(MONTHS)
    pool_desc = f"sum of main OR donor pool ({len(pool)} units)"

    # ---------------- E1: Charleston all-species value, SC -----------------
    inf1, ps1 = space_inference(S, CH, pool, W, "E1_charleston_value", "value_all", plc)
    rows, r1 = sc_rows("E1", "Charleston all-species value", "value_all", S[CH], S, pool, W, inf1)
    t1, tp1 = time_inference_sc(S[CH], S, pool, r1["during_pct"], "E1_charleston_value", "value_all", plc)
    rows[0].update(t1)
    est += rows

    # ---------------- E2: Charleston all-species value, DiD -----------------
    row, r2 = did_row("E2", "Charleston all-species value", "value_all", S[CH], Kall, pool_desc,
                      plc=plc, tag="E2_charleston_value_did")
    est.append(row)
    est += after_did_rows("E2", "Charleston all-species value", "value_all", S[CH], Kall, pool_desc)

    # ---------------- E3: Charleston all-species pounds ---------------------
    inf3, _ = space_inference(Sp, CH, pool, W_MAIN, "E3_charleston_pounds", "pounds_all", plc)
    rows, r3 = sc_rows("E3", "Charleston all-species pounds", "pounds_all", Sp[CH], Sp, pool, W, inf3,
                       notes="ODFW round weight; donor pounds dominated by Pacific whiting (Newport, Astoria)")
    t3, _ = time_inference_sc(Sp[CH], Sp, pool, r3["during_pct"], "E3_charleston_pounds", "pounds_all", plc)
    rows[0].update(t3)
    est += rows
    row, _ = did_row("E3", "Charleston all-species pounds", "pounds_all", Sp[CH],
                     D.agg_series(pool, "pounds")[0].reindex(MONTHS), pool_desc, plc=plc,
                     tag="E3_charleston_pounds_did")
    est.append(row)

    # ---------------- E4: Charleston Dungeness crab value -------------------
    crab_note = ("ODFW blanks = 0 (documented assumption); Charleston crab part-blank in all 10 closure "
                 "months (bay crab; Sep 2020 ocean crab, season closed) - see R5")
    inf4, _ = space_inference(Sc, CH, cpool, W_MAIN, "E4_charleston_crab", "value_crab", plc)
    rows, r4 = sc_rows("E4", "Charleston Dungeness crab value", "value_crab", Sc[CH], Sc, cpool, W, inf4,
                       notes=crab_note)
    t4, _ = time_inference_sc(Sc[CH], Sc, cpool, r4["during_pct"], "E4_charleston_crab", "value_crab", plc)
    rows[0].update(t4)
    est += rows
    Kc = D.agg_series(cpool, scheme="crab")[0].reindex(MONTHS)
    row, r4d = did_row("E4", "Charleston Dungeness crab value", "value_crab", Sc[CH], Kc,
                       f"sum of OR crab donor pool ({len(cpool)} units)", notes=crab_note,
                       plc=plc, tag="E4_charleston_crab_did")
    est.append(row)
    est += after_did_rows("E4", "Charleston Dungeness crab value", "value_crab", Sc[CH], Kc,
                          f"sum of OR crab donor pool ({len(cpool)} units)")

    # ---------------- E5: shift test, Winchester Bay unit -------------------
    wb_note = "Waldport-Winchester Bay ODFW table: also Florence and non-inventory ports, so it dilutes Winchester Bay"
    inf5, ps5 = space_inference(S, WB, pool, W, "E5_wb_unit_value", "value_all", plc)
    rows, r5 = sc_rows("E5", "Shift: Waldport-Winchester Bay unit all-species value", "value_all",
                       S[WB], S, pool, W, inf5, notes=wb_note)
    t5, _ = time_inference_sc(S[WB], S, pool, r5["during_pct"], "E5_wb_unit_value", "value_all", plc)
    rows[0].update(t5)
    est += rows
    row, r5d = did_row("E5", "Shift: Waldport-Winchester Bay unit all-species value", "value_all", S[WB],
                       Kall, pool_desc, notes=wb_note, plc=plc, tag="E5_wb_unit_value_did")
    est.append(row)
    est += after_did_rows("E5", "Shift: Waldport-Winchester Bay unit all-species value", "value_all",
                          S[WB], Kall, pool_desc)

    # ---------------- E6: Charleston + Winchester Bay unit combined ---------
    inf6, ps6 = space_inference(S, CB, pool, W, "E6_combined_value", "value_all", plc)
    rows, r6 = sc_rows("E6", "Combined Charleston + Waldport-Winchester Bay unit all-species value",
                       "value_all", S[CB], S, pool, W, inf6)
    t6, _ = time_inference_sc(S[CB], S, pool, r6["during_pct"], "E6_combined_value", "value_all", plc)
    rows[0].update(t6)
    est += rows
    row, r6d = did_row("E6", "Combined Charleston + Waldport-Winchester Bay unit all-species value",
                       "value_all", S[CB], Kall, pool_desc, plc=plc, tag="E6_combined_value_did")
    est.append(row)
    est += after_did_rows("E6", "Combined Charleston + Waldport-Winchester Bay unit all-species value",
                          "value_all", S[CB], Kall, pool_desc)

    # =========================== ROBUSTNESS ==================================
    def add(rid, check, rows_or_row):
        for row in rows_or_row if isinstance(rows_or_row, list) else [rows_or_row]:
            rob.append({"robustness_id": rid, "check": check,
                        **{k: v for k, v in row.items() if k != "estimate_id"}})

    def sc(rid, check, label, t, SS, donors, windows=None, **kw):
        rows, r = sc_rows(rid, label, "", t, SS, donors, windows or {"during": K.DURING}, **kw)
        add(rid, check, rows)
        return r

    def did(rid, check, label, t, k, control, **kw):
        row, r = did_row(rid, label, "", t, k, control, **kw)
        add(rid, check, row)
        return r

    # R1 placebo dates (full lists in t42_placebos.csv)
    for lab, est_id, tinf, actual in [("E1 SC value", "E1", t1, r1["during_pct"]),
                                      ("E3 SC pounds", "E3", t3, r3["during_pct"]),
                                      ("E4 SC crab", "E4", t4, r4["during_pct"]),
                                      ("E5 SC Winchester Bay unit", "E5", t5, r5["during_pct"]),
                                      ("E6 SC combined", "E6", t6, r6["during_pct"])]:
        rob.append({"robustness_id": "R1", "check": "placebo dates", "label": lab, "method": "synthetic_control",
                    "window": "during", "pct_change": actual, "p_time": tinf["p_time"],
                    "p_time_incl_post": tinf["p_time_incl_post"],
                    "notes": f"fake Dec 2017/2018 gaps {tinf['placebo_time_pct_range']}; "
                             f"fake Dec 2021-2023 gaps {tinf['placebo_time_post_pct_range']}"})
    for lab, r in [("E2 DiD value", r2), ("E4 DiD crab", r4d), ("E5 DiD Winchester Bay unit", r5d),
                   ("E6 DiD combined", r6d)]:
        rob.append({"robustness_id": "R1", "check": "placebo dates", "label": lab, "method": "window_DiD",
                    "window": "during", "pct_change": r["effect_pct"], "p_time": r["p_time"],
                    "notes": "pre windows: " + ", ".join(f"Dec {y}:{np.exp(v) - 1:+.0%}" for y, v in r["placebos"].items())
                             + "; post windows: " + ", ".join(f"Dec {y}:{np.exp(v) - 1:+.0%}" for y, v in r["post_placebos"].items())})

    # R2 leave-one-out donors: every donor for E1 (only 5); weighted donors elsewhere
    for d in pool:
        sc("R2", "leave-one-out donor", f"E1 SC without {d}", S[CH], S, [x for x in pool if x != d])
        did("R2", "leave-one-out donor", f"E2 DiD without {d}", S[CH],
            D.agg_series([x for x in pool if x != d])[0].reindex(MONTHS), f"donor sum without {d}",
            post_placebos=False)
    for tag, rr, t, SS, dd in [("E4 crab", r4, Sc[CH], Sc, cpool), ("E5 Winchester Bay unit", r5, S[WB], S, pool),
                               ("E6 combined", r6, S[CB], S, pool)]:
        w = rr["weights"]
        for d in w[w > 0.01].index:
            sc("R2", "leave-one-out donor", f"{tag} SC without {d}", t, SS, [x for x in dd if x != d])

    # R3 value vs pounds
    sc("R3", "pounds instead of value", "E1 pounds SC [= E3]", Sp[CH], Sp, pool)
    sc("R3", "pounds instead of value", "E4 crab pounds SC", Scp[CH], Scp, cpool)
    did("R3", "pounds instead of value", "E4 crab pounds DiD", Scp[CH],
        D.agg_series(cpool, "pounds", "crab")[0].reindex(MONTHS), "OR crab donor pool pounds", post_placebos=False)
    sc("R3", "pounds instead of value", "E5 Winchester Bay unit pounds SC", Sp[WB], Sp, pool)
    sc("R3", "pounds instead of value", "E6 combined pounds SC", Sp[CB], Sp, pool)
    sc("R3", "pounds instead of value", "E6 combined crab pounds SC", Scp[CB], Scp, cpool)

    # R4 crab vs non-crab
    sc("R4", "crab vs non-crab", "Charleston crab value SC [= E4]", Sc[CH], Sc, cpool)
    sc("R4", "crab vs non-crab", "Charleston non-crab value SC", Sn[CH], Sn, pool, windows=W_MAIN,
       notes="non-crab = all minus Dungeness")
    did("R4", "crab vs non-crab", "Charleston non-crab value DiD", Sn[CH],
        D.agg_series(pool, scheme="noncrab")[0].reindex(MONTHS), "donor non-crab sum", post_placebos=False)
    sc("R4", "crab vs non-crab", "Winchester Bay unit crab value SC", Sc[WB], Sc, cpool)
    sc("R4", "crab vs non-crab", "Winchester Bay unit non-crab value SC", Sn[WB], Sn, pool)
    sc("R4", "crab vs non-crab", "Combined crab value SC", Sc[CB], Sc, cpool)
    sc("R4", "crab vs non-crab", "Combined non-crab value SC", Sn[CB], Sn, pool)

    # R5 crab with ODFW blanks as missing (T4.1 rule: fully blank -> null; part-blank kept, flagged)
    nb = {u: int((flags(u, "crab") == "blank_assumed_zero").sum()) for u in [CH, WB] + cpool}
    note5 = ("blank_assumed_zero -> null (pairwise/pre-fit deletion); part_blank kept as lower bound. "
             "Fully blank crab months: " + ", ".join(f"{u.replace('OR-ODFW-', '').replace('OR-', '')} {n}" for u, n in nb.items()))
    sc("R5", "crab with blanks as missing", "Charleston crab SC", Sb[CH], Sb, cpool, windows=W_MAIN, notes=note5)
    did("R5", "crab with blanks as missing", "Charleston crab DiD", Sb[CH],
        D.agg_series(cpool, scheme="crab", blanks_missing=True)[0].reindex(MONTHS), "OR crab donor sum",
        notes=note5, post_placebos=False)
    sc("R5", "crab with blanks as missing", "Winchester Bay unit crab SC", Sb[WB], Sb, cpool, notes=note5)
    sc("R5", "crab with blanks as missing", "Combined crab SC", Sb[CB], Sb, cpool, notes=note5)

    # R6 alternative start 2020-01 (Dec 2019 left out of the event window and of the fit)
    Walt = {"during": K.DURING_ALT_START}
    for lab, t, SS, dd in [("E1 value", S[CH], S, pool), ("E4 crab", Sc[CH], Sc, cpool),
                           ("E5 Winchester Bay unit", S[WB], S, pool), ("E6 combined", S[CB], S, pool)]:
        sc("R6", "alternative start 2020-01", f"{lab} SC Jan-Sep 2020", t, SS, dd, windows=Walt)
    did("R6", "alternative start 2020-01", "E2 DiD Jan-Sep windows", S[CH], Kall, pool_desc,
        pre_years=[2016, 2017, 2018, 2019], event_year=2020, m_start=1, m_end=9, post_placebos=False,
        notes="pre windows Jan-Sep 2016-2019 (Jan-Sep 2019 is wholly pre-closure)")
    did("R6", "alternative start 2020-01", "E5 DiD Jan-Sep windows", S[WB], Kall, pool_desc,
        pre_years=[2016, 2017, 2018, 2019], event_year=2020, m_start=1, m_end=9, post_placebos=False)

    # R7 excluding the COVID-shock months Mar-Jun 2020 from the during window
    cov = set(K.COVID_MONTHS)
    cov_all_years = {y * 100 + m for y in range(2016, 2025) for m in (3, 4, 5, 6)}
    for lab, est_id, rr in [("E1 value", "E1", r1), ("E3 pounds", "E3", r3), ("E4 crab", "E4", r4),
                            ("E5 Winchester Bay unit", "E5", r5), ("E6 combined", "E6", r6)]:
        ms = [m for m in M.months_between(*K.DURING, MONTHS) if m not in cov]
        obs, cf = rr["treated"][ms].sum(), rr["counterfactual"][ms].sum()
        rob.append({"robustness_id": "R7", "check": "exclude COVID months Mar-Jun 2020",
                    "label": f"{lab} SC, during minus Mar-Jun 2020", "method": "synthetic_control",
                    "window": "during_ex_covid", "observed": obs, "counterfactual": cf, "gap": obs - cf,
                    "pct_change": obs / cf - 1, "n_months": len(ms),
                    "notes": "same weights as the main fit; 6 months (Dec 2019-Feb 2020, Jul-Sep 2020)"})
    for lab, t, k in [("E2 value", S[CH], Kall), ("E5 Winchester Bay unit", S[WB], Kall),
                      ("E6 combined", S[CB], Kall), ("E4 crab", Sc[CH], Kc)]:
        did("R7", "exclude COVID months Mar-Jun 2020", f"{lab} DiD, Mar-Jun dropped from every window",
            t, k, "donor sum", drop_months=cov_all_years, post_placebos=False)

    # R8 after-period split: SC rows already in estimates (after_y1, after_later); repeat here
    for lab, rr in [("E1 value", r1), ("E3 pounds", r3), ("E4 crab", r4), ("E5 Winchester Bay unit", r5),
                    ("E6 combined", r6)]:
        for win in ("after_y1", "after_later"):
            rob.append({"robustness_id": "R8", "check": "after-period split", "label": f"{lab} SC",
                        "method": "synthetic_control", "window": win, "period": f"{W[win][0]}-{W[win][1]}",
                        "observed": rr[f"{win}_obs"], "counterfactual": rr[f"{win}_cf"],
                        "gap": rr[f"{win}_gap"], "pct_change": rr[f"{win}_pct"],
                        "post_pre_rmspe_ratio": rr[f"{win}_ratio"], "n_months": rr[f"{win}_n"]})
    for lab, est_id in [("E2 value DiD", "E2"), ("E4 crab DiD", "E4"), ("E5 Winchester Bay unit DiD", "E5"),
                        ("E6 combined DiD", "E6")]:
        for e in est:
            if e["estimate_id"] == est_id and e["method"] == "window_DiD" and e["window"] in ("after_y1", "after_later"):
                rob.append({"robustness_id": "R8", "check": "after-period split", "label": lab,
                            "method": "window_DiD", "window": e["window"], "pct_change": e["pct_change"],
                            "p_time": e.get("p_time", np.nan), "notes": e.get("notes", "")})

    # R9 donor pool with northern CA added (user: robustness check only)
    pool9, cpool9 = pool + ca_pool, cpool + ca_cpool
    note9 = "CDFW landing date / landed weight vs ODFW purchase date / round weight; scaled value only"
    for lab, t, SS, dd, tg in [("E1 value", CH, S, pool9, "R9_E1"), ("E4 crab", CH, Sc, cpool9, "R9_E4"),
                               ("E5 Winchester Bay unit", WB, S, pool9, "R9_E5"), ("E6 combined", CB, S, pool9, "R9_E6")]:
        inf9, _ = space_inference(SS, t, dd, {"during": K.DURING}, tg, lab, plc)
        sc("R9", "donors + northern CA", f"{lab} SC, OR + northern CA donors", SS[t], SS, dd,
           p_space=inf9, notes=note9)
    did("R9", "donors + northern CA", "E2 DiD vs OR + northern CA donor sum", S[CH],
        D.agg_series(pool9)[0].reindex(MONTHS), "OR + northern CA sum", notes=note9, post_placebos=False)

    # R11 other nearby harbor: Bandon-Port Orford unit (Bandon 17.7 nm), excluded from the
    # donor pool as a possible receiver. Not a documented backup; checked so that "did not
    # go to Winchester Bay" is not read as "went nowhere nearby".
    BP = "OR-ODFW-bandon-port-orford"
    S[BP] = ser(BP)
    S["CH+WB+BP"] = S[CB] + S[BP]
    note11 = "Bandon-Port Orford is not a documented backup; checked as the nearest other harbor (Bandon 17.7 nm)"
    for lab, t, tg in [("Bandon-Port Orford unit", BP, "R11_bandon"),
                       ("Charleston + WB unit + Bandon-Port Orford", "CH+WB+BP", "R11_ch_wb_bp")]:
        inf11, _ = space_inference(S, t, pool, W_MAIN, tg, "value_all", plc)
        sc("R11", "other nearby harbor (Bandon-Port Orford)", f"{lab} SC", S[t], S, pool, windows=W_MAIN,
           p_space=inf11, notes=note11)
        did("R11", "other nearby harbor (Bandon-Port Orford)", f"{lab} DiD", S[t], Kall, pool_desc,
            notes=note11, post_placebos=False)

    # R10 power: test inversion (log-symmetric). For a hypothetical true loss L the
    # observed log effect would be log(1-L); p = its rank among the placebos.
    def inversion(label, plac_logs, kind):
        pl = pd.Series(plac_logs).dropna()
        out = {"robustness_id": "R10", "check": "power (test inversion)", "label": label, "method": kind,
               "window": "during", "n_placebos": len(pl),
               "placebo_log_range": f"{np.exp(pl.min()) - 1:+.0%} to {np.exp(pl.max()) - 1:+.0%}",
               "smallest_loss_outside_all_placebos": float(1 - np.exp(-pl.abs().max())),
               "min_attainable_p": 1 / (len(pl) + 1)}
        for L in (0.3, 0.5, 0.75, 0.9):
            x = np.log(1 - L)
            out[f"p_if_true_loss_{int(L * 100)}"] = M.perm_p(x, pd.concat([pl, pd.Series([x])]))
        rob.append(out)

    sp = ps1[~ps1.is_treated].during_pct
    inversion("E1 SC, placebo-in-space (5 donors)", np.log1p(sp), "synthetic_control")
    tpre = tp1[tp1.timing == "pre"].during_pct
    inversion("E1 SC, placebo-in-time pre (Dec 2017, 2018)", np.log1p(tpre), "synthetic_control")
    inversion("E1 SC, placebo-in-time pre + post", np.log1p(tp1.during_pct), "synthetic_control")
    inversion("E2 DiD, pre windows (Dec 2016-2018)", r2["placebos"], "window_DiD")
    inversion("E2 DiD, pre + post windows", pd.concat([r2["placebos"], r2["post_placebos"]]), "window_DiD")
    inversion("E5 SC Winchester Bay unit, placebo-in-space", np.log1p(ps5[~ps5.is_treated].during_pct),
              "synthetic_control")
    inversion("E6 SC combined, placebo-in-space", np.log1p(ps6[~ps6.is_treated].during_pct), "synthetic_control")

    # ---------------- write tables ----------------
    E, R, P = pd.DataFrame(est), pd.DataFrame(rob), pd.DataFrame(plc)
    pre = K.OUT_PREFIX
    E.to_csv(K.TABLES / f"{pre}_estimates.csv", index=False, float_format="%.10g")
    R.to_csv(K.TABLES / f"{pre}_robustness.csv", index=False, float_format="%.10g")
    P.to_csv(K.TABLES / f"{pre}_placebos.csv", index=False, float_format="%.10g")
    pd.DataFrame(dlog).to_csv(K.TABLES / f"{pre}_donors.csv", index=False, float_format="%.10g")

    from portgaps.eventstudy import figures_charleston as F
    F.make_all(S, r1, ps1, tp1, r2, r5, r6, ps5, ps6)
    return E, R, P


if __name__ == "__main__":
    E, R, P = main()
    pd.set_option("display.width", 250)
    cols = ["estimate_id", "method", "window", "observed", "counterfactual", "pct_change",
            "p_space_ratio", "p_space_pct", "p_time", "p_time_incl_post", "weights_gt_0.01"]
    print(E[[c for c in cols if c in E]].to_string(float_format=lambda x: f"{x:,.3f}"))
    print(R[["robustness_id", "label", "window", "pct_change", "p_time"]].to_string(float_format=lambda x: f"{x:,.3f}"))
