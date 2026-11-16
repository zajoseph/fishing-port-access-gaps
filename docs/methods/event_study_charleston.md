# Event study: Charleston ice-plant fire, Dec 2019 – Sep 2020 (T4.2)

- **Code:** `src/portgaps/eventstudy/`. Entry point `run_charleston.py`, settings `config_charleston.py`, figures `figures_charleston.py`. Estimators are shared with T4.1 in `methods.py`.
- **Rebuild:** `python -I src/portgaps/eventstudy/run_charleston.py`. Takes about 5 s and is deterministic.
- **Notebook:** `notebooks/05_event_study_charleston.ipynb`.
- **Tables:** `outputs/tables/t42_estimates.csv`, `t42_robustness.csv`, `t42_placebos.csv`, `t42_donors.csv`.
- **Figures:** `outputs/figures/t42_treated_vs_counterfactual.png`, `t42_winchester_shift.png`, `t42_placebo_distribution.png`.
- **Tests:** `tests/test_eventstudy.py`.
- **T4.1 unchanged:** `methods.py` gained optional keyword arguments only. T4.1 was rerun and all 7 of its outputs (4 tables, 3 PNGs) are byte-identical to main.

## 1. Question and event

What happened to Charleston landings while its ice plant was out? Did the landings shift to the documented backup, Winchester Bay (23.4 charted-equivalent nm; Charleston boats used its ice plant after the fire, per `facilities.csv`), or did they disappear?

**Event dates.** These come from the closure sequence (`docs/data_dictionary.md` §5), not from `status_*`. The plant was closed on 2019-12-20 (fire; declared a total loss) and reopened on 2020-09-12.
- **During** = 2019-12 to 2020-09. December 2019 counts as during, although it holds only about 11 closed days.
- **After** = 2020-10 to 2024-12. Split into year 1 (2020-10 to 2021-09) and later (2021-10 to 2024-12).
- **Pre** = 2016-01 to 2019-11.

**Series.**
- Charleston is the ODFW harbor-level table, `species_scheme = all`, nominal dollars as published.
- It stops at 2024-12, because Charleston is part of the Florence–Charleston group from 2025; that group is not split.
- Every Oregon unit used here has complete all-species value and pounds for 2016-01 to 2024-12, so no null months arise for all species.
- ODFW blanks = 0 by the documented assumption.

## 2. Context the design has to handle

**Dungeness season.** All dates are from ODFW releases and notices; context only, no series was adjusted.

| Season | Opening (Charleston's area in bold where split) | Source |
|---|---|---|
| 2016-17 | S of Cape Blanco Dec 18, 2016; **Cape Blanco–WA border Jan 1, 2017** | [ODFW 2016-12-09](https://www.dfw.state.or.us/news/2016/12_dec/120916.asp), [PSMFC industry notice](https://www.psmfc.org/crab/2016-2017%20files/IndustryNoticeNorthOpener_122116.pdf) |
| 2017-18 | **Cape Blanco to Columbia River Jan 15, 2018** | [ODFW 2017-12-21](https://dfw.state.or.us/news/2017/12_dec/122117.asp) |
| 2018-19 | **North of Cape Arago Jan 4, 2019** (south later) | [ODFW 2018-12-31](https://dfw.state.or.us/news/2018/12_december/123118b.asp) |
| 2019-20 (closure) | **Coastwide Dec 31, 2019** | [ODFW 2019-12-20](https://dfw.state.or.us/news/2019/12_Dec/122019.asp) |
| 2020-21 | **S of Cape Falcon Dec 16, 2020**; north of Cape Falcon Feb 15, 2021 | [ODFW 2020-12-18](https://dfw.state.or.us/news/2020/12_Dec/121820.asp), [National Fisherman](https://nationalfisherman.com/west-coast-pacific/on-time-opening-for-oregon-dungeness-season) |
| 2021-22 | **On time, Dec 1, 2021** (first since 2014-15) | [ODFW 2021-11-19](https://dfw.state.or.us/news/2021/11_Nov/111921.asp) |
| 2022-23 | **Jan 15, 2023** for much of the coast, then in stages | [OPB](https://opb.org/article/2023/01/07/oregon-opens-commercial-crabbing-season-january-15-after-delay) |
| 2023-24 | **Cape Foulweather–CA border Dec 16, 2023**; Cape Falcon–Cape Foulweather Dec 31 | [ODFW 2023-12-20](https://dfw.state.or.us/news/2023/12_Dec/122023b.asp), [Tillamook County Pioneer (ODFW release)](https://tillamookcountypioneer.net/commercial-dungeness-crab-season-begins-dec-16-from-cape-foulweather-to-california-border) |

What this means for the windows:
- **The closure season opened coastwide on Dec 31, 2019**, so Dec 2019 holds almost no ocean crab at any Oregon port. Dropping December (R6) changes nothing.
- The three pre windows (Dec 2016, 2017, 2018) also opened Jan 1–15. Their crab timing matches the event window better than the post placebo windows do: Dec 2021 opened on time, and the 2020-21 and 2023-24 seasons opened Dec 16.
- The ocean crab season ends Aug 14, so Sep holds no ocean crab.

**COVID.**
- The first hit was the halt of live-crab sales to China in late January 2020 ([OPB, Apr 2020](https://opb.org/news/article/restaurant-closures-put-oregon-seafood-industry-in-limbo); [OSU Extension](https://extension.oregonstate.edu/node/160241)). Restaurant closures followed in March.
- The pink shrimp season opened Apr 1 into falling prices ([KLCC, Mar 2020](https://www.klcc.org/post/coronavirus-disrupts-shrimp-market-commercial-season-nears)). The 2020 catch was still large, 42.3 M lb ([SeafoodSource](https://www.seafoodsource.com/news/supply-trade/oregon-pink-shrimp-season-opens-amidst-pandemic-uncertainty)).

**Exposure.** Pre-period value shares (crustaceans = Dungeness + pink shrimp):

| Unit | Crustaceans | Fish | Molluscs |
|---|---|---|---|
| Charleston | 70% | 29% | |
| Newport | 54% | 44% | |
| Astoria | 40% | 60% | |
| Gearhart–Garibaldi | 65% | 18% | 17% |
| Gold Beach–Brookings | 76% | 21% | |

So Charleston is **more** crab- and shrimp-exposed than the donors that carry most of the SC weight (Newport 0.52, Astoria 0.13). Gold Beach–Brookings (0.18) is the only weighted donor more exposed than Charleston.

If the China halt and spring 2020 hit crab and shrimp harder than fish, the counterfactual understates Charleston's COVID shock, and the estimate leans toward showing a loss. Two checks address this:
- crab and non-crab separately (R4);
- dropping Mar–Jun 2020 (R7).

The Jan–Feb crab-export shock cannot be dropped without dropping the opener.

## 3. Methods (user-approved, T4.2 chat 2026-11-16)

These are the same as T4.1:
- **SC:** synthetic control on each unit's monthly series, scaled to its own pre-period mean, with non-negative weights summing to 1. Fit months are 2016-01 to 2019-11 (47 months).
- **DiD:** log ratio of treated to donor-sum window totals, event window minus the mean of the pre windows. Windows run Dec→Sep (the closure's 10 months); the pre windows are Dec 2016, 2017 and 2018. After-period DiD uses Oct→Sep years 2020-21 to 2023-24 against 2016-17 to 2018-19.
- **Missing data:** null months are dropped pairwise, never filled.

### Donor pool (`t42_donors.csv`)

**Main pool = 5 Oregon ODFW units** (same agency, purchase-date basis, round weight). Distances are charted-equivalent nm from Charleston.

| Unit | Nearest harbor (nm) | Pre corr. with Charleston | Used |
|---|---|---|---|
| Newport | 82.9 | 0.92 | yes |
| Gearhart–Garibaldi | 145.0 | 0.88 | yes |
| Astoria | 193.9 | 0.82 | yes |
| Gold Beach–Brookings | 64.2 (Brookings 90.5) | 0.59 | yes |
| Netarts–Depoe Bay | 94.3 | 0.18 | yes (tiny, $0.4 M/yr; gets ~0 SC weight) |
| Waldport–Winchester Bay | 23.4 (Florence 48.0) | 0.63 | no: receiver (shift-test unit) |
| Bandon–Port Orford | 17.7 (Port Orford 44.4) | 0.53 | no: Bandon inside 40 nm (checked in R11) |

- Newport and Gold Beach are beyond 40 nm but could still have taken some Charleston boats. Leave-one-out (R2) covers them.
- **Northern CA donors are a robustness check only (R9; user answer).** Rule: CA crab Fishing Zones 1–2 harbors that pass the null screens and have no own event in the window. That leaves Humboldt Bay (partial_confidential lower bound), Noyo Harbor and Shelter Cove. The rest are excluded:
  - Crescent City: own closure from 2024-10;
  - Trinidad: null months in the window;
  - Point Arena: 34% of pre months null.
- None of the northern CA harbors passes the crab null screen.
- The other CA harbors track Charleston poorly (central CA crab opens Nov 15; pre correlations about 0 or negative). CA also uses landing date and landed weight.
- **Crab pool:** the same 5 OR units. All have pre crab ≥ $100k/yr (Netarts–Depoe Bay $117k).

## 4. Inference

- **Placebo-in-space:** each donor is refit as if treated. With 6 units, the smallest attainable p is 0.17 (`p_space_ratio` one-sided on post/pre RMSPE; `p_space_pct` two-sided on the gap).
- **Placebo-in-time, main (user answer):** pre-period fake events only.
  - SC: Dec 2017 and Dec 2018 (Dec 2016 leaves 11 fit months). Smallest p = 0.33.
  - DiD: the 3 pre windows. Smallest p = 0.25.
- **Placebo-in-time, extra (`p_time_incl_post`):** adds fake Dec events in 2021, 2022 and 2023, fitted without the closure months. This assumes the closure had no lasting effect.
- **Power (R10, test inversion):** see §6.

## 5. Results (`t42_estimates.csv`; value in nominal $)

**Charleston, during (Dec 2019 – Sep 2020).**

| Est. | Method | Observed | Counterfactual | Change | p (space ratio / gap) | p_time (pre) | p_time (pre + post) |
|---|---|---|---|---|---|---|---|
| E1 all-species value | SC | $18.9 M | $28.7 M | **−33.9%** | 0.33 / 0.17 | 0.33 | 0.17 |
| E2 all-species value | DiD | $18.9 M | $28.9 M | **−34.5%** | – | 0.25 | 0.29 |
| E3 all-species pounds | SC / DiD | 15.0 M lb | 18.9 / 21.3 M lb | −20.7% / −29.7% | 0.50 / 0.67 | 0.33 / 0.25 | 0.50 / 0.29 |
| E4 Dungeness value | SC / DiD | $10.6 M | $16.5 / $17.9 M | −35.7% / −40.8% | 0.50 / 0.50 | 0.33 / 0.25 | 0.33 / 0.29 |

SC weights (E1): Newport 0.52, Gold Beach–Brookings 0.18, Gearhart–Garibaldi 0.16, Astoria 0.13. Pre-fit RMSPE is 0.24 of the pre mean.

**Charleston, after the reopening.**

| Period | SC | DiD |
|---|---|---|
| Year 1 (Oct 2020 – Sep 2021) | −25.4% | −16.0% |
| Later (Oct 2021 – Dec 2024) | −31.8% | −33.6% (mean of 2021-22 to 2023-24: −31%, −33%, −37%) |

Crab after: year 1 SC +41% / DiD +9%; later SC −19% / DiD −30%.

**Shift test, during.**
- **E5, Waldport–Winchester Bay unit:** SC **+3.7%** ($4.41 M vs $4.26 M; p_space 0.83, p_time 1.00); DiD **−0.8%** (p_time 1.00). SC weights: Gearhart–Garibaldi 0.67, Netarts–Depoe Bay 0.26.
- **E6, Charleston + Winchester Bay unit combined:** SC **−29.5%** ($23.3 M vs $33.1 M; p_space 0.33/0.33, p_time 0.33); DiD **−30.2%** (p_time 0.25).
- The receiver unit shows no gain in value. The combined area falls by nearly as much as Charleston alone.

**Shift test, after.**
- Receiver unit: SC −10% (year 1) and −15% (later); DiD +56% (year 1) and +30% (later).
- The two methods disagree because they use different controls. The SC leans on Garibaldi, which doubled after 2020; the DiD uses the donor sum, dominated by Newport and Astoria.
- Combined: −21% to −26% (SC), −7% to −25% (DiD).

**What the placebos show** (`t42_placebo_distribution.png`):
- **Pre-period fake events were all small.** SC −5% to +4%, DiD −5% to +9%. Charleston's −34% sits outside every one of them, but with 2–3 placebos the p-value cannot go below 0.25–0.33.
- **Post-reopening fake events were large and negative.** SC −28% to −11%, DiD −36% to −30%. They match the closure-window gap, so the drop is **not specific to the closure window.**
- **Placebo-in-space:** Charleston has the largest negative gap of the 6 units (p_space_pct 0.17, the minimum), but Gold Beach–Brookings (−31%) and Netarts–Depoe Bay (−28%) come close.

## 6. Robustness (`t42_robustness.csv`; all required checks reported)

**R1 Placebo dates:** summarized in §5. The full lists are in `t42_placebos.csv` (`timing` = pre / post).

**R2 Leave-one-out donors**
- E1 SC: −32% to −38%; E2 DiD: −33% to −37%, whichever donor is dropped (including Newport and Gold Beach–Brookings).
- Crab SC: −33% to −44%.
- Receiver unit SC: −2% to +12%.
- Combined SC: −27% to −34%.
- So the Charleston drop does not rest on one donor.

**R3 Value vs pounds**
- Charleston all-species pounds fall less than value: SC −21%, DiD −30%.
- Crab pounds fall like crab value: SC −36%, DiD −40%.
- Receiver unit pounds SC **+78%** (3.20 M vs 1.80 M lb, mostly non-crab; see R4).
- Combined pounds SC −12%; combined crab pounds −32%.

**R4 Crab vs non-crab**
- Charleston crab −36% (SC) / −41% (DiD); non-crab −26% (SC) / −29% (DiD). Both fall.
- Receiver unit: crab SC −18%, non-crab SC **+60%** (+$0.67 M).
- Combined: crab −33%, non-crab −18%.

**R5 Crab with blanks as missing** (T4.1 rule, user answer: fully blank → null; part-blank kept as flagged lower bound)
- Charleston crab SC −28% (32 fit months left).
- DiD −53%, but this drops 3 of the 10 event months, including high-value ones, because any blank donor month removes that month. Read the DiD as unreliable.
- Receiver unit crab SC +4%; combined crab SC −38%.

**R6 Alternative start 2020-01:** E1 −34%; crab −36%; receiver +5%; combined −30%; DiD Jan–Sep −36% (4 pre windows, p 0.20).

**R7 Excluding Mar–Jun 2020:** E1 −33%; pounds −29%; crab −38%; receiver +8%; combined −30%. The DiD with Mar–Jun dropped from every window gives −36%. So the gap is not concentrated in the COVID-shutdown months.

**R8 After-period split:** see §5. Charleston value is −25% (SC) / −16% (DiD) in year 1 and −32% / −34% later.

**R9 OR + northern CA donors:** E1 SC −31% (p_space 0.44 / 0.67 with 9 units); crab −36% (no CA crab donor passes); receiver −3%; combined −27%; DiD −32%.

**R10 Power (test inversion, log-symmetric).** The question is how large a true loss would have to be before the design could rank it as extreme.

| Placebo set | Smallest loss outside all placebos | Smallest attainable p |
|---|---|---|
| Pre-only SC (2 placebos) | 5% | 0.33 |
| Pre-only DiD (3 placebos) | 8% | 0.25 |
| Space (5 placebos) | 31% | 0.17 |
| Pre + post SC (5 placebos) | 28% | 0.17 |
| Pre + post DiD (6 placebos) | 36% | 0.14 |

Even a true 75–90% loss gives p = 0.14–0.33, because the p-values are capped by the number of placebos.

**R11 Other nearby harbor (added check):** Bandon–Port Orford unit (Bandon 17.7 nm, not a documented backup).
- SC +36% (weight 0.90 on Gold Beach–Brookings; poor fit); DiD −4%. Inconclusive. The unit is about $4–5 M/yr, so even the SC figure is about +$1.1 M against Charleston's −$9.7 M.
- Charleston + receiver + Bandon–Port Orford: −24% (SC), −27% (DiD).

## 7. Limits

- **The drop is not specific to the closure.**
  - Charleston fell about one-third relative to Oregon donors in the closure window, and stayed roughly that far below in every year after the plant reopened (2020-21 to 2023-24).
  - Annual Charleston value: $28.6 M (2019), $20.0 M (2020), $34.8 M (2021), $14.2 M (2022), $27.1 M (2023), $24.8 M (2024). Meanwhile donors grew, e.g. Astoria $68 M in 2024 and Garibaldi more than doubled.
  - So the design cannot separate a closure effect from a Charleston-specific decline (or donor growth) that began with the 2019-20 season.
  - A lasting closure effect (boats that left and stayed away) is possible but undocumented. LOO without Newport or Gold Beach–Brookings does not change the result, so a permanent move to those ports is not what drives it.
- **Power:**
  - With 5 donors and 2–3 pre placebos, no test can return p below 0.17 (space) or 0.25–0.33 (time).
  - The pre placebos are tight, so the during gap is as extreme as the design can show. But the post placebos and other donors produce gaps of similar size.
- **COVID exposure:** Charleston's crab and shrimp mix is more exposed than its main donors' (§2). Some of the during-window gap may be COVID rather than ice. R7 says it is not concentrated in Mar–Jun, but the China live-crab halt (Jan–Feb) cannot be separated from the opener.
- **The receiver unit dilutes Winchester Bay.** The Waldport–Winchester Bay table also holds Florence and non-inventory ports.
  - A shift into Winchester Bay alone smaller than the unit's pre-window swings (DiD −35% to +39%) would not show.
  - The R3/R4 non-crab and pounds gains (+$0.67 M; +1.4 M lb) are consistent with some volume going there, but they have no inference and are small next to Charleston's loss.
- **Data:**
  - ODFW blanks = 0 by assumption. Charleston crab is part-blank in all 10 closure months (bay crab; Sep 2020 ocean crab, season closed); fully blank months are rare (Charleston 4).
  - Nominal dollars.
  - ODFW purchase date and round weight on both sides of every Oregon comparison. R9 mixes in CDFW landing date and landed weight; use value there.
- **In-sample caveat:** Charleston (index event E2) was an input to the threshold choice, so its agreement with the index (Winchester Bay 23.4 nm as the backup) is partly in-sample. This study does not test the threshold.
- **Facility status** is current, not monthly; nothing here is dated from `status_*`.
- **The T3.3 descriptive ratio of 0.66×** overlaps COVID and is not a result. Its size happens to match the −34% here, but it has no counterfactual.

## 8. Plain-language result

During the ten months without its ice plant, Charleston landed about **one-third less** than comparable Oregon ports would predict: about $19 M against a counterfactual of about $29 M. The range across designs is −30% to −41% for value (SC −34%, DiD −35%, crab −36% to −41%) and −21% to −30% for pounds.

**The landings did not show up at Winchester Bay.** The unit containing Winchester Bay shows no gain in value (+4% SC, −1% DiD), and Charleston plus that unit together still fall about 30%. In plain terms, the lost landings mostly **disappeared from this stretch of coast** rather than shifting to the documented backup. The only hint of a shift is a small, untested rise in non-crab pounds in the Winchester Bay unit.

**How confident can we be? Not very, for two reasons.**
1. The drop was as large as the design can detect, but with only five comparison ports no test can come out significant (the smallest possible p-value is 0.17).
2. Charleston stayed about a third below the same comparison in every year after the plant reopened. So the closure-period drop looks like the start of a longer Charleston-specific slump, or lasting damage, rather than a clean ten-month dip. This study cannot tell which.

Report it as "Charleston landings fell about a third during the closure and did not move to Winchester Bay, but the shortfall persisted after reopening, so it cannot be attributed to the ice plant alone; low power." Never call it a significant effect.

### Comparison with Crescent City (T4.1)

The two ice closures look different:
- **Crescent City** (Oct 2024 – Aug 2025) held its value: SC +3%, DiD +10%, combined with South-OR −6%. The verdict there was "did not disappear; no detectable shift," fitting Brookings as a trucked-ice supplier rather than a landing port.
- **Charleston** shows a sizable relative loss (−30% to −41%) with no offsetting gain at the backup unit. That leans toward "disappeared."

Both studies share the same weakness: few donors and coarse placebo inference, so neither result is significant. Each also has its own confound:
- Crescent City's value held partly on a high crab price.
- Charleston's loss overlaps the start of COVID and continues after the plant reopened.

Together they do not support a single general claim about what an ice-plant loss does to a harbor's landings.
