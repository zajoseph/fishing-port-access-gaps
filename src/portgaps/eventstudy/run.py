"""T4.1 Crescent City ice-closure event study: main estimates, shift test,
robustness, placebos, figures.

Run from the repo root:  python -I -m portgaps.eventstudy.run  (with src/ on
PYTHONPATH), or  python -I src/portgaps/eventstudy/run.py
Writes outputs/tables/t41_{estimates,robustness,placebos,donors}.csv and
outputs/figures/t41_*.png. Deterministic; about 10 s.
"""
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "portgaps.eventstudy"

import numpy as np
import pandas as pd

from portgaps.eventstudy import config as C, data as D, methods as M

W = {"during": C.DURING, "after": C.AFTER}
W_ALT = {"during": C.DURING_ALT, "after": C.AFTER_ALT}
CC = C.TREATED
SO, CO = "south-OR", "central-OR"
# After-period DiD windows: Sep-Dec; pre years 2016-2023 (2024's Sep-Dec overlaps
# the closure, so it is not a pre window).
AFTER_DID = dict(pre_years=list(range(2016, 2024)), event_year=2025, m_start=9, m_end=12)


def series_dict(units, measure="value_usd", scheme="all", blanks_missing=False):
    out = {}
    for u in units:
        if u == SO:
            out[u] = D.agg_series(C.SOUTH_OR, measure, scheme, blanks_missing)[0]
        elif u == CO:
            out[u] = D.agg_series(C.CENTRAL_OR, measure, scheme, blanks_missing)[0]
        else:
            out[u] = D.unit_series(u, measure, scheme, blanks_missing)[0]
    return out


def sc_row(est_id, label, outcome, treated_series, S, donors, windows, window,
           p_space=None, notes=""):
    r = M.sc_fit(treated_series, pd.DataFrame({d: S[d] for d in donors}), C.PRE_END, windows)
    w = r["weights"]
    top = ";".join(f"{k}:{v:.2f}" for k, v in w[w > 0.01].sort_values(ascending=False).items())
    row = {
        "estimate_id": est_id, "label": label, "outcome": outcome, "method": "synthetic_control",
        "window": window, "period": f"{windows[window][0]}-{windows[window][1]}",
        "observed": r[f"{window}_obs"], "counterfactual": r[f"{window}_cf"],
        "gap": r[f"{window}_gap"], "pct_change": r[f"{window}_pct"],
        "n_months": r[f"{window}_n"], "n_months_missing": r[f"{window}_n_missing"],
        "pre_rmspe_scaled": r["pre_rmspe"], "post_pre_rmspe_ratio": r[f"{window}_ratio"],
        "n_fit_months": r["n_fit_months"], "n_donors": len(donors), "weights_gt_0.01": top,
        "notes": notes,
    }
    if p_space is not None:
        row.update(p_space)
    return row, r


def did_row(est_id, label, outcome, t, k, control_desc, window="during", notes="", **kw):
    r = M.window_did(t, k, **kw)
    return {
        "estimate_id": est_id, "label": label, "outcome": outcome, "method": "window_DiD",
        "window": window, "control": control_desc,
        "observed": r["obs"], "counterfactual": r["cf"], "gap": r["gap"],
        "pct_change": r["effect_pct"], "effect_log": r["effect_log"],
        "pre_sd_log": r["pre_sd_log"], "n_pre_windows": r["n_pre_windows"],
        "p_time": r["p_time"],
        "placebo_time_pct_range": (f"{np.exp(r['placebos'].min()) - 1:+.0%} to {np.exp(r['placebos'].max()) - 1:+.0%}"
                                   if len(r["placebos"]) else ""),
        "placebo_windows": "; ".join(f"{k}-{(k + 1) % 100:02d}:{np.exp(v) - 1:+.0%}" for k, v in r["placebos"].items()),
        "months_dropped_event": r["months_dropped_event"],
        "months_dropped_pre": r["months_dropped_pre"], "notes": notes,
    }, r


def space_inference(S, treated, donors, windows, tag, outcome, placebo_rows):
    ps = M.placebo_in_space(S, treated, donors, C.PRE_END, windows)
    res = {}
    for w in windows:
        t = ps[ps.is_treated].iloc[0]
        res[w] = {
            "p_space_ratio": M.perm_p(t[f"{w}_ratio"], ps[f"{w}_ratio"], two_sided=False),
            "p_space_pct": M.perm_p(t[f"{w}_pct"], ps[f"{w}_pct"]),
            "n_placebo_units": len(ps),
        }
    for _, x in ps.iterrows():
        for w in windows:
            placebo_rows.append({"placebo_type": "space", "analysis": tag, "outcome": outcome,
                                 "unit_or_date": x.unit_id, "is_actual": bool(x.is_treated),
                                 "window": w, "pct_gap": x[f"{w}_pct"],
                                 "post_pre_rmspe_ratio": x[f"{w}_ratio"],
                                 "pre_rmspe_scaled": x.pre_rmspe})
    return res, ps


def main():
    C.TABLES.mkdir(parents=True, exist_ok=True)
    C.FIGS.mkdir(parents=True, exist_ok=True)
    est, rob, plc, donors_log = [], [], [], []

    pool = D.donor_pool("all", donors_log)
    cpool = D.donor_pool("crab", donors_log)
    for u in pool:
        donors_log.append({"scheme": "all", "unit_id": u, "excluded_reason": ""})
    for u in cpool:
        donors_log.append({"scheme": "crab", "unit_id": u, "excluded_reason": ""})

    S = series_dict([CC] + pool + [SO, CO])
    Sc = series_dict([CC] + cpool + [SO, CO], scheme="crab")
    Sp = series_dict([CC] + pool + [SO, CO], measure="pounds")
    Sn = series_dict([CC] + pool, scheme="noncrab")

    # ---------------- E1: Crescent City, all-species value, SC ----------------
    inf, ps_main = space_inference(S, CC, pool, W, "E1_cc_all_value", "value_all", plc)
    for w in W:
        row, r_main = sc_row("E1", "Crescent City all-species value", "value_all",
                             S[CC], S, pool, W, w, inf[w])
        est.append(row)
    tp = M.placebo_in_time_sc(S[CC], pd.DataFrame({d: S[d] for d in pool}), C.SC_PLACEBO_YEARS)
    for _, x in tp.iterrows():
        plc.append({"placebo_type": "time", "analysis": "E1_cc_all_value", "outcome": "value_all",
                    "unit_or_date": x.fake_event, "is_actual": False, "window": "during",
                    "pct_gap": x.during_pct, "post_pre_rmspe_ratio": x.during_ratio,
                    "pre_rmspe_scaled": x.pre_rmspe})
    p_time_sc = M.perm_p(est[0]["pct_change"],
                         pd.concat([tp.during_pct, pd.Series([est[0]["pct_change"]])]))
    est[0]["p_time"] = p_time_sc
    est[0]["placebo_time_pct_range"] = f"{tp.during_pct.min():+.0%} to {tp.during_pct.max():+.0%}"

    # ---------------- E2: Crescent City, window DiD vs donor-pool total -------
    K = D.agg_series(pool)[0]
    row, r_did = did_row("E2", "Crescent City all-species value", "value_all", S[CC], K,
                         f"sum of main CA donor pool ({len(pool)} harbors)")
    est.append(row)
    for k, v in r_did["placebos"].items():
        plc.append({"placebo_type": "time", "analysis": "E2_cc_all_value_did", "outcome": "value_all",
                    "unit_or_date": f"{k}-10", "is_actual": False, "window": "during",
                    "effect_log": v, "pct_gap": np.exp(v) - 1})
    row, _ = did_row("E2", "Crescent City all-species value", "value_all", S[CC], K,
                     f"sum of main CA donor pool ({len(pool)} harbors)", window="after", **AFTER_DID)
    est.append(row)

    # ---------------- E3: Crescent City Dungeness crab, SC --------------------
    inf_c, _ = space_inference(Sc, CC, cpool, W, "E3_cc_crab_value", "value_crab", plc)
    for w in W:
        row, _ = sc_row("E3", "Crescent City Dungeness crab value", "value_crab",
                        Sc[CC], Sc, cpool, W, w, inf_c[w],
                        notes="crab donors: pre mean >= $100k/yr; no null crab month in window")
        est.append(row)
    Kc = D.agg_series(cpool, scheme="crab")[0]
    row, _ = did_row("E3", "Crescent City Dungeness crab value", "value_crab", Sc[CC], Kc,
                     f"sum of crab donor pool ({len(cpool)} harbors)")
    est.append(row)

    # ---------------- E4/E5: shift test South-OR vs Central-OR ----------------
    shift_did = {}
    for eid, sch, SS, lab in [("E4", "value_all", S, "all-species"), ("E5", "value_crab", Sc, "Dungeness crab")]:
        row, r = did_row(eid, f"Shift: South-OR (Bandon-Brookings) {lab} value", sch, SS[SO], SS[CO],
                         "Central-OR (Gearhart-Charleston), same agency/opener",
                         notes="ODFW blanks = 0 (documented assumption); see R7 for blanks as missing")
        est.append(row)
        shift_did[sch] = r
        for k, v in r["placebos"].items():
            plc.append({"placebo_type": "time", "analysis": f"{eid}_shift_did", "outcome": sch,
                        "unit_or_date": f"{k}-10", "is_actual": False, "window": "during",
                        "effect_log": v, "pct_gap": np.exp(v) - 1})
        row, _ = did_row(eid, f"Shift: South-OR (Bandon-Brookings) {lab} value", sch, SS[SO], SS[CO],
                         "Central-OR (Gearhart-Charleston)", window="after", **AFTER_DID)
        est.append(row)

    # ---------------- E6: Crescent City + South-OR combined -------------------
    comb = S[CC] + S[SO]
    S6 = dict(S)
    S6["CC+SO"] = comb
    pool6 = pool + [CO]
    inf6, _ = space_inference(S6, "CC+SO", pool6, W, "E6_combined_value", "value_all", plc)
    for w in W:
        row, r_comb = sc_row("E6", "Combined Crescent City + South-OR all-species value", "value_all",
                             comb, S6, pool6, W, w, inf6[w],
                             notes="cross-state sum: CDFW landing date vs ODFW purchase date; value is comparable, weight bases differ")
        est.append(row)
    row, _ = did_row("E6", "Combined Crescent City + South-OR all-species value", "value_all", comb,
                     D.agg_series(pool)[0] + S[CO], "CA donor pool total + Central-OR")
    est.append(row)

    # ---------------- E7: descriptive, Crescent City + Trinidad + Humboldt ------
    near = ["CA-trinidad", "CA-humboldt-bay"]
    Sn3 = series_dict([CC] + near)
    tot3 = Sn3[CC] + Sn3[near[0]] + Sn3[near[1]]
    yrs = C.WINDOW_START_YEARS_PRE + [C.EVENT_WINDOW_YEAR]
    T3, _, N3 = M.paired_window_totals(tot3, tot3, yrs)
    prior = T3[C.WINDOW_START_YEARS_PRE]
    est.append({"estimate_id": "E7", "label": "Descriptive: Crescent City + Trinidad + Humboldt Bay",
                "outcome": "value_all", "method": "descriptive_window_total", "window": "during",
                "observed": T3[2024], "counterfactual": prior.mean(),
                "gap": T3[2024] - prior.mean(), "pct_change": T3[2024] / prior.mean() - 1,
                "months_dropped_event": int(N3[2024]), "months_dropped_pre": int(N3[C.WINDOW_START_YEARS_PRE].sum()),
                "notes": "not causal; 'counterfactual' = mean of the 8 prior Oct-Aug windows over observed months; "
                         f"2024-25 ranks {int((prior < T3[2024]).sum()) + 1} of 9 windows counting from the lowest; null months dropped (lower bounds)"})

    # =========================== ROBUSTNESS ==================================
    base = est[0]

    def add_sc(rid, check, label, treated, SS, donors, windows=W, window="during", notes=""):
        row, r = sc_row(rid, label, "", treated, SS, donors, windows, window, notes=notes)
        row = {"robustness_id": rid, "check": check, **{k: v for k, v in row.items() if k != "estimate_id"}}
        rob.append(row)
        return r

    def add_did(rid, check, label, t, k, control, notes="", window="during", **kw):
        row, r = did_row(rid, label, "", t, k, control, window=window, notes=notes, **kw)
        row = {"robustness_id": rid, "check": check, **{k2: v for k2, v in row.items() if k2 != "estimate_id"}}
        rob.append(row)
        return r

    # R1 placebo dates (summaries; full lists in t41_placebos.csv)
    rob.append({"robustness_id": "R1", "check": "placebo dates", "label": "E1 SC fake events Oct 2017-Oct 2023",
                "method": "synthetic_control", "window": "during", "pct_change": base["pct_change"],
                "p_time": p_time_sc, "notes": f"fake-event 11-month gaps range {tp.during_pct.min():+.0%} to {tp.during_pct.max():+.0%}; "
                f"actual {base['pct_change']:+.1%}"})
    for lab, r in [("E2 DiD vs donor pool", r_did), ("E4 shift all-species", shift_did["value_all"]),
                   ("E5 shift crab", shift_did["value_crab"])]:
        rob.append({"robustness_id": "R1", "check": "placebo dates", "label": lab, "method": "window_DiD",
                    "window": "during", "pct_change": r["effect_pct"], "p_time": r["p_time"],
                    "notes": "placebo windows: " + ", ".join(f"{k}:{np.exp(v) - 1:+.0%}" for k, v in r["placebos"].items())})

    # R2 leave-one-out donors (every donor with weight > 0.01)
    wts = r_main["weights"]
    for d in wts[wts > 0.01].index:
        add_sc("R2", "leave-one-out donor", f"E1 without {d}", S[CC], S, [x for x in pool if x != d])
    rc = M.sc_fit(Sc[CC], pd.DataFrame({d: Sc[d] for d in cpool}), C.PRE_END, W)["weights"]
    for d in rc[rc > 0.01].index:
        add_sc("R2", "leave-one-out donor", f"E3 crab without {d}", Sc[CC], Sc, [x for x in cpool if x != d])

    # R3 value vs pounds
    add_sc("R3", "pounds instead of value", "E1 pounds (SC)", Sp[CC], Sp, pool)
    add_sc("R3", "pounds instead of value", "E1 pounds (SC), after", Sp[CC], Sp, pool, window="after")
    add_did("R3", "pounds instead of value", "E2 pounds (DiD)", Sp[CC], D.agg_series(pool, "pounds")[0],
            "sum of main CA donor pool", notes="donor-pool pounds dominated by market squid")
    add_did("R3", "pounds instead of value", "E4 shift pounds (DiD)", Sp[SO], Sp[CO], "Central-OR",
            notes="ODFW round weight both sides; Central-OR pounds dominated by Pacific whiting")
    add_sc("R3", "pounds instead of value", "E6 combined pounds (SC)", Sp[CC] + Sp[SO],
           {**Sp, "CC+SO": Sp[CC] + Sp[SO]}, pool + [CO],
           notes="mixes CDFW landed weight with ODFW round weight")

    # Crab pounds: all-species pounds are dominated by bulk species (market squid in
    # southern/central CA donors, Pacific whiting in Central-OR), so the volume
    # check that matters for a crab port is crab pounds.
    Scp = series_dict([CC] + cpool + [SO, CO], measure="pounds", scheme="crab")
    add_sc("R3", "pounds instead of value", "E3 crab pounds (SC)", Scp[CC], Scp, cpool)
    add_did("R3", "pounds instead of value", "E3 crab pounds (DiD vs crab donor pool)", Scp[CC],
            D.agg_series(cpool, "pounds", "crab")[0], f"crab donor pool ({len(cpool)})")
    add_did("R3", "pounds instead of value", "E3 crab pounds (DiD vs same-zone)", Scp[CC],
            D.agg_series(C.SAME_ZONE, "pounds", "crab")[0], "Trinidad+Humboldt+Noyo+Shelter Cove crab")
    add_did("R3", "pounds instead of value", "E3 crab pounds (DiD vs Humboldt Bay)", Scp[CC],
            D.unit_series("CA-humboldt-bay", "pounds", "crab")[0], "Humboldt Bay crab")
    add_did("R3", "pounds instead of value", "E5 shift crab pounds (DiD)", Scp[SO], Scp[CO], "Central-OR crab")
    add_sc("R3", "pounds instead of value", "E6 combined crab pounds (SC)", Scp[CC] + Scp[SO],
           {**Scp, "CC+SO": Scp[CC] + Scp[SO]}, cpool + [CO], notes="landed vs round weight")

    # R4 crab vs non-crab
    add_sc("R4", "crab vs non-crab", "E3 crab (SC) [same as E3]", Sc[CC], Sc, cpool)
    add_sc("R4", "crab vs non-crab", "Non-crab value (SC)", Sn[CC], Sn, pool,
           notes="non-crab = all minus Dungeness; null where either is withheld")
    add_sc("R4", "crab vs non-crab", "Non-crab value (SC), after", Sn[CC], Sn, pool, window="after")
    add_did("R4", "crab vs non-crab", "Non-crab value (DiD)", Sn[CC], D.agg_series(pool, scheme="noncrab")[0],
            "sum of main CA donor pool")

    # R5 excluding withheld / no-record months
    flags = {u: D.unit_series(u)[1] for u in [CC] + pool}
    clean_pool = [u for u in pool if not (flags[u][flags[u].index <= C.PRE_END] == "partial_confidential").any()]
    bad = set()
    for u in [CC] + clean_pool:
        f = flags[u]
        bad |= set(f[f.isin(["confidential", "no_record_zero", "partial_confidential"])].index)
    pre_bad = sorted(m for m in bad if m <= C.PRE_END)
    r5 = M.sc_fit(S[CC], pd.DataFrame({d: S[d] for d in clean_pool}), C.PRE_END, W, exclude_months=pre_bad)
    rob.append({"robustness_id": "R5", "check": "exclude withheld/no-record months",
                "label": "E1 SC, fit months exclude any flagged month; partial_confidential donors dropped",
                "method": "synthetic_control", "window": "during", "observed": r5["during_obs"],
                "counterfactual": r5["during_cf"], "gap": r5["during_gap"], "pct_change": r5["during_pct"],
                "n_fit_months": r5["n_fit_months"], "n_donors": len(clean_pool),
                "pre_rmspe_scaled": r5["pre_rmspe"],
                "notes": f"dropped donors: {sorted(set(pool) - set(clean_pool))}; {len(pre_bad)} pre months excluded; "
                         f"in-window flagged months: {sorted(m for m in bad if m > C.PRE_END)}"})
    add_did("R5", "exclude withheld/no-record months", "E2 DiD, flagged months dropped from every window",
            S[CC], D.agg_series(clean_pool)[0], "sum of donor pool without partial_confidential harbors",
            drop_months=set(bad))

    # R6 alternative event end (lease month 2025-02)
    add_sc("R6", "alternative event end (2025-02)", "E1 SC during 2024-10..2025-02", S[CC], S, pool, W_ALT, "during")
    add_sc("R6", "alternative event end (2025-02)", "E1 SC after 2025-03..2025-12", S[CC], S, pool, W_ALT, "after")
    add_did("R6", "alternative event end (2025-02)", "E2 DiD Oct-Feb windows", S[CC], K, "sum of main CA donor pool",
            m_start=10, m_end=2)
    add_did("R6", "alternative event end (2025-02)", "E4 shift DiD Oct-Feb windows", S[SO], S[CO], "Central-OR",
            m_start=10, m_end=2)
    add_did("R6", "alternative event end (2025-02)", "E4 shift DiD Mar-Dec (after-alt)", S[SO], S[CO], "Central-OR",
            window="after", pre_years=list(range(2016, 2024)), event_year=2025, m_start=3, m_end=12)

    # R7 South-OR Dungeness with ODFW blanks as missing
    Sb = series_dict([SO, CO], scheme="crab", blanks_missing=True)
    add_did("R7", "ODFW blanks as missing", "E5 shift crab DiD, blank_assumed_zero -> null (pairwise deletion)",
            Sb[SO], Sb[CO], "Central-OR crab",
            notes="part_blank_assumed_zero kept as lower bound; months with a fully blank cell dropped from both sides")
    add_did("R7", "ODFW blanks as missing", "E5 shift crab DiD, blanks missing, after", Sb[SO], Sb[CO],
            "Central-OR crab", window="after", **AFTER_DID)

    # R8 same-zone control (CA crab Zones 1-2), accepting spillover risk
    Kz = D.agg_series(C.SAME_ZONE)[0]
    Kzc = D.agg_series(C.SAME_ZONE, scheme="crab")[0]
    add_did("R8", "same-zone control (Zones 1-2)", "CC all-species vs Trinidad+Humboldt+Noyo+Shelter Cove",
            S[CC], Kz, "same-zone sum", notes="if CC boats landed in Trinidad/Humboldt, this overstates any drop")
    add_did("R8", "same-zone control (Zones 1-2)", "CC crab vs same-zone crab", Sc[CC], Kzc, "same-zone crab sum")
    add_did("R8", "same-zone control (Zones 1-2)", "CC all-species vs Humboldt Bay only", S[CC],
            D.unit_series("CA-humboldt-bay")[0], "Humboldt Bay (partial_confidential = lower bound)")

    # R9 South-OR synthetic control with CA + Central-OR donors (cross-state)
    add_sc("R9", "shift test via SC", "South-OR SC, donors = CA pool + Central-OR", S[SO], S, pool + [CO],
           notes="cross-state donors; date and weight bases differ")
    # R10 DiD for CC against the crab donor pool (all-species)
    add_did("R10", "alternative DiD control", "CC all-species vs crab donor pool total", S[CC],
            D.agg_series(cpool)[0], f"crab donor pool ({len(cpool)})")

    # ---------------- write tables ----------------
    E = pd.DataFrame(est)
    R = pd.DataFrame(rob)
    P = pd.DataFrame(plc)
    E.to_csv(C.TABLES / "t41_estimates.csv", index=False, float_format="%.10g")
    R.to_csv(C.TABLES / "t41_robustness.csv", index=False, float_format="%.10g")
    P.to_csv(C.TABLES / "t41_placebos.csv", index=False, float_format="%.10g")
    pd.DataFrame(donors_log).to_csv(C.TABLES / "t41_donors.csv", index=False)

    from portgaps.eventstudy import figures
    figures.make_all(S, r_main, ps_main, tp, r_did, shift_did, r_comb, comb)
    return E, R, P


if __name__ == "__main__":
    E, R, P = main()
    pd.set_option("display.width", 220)
    cols = ["estimate_id", "label", "method", "window", "observed", "counterfactual", "pct_change",
            "p_space_ratio", "p_space_pct", "p_time"]
    print(E[[c for c in cols if c in E]].to_string(float_format=lambda x: f"{x:,.3f}"))
    print(R[["robustness_id", "label", "window", "pct_change", "p_time"]].to_string(float_format=lambda x: f"{x:,.3f}"))
