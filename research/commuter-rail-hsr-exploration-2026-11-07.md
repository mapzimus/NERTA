# Commuter rail and high-speed rail: exploration for the next phase

Research only, November 7, 2026. Nothing on the map was changed. The Day 8 files post as they are; everything here is for after Sunday.

How to read the labels:

- **Exists**: running today, with 2 named sources.
- **Two**: a real proposal or real history, with 2 named sources.
- **One-unverified**: only 1 source found.
- **Invented**: no source. Our idea.

"Checked today" means I confirmed it on November 7. "Research 01" to "04" means the source comes from the November 3 files in `research/`, which I didn't re-open.

## 1. Summary

1. Most commuter rail on the map is solid ground. Every solid line and stop I checked runs today, per the MBTA V3 API. South Coast Phase 2, South Salem, Peabody, the Northern Tier and the Cape each have 2 sources as real proposals.
2. Five things look wrong or thin. Montreal is drawn on the Fitchburg line. Bangor goes via Portsmouth on the Newburyport line. "TO PLYMOUTH" points to a stop closed since 2021. South Acton to Marlborough is now a rail trail. Two audit claims are out of date: the MBTA still calls the stop Lansdowne, not David Ortiz, and Haverhill trains do stop at Oak Grove.
3. Of the five high-speed rows, only NYC runs today. Albany gets one train a day. Concord NH, Montreal and Bangor are studies. None of those four studies plans trains anywhere near Acela speed.
4. Inside the frame, Amtrak serves South Station, Back Bay, Route 128, North Station and Anderson/Woburn. Route 128 is the only one of these the map leaves off.
5. **Recommendation:** after Sunday, build the regional rail poster (HANDOVER step 3) with high-speed rail as gold rows at the edges. Move Montreal to the Lowell row and Maine to the Haverhill row, and keep the rows unbranded ("HIGH-SPEED RAIL"). A separate intercity poster can come later.

## 2. Audit of every commuter rail and high-speed item now on the map

Read from `make_tmap.py` (`CR_STOPS`, `CR_PATHS`, `CR_TEXT`, the gold paths and the Key) and `copies/type_fixed_v26.png`. Commuter rail on this map has only two line styles: solid, and dashed "where new". The gold line has one style.

### Commuter lines, branches and stops

| # | Item | Drawn as | Status | Sources |
|---|---|---|---|---|
| 1 | Through-running under downtown (the BIGGER Dig) | Solid purple through the four-track tunnel | **Two** (proposal) | MassDOT NSRL final report 2019; Harvard "The Missing Mile" (Aug 2026) and Boston Globe, Aug 15, 2026 (Research 01) |
| 2 | Lowell Line: West Medford, Winchester, Anderson/Woburn, Wilmington | Solid | **Exists** | MBTA V3 API route stops (checked today); OpenStreetMap match in `SOURCES.md`. MBTA name is "Winchester Center" |
| 3 | Haverhill Line beside Orange, transfers at Malden Center and Reading | Solid, express past Oak Grove | **Exists**. The skip at Oak Grove is our choice | MBTA V3 API: 43 Haverhill stops at Oak Grove on Monday, Nov 9, the same count as Malden Center (checked today); WHAV and Patch, Sept 2022: Oak Grove became a permanent Haverhill stop. **`line_audit.md` says trains "pass and do not stop". That's wrong for today** |
| 4 | Newburyport/Rockport Line: Chelsea, Central Sq (Lynn), Swampscott, Salem, Beverly | Solid | **Exists** | MBTA V3 API; Wikipedia. Lynn moved to an interim platform Dec 18, 2023, and the API now calls it "Lynn Interim" (MBTA news release; Mass Transit) |
| 5 | Fitchburg Line: Porter, Concord, South Acton, Ayer | Solid | **Exists** | MBTA V3 API; OpenStreetMap match |
| 6 | Worcester Line: Back Bay, West Station, Boston Landing, Newtonville, West Newton, Wellesley | Solid | **Exists**, except West Station | MBTA V3 API; Wikipedia. "Wellesley" stands for three real stops |
| 7 | West Station | Tier 2 station | **Two** (proposal; no build date) | Wikipedia: still conceptual as of 2026; MassDOT Allston Multimodal deck, June 2025: environmental review through fall 2026 |
| 8 | "David Ortiz" commuter stop | Solid stop | **Invented name.** The real stop is Lansdowne | MBTA V3 API lists "Lansdowne" (checked today); Boston Magazine and WHDH: Yawkey became Lansdowne on April 8, 2019. **`line_audit.md` row "Exists today as David Ortiz" is wrong**; the "Local touches" row is right |
| 9 | Providence Line: Back Bay, Hyde Park, Readville, Mansfield | Solid | **Exists** | MBTA V3 API; Wikipedia |
| 10 | Stoughton branch at Canton Junction | Solid | **Exists** | MBTA V3 API; Wikipedia line diagram and an old MBTA map (`line_audit.md`) |
| 11 | Franklin split at Readville: Endicott, Islington, Norwood, Walpole | Solid | **Exists** | MBTA V3 API; Wikipedia and massbytrain. "Norwood" stands for Norwood Depot and Norwood Central |
| 12 | Foxborough branch leaving at Walpole | Solid | **Exists**, with regular weekday service since Oct 2, 2023 | NBC Boston and CBS Boston (permanent service); Wikipedia (Foxboro station); MBTA V3 API trips run Windsor Gardens, then Foxboro, and a Walpole-Foxboro shuttle pattern exists. **Upgrade the "One" in `line_audit.md` to Two** |
| 13 | Foxborough to Mansfield | Dashed | Track and stadium event trains **Exist**; regular service is **Invented** | MBTA V3 API: the event pattern runs Foxboro, Mansfield, Attleboro, Providence (checked today); Wikipedia (Framingham Secondary). **Upgrade from One to Two for the track** |
| 14 | Fall River/New Bedford Line: Brockton, Bridgewater | Solid | **Exists** | MBTA V3 API (that's the line's name now); MBTA South Coast Rail page and Turn to 10: opened March 24, 2025 (Research 01) |
| 15 | "TO CAPE COD" | Label | **Exists** as the summer CapeFLYER. Year-round service is **Two** (proposal) | WBUR, May 22, 2026, and Progressive Railroading: the 2026 CapeFLYER season. Cape Cod Commission and Connecticut Public, May 2026: the 2021 study priced Buzzards Bay at $67M. **Upgrade from One to Two** |
| 16 | Kingston Line: Abington, Hanson, Kingston | Solid | **Exists** | MBTA V3 API; Wikipedia |
| 17 | "TO PLYMOUTH" | Label on a solid line | **Closed** since April 5, 2021. A reopening is **Invented**: no plan or date found | Wikipedia (Kingston Line, Plymouth station); Plymouth Independent (Research 01). The MBTA V3 API doesn't list Plymouth. The promised 2022 reopening didn't happen |
| 18 | Greenbush, leaving north of Braintree: East Weymouth, Hingham, Cohasset, North Scituate, Greenbush | Solid | **Exists** | MBTA V3 API; MBTA Greenbush timetable and Wikipedia (`line_audit.md`). "Hingham" stands for West Hingham |
| 19 | Stoughton to Taunton: North Easton, Easton Village, Raynham Place, Taunton | Dashed, hollow stops | **Two** (proposal, no timeline, about $3.4B) | MBTA South Coast Rail page; Wikipedia; Town of Bridgewater corridor map |
| 20 | South Acton to Marlborough, with Hudson | Dashed | **One-unverified.** I recommend **Invented** | The MPO appendix listing didn't turn up in today's search. The corridor is now the Assabet River Rail Trail (Wikipedia; Freedom's Way and TrailLink). The last rails in Acton and Maynard came out in 2014 |
| 21 | Northern Tier: "FITCHBURG LINE TO GREENFIELD, NORTH ADAMS" | Label | **Two** (studied; every option had a negative benefit-cost result) | MassDOT Northern Tier final report, Nov 2024; WAMC (Research 01) |
| 22 | South Salem stop | Hollow stop ("stripe" in code) | **Two** (in design) | City of Salem, South Salem platform page; Wikipedia: MBTA design contract J63PS01, July 10, 2026; Patch: federal design money (amounts differ, $2M or $2.8M). **Upgrade from One to Two** |
| 23 | Peabody line, South Salem to Peabody | Dashed | **Two** for a Salem-to-Peabody proposal | Mass Transit and Item Live, 2018: state-funded Peabody-Salem trolley study, about $35M (Research 01). The real branch leaves at Salem; leaving at South Salem is schematic, already accepted |
| 24 | Danversport, Danvers, Middleton, "TO LAWRENCE" | Dashed, hollow stops | **Two** for the history; the revival is **Invented** | Wikipedia (Essex Railroad) and nashuacitystation.org both list Danversport, Danvers and South Middleton as real stations. Order Peabody, Danversport, Danvers matches Wikipedia only (One). Passenger service to Danvers Junction ended in 1958, and Danvers to North Andover was abandoned in 1927 |
| 25 | Marblehead spur | Dashed | **Two** for the history (closed 1959); the revival is **Invented** | Wikipedia; Marblehead Weekly News (`line_audit.md`) |
| 26 | Ruggles | No commuter transfer drawn | **Exists, missing** | MBTA V3 API: Providence, Franklin and Needham trains stop there; Wikipedia |
| 27 | Route 128 | Not drawn | **Exists, missing** | MBTA V3 API: 42 commuter stops on Monday, Nov 9; Amtrak's Great American Stations page and Acela timetable |

### High-speed rail and Amtrak

| # | Item | Drawn as | Status | Sources |
|---|---|---|---|---|
| 28 | "HIGH-SPEED RAIL TO NYC VIA PROVIDENCE, NEW HAVEN" | Gold in purple on the Providence line | **Exists** (Acela and Northeast Regional) | Amtrak Acela timetable; WBUR, Aug 28, 2025: NextGen Acela entered service at up to 160 mph |
| 29 | "HIGH-SPEED RAIL TO ALBANY VIA WORCESTER, SPRINGFIELD" | Gold on the Worcester line | **Exists** as 1 daily train. More trains are **Two** (plan); "high-speed" is ours | Amtrak media release and Progressive Railroading: the Lake Shore Limited Boston section came back Dec 1, 2025. Wikipedia (Lake Shore Limited). Compass Rail plans Boston to Albany in Phase III, 2045 (MassDOT April 2026 deck; Streetsblog Mass) |
| 30 | "HIGH-SPEED RAIL TO CONCORD NH VIA LOWELL, NASHUA, MANCHESTER" | Gold on the Lowell line | **Two** (proposal, paused since December 2022) | Granite Memo and Rep. Kuster: the Executive Council ended the study 3-2 (Research 02). CBS Boston and Vermont Public, 2021: Amtrak Connects US showed Boston to Concord |
| 31 | "HIGH-SPEED RAIL TO MONTREAL VIA BURLINGTON VT" | Gold on the **Fitchburg** line | Montreal is **Two**. The Fitchburg routing is **Invented** | FRA eLibrary and Wikipedia: Northern New England Corridor designated Oct 2000, Boston hub with legs to Portland and Montreal. The 2003 study ran via Nashua, Manchester, Concord and Lebanon (Sun Journal; BDN; Research 04). NNEIRI 2016 ran via Springfield and Vermont (Trains In The Valley; USDOT). No study I found uses Fitchburg |
| 32 | "HIGH-SPEED RAIL TO BANGOR VIA PORTSMOUTH, PORTLAND, AUGUSTA" | Gold on the **Newburyport** line | Portland **Exists** (Downeaster), but by another route. Augusta and Bangor were studied and turned down (**Two**). Portsmouth routing is **Invented** | NNEPRA, two documents: Downeaster to Brunswick. BDN 2023 and 2025: MaineDOT called more Bangor study "imprudent". Press Herald and Mass Transit: LD 487 failed in 2025. Greenway.org and City of Portsmouth: the Portsmouth line is now the NH Seacoast Greenway, opened Sept 2024 (Research 02) |
| 33 | High-speed stops only at Boston Central, North, South, West and Back Bay | Rule in the Key | **Max's call.** Boston Central (four-track option) and West Station are not Amtrak plans | Amtrak timetables (South, Back Bay, Route 128, North); Wikipedia (Anderson RTC) |
| 34 | South Station and Back Bay | Tier 1 and Tier 2 | **Exists** for Amtrak (Acela, Northeast Regional, Lake Shore Limited) | Amtrak timetables; Wikipedia (Lake Shore Limited) |
| 35 | North Station | Tier 1 | **Exists** for Amtrak (Downeaster terminal) | NNEPRA; amtrakguide.com |
| 36 | Anderson/Woburn | Commuter stop; gold passes without stopping | **Exists** as a Downeaster stop. Amtrak calls it "Woburn-Anderson" | Wikipedia (Anderson RTC); amtrakguide.com |
| 37 | Framingham, Worcester, Haverhill | Inside line labels only | **Exist** as Amtrak stops. A Framingham stop is on the Rejected list, so it stays in the label | Wikipedia (Lake Shore Limited) and the Michigan Association of Railroad Passengers timetable; amtrakguide.com (Haverhill) |
| 38 | Springfield to New Haven via Hartford | Not shown, on purpose | **Exists** (Hartford Line, Valley Flyer) | Wikipedia (Valley Flyer); Trains magazine (made permanent) |

## 3. Findings

### 3a. Regional rail as a program

1. **The MBTA is rewriting its regional rail plan right now.** The Rail Modernization Plan replaces the 2020 Rail Vision. Virtual meetings fall on November 4 and 17, 2026, with more in spring 2027. The MBTA API now labels every commuter route "Regional Rail". I found no formal rename, so treat that label as one source.
2. **Rail Vision is still the benchmark.** Its "Full Transformation" option ($28.9B in 2020 dollars) means full electrification, high platforms and 15-minute service at most stations. It assumes the North-South Rail Link, South Coast full build and Foxboro.
3. **Electrification is slow.** Fairmount battery trains slipped to about 2030, although the MBTA page still says 2028. The MBTA is buying 10 battery-electric and 10 diesel locomotives, with the battery units aimed at Providence/Stoughton.
4. **A new operator is coming.** Keolis's contract ends June 30, 2027. Three teams are shortlisted, with a pick due by the end of 2026. The brief asks for high-frequency regional rail.
5. **Stations open and close.** Opened: South Coast Rail (March 2025), Foxboro weekday service (October 2023), Oak Grove (2022). Closed since 2021: Plymouth and Prides Crossing. Lynn runs from an interim platform until about 2030. Coming: South Salem (in design) and Everett at Encore (Wynn deal, January 2026).

| Finding | Source 1 | Source 2 | Agree or differ |
|---|---|---|---|
| Rail Modernization Plan, Nov 4 and 17 meetings | Railway News (railwaynews.net, 2026) | American-Rails; MBTA project page (Research 01) | Agree on dates. They differ on the horizon: "next decade" or "through 2050" |
| "Regional Rail" label | MBTA V3 API route descriptions (checked today) | None | **One-unverified** as a rename |
| Rail Vision $28.9B, 15-minute target | MBTA Rail Vision Final Report, Feb 2020 | Railway Track & Structures | Agree (Research 01) |
| Fairmount battery service | Streetsblog Mass, May 28, 2026: about 2030 | Dorchester Reporter, June 18, 2026: delayed | Agree on 2030. The MBTA page still says 2028 |
| Battery locomotive order | A Better City, Mar 12, 2026 | Progressive Railroading | Agree (Research 01) |
| New operator, contract ends June 30, 2027 | Metro Magazine | Railway News | Agree |
| Plymouth closed April 5, 2021 | Wikipedia (Kingston Line) | Plymouth Independent; MBTA V3 API (not listed) | Agree |
| Prides Crossing closed | Wikipedia | Patch; MBTA V3 API (not listed) | Agree on closure. Dates differ: Jan 23 or April 5, 2021 |
| Oak Grove a permanent Haverhill stop | WHAV, Sept 21, 2022 | Patch; MBTA V3 API schedule | Agree |
| Lynn interim platform, Dec 18, 2023 | MBTA news release | Mass Transit; Item Live | Agree. The permanent station is due about 2030 (one source) |
| Everett station at Encore | WBUR, Jan 7, 2026 | Boston Globe, Jan 6, 2026 | Agree (Research 01) |
| South Salem in design | City of Salem | Wikipedia (MBTA contract J63PS01); Patch | Agree on design. Grant amount differs |
| Haverhill double track, $139.6M | WBUR, Aug 25, 2026 | Railway Track & Structures | Agree. Finish dates differ: 2028 to 2030 |
| Inner Newburyport line every 30 minutes on weekdays | MBTA Lynn release, as summarized in search | None | **One-unverified** |

**North-South Rail Link (the BIGGER Dig).** MassDOT's 2019 pick was two tracks with no Central Station. The four-track option with Central Station was $21.53B in 2028 dollars. No state study is active. Harvard's August 2026 paper revived the case. Two sources each, from Research 01. Drawing four tracks and Boston Central is a deliberate fantasy choice, and the map already makes it.

### 3b. High-speed rail rows

1. **NYC is real and already high-speed.** NextGen Acela runs up to 160 mph. NEC FUTURE (2017) sets a 2 hour 45 minute express target to New York and adds a new segment from Sharon to Hyde Park. That segment comes from one FRA fact sheet, so it's unverified.
2. **Albany is real but thin.** One Lake Shore Limited train a day, back since December 2025. Compass Rail plans Boston to New Haven via Springfield first (2030 or the early 2030s; sources differ) and Boston to Albany by 2045. A Boston-Albany service study began October 2026.
3. **Concord NH is real but stalled.** New Hampshire's Executive Council ended the study in 2022. Nashua is pushing a Nashua-only first piece. Amtrak's 2021 vision drew Boston to Concord.
4. **Montreal is real, but not via Fitchburg.** The federal corridor (2000) and the 2003 study both ran Boston, Lowell, Nashua, Manchester, Concord NH, Lebanon, Montpelier, Burlington area, Montreal. That's the map's Concord row, continued. The other real path is via Springfield and the Vermonter (NNEIRI, 2016), which is still blocked at the border. The only real Fitchburg-line intercity idea is the Northern Tier option to Albany via North Adams, from one source (NT24).
5. **Maine is real only to Portland and Brunswick.** The Downeaster leaves on the Lowell Line, crosses the Wildcat Branch and runs up the Haverhill Line, stopping at Woburn and Haverhill. It never touches Portsmouth. The Eastern Route to Portsmouth is now a trail. Maine studied Augusta and Bangor and turned them down.

| Finding | Source 1 | Source 2 | Agree or differ |
|---|---|---|---|
| NextGen Acela, Aug 28, 2025, 160 mph | WBUR | NHPR; CBS Boston | Agree. Trip-time savings differ by report |
| NEC FUTURE Record of Decision, 2017 | FRA ROD highlights | Railway Gazette | Agree (Research 04) |
| Lake Shore Limited Boston section back Dec 1, 2025 | Amtrak media release | Progressive Railroading; Wikipedia | Agree. The cause was a sinkhole found in May 2025 |
| Compass Rail phases (Inland Route, then Albany 2045) | MassDOT deck, April 2026 | Streetsblog Mass, May 2025 | Differ on the first date: 2030 or early 2030s |
| Boston-Albany Corridor ID, $3.5M study | Mass Transit | Rep. Neal; mass.gov | Agree |
| Capitol Corridor study ended Dec 2022 | Granite Memo | Rep. Kuster release | Agree (Research 02) |
| Amtrak Connects US: Boston to Concord | CBS Boston, 2021 | Vermont Public / NEPM, 2021; Concord Monitor | Agree. Patch reported it as one route from Manchester through Boston to Albany |
| Northern New England Corridor, Oct 2000 | FRA eLibrary | Wikipedia; TRB | Agree on Boston hub, Portland and Montreal. Concord isn't named in the 2000 text |
| 2003 Boston-Montreal study via Concord and Lebanon | Sun Journal (excerpt) | Bangor Daily News archive (excerpt); study on ROSA P | Agree. Both pages refused a full read |
| NNEIRI via Springfield and Vermont, 2016 | Trains In The Valley | USDOT release | Agree (Research 04) |
| Vermonter to Montreal blocked | VTDigger, Aug 2026 | WCAX, Sept 2026 | Agree: the bridge and customs are the blockers |
| Downeaster via Wildcat Branch, stops at Woburn | Wikipedia (Haverhill Line; Anderson RTC) | TransitMatters; MBTA V3 API (a Haverhill pattern runs via Anderson/Woburn) | Agree |
| Bangor turned down | BDN, April 2023 | BDN, March 2025; Press Herald 2025 (LD 487) | Agree. Ridership forecasts differ widely (MaineDOT vs Rail Passengers Association) |
| Portsmouth line now a trail | greenway.org | City of Portsmouth | Agree. Only the miles differ |

### 3c. Amtrak, or whatever succeeds it

Max's scope: the high-speed rows stand for Amtrak or its successor.

1. **Routes that reach Boston today:** Acela and Northeast Regional (South Station, Back Bay, Route 128), the Downeaster (North Station, Woburn, Haverhill, then New Hampshire and Maine to Brunswick, five round trips), and the Lake Shore Limited Boston section (South Station, Back Bay, Framingham, Worcester, Springfield, Pittsfield, Albany, one train a day).
2. **The Vermonter and Valley Flyer don't reach Boston.** They meet the Lake Shore Limited at Springfield. Boston to Springfield to New Haven (the Inland Route) is the planned link.
3. **Stations inside the frame:** South Station, Back Bay, Route 128, North Station and Anderson/Woburn. The map shows four. Route 128 is missing, even as a commuter stop.
4. **Stations outside the frame:** Framingham and Worcester (Lake Shore Limited), Haverhill (Downeaster), Providence (Northeast Corridor). They already live in the line labels. Framingham as a drawn stop is rejected; keep it in the label.
5. **Operator naming:** see section 4, option 4.

| Finding | Source 1 | Source 2 | Agree or differ |
|---|---|---|---|
| Route 128 served by Acela and Northeast Regional | Amtrak Acela timetable | Amtrak Great American Stations page | Agree. Not every Acela stops there |
| Lake Shore Limited Boston-section stops | Wikipedia | Michigan Association of Railroad Passengers timetable | Agree on all six stops |
| Downeaster stops and terminal | amtrakguide.com | NNEPRA documents (Research 02) | Agree. Old Orchard Beach is seasonal |
| Valley Flyer: New Haven to Greenfield | Wikipedia | Trains magazine | Agree. Neither lists Boston |

## 4. Gaps and downgrades

**Real items the map is missing (most useful first):**

1. **Route 128** on the Providence line. It's a real commuter and Amtrak station (Exists).
2. **Ruggles commuter transfer.** Providence, Franklin and Needham trains stop there today (Exists). On the drawing the purple line passes about 6 units from the Ruggles dot.
3. **Oak Grove commuter transfer.** It exists today. If Haverhill trains skip it in this future, `line_audit.md` should say that's our choice.
4. **Everett commuter stop at Encore** on the Newburyport line (Two). Encore is already on Cyan, so this would be a commuter transfer, not a new place.
5. **Buzzards Bay** in the Cape label, for example "TO BUZZARDS BAY, CAPE COD" (Two: the 2021 study).

**Downgrade or relabel.** Commuter rail has no striped style, so "downgrade" here means marking an item imagined:

1. Montreal on the Fitchburg row: Invented routing.
2. "VIA PORTSMOUTH" on the Bangor row: Invented routing.
3. South Acton to Marlborough: from One to Invented, because the corridor is a rail trail.
4. "TO PLYMOUTH": a reopening with no plan. Mark it as ours.
5. The gold line has one style, so all five rows read as running. Only NYC runs at high speed.

**Upgrade in `line_audit.md`:** Foxborough at Walpole, Foxborough to Mansfield (track), Cape Cod, South Salem, and "Haverhill drawn as its own branch" (MBTA V3 API route patterns plus Wikipedia). All move from One to Two.

**Fix in `line_audit.md`:** the Lansdowne row ("Exists today as David Ortiz"), the Oak Grove claim, and Lynn's name ("Lynn Interim" in MBTA data now).

## 5. How posters could show commuter rail and high-speed rail

Ranked. All of this is after the Day 8 post, on copies only.

| Rank | Option | What it is | Effort |
|---|---|---|---|
| **1 (recommended)** | **Regional rail poster** | One large sheet with all 12 MBTA lines, every real stop (about 140, from `fetch_mbta.py`), the dashed proposals, and the high-speed rows as gold arrows at the edges. It's HANDOVER step 3 and the "Regional commuter rail map" in `docs/IDEAS.md`. `make_regional.py` exists but used Natural Earth, so it's a start, not a base | 10 to 14 hours over 2 or 3 sessions, plus Max's review |
| 2 | **Intercity / high-speed poster** | A New England sheet in the style of the ferry network poster. Boston hub, with six corridors: NYC, Albany, Montreal via Concord, Montreal via Springfield, Maine, and Hartford. About 40 real Amtrak and studied stations. Shows where the gold rows go | 5 to 8 hours over 1 or 2 sessions |
| 3 | **Main-map fixes only** | Move the Montreal and Maine rows, add Route 128 and the Ruggles and Oak Grove transfers, add a Key row for planned high-speed rail. No new poster | 2 to 4 hours, on a copy |
| 4 | **One poster per commuter line** | Twelve posters in the line-poster format. The commuter lines aren't in `lines()`, so `make_line_poster.py` and `poster_audit.py` would need new code. Lots of repetition for little gain | 15 to 25 hours. Not recommended now |

**Naming the operator on the high-speed rows (Max's added question):**

1. **Keep "HIGH-SPEED RAIL", no brand (recommended).** It fits the NERTA rule of no backstory, and the map stays clear of a second organization to disclaim.
2. **Name Amtrak in the Key only:** "High-speed and intercity rail (Amtrak today)". Rows stay short.
3. **Name Amtrak on every row.** That makes the rows longer in an already crowded top right, and the disclaimer would need "or Amtrak". Use the name only, never the logo. I'm not a lawyer.
4. **Invent a successor brand.** I don't recommend it. It adds the kind of backstory Max chose to leave out for NERTA.

## 6. Open questions for Max

1. **High-speed routes:** move Montreal onto the Lowell/Concord row and Maine onto the Haverhill row to match real studies? Or keep Fitchburg and Portsmouth, and log them as imagined?
2. **Route 128:** add it as a commuter stop? And should high-speed trains stop there, as Acela does today, or keep the major-stations-only rule?
3. **A third style:** should commuter rail and the gold line get a striped "real proposal" style? South Coast Phase 2, South Salem, Peabody, Concord NH and Albany would then stand apart from Marlborough, Middleton, Marblehead and Montreal via Fitchburg.
4. **Plymouth:** keep "TO PLYMOUTH" as a planned reopening (logged as ours), or drop it?
5. **Operator name:** keep the rows unbranded, or name Amtrak in the Key?
