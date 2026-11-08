# Bus plan (draft)

Research notes, November 7, 2026. Advice only. Nothing on the map or posters has changed.

**Heads up:** `docs/DECISIONS.md` still lists "Showing buses" under Rejected. `docs/IDEAS.md` says Max reversed that call for later testing. Max should settle which one stands before any bus work starts.

## Sources used

| Short name | What it is | Date seen |
|---|---|---|
| **MBTA API** | MBTA V3 API, `api-v3.mbta.com/routes` and `/stops`. Live MBTA data. Each bus route's `description` field says "Frequent Bus", "Local Bus", "Coverage Bus" and so on | Pulled Nov 7, 2026 |
| **WP list** | Wikipedia, "List of MBTA bus routes" (route termini) | Nov 7, 2026 |
| **WP key** | Wikipedia, "MBTA key bus routes" (frequency upgrade dates) | Nov 7, 2026 |
| **SB 2024** | Streetsblog Mass, "New T map highlights new frequent service bus routes", Sep 11, 2024 | |
| **SB 2023** | Streetsblog Mass, "Here's the MBTA's bus lane wishlist for its new high-frequency bus routes", Oct 23, 2023 | |
| **SB 2026** | Streetsblog Mass, "Redesigning the redesign: the T tweaks its bus network with 11 new route adjustments", Jul 3, 2026 | |
| **krmatt** | krmatt.github.io/gtfs, a hobby GTFS tracker, last updated Oct 15, 2025 (seen only as a search snippet) | |

I could not open the MBTA's 2023 Bus Network Redesign final report PDF (the host didn't resolve), so the full 2022 plan route list is **not** here. See the end of section 3.

---

## 1. Recommendation

**Short answer: show nothing on the main map now. Later, add bus-transfer markers at stations, not a faint network.**

1. **Nothing for Sunday.** The handover says the Day 8 post uses the existing files with no redraw. A bus layer added the day before would skip the full check pass (`labels.py`, `marks.py`, `audit.py`, `routing.py`, `poster_audit.py`) and a crop review. That isn't worth risking for a 24-hour deadline.
2. **A faint network fails at social-media size.** The main map is about 18.5 by 15.8 inches, shown at roughly 1080 to 2048 pixels wide. The frequent network alone is 25 routes (section 3), and the core is already crowded (the top right corner is a known problem). A pale layer at that size reads as gray noise behind the lines, not as information. The full network is about 150 routes (MBTA API count), which is hopeless at that size.
3. **A faint network hurts credibility through double counting.** About half of today's frequent routes run on corridors this map already turns into rail: SL4/SL5 under extended Orange, the 28 under Orange on Blue Hill Ave, the 104 and SL3 under Yellow, the 57 under the Green A branch, the 39 under the Green E extension, and the 77 under Red to Arlington Heights. Drawing both says "we built a subway and kept the same bus beside it", which a transit-savvy viewer will flag. A real future network would cut or reshape those buses.
4. **Markers are the right middle ground, later.** A small bus symbol at the 15 to 25 stations in section 2 tells a viewer "big bus hub here" without drawing a single route. It fits the poster language already in use (pills), is easy to check with the existing marks tools, and stays true even if the bus routes change.
5. **Save the network for the separate surface map.** Max's plan (stops first, then lines, pale pink with a thin black center line, trams on the top corridors) belongs on its own sheet, where the bus routes can carry the detail. That map can also show which buses a future network would cut once rail opens. The pale pink style is untested here; check it against Red and the pink-ish fills already on the map before committing.

## 2. Bus-to-rail transfer hubs

"Frequent" = the MBTA API labels it "Frequent Bus" today (Nov 2026). Route lists come from the MBTA API query `routes?filter[stop]=<station>&filter[type]=3`, unless noted.

**Evidence levels:**
- **Verified:** the hub is a terminus for those routes in both the MBTA API (route names) and WP list.
- **Partly verified:** some routes confirmed by both; pass-through routes are MBTA API only.
- **Unverified:** MBTA API only.

| # | Hub | Key routes (frequent in bold) | On map list? | Evidence |
|---|---|---|---|---|
| 1 | Nubian | **1, 15, 23, 28, 66, SL4, SL5**, 8, 14, 19, 41, 42, 44, 45, 47, 171 | Yes (Orange dash, Yellow) | Partly verified: 1, 66, SL4, SL5 termini in MBTA API + WP list. 15, 23, 28 pass through, MBTA API only |
| 2 | Ruggles | **15, 22, 23, 28, 9**, 8, 19, 43, 44, 45, 47, 65, 85, CT3 | Yes | Partly verified: 15, 22, 23, 28 termini in both. Route 9 here is MBTA API only (see note A) |
| 3 | Forest Hills | **31, 32, 39**, 16, 21, 30, 34, 34E, 35, 36, 37, 38, 40, 42, 50, 51 | Yes | Verified: 31, 32, 34, 39 termini in both |
| 4 | Ashmont | **15, 22, 23**, 18, 21, 24, 26, 215, 217, 240 | Yes | Verified: 22, 23, 215, 217, 240 termini in both. 15 is MBTA API only |
| 5 | Mattapan | **15, 28, 31**, 24, 29, 30, 33, 245, 716 | Yes | Verified: 28, 31 termini in both. 15 is MBTA API only |
| 6 | Harvard | **66, 71, 73, 77, 109**, 74, 75, 78, 86, 96 (and **1** at Harvard Sq) | Yes | Verified: 1, 66, 71, 73, 77, 86, 96, 109 termini in both |
| 7 | Sullivan Sq | **109**, 85, 89, 90, 91, 92, 93, 95, 101, 105 | Yes | Verified: 89, 91, 92, 93, 95, 101, 105 termini in both |
| 8 | Wellington | **110**, 97, 99, 100, 106, 108, 112, 134 | Yes | Verified: 106, 108, 110, 112 termini in both |
| 9 | Malden Center | **104**, 97, 99, 101, 105, 106, 108, 131, 132, 137, 411, 430 | Yes | Verified: 101, 104, 105 termini in both |
| 10 | Wonderland | **110, 116**, 411, 424, 426, 439, 441, 442, 450, 455 | Yes | Verified: 110, 116, 455 termini in both |
| 11 | Maverick | **116**, 114, 120, 121 | Yes | Verified: 116 terminus in both |
| 12 | Airport | **104, SL3**, 171 | Yes | Verified: 104 terminus in both. SL3 is MBTA API only here |
| 13 | Chelsea | **SL3** (the 111 and 112 also cross Chelsea, see note B) | Yes (Yellow) | Verified: SL3 terminus in both |
| 14 | Haymarket | **111**, 426, 428, 450, plus 92 and 93 "Downtown" | Yes | Verified: 111, 426, 450 termini in both. See note B |
| 15 | Kenmore | **57, 9**, 8, 19, 60 | Yes | Verified: 57, 8, 60 termini in both. See note A on the 9 and the 57 |
| 16 | Quincy Center | 210, 211, 215, 216, 217, 220, 222, 225, 230, 236, 238, 245 (no frequent route) | Yes | Verified: 215, 217, 220, 222, 225, 230, 236, 238 termini in both |
| 17 | Central Sq, Lynn | 426, 429, 435, 436, 456 (no frequent route) | Near "Lynn" (Blue). Check it's the same spot | Verified: 426, 435, 436 termini in both. See note B |
| 18 | Central (Cambridge) | **1**, 47, 70, 83, 91, 64 | Yes | Partly verified: 91 terminus in both; 47, 83 MBTA API only. See note B |
| 19 | Andrew | **9**, 10, 16, 17, 18, 171, CT3 | Yes | Unverified (MBTA API only) |
| 20 | Fields Corner | **15**, 17, 18, 19, 201, 202, 210 | Yes | Verified: 15 terminus in both |
| 21 | Davis | 87, 88, 89, 90, 94, 96 | Yes | Verified: 89, 90, 94 termini in both |
| 22 | Watertown Yard / Watertown Sq | **57** (Yard), **71** (Square), 52, 59, 504 | "Watertown" (Green A) is the square; the Yard is a short walk south | Verified: 57, 71 termini in both. 52, 59, 504 MBTA API only |
| 23 | Jackson Sq | **22**, 14, 29, 41, 44 | Yes | Unverified (MBTA API only) |
| 24 | Back Bay | **39** | Yes | Verified: 39 terminus in both |
| 25 | South Station | **SL1, SL2, SL3** (plus SLW) | Yes | Verified: SL1, SL2, SL3 termini in both |

**Not big hubs:** JFK/UMass (8, 16, 41), Braintree (210, 226, 230, 236), Alewife (62, 67, 76, 350) and Lechmere (69, 80, 87, 88) have buses but no frequent route.

**Note A, routes 9 and 57 may be changing.** The MBTA API still names the 9 "City Point - Copley Square" and the 57 "Watertown Yard - Kenmore Station". But the API's stop list for the 9 runs from Longwood via Ruggles, Newmarket and Broadway to City Point. The 57's list starts at Haymarket and runs along Tremont St. These look like redesign changes. They're one source only, so they're **unverified**. Check the MBTA route pages before using them.

**Note B, the API misses some stations.** Haymarket, Central, Lynn, Hynes, Assembly and others returned no bus routes. Their bus stops aren't filed under the station, so a station-only query comes back empty. The routes in those rows come from the termini in the route names. Any future script has to look for bus stops within about 150 m of each station, not under the station ID.

## 3. Frequent network corridors

### Frequent today (MBTA API, Nov 2026): 25 routes

| Route | Corridor | Second source | Overlaps a NERTA line? |
|---|---|---|---|
| 1 | Mass Ave, Harvard to Nubian | WP key (Aug 2025 upgrade), SB 2023 | Partial: crosses Yellow at Mass Ave. Shares Melnea Cass to Nubian with Yellow |
| 9 | Broadway / South Boston (route may be changing, note A) | SB 2023 calls it frequent (via Berkeley St) | **Yes**, if the new path holds: Yellow (Longwood, Ruggles, Newmarket) and Cyan (Broadway to City Point) |
| 15 | Dudley St / Uphams Corner, Fields Corner to Ruggles | WP key (Aug 2025) | Partial: Indigo at Uphams Corner, Yellow from Nubian to Ruggles |
| 22 | Talbot Ave, Ashmont to Ruggles | WP key (Aug 2025) | Partial: Indigo at Talbot Ave only |
| 23 | Washington St Dorchester, Ashmont to Ruggles | WP key (Aug 2025) | Partial: the Orange dash runs through Four Corners |
| 28 | **Blue Hill Ave / Warren St**, Mattapan to Ruggles | WP key (Aug 2025), SB 2023 (bus priority corridor) | **Yes**: Orange dash Nubian, Grove Hall, Seaver St, Wellington Hill, Mattapan |
| 31 | Morton St, Mattapan to Forest Hills | krmatt (Aug 2025 list) | No: Indigo only crosses at Morton St |
| 32 | Hyde Park Ave, Forest Hills to Wolcott Sq | WP key (Dec 2025) | Partial: the Orange stripe to Hyde Park and Readville |
| 39 | Huntington Ave / Centre St, Forest Hills to Back Bay | WP key (key route) | **Yes**: Green E stripe from Heath St to Hyde Sq and Forest Hills |
| 57 | Comm Ave / Brighton Ave / Washington St, Watertown to Kenmore | WP key (key route) | **Yes**: the Green A stripe through Allston, Brighton Center, Oak Sq and Newton Corner |
| 66 | Harvard St (Allston and Brookline), Harvard to Nubian | WP key (Dec 2025) | No. **Best free candidate** |
| 71 | Mt Auburn St, Watertown Sq to Harvard | WP key (Dec 2025) | No. Free candidate |
| 73 | Belmont St / Trapelo Rd, Waverley Sq to Harvard | WP key (Dec 2025) | Partial: the Red stripe ends at Waverley Sq, but on the rail corridor, not Trapelo |
| 77 | Mass Ave north, Arlington Heights to Harvard | WP key (Dec 2025), SB 2023 | **Yes**: the Red stripe from Alewife to Arlington Heights |
| 104 | Airport, Chelsea, Everett, Malden | SB 2024, WP list | **Yes**: Yellow from Airport to Everett Sq |
| 109 | Linden Sq, Everett, Sullivan to Harvard | SB 2024, WP list | Partial: Yellow Everett Sq to Sullivan; the Orange dash at Linden Sq |
| 110 | Wonderland to Wellington via Revere and Everett | SB 2024 | Partial: the Orange dash Malden to Wonderland takes a more northern path |
| 111 | Chelsea to Haymarket over the Tobin | WP key (key route) | Partial: Yellow at Chelsea and Bellingham Sq |
| 116 | Revere St, Wonderland to Maverick | SB 2024 | Runs beside today's Blue Line. No new-line overlap |
| SL1 | Logan to South Station | MBTA API only | Partial: Silver at Logan Terminals |
| SL2 | Design Center to South Station | MBTA API only | Partial: Cyan and Yellow cover the Seaport |
| SL3 | Chelsea, Airport to South Station | SB 2026 (frequency increase) | **Yes**: Yellow from Chelsea to Day Sq and Airport (DECISIONS says Yellow follows this corridor) |
| SL4 | Washington St, Nubian to South Station | MBTA API only | **Yes**: the Orange dash from Tufts Medical through Dover, Northampton and Nubian |
| SL5 | Washington St, Nubian to Temple Pl | SB 2026 (frequency increase) | **Yes**: same as SL4 |
| SLW | Silver Line Way to South Station | MBTA API only | Covered by Cyan |

**The count doesn't match.** The MBTA API shows 25 frequent routes. SB 2026 cites a slide saying 21 systemwide. The gap may come from how the Silver Line branches are counted, but that's a guess. So the "25" is **unverified**. The 2022 plan aimed for about 30 (SB 2023 and the SB 2022 first-look article agree on the plan to double from 15 to 30).

### Clean tram or BRT candidates (no double counting)

Best first:
1. **66, Harvard St**: Harvard, Allston, Coolidge Corner, Brookline Village, Nubian. It crosses five or more NERTA lines without running along any of them. It's the strongest "surface ring" candidate.
2. **71, Mt Auburn St**: Watertown Sq to Harvard. A short, classic streetcar corridor.
3. **31, Morton St**: links Mattapan and Forest Hills. It ties the Red, Orange dash and Indigo southern ends together.
4. **22 and 23, Talbot Ave and Washington St**: Ashmont to Ruggles. Some overlap with Orange and Indigo, but they serve Codman Sq, which the map skips.
5. **110 and 116, Revere and Everett**: an East Boston to Revere to Everett surface link north of Yellow.

**Don't draw these as new trams.** NERTA already turns them into rail: 28 (Blue Hill Ave), SL4/SL5 (Washington St), 104 and SL3 (Chelsea and Airport), 57 (Comm Ave), 39 (Centre St), 77 (Mass Ave north).

**The full 2022 plan list is still missing.** I couldn't confirm the plan's full list of about 30 high-frequency routes, or whether it used "T" prefixes on route numbers. That's unverified from memory, so it isn't used here. Next source to try is the MBTA's Bus Network Redesign final report (May 2023), linked from the MBTA's project page.

## 4. How line posters could show buses later

1. **Route numbers beside each stop.** Put a small row of bus route numbers under or beside the stop name. Frequent routes go first in a pale pink pill with black text, which matches the future bus color. Other routes follow in plain small text. Cap the row at about 6, then "+3" and so on, so Nubian (16 routes) and Forest Hills (16) don't swamp the poster.
2. **Show frequent routes only, at first.** That's 25 routes total, which keeps every row short and every number checkable. Add local routes in a second pass if it still reads well.
3. **Leave out buses a NERTA line replaces.** For example, don't list SL4/SL5 at Dover or Northampton on the Orange poster. Write the rule down in `docs/DECISIONS.md` so it's applied the same way everywhere.
4. **Data path:**
   - Pull routes from the MBTA V3 API (`/routes?filter[type]=3` gives the number, name and Frequent/Local label) or the MBTA GTFS feed (`routes.txt`, `stops.txt`, `stop_times.txt`, `trips.txt`).
   - Match bus stops to NERTA stations **by distance**, about 150 m, not by station ID (see note B).
   - Save the result as a dated CSV in `boston-map/data/` so posters don't change when the API changes.
   - Re-pull before any final render. Routes are being reshaped through 2026 (SB 2026: 11 route groups proposed, Board vote by end of 2026).
5. **Two-source check.** The MBTA API and GTFS both come from the MBTA, so they count as **one** source. Cross-check frequent status against WP key or Streetsblog, or ask Max for an override.

## Open items

1. Settle the DECISIONS vs IDEAS conflict on buses.
2. Confirm the new paths for the 9 and the 57 (note A).
3. Find the full 2022 plan route list (section 3).
4. Resolve the frequent count: 25 (MBTA API) vs 21 (SB 2026 slide).
