"""Landed-value basis for the T3.2 index.

Value of a harbor = mean annual all-species ex-vessel value, 2019-2024, nominal.

* CA: harbor-level panel (CDFW MFDE). Confidential months are left out, so the
  value is a lower bound, flagged; same lower and upper.
* OR: harbor-level where ODFW publishes it (Newport, Charleston). Other harbors
  take their 2016-2024 ODFW table unit. A unit with one inventory harbor is used
  whole (flag unit_level). A unit shared by inventory harbors is never split.
* WA: unit = PacFIN ALL005 group (annual, all species); sub-blocks = FOSS
  annual port values.

Shared units: a harbor's own range is lower = its own FOSS value (else 0) and
upper = the whole unit value. For a set of cut-off harbors, `set_value` returns
(lower, upper):
  upper = sum of whole-unit values over every unit touched (deduplicated on
          unit_id, so a shared unit is counted once);
  lower = per unit: the whole unit if every inventory harbor in it is cut off
          and it holds no non-inventory ports; otherwise the sum of FOSS
          sub-blocks whose harbors are all cut off (capped at the unit value).
"""
from __future__ import annotations

import pandas as pd

from . import config as C


def _mean_years(df: pd.DataFrame, col: str = "value_usd") -> float:
    """Mean over the 6 value years; missing years count as 0."""
    y0, y1 = C.VALUE_YEARS
    s = df.set_index("year")[col].reindex(range(y0, y1 + 1)).fillna(0.0)
    return float(s.mean())


def build_values() -> tuple[pd.DataFrame, dict]:
    ports = pd.read_csv(C.PROC / "ports.csv")
    bridge = pd.read_csv(C.PROC / "port_unit_bridge.csv")
    lm = pd.read_csv(C.PROC / "landings_monthly.csv")
    ann = pd.read_csv(C.TABLES / "t21_annual_crosscheck.csv")
    y0, y1 = C.VALUE_YEARS

    # unit for the value window: the bridge row that covers 2019-2024
    br = bridge[(bridge.valid_from <= f"{y0}-01") & (bridge.valid_to >= f"{y1}-12")]
    assert br.port_id.is_unique and len(br) == len(ports), "one value unit per harbor"
    unit_of = dict(zip(br.port_id, br.unit_id))

    units: dict[str, dict] = {}
    for uid, g in br.groupby("unit_id"):
        units[uid] = {"members": sorted(g.port_id), "value": None, "blocks": [],
                      "noninv": uid in C.UNITS_WITH_NONINVENTORY_PORTS,
                      "source": None, "lower_bound_withheld": False,
                      "confidential_share": 0.0, "partial_share": 0.0}

    # CA and OR: all-species monthly panel
    allsp = lm[(lm.species_scheme == "all") & lm.year.between(y0, y1)]
    for uid, u in units.items():
        if uid.startswith("WA-"):
            continue
        g = allsp[allsp.unit_id == uid]
        assert len(g) == 12 * (y1 - y0 + 1), (uid, len(g))
        u["value"] = float(g.value_usd.fillna(0).sum()) / (y1 - y0 + 1)
        u["confidential_share"] = float((g.withheld_flag == "confidential").mean())
        u["partial_share"] = float((g.withheld_flag == "partial_confidential").mean())
        u["lower_bound_withheld"] = bool(g.withheld_flag.isin(
            ["confidential", "partial_confidential", "pacfin_confidential"]).any())
        u["source"] = "CDFW MFDE harbor panel" if uid.startswith("CA-") else "ODFW FTR205 port table"

    # WA: ALL005 group value (upper); FOSS sub-blocks
    for uid, gname in C.WA_GROUPS.items():
        g = ann[(ann.source == "pacfin_all005") & (ann.unit == gname)]
        units[uid]["value"] = _mean_years(g)
        units[uid]["source"] = f"PacFIN ALL005 {gname} (annual; '*' cells excluded)"
        units[uid]["lower_bound_withheld"] = bool(
            ann[(ann.source == "pacfin_all005") & (ann.unit == gname) & ann.year.between(y0, y1)]
            .n_species_cells_confidential.fillna(0).gt(0).any())

    foss = ann[(ann.source == "foss")]
    for fname, members in C.FOSS_BLOCKS.items():
        uids = {unit_of[m] for m in members}
        assert len(uids) == 1, (fname, uids)
        uid = uids.pop()
        g = foss[foss.unit == fname]
        n_years = int(g[g.year.between(y0, y1)].value_usd.notna().sum())
        units[uid]["blocks"].append({"name": fname, "members": members,
                                     "value": min(_mean_years(g), units[uid]["value"]),
                                     "years_listed": n_years})

    # per-harbor table
    rows = []
    for _, p in ports.iterrows():
        uid = unit_of[p.port_id]
        u = units[uid]
        shared = len(u["members"]) > 1
        if not shared:
            low = high = u["value"]
        else:
            low = sum(b["value"] for b in u["blocks"] if b["members"] == [p.port_id])
            low = min(low, u["value"])
            high = u["value"]
        own_block = [b for b in u["blocks"] if p.port_id in b["members"]]
        rows.append({
            "port_id": p.port_id, "port_name": p.port_name, "state": p.state,
            "unit_id": uid, "unit_members": ";".join(u["members"]),
            "shared_unit": "Y" if shared else "N",
            "value_low": round(low), "value_high": round(high),
            "unit_value": round(u["value"]),
            "foss_block": own_block[0]["name"] if own_block else "",
            "foss_years_listed": own_block[0]["years_listed"] if own_block else "",
            "value_source": u["source"],
            # single-inventory-harbor ODFW table that also holds other (non-inventory) ports
            "unit_level": "Y" if (uid.startswith("OR-ODFW") and not shared) else "N",
            "lower_bound_withheld": "Y" if u["lower_bound_withheld"] else "N",
            "confidential_share": round(u["confidential_share"], 3),
            "partial_confidential_share": round(u["partial_share"], 3),
            "heavily_withheld": "Y" if (p.state == "CA" and u["confidential_share"] >= C.HEAVY_WITHHELD_SHARE) else "N",
            "marina_only": "Y" if p.port_id in C.MARINA_ONLY else "N",
        })
    hv = pd.DataFrame(rows)
    return hv, units


def set_value(cut: set[str], units: dict, unit_of: dict) -> tuple[float, float]:
    """(lower, upper) landed value of a set of cut-off harbors; no double counting."""
    low = high = 0.0
    for uid in {unit_of[h] for h in cut}:
        u = units[uid]
        mem = set(u["members"])
        high += u["value"]
        if len(mem) == 1:
            low += u["value"]
        elif mem <= cut and not u["noninv"]:
            low += u["value"]
        else:
            low += min(u["value"], sum(b["value"] for b in u["blocks"] if set(b["members"]) <= cut))
    return low, high
