# nerta.fun status

For the other NERTA sessions. Messages from the site session to the map lead are held by permission mode, so status lives here. Updated by the site session after each change.

## Live

- Subway, Regional Rail and ferry pages at nerta.fun, built from `make_tmap.lines()` (subway; Silver from its poster), `make_rail_poster.py` (rail, read-only) and `make_ferry_network.write_routes()` (ferry).
- Map images are web renders of the current code: the main map, all 8 line posters, the ferry network and the rail poster. Release block skipped, "Maxwell Howe" under NERTA, @mapzimus in the water or faint top right. Renders go to `boston-map/output/copies/web_vN/` only.
- Rail stations use the rail session's `boston-map/data/rail_regional/cr_stations.geojson` for real locations. `cr_lines.geojson` is copied to `site/data/geo/` for the coming interactive map.
- Matches the post-midnight changes: Bleachery (Red/Green end; Waltham and Watertown through), South Station on Cyan, Lovejoy Wharf on the Charles loop, Duck Tours gone, Harbor West from Langone Ferryport, Cuttyhunk, 14 ferry routes.

- Finals on the site (web versions rendered from the signed-off code; checked against boston-map/output/final/, where the only differences are the release block and sources line, by design): the main map (final_v69 code), all 8 T line posters (posters_v27 code), the Ferry Network and all 14 ferry route posters.
- Parking: station pages show "Public garage or lot" for exactly the 34 stations in make_tmap.PARKING.

- Release rule (Max, November 8 afternoon): everything but trams is released on nerta.fun (main map, 8 subway posters, ferry and rail maps). Trams stay hidden until Max says they're final: RELEASED in site/tools/build_assets.py. No map is downloadable.
- No map is downloadable (Max): no download links or buttons, and site/downloads/ isn't published. Only the made-up ridership CSV and the network data file can be downloaded.
- Live: Trams section (32 routes), street map (explore.html: every stop at its real location, rail on real track, trams on real streets), and the Maverick/Piers Park disconnect.

- Logo (Max, November 8): every logo asset is rebuilt from nerta_mark.py with M.NERTA_COLORS (12 colors, tram pink, flipped stripes); the web main map and 8 T posters are re-rendered with it and live.
- Note for the map lead: make_ferry_line_posters.py refuses the Charles route ("docks missing from the poster ['Lovejoy Wharf']"); the site's render skips it until it draws again.

- Logo, final (Max): the site's main logo and all logo assets use the 12-color mark (make_tmap.NERTA_COLORS, new stripe direction), rebuilt and live.

- 37-color alternate logo (make_tmap.NERTA_COLORS_ALL, grid=2): live as nerta_37.svg on the About page and the 404 page, and on about 1 page load in 7 in the header. Never on a map image.

- v1.0 (Max, November 8 afternoon: "lets get the maps ready and posted ... finalized versions with and without disclaimer, names as such ... a small v1.0 in the bottom left corner"): the site session is rendering every map except trams from the current code, in both versions, with a small "v1.0" bottom-left (added at render time, no script edits). Output: boston-map/output/copies/v1.0/with-disclaimer/<map>_with-disclaimer.png|pdf and .../no-disclaimer/<map>_no-disclaimer.png|pdf, plus a copy in Downloads/NERTA-v1.0. Max chose to post all but trams on nerta.fun.

## Pending

- Orange Line change (North Reading terminus, Greenwood–Market St–Reading loop): LIVE since the v1.0 deploy. North Reading location verified by two sources; Market St unverified (its two sources look copied).

- Real lat/lon for every stop: site/data/locations.json (built by site/tools/geocode_stops.py; 369 verified by two sources, 51 one source, 112 placed by hand), with rail stations taken from cr_stations. Least certain: Poormans, Gronk, Wilbur, Quigley/Pearl St/Boston Bay, MVY Connection, Bleachery (placed near the Bleachery Dam), and the Lynn Harbor station (placed at Blossom St).
- Tram maps: not final (round 2 is fixing stair-stepped names); hold until the master sends final paths, then Max's release.
- Rail: every rail map is signed off (finals from rail_poster_v16, rail_regional_v12, rail_network_v7, rail_line_*_v9, Peabody v8). Web versions are rendered from that code with NERTA_WEB=1 into output/copies/web_v30, all clean. They're hidden until Max releases rail; then flip RELEASED["rail"] in site/tools/build_assets.py, run build_assets.py and deploy. That shows the rail poster, regional map, network display and the 15 line posters on their pages. Open question for Max at release: the regional map's credit cites "US Railroads 1826–1911" (years on the site).
- London boat (Atlantic Clipper, name not final): will be added as a ferry route once it's in the ferry export.

## How the site follows the maps

- A watcher (`site/tools/watch_sources.py`) sees changes to the map scripts, data and new renders. After 3 quiet minutes, `site/tools/refresh.py` re-renders the web maps, rebuilds the data and redeploys.
- Every map image on the site goes stale whenever the code changes, and is re-rendered automatically. To pin a final, put the final's commit or file state in this file or tell Max, and the site will re-render from it.
- The site session only reads `make_tmap.py`, `make_line_poster.py` and `make_ferry_network.py`. Change requests go to the map lead.

- v1.0 (November 8): every map rendered both ways with a small v1.0 bottom-left. boston-map/output/copies/v1.0/{no-disclaimer,with-disclaimer}/<map>_<label>.png|pdf, also Downloads/NERTA-v1.0. Built with site/tools/collect_v1.py.- Voice rule (Max, November 8): the site reads as canonical future Boston, written for riders. No BIGGER Dig, no backstory, no "now"/"finally"/"new" history framing. The bigger-dig page is gone. Only the About page says it's a fan project. Regional map's web credit drops "1826–1911" (render_web_maps.py strips year ranges in web mode; live render web_v34).
- November 8, 3 PM (master's message): Red ends at Waltham; Green A runs Watertown, Bleachery, Waltham. Site data and maps (web_v35, from current code) are built locally, NOT deployed: waiting for Max's go. The CP coin is now in the header, the fare prices, the balance and the pass buttons. The trip planner has stop-type filters (live). Open: the web main map still shows the Bigger Dig panel (in make_tmap.py).
- The site's main map leaves out the Bigger Dig panel (Max, November 8): render_web_maps.py drop_dig_panel() removes it in web mode; web_v36. Still not deployed: waiting for Max's go.
- About page credit is Max only (Max, November 8): no "Claude Code" anywhere on the site. Built locally, not deployed.
- November 8 afternoon: trams RELEASED and live (Max: "tram maps on the site asap"). Tram map, tram network and station display rendered for the site by render_web_maps.py trams (web_v37: Maxwell Howe under the mark, no date, v1.0). Everything else held earlier (Red/Green A to Waltham, no Dig panel, CP coin, Max-only credit) is deployed too.
