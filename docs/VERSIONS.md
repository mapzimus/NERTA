# Map versions

Everything is in `boston-map/output/` unless noted.

## Current

| File | What it is |
|---|---|
| `t_map.png`, `t_map.pdf` | **The current map, drawn from the code.** Includes Max's title block edits, the Suffolk Downs ring and the South Salem label. |
| `day08_rapid_transit.ai`, `day08_rapid_transit.png` | **Current Illustrator build and export** of the same map. |
| `day08_rapid_transit_max_edits.ai` | Max's hand-edited file, kept for reference. Its edits are now in the code. It doesn't have the South Salem fix. |
| `line_red.png`, `line_red.pdf` | Red Line poster sample, the only one so far. |

## Older

| File | What it is |
|---|---|
| `map.png`, `map.pdf` | The first idea: "What if the MBTA covered all of New England." A geographic map of the whole region, later dropped from Day 8. |
| `regional_map.png`, `regional_map.pdf` | A second regional poster, also dropped. |
| `draft_network.png` | Early network draft. |

## How the map evolved

1. **New England map:** the MBTA stretched across the region, with small subways in other cities.
2. **Two posters:** a regional map plus a Boston wall poster.
3. **Boston only:** the T wall-poster style with the real coast bent to fit. Regional dropped.
4. **Fantasy first:** the "Rapid Transit" title, and the Bigger Dig box with costs.
5. **Commuter rail pass:** all 13 MBTA routes shown, with new stops and offshoots tied to real proposals.
6. **This repo:** the project moves out of the challenge and keeps going.

The full 40-pass record is in [history/decision_log_all_passes.md](history/decision_log_all_passes.md).

## Scripts

| Script | Draws |
|---|---|
| `make_tmap.py` | Current main map |
| `make_line_poster.py` | Line posters (`red` so far) |
| `make_map.py` | The first New England map |
| `make_regional.py` | The regional poster |
| `build_extensions.py` | Builds the regional extension layers |
| `fetch_mbta.py`, `fetch_access.py` | Download MBTA and wheelchair data |

Only `make_tmap.py` and `make_line_poster.py` were test-run in this repo. The others had their paths updated but haven't been run here.
