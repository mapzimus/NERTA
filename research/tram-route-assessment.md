# Tram route assessment

Research notes, November 8, 2026. Advice only. Nothing in the tram data, the maps or the code has changed. This covers **routes**; another session is re-planning **stops**, so stop names below are NERTA stations, not final tram stops.

The question for each of the 32 draft trams: now that NERTA rail exists, where should this tram still run?

## 1. Summary

1. **Pull the Roxbury and Dorchester trams off the new rail.** 15 starts at Nubian, 22 at Jackson Sq, 23 at Grove Hall. Ruggles to Nubian is now one Yellow stop, Ruggles to Jackson Sq is the Orange Line, and Nubian to Grove Hall (Warren St) is the Orange Blue Hill Ave branch. Codman Sq, the real gap, keeps both 22 and 23.
2. **Trim Mass Ave (1) and Broadway (9) where they sit on top of rail.** The 1 becomes Central to Boston Medical: Red runs under Mass Ave from Harvard to Central, and Yellow plus the Orange branch cover Boston Medical to Nubian. The 9 becomes Copley to Broadway: Cyan's West Broadway, L Street and City Point stops run the South Boston half.
3. **Drop four trams that NERTA rail now runs.** 64 Oak Sq (Yellow, Red and the Worcester Line), 225 Weymouth Landing (Red to Weymouth and the Greenbush Line), 60 Route 9 (Green D), 712 Winthrop (Blue's Winthrop branch). Three more are weak and could go too: 38, 100 and 78.
4. **Merge trams that share one street.** 34 folds into 34E, which ends at Dedham Sq (the Franklin Line runs beside it past there). 222 folds into 220. 78 folds into 75. 95 and 101 swap halves at Medford Sq so one runs Sullivan to Medford Sq and the other Arlington Ctr to Malden Center.
5. **Fill the gap NERTA leaves at Columbia Point.** Start 16 Columbia Rd at JFK/UMass instead of Andrew, and run it on down Mt Vernon St to Dorchester Bay City, UMass Boston and the Columbia Point ferry dock. The city already plans bus lanes on that street.

Net result: 32 drafts become 23 trams, plus one optional Seaport stub (section 4).

---

## 2. How this was checked

- **Overlap check.** Each tram's path (the MBTA bus shape in `tram_draft.json` and `tram_extra.json`) was measured against NERTA rail: T lines as straight chords between their real station spots from `stations_real.geojson`, in `lines()` order, and commuter rail as real track from `rail_regional/lines.geojson`. "Beside rail" means a stop-to-stop leg runs at least 60% within 250 m of a NERTA line. Chords are rough on curvy lines (the Green D, the Orange Saugus dash), so those cases also use judgment.
- **Sources.** The bus shapes and stop lists come from the MBTA alone, so the measured overlaps rest on **one source family** (question 5). Every verdict is my judgment from those numbers plus the facts in section 5, each labeled Two, One or unverified.
- **Rejected list checked.** Nothing below adds a Trapelo Rd stop, a River Works stop, an East Saugus stop, or an offshoot on the Rejected list. The 73 stays off.
- Scripts: `overlap.py` and `legs.py` in this session's scratchpad (`C:\Users\mhowe\AppData\Local\Temp\claude\8c6edb261a248c64\0653f160-55cf-4699-8cf8-94186486f157\scratchpad\`). Read-only.

---

## 3. Per-route verdicts

Kilometers are from the overlap check. "Weak" marks a call that rests mostly on judgment.

### The first 13 (`tram_draft.json`)

| Route | Verdict | Change | Basis |
|---|---|---|---|
| 66 Harvard St | Keep | No route change. It shares Huntington Ave with the E for about 1 km (Brigham Circle to Riverway); that's a shared street, not a duplicate. Meets the 70 at Barrys Corner, by Harvard's new Allston campus | Biggest crosstown gap; Bus Priority Vision corridor (Two, `bus-exploration`) |
| 1 Mass Ave | Trim: Central to Boston Medical | Cut Harvard to Central (1.4 km, all within 250 m of Red, which runs under Mass Ave) and Boston Medical to Nubian (1 km on top of the Orange branch and Yellow) | Overlap check. The real gap is MIT, Back Bay and the South End (Two, `bus-exploration`) |
| 70 Western Ave and Arsenal St | End at Waltham | Cut the 2.3 km tail past Waltham Center to Market Place Dr. The last 2.2 km into Waltham already runs beside the Red Waltham branch | Overlap check. Arsenal St project (Two, `bus-exploration`) |
| 71 Mt Auburn St | Keep | No change. Ends at Watertown (Green A) and Harvard | Bus lanes running today (Two, `bus-exploration`) |
| 16 Columbia Rd | Reroute and extend | Start at JFK/UMass, not Andrew: the Andrew to South Bay detour runs beside Yellow's Newmarket to JFK/UMass leg. Then extend east on Mt Vernon St to Columbia Point (section 4A). Keep the Forest Hills end | Overlap check; Columbia Rd corridor (Two, `bus-exploration`); Mt Vernon St (section 5) |
| 15 Dudley St | Trim: start at Nubian | Cut Ruggles to Nubian: it runs beside Orange to Roxbury Crossing, and Ruggles to Nubian is one Yellow stop. Keep Nubian, Uphams Corner, Fields Corner | Overlap check |
| 22 Talbot Ave and Columbus Ave | Trim: start at Jackson Sq | Cut Ruggles to Jackson Sq: 1.8 km on Columbus Ave, all within 250 m of Orange. Keep Egleston, Seaver St, Talbot Ave, Codman Sq, Ashmont | Overlap check. Columbus Ave lanes (Two, `bus-exploration`) |
| 23 Washington St, Dorchester | Trim: start at Grove Hall | Cut Ruggles to Grove Hall: Yellow covers Ruggles to Nubian, and Warren St (1.5 km) is the Orange Blue Hill Ave branch. Keep Grove Hall, Four Corners, Codman Sq, Ashmont | Overlap check. Codman Sq has no NERTA stop |
| 31 Morton St | Reroute: end at Morton St (Indigo) | At Wellington Hill, stay on Morton St 0.8 km east to Morton St station instead of riding 1.9 km down Blue Hill Ave under the Orange branch to Mattapan. Old detour to reach a far station | Overlap check. Going on to Ashmont along Gallivan Blvd would be invented (question 4) |
| 9 Broadway | Trim: Copley to Broadway | Cut Broadway to City Point (3.7 km near Cyan's South Boston stops). Keep the South End link, Copley to Dover to Broadway | Overlap check |
| 111 Chelsea | Keep, end at North Station | No route change except ending at North Station (the Tier 1 hub, with Langone Ferryport) instead of Haymarket next door. The Tobin crossing stays: Chelsea has no subway, and Yellow goes around | 111 carries about 7,500 riders a day (One, TransitMatters in `05-boston-subway.md`); corridor (Two, `bus-exploration`) |
| 116 Inland Revere | Keep | No change. Meridian St, Chelsea and inland Revere sit between Blue on the coast and Yellow | Inland Revere gap (Two for the corridor, `bus-exploration`) |
| 110 Revere and Everett | Trim: end at Revere Beach | Cut Revere Beach to Wonderland (0.5 km beside Blue, one stop). Keep the Wellington start: it's the only tram linking Everett to Wellington, which Yellow doesn't | Overlap check |

### Max's 19 (`tram_extra.json`)

| Route | Verdict | Change | Basis |
|---|---|---|---|
| 216 Houghs Neck | Keep | No change. Only 7% of it is anywhere near rail. Lowest priority of the keepers | Overlap check |
| 101 Medford Sq | Trim: Sullivan to Medford Sq | Hand the Medford Sq to Malden Center leg to the 95. Keep Broadway through Winter Hill, which no rail touches | Medford Sq has no NERTA stop |
| 34 Dedham | Merge into 34E | Same street as 34E from Forest Hills to Dedham. Its Dedham Mall end could be a short branch if Max wants the mall | Overlap check |
| 34E Walpole | Trim: Roslindale Village to Dedham Sq | Cut Forest Hills to Roslindale Village (1.9 km on top of Orange) and Dedham to Walpole (3.4 km within 250 m of the Franklin Line, which stops at Norwood and Walpole) | Overlap check |
| 225 Weymouth Landing | Drop | Quincy Center to Weymouth Landing is already two rail rides: Red to Weymouth and the Greenbush Line. The Quincy Ave stretch is pod country | `lines()` (Red to Weymouth is dashed, One source, `line_audit.md`) |
| 100 Fellsway | Drop (weak) | The first 1.2 km runs beside Orange, and the rest is a parkway between Orange and the Green E. Keep only if every Wellington spoke matters | Overlap check, judgment |
| 222 East Weymouth | Merge into 220 | Shares Quincy Center to North Weymouth with the 220. East Weymouth is a Greenbush stop with direct trains to Quincy Center | Overlap check, `CR_STOPS` |
| 64 Oak Sq | Drop | Kendall to Central runs under Red; Yellow runs West Station to Kendall; West Station to Oak Sq runs 3 km within 250 m of the Worcester Line, and Green A serves Oak Sq. Boston Landing loses its tram (question 3) | Overlap check |
| 240 Randolph | Trim | Start at Central Ave on the Mattapan line, not Ashmont: Ashmont to Central Ave runs beside the trolley. End in Randolph's town center and drop the run on to Avon. Long and thin through the Blue Hills either way (weak) | Overlap check, judgment |
| 220 Hingham | Keep, absorb 222 | Quincy Center, Quincy Point and the Fore River, North Weymouth, Hingham Shipyard ferry dock, Hingham. The coastal side the Greenbush Line misses | Hingham Shipyard dock (Two, `line_audit.md`) |
| 455 Lynn and Salem | Trim: Central Sq (Lynn) to Salem | Cut Wonderland to West Lynn: Route 107 across the Saugus marsh, with Blue beside it. Keep Lynn, Swampscott, Vinnin Sq, Salem. Even this half runs near the commuter line for long stretches, so it could go too (weak) | Overlap check |
| 215 West Quincy | Keep | No change. The only link between Red's two southern branches, through East Milton and West Quincy | Overlap check |
| 95 Mystic Ave | Reroute: Arlington Ctr to Malden Center | Drop the Sullivan to Medford Sq half on Mystic Ave (I-93 frontage; the 101 gives Medford Sq its Sullivan link). Take over the 101's Medford Sq to Malden Center leg. Result: a crosstown from Red at Arlington Ctr, Green at West Medford, to Orange and the Haverhill Line at Malden Center | Overlap check, judgment |
| 75 Huron Ave | Keep, absorb 78 | Harvard to Belmont Ctr. A direct crosstown where Red goes the long way round by Alewife | Overlap check |
| 712 Winthrop | Drop | Orient Heights to Winthrop Center is Blue's Winthrop branch (1.3 km, 95% within 250 m). The 1.5 km Point Shirley tail is pod country | Overlap check |
| 78 Arlmont | Merge into 75 (weak) | Its first leg is the 75's Concord Ave start. The Belmont Hill and Arlmont end is low density and ends 1.3 km from Red at Arlington Heights | Overlap check, judgment |
| 106 Lebanon St | Reroute: start at Everett Sq | Drop the Wellington and Santilli Circle start: an old detour to reach Orange before Everett had a station. Start at Everett Sq (Yellow), then Main St, Malden Center, Lebanon St | Overlap check |
| 60 Route 9 | Drop | The Green D runs beside Route 9 from Brookline Village to Chestnut Hill, and Kenmore to Brookline Village is Yellow, D and E. The Chestnut Hill mall is about 1.2 km from the D | Judgment from the map; the chord check undercounts the D |
| 38 Centre St, West Roxbury | Drop (weak) | Orange's VFW Parkway extension runs the Needham Line through West Roxbury. Forest Hills to South St sits on the E extension, and past Bellevue it runs beside Orange. The unique middle borders the Arboretum and parkland | Overlap check, judgment |

---

## 4. Proposed new corridors

| | Corridor | Street | Why | Status |
|---|---|---|---|---|
| A | **Columbia Point**, as the 16's new east end: JFK/UMass, Mt Vernon St, Dorchester Bay City, UMass Boston, Columbia Point dock | Mt Vernon St (real) | Dorchester Bay City is a $5B, 21-building, 36-acre project; JFK/UMass is about 1.5 km away. The city plans bus lanes on Mt Vernon St for a future frequent route, and its station plan looks at a ferry tied to JFK/UMass | Street redesign: Two. Bus lanes and frequent route: One. Ferry dock: Two. A tram here is **invented** |
| B | **Marine Park stub** (optional): Seaport, Northern Ave, Tide St, Drydock Ave, Design Center, Black Falcon Ave | The SL2's real streets | The Raymond L. Flynn Marine Park is about 1 km past Cyan's Seaport stop. Today's SL2 loops there, and a 2026 city plan calls for a priority shuttle | SL2 route: Two. Shuttle plan: Two, both snippets. A tram here is **invented**, and pods may do |
| C | **Morton St to Ashmont** (optional, with the 31): Morton St station, then Gallivan Blvd to Ashmont | Gallivan Blvd (real) | Would tie Forest Hills, Indigo and Red together across the south | **Invented.** No proposal found |

### Gaps checked, by site

| Site | NERTA rail there | Tram needed? |
|---|---|---|
| Columbia Point (Dorchester Bay City, UMass Boston) | None on the peninsula | **Yes:** corridor A |
| Seaport (Marine Park end) | Cyan and Yellow in the core | Maybe: corridor B |
| Suffolk Downs (16.2 million sq ft, about 10,000 homes) | Blue at Suffolk Downs and Beachmont, ferry dock | No. Two Blue stops sit on the site |
| Assembly and Everett waterfront, Stadium | Orange, Cyan, Yellow; Encore and Stadium stops | No. The stadium deal also pays for a new Assembly entrance toward a footbridge |
| Widett Circle | Newmarket (Yellow, Indigo), Broadway (Red, Cyan) | No. The MBTA bought it for a layover yard; NERTA's through-running is the reason it could become a neighborhood |
| Beacon Yards, West Station, Allston | West Station (Blue, Green, Yellow, commuter rail), Green A and B | No new tram. 66 and 70 meet by Harvard's Enterprise Research Campus off Western Ave. Boston Landing is the one loss (question 3) |
| Boston Central | Cyan, every commuter line, high-speed rail, walkways to Park and Downtown Crossing | No |
| Codman Sq, Medford Sq | None | Covered by 22 and 23, and by 95 and 101 |

Side note for the ferry session: the city's capital plan lists a Pier 10 ferry terminal in the Marine Park with service to North Station, "in design" (One). That would land at Langone Ferryport.

---

## 5. Facts used, and their sources

"Read" means I read the page. "Snippet" means a search summary only.

| Fact | Source 1 | Source 2 | Agree or differ | Status |
|---|---|---|---|---|
| Dorchester Bay City: $5B, 21 buildings, 36 acres on Mt Vernon St and Morrissey Blvd; master plan approved September 2023 | [Boston Globe via Boston.com, Sep 15, 2023](https://www.boston.com/news/the-boston-globe/2023/09/15/massive-dorchester-bay-city-project-gets-green-light-from-bpda/) (snippet) | [Banker & Tradesman, 99-year lease](https://bankerandtradesman.com/accordia-inks-99-year-bayside-lease-clears-way-for-redevelopment/) (snippet) | Agree on the project and site. One report gives 1,900 homes; not checked | Two |
| Mt Vernon St is slated for redesign | [Boston Planning, Mt Vernon Street Design, 2014-15](https://www.bostonplans.org/planning/planning-initiatives/mt-vernon-street-design) (snippet) | [Dorchester Reporter, Oct 31, 2024](https://www.dotnews.com/?p=68538) (read) | Agree on a redesign. The 2015 plan kept the car lanes; the 2024 plan swaps one lane each way for a bus lane | Two |
| Bus lanes on Mt Vernon St for a planned frequent route, UMass Boston to JFK to South Bay, Boston Medical, Copley; a Columbia Point ferry tied to JFK/UMass by frequent bus as a longer-term idea | Dorchester Reporter, Oct 31, 2024 (read) | [City, JFK/UMass Station Area Action Plan](https://boston.gov/departments/transportation/jfkumass-station-area-action-plan) (read) mentions exploring ferry service only | The city page confirms the ferry idea, not the lanes | Lanes: One, unverified. Ferry idea: Two |
| Suffolk Downs: about 16.2 million sq ft; about 10,000 homes | [REBusiness](https://rebusinessonline.com/partnership-breaks-ground-on-16-2-msf-mixed-use-redevelopment-of-suffolk-downs-racetrack-near-boston/) (snippet) | [Bisnow](https://www.bisnow.com/boston/news/mixed-use/suffolk-downs-groundbreaking-113170) (snippet) | Agree on about 16 million sq ft. The 10,000 homes figure came from search summaries citing several reports | Two for floor area; homes One |
| Widett Circle: MBTA bought 24 acres for $255M, April 2023, for a commuter rail layover yard | [Boston Globe, Apr 12, 2023](https://www.bostonglobe.com/2023/04/12/business/mbta-completes-purchase-widett-circle-plans-old-meatpacking-district-become-railyard) (snippet) | [Trains.com](https://www.trains.com/pro/passenger/commuter-regional/mbta-completes-purchase-of-land-for-new-commuter-yard) (snippet) | Agree | Two |
| Harvard's Enterprise Research Campus, 36 acres off Western Ave, under construction | [Harvard Allston Land Co.](https://halc.harvard.edu/) (snippet) | [GlobeSt, 2019, Tishman Speyer picked](https://globest.com/2019/12/23/tishman-speyer-tabbed-as-preferred-developer-for-harvard-u-enterprise-research-campus) (snippet) | Agree the campus exists. The Western Ave location is Harvard's own wording | Two for the project; location One |
| Revolution stadium on the 43-acre Mystic plant site; Everett's deal pays $17.5M for a new Assembly entrance toward a footbridge | [Boston Globe, Dec 31, 2025](https://www.bostonglobe.com/2025/12/31/business/kraft-soccer-stadium-everett-revolution) (snippet) | [CBS Boston](https://www.cbsnews.com/boston/news/new-england-revolution-soccer-stadium-kraft-group) (snippet) | Agree. Permits still pending | Two, both snippets |
| SL2 loops the Design Center via Northern Ave, Tide St, Drydock Ave and Black Falcon Ave | [Wikipedia, Silver Line](https://en.wikipedia.org/wiki/Silver_Line_(MBTA)) (snippet) | [MBTA SL2 route profile](https://d2o8eokdkim9o8.cloudfront.net/sites/default/files/projects/betterbus/route-profiles/SL2.pdf) (snippet) | Agree | Two |
| Marine Park growth calls for transit upgrades; a priority shuttle is planned | [Boston Planning, Marine Park transportation committee, Mar 2026](https://www.bostonplans.org/documents/planning/coastal-resilience/raymond-l-flynn-marine-park-flood-mitigation-plann/raymond-l-flynn-marine-park-transportation-advisor) (snippet) | [Banker & Tradesman](https://bankerandtradesman.com/ferry-and-bus-upgrades-tied-to-marine-park-growth) (snippet) | Agree on the need; only the city deck names the shuttle | Two for the need; shuttle One |
| Pier 10 ferry terminal to North Station, in design | [City of Boston FY26-30 capital plan](https://www.boston.gov/sites/default/files/file/2025/11/Planning%20Cabinet%20Capital.pdf) (snippet) | none | — | One, unverified |
| Bus corridor facts (Harvard St, Mass Ave, Columbia Rd, Arsenal St, Columbus Ave, Mt Auburn St, Chelsea, inland Revere) | `research/bus-exploration-2026-11-07.md` | same file's second sources | See that file | As labeled there |

---

## 6. Open questions for Max

1. Seven of your 19 go (64, 225, 60, 712 firmly; 38, 100, 78 as weak calls). OK to cut, or keep any?
2. Mass Ave: trim to Central to Boston Medical, or keep the Harvard and Nubian ends for a one-seat ride?
3. With the 64 gone, Boston Landing has no tram. Leave it to pods, or keep a short West Station, Boston Landing, Oak Sq tram?
4. Should the 31 stop at Morton St (Indigo), or go on along Gallivan Blvd to Ashmont (invented)?
5. DO YOU WANT TO OVERRIDE THE TWO-SOURCE RULE FOR THE MBTA BUS SHAPES AND STOP LISTS BEHIND THE OVERLAP CHECK? THEY COME FROM THE MBTA ALONE, SO THEY COUNT AS ONE SOURCE.
