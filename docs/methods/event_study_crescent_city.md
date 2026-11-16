# Event study: Crescent City ice-plant closure, Oct 2024 – Aug 2025 (T4.1)

Code: `src/portgaps/eventstudy/` (rebuild: `python -I src/portgaps/eventstudy/run.py`, about 5 s, deterministic). Notebook: `notebooks/04_event_study_crescent_city.ipynb`. Tables: `outputs/tables/t41_estimates.csv`, `t41_robustness.csv`, `t41_placebos.csv`, `t41_donors.csv`. Figures: `outputs/figures/t41_*.png`. Tests: `tests/test_eventstudy.py`.

## 1. Question and event

What happened to Crescent City landings while the harbor had no ice plant? And did the landings shift to Brookings (the index's predicted backup, 20.5 charted-equivalent nm, and the documented source of trucked ice) or disappear?

**Event dates.** These come from the closure sequence in `docs/data_dictionary.md` §5, not from `status_*`:
- closed 2024-10-05 (Pacific Seafood exit; equipment pulled Nov 2024; ice trucked from Brookings);
- Ocean Gold lease about 2025-02;
- running by 2025-08-27 (exact restart day unknown).

**Windows.**

| Window | Months |
|---|---|
| Pre | 2016-01 – 2024-09 |
| During | 2024-10 – 2025-08 (the event month counts as during) |
| After | 2025-09 – 2025-12 (4 months) |
| Alternative end (robustness) | during 2024-10 – 2025-02; after 2025-03 – 2025-12 |

**Data.**
- CA: CDFW MFDE harbor-level, all species, calendar year, nominal dollars. Withheld months stay null and are never imputed; `no_record_zero` = 0.
- OR: ODFW FTR205 (dealer purchase date, round weight). Blanks = 0 by the documented assumption; R7 reruns crab with blanks as missing.

## 2. Things the design has to handle

1. **Brookings has no harbor-level series.** Its ODFW unit is *Gold Beach–Brookings* in 2016–24, then *Bandon–Port Orford–Gold Beach–Brookings* from 2025, so the unit changes inside the closure window. The two 2016–24 tables *Bandon–Port Orford* + *Gold Beach–Brookings* cover exactly the 2025 group's four harbors. Their sum, **South-OR**, is a consistent unit for 2016–25.
   - Brookings is the closest of the four (Gold Beach is 46 nm from Crescent City, Port Orford 81, Bandon 93).
   - A shift into Brookings is therefore diluted by three other harbors' landings, and the unit cannot say which harbor received it.
2. **Crab season timing is the main confounder.** Crescent City earned 89% of its 2019–24 value from Dungeness crab.
   - In 2024-25 the commercial opener for CA Fishing Zones 1–2 (Oregon border to the Sonoma/Mendocino line) was delayed to Jan 15, 2025, with a 25% trap reduction. Zones 3+ opened Jan 5, 2025 ([CDFW](https://wildlife.ca.gov/News/Archive/commercial-dungeness-crab-fishery-to-open-jan-5-in-central-california)).
   - Southern Oregon opened Dec 16, 2024 ([ODFW](https://www.dfw.state.or.us/news/2024/12_Dec/120624.asp)).
   - CDFW closed commercial crab in Zones 1–2 from Jun 20, 2025 ([CDFW Whale Safe Fisheries](https://wildlife.ca.gov/Conservation/Marine/Whale-Safe-Fisheries/Lost-Gear)).
   - A single month (e.g. Dec 2024, when Oregon was open and northern California was not) would therefore look like a shift that is only the openers differing. **All headline effects are sums over the whole 11-month window**, which contains each year's opener.
3. **One treated unit.** Inference is by permutation, not by standard errors (§4).
4. **Crescent City is the largest crab port in California.** A weighted average of smaller ports cannot reach its dollar level, so SC works on each unit's series divided by its own pre-period monthly mean (shape, not size). The counterfactual is then rescaled to Crescent City dollars.

## 3. Methods (user-approved, T4.1 chat 2026-11-16)

- **Main method: synthetic control (SC).** Weights are non-negative and sum to 1. They are fitted on the scaled monthly value over pre months where Crescent City and every donor are observed (91 of 105).
  - Headline = the cumulative gap over the 11 during-months: observed − counterfactual, in $ and %.
- **Alongside it: window-total DiD.** The statistic is log(treated Oct–Aug total / control Oct–Aug total) in 2024-25, minus its mean over the 8 prior windows (2016-17 … 2023-24).
  - Months where either side is null are dropped from both sides of that window (pairwise deletion, never filled).
  - The after-period DiD uses Sep–Dec windows, 2016–2023 vs 2025.
- **Shift test.**
  - (E4/E5) South-OR vs **Central-OR**. Central-OR is every ODFW table from Gearhart to Charleston; the 2016–24 tables and the 2025 tables cover the same ports, except that "Seaside" is not named in the 2025 Gearhart table. It shares South-OR's agency, date basis, weight basis and crab opener.
  - (E6) Crescent City + South-OR combined, against SC (donors = CA pool + Central-OR) and against a DiD control (CA donor pool total + Central-OR).
  - (E7) Crescent City + Trinidad + Humboldt combined, descriptive only.

### Donor pool (`t41_donors.csv`)

The main all-species pool has **18 CA harbors**: Bodega Bay, Channel Islands, Dana Point, LA/LB, Mission Bay, Monterey, Morro Bay, Moss Landing, Noyo Harbor, Oceanside, Pillar Point, Port San Luis, San Diego Bay, San Francisco, Santa Barbara, Santa Cruz, Shelter Cove and Ventura.

Excluded, with reasons:

| Excluded | Reason |
|---|---|
| Brookings | The receiving port, and the only harbor within the logged 40 nm threshold (20.5 nm). It is in Oregon. |
| Trinidad (45.0 nm), Humboldt Bay (67.7 nm) | User answer: possible receivers and a spillover buffer. They are the next CA harbors, in the same crab zone, and Humboldt has ice. |
| Point Arena | Own facility outage inside the after-window (hoist out 2025-10-18 → 2026-01-29). |
| Vallejo, Avalon, Huntington Harbour, Port Hueneme, Marina del Rey | Heavily withheld: ≥30% of pre months null (the index's s3 rule, applied to the pre window). |
| Berkeley, Newport Beach, Redondo Beach | A null month inside 2024-10 – 2025-12, so the counterfactual would be undefined there. |

- **Crab pool:** the same rules, plus mean annual pre-period crab value ≥ $100k and no null crab month in the window. That leaves **4 donors: Bodega Bay, Pillar Point, San Francisco, Shelter Cove.**
  - Noyo, Moss Landing, Santa Cruz, Morro Bay, Monterey and Port San Luis fail on single off-season withheld crab months.
  - A first version that allowed up to 2 null months dropped Jan 2025, the opener month, from the window, so the strict rule was kept.
- **SC weights:** the all-species SC puts essentially all weight on **Shelter Cove**, the only Zone 2 harbor left in the pool and so the only one that shares Crescent City's opener timing. The leave-one-out runs (R2) show what this weighting does to the result.

## 4. Inference

- **Placebo-in-space (SC):** each donor in turn is treated as if it had the closure, and the SC is refitted with the other donors.
  - p = the share of the 19 units (Crescent City + 18 donors) whose post/pre RMSPE ratio is at least Crescent City's (`p_space_ratio`), or whose |11-month % gap| is at least Crescent City's (`p_space_pct`).
  - The smallest attainable p is 1/19 = 0.053 for all-species, and 1/5 = 0.20 for crab (4 donors).
- **Placebo-in-time:**
  - SC: fake events in October 2017–2023, fitted only on earlier data and evaluated on the next 11 months.
  - DiD: each prior window is compared with the mean of the others.
  - p = the share of |placebo| ≥ |actual|, counting the actual. With 8 windows the smallest attainable p is 1/9 = 0.11.
- **What a result needs to clear.** The placebo distributions are wide:
  - SC fake-event gaps run **−84% to +161%**;
  - DiD placebo windows run **−84% to +162%**.
  - Prior-season shocks (the 2019–21 domoic-acid and whale-entanglement delays, the 2023-24 delayed opener) move a crab port's share more than most plausible closure effects would.
  - **Test inversion** (log-symmetric, on the placebo-in-time distributions): a true loss of 30%, 50% or even 75% of the counterfactual would still leave the observed result inside the placebo range (SC p = 0.63, 0.50, 0.25; DiD p = 0.78, 0.44, 0.22).
  - Only a loss above about 84% could be rejected, and even then only at the smallest attainable p (1/8 for SC, 1/9 for DiD).
  - **The permutation tests therefore cannot statistically rule out even a large loss.** The evidence against disappearance is the size of the observed landings (§5, §8), not a test rejection.

## 5. Results

| ID | What | Window | Observed | Counterfactual | Change | p |
|---|---|---|---|---|---|---|
| E1 | Crescent City all-species, SC | during | $18.15M | $17.66M | **+2.8%** | space-ratio 0.53; space-gap 1.00; time 1.00 |
| E1 | same | after (4 mo) | $1.33M | $2.21M | −39.9% | space-ratio 1.00; space-gap 0.37 |
| E2 | Crescent City all-species, DiD vs 18-donor total | during | $18.15M | $16.46M | **+10.3%** | time 1.00 |
| E2 | same | after | $1.33M | $1.66M | −19.8% | time 0.89 |
| E3 | Crescent City crab, SC (4 donors) | during | $16.47M | $15.48M | +6.4% | space-ratio 0.40; space-gap 0.60 |
| E3 | Crescent City crab, DiD vs crab-pool total | during | $16.47M | $8.99M | +83% | time 0.78 |
| E4 | **Shift:** South-OR vs Central-OR, all species | during | $12.94M | $15.55M | **−16.7%** | time 0.67 |
| E5 | **Shift:** South-OR vs Central-OR, crab | during | $10.33M | $8.12M | +27.3% | time 0.89 |
| E6 | Crescent City + South-OR, SC | during | $31.09M | $33.08M | **−6.0%** | space-ratio 0.55; space-gap 0.90 |
| E6 | Crescent City + South-OR, DiD | during | $31.09M | $31.97M | −2.7% | time 1.00 |
| E7 | Crescent City + Trinidad + Humboldt (descriptive) | during | $35.51M | $28.88M (prior mean) | +23% | 2024-25 = 5th of 9 windows (middle) |

**Reading the results.**
- During the closure, Crescent City's landed value tracked its counterfactual (SC +3%, DiD +10%). None of the placebo tests come close to rejecting "no change".
- The Bandon–Brookings unit did not gain share against Central Oregon in all-species value (−17%). Its crab value was +27%, but that sits inside its own placebo range (−82% to +73%).
- The combined Crescent City + South-OR area is within about 6% of its counterfactual. A large shift would show up as Crescent City falling while South-OR rose; neither happened beyond normal year-to-year variation.
- The after-period estimates (−40% SC, −20% DiD) rest on 4 off-season months. December 2025 had no crab in Zones 1–2, because the opener was delayed to at least Jan 15, 2026. They are not informative (§7).

## 6. Robustness (`t41_robustness.csv`; all required checks reported)

| Check | Result |
|---|---|
| **R1 Placebo dates** | Actual gaps rank in the middle or bottom of the placebo distributions (SC p_time 1.00; DiD 1.00; shift all 0.67; shift crab 0.89). Full lists are in `t41_placebos.csv`. |
| **R2 Leave-one-out donors** | Dropping Shelter Cove moves E1 to **+30%** (weights spread over the other donors). For crab, dropping Bodega gives +5% and dropping Shelter Cove +43%. Nothing turns negative. |
| **R3 Value vs pounds** | All-species pounds fall (SC −38%, DiD −55%, shift −63%, combined −54%). But all-species pounds are dominated by bulk species: market squid in the CA donors, Pacific whiting in Central-OR. **Crab pounds** are the volume check that fits a crab port: SC −0.1%; DiD vs crab pool +60%; vs same-zone −12%; vs Humboldt only −42% (p 0.22); shift crab pounds +19%; combined crab pounds −1%. Crescent City crab sold at about $6.5/lb in 2024-25 against about $2.4/lb in 2022-23 ($16.5M / 2.52M lb vs $24.1M / 9.85M lb). It was a low-volume, high-price season coastwide (Central-OR crab pounds were the lowest of the 9 windows), so **value held partly on price.** |
| **R4 Crab vs non-crab** | Crab SC +6%. Non-crab SC −4% (during) and +70% (after). Non-crab DiD −57% (p 0.22); its control is dominated by squid ports. |
| **R5 Excluding withheld/no-record months** | Fit months drop every flagged month (16) and the partial_confidential donors (LA/LB, San Diego Bay) are removed: E1 +3.1%. DiD with flagged months dropped from every window: +24%. |
| **R6 Alternative event end (2025-02)** | SC during Oct–Feb +31%, after Mar–Dec −51%. DiD Oct–Feb +6%. Shift Oct–Feb +3%; shift Mar–Dec −28% (p 0.33). |
| **R7 Brookings species series, ODFW blanks as missing** | Shift crab DiD with `blank_assumed_zero` → null and pairwise deletion: +47% (p 0.78); after +146% (Sep–Dec crab windows are near zero, so this is not informative). Same direction as the blank-as-zero run (E5 +27%). |
| R8 Same-zone control (extra) | Crescent City vs Trinidad + Humboldt + Noyo + Shelter Cove: all species +4%, crab −14%. **Vs Humboldt alone: −15% (all species), −42% (crab pounds), but the 2023-24 placebo window, before the closure, shows the same shortfall (−16% and −45%).** |
| R9 South-OR via SC (cross-state donors) | −17%, matching E4. |
| R10 DiD vs crab-pool total (all species) | +50%. |

## 7. Limits

- **Low power.** Prior seasons swing by −84% to +160% against any counterfactual over an 11-month window. With 7–8 placebo windows and 18 donors, no test here can reject losses below about 84% (§4). The point estimates are near zero, but the statistical uncertainty around them is very wide.
- **Shelter Cove dependence.** The main SC is in effect "Crescent City vs Shelter Cove, scaled". Shelter Cove is a small Zone 2 harbor ($0.46M/yr) with 9 withheld pre months. Leave-one-out (+30%) and the DiD (+10%) give the same sign without it.
- **Pre-existing divergence from Humboldt.** Against its nearest large neighbour, Crescent City's crab share was already lower in 2023-24, the season before the closure, and stayed there in 2024-25. Neither the cause nor the start of that change can be dated from these data. An anticipation effect (Pacific Seafood winding down before it exited) is one possibility but is not documented in the project sources, and the study does not attribute the gap to the closure.
- **Shift test resolution.** South-OR is four harbors. Brookings' own share is not public, so a shift into Brookings smaller than South-OR's normal year-to-year swing (all-species placebo windows −41% to +31%) would not be visible. The test can show there was no large shift into the Bandon–Brookings area. It cannot rule out a modest one.
- **Cross-state comparison (E6, R9).** CDFW reports landing date and landed weight; ODFW reports dealer purchase date and round weight. Value is comparable across the border; pounds are not (round weight exceeds landed weight for gutted product). A landing-vs-purchase-date lag can move value across a month boundary, but rarely across the Oct–Aug window boundary.
- **After period.** It has 4 months, all off-season, and Dec 2025 had no CA Zone 1–2 crab. It says nothing about the 2025-26 season under Ocean Gold, and cannot until CDFW publishes 2026 months.
- **Partly in-sample for the index.** Crescent City helped set the 40 nm threshold. This study tests the outcome (did landings disappear?), not the threshold.
- **Not tested:** vessels, trips, which buyers or processors handled the catch, prices paid, or how ice reached the boats. These are out of scope or not available as public monthly data.

## 8. Plain-language result

During the 11 months without an ice plant, Crescent City's landings **did not disappear**. Its fleet landed about $18.2 million. That is close to what similar harbors' patterns predict (about $16.5–17.7 million) It ranks 6th-highest of Crescent City's 9 Oct–Aug windows since 2016; the three lower windows were seasons hit by delayed openers or domoic acid. Crab volume was 2.5 million pounds, 3rd-lowest of the 9 windows, but this was a low-volume year across the coast.

**There was no detectable shift of landings to the Bandon–Brookings area.** Southern Oregon's share of Oregon landings was, if anything, slightly lower than usual. Together, Crescent City and southern Oregon landed about what they normally would. This fits the documented workaround, ice trucked in from Brookings: Brookings served as the backup *ice supply*, not as the landing port.

**How confident we can be:**
- Confident that landings did not collapse: the dollars and pounds were ordinary for a Crescent City season and moved with its peers.
- The formal tests are weak. Crab seasons swing so much that the data cannot statistically tell a zero effect from a moderate, or even a fairly large, loss. The best single estimate is "about no change" (between −6% and +10% across the main designs).
- In pounds the season was small. It was a low-volume, high-price year across the coast, and Crescent City's crab volume fell further against Humboldt Bay, but that gap had already opened the season before the closure.
- The after-reopening period is too short to judge until 2026 data are published.
