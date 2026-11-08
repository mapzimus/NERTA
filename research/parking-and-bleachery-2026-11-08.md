# Parking (P) and Bleachery check, November 8, 2026

Merges two sweeps (r0: 3 MBTA sources; r2: MBTA API plus a second source) with web re-checks today. MBTA API and the MBTA station page read one feed, so they count as one source. Wikipedia station counts often copy older MBTA figures. Spaces read "source A / source B". Scope: NERTA T stops in `make_tmap.lines()` only.

## P list: 34 stops (garage, or lot of about 100+, 2 sources agree it exists)

| Stop(s) | Kind | Spaces | Sources | Note |
|---|---|---|---|---|
| Braintree | Garage | 1,305 / 1,322 | MBTA API, Wikipedia | Garage 1,197 + Ivory St lot |
| Alewife | Garage | 2,471 / 2,733 | MBTA API, Wikipedia | |
| North Quincy | Garage | 832 / 1,206 | MBTA API, Wikipedia | Hancock St garage |
| Quincy Adams | Garage | 800 / 2,538 | MBTA API, Wikipedia | From Nov 3 side B (1,273) is held for Logan Express |
| Wellington | Garage + lot | 2,035 / 1,316 | MBTA API, Wikipedia | Both agree on the 1,300+ lot; Station Landing garage is MBTA only |
| Wonderland | Garage + lot | 1,912 / 1,862 | MBTA API, Wikipedia | |
| Woodland | Garage | 534 / 548 | MBTA API, Wikipedia | |
| North Station | Private garage | 1,275 / 1,275 | MBTA API, Wikipedia | Under TD Garden, ProPark |
| South Station | Private garage | 210 / 225 | MBTA API, Wikipedia | Bus terminal garage |
| Haymarket | Private garage | about 1,100-1,160 | MBTA Stations and Rates (Haymarket row, up to $33), Wikipedia (Bulfinch Crossing), garage operator site (open 24/7) | MBTA station page and API list none. Site still under construction. Not Gov't Center |
| Assembly | Retail garage | about 2,000 / 1,000+ public | Wikipedia (Assembly station), MGB directions page, Parkopedia, Banker & Tradesman | Federal Realty, open to the public, paid |
| Central Sq (Lynn) | Garage, partly open | 350 + Ellis St city lot 64 | MBTA API and alert, Daily Item Dec 2024 | Differ: Wikipedia says it closed Oct 2022. MBTA shows typical weekday use of 127 |
| Belmont Ctr | Town lot | 141 / 138 | MBTA API, MAPC 2017 study | Claflin St lot. Town commuter passes are limited |
| Watertown | MBTA lot | 164 / 164 | MBTA API, Wikipedia (Watertown Yard) | At Watertown Yard, about 250 m south of the Square: the old A-branch end |
| Wollaston | Lot | 531 / 550 | MBTA API, Wikipedia | |
| Oak Grove, Malden Center, Sullivan Sq, Forest Hills, Wakefield | Lots | 729/788, 195/195, 197/222, 217/206, 116/117 | MBTA API, Wikipedia | |
| Roslindale Village, Highland, Hyde Park, Readville | Lots | 143/144, 175/175, 121/121, 346/353 | MBTA API, Wikipedia | |
| Orient Heights, Suffolk Downs, Beachmont | Lots | 411/434, 108/108, 416/430 | MBTA API, Wikipedia | |
| Riverside, Needham Junction, Hersey | Lots | 935/925, 125/175, 318/360 | MBTA API, Wikipedia | |
| Lexington Ctr (planned stop) | Town lot | 292 (or 118) / 310 | MAPC 2017 study, Parkopedia | Lot at Lexington Depot, Meriam St. MAPC's own tables differ |
| Encore (invented stop) | Casino garage | 2,900 / 1,960 | Encore Boston Harbor parking page, Boston Globe 2019 | Free to anyone. Count unverified |
| Lynn Harbor (our stop) | Ferry lot | 300 / 301 / 150-200 | MBTA API, Boston Globe 2014, Boston Harbor Now 2019 | Blossom St Pier, free. Counts only because the ferry map puts Lynn Harbor there |
| Terminals (Logan) | Airport garage | about 11,000-12,000 | Boston Globe 2026, CBS Boston | Central Parking. Count unverified. Silver already has a Parking stop |

## Maybe: 7 stops

| Stop | Why it is not in the P list |
|---|---|
| Weymouth | Its real place is not set (one-source branch). South Weymouth (538/539) and Weymouth Landing (290/290) both have real lots |
| Arlington Ctr | Russell Common town lot is real (Wikipedia, town parking report), but its size (about 220) comes only from Parkopedia |
| Weston | MassDOT Park and Ride, 672 South Ave by I-95: 100 free spaces (MassDOT, Parkopedia). Carpool lot right at the line. Weston's spot is Max's idea |
| Park Street | Boston Common Garage, 1,350 (MCCA, Boston Discovery Guide). Its entrance is on Charles St, about 500 m away. The MBTA does not list it |
| West Roxbury | 62 (MBTA API, current) / 175 (Wikipedia, massbytrain). The sources fall on both sides of the line |
| Waltham | City lots: 86 (MBTA) / 50 (Wikipedia). Under 100 |
| Needham Heights | 87 (MBTA) / 71 permit-only (Wikipedia). Under 100 |

Left off: lots under 100 (Savin Hill, Butler, Milton, Fairmount, Reading, Greenwood, the Melrose stops, Wyoming Hill, Bellevue, Uphams Corner, West Medford, Chestnut Hill, Eliot, Waban, Auburndale, Wellesley Hills, the Brookline meters). Mattapan is down to about 50 since the 2023 housing (MBTA API 53; Dorchester Reporter and Boston Haitian: at least 50 kept). Saugus Center: 1 source, 2-hour limit. Wyoma Sq, Winthrop Center: small or short stay. Lexington Route 128: garage planned in the 1970s, never built. Stadium: capped at 75. No parking at Quincy Center, Gov't Center, West Station or VFW Parkway. Neither sweep checked 43 newer stops, including Bleachery, Convention Center, Navy Yard and Seaport.

## Bleachery: fact check of the r1 notes

| Claim | Status | Sources |
|---|---|---|
| Stop at River St @ Seyon St, Waltham, 42.3685, -71.2176 | Verified (the stop) | MBTA stop list (stops 7808, 7852), r1 notes |
| OSM labels that stretch "The Bleachery", within 20 m | Wrong | OSM puts "The Bleachery" about 570 m northwest (42.3719, -71.2228) and the Bleachery Dam about 450 m west. The stop sits on the east edge of the area |
| River St becomes Pleasant St at the Watertown line | Verified | MBTA stop list (Seyon St in Waltham; Repton Pl, 330 m east, in Watertown), Patch 2011 (from r1) |
| Mill closed in 1951 when Raytheon took the site | Verified | waltham-community.com, Waltham Museum (quoted on a blog). Opening year differs: 1820 vs 1819 (Digital Commonwealth) |
| Raytheon at Seyon St was the mill site; 41 Seyon St office park | Unverified | An OSHA record lists Raytheon at 20 Seyon St, but no source ties Seyon St to the mill |
| Watertown Branch ran Watertown Sq, Pleasant St, over the Charles by the Bleachery Dam, to Waltham | Verified | Wikipedia (Watertown Branch), waltham-community.com (trestle "to the factory") |
| Passenger service ended July 9, 1938; abandoned 1960, 1991, 2000 | Verified | Wikipedia, Trailspotting 2023 (gives the year only); waltham-community.com has the same date |
| Trestle removed August 2016 | Unverified | Wikipedia only |
| A station named "Bleachery" (1882 timetable) | Unverified | nashuacitystation.org only. Wikipedia and waltham-community.com don't list it |
| 1926 report: Red under Mt Auburn St to Watertown, then on the Watertown Branch to Waltham | Unverified | Wikipedia (Red Line) only. The Leventhal Map Center shows the report exists, but I couldn't read its Watertown part |
| 1947 plan picked Porter to Waltham via Belmont over Watertown | Verified | Wikipedia, Boston Globe Apr 6 1947 (from r1). This backs the Red Waltham branch, not Bleachery |
| No modern rail or BRT study for Waltham to Watertown Sq | None found | r1's search and mine. Trailspotting: nothing to ride west of the Square |
| 1903 streetcar from Waltham to Park St | Unverified | Wikipedia only |

**Verdict: partly grounded.** It is a real place on a real former railroad. The Watertown Branch linked Watertown Sq and Waltham through the Bleachery until 1938 for passengers and 2000 for freight. Red and the A meeting there is invented, and the only proposal (1926) has one source. `make_tmap.py` draws both Bleachery legs as stripe (real proposal). Under the house rule they would be dashed unless Max overrides the 2-source rule for the 1926 report.
