# T3.2b call sheet: facility cells still open after public search (2026-11-14)

The cells come from `outputs/tables/t32b_targets.csv` (the 42 selected) and `outputs/tables/t32b_verification_log.csv`. Calls are listed in order of the top-10 stranded value that depends on them (column `$M at stake`, from the targets table: the largest drop, in $M per year, if the cell turned out to be available).

**How to record an answer.** Write the answer in the blank, with the role of the person you spoke to (no names) and the date. Claude then adds one row per cell to `data/processed/facilities.csv` with `source_type = other`, notes `phone/email with <role>, YYYY-MM-DD`, `as_of_date` = the call date, and confidence high or medium.

**Coding reminders (logged rulings).**
- **Ice:** bulk ice sold to commercial boats counts. Retail bagged ice does not.
- **Hoist:** a dock hoist or crane used to offload catch counts. A travel-lift or launch hoist does not, except at harbors with no moorage.
- **Cold storage:** storage the fleet or its buyers can use for catch counts. A processor that stores only its own product counts only if fishermen can deliver into it. Write down exactly what you're told.
- **No answer, or "don't know":** the cell stays not_found and is logged as "called, unresolved".

**Phone sources.** `[port site]` means the number was taken from the port's or district's own website. Other tags name the listing the number came from; check it against the port's site before calling. "Look up" means no number was captured. Use the main office number on the site named.

---

## Tier 1: more than $60M at stake

### 1. Port of Willapa Harbor: Tokeland and Bay Center ($115–121M)
- **Office:** Port office, 360-942-3422 `[port site, Bay Center Marina page]`. Tokeland harbormaster, 360-942-7693 `[WPPA 2026 guide / PredictWind]`.
- **Tokeland: ice.** Can commercial boats buy bulk ice at the Tokeland dock or nearby now? Who sells it? 
  Answer: ______
- **Tokeland: cold storage.** Is there cold storage at Tokeland that fishermen or buyers can put catch into (the seafood servicing buildings or the nearby plant)? 
  Answer: ______
- **Tokeland: fuel.** Is the diesel fuel dock open and selling to commercial boats now? WPPA 2025/2026 say no; older listings say diesel. 
  Answer: ______
- **Tokeland: hoist.** Is there a crane or hoist on the high dock or work dock used to offload catch? Who runs it? 
  Answer: ______
- **Bay Center: ice, cold storage, hoist.** Same three questions for Bay Center Marina. 
  Answers (ice / cold storage / hoist): ______ / ______ / ______

### 2. Port of Peninsula: Nahcotta ($115–121M)
- **Office:** Port office, 360-665-4547 `[WPPA 2025 guide]`.
- **Ice:** Is bulk ice available to commercial boats at the Nahcotta basin now? Who operates it? 
  Answer: ______
- **Cold storage:** Can fishermen or buyers store catch in cold storage at the port? 
  Answer: ______
- **Hoist:** Is the hoist on the dock used to offload catch, or only to launch and haul boats? 
  Answer: ______

### 3. Port of Ilwaco ($66–121M)
- **Office:** Port office, 360-642-3143 `[port site]`.
- **Cold storage:** Is there cold storage at the port that fishermen or outside buyers can use for catch, as opposed to processors storing their own product? 
  Answer: ______
- **Hoist:** Since the Ilwaco Landing fire, can any commercial boat use a crane to offload (Safe Coast Seafoods or other), or only boats selling to that processor? Is the public fishermen's dock with crane funded or built? 
  Answer: ______

### 4. Port of Chinook ($115–121M for cold storage; ice is a user-added cell)
- **Office:** Port office, 360-777-8797 `[WPPA 2026 guide]`.
- **Ice:** Is the commercial ice machine on pier two running? When did it start selling ice (month and year)? Bulk or bagged? 
  Answer: ______
- **Cold storage:** Is there cold storage at the port that fishermen or buyers can use for catch? 
  Answer: ______

### 5. Westport Marina, Port of Grays Harbor ($66–72M; confirm the new row)
- **Office:** Marina office, 360-533-9562 `[WPPA 2026 guide]`.
- **Hoist:** Boats offload at the processors' docks. Do the processors use cranes or hoists on their docks to offload catch? Is there any port-owned offload crane? 
  Answer: ______

### 6. City of Warrenton marina ($65–67M)
- **Office:** Harbormaster, 503-861-3822 `[PredictWind listing; confirm on the city site]`.
- **Ice:** Can commercial boats buy bulk ice at the Warrenton mooring basin or Hammond now? Who sells it? 
  Answer: ______
- **Cold storage:** Is there cold storage in Warrenton that fishermen or buyers can use for catch? 
  Answer: ______

### 7. City of Depoe Bay harbor ($61M)
- **Office:** Harbormaster, (541) 921-5010 `[city site, moorage agreement]`.
- **Ice:** Is bulk ice available to commercial boats in the harbor now? Who sells it? 
  Answer: ______

### 8. Port of Siuslaw, Florence (ice $60M; cold storage $31M)
- **Office:** Port office, 541-997-3426, port@portofsiuslaw.com `[port site]`.
- **Ice:** Does the port or anyone at the docks sell bulk ice to commercial boats now? Older sources say yes; the 2023 Snapshot and the 2025 rate page say no. 
  Answer: ______
- **Cold storage:** Is there cold storage fishermen or buyers can use for catch? 
  Answer: ______

---

## Tier 2: $30–60M at stake

### 9. Port of Hueneme: optional confirm of the new not_found row ($46.5M)
- **Office:** Commercial fishing contact. Look up on portofhueneme.org (Commercial Fishing page).
- **Cold storage:** Can squid or other fishing landings use any of the on-dock cold storage, or is it all produce and cargo? 
  Answer: ______

### 10. Santa Barbara Waterfront Department ($46.5M)
- **Office:** Waterfront office. Look up on santabarbaraca.gov (Waterfront).
- **Cold storage:** Is there any cold storage at the harbor that commercial fishermen or buyers can use for catch? 
  Answer: ______

### 11. Ventura Port District (cold storage $46.5M; ice $28M)
- **Office:** District office. Look up on venturaharbor.com.
- **Cold storage:** Is there cold storage for catch at the fish pier or the harbor? 
  Answer: ______
- **Ice:** Is bulk ice sold to commercial boats at Ventura Harbor now (not bagged ice at the fuel dock)? Who operates it? 
  Answer: ______

### 12. Channel Islands Harbor ($46.5M)
- **Office:** Harbor Department office. Look up on the County of Ventura harbor site.
- **Cold storage:** Is there cold storage at the harbor that fishermen or buyers can use for catch? 
  Answer: ______

### 13. Port of Anacortes, Cap Sante Marina ($41–52M)
- **Office:** Marina office, (360) 293-0694 `[marinas.com]`.
- **Ice:** Is bulk ice for commercial boats available at the marina or T Dock now (not bagged)? Who sells it? 
  Answer: ______
- **Cold storage:** Is there cold storage near the marina that fishermen or buyers can use for catch? 
  Answer: ______

### 14. La Conner Marina, Port of Skagit ($41–52M)
- **Office:** Marina office. Look up on portofskagit.com.
- **Ice and cold storage:** Same two questions as Anacortes. 
  Answers (ice / cold storage): ______ / ______

### 15. Lineage, Bellingham Roeder port facility ($41–52M)
- **Office:** Facility office, (360) 733-1640 `[operator site, onelineage.com]`.
- **Ice:** Does the former Bellingham Cold Storage ice plant still sell ice to fishing boats? Bulk ice at the dock? 
  Answer: ______

### 16. Blaine Harbor, Port of Bellingham ($40M)
- **Office:** Blaine Harbor office. Look up on portofbellingham.com.
- **Ice and cold storage:** Is bulk ice available to commercial boats at Blaine Harbor? Is there cold storage fishermen or buyers can use? 
  Answers (ice / cold storage): ______ / ______

### 17. Marina del Rey ($39M) and 18. King Harbor, Redondo Beach ($39M)
- **Office:** Harbor offices. Look up on the LA County Beaches & Harbors and City of Redondo Beach sites.
- **Cold storage:** Is there cold storage at the harbor that commercial fishermen or buyers can use for catch? 
  Answers (MdR / Redondo): ______ / ______

### 19. Port of Bandon ($30–37M)
- **Office:** Harbor office, (541) 347-3206, info@portofbandon.com `[port site]`.
- **Cold storage:** Is there cold storage at the port that fishermen or buyers can use for catch? 
  Answer: ______

### 20. Port of Port Townsend ($36M)
- **Office:** Boat Haven office. Look up on portofpt.com.
- **Ice:** Is bulk ice for commercial boats available (not bagged)? 
  Answer: ______
- **Cold storage:** Is there cold storage fishermen or buyers can use? 
  Answer: ______

### 21. Salmon Harbor, Winchester Bay ($31–33M)
- **Office:** Marina office, 541-271-3407 ext. 301 `[listing pointing to the Douglas County site]`.
- **Cold storage:** Is there cold storage at Salmon Harbor that fishermen or buyers can use for catch? 
  Answer: ______

### 22. Port of Port Orford ($30M)
- **Office:** Port office, 541-332-7121 `[OR Blue Book]`.
- **Cold storage:** Apart from the planned seafood hub, is there cold storage on the dock now that fishermen or buyers can use? 
  Answer: ______

### 23. Port of Gold Beach ($30M)
- **Office:** Port office, 541-247-6269 `[OR Blue Book]`. Staff mobile, 541-425-1569 `[port site]`.
- **Cold storage:** Does the fish buyer or processor on the commercial dock have cold storage that fishermen can deliver into? 
  Answer: ______

---

## Tier 3: under $30M at stake

### 24. City of Newport Beach harbor ($27M)
- **Office:** Harbor Department. Look up on newportbeachca.gov.
- **Ice:** Is bulk ice available to commercial boats (dory fleet or others) in the harbor? 
  Answer: ______

### 25. Noyo Harbor District: opening date only ($7.5M)
- **Office:** District office, (707) 964-4719 `[district packet]`.
- **Ice:** In what month did the new icehouse start selling ice to boats? The February 12, 2026 packet says the office "will begin to operate" it. Is it running now? 
  Answer: ______

---

## Cells not on this sheet
- **Resolved from public sources** (new rows added; see the verification log): Westport hoist (available, low; call #5 confirms it) and Port Hueneme cold storage (not_found, low; call #9 is optional).
- **Not selected for checking** (target ranks 41–97, plus Bandon and Gold Beach ice): listed in `t32b_targets.csv` with `selected_for_check` blank. Out of scope for T3.2b.
