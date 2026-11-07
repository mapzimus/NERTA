# Day 8 network proposal: what if the MBTA covered all of New England

Draft for Max to mark up. Nothing is drawn yet. Sources and fact labels are in `research/`. Stop lists and line pairings here are judgment calls unless the research file says otherwise.

## The sorting rule

Every line on the map gets one of three looks, so people can see how real it is:

| On the map | Meaning | Comes from |
|---|---|---|
| Solid, today's style | Exists today | Current MBTA and other services |
| Solid, new | Real proposal or strong case | "Makes sense" verdicts |
| Dashed | Imagined | "Fantasy only" verdicts that close a real gap |

"Doesn't make sense" lines are left off.

## 1. The Bigger Dig and Boston Central

- **Tunnel:** four tracks between North Station and South Station. Four tracks is the state's rejected, costlier design ($21.53B in 2028 dollars, against $13.22B for two tracks). It's the only design that had a Central Station.
- **Boston Central:** the main hub, under State Street (Blue and Orange), with a walkway to Government Center (Green). This site is our invention. The state's four-track site was at Aquarium.
- **North and South Station:** stay open as through stops. Greenbush and Kingston/Plymouth can keep ending at South Station's surface tracks.
- **Must fix:** the single-track stretch between Quincy and JFK/UMass, which limits Old Colony trains to about 6 an hour.

## 2. Through lines

Based on the state's four-track pairings, then extended. Line letters are placeholders.

| Line | South or west end | Through Boston to | Status of the extensions |
|---|---|---|---|
| A | New Haven, New London, Westerly, Providence | Lowell, Nashua, Manchester, then Concord | Shoreline and Lowell to Manchester solid new; Concord dashed |
| B | Springfield, Worcester | Salem, Newburyport, then Portsmouth | Worcester to Springfield solid new; Portsmouth dashed |
| C | Milford, Franklin | Haverhill, Plaistow, Dover, Portland, Brunswick, Rockland | Mostly solid new. Uses the Downeaster route |
| D | Needham line removed (Orange and Green take over) | Haverhill short trips need a new partner | Open. Candidates: Dedham or Foxboro trains |
| E | Fairmount | Fitchburg, Gardner, Greenfield, then North Adams | Past Fitchburg dashed. All six Northern Tier options had negative benefit-cost |
| F | Fall River, New Bedford | Rockport | Dashed through the tunnel. Today's service stays |

**Added stops on existing lines:** Peabody branch, Everett at Encore, South Salem, West Station, Plymouth reopened.

## 3. Lines that don't run through Boston

| Line | Route | Status |
|---|---|---|
| Valley | New Haven, Hartford, Springfield, Northampton, Greenfield, Brattleboro, White River Jct, Montpelier, Essex Jct, St. Albans, to Montréal | Solid new to White River Jct and St. Albans; Montpelier segment dashed |
| Champlain | Burlington, Rutland, then Bennington | Burlington to Rutland exists; Bennington dashed |
| Berkshire | Springfield, Westfield, Pittsfield, to Albany | Solid new |
| Housatonic | Danbury to Pittsfield | Dashed. One regional operator removes Connecticut's objection |
| Blackstone | Providence, Pawtucket, Woonsocket, Worcester | Solid new, stops are judgment |
| Cape | Buzzards Bay, Bourne, Hyannis | Solid new to Bourne; Hyannis dashed |
| Granite | Concord to Lebanon and White River Jct | Dashed. Rails are gone, but it's the signature line |
| Pine Tree | Brunswick, Augusta, Waterville, Bangor; Portland to Lewiston-Auburn | Dashed. Lewiston track reportedly abandoned, ONE SOURCE |
| Seacoast | Dover to Rochester | Solid new |

**Off the edge:** New York, Albany and Montréal. Québec City and Saint John are dropped.

## 4. Boston subway (for the Boston box)

| Line | Add | Look |
|---|---|---|
| Blue | Lynn; Red-Blue Connector to Charles/MGH | Solid new. Stops at Lynn on purpose |
| Orange | Roslindale, West Roxbury, VFW Parkway | Solid new, replaces that end of the Needham Line |
| Red | Arlington Heights | Solid new, the Minuteman fight |
| Green | Route 16, Hyde Square; dashed to Nubian and Seaport | Mixed |
| Silver | SL3 through Everett to Sullivan | Solid new |
| Yellow (new) | 26-stop horseshoe: Logan, Chelsea, Everett, Sullivan, Kendall, Longwood, Nubian, Seaport, with a dashed Harvard branch | Dashed, Grand Junction part solid |

**Left off:** Blue to Beverly, Red to Hingham, Red to Dudley, Green to Woburn.

## 5. City systems

| City | System | Basis |
|---|---|---|
| Providence | Light rail | Real study: 17,000 to 19,000 daily riders |
| Hartford | Light rail, converting the CTfastrak busway | Strongest fantasy case, but no real proposal |
| Worcester | Light rail: Union Station, Main South, Lake Quinsigamond | Just short of the bar, no real study |
| Portland | One light rail line: Gorham, Westbrook, downtown | Follows the real bus rapid transit corridor |
| New Haven | Small light rail | Fantasy |
| Springfield, Burlington, Manchester, Bridgeport | One short streetcar each | Fantasy. Research says these don't need more |

No real subway fits anywhere outside Boston. These are small light rail or streetcar systems, even if the map calls them "subway" in spirit.

## How two reports were reconciled

- **Blue to Lynn:** one report said makes sense, the other fantasy. Drawn solid. 101,000 people with no rapid transit, and studied since 1926.
- **Red to Arlington Heights:** same split. Drawn solid, since the Town Meeting vote makes it live.
- **Urban Ring:** fantasy as a whole, so Yellow is dashed, except the Grand Junction section.

## Decisions for Max

1. **Needham Line (decided):** Orange takes the West Roxbury end. Green to Needham (dashed) covers the rest, so the Needham commuter line goes away and Line D below needs a new southern partner.
2. **Tunnel name (decided):** the map label is "The BIGGER Dig", capitalized that way. No extra tagline.
3. **City systems (decided):** keep all nine.

## What isn't verified yet

- Many facts are ONE SOURCE or from search excerpts, labeled in the research files. NH and Maine is the weakest report.
- Before any number goes on a map, it needs two sources or Max's override.
- Tunnel and Boston Central geometry is invented for this map, and buildability at State Street is unchecked.
- Real line and stop geometry still has to be gathered.

## Changes after Max's review (2026-11-04)

The single New England map is replaced by two posters in the T wall-map style: Boston metro (`src/make_tmap.py`) and regional commuter rail (`src/make_regional.py`). Northern and central NH, ME and VT are dropped, so Burlington, Bangor, the Granite and Pine Tree lines and the Champlain line are off the map.

- **Logan West Garage removed.** It was a stop on the 2009 Urban Ring fact sheet (ONE SOURCE, `research/05-boston-subway.md`), not useful to riders. Yellow now ends at Logan Terminals, standing in for the people mover Massport studied in 2018 (status now unknown).
- **Revolution Stadium** stop added on Yellow next to Encore. The stadium is not built or fully approved.
- **Newburyport/Rockport** now runs through Chelsea (a real stop today) and Everett at Encore (proposed, Wynn up to $25M), and stays on land past Lynn to Salem.
- **Peabody** striped, **Danvers** dashed, as a branch from Salem.
- **Blue** dashed from Charles/MGH to Kendall. Focus40 says "and Beyond" without a place, so Kendall is judgment. Bowdoin stays on the map, though the real connector plan closes it.
- **Added dashed:** Orange to Reading, Green to Watertown, Green Union Square to Porter.
- **Yellow:** Cambridgeport left off for label room. Chelsea on the map is the Mystic Mall commuter rail station. Bellingham Square added. Harvard branch rerouted so West Station sits on the Worcester Line.
- **Haverhill** moves to the Wildcat Branch and joins the Lowell Line, because Orange takes the Reading corridor. Harvard's model and TransitMatters both discuss this split.
- **In-city stops added:** North Cambridge on Red (a resident's request to the MPO, not a study), Sullivan commuter rail superstation (Focus40), Union Square Allston on the dashed Watertown branch.
- **Regional accuracy:** Saco replaces Biddeford, Braintree and Canton Junction are now the junctions, Bourne to Hyannis is striped because the CapeFLYER runs it on summer weekends.
- **Silver Line and buses** left off the Boston map.

## Second review and fantasy additions (2026-11-04)

Money is no object, per Max. All of these are dashed and imagined.

- **Boston:** Red to Lexington and Route 128, Red to Waltham, Orange to Dedham, Green from Nubian up Blue Hill Ave to Mattapan, Blue to Mass Ave/MIT (replaces the Kendall hook), Yellow closes into a full ring with a tunnel from the Seaport to Logan.
- **Region:** New London, Norwich, Putnam, Worcester; Hartford, Willimantic, Providence; Bradley Airport spur; Waterbury to Torrington; Fall River to Newport; Bourne to Woods Hole; Hyannis, Orleans, Provincetown.
- **Yellow** now crosses Orange at Sullivan only, not Assembly. The real footbridge to Assembly is left to the imagination.
- **Coast:** South Boston and Dorchester anchored by hand so every stop is on land. Rivers on the Boston map are hand-drawn.

**Regional map, later change:** city light rail and streetcars removed at Max's request. The T subway lines, including the fantasy ends at Lexington, Waltham, Reading and Dedham, now reach out from Boston Central on the commuter map. "City systems (decided): keep all nine" above is superseded on this map.
- **Portsmouth to Dover** added, dashed, so the Rochester line reaches Portsmouth (Max, 2026-11-04). Whether usable track survives on this link is unchecked.
- **Danvers to Lawrence** added, dashed, via Middleton: the old Essex Railroad corridor. Most of it was abandoned in 1927 (sources differ on dates).
- **Orange branch to Saugus** added, dashed, from Malden Center through Linden Square and Cliftondale along the old Saugus Branch (Max, 2026-11-04).
- **Blue to Lynn** runs nonstop from Wonderland: River Works and West Lynn removed at Max's request.

## Third pass (2026-11-04)

- **Cyan Line (new, dashed):** Winthrop Center, Logan Terminals, tunnel to City Point, South Boston, Broadway. Built for two of the biggest gaps left, Winthrop and South Boston. All invention.
- **Indigo Line:** Fairmount drawn as rapid transit, after the state's Indigo Line idea. Green reaches Mattapan by Blue Hill Ave.
- **Orange** runs on from Saugus through East Saugus to Lynn on the old Saugus Branch.
- **New names:** Hartwell Ave, Mystic Valley, Allston Village, Convention Center, Melrose Highlands, Boston Medical, MIT.
- **Rivers** redrawn so stops sit on their true banks. Regional Cape restored to its real shape.
- **Indigo** runs into South Station (Max, 2026-11-04), as the Fairmount Line does today.
- **Fairmount rapid transit is now the Pink Line**, not Indigo: indigo read as commuter rail purple, which some riders call the Purple Line (Max, 2026-11-04).
- **Each new line now has one job.** Yellow is the closed ring around the core. Cyan is rebuilt as Winthrop, Orient Heights, Eagle Hill, Maverick, a tunnel under the inner harbor, Courthouse, then two ends at Broadway and City Point. Pink is the Fairmount corridor. Yellow no longer runs beside Cyan in the harbor or through South Boston.
- **Peabody and Danvers** no longer branch from Salem. A dashed line leaves the Rockport line at the proposed South Salem stop, runs to Peabody and Danvers, and continues through Middleton to the Haverhill line at Lawrence, roughly the old Essex Railroad (Max, 2026-11-04).
- **Seaport** replaces the World Trade Center name on the Yellow and Green transfer station (Max, 2026-11-04).
- **Blue Hill Ave** is now a dashed Orange branch from Ruggles to Mattapan, after the 2026 city councilor proposal. Green ends at Nubian.
- **Cyan** ends at Seaport. West Broadway and City Point are removed, so South Boston east of the Convention Center is an open gap again.
- **Green B** runs on from Boston College through Newton City Hall to Norumbega, on the old Commonwealth Avenue Street Railway median. Evidence for every line is in `data/line_audit.md`.

## Fourth pass (2026-11-04)

- **Cyan rebuilt (Max's design):** Assembly, Encore, Revolution Stadium, Charlestown (new dedicated station), Navy Yard, City Square, North Station, Aquarium, Boston Central, Fort Point, Seaport. City Square was a real Orange Line stop on the Charlestown Elevated, closed in 1975. Thompson Square is replaced by the new Charlestown station.
- **Yellow** keeps Everett Square and Chelsea, and meets Cyan at Revolution Stadium.
- **Indigo restored** in name and color. It was a real plan, so the Pink Line is gone. Stops are the real Fairmount list. South Bay removed (invented).
- **Indigo Track 61 branch:** Broadway, West Broadway, Convention Center, then dashed to City Point. Links Dorchester to South Boston, after the city's Track 61 idea.
- **Blue to Winthrop** dashed from Orient Heights, on the old Narrow Gauge Winthrop loop (closed 1940).
- **Ferries** drawn as on the real wall map.
- **Newton:** B runs west from Boston College to Newton City Hall and Norumbega, and Watertown moves closer.
- **Allston and Brighton:** the Watertown branch stops at Allston, Brighton Center, Oak Sq and Newton Corner.
- **Cyan final order:** Seaport, Fort Point, Boston Central, Aquarium, North Station, City Square, Navy Yard, Charlestown, Revolution Stadium, Encore, Assembly (Max chose this over ending at Chelsea). Yellow meets Cyan at Revolution Stadium.
- **Green to the Seaport removed.** Green stays to Nubian. Cyan now carries Courthouse and transfers at South Station, so the Seaport keeps a downtown link.
- **Kendall** replaces the Kendall/MIT label (Max, 2026-11-04). The separate Mass Ave stop on Yellow and Blue is labeled MIT.

## Fifth pass (2026-11-04)

- Southie: L Street added, the whole Indigo branch dashed.
- E continues through Hyde Square to Forest Hills, and Green runs on to Hyde Park.
- Walkway ties Downtown Crossing into Boston Central, after the Focus40 superstation.
- Red terminal renamed Lexington Route 128.
- Regional: Manchester Airport and T.F. Green stops, Route 128 ring, Indigo, ferries.
- **Mass & Cass Treatment Center** is the stop name, at Max's request (2026-11-04). It is not a real facility name.

## Sixth pass: decluttering (2026-11-04)

Rule from Max: only North Station, South Station and Boston Central carry more than two lines.

- **Removed:** Green to Nubian, Green Union Sq to Porter, Orange past Saugus Center, Yellow's Harvard branch, Blue past Charles/MGH, Bowdoin (the real connector plan closes it), Lynn ferry, Waverley and Belmont commuter rail labels, Indigo's South Boston branch.
- **Sullivan** and **Revolution Stadium** lose their commuter rail links, so they stay two-line stations.
- **Cyan** now continues past Seaport around City Point and along Broadway to Red at Broadway, so the Seaport connects to Southie.
- **Blue Hill Ave branch** now leaves Orange at Mass. Ave and crosses Yellow once at Mass & Cass, so Nubian is a plain Yellow stop. This differs from the real proposal, which branches at Ruggles.

## Station tiers (Max, 2026-11-04)

- **Tier 1:** Boston Central, with high-speed rail to New York.
- **Tier 2:** North Station, South Station, West Station. Commuter rail can start here.
- **Tier 3:** all other subway stations.
- **Tier 4:** small commuter rail stops.
- **Blue** extends past Charles/MGH through MIT to West Station.
- **Bowdoin closes**, as in the real Red-Blue Connector plan. Real lines keep their shape and the new map builds on them. West Station links to the Green Line at Kenmore. The real walk is longer than the map suggests.
- **Lynn Harbor** added on Blue between Wonderland and Lynn, near the Lynnway (Max, 2026-11-04).

## Seventh pass (2026-11-04)

- **South End gap:** the Blue Hill Ave branch now follows the old Washington Street Elevated from Tufts Medical through revived Dover and Northampton stations to Nubian, then the councilors' corridor to Mattapan. Mass & Cass goes back to a Yellow-only stop.
- **Inman Square:** Green's Union Square branch extends one stop to Inman.
- **Riverside to Auburndale** dashed. Right of way exists per one opinion piece.
- **Newport** now connects to Providence through Bristol, on the old Providence, Warren and Bristol corridor (East Bay Bike Path today) plus a new bridge.
- **High-speed rail** added to the Boston key.

## Scope change (2026-11-04)

The regional commuter rail map is dropped for now. Day 8 is the Boston T map only. `src/make_regional.py` and `output/regional_map.png` stay in the folder, unused. README and captions still describe two maps and need rewriting.

## Eighth pass (2026-11-04)

- **Coast rebuilt** with waterfront anchors only and heavier smoothing, so inland schematic moves no longer tear the shoreline.
- **Aquarium renamed Long Wharf** (Blue and Cyan).
- **Old North:** new Cyan stop for the North End, near Hanover Street and the Old North Church.
- **Harbor Loop ferry** (Max's route): Long Wharf, North End, Lovejoy Wharf, up the Boston bank of the Charles, turning just past the Harvard Bridge, down the Cambridge bank, Charlestown, the Mystic, Chelsea Creek, East Boston, Logan Dock, Fort Independence, Seaport, back to Long Wharf. The stops are invented; the MBTA did announce a route called Harbor Loop for 2026, but this is a different route.
- **Hingham/Hull ferry** rerouted over water.

## Ninth pass (2026-11-04)

- Subtitle is now "What if the T went everywhere?". Pill row and title rule removed; pills sit at line ends as on the poster, with the GL letter in a circle.
- Accessibility icons added from the MBTA V3 API (`data/wheelchair.csv`, one source). New stops are drawn as accessible.
- Charles basin widened from the locks to just past the Harvard Bridge, wider than life, to hold the ferry's two lanes. Ferries are routed by computer through open water; track over land measures 0.
- **Harbor Loop** now runs up the Mystic to a dock at Encore.

## Tenth pass: research brief

From Max's siting brief (one document; sources it cites not yet checked). West Station added to Yellow via the Grand Junction. Green ends at West Medford, not Mystic Valley, with the Lowell line drawn west to meet it. East Arlington added. Needham spur now leaves Eliot, in true order: Needham Heights, then Needham Junction. Callout places Boston Central under Atlantic Avenue. High-speed line runs on to Maine. Cut: E to Hyde Park, B to Norumbega, D to Auburndale, Orange to Dedham. Red to Waltham kept by Max's choice. Ferry stops now sit on the shoreline; Lovejoy Wharf, Back Bay and MIT ferry labels dropped for room.

## Eleventh pass: names

Max's call: the T stop goes back to Aquarium, the new stop is North End (was Old North), and Long Wharf is the ferry stop. Labels moved off lines across the core.

## Twelfth pass

Stadium (renamed) is now a Yellow/Cyan transfer dot. Longwood Medical Area is one station joining Yellow in the core to the E, and that real E stop is now drawn. Landmark Center added on Yellow between Fenway and Longwood (invented). City Square moved onto Charlestown land. Salem moved up the line. Blue runs through the Boston Central ring. High-speed runs to Montreal up the Lowell line and to Maine up the Newburyport line. Lynn ferry and Salem ferry split off Winthrop; Salem stays out to sea around Nahant and leaves the map, since Marblehead and Salem Harbor fall past the edge. Orange gains Wyoming Hill and Greenwood. Watertown line turns back at West Station. Tier 2 now reads through stations.

## Thirteenth pass: title

Title is now a T roundel with "Rapid Transit / Year 2050", replacing the tagline and subtitle; The BIGGER Dig is only the info box. Max asked for the T mark, reversing the earlier no-logo rule; the fan-map line stays. Sources line now black. Later moved to 2050.

## Fourteenth pass: West Station

West Station moved to where Yellow crosses the Worcester line, beside Kenmore and Hynes, joined to Kenmore by a transfer capsule, so Yellow keeps its old straight shape. Lansdowne is now a small commuter stop. Blue and the Watertown line reach West Station from the north and west. Roundel and title redrawn.

## Fifteenth pass

Green now joins the trunk at Hynes with no gap; the West-Kenmore pill is gone. Worcester line carries high-speed rail. Lynn ferry docks at Lynn Harbor. Salem and its arrow separated. Every dot, ferries included, has a fine black edge. Harbor Loop note: "follows a ferry chartered in 1631", two sources agree on 1631 and the Charlestown-Boston crossing (MBTA history page, Wikipedia on the Winnisimmet Ferry); they differ on the third landing, and "first in the country" is left off.

## Sixteenth pass

Fitchburg leaves to the northwest and carries high-speed rail to Burlington VT and Montreal. Lowell/Haverhill high-speed now reads Manchester NH, Newburyport reads Portland ME. Old Colony lines labeled South Shore / Cape Cod. Key row shortened to High-speed rail.

High-speed labels: Hartford and NYC on the Worcester line, Providence on the south line. South Shore / Cape Cod and the Danvers branch stay regular commuter rail.

## Seventeenth pass: track map

From the historic track map (research/06): Red to Lexington, Red to Waltham, Green to West Medford, E from Hyde Sq to Forest Hills and the Watertown line move from imagined to real proposal. Medford Hillside added.

## Eighteenth pass: routing

Routing check on all stop pairs. Watertown now meets the B with a transfer at Brighton Center and Harvard Ave. Green runs from Union through Inman to Harvard. Faint crosstown buses fill the remaining gaps, unnumbered: Forest Hills to Mattapan, Medford to Davis, Needham to West Roxbury, Roslindale to Readville. Year changed to 2050.

## Nineteenth pass

Buses removed at Max's call. Date removed; title is the roundel and "Rapid Transit".

## Twentieth pass

Orange's Saugus branch runs through East Saugus to Wonderland (new stop invented). River Works moved up the line toward Lynn. Lexington and Waltham joined by a Red link along Route 128 with a Trapelo Rd stop, making a loop (invented). Mission Park to Roxbury Crossing dropped: 0.74 miles by MBTA stop coordinates, and Yellow already links Longwood to Ruggles. Italics and their key line removed. Nahant causeway drawn.

## Twenty-first pass

Coast redrawn by hand as a schematic instead of bending the real one. Needham spur runs on through Hersey to VFW Parkway. Orange branch from Forest Hills through Hyde Park to Readville. Old Colony lines moved beside the Red, with transfers at JFK/UMass and Quincy Center; they had missed those stations. Stray Hyde Park commuter square now has its name. High-speed labels trimmed: Springfield and Albany on Worcester, Providence and NYC on the south line; Hartford dropped.

## Twenty-second pass

Line pills moved beside their lines. Back Bay is Tier 2. Key and Dig boxes tightened. Harbor ferries share one channel out of Long Wharf.

Cyan straightened along the Seaport.

## Twenty-third pass: type and cost

Type system for the title block, Key, Dig box and sources line. Wheelchair icons are vector shapes. Dig box carries three figures: $21.5B tunnel (MassDOT four-track estimate), $15B original Big Dig, ~$125B for the whole map. The last is our rough sum: tunnel $21.5B, regional rail $40.7B (Rail Vision, 2030 dollars), and about 110 new miles at the Green Line Extension rate of about $0.53B a mile. Mixed-year dollars, high-speed trains and ferries not counted.

## Twenty-fourth pass: real coast

Hand-drawn coast replaced with real Census shapes bent through matched shoreline points, so the Harbor Islands, Nahant and Hull appear. Georges Island added as a stop on the Hingham / Hull ferry. Stop review scored every new stop on residents and jobs within half a mile; scratch results are not in the repo.

## Twenty-fifth pass: stop review

Landmark Center removed (0.1 miles from Fenway). Franklin Park stop renamed Seaver St, on Blue Hill Ave. Charlestown stop renamed Thompson Sq. Plymouth added to the South Shore label. Dashed branches added to Marblehead and to Woburn and Burlington. Blue spur from Lynn to Wyoma Sq. Blue to Salem considered and dropped by Max.

## Twenty-sixth pass: Logan and the tunnel

Marblehead branch leaves South Salem and bends to the coast. Tunnel redrawn as four tracks, white local pair and gold express pair, with a Key row. "Terminals" replaces Logan Terminals, and Yellow runs straight with one long curve through Airport. Silver Line stays, as a short Logan shuttle running both ways from Logan Dock past the terminals and Rental Cars to Airport, meeting Yellow at Terminals. No documented name for the station beyond "Central Station"; Boston Central is ours.

## Twenty-seventh pass

East Saugus stop removed: the lookup had landed on a church in Pleasant Hills, not a real destination. Labels moved at Stadium, Thompson Sq, Bellingham Sq, Airport, Maverick and Rental Cars.

All station labels get a small white halo.

Marker check: a stop under a transfer pill has no dot, and no dot, pill or label overlaps another marker.

## Twenty-eighth pass

Added "Replacement shuttle buses: none" to the Key and a Duck Boats ferry label on the Charles. Captions and README reframed as a personal fantasy map, not a record of real plans. Rejected nods: Storrow, Scollay Sq, Citgo.

## Twenty-ninth pass: local touches

Lansdowne renamed David Ortiz. Long Island Recovery Campus added as a ferry stop. "364.4 Smoots" added by the Harvard Bridge. Duck Boats and the shuttle line stay.

Thirtieth pass: the Charles label is now the Smoots stop. Red extended from Braintree to South Weymouth, an older planned branch.

Thirty-first pass: Yellow moved toward Fenway and straightened from JFK/UMass to Seaport. Convention Center now sits where Yellow crosses Cyan. Duck Boats beside its dot. Smoots removed.

Thirty-second pass: Longwood is one transfer ring where Yellow crosses the E. Lines running today drawn heaviest, new branches lighter. Big station names enlarged. Commuter rail lines faded.

Thirty-third pass: Parking added to Silver. No transfer pill spans more than two line gaps: Watertown branch lowered to meet the B line, Gov't Center is its own crossing, Boston Central runs Orange to Cyan around the hub, North Station runs Green to the tunnel with a separate Cyan stop beside it.

Thirty-fourth pass: last Red stop renamed Weymouth, name moved west of the commuter rail. Encore name moved under its dot.

Thirty-fifth pass: high-speed edge labels rewritten with named routes, including a Springfield to New Haven link via Hartford, and Bangor replacing Portland as the northeast end.

Thirty-sixth pass: Springfield to New Haven via Hartford label removed. That leg is off the map, so it is not shown.

Thirty-seventh pass: Franklin now splits from the Providence line just south of Readville, Foxborough splits from Franklin at Walpole, and the Providence and Franklin lines are labeled separately.

Thirty-eighth pass: all 13 MBTA commuter routes accounted for. Added Stoughton, Haverhill, Rockport, Greenbush, Kingston and Fall River/New Bedford as their own branches with their own labels.

Thirty-ninth pass: new commuter stops and offshoots tied to real proposals. Stoughton to Taunton (South Coast Rail Phase 2), South Acton to Marlborough, Northern Tier label, Cape Cod via Middleborough. Sudbury, Lynnfield, Medfield and Millis removed.

Fortieth pass: Suffolk Downs drawn as a larger station, based on the planned redevelopment. Other development checks led to no map change.

Forty-first pass: Park Street and Downtown Crossing labels moved. Winthrop Landing ferry and Office Center Silver stop added. Suffolk Downs ferry not added: no proposal found.

Forty-second pass: North Station pill extended to Cyan. South Station label moved closer to its stop.

Forty-third pass: North Shore ferry runs to Nahant, Swampscott and Marblehead, then off the map to Salem and Gloucester. Squantum Point and Hingham Shipyard added on the South Shore.

Forty-fourth pass: Marblehead, Marblehead Neck and Salem Harbor brought inside the frame. Marblehead stop moved into town. Ferry routed around the Neck into Marblehead Harbor.

Forty-fifth pass: consistency audit. Line labels, stop name abbreviations and the Key were made uniform. Salem Wharf added, and the ferry arrow now reads To Gloucester.

Forty-sixth pass: all eight posters, a 2026-dollar cost panel, Airport as Tier 2. Day Sq added on Yellow and the Lewis Mall ferry stop labeled.

Forty-seventh pass: Moakley Park stop added on Yellow between JFK/UMass and Convention Center.

Forty-eighth pass: Key explains high-speed rail as express. Station wheelchair icons replaced by one Key note. River Works removed. High-speed pills limited to Tier 1 and 2 stations. Yellow poster redrawn as a parallelogram.

Forty-ninth pass: Logan Terminals renamed. Terminals D and F added. Red's Trapelo Rd loop removed so only Yellow wraps around. Tiers 1 and 2 enlarged. Ferry pills name their docks. Poster frames refit to each line, at 600 dpi. Stop count corrected to 215.

Fiftieth pass: Encore added to Yellow, sharing the Cyan stop's label. Stadium label moved. Full audit of stops, transfers and crossings run against all saved versions. Poster audit script added.
