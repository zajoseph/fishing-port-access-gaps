# Port crosswalk (T2.1)

As of 2026-11-13. Built by `src/portgaps/clean/write_crosswalk_t21.py` from `data/processed/ports.csv`, `outputs/tables/t21_units.csv` and `outputs/tables/t21_coverage.csv`.

**How to read it.** Each of the 58 inventory harbors (`port_id`) maps to:
- the agency port code(s) its landings are reported under;
- the PacFIN port code and **PacFIN port group**, from PacFIN's public port hierarchy (`pc_tree.txt`, https://pacfin.psmfc.org/pacfin_pub/data_rpts_pub/code_lists/pc_tree.txt, read 2026-11-13). A `~` marks an inferred assignment: a CDFW code with no PacFIN code of its own, placed in the PacFIN "Other ... County Ports" code for its county;
- the report name used in the panel (CDFW MFDE port name, ODFW FTR205 table, or PacFIN CRAB002 group);
- the **finest level the monthly panel has for it**, and the panel `unit_id`(s) that carry it (`data/processed/landings_monthly.csv`);
- the NOAA FOSS annual "top US ports" name, where one exists (annual cross-check only; see `outputs/tables/t21_annual_crosscheck.csv`).

**Unit types** (`unit_type` in the panel):
- `harbor`: the unit is this one harbor. CA multi-code harbors (Humboldt Bay, LA/LB, San Diego Bay) are the sum of their CDFW codes.
- `code_group`: one agency port code that covers several inventory harbors (ODFW Astoria = PacFIN AST, covers Astoria + Warrenton).
- `agency_group`: an agency's multi-port reporting group (ODFW combined-port tables; PacFIN port groups for WA). Values are the group total and are **never split** across harbors here.
- `state_group`: not used (no harbor relies on a statewide figure).

**Shared codes and groups.**
- AST (Astoria + Warrenton): ODFW "Astoria" table, 2016-2025. ODFW gives no Warrenton-only figure.
- LWC (Ilwaco + Chinook): no public all-species monthly data. Panel unit = PacFIN CRAB002 group **CLW**, Dungeness crab only. **Evidence for Ilwaco in CLW:** PacFIN `pc_tree.txt` lists LWC ILWACO/CHINOOK under CLW COLUMBIA RIVER PORTS (WASHINGTON), with OCR (other Columbia River ports) as the only other member. Consistent with this, FOSS annual "Ilwaco-Chinook" value is 0.82-1.05 x PacFIN ALL005 CLW (2016-2024) (`outputs/tables/t21_spotchecks.csv`).
- WLB (Tokeland + Bay Center + Nahcotta): in PacFIN group CWA with Westport and La Push; FOSS has an annual "Willapa Bay" row.
- ODFW 2025 break: tables were regrouped in 2025. Charleston moves into "Florence-Winchester Bay-Charleston"; Newport into "Depoe Bay-Newport-Waldport-Yachats"; Gold Beach-Brookings merges with Bandon-Port Orford; Garibaldi's group adds Netarts to Siletz Bay (Depoe Bay leaves it). Each composition has its own `unit_id`; no group is split by assumption.
- ODFW "Columbia River" table (in-river landings) maps to no inventory harbor and is not in the panel. It is used only in the statewide-sum check.

**WA.** No public port-level or all-species monthly landings. The finest monthly level is the PacFIN port group, for Dungeness crab only. All-species values exist only annually: PacFIN ALL005 by group, and FOSS by major port where listed.

| port_id | harbor | agency code(s) | PacFIN code | PacFIN group | report name in panel | finest monthly level | panel unit_id(s) | FOSS annual port |
|---|---|---|---|---|---|---|---|---|
| CA-crescent-city | Crescent City | 201 Crescent City | CRS | CCA | MFDE Port = CRESCENT CITY | harbor (all species) | CA-crescent-city | Crescent City |
| CA-trinidad | Trinidad | 231 Trinidad | TRN | ERA | MFDE Port = TRINIDAD | harbor (all species) | CA-trinidad | Trinidad (2023 only) |
| CA-humboldt-bay | Humboldt Bay (Eureka / Fields Landing / King Salmon) | 220 Eureka;217 Fields Landing;219 Humboldt Bay;246 King Salmon;212 Arcata | ERK; FLN; ~OHB (Humboldt Bay, King Salmon, Arcata) | ERA | MFDE Port = EUREKA; FIELDS LANDING; HUMBOLDT BAY; KING SALMON; ARCATA | harbor (all species) | CA-humboldt-bay | Eureka |
| CA-shelter-cove | Shelter Cove | 215 Shelter Cove | ~OHB | ERA | MFDE Port = SHELTER COVE | harbor (all species) | CA-shelter-cove | - |
| CA-noyo-harbor | Noyo Harbor (Fort Bragg) | 223 Fort Bragg | BRG | BGA | MFDE Port = FORT BRAGG | harbor (all species) | CA-noyo-harbor | Fort Bragg |
| CA-point-arena | Point Arena (Arena Cove) | 213 Point Arena | ARE | BGA | MFDE Port = POINT ARENA | harbor (all species) | CA-point-arena | - |
| CA-bodega-bay | Bodega Bay (Spud Point) | 473 Bodega Bay | BDG | BDA | MFDE Port = BODEGA BAY | harbor (all species) | CA-bodega-bay | Bodega Bay |
| CA-san-francisco | San Francisco (Fisherman's Wharf / Pier 45) | 440 San Francisco | SF | SFA | MFDE Port = SAN FRANCISCO | harbor (all species) | CA-san-francisco | San Francisco Area (group) |
| CA-vallejo | Vallejo | 453 Vallejo | ~OSF | SFA | MFDE Port = VALLEJO | harbor (all species) | CA-vallejo | San Francisco Area (group) |
| CA-berkeley | Berkeley | 472 Berkeley | BKL | SFA | MFDE Port = BERKELEY | harbor (all species) | CA-berkeley | San Francisco Area (group) |
| CA-pillar-point | Pillar Point Harbor (Princeton / Half Moon Bay) | 452 Princeton-Half Moon | PRN | SFA | MFDE Port = PRINCETON-HALF MOON | harbor (all species) | CA-pillar-point | Princeton-Half Moon Bay |
| CA-santa-cruz | Santa Cruz | 593 Santa Cruz | CRZ | MNA | MFDE Port = SANTA CRUZ | harbor (all species) | CA-santa-cruz | - |
| CA-moss-landing | Moss Landing | 592 Moss Landing | MOS | MNA | MFDE Port = MOSS LANDING | harbor (all species) | CA-moss-landing | Moss Landing |
| CA-monterey | Monterey | 550 Monterey | MNT | MNA | MFDE Port = MONTEREY | harbor (all species) | CA-monterey | Monterey |
| CA-morro-bay | Morro Bay | 606 Morro Bay | MRO | MRA | MFDE Port = MORRO BAY | harbor (all species) | CA-morro-bay | Morro Bay |
| CA-port-san-luis | Port San Luis (Avila Beach) | 602 Avila/Port San Luis | AVL | MRA | MFDE Port = AVILA/PORT SAN LUIS | harbor (all species) | CA-port-san-luis | Avila Beach (2023 only) |
| CA-santa-barbara | Santa Barbara Harbor | 611 Santa Barbara Harbor | SB | SBA | MFDE Port = SANTA BARBARA HARBOR | harbor (all species) | CA-santa-barbara | Santa Barbara |
| CA-ventura | Ventura Harbor | 613 Ventura | VEN | SBA | MFDE Port = VENTURA | harbor (all species) | CA-ventura | Port Hueneme-Oxnard-Ventura (group) |
| CA-channel-islands | Channel Islands Harbor (Oxnard) | 608 Oxnard | OXN | SBA | MFDE Port = OXNARD | harbor (all species) | CA-channel-islands | Port Hueneme-Oxnard-Ventura (group) |
| CA-port-hueneme | Port Hueneme | 605 Port Hueneme | HNM | SBA | MFDE Port = PORT HUENEME | harbor (all species) | CA-port-hueneme | Port Hueneme-Oxnard-Ventura (group) |
| CA-marina-del-rey | Marina del Rey | 776 Marina Del Rey | ~OLA | LAA | MFDE Port = MARINA DEL REY | harbor (all species) | CA-marina-del-rey | - |
| CA-redondo-beach | Redondo Beach (King Harbor) | 742 Redondo Beach | ~OLA | LAA | MFDE Port = REDONDO BEACH | harbor (all species) | CA-redondo-beach | - |
| CA-los-angeles-long-beach | Los Angeles / Long Beach Harbor (Fish Harbor, San Pedro) | 745 Terminal Island;770 San Pedro;743 Long Beach;744 Los Angeles;746 Wilmington | TRM; SP; LGB; WLM; ~OLA (Los Angeles 744) | LAA | MFDE Port = TERMINAL ISLAND; SAN PEDRO; LONG BEACH; LOS ANGELES; WILMINGTON | harbor (all species) | CA-los-angeles-long-beach | Los Angeles |
| CA-huntington-harbour | Huntington Harbour | 768 Huntington Beach | ~OLA | LAA | MFDE Port = HUNTINGTON BEACH | harbor (all species) | CA-huntington-harbour | - |
| CA-newport-beach | Newport Beach | 748 Newport Beach | NWB | LAA | MFDE Port = NEWPORT BEACH | harbor (all species) | CA-newport-beach | - |
| CA-avalon | Avalon (Santa Catalina Island) | 741 Avalon | ~OLA | LAA | MFDE Port = AVALON | harbor (all species) | CA-avalon | - |
| CA-dana-point | Dana Point Harbor | 767 Dana Point | DNA | LAA | MFDE Port = DANA POINT | harbor (all species) | CA-dana-point | Dana Point (2023 only) |
| CA-oceanside | Oceanside Harbor | 883 Oceanside | OCN | SDA | MFDE Port = OCEANSIDE | harbor (all species) | CA-oceanside | Oceanside (2023 only) |
| CA-mission-bay | Mission Bay | 869 Mission Bay | ~OSD | SDA | MFDE Port = MISSION BAY | harbor (all species) | CA-mission-bay | - |
| CA-san-diego-bay | San Diego Bay (Tuna Harbor / Driscoll's Wharf) | 880 San Diego;881 Point Loma | SD; ~OSD (Point Loma) | SDA | MFDE Port = SAN DIEGO; POINT LOMA | harbor (all species) | CA-san-diego-bay | San Diego |
| OR-astoria | Astoria (Port of Astoria West/East Basins) | (ODFW tables at right) | AST (shared) | CLO | ODFW FTR205 table(s): Astoria (2016-2025) | code_group (all species) | OR-ODFW-astoria | Astoria |
| OR-warrenton | Warrenton (City Mooring Basin; Hammond Marina) | (ODFW tables at right) | AST (shared) | CLO | ODFW FTR205 table(s): Astoria (2016-2025) | code_group (all species) | OR-ODFW-astoria | Astoria |
| OR-garibaldi | Garibaldi (Port of Garibaldi) | (ODFW tables at right) | TLL | TLA | ODFW FTR205 table(s): Gearhart-Seaside-Cannon Beach-Nehalem Bay-Garibaldi (2016-2024) / Gearhart-Cannon Beach-Nehalem Bay-Garibaldi-Netarts-Sand Lake-Pacific City-Salmon River-Siletz Bay (2025) | agency_group (all species) | OR-ODFW-gearhart-garibaldi; OR-ODFW-gearhart-siletz-bay-2025 | Tillamook |
| OR-depoe-bay | Depoe Bay (City harbor) | (ODFW tables at right) | DPO | NPA | ODFW FTR205 table(s): Netarts-(Sand Lake)-Pacific City-Siletz Bay-Salmon River-Depoe Bay (2016-2024) / Depoe Bay-Newport-Waldport-Yachats (2025) | agency_group (all species) | OR-ODFW-netarts-depoe-bay; OR-ODFW-depoe-bay-yachats-2025 | - |
| OR-newport | Newport (Port of Newport commercial marina) | (ODFW tables at right) | NEW | NPA | ODFW FTR205 table(s): Newport (2016-2024) / Depoe Bay-Newport-Waldport-Yachats (2025) | harbor then agency_group (all species) | OR-newport; OR-ODFW-depoe-bay-yachats-2025 | Newport |
| OR-florence | Florence (Port of Siuslaw) | (ODFW tables at right) | FLR | CBA | ODFW FTR205 table(s): Waldport-Yachats-Florence-Winchester Bay (2016-2024) / Florence-Winchester Bay-Charleston (2025) | agency_group (all species) | OR-ODFW-waldport-winchester-bay; OR-ODFW-florence-charleston-2025 | - |
| OR-winchester-bay | Winchester Bay (Salmon Harbor, Douglas County) | (ODFW tables at right) | WIN | CBA | ODFW FTR205 table(s): Waldport-Yachats-Florence-Winchester Bay (2016-2024) / Florence-Winchester Bay-Charleston (2025) | agency_group (all species) | OR-ODFW-waldport-winchester-bay; OR-ODFW-florence-charleston-2025 | Winchester Bay |
| OR-charleston | Charleston (Port of Coos Bay Charleston Marina) | (ODFW tables at right) | COS | CBA | ODFW FTR205 table(s): Charleston (2016-2024) / Florence-Winchester Bay-Charleston (2025) | harbor then agency_group (all species) | OR-charleston; OR-ODFW-florence-charleston-2025 | Coos Bay-Charleston |
| OR-bandon | Bandon (Port of Bandon) | (ODFW tables at right) | BDN | CBA | ODFW FTR205 table(s): Bandon-Port Orford (2016-2024) / Bandon-Port Orford-Gold Beach-Brookings (2025) | agency_group (all species) | OR-ODFW-bandon-port-orford; OR-ODFW-bandon-brookings-2025 | - |
| OR-port-orford | Port Orford (Port of Port Orford dolly dock) | (ODFW tables at right) | ORF | BRA | ODFW FTR205 table(s): Bandon-Port Orford (2016-2024) / Bandon-Port Orford-Gold Beach-Brookings (2025) | agency_group (all species) | OR-ODFW-bandon-port-orford; OR-ODFW-bandon-brookings-2025 | Port Orford |
| OR-gold-beach | Gold Beach (Port of Gold Beach) | (ODFW tables at right) | GLD | BRA | ODFW FTR205 table(s): Gold Beach-Brookings (2016-2024) / Bandon-Port Orford-Gold Beach-Brookings (2025) | agency_group (all species) | OR-ODFW-gold-beach-brookings; OR-ODFW-bandon-brookings-2025 | - |
| OR-brookings | Brookings (Port of Brookings Harbor) | (ODFW tables at right) | BRK | BRA | ODFW FTR205 table(s): Gold Beach-Brookings (2016-2024) / Bandon-Port Orford-Gold Beach-Brookings (2025) | agency_group (all species) | OR-ODFW-gold-beach-brookings; OR-ODFW-bandon-brookings-2025 | Brookings |
| WA-ilwaco | Ilwaco (Port of Ilwaco) | none public (WDFW) | LWC (shared Ilwaco/Chinook) | CLW | PacFIN CRAB002 group CLW | agency_group (Dungeness crab only) | WA-PACFIN-CLW | Ilwaco-Chinook |
| WA-chinook | Chinook (Port of Chinook) | none public (WDFW) | LWC (shared Ilwaco/Chinook) | CLW | PacFIN CRAB002 group CLW | agency_group (Dungeness crab only) | WA-PACFIN-CLW | Ilwaco-Chinook |
| WA-tokeland | Tokeland (Port of Willapa Harbor marina) | none public (WDFW) | WLB (shared) | CWA | PacFIN CRAB002 group CWA | agency_group (Dungeness crab only) | WA-PACFIN-CWA | Willapa Bay |
| WA-bay-center | Bay Center (Port of Willapa Harbor marina) | none public (WDFW) | WLB (shared) | CWA | PacFIN CRAB002 group CWA | agency_group (Dungeness crab only) | WA-PACFIN-CWA | Willapa Bay |
| WA-nahcotta | Nahcotta (Port of Peninsula) | none public (WDFW) | WLB (shared) | CWA | PacFIN CRAB002 group CWA | agency_group (Dungeness crab only) | WA-PACFIN-CWA | Willapa Bay |
| WA-westport | Westport (Port of Grays Harbor Westport Marina) | none public (WDFW) | WPT | CWA | PacFIN CRAB002 group CWA | agency_group (Dungeness crab only) | WA-PACFIN-CWA | Westport |
| WA-la-push | La Push (Quileute Harbor Marina) | none public (WDFW) | LAP | CWA | PacFIN CRAB002 group CWA | agency_group (Dungeness crab only) | WA-PACFIN-CWA | La Push |
| WA-neah-bay | Neah Bay (Makah Marina / Port of Neah Bay) | none public (WDFW) | NEA | NPS | PacFIN CRAB002 group NPS | agency_group (Dungeness crab only) | WA-PACFIN-NPS | Neah Bay |
| WA-port-angeles | Port Angeles (Port Angeles Boat Haven) | none public (WDFW) | PAG | NPS | PacFIN CRAB002 group NPS | agency_group (Dungeness crab only) | WA-PACFIN-NPS | Port Angeles (2019, 2023) |
| WA-port-townsend | Port Townsend (Boat Haven, Port of Port Townsend) | none public (WDFW) | TNS | NPS | PacFIN CRAB002 group NPS | agency_group (Dungeness crab only) | WA-PACFIN-NPS | Port Townsend (2019, 2023) |
| WA-seattle | Seattle (Fishermen's Terminal, Salmon Bay) | none public (WDFW) | SEA | SPS | PacFIN CRAB002 group SPS | agency_group (Dungeness crab only) | WA-PACFIN-SPS | Seattle |
| WA-everett | Everett (Port of Everett Marina) | none public (WDFW) | EVR | SPS | PacFIN CRAB002 group SPS | agency_group (Dungeness crab only) | WA-PACFIN-SPS | Everett (2016-2019) |
| WA-la-conner | La Conner (Port of Skagit La Conner Marina) | none public (WDFW) | LAC | NPS | PacFIN CRAB002 group NPS | agency_group (Dungeness crab only) | WA-PACFIN-NPS | Anacortes-La Conner (group) |
| WA-anacortes | Anacortes (Port of Anacortes Cap Sante Marina) | none public (WDFW) | ANA | NPS | PacFIN CRAB002 group NPS | agency_group (Dungeness crab only) | WA-PACFIN-NPS | Anacortes-La Conner (group) |
| WA-bellingham | Bellingham (Port of Bellingham Squalicum Harbor) | none public (WDFW) | BLL | NPS | PacFIN CRAB002 group NPS | agency_group (Dungeness crab only) | WA-PACFIN-NPS | Bellingham |
| WA-blaine | Blaine (Port of Bellingham Blaine Harbor) | none public (WDFW) | BLN | NPS | PacFIN CRAB002 group NPS | agency_group (Dungeness crab only) | WA-PACFIN-NPS | Blaine |
