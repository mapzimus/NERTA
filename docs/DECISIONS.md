# Decisions

What's been settled, so nobody reopens it by accident. Detail is in [history/decision_log_all_passes.md](history/decision_log_all_passes.md).

## The concept

- A personal fantasy, lightly grounded in reality. People should pore over it for hours and argue about it.
- Very unique. Other maps are for comparison, never copied.
- Local in-jokes reward zooming in, but they shouldn't push too hard.
- Title is "Boston's Rapid Transit", on two lines. No date on the map.
- **Sheet extent, after Day 8:** half an inch more on the top and right, at the same scale, for Beverly. `XLIM, YLIM = (-46, 229.4), (-20, 215.4)`. Day 8 used `(-46, 222), (-20, 208)`. The Danversport ferry dock is left off this map (Danversport is a commuter stop now): it would need about an inch on top, and without the Danvers River it looks wrong.
- Max's disclaimer paragraph in the title block replaces "NOT A REAL MBTA MAP" on the main map.
- Keep the T, unchanged. **NERTA wordmark (November 7, 2026, Max's call):** a small, wide, white-on-ink pill reading NERTA sits under the T roundel on the main map and every line poster. No backstory and no spelled-out name anywhere, so people ask when the MBTA dissolved. Code: `boston-map/src/nerta_mark.py`, variant B.

## Look

- Style of the real station wall posters: a schematic on a 45-degree grid.
- Solid is running today, striped is a real proposal, dashed is imagined.
- Black edge on every dot, including ferries. Small white halos on labels.
- No wheelchair icons at stations. Every station is accessible in this future, so the Key has one wheelchair symbol beside "All stations accessible". Posters do the same.
- No italics, except Max's disclaimer paragraph (Arial Narrow Italic).
- Lines running today are heaviest. New branches are lighter. Commuter rail is faded back.
- Big stations get bigger names: Boston Central, North, South, West, Back Bay.
- Coast comes from real Census towns bent to fit the diagram, not drawn by hand.
- Furniture sits in the corners: title top left, Dig box and Key bottom right, sources bottom right.
- **Transfer pills stay short.** Across most of the map they span one line gap. Boston Central spans two, and North Station spans three, from Green to Cyan, at Max's request. If two lines are far apart, move a line or use a real crossing.
- Old-style colored transfer bars belong on the line posters, not the main map.

## The network

- **The Bigger Dig:** four tracks under Atlantic Ave joining North and South Stations, with Boston Central in the middle. Walkways reach Downtown Crossing and Park. Costs shown: $21.5B tunnel, $15B original Big Dig, ~$125B whole map (rough sum).
- All commuter rail runs through the tunnel, so no line ends downtown.
- **Red:** extended to Weymouth, as the last stop. Mattapan line stays in its current shape.
- **Yellow:** the ring around the core, through West Station, Kenmore, Longwood, Ruggles, Nubian and JFK/UMass.
- **Cyan:** Assembly to South Boston. The Key says South Boston, not Southie (Max, November 7, 2026).
- **Indigo:** the Fairmount corridor.
- **Silver:** a short airport line, doubling back rather than looping. Logan Dock to Airport past all terminals, with Office Center, Rental Cars and Parking stops. The SL pill sits inside the loop.
- **Airport** is Tier 2: Blue, Yellow and Silver meet there.
- **Blue:** Wyoma Sq and Winthrop Center branches, plus the west link to West Station.
- **East Boston:** Day Sq is on Yellow, not Blue, because the real proposal is on the Silver Line corridor Yellow follows. Lewis Mall is the ferry stop.
- **Letters:** Green only, on the map since November 7: A Watertown, B Weston, C Cleveland Circle, D Riverside/Wellesley Hills and Union Sq, E Medford, N Needham. Other lines are named by end station, as the real Red Line is.

## Commuter rail and high-speed rail

- All 13 MBTA commuter routes are accounted for. Fairmount became Indigo. Needham became Green.
- Each line gets its own label. Newburyport and Rockport stay together as `NEWBURYPORT / ROCKPORT LINE`.
- Real split points: Franklin south of Readville, Foxborough at Walpole, Greenbush, Kingston and Fall River all at Braintree.
- Worcester line: Wellesley is the last stop shown, then `TO FRAMINGHAM, WORCESTER`.
- New offshoots must come from real proposals: Stoughton to Taunton, South Acton to Marlborough, Northern Tier to Greenfield and North Adams, Cape Cod via Middleborough. Foxborough to Mansfield uses real track.
- High-speed trains only stop at Tier 1 and Tier 2 stations: Boston Central, North, South, West and Back Bay. Airport is Tier 2 but has no high-speed line. The gold line passing through a stop doesn't mean trains stop there. High-speed rail runs on its own tracks beside, above or below commuter rail, express through places like Chelsea, River Works, Lynn and Salem on its way to cities like Portsmouth.
- High-speed pills on posters are gold inside a purple rim, matching the map line, so they don't read as Yellow Line.
- The Yellow and Silver transfer stop at Logan is "Logan Terminals" everywhere, matching Logan Dock. Plain "Terminals" read oddly beside Terminal A, B, C and E.
- Logan has Terminals A to F on the Silver Line. D returns after its 2006 removal, and F is a deliberate joke. A, B, C, E keep their real order.
- Only Yellow gets a wraparound shape. Every other line is a straight line or a tree, so Red's invented Trapelo Rd link was removed. Lexington Route 128 and Waltham are now separate terminals.
- Poster frames fit each line. Short lines get taller rows so every poster but Yellow and Green stands upright.
- A poster's ferry pill names the dock when it has a different name from the station, such as "F via Lovejoy Wharf".
- Encore is on Cyan only. Yellow runs past it without stopping, and that's correct.
- High-speed rail, labels only:
  - Concord NH via Lowell, Nashua, Manchester
  - NYC via Providence, New Haven
  - Albany via Worcester, Springfield
  - Montreal via Burlington VT
  - Bangor via Portsmouth, Portland, Augusta
- Springfield to New Haven via Hartford is part of the plan but **not shown**, because that leg is off the map.

## Day 8 release, November 8, 2026

- **Release scope:** the main map and the eight rapid-transit line posters. Ferries appear on the main map with labels, but the ferry route posters are held back. The regional map is on hold. Buses stay off.
- **Key:** regrouped into Service, New lines, Rail and ferry, Stations. Rows say "Service today", "Planned: based on a real proposal" and "Imagined". The ferry dock and walking link have a symbol. "Replacement shuttle buses: none" stays as a small caption.
- **Light Utopia restyle:** teal-leaning water `#bfe3e2` with a thinner coast `#86bcbb`, and rounded Key and Dig panels.
- **Commuter rail:** Reading and Malden Center are transfers between Orange and the Haverhill Line, which runs express past the Melrose and Wakefield stops now on Orange. Melrose/Cedar Park is added to Orange. Beverly is added on the Newburyport/Rockport line, where the two split. The Woburn and Burlington branch is dropped: it was drawn on the wrong side, the real branch closed in 1981, and Burlington had no proposal. Anderson/Woburn covers Woburn.
- **Ferry labels:** a dock beside a commuter stop takes that stop's name, as at Swampscott, Marblehead, Salem and Beverly. Long Wharf has its own bold label as the main hub. The North Shore boat runs Winthrop, Lynn, Nahant, Swampscott, Marblehead, Salem, Beverly, then `TO SALISBURY` (via Gloucester).
- T stops figure is now 224 (214 on the map plus the 10 Logan Silver stops), after the Green extensions, Vertex Tower and Wu Sq on November 7.
- Silver Line poster reads Airport at the top, down to Logan Dock, like the real airport maps (Max).

## Ferries

Five routes, one color each, drawn as round dots on a white wake so they read as boats, never as subway. Merged from Cursor's 12 legs on November 6, 2026, at Max's request.

- **Inner Harbor** (teal): Encore, Navy Yard, Lovejoy Wharf, Langone, Long Wharf, Lewis Mall, Logan Dock, Fan Pier.
- **Charles River** (violet, proposed): Cambridgeport, Kendall, Esplanade, Lovejoy Wharf, with an arrow to Watertown Sq.
- **South Shore** (oxblood): Columbia Point, Squantum Point, Hingham Shipyard.
- **North Shore** (lime): Winthrop Landing, Lynn, then Nahant, Swampscott and Marblehead Harbors to Salem Wharf and Beverly. The arrow says `TO SALISBURY`, and the title adds `TO SALISBURY VIA GLOUCESTER`.
- **Harbor Islands** (bronze): Spectacle, Long Island Recovery Campus, Georges, Hull.
- Docks are white squares. A dock beside a station gets a fine dotted walking link and no name of its own.
- Claude's calls, open to Max overruling: Chelsea Creek dropped, the express and the Langone pedestrian bridge dropped, Haverhill kept beside Orange, the Newburyport detour through Wonderland reverted.
- **Real-geography pass, November 7, 2026, before posting:**
  - Blue Hill Ave branch: Nubian, then straight down to Grove Hall, then along Blue Hill Ave about 7 units off the Fairmount line, crossing it at Blue Hill Ave (a new Orange-Indigo transfer) and ending at Mattapan. Four Corners is Fairmount only now.
  - The Mattapan trolley bends west after Butler, as the real line does, to meet it.
  - The Yellow ring runs in real order: Ruggles, Nubian, Melnea Cass, Boston Medical, Newmarket.
  - Saugus branch: Cliftondale and Saugus Center climb to their real level before dropping to Wonderland.
  - Inman Sq sits level with Harvard, and Union Sq moved a few units east. Watertown is north of Newton Corner. Columbia Point, Squantum Point and Long Island docks are in real order.
- **Left as schematic, on purpose:**
  - West Station beside Kenmore (already recorded as schematic in `line_audit.md`; moving it rewires five lines).
  - The Green B/C/D fan and Cleveland Circle, which the official map draws the same way.
  - Everett Sq, which can't move north without hitting the Cyan Line at Encore.
  - The Worcester Line row.
- **Max's map review, November 7, 2026:**
  - Level labels at Ruggles and Boylston. Copley and Arlington went level too (Copley above the line, Arlington below), because their tilted names blocked every level spot for Boylston.
  - Lynn station renamed Central Sq, the real location of the Lynn commuter stop.
  - Two kinds of boat. Harbor and river ferries (Inner Harbor, Charles, Harbor Islands) are slower for safety and drawn as dots. The North Shore and South Shore boats are high-speed and drawn as streaks. The Key has a row for each.
  - Purple arrowheads draw over the gold high-speed stripe.
  - The main map only points the coast boats onward: TO SALISBURY, and ON TO CAPE COD & THE ISLANDS.
- **Final audit, November 7 (15 reviewers), choices made:**
  - Every station label is level except Wellington Hill: it sits in a 45-degree strip between the Orange branch and the Indigo line with no level room.
  - Greenbush now leaves the Old Colony line north of Braintree, as real trains do. Mansfield is a filled (running) stop. West Station to Hynes is striped.
  - Accepted as schematic: the Fitchburg Line crosses the Red Waltham branch west of South Acton; the North Shore boat runs under the BIGGER Dig panel between Long Wharf and Winthrop; the Peabody line leaves at South Salem rather than Salem.
  - Key says "Commuter rail, dashed where new" and shows a dashed sample.
- **Type audit, November 7 (15 more reviewers: type, kerning, label placement), choices made:**
  - Green letter pills are now the same height and type size as the other line bullets (9.2 units wide, was 14.6), set under each branch's end name. The E has a second pill on the Forest Hills leg, level with Heath St (Max asked for it).
  - Line-end styling follows the drawn network: READVILLE and VFW PARKWAY are bold ends; Oak Grove is plain because Orange runs on to Reading, like Alewife and Braintree.
  - Moved to clear labels and lines, not for geography: Allston (off the Worcester Line), Maverick (down the Blue Line, clear of STATION), Mass Ave on Orange (off the Back Bay ring), Rental Cars (onto the Silver line), Logan Dock and the Marblehead dock.
  - The Charles River now starts at Watertown, clear of the Worcester caption. The North Shore ferry text uses a darker lime (#6f7c00); the route line keeps its color.
  - Two-line labels draw their halos first, so a lower line no longer cuts the descenders above it. Station names use curly apostrophes.
  - Held for Max: Mass & Cass stays 9.4 (its hierarchy); Boylston's dot, Union Sq, South Station's tilted pill, the Dig panel's walkways, Foxborough or Foxboro.
- **Built and real, November 7 evening (Max):** the map and posters read as if hung in a Boston station today, for riders. Every line draws solid and every stop filled (`BUILT = True` in make_tmap.py; `lines()` and `CR_STOPS` keep each piece's status for line_audit.md). The Key and captions speak to riders: all 8 lines by name, "Commuter Rail", "Express ferry", "Ferry dock, short walk to station", no "proposed". Only Max's disclaimer and the BIGGER Dig box speak to map viewers.
  - Lore: everything is driverless maglev and runs 24/7, with extra service for events. No buses: on-demand floating magnetic pods replace cars and buses in the city. Posters say "Driverless maglev, 24 hours a day" and name event service where a line serves a venue.
  - Disclaimer: "MOST" in bold caps; "are grounded in real data & studies,".
  - The #30DayMapChallenge tag and "Day 8 • Utopia" stay on the main map and every poster for the November 8 release (Max: "we will probably remove it later on"). The posters' red "NOT A REAL MBTA MAP" is retired: the new T and NERTA style make it plain (CLAUDE.md updated).
  - The main map Key adds "Driverless maglev, 24 hours a day" above "Replacement shuttle buses: none"; the footer reads "Pods on demand at every station."
  - NORTH STATION's label sits above its pill, over the Orange Line (Max), which frees room to label the Lovejoy Wharf dock.
  - Vertex Tower: a brand-new supertall with its own Cyan stop in the Seaport loop, between Seaport and City Point. Max asked for a future skyscraper station "without much context"; the name is a subtle nod to Vertex Pharmaceuticals at Fan Pier (Max picked it over Toast and Moderna).
  - Wu Sq: an Orange stop in Roslindale, between Roslindale Village and Bellevue, a quiet nod to Mayor Wu (Max). Boston names squares after people, so it reads as in-world.
  - David Ortiz (the real Lansdowne commuter stop) and Hynes are one transfer station, drawn as a capsule (Max asked for a transfer; on this map Hynes is its neighbor, though the real walk is to Kenmore).
- **The T, November 7 evening (Max), replacing "Keep the T, unchanged":** a bold block T in three layers: black outline, a band of color, white core, inside the usual white roundel. Line posters use their line color. The main map uses diagonal stripes of 11 colors in Max's order: Red, Orange, Yellow, Blue, ferry teal, Cyan, Silver, high-speed gold, Indigo, commuter rail purple, tram (Green). Stripes are aligned: the T's proportions sit on a diagonal grid, so every corner lands on a stripe edge and each color shows twice. The NERTA pill gets the same color rim outside. Code: `nerta_mark.draw_t`, `draw_nerta(..., colors=)`. Rejected: a black roundel interior, with or without a color rim.
- **Stops, November 7 evening:** Babson renamed Wellesley Hills (Max). Wellesley Hills and Auburndale are real Worcester Line stations, so each gets a CR pill on the main map and its poster.
- **Type audit, Part 3 settled (November 7, late):** Mass & Cass label at 8.6 pt (clears Indigo; the station symbol keeps its hierarchy). South Station's tilted pill shortened so it stops before the Cyan curve. The Dig panel says "Underground walkways", which is why none are drawn. Foxboro, the MBTA station name. The CL pill centered in the Haverhill jog. Left as they are: Boylston's dot, Union Sq and Lechmere (November 6 decision), Four Corners, the ampersand in ON TO CAPE COD & THE ISLANDS, and the disclaimer's black. The Green poster posts with a second, cropped image so its type reads on a phone.
- **Oak Grove is a commuter rail transfer (Max, November 7, late):** a capsule joins Orange and the Haverhill Line, as at Malden Center, and the Orange poster shows a CR pill. Real Haverhill trains stop there since 2022. The rail poster must show Oak Grove as a Haverhill Line stop.
- **Every-map rule (Max):** "any changes made in these sessions should reflect on every single map, no oversights", and the decisions made about commuter rail and trams are to be carried onto every other map. Side sessions (rail poster, tram poster) list their changes in `research/*-changes-for-all-maps.md`; the main map session applies them everywhere and re-checks.
- **Langone Ferryport (Max, November 7, late), the giant ferry hub at Langone Park:** it replaces the Cyan stop "North End" and joins North Station as one complex (an L-shaped capsule). Every major ferry route starts and ends there, spurs excepted. The Express shuttle runs Navy Yard, Langone Ferryport, Long Wharf, at all times. Navy Yard and Long Wharf stay major ports but are no longer hubs. Spec: the session scratchpad's `spec_langone.md`.
  - North Shore route: absorbs Winthrop and Revere. It calls at Winthrop Landing, Winthrop Beach, Highlands Beach, Suffolk Downs, Beachmont, Revere Beach, Wonderland, Lynn Harbor, Nahant, Swampscott, Clifton, Marblehead, Salem and on to Salisbury. High-speed trips stop only at Langone Ferryport, Lynn Harbor, Salem, Gloucester, Rockport, Newburyport and Salisbury. Caption: "TO SALISBURY VIA GLOUCESTER, NEWBURYPORT". Newburyport and Newport, RI are major ports.
  - Clifton: a North Shore ferry stop, and a commuter rail stop east of South Salem (South Salem, Clifton, Marblehead).
  - Main map look: water nudged toward cyan (`#b6e2e7`); a few faint "@mapzimus" marks in open water; the BIGGER Dig panel moved northeast and rewritten with useful counts. Suffolk Downs is a ferry dock by Max's own list, which overrides its old Rejected entry.
- **Names, November 7 late (Max):** "Express" is now **Fast Ferry (FF)** everywhere: the Navy Yard, Langone Ferryport, Long Wharf shuttle; the North Shore and South Shore Fast Ferry; and "fast ferries stop at major ports only". The Charles stop **Gronk** keeps its name (Max's call, made knowing it is a Patriots nickname). **Pods on demand** appears on every poster: "at every dock" on the ferry poster, "at every station" on the line posters, and in the main map's footer.
- **Ferry poster, planned, after the main map:** one large poster with every ferry route, tied together by the Long Wharf to Navy Yard shuttle (the real MBTA F4 route). North Shore to Newburyport, ending at Salisbury; South Shore past Hull to Plymouth, the Cape Cod Canal, the whole Cape, Buzzards Bay, New Bedford, Newport and Fall River; a Nantucket and Martha's Vineyard leg from Chatham to Woods Hole. River boats on the Charles, Mystic and Chelsea Creek run clockwise and counterclockwise loops, plus zigzag boats for crossing. Claude Code builds it (not Cursor). Every new stop gets a `line_audit.md` row.

## Cost

About $125B in 2026 dollars, about 5 times the Big Dig's $24B. The math is in `boston-map/data/SOURCES.md`.

## Development checks

Suffolk Downs was upgraded to a larger station. Sullivan, Stadium and West Station were confirmed as they are. No new rail stops came from this research.

## Rejected. Don't suggest again.

- Hand-drawn coast
- Silver Line loop
- Salem on the Blue Line
- Smoots stop or label
- Showing buses
- A date in the title
- Italics
- Jokes about Storrow, Scollay or the Citgo sign
- A Charlie line
- Patriots or Tom Brady naming
- Long transfer pills, including the Longwood one
- Natick and Framingham stops on the Worcester line
- A replacement logo for the T. (A NERTA wordmark under the T was approved on November 7, 2026.)
- Rockport as its own drawn branch
- Invented offshoots with no proposal: Sudbury, Lynnfield, Medfield, Millis
- Foxborough off the Greenbush line (wrong side of the region)
- Suffolk Downs ferry (no proposal found, reopen only if one turns up)
- East Saugus stop
- River Works stop (it mainly serves GE employees today)
- Trapelo Rd stop and the Lexington to Waltham link
- The caption "Everything Boston ever drew..."
- The line "What if the T went everywhere"
