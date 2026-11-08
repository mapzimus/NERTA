# Free rides on NERTA

Research for the Charlie points lore, November 8, 2026. Nothing on any map has changed yet.

Max's rule: free where Boston has real free rides today, plus short shuttles that just link two stations or docks.

## Summary

1. Two real free rides carry over to NERTA: the free Logan Airport rides (Massport shuttles and the SL1 from the airport) become the **Silver Line Logan shuttle**, and fare-free bus Route 23 becomes **tram 23**.
2. Routes 28 and 29 have no tram of their own. The tram work folded them into the Orange Line's Mattapan branch and tram 22, so neither gets a free symbol unless Max wants a free stretch of Orange.
3. The one true short shuttle on NERTA is the **Fast Ferry shuttle** (Navy Yard, Langone Ferryport, Long Wharf), about 1.7 km. It is free.
4. The river **zigzag boats** (Charles, Mystic, Chelsea Creek) cross bank to bank, which makes them a chain of short dock-to-dock links. I recommend making them free. Max decides.
5. None of the short T spurs counts as a shuttle. Each one runs through from a longer line or ends a line in a town.

Fare-free Routes 23, 28 and 29 are confirmed only through December 31, 2026. Nothing has been announced for 2027. The lore still holds, because they are free "today".

## Real free rides, November 2026

| Real ride | What is free | Sources | Agree or differ | Status |
|---|---|---|---|---|
| SL1 from Logan | Boarding at the airport is free. Riding to the airport costs a fare ($2.40 per CapeFLYER) | [MBTA, Logan Airport page](https://www.mbta.com/destinations/logan-airport); [CapeFLYER, Connecting from Logan](https://capeflyer.com/logan-airport-to-capecod/) | Both agree: free from the airport, paid going to it | Verified |
| Massport on-airport shuttles 11, 22, 33, 55, 66, 88 | Free, between the terminals, Airport station (Blue Line), the Rental Car Center, Economy Parking and, on Route 66, the water transportation dock | [Massport, On-Airport Shuttle](https://www.massport.com/logan-airport/to-from-logan/transportation-options/on-airport-shuttle); [MBTA, Logan Airport page](https://www.mbta.com/destinations/logan-airport) | Both agree the shuttle is free. Hours differ by source: Massport gives 9 AM to 10 PM for 22 and 33, some third-party pages give 7 AM | Verified (hours: Massport's) |
| Routes 23, 28, 29 | Fare-free for all riders through December 31, 2026. 23: Ashmont to Ruggles via Nubian. 28: Mattapan to Ruggles. 29: Mattapan to Jackson Sq | [City of Boston, Free Route 23, 28 and 29 Bus Program](https://www.boston.gov/departments/transportation/free-route-23-28-and-29-bus-program); [Boston.com, June 9, 2026](https://boston.com/news/transportation/2026/06/09/free-mbta-bus-routes-extended-through-end-of-year-wu-announces) | Both give the end of 2026. Boston.com says the city is working on 2027 options; no decision found | Verified through 2026. 2027 unknown |
| Replacement shuttle buses during closures | Free shuttles have run for each recent closure | [WBUR, Red Line, July 2025](https://www.wbur.org/news/2025/07/10/red-line-closure-july-kendall-mit-jfk-umass-shuttles-free-newsletter); [WBUR, Green Line, February 2024](https://www.wbur.org/news/2024/02/20/mbta-green-line-closure-c-branch-copley-free-shuttles-commuter-rail-newsletter); [Mass Transit, MBTA release on the 2022 Orange Line closure](https://www.masstransitmag.com/rail/maintenance/press-release/21277396/massachusetts-bay-transportation-authority-mbta-mbta-releases-diversion-plan-ahead-of-orange-line-closure-beginning-aug-19) | They agree that shuttles are free each time. No standing policy was found | Verified as usual practice. NERTA has none ("Replacement shuttle buses: none") |
| Back Bay Logan Express | Free from Logan to Back Bay, $3 to Logan | [Wikipedia, Logan Express](https://en.wikipedia.org/wiki/Logan_Express); [Mass Convention Center Authority, April 29, 2019](https://massconvention.com/about-us/news-item/back-bay-logan-express-riders-will-pay-less-and-get-security-line-perks-sta) | They agree. Only Wikipedia confirms it still runs this way in 2026 | Fare verified; 2026 status from 1 source. NERTA has no buses, so it has no NERTA version |
| Encore water shuttle | Free boat from Long Wharf North to Encore Boston Harbor | [Encore Boston Harbor, Transportation](https://encorebostonharbor.com/transportation); [American Express Travel, Encore listing](https://www.americanexpress.com/en-us/travel/discover/property/Massachusetts-US/Everett/Encore-Boston-Harbor) | They agree it is free. Encore's posted schedule ran only through May 1, 2026; no 2026-27 season found | Free verified; current season unverified |
| Boston Link Bus pilot | Five fare-free city routes (not MBTA), planned for early 2027 | [WBUR, October 20, 2026](https://www.wbur.org/news/2026/10/20/boston-free-bus-new-routes) only | One source | Unverified, and it hasn't started |

Not free today: the MBTA F4 Charlestown ferry, $3.70 ([Wikipedia, MBTA ferry](https://en.wikipedia.org/wiki/MBTA_ferry); [Celebrate Boston](https://www.celebrateboston.com/mbta/charlestown-long-wharf-ferry.htm)). The East Boston ferry was found at $2.40, one source; unverified.

## Each NERTA piece

| Piece | Map(s) it appears on | Free | Basis | Sources |
|---|---|---|---|---|
| Silver Line, the Logan shuttle: Logan Dock, Office Center, Terminals, Parking, A to F, Rental Cars, Airport (`make_tmap.py` `main()`, not `lines()`) | Main map, Silver Line poster, nerta.fun | **Yes, the whole line** | It replaces the free Massport shuttles, including Route 66 to the water dock, and the free-from-Logan SL1. `line_audit.md` already describes it this way. It is also short: Logan Dock to Airport station is about 1.4 km in a straight line | Massport; MBTA |
| Tram 23, Washington St, Dorchester: Ashmont to Nubian via Codman Sq, Four Corners and Grove Hall | Tram poster (in review), `tram_network.json` | **Yes, the whole line** | Real fare-free Route 23. NERTA's ends at Nubian; the real one runs on to Ruggles | City of Boston; Boston.com |
| Orange Line Mattapan branch, Tufts Medical Ctr to Mattapan via Nubian, Grove Hall, Seaver St, Wellington Hill and Blue Hill Ave | Main map, Orange poster | **No** (open question) | The Nubian to Mattapan stretch follows the Route 28 corridor (`tram_candidates.json`: 71% of the 28 runs under rail). The branch runs through to downtown, so a free symbol would cover far more than the 28 does | City of Boston; Boston.com (for the 28) |
| Tram 22, Ruggles to Ashmont via Jackson Sq, Egleston Sq and Seaver St | Tram poster | No | It takes over the 29's Jackson Sq to Seaver St half, but its real counterpart is Route 22, which charges a fare. The 29 has no single NERTA counterpart | City of Boston (29 route) |
| Trams 16 and 31 (also cross Seaver St and Blue Hill Ave) | Tram poster | No | Their real counterparts, Routes 16 and 31, charge a fare | None needed |
| Yellow Line, Seaport to Terminals to Airport | Main map, Yellow poster | No | It follows the SL1's tunnel path, but it is a whole Urban Ring line. The real "free from the airport" rule could be a Key note instead of a symbol | MBTA; CapeFLYER |
| Blue Line at Airport | Main map, Blue poster | No | Real Blue Line rides from Airport station are paid | None needed |
| Every other T line, commuter rail, high-speed rail, other trams | All | No | No real free ride today | None needed |
| Fast Ferry shuttle, Navy Yard to Langone Ferryport to Long Wharf | Main map, Ferry Map, Fast Ferry poster (`ferry_fast_ferry`), nerta.fun ferry section | **Yes** | The short shuttle in Max's rule. It is not free today (F4 charges $3.70), so it counts as a shuttle, not as a real free ride | Rule; F4 fare from Wikipedia and Celebrate Boston |
| North Shore and South Shore Fast Ferry | Main map, Ferry Map, their posters | No | Long routes. They share the "Fast Ferry" name, so the symbol must sit on the shuttle only, including on the Fast Ferry poster, which also shows the high-speed routes | None needed |
| River zigzag boats, Charles, Mystic, Chelsea Creek | Ferry Map, the three river posters | **Recommended yes** | Each hop crosses bank to bank between two docks. They work like a bridge, not a trip downtown | Rule |
| River loops (both directions) and their hub links | Ferry Map, river posters, main map | No | Real-length routes. The links (Langone to Lovejoy Wharf about 0.5 km, Langone to Navy Yard about 0.7 km, Langone to Boston Bay) are the first leg of each loop, not separate boats | None needed |
| Encore on the Mystic loop | Ferry Map, main map | No | The real free Encore boat is a private casino perk. NERTA reaches Encore only by the paid Mystic loop | Encore; American Express Travel |
| Walking links (Lovejoy Wharf to North Station, dock squares, Dig walkways) | Main map, Ferry Map, posters | Free by nature | Walking, not riding. No symbol needed | None needed |

## Short shuttles

Straight-line lengths come from the repo's station points (`stations_real.geojson`) and are approximate. Navy Yard is the yard's center, not Pier 4. Logan Dock is my own estimate.

| Short piece | Length | Free shuttle? | Reason |
|---|---|---|---|
| Fast Ferry shuttle, Navy Yard to Langone (0.7 km) to Long Wharf (1.0 km) | about 1.7 km | **Yes** | It just links three major docks, nonstop and at all times |
| Silver Line Logan shuttle, Logan Dock to Airport | about 1.4 km straight, longer by the terminals | **Yes** | It just links the water dock, the terminals and the station. It is also a real free ride |
| River zigzag boats | Crossings of a few hundred meters (not measured) | **Yes, recommended** | Dock-to-dock river crossings |
| Blue, Charles/MGH to Gov't Center (Red-Blue Connector) | 0.95 km | No | Blue trains run through it to West Station |
| Blue, Orient Heights to Winthrop Center | 1.9 km | No | It ends the line in a town center rather than linking two stations. Tram 712 also serves Winthrop |
| Blue, Central Sq to Wyoma Sq | 2.5 km | No | The end of the line, not a link |
| Red, Braintree to Weymouth | 3.7 km | No | The end of the line |
| Green D, Riverside to Wellesley Hills | 3.6 km | No | D trains run through |
| Green D, Union Sq to Inman Sq to Harvard | 0.6 km + 1.5 km | No | D trains run through |
| Green, Union Sq to Lechmere | 1.6 km | No | D trains run through |
| Green, Hynes to West Station | 3.3 km | No | A trains run through |
| River loop hub links (Langone to Lovejoy Wharf, Navy Yard, Boston Bay) | 0.5 to 0.7 km (Boston Bay not measured) | No | The first leg of each loop |
| Islands links: Vineyard Haven to Woods Hole, Woods Hole to Cuttyhunk, Canal Pass, Noman's Land spur | Many km each (not measured) | No | Long open-water legs, not short links |

## Final free list

1. Silver Line, the Logan shuttle (whole line).
2. Tram 23, Washington St, Dorchester (whole line).
3. Fast Ferry shuttle, Navy Yard, Langone Ferryport, Long Wharf.
4. River zigzag boats on the Charles, Mystic and Chelsea Creek (recommended, Max's call).

No override of the two-source rule is needed: the real-world facts behind items 1 and 2 each have two sources, and items 3 and 4 rest on Max's shuttle rule, not on data. "Charlie points" is fare lore and doesn't clash with the rejected "Charlie line".

## Open questions for Max

1. Should the Orange Mattapan branch be free between Nubian and Mattapan, standing in for Route 28, or not free at all?
2. Should the river zigzag boats be free?
3. Should the Key add a line saying rides from Logan are free (like the real SL1), so Yellow and Blue need no symbol?
4. Does the Winthrop spur run as its own shuttle from Orient Heights? If it does, it would count as a free shuttle.
5. If the city ends free Routes 23, 28 and 29 in 2027, does tram 23 stay free in NERTA?
