# Rail poster: changes the other maps need

November 7, 2026. Written for the session that edits `make_tmap.py`, `make_line_poster.py` and `make_ferry_network.py`. The rail poster (`boston-map/src/make_rail_poster.py`, newest render `boston-map/output/copies/rail_poster_v6.png`) didn't edit any of them.

Ferry pills on the rail poster come from its own `FERRY` table (station, dock, route, high-speed stop). The coastal docks past the main map's edge aren't in the main map's data. When the ferry poster or `DOCKS` change, update that table too.

Max's rule: "any changes made in these sessions should reflect on every single map, no oversights."

The poster reads the main map live: its stops and names come from `CR_STOPS`, and its transfer pills from `lines()` plus `make_line_poster.EXTRA_TRANSFERS`, `FERRY_COLOR` and `FERRY_VIA`. So most main-map changes reach the poster on the next render. The items below go the other way: the poster has them and the other maps don't yet.

Sources for every item are in `boston-map/data/line_audit.md`, section "Commuter and high-speed rail poster".

## Changes to make

| # | What | Main map (`make_tmap.py`) | Line posters | Ferry poster | Status |
|---|---|---|---|---|---|
| 1 | **Montreal high-speed row moves to the Lowell line** (Max, Nov 7: real route) | Drop `HIGH-SPEED RAIL TO MONTREAL VIA BURLINGTON VT` from the Fitchburg rows in `CR_TEXT`. Remove the gold line on the Fitchburg path (third `ax.plot(..., color=HSR)` in `main()`). Lowell rows become `HIGH-SPEED RAIL TO CONCORD NH, MONTREAL` and `VIA LOWELL, NASHUA, MANCHESTER, BURLINGTON VT` | None. HSR pills don't change | None | Two for the 2003 study route |
| 2 | **Maine high-speed row moves to the Haverhill line** (Max, Nov 7) | Remove gold from the Newburyport path (fourth gold `ax.plot`) and draw it on the Haverhill path. Move the rows under `HAVERHILL LINE`: `HIGH-SPEED RAIL TO BANGOR`, `VIA HAVERHILL, PORTLAND, AUGUSTA`. Drop the Bangor rows from the Newburyport label | None | None | Two to Portland; Two that Bangor was studied |
| 3 | **Route 128: new commuter stop, and high-speed trains stop there** (Max, Nov 7) | Add a commuter stop on the Providence path between Readville and the Stoughton split (`(46, -1)` to `(46, -3)` is tight, so it may need room). The Key or DECISIONS wording "high-speed only at Tier 1 and 2" needs "and Route 128" | Not a T station, so no pill. Don't confuse it with Red's "Lexington Route 128" | None | Two |
| 4 | **Plymouth reopens** (Max, Nov 7) | `TO PLYMOUTH` can stay. Optional: draw Plymouth as a stop. The `line_audit.md` row "Plymouth on the South Shore line" should say reopened by Max | None | None | Invented reopening |
| 5 | **NYC row adds Philadelphia and Washington** | Optional, if it fits: `HIGH-SPEED RAIL TO NYC, PHILADELPHIA, WASHINGTON` | None | None | Two |
| 6 | **Albany row adds Chicago** | Optional, if it fits: `HIGH-SPEED RAIL TO ALBANY, CHICAGO` | None | None | Two |
| 7 | **Key wording for high-speed stops** | If the Key mentions where high-speed trains stop, list North Station, Boston Central, South Station, Back Bay, West Station and Route 128 | Same, if any poster Key says it | None | Max's call |
| 7a | **North Station ferry pill reads "F via Langone Ferryport"** (Langone spec, item 1) | Walking link from North Station to Langone Ferryport | `FERRY_VIA["North Station"]` = "Langone Ferryport" (Orange, Green, Cyan posters) | North Station pill at Langone Ferryport | Max's call |
| 7b | **Boston Central ferry pill "F via Rowes Wharf"** | Optional walking link from Boston Central to Rowes Wharf | Add `F` to `EXTRA_TRANSFERS["Boston Central"]` and `FERRY_VIA["Boston Central"]` = "Rowes Wharf" (Cyan, Blue, Orange posters) | Already there: Rowes Wharf carries CL and CR | Ferry poster's link |
| 7c | **Quincy Center ferry pill** (South Shore Express, dock "Quincy") | Optional walking link from Quincy Center to the Quincy dock | Add `F` at Quincy Center on the Red poster, in South Shore oxblood | Already there: Quincy carries RL and CR | Ferry poster's link |
| 7d | **Clifton ferry pill** (North Shore) | Clifton dock beside the Clifton commuter stop (Langone spec, item 10) | Not a T station | Clifton stop between Swampscott and Marblehead | Max's call |
| 7e | **High-speed ferry stops marked** | If the Key keeps an express-ferry row, it can use the rail poster's sign: a thin white ring inside the F pill where high-speed boats stop (Langone Ferryport, Salem, Gloucester, Rockport, Quincy, New Bedford) | Same ring on any pill at those docks | Bullseye docks already do this | Max's call ("dont forget high speed ferries too") |

## Docs to update (no drawing)

| # | File | Change |
|---|---|---|
| 8 | `docs/DECISIONS.md`, Rejected list | "Natick and Framingham stops on the Worcester line" and "Rockport as its own drawn branch" become main-map only. On the rail poster Max wants every real station, and Rockport as a fork of one line at Beverly |
| 9 | `docs/DECISIONS.md`, Commuter rail | High-speed rows: Montreal via Lowell and Concord NH; Bangor via Haverhill; Route 128 is a high-speed stop. Rows stay unbranded, with no Amtrak name (Max, Nov 7) |
| 10 | `docs/DECISIONS.md`, Commuter rail | Fitchburg trains skip Belmont and Waverley, where Red now runs. This matches the Haverhill skip at Melrose and Wakefield. Both maps already draw it that way |
| 11 | `docs/VERSIONS.md` | Add `copies/rail_poster_v6.png` and `.pdf` as the current rail poster. v1 to v5 are earlier passes from the same night |
| 12 | `line_audit.md`, row "High-speed destinations" | Montreal and Bangor are no longer "Invented routing": see items 1 and 2 |

## Already the same everywhere (no change)

- Oak Grove on the Haverhill line, and Clifton on the Marblehead branch: the poster reads them from the main map.
- Names follow the main map: Central Sq (Lynn), David Ortiz, Foxboro, Winchester, Hingham. The poster also shows real stations the main map stands in for, with their own names: Norwood Depot and Norwood Central for "Norwood", and Wellesley Farms, Wellesley Hills and Wellesley Square for "Wellesley".
- Transfer and ferry pills come from the line posters' own tables, so they match, including "F via Lovejoy Wharf" and "F via Dorchester Ave".

## Questions for Max (raised one at a time, not changes yet)

- Real names: "Winchester" is Winchester Center, and "Hingham" is West Hingham. Rename them on every map, or keep the short names?
- The line's second color appears on the rail poster only. Should the main map's commuter lines keep one purple?
