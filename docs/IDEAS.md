# Ideas

Brainstorming, not decisions. None of this is on the map.

## NERTA: the name and the T

**The idea:** the MBTA dissolves into a regional body, the New England Regional Transit Authority. Max also floated NETA and "Agency" in place of Authority. Current favorite: NERTA.

**The problem:** nobody would really give up "the T", so how does the name change work?

**The answer so far: the agency changes, the brand doesn't.**
- People don't ride the agency. They ride the T. Most riders never say "MBTA" anyway.
- London works this way: Transport for London runs the Tube. Chicago's CTA runs the L.
- So NERTA runs the region, and "the T" stays the name of Boston's subway. It's a small joke too: the agency changes and everyone keeps saying the T.
- Other cities could get their own short local names under NERTA.
- This also makes the premise easy to explain in one line.

**Still to decide:**
1. Does NERTA ever appear on the Boston map, or only on region-wide maps?
2. Does commuter rail become its own NERTA brand, with the T as just the subway?
3. Who pays for it, and how does a six-state agency get created? (Good debate fuel. A real interstate compact is the natural route.)

## The T logo

Max is worried a lookalike or real T could cause trouble, especially if the map argues the MBTA should dissolve.

- **Max's call so far:** no new logo. Keep the T.
- This isn't legal advice, and it's worth asking someone who knows trademark law before selling anything.
- Making a logo "super similar but different up close" doesn't really protect you. The usual test is whether people could be confused, so a deliberate near-copy can be worse than an obvious fan use.
- The stronger protections are the plain ones: non-commercial, clearly labeled "NOT A REAL MBTA MAP", no selling prints.
- If it ever goes commercial, the roundel should come off in favor of something clearly original.

## Subways for other New England cities

Real research and logic, with a good mix of fantasy and hopefulness.

**Method for cities with no stations today:**
1. Place stations first, based on need: housing, jobs, hospitals, schools, entertainment, travel hubs, existing infrastructure.
2. Draw lines through the stations afterward. Lines come from stations, not the other way around.

**Starting list from the original plan:** Portland, Worcester, Hartford, Springfield, Manchester/Nashua and Burlington. City transit research is in `research/`, especially `04-vermont-gateways-city-transit.md`.

**Tools ready to reuse:** `boston-map/tools/stopcheck/` scored stops using Census population and jobs data, which is close to what the method needs.

## Regional commuter rail map

This is the next big piece. Max's order: main map, every line on its own, then a regional commuter rail map. It has room for every real stop, spur lines, high-speed rail and proposals. The old 1970s purple commuter map is a good reference for the layout.

## Buses

Line posters feel incomplete without bus connections. Max's plan:
- Show buses on the regional commuter rail map.
- Show them very faintly on the main map, behind everything. This reverses the earlier call to leave buses off, so test it before committing to it.
- Decide how a line poster lists bus routes, most likely as small route numbers beside each station, like the official posters.

MBTA route data would drive this, and it needs its own design pass so it stays readable.

## Top right corner of the main map

This is the most crowded spot. Options, best first:
1. **Add width on the right.** About 12 more units gives North Shore labels room. The Dig box and Key would shift right with it. The poster gets slightly wider.
2. **Move the three label rows.** Shift the Newburyport and Bangor text left, above the Peabody line, away from Salem.
3. **Add a North Shore inset box.** Clean, but it adds a new element to the map.

## Regional map

The first New England maps in `boston-map/output/` could return as the NERTA system map, now that the project has room for them. Their ideas carry over too, such as Max's Newport to Providence link through Bristol. The decision log has the full regional network.

## Suffolk Downs

The new neighborhood is planned and on the map as a larger Blue Line station. A ferry doesn't fit: the nearest water is Belle Isle Marsh, a protected salt marsh. Winthrop Landing is the nearest realistic dock.

## Development-led stops

Bay City on Columbia Point, Suffolk Downs and Sullivan Square are examples of real plans that justify transit. Worth repeating that check for every city.
