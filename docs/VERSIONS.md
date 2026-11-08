# Map versions

Everything is in `boston-map/output/` unless noted.

## Current

| File | What it is |
|---|---|
| `day08-utopia-boston*`, `day08-line-*.png` | **The posting set**, named for the 30 Day Map Challenge. Copies of the files below. |
| `day08_rapid_transit_hires.png` | **The main map at its highest resolution**, 600 dpi from Illustrator. Use this for print or zooming. |
| `day08_rapid_transit.png` | The main map at 200 dpi from Illustrator. Use this for posting. |
| `day08_rapid_transit.ai` | The current Illustrator file. |
| `t_map.pdf` | The main map as a vector PDF, drawn from the code. |
| `t_map.png` | The 200 dpi working render, used by the checks. |
| `line_<name>.png` | Line posters at 600 dpi: red, orange, blue, green, yellow, cyan, indigo, silver. |
| `line_<name>.pdf` | The same posters as vector PDFs. |
| `day08_rapid_transit_max_edits.ai` | Max's hand-edited file, kept for reference. Its edits are now in the code. |

## Finals, November 8 (signed off by the master session)

Saved by `boston-map/tools/finalize.py` to three places: `boston-map/output/final/` (PDF and PNG), `C:\Users\mhowe\Downloads\NERTA-final\`, and `C:\Users\mhowe\Desktop\NERTA-FINAL-Disclaimer\<map>\` (feed, Instagram feed and portrait, TikTok, Instagram and TikTok carousels with the whole map as slide 1, zoom, full PNG, MANIFEST.txt). Every final carries the release block.

| Final | Made from |
|---|---|
| `main-map` | `copies/final_v73.pdf`, rasterized at 400 dpi (5 text-placement audit rounds, the parking round, then the South Shore Fast Ferry round Hull to Fall River with its own audit). The earlier v69 final is in each folder's `superseded/` |
| `line-<color>` (8) | `copies/posters_v27/` at 600 dpi |
| `ferry-network` | `copies/ferry_network_v18` (3 audit rounds) |
| `ferry_<route>` (14) | `copies/ferry_lines_v3/` from `make_ferry_line_posters.py` (2 audit rounds) |

Re-finalized after "disconnect maverick from piers park" (Max, November 8): `line-blue` from `copies/posters_v28`, `ferry-network` from `copies/ferry_network_v19`, `ferry_east_boston` from `copies/ferry_lines_v4`. Older versions are in each folder's `superseded/` (moved by `boston-map/tools/supersede.py`).

Re-finalized after the logo and Charlie Points round (November 8): `main-map` from `copies/final_v80.pdf` (400 dpi; v80 adds the Dig panel's "all but the Peabody line"), `line-<color>` from `copies/posters_v30b`, `ferry-network` from `copies/ferry_network_v21`, `ferry_<route>` from `copies/ferry_lines_v6c`. Earlier finals are in `superseded/` with the tag `pre_cp`.

Rail finals (November 8, rail session's maps, 2 audit rounds each): `rail_line_<stem>` (15) from `copies/rail_line_*_v9` (Peabody `v8`), `rail-poster` from `copies/rail_poster_v16`, `rail-regional` from `copies/rail_regional_v12`, `rail-network` from `copies/rail_network_v7`.

Tram maps (tram session) are still in review: round 2 audit in `research/audit-tram-r2-2026-11-08.json`; `tram_network_v4` is close, the tram map and station display need their stair-stepped names fixed.

Re-finalized after the Orange Line north change (North Reading end, Lynnfield loop; Max, November 8): `main-map` from `copies/final_v83.pdf` (400 dpi) and `line-orange` from `copies/posters_v32`. A pixel diff against v80 showed only the Orange north end and the T stops figure changed. Earlier finals are in `_superseded/` with the tag `pre_northreading`.

**Release v1.0 (November 8, Max):** every final in two versions, `<slug>_v1.0_disclaimer` and `<slug>_v1.0_no-disclaimer` (the six disclaimer lines removed; the credit, hashtag and Day 8 stay), each with a small "v1.0" in the bottom-left corner. Made by `boston-map/tools/release_v1.py <slug> ...` from `output/final/<slug>.pdf`, into `output/final/v1.0/`, `Downloads\NERTA-final\v1.0\` and `Desktop\NERTA-FINAL-Disclaimer\v1.0\<slug>\` (both social sets in one folder). 42 maps so far; the tram maps follow when signed off.

The London boat is still the working name "Atlantic Clipper" in these finals; a new name means re-running finalize for the maps that show it.

## Work in progress, after Day 8

Newest copies, November 7 late (all in `boston-map/output/copies/`, never in `output/` itself):

| File | What it is |
|---|---|
| `final_v56.png`, `.pdf` | Main map: rail list items 1-6, Route 128, London boat, Key row |
| `posters_v19/` | All eight line posters: release block, AC pill at Aquarium, Blue facing north |
| `ferry_network_v15.png`, `.pdf` | Ferry Map: release block, AC at Long Wharf, Cuttyhunk and Vineyard Haven, CANAL PASS |
| `rail_poster_v7.png`, `.pdf` | Combined commuter and high-speed rail poster (rail session) |
| `ferry_lines_v1/` | One poster per ferry route (in progress) |


| File | What it is |
|---|---|
| `copies/hq_2026-11-07/` | **High-quality set of the map as it stands:** `current_map` (600 dpi PNG and vector PDF), all eight `line_*` posters (600 dpi and PDF) and the five `ferry5_*` ferry posters (600 dpi). |
| `copies/wide_v3_lbl.png`, `.pdf` | Newest working render: five ferry routes, wider sheet, Beverly. |
| `copies/ferry5_*.png` | The five ferry route posters at 160 dpi. |
| `copies/archive/` | Every earlier draft render from November 7, Cursor's and Claude's. Nothing deleted. |

## Older

| File | What it is |
|---|---|
| `archive/map.png`, `map_hires.png`, `map.pdf` | The first idea: "What if the MBTA covered all of New England." A geographic map of the whole region, later dropped from Day 8. |
| `archive/regional_map.png`, `regional_map_hires.png`, `regional_map.pdf` | A second regional poster, also dropped. |
| `archive/draft_network.png` | Early network draft. |
| `archive/day08_rapid_transit [Recovered]*.ai` | Two Illustrator crash recoveries. No hand edits worth keeping. |

## How the map evolved

1. **New England map:** the MBTA stretched across the region, with small subways in other cities.
2. **Two posters:** a regional map plus a Boston wall poster.
3. **Boston only:** the T wall-poster style with the real coast bent to fit. Regional dropped.
4. **Fantasy first:** the "Rapid Transit" title, and the Bigger Dig box with costs.
5. **Commuter rail pass:** all 13 MBTA routes shown, with new stops and offshoots tied to real proposals.
6. **This repo:** the project moves out of the challenge and keeps going.
7. **Line posters:** one poster per line, each fitted to its own shape. Only Yellow wraps around.

The full pass-by-pass record is in [history/decision_log_all_passes.md](history/decision_log_all_passes.md).

## Scripts

| Script | Draws |
|---|---|
| `make_tmap.py` | Current main map |
| `make_line_poster.py` | All line posters. Add a line name to draw just one. |
| `make_map.py` | The first New England map |
| `make_regional.py` | The regional poster |
| `build_extensions.py` | Builds the regional extension layers |
| `fetch_mbta.py`, `fetch_access.py` | Download MBTA and wheelchair data |

Only `make_tmap.py` and `make_line_poster.py` were test-run in this repo. The others had their paths updated but haven't been run here.
