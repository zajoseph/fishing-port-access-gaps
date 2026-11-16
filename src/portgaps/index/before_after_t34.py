"""T3.4 before/after: top 10 per service at 25/30/40/50 nm, main and s1, and the
"holds under both runs" list (main top-10 entry with value > 0 that keeps
value > 0 under s1, as in docs/review_index_t33.md section 4).

Before = index_sensitivity.csv as committed on main before T3.4
(git show 909c73d:outputs/tables/index_sensitivity.csv; byte-identical to the 933044e
index run, per T3.3 and a T3.4 rerun of the unmodified code); after = the regenerated file.
    python -I src/portgaps/index/before_after_t34.py <before_sensitivity.csv>
Writes outputs/tables/t34_before_after.csv.
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
T = ROOT / "outputs" / "tables"
TH = [25, 30, 40, 50]
RUNS = ["main", "s1_not_found_as_available"]
COLS = ["run", "threshold_nm", "service", "facility_id", "rank_service", "stranded_low", "stranded_high"]


def load(p):
    s = pd.read_csv(p)
    return s[s.stranded_low.notna() & s.run.isin(RUNS) & s.threshold_nm.isin(TH)][COLS]


def top10(s):
    return s[(s.rank_service <= 10) & (s.stranded_high > 0)]


def holds(s):
    m = top10(s[s.run == "main"])
    s1 = s[s.run == "s1_not_found_as_available"].set_index(["threshold_nm", "facility_id"]).stranded_high
    v = [s1.get((t, f), 0) for t, f in zip(m.threshold_nm, m.facility_id)]
    return set(zip(m.threshold_nm, m.facility_id)), {k for k, x in zip(zip(m.threshold_nm, m.facility_id), v) if x > 0}


def main(before_path):
    b, a = load(before_path), load(T / "index_sensitivity.csv")
    key = ["run", "threshold_nm", "service", "facility_id"]
    tb, ta = top10(b), top10(a)
    ids = pd.concat([tb[key], ta[key]]).drop_duplicates()
    out = (ids.merge(b, on=key, how="left").merge(a, on=key, how="left", suffixes=("_before", "_after")))
    out["in_top10_before"] = out.set_index(key).index.isin(tb.set_index(key).index)
    out["in_top10_after"] = out.set_index(key).index.isin(ta.set_index(key).index)

    def change(r):
        if r.in_top10_before and not r.in_top10_after:
            return "left_top10"
        if r.in_top10_after and not r.in_top10_before:
            return "entered_top10"
        if r.rank_service_before != r.rank_service_after:
            return "rank_moved"
        if (r.stranded_low_before, r.stranded_high_before) != (r.stranded_low_after, r.stranded_high_after):
            return "value_changed"
        return "unchanged"
    out["change"] = out.apply(change, axis=1)
    hb_all, hb = holds(b)
    ha_all, ha = holds(a)
    k2 = list(zip(out.threshold_nm, out.facility_id))
    out["holds_both_runs_before"] = ["Y" if k in hb else ("N" if k in hb_all else "") for k in k2]
    out["holds_both_runs_after"] = ["Y" if k in ha else ("N" if k in ha_all else "") for k in k2]
    out.loc[out.run != "main", ["holds_both_runs_before", "holds_both_runs_after"]] = ""
    for c in ["in_top10_before", "in_top10_after"]:
        out[c] = out[c].map({True: "Y", False: "N"})
    for c in ["rank_service_before", "rank_service_after", "stranded_low_before", "stranded_low_after",
              "stranded_high_before", "stranded_high_after"]:
        out[c] = out[c].astype("Int64")
    out["run"] = pd.Categorical(out.run, RUNS)
    out = out.sort_values(["run", "threshold_nm", "service", "rank_service_after", "rank_service_before", "facility_id"])
    out.to_csv(T / "t34_before_after.csv", index=False)
    for lab, (al, h) in {"before": (hb_all, hb), "after": (ha_all, ha)}.items():
        print(lab, "holds at 40:", sum(t == 40 for t, _ in h), "of", sum(t == 40 for t, _ in al),
              "| 25-50:", len(h), "of", len(al))
    print(out.change.value_counts().to_string())


if __name__ == "__main__":
    main(sys.argv[1])
