# Tram network: design notes

Max's decisions for the NERTA tram network, November 7, 2026, from the tram poster session. Newest at the bottom of each list. Nothing here is on the main map or the line posters yet; anything the other maps need goes in `research/tram-changes-for-all-maps.md`.

## The world

- No buses in NERTA. Trams run on today's busiest bus streets, and pods cover the rest. When Max says "bus map", he means the tram map.
- Everything is driverless maglev, 24/7, with special-event service, as on the other maps.

## What gets made

1. **A tram map over faded NERTA**: trams drawn on the main map's layout, with NERTA rail faded behind.
2. **A standalone tram network poster**, like the big ferry poster: stops on a grid of rows, with transfer pills.
3. Later, maybe one poster per tram line (the main session's note: ferry and rail are getting line posters). The combined poster comes first.
4. Posted versions carry the release block from `boston-map/src/release_tag.py` (disclaimer, credit, hashtag, Day 8). nerta.fun versions leave it out.

## How it gets made

1. **Decide on a real map first.** `boston-map/tools/make_tram_realmap.py` writes a clickable web map (`output/copies/tram_realmap_vN.html`, served at `localhost:8765` by the `tram-realmap` launch entry). It shows NERTA stations at their real spots, today's frequent buses and the draft trams.
2. **Bend into NERTA.** `boston-map/src/tram_merge.py` bends real geography onto the main map's layout with a thin-plate spline through every station (real spot to map spot), pins transfer stops to their stations, and straightens each tram to 45 degrees.
3. **Merge and adjust** both layers until they sit together cleanly (Max: "alter everything around merging the two separate maps together").
4. **One shared real-geography set** (Max): stations, commuter rail and trams together. The rail poster session writes the rail layer to `boston-map/data/rail_regional/`; the tram web map reads it.

## Look

- **Color: hot pink `#e0457b`** (Max). CIEDE2000 at least 20.5 from every NERTA line, commuter rail, high-speed gold, all 15 ferry routes, water and paper; 22.3 from Red.
- **Tram stop:** a white circle with a hot-pink edge and a hot-pink cross. One arm runs along the track and one across it, so it reads as a + on straight lines and an X on diagonals. The cross runs about a third past the circle's edge. Pink, not black, is Max's call for tram stops; the house rule "black edge on every dot" stays for every other mode.
- The trams are thin lines ("the tiny pink lines").
- **A super thin black line runs down the middle of the pink line** (Max). It stops at each stop's circle. The line keeps its width; inside the circle only the skinny cross arm shows (Max considered changing the thickness, then kept it).
- Exact sizes for every map are in `research/tram-changes-for-all-maps.md`.

## Network

- **13 routes approved** on the real map (Max: "that all looks perfect"): 66 Harvard St, 1 Mass Ave, 70 Western Ave and Arsenal St, 71 Mt Auburn St, 16 Columbia Rd, 15 Dudley St, 22 Talbot Ave and Columbus Ave, 23 Washington St in Dorchester, 31 Morton St, 9 Broadway, 111 Chelsea, 116 Inland Revere, 110 Revere and Everett. Data: `boston-map/data/tram/tram_draft.json`.
- The 73 is left off: it overlaps the rejected Trapelo Rd stop.
- **19 more added** (Max, "All 19 picks"): 216, 101, 34, 34E, 225, 100, 222, 64, 240, 220, 455, 215, 95, 75, 712, 78, 106, 60, 38. 32 routes in all.
- **Stops are planned for NERTA**, not copied from today's bus stops (Max: "new stops and stuff might change bus routes"). Every NERTA station a tram passes gets a stop. The 15 and 23 end at Nubian; the 9 at City Point station; the 31 at Mattapan.
- **The route check** (`research/tram-route-assessment.md`) suggested cutting 7 of the 19 and trimming others. Max: "Keep all 19." Its other suggestions (trims, merges, Columbia Point) are not applied.
- **More to add** (Max): the major routes that meet the subway, and ones that meet commuter rail stops. Candidates are ranked by weekday trips from the MBTA API and shown on the real map for Max to pick.
- If a tram stop sits by Long Wharf or Aquarium, it gets a pill for the London ferry (working name "Atlantic Clipper"; color and code come from the main session).

## Calls made while Max said "finish up" (November 8, tram session; Max can overrule)

- Tram transfers on the main map and line posters: one short pink `TR` pill (long pills are on the Rejected list).
- On the trams-over-NERTA map, squeezed stretches stay straight, with stops evenly spaced and smaller circles; no U-shaped swing-outs.
- Transfer stops at NERTA stations keep an ink edge, so they read as stations.
- A ferry-size station display (Max's ask) goes beside the ferry display; the big Tram Network poster stays too.
- Website export: `boston-map/data/tram/tram_network.json` (`boston-map/tools/export_tram_network.py`).

## Release

- Max, morning of November 8 (relayed by the nerta.fun session): only the main map and the 8 subway posters are released today. The tram posters and the station display wait until Max releases them.
- Trams are live on nerta.fun from `tram_network.json`: a Trams page, one page per route, station departure boards, the trip planner and the street map.

- Logo (Max, November 8): the multicolor T and NERTA pill now include tram hot pink among the line colors, with the stripes flipped. The tram maps use the single-color pink mark, so they don't change.

## Files (November 8)

- Boston Trams over faded NERTA: `boston-map/output/copies/tram_map_v15` (`src/make_tram_map.py`).
- Tram Network poster: `tram_network_v4` (`src/make_tram_poster.py`).
- Tram station display, ferry-display size: `tram_display_v6` (v7 in progress).
- Each has a `_web` copy without the release block. All three are waiting on the main session's audit.

- The trams-over-NERTA map (v19) leaves off 118 stops so every name pairs with its own stop. Max saw it and said "OK as is": it is the overview, and the two posters keep every stop.

- The station display may grow past the ferry display's size (about 30 x 37 in, same type) so its core reads cleanly (Max, after seeing v7).

- **Trams on the main map** (Max, after v1 "dominates the map way too much"): only a thin pink line (about 1.2 pt) with a tiny black center strip, and stops as small pink outlined triangles ("triangles are stops"). No names, route numbers or FREE tag, drawn under the T lines. Preview: `boston-map/output/copies/main_with_trams_v2` (`src/make_main_with_trams.py`).

- **Max: put the light trams on the real main map** ("Yes, add them"). Handed to the main session, which owns `make_tmap.py`.

## Open

- Which extra routes (pending the candidate list).
- Tram line names on the posters: today's route numbers, or new ones.
- Room in Dorchester and Roxbury: the main map squeezes them, and six trams meet there.
