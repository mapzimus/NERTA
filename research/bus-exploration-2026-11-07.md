# Bus exploration

Research notes, November 7, 2026. Advice only. Nothing on the map, the posters or the code has changed. This builds on `research/bus-plan-draft.md` and doesn't repeat its tables.

## 1. Summary

1. **Recommendation:** keep the main map bus-free. Put buses on a separate NERTA surface map after the regional map. Later, give each line poster a small "Frequent bus" panel.
2. "Showing buses" is still on the Rejected list, and a faint bus layer was already tried and removed in passes 18 and 19. Any main-map option needs Max to reopen it first.
3. Of today's 25 frequent routes, 10 run where NERTA already built rail: the 28, 39, 57, 77 and all six Silver Line routes. 12 are real gaps, led by Harvard St (66), Mass Ave (1), Columbia Rd, and Chelsea and inland Revere (111, 116).
4. Real bus projects worth a stripe: Arsenal St and Western Ave (70) and Columbus Ave Phase 2. Two lanes already run (solid): Mt Auburn St and Roslindale. Blue Hill Ave is real, but it sits under the Orange dash. Every tram idea is dashed and invented.
5. The official November 2024 Red Line poster lists no bus routes. Bus numbers on NERTA posters would be Max's own idea, not a copy of the MBTA's.

---

## 2. Findings

### Sources

"Read" means I read the page or document text. "Snippet" means I saw only a search-result summary, so it's weaker.

| Short name | What it is | How seen |
|---|---|---|
| **MBTA API** | MBTA V3 API, pulled November 7, 2026: `/routes`, `/route_patterns`, and bus stops within about 200 m of each hub | Read |
| **BNRD report** | MBTA, Bus Network Redesign Final Report, May 25, 2023 (cdn.mbta.com) | Read |
| **BPV** | MBTA, "Bus Priority Vision", October 2023, 26 corridors (cdn.mbta.com) | Read |
| **SB 2023** | Streetsblog Mass, "Here's the MBTA's bus lane wishlist…", Oct 23, 2023 | Read |
| **SB Apr 2024** | Streetsblog Mass, "Bus network redesign shows signs of life", Apr 11, 2024 | Read |
| **SB Sep 2024** | Streetsblog Mass, "New T map highlights new frequent service bus routes", Sep 11, 2024 | Read |
| **SB 2025** | Streetsblog Mass, "Another bus lane bites the dust", Jul 8, 2025 | Read |
| **SB Jul 2026** | Streetsblog Mass, "Redesigning the redesign…", Jul 3, 2026 | Read |
| **SB Sep 2026** | Streetsblog Mass, "What's changed… in Boston's new Blue Hill Avenue busway plan", Sep 9, 2026 | Read |
| **CB 2022** | CommonWealth Beacon, "MBTA unveils redesigned bus redesign", Oct 2022 | Read |
| **Boston.com 2026** | Boston.com, Columbus Ave bus lane, Oct 14, 2026 | Read |
| **MBTA Arsenal** | mbta.com, Arsenal Street Transit Priority Corridor Project page | Read |
| **WP key / WP list / WP streetcar** | Wikipedia: MBTA key bus routes; List of MBTA bus routes; Boston-area streetcar lines | Read |
| **Metro 2009** | Metro Magazine, "MBTA updates system maps, signage", Sep 21, 2009 | Read |
| **Ref poster / Ref GL map** | `reference/private/chat_03.jpg` (official Red Line poster, Nov 2024) and `chat_02.png` (older Green Line station map) | Seen directly |
| Snippet sources | Boston Globe (Oct 5, 2026, Columbus Ave); Axios (Oct 6, 2026, Blue Hill Ave); Boston.gov and SB Feb 2026 (Rutherford Ave); SB Jun 2026 (Arsenal St); Cambridge city page and SB 2019 (Mt Auburn St); Boston.gov and MAPC (Roslindale lanes); Wikipedia trolleybus page and Watertown News (Mt Auburn St streetcar) | Snippet |

The MBTA API, the BNRD report and the BPV all come from the MBTA. Under the data rule they count as **one** source family, the same way the draft treated the API and GTFS.

### 2a. Key facts

| # | Claim | Source 1 | Source 2 | Agree or differ | Status |
|---|---|---|---|---|---|
| 1 | 150 bus routes today. 25 are labeled "Frequent Bus": 19 regular routes plus 6 Silver Line routes | MBTA API | SB Jul 2026 slide: "21 frequent routes" | **Differ.** 19 regular routes plus 2 Silver Line groups (Waterfront, Washington St) would make 21. That's my arithmetic, not a source | Count unverified |
| 2 | 14 of the 25 frequent routes are confirmed outside the MBTA: 104, 109, 110 and 116 since December 2024; 1, 15, 22, 23 and 28 since August 24, 2025; 32, 66, 71, 73 and 77 since December 14, 2025 | MBTA API | SB Sep 2024 (Phase 1 routes) and WP key (2025 dates) | Agree. SB Jul 2026 also named the 31 for summer 2025 but didn't confirm it ran | Two for those 14. The other 11 rest on MBTA data alone |
| 3 | The redesign plan has 30 high-frequency routes, up from 15. The MBTA Board approved it November 17, 2022 | BNRD report | CB 2022 | Agree on 30. CB expected a December vote; the report says November 17 | Two |
| 4 | The plan named frequent routes with a "T" prefix (T22, T70 and so on). The MBTA won't use it on public signs | BNRD report and BPV | SB Apr 2024 (spokesperson quote) | Agree | Two |
| 5 | 26 of the plan's 30 frequent numbers found: T1, T7, T8, T9, T12, T15, T16, T22, T23, T28, T31, T39, T47, T57, T66, T70, T71, T73, T77, T96, T101, T104, T109, T110, T111, T116 | BPV | BNRD report (both MBTA) | Agree | One (MBTA only). 4 numbers still missing |
| 6 | **Draft note A resolved.** The 9 still runs Copley to City Point and the 57 Watertown Yard to Kenmore. The odd stops were school-day trips (9 via Longwood) and early-morning trips (57 from Haymarket) | MBTA API `route_patterns` (main pattern typicality 1, odd ones 3) | WP list termini | Agree | Two |
| 7 | The Bus Priority Vision lists 26 corridors, covering 10 to 15% of the bus network and 80% of riders | BPV | SB 2023 names the same corridors: Mass Ave, Brookline Ave, Hyde Park Ave, Western Ave and Arsenal St, Harvard St, Columbia Rd, Meridian St, 2nd St, Berkeley St, Blue Hill Ave | Agree on the corridors. SB gives no mileage | Two for the corridor list |
| 8 | Columbus Ave: center bus lanes from Walnut Ave to Jackson Sq opened in 2021 (22, 29, 44). Phase 2, Jackson Sq to Ruggles, is now curbside, with work starting in 2027 | Boston.com 2026 | Globe, Oct 5, 2026 (snippet) | Agree | Two |
| 9 | Blue Hill Ave: a center-running busway from Grove Hall to Mattapan Sq for the 28 and 22. Congress earmarked $80M, tied to center running, and the state pledged $51M. There's no construction date | SB Sep 2026 | Axios, Oct 2026 (snippet): the center lanes stay, with strong local opposition | Agree | Two |
| 10 | Rutherford Ave and Sullivan Sq: the city reopened the busway design (side or center), showed a pre-25% design in May 2026, and the project is worth about $200M | Boston.gov project page (snippet) | SB Feb 2026 (snippet) | Agree | Two, both snippets |
| 11 | Arsenal St: a 1.8-mile bus priority corridor from Greenough Blvd to Watertown Sq. The plan makes the 70 frequent. Planning runs mid-2026 to early 2027 | MBTA Arsenal | SB Jun 2026 (snippet) | Agree. SB corrected its rider count: about 5,000 a day on the whole route, about 2,000 on Arsenal St alone | Two |
| 12 | The northbound North Washington St bus lane (92, 93, 111) was paved over in July 2025 and won't be restored. About 14,900 daily riders use these routes, two-thirds of them on the 111 | SB 2025 | none found | — | One, unverified |
| 13 | Mt Auburn St bus lanes (71, 73) have been permanent since 2019, from Cottage St in Watertown to Fresh Pond Pkwy | Cambridge city page (snippet) | SB 2019 (snippet) | Agree | Two, both snippets |
| 14 | Washington St lanes, Roslindale Village to Forest Hills: permanent since June 2018 and expanded in 2021 and 2023. They carry 10 routes and about 15,000 weekday riders | Boston.gov (snippet) | MAPC case study (snippet). The MBTA API finds the same 10 routes at Roslindale Village | Agree | Two |
| 15 | The official MBTA map has drawn frequent buses as thinner lines since 2014, and as lighter yellow lines on the fall 2024 map | SB Sep 2024 | WP key (key routes as thinner lines on the 2014 map) | Agree on thin lines. Only SB names the color | Two for thin lines, One for color |
| 16 | The official Red Line poster (Nov 2024) shows no bus numbers. It has rail and SL pills only, plus "All buses and Silver Line are accessible." The MBTA puts bus routes on separate key-bus and neighborhood maps at stations | Ref poster | Metro 2009 | Agree | Two |
| 17 | An older MBTA Green Line station map draws the 39 bus as a dashed line where E service to Arborway was suspended | Ref GL map | none | — | One |
| 18 | The 71 and 73 were streetcars until September 1958, then trackless trolleys until March 2022 | WP streetcar | WP trolleybus page and Watertown News (snippets) | Agree. The end date varies by a day (March 12 or 13) | Two, but weak: two Wikipedia pages |
| 19 | A faint bus layer was tried on the main map: unnumbered crosstown buses, Forest Hills to Mattapan, Medford to Davis, Needham to West Roxbury, Roslindale to Readville. Max removed it the next pass | `docs/history/decision_log_all_passes.md`, passes 18 and 19 | `docs/DECISIONS.md` Rejected list: "Showing buses" | Agree | Two (project records) |

### 2b. Today's frequent routes against NERTA

This is my judgment, from `lines()` in `make_tmap.py` and each route's corridor.

| Verdict | Routes | What NERTA does there |
|---|---|---|
| **Replaced** (10) | 28, 39, 57, 77, SL1, SL2, SL3, SL4, SL5, SLW | Orange dash on Blue Hill Ave; Green E stripe to Forest Hills; Green A stripe to Watertown; Red stripe to Arlington Heights; the Silver Logan shuttle, Yellow, and Cyan in the Seaport; the Orange dash on Washington St |
| **Partly replaced** (3) | 32, 104, 109 | Orange stripe to Hyde Park; Yellow from Airport to Everett Sq; Yellow from Everett to Sullivan, plus the Green dash from Union Sq to Harvard |
| **Gap** (12) | 1, 9, 15, 22, 23, 31, 66, 71, 73, 110, 111, 116 | Rail only crosses these corridors. They stay as buses in a NERTA future |

The plan's frequent routes that aren't frequent yet are the T7, T8, T12, T16, T47, T70, T96 and T101. Of those, the **70** (Western Ave and Arsenal St) and the **16** (Morton St and Columbia Rd) are gaps. The others run where Yellow, Cyan or the Green Line Extension already go. The 70 is Two (row 11). The rest are One (MBTA only).

### 2c. Hubs beyond the draft's 25

These are NERTA stations the draft didn't cover. Routes come from the MBTA API (bus stops within about 200 m), counting only **typical** trips. Frequent routes are in bold. "Verified" means the route ends there in both the MBTA API and WP list.

| Hub (NERTA line) | Routes | Evidence |
|---|---|---|
| Everett Sq (Yellow) | **104, 109, 110**, 97, 112 | Partly verified: SB Sep 2024 puts the 104, 109 and 110 in Everett. The square itself is API only |
| Linden Sq (Orange dash) | **109**, 108, 119, 411, 426, 428, 429 | Verified for 108 and 109 |
| Watertown (Green A) | **57** (Yard), **71**, 52, 59, 70, 504 | Verified for 59 and 71 |
| Newton Corner (Green A) | **57**, 52, 504; 553, 554, 556, 558 end here | 57, 52, 504: API only. 553 to 558: WP list only. Unverified |
| Waltham (Red stripe) | 61, 70, 505, 553, 554, 556, 558 | Verified for 61, 70, 505. The 70 is planned frequent |
| Arlington Heights (Red stripe) | **77**, 62 | Verified for 77 |
| Grove Hall (Orange dash) | **23, 28**, 14, 19, 45 | Partly verified: SB Sep 2026 has the 28 on the Grove Hall busway |
| Roslindale Village (Orange stripe) | 14, 30, 34, 34E, 35, 36, 37, 40, 50, 51 | Two: the API and Boston.gov name the same 10 routes |
| Hyde Park (Orange stripe) | **32**, 33, 50 | Partly verified: 32 and 50 end at Cleary Sq per WP list |
| Central Sq, Lynn (Blue) | 426, 429, 435, 436, 439, 441, 442, 455, 456 | Verified for 426, 429, 435, 436, 456 (more than the draft found) |
| Uphams Corner, Talbot Ave (Indigo) | **15**, 41; **22** | Talbot Ave: Two (WP: 22 "via Talbot Avenue"). Uphams: API only |
| Coolidge Corner, Brookline Village (Green C, D) | **66**; **66**, 60, 65 | MBTA only (API and BPV). Unverified |

The API didn't find Bellingham Sq, Wyoma Sq or Blue Hill Ave by name, and Morton St station picks up only the 21 and 26. The 31's stops on Morton St are farther than 200 m from the station.

**Data trap: filter by typical trips.** A plain stop-to-route query brings in rare trips. At Haymarket it adds the 15, 39, 57 and 116 (early-morning trips only) and a dozen rail shuttles. At Kenmore it adds the 9 (school days only). At Hyde Park it adds the 39. Any poster list must keep only `route_patterns` with typicality 1 or 2.

---

## 3. Ways to show buses, ranked

**1. A separate NERTA surface map (recommended).**
- **What:** today's frequent network, the real busways striped, tram ideas dashed, and NERTA rail faded behind as context. It's its own sheet, so the main map stays as posted.
- **Effort:** about 12 to 16 hours over 3 or 4 sessions. That covers the data pull (1 hour), a new script reusing `station_kit.py` and `lines()`, layout, and the check pass. It fits Max's order: the regional map first, then buses.
- **Clutter:** none on the main map. The surface sheet can carry route numbers in small level shields at corridor ends, never along the line, so nothing is tilted.
- **Color:** the MBTA draws buses in yellow (row 15), but Yellow is NERTA's ring line. Max's pale pink idea works. I checked it against every NERTA color with the house test (CIEDE2000 above 15): `#f7b8cf` passes, closest to commuter purple at 17.2. `#f4a6c0` passes narrowly at 15.8. A deeper rose, `#e87ea1`, fails against commuter purple at 14.7.

**2. A "Frequent bus" panel on each line poster.**
- **What:** a small table next to the Key, listing hub stops and their frequent routes, such as `Nubian 1 15 23 28 66`. Frequent routes only, typical trips only, and no routes the NERTA line itself replaces (for example, no SL4 or SL5 on the Orange poster).
- **Effort:** about 4 to 5 hours. A dated CSV in `boston-map/data/` (1 hour), panel code in `make_line_poster.py` (2 hours), a `poster_audit.py` check that every listed stop is on the poster (1 hour), and a crop review. Render to `output/copies/` only.
- **Clutter:** low. The diagram doesn't change, so no pill or name has to move.

**3. Route numbers beside each stop on the posters.**
- **What:** the plan in `docs/IDEAS.md`. Cap it at 4 numbers, then "+2" and so on, in level text.
- **Effort:** about 6 to 8 hours, most of it moving labels on the Green and Yellow posters.
- **Clutter:** medium to high. Nubian has 7 frequent routes, and the numbers compete with transfer pills. Real MBTA posters don't do this (row 16).

**4. Anything on the main map (hub marks or a faint overlay).**
- **Status:** on the Rejected list. A faint layer was already tried and removed (row 19). It's listed only because the brief asked.
- **Effort:** hub marks about 3 hours. A faint overlay takes a day or more. Either needs the full check pass and a new posting copy.
- **Clutter:** the top right corner is already crowded. A faint layer reads as gray noise at social-media size, and it double counts the 10 replaced routes.
- **Smallest version, if Max ever wants it:** change only the footer text, from "Buses not shown" to "Buses not shown. See the NERTA surface map", once that map exists.

---

## 4. Candidate corridors

How a corridor would be drawn on the surface map: **solid** = bus lanes running today, **stripe** = a real proposal, **dash** = imagined. Status follows the data rule.

| # | Corridor | Routes | Why | Draw as | Status |
|---|---|---|---|---|---|
| 1 | Harvard St: Harvard, Allston, Coolidge Corner, Brookline Village, Nubian | 66 | The biggest frequent gap. It crosses Red, Green B, C and D, Orange and Yellow without running along any of them | Stripe (BPV corridor, 4.3 mi). A tram version is a dash | Two for bus priority (BPV, SB 2023). Tram: Invented |
| 2 | Western Ave and Arsenal St: Central, Western Ave, Watertown Sq, Waltham | 70 | Planned frequent. It links Red, Green A, the Red stripe and the Fitchburg Line | Stripe | Two (MBTA Arsenal, SB Jun 2026, BPV) |
| 3 | Columbia Rd: JFK/UMass, Uphams Corner, Grove Hall, Franklin Park | 15, planned 8 and 16 | A crosstown linking Red, Yellow, Indigo and the Orange dash | Stripe. A tram version is a dash | Two for bus priority (BPV, SB 2023). Tram: Invented |
| 4 | Mass Ave: Harvard, MIT, Symphony, Melnea Cass, Nubian | 1 | Red and Yellow cover only its ends. Back Bay and the South End are open | Stripe where lanes are planned. Existing lane segments solid | Two (BPV, SB 2023) |
| 5 | Chelsea to Haymarket over the Tobin | 111 | Chelsea's direct ride downtown. Yellow goes around | Stripe (BPV corridor Woodlawn to Haymarket, 4.5 mi) | Two for the corridor (BPV, SB 2025). Lane removal: One |
| 6 | Inland Revere: Wonderland, Revere, Chelsea, Maverick | 116, 110 | `05-boston-subway.md` names inland Revere a gap | Stripe (BPV Wonderland to Maverick, 4.7 mi). A tram version is a dash; the 116's corridor was trackless trolley until 1961 | Two for bus priority (BPV, SB 2023: Meridian St). History: One (WP streetcar) |
| 7 | Mt Auburn St: Watertown Sq to Harvard | 71 | Real lanes today. A streetcar ran here until 1958 | Solid lanes. A streetcar revival is a dash | Two for the lanes (snippets), Two for history (weak). Revival: Invented |
| 8 | Columbus Ave: Franklin Park, Jackson Sq, Ruggles | 22, 29, 44 | New England's first center bus lane. Phase 2 is curbside, starting 2027 | Solid to Jackson Sq, stripe to Ruggles | Two |
| 9 | Washington St: Roslindale Village to Forest Hills | 10 routes | Running lanes with about 15,000 weekday riders | Solid | Two (snippets) |
| 10 | Morton St: Mattapan to Forest Hills | 31, planned 16 | Ties the south ends of Red, Indigo and Orange together | Stripe | One, unverified (BPV only) |
| 11 | Talbot Ave and Washington St, Dorchester: Ashmont to Codman Sq to Ruggles | 22, 23 | Codman Sq has no NERTA stop | Stripe on the BPV segments | One, unverified (BPV only) |
| 12 | Blue Hill Ave busway: Grove Hall to Mattapan | 28 | Real and partly funded, but NERTA's Orange dash already runs here | Leave it off, or draw it faint with a note (Max's call, question 4) | Two |

**Not recommended:**
- A tram on the 73 corridor. It overlaps the rejected Trapelo Rd stop.
- The SL3 extension through Everett and the Rutherford Ave busway. They're real (Two), but Yellow, Orange and Cyan already run there.

---

## 5. Open questions for Max

1. "Showing buses" is on the Rejected list, but `docs/IDEAS.md` and `HANDOVER.md` both plan a bus test. Does the rejection cover only the main map, or also posters and a separate surface map?
2. DO YOU WANT TO OVERRIDE THE TWO-SOURCE RULE FOR THE MBTA'S FREQUENT-ROUTE LIST? THE API AND THE MBTA'S PLAN DOCUMENTS COUNT AS ONE SOURCE, AND OUTSIDE SOURCES CONFIRM ONLY 14 OF THE 25 ROUTES.
3. On posters: one "Frequent bus" panel per poster, or route numbers beside each stop?
4. On a surface map, should real busways that sit under NERTA rail be drawn (Blue Hill Ave, SL3 through Everett, Rutherford Ave), or left off to avoid double counting?
5. Are invented tram dashes wanted (Harvard St, Mt Auburn St, Columbia Rd, Revere), or buses and real busways only?

*Method note: scripts for the API pulls and the color check are in this session's scratchpad (`research_bus/`). They read the public MBTA API and use no key. Routes are changing through 2026 (SB Jul 2026: 11 route groups proposed, Board vote by year end), so pull fresh data before any render.*
