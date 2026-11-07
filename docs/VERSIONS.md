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

## Older

| File | What it is |
|---|---|
| `map.png`, `map_hires.png`, `map.pdf` | The first idea: "What if the MBTA covered all of New England." A geographic map of the whole region, later dropped from Day 8. |
| `regional_map.png`, `regional_map_hires.png`, `regional_map.pdf` | A second regional poster, also dropped. |
| `draft_network.png` | Early network draft. |

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
