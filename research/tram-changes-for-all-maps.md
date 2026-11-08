# Tram network: changes the other maps need

November 7, 2026. Written for the session that edits `make_tmap.py`, `make_line_poster.py` and `make_ferry_network.py`. The tram work (`boston-map/tools/make_tram_realmap.py`, `boston-map/src/tram_merge.py`, and later `boston-map/src/make_tram_poster.py`) doesn't edit any of them.

Max's rule: "any changes made in these sessions should reflect on every single map, no oversights."

**Status (November 7, late):** 32 tram routes: the 13 Max approved first and 19 more. Stops are planned for NERTA, not copied from today's bus stops: a stop at every NERTA station a tram passes, shared stops where trams cross, and squares or main cross streets about every 650 m. Data: `boston-map/data/tram/tram_draft.json`; sources and every stop in `boston-map/data/line_audit.md`, section "Tram network (November 7, 2026)". The symbol spec is final, so it comes first. Decisions and reasons are in `research/tram-design-notes.md`.

## Tram line and stop symbol (Max, November 7)

Use this wherever trams appear: the main map, the line posters, the ferry poster and the Keys. Max described it in four messages, and an earlier relay read the cross as always upright. That reading is superseded: Max picked "one arm along the track" from a mockup.

| Part | Drawing |
|---|---|
| Line | Hot pink `#e0457b`, width W (thin: Max's "tiny pink lines"). Round caps. The width stays the same everywhere on the line. |
| Center line | A super thin black line, `#16161a`, down the middle of the pink line, about 0.11 W (0.35 pt when W is 3.2 pt). Butt caps. It stops at each stop's circle. |
| Stop circle | White fill `#ffffff`, hot-pink edge `#e0457b`. Diameter about 7.5 W at poster scale (a 3.2 pt line gets about a 24 pt circle). The edge is about 0.4 W. Drawn over the line, so the line looks skinny inside it. |
| Stop cross | Hot pink, the same stroke as the circle's edge, with butt caps. **One arm along the track and one square across it**, so it reads as a + where the track is level or upright and an X where it runs at 45 degrees. On a curve, follow the track's direction at the stop. Each arm reaches 1.35 times the circle's radius from the center, so it sticks out past the circle by about a third of the radius. |
| Not black | Tram stops are pink, not black-edged. This is Max's exception to the house rule "black edge on every dot", for trams only. |

Sizes are proportional to W, so one symbol works at any scale. The tram poster will confirm the ratios on its first render; if they change, this table changes and I'll message you.

Mockup (not a poster): drawn by `stop_symbol.py` in the tram session's scratchpad.

## Changes to make

| # | What | Main map (`make_tmap.py`) | Line posters | Ferry poster | Status |
|---|---|---|---|---|---|
| 1 | Tram line and stop symbol, above | Only where trams appear | Only if a poster shows a tram line or Key row | Same | Max's call, final |
| 2 | Tram transfer marker at the 76 NERTA stations below | A marker at each listed station | A marker beside each listed station on its line's poster (lists by line below) | Hingham Shipyard dock: the 220 tram stops there | Data final; **the look is Max's call** (question below) |
| 3 | London ferry pill (`AC`, Atlantic Clipper) at a tram stop by Long Wharf or Aquarium | None: no tram stop is within a short walk. The nearest is Haymarket on the 111, 650 m from Aquarium and 780 m from Long Wharf | None | None | Nothing to draw |

**Default until Max says otherwise (tram session's call, November 8):** one short hot-pink pill `TR` (`#e0457b`, white bold text), set after the other pills at each station below. Key row: "TR: Tram". Long pills with route numbers would break the Rejected rule "Long transfer pills". If Max picks route numbers instead, this changes.

**Question for Max (still open):** how should a tram transfer look on the main map and the line posters? Options: (a) a hot-pink pill with the route numbers, like `T 66 1 15 23` at Nubian; (b) one generic pink tram pill, with numbers only on the tram poster; (c) the tram stop symbol (pink circle and cross) as a small mark beside the station. Busiest: Quincy Center and Forest Hills (5 trams each), Harvard (5), Nubian (4), Ashmont (4).

### Stations where a tram stops

Names are the main map's labels; where `lines()` uses another key, it follows in parentheses. Lines come from `stations_real.geojson`, so commuter rail shows only at commuter-only stops; the posters' own `EXTRA_TRANSFERS` adds CR, ferry and high-speed pills as now.

| Station | NERTA lines | Tram routes stopping |
|---|---|---|
| Allston | Green | 66, 64 |
| Andrew | Red | 16 |
| Arlington | Green | 9 |
| Arlington Center (`Arlington Ctr` in `lines()`) | Red | 95 |
| Ashmont | Red | 22, 23, 240, 215 |
| Bellevue | Orange | 38 |
| Bellingham Sq | Yellow | 111, 116 |
| Belmont Center (`Belmont Ctr` in `lines()`) | Red | 75 |
| Blue Hill Ave | Orange, Indigo | 31 |
| Boston Landing | Commuter rail | 64 |
| Boston Medical | Yellow | 1 |
| Brigham Circle | Green | 66 |
| Broadway | Red, Cyan | 9 |
| Brookline Hills | Green | 60 |
| Brookline Village | Green | 66, 60 |
| Cedar Grove | Red | 215 |
| Central | Red | 1, 70, 64 |
| Central Ave | Red | 240 |
| Central Sq | Blue | 455 |
| City Point | Cyan | 9 |
| City Sq (`City Square` in `lines()`) | Cyan | 111 |
| Coolidge Corner | Green | 66 |
| Copley | Green | 9 |
| David Ortiz | Commuter rail | 60 |
| Dover | Orange | 9 |
| Everett Sq | Yellow | 110 |
| Fenway | Green, Yellow | 60 |
| Fields Corner | Red | 15 |
| Forest Hills | Orange, Green | 16, 31, 34, 34E, 38 |
| Four Corners | Indigo | 16, 23 |
| Grove Hall | Orange | 23 |
| Harvard | Red, Green | 66, 1, 71, 75, 78 |
| Harvard Ave | Green | 66 |
| Haymarket | Orange, Green | 111 |
| Hingham | Commuter rail | 220 |
| Hynes | Green | 1 |
| Jackson Sq | Orange | 22 |
| Kendall (`Kendall/MIT` in `lines()`) | Red, Yellow | 64 |
| Kenmore | Green, Yellow | 60 |
| Malden Center | Orange | 101, 106 |
| MIT (`Mass Ave` in `lines()`) | Blue, Yellow | 1 |
| Mass Ave (`Mass. Ave` in `lines()`) | Orange | 1 |
| Mattapan | Red, Orange | 31 |
| Maverick | Blue | 116 |
| Melnea Cass | Yellow | 1 |
| Milton | Red | 240 |
| Mission Park | Green | 66 |
| Navy Yard | Cyan | 111 |
| Newmarket | Yellow, Indigo | 16 |
| North Station | Orange, Green, Cyan | 111 |
| Northampton | Orange | 1 |
| Norwood | Commuter rail | 34E |
| Nubian | Orange, Yellow | 66, 1, 15, 23 |
| Oak Sq | Green | 64 |
| Orient Heights | Blue | 712 |
| Quincy Center | Red | 216, 225, 222, 220, 215 |
| Revere Beach | Blue | 110 |
| Roslindale Village | Orange | 34, 34E |
| Roxbury Crossing | Orange | 66, 22 |
| Ruggles | Orange, Yellow | 22 |
| Salem | Commuter rail | 455 |
| Seaver St | Orange | 16, 22 |
| South Salem | Commuter rail | 455 |
| Sullivan Sq | Orange, Yellow | 101, 95 |
| Swampscott | Commuter rail | 455 |
| Talbot Ave | Indigo | 22 |
| Uphams Corner | Indigo | 16, 15 |
| Walpole | Commuter rail | 34E |
| Waltham | Red | 70 |
| Watertown | Green | 70, 71 |
| Wellington | Orange | 110, 100, 106 |
| Wellington Hill | Orange | 31 |
| West Broadway | Cyan | 9 |
| West Medford | Green | 95 |
| West Station | Blue, Green, Yellow | 66, 64 |
| Wonderland | Orange, Blue | 116, 110, 455 |

### By line poster

- **Red**: Andrew, Arlington Center, Ashmont, Belmont Center, Broadway, Cedar Grove, Central, Central Ave, Fields Corner, Harvard, Kendall, Mattapan, Milton, Quincy Center, Waltham
- **Orange**: Bellevue, Blue Hill Ave, Dover, Forest Hills, Grove Hall, Haymarket, Jackson Sq, Malden Center, Mass Ave, Mattapan, North Station, Northampton, Nubian, Roslindale Village, Roxbury Crossing, Ruggles, Seaver St, Sullivan Sq, Wellington, Wellington Hill, Wonderland
- **Blue**: Central Sq, MIT, Maverick, Orient Heights, Revere Beach, West Station, Wonderland
- **Green**: Allston, Arlington, Brigham Circle, Brookline Hills, Brookline Village, Coolidge Corner, Copley, Fenway, Forest Hills, Harvard, Harvard Ave, Haymarket, Hynes, Kenmore, Mission Park, North Station, Oak Sq, Watertown, West Medford, West Station
- **Yellow**: Bellingham Sq, Boston Medical, Everett Sq, Fenway, Kendall, Kenmore, MIT, Melnea Cass, Newmarket, Nubian, Ruggles, Sullivan Sq, West Station
- **Cyan**: Broadway, City Point, City Sq, Navy Yard, North Station, West Broadway
- **Indigo**: Blue Hill Ave, Four Corners, Newmarket, Talbot Ave, Uphams Corner
- **Silver**: none. No tram reaches Logan.
- **Commuter rail only** (main map commuter stops and the rail poster): Boston Landing, David Ortiz, Hingham, Norwood, Salem, South Salem, Swampscott, Walpole.

### Stops that moved off the station spot

The tram stop sits at the station's spot in `stations_real.geojson`, except where that spot was a street centroid or off the square: Melnea Cass and Northampton (1), Uphams Corner (15, 16: Columbia Rd at Hancock St), Grove Hall (23: Washington St at Blue Hill Ave), Seaver St (16, 22: Blue Hill Ave at the Franklin Park Zoo gate). Nothing on the main map moves; this only matters if a map is drawn in real geography.

### NERTA stations no tram reaches

Stadium (890 m from the 101), Inner Belt (750 m from the 95) and Wu Sq (460 m from the 38) have no tram stop. Everett Sq, Grove Hall and Melnea Cass do.

## Docs to update (no drawing)

| # | File | Change |
|---|---|---|
| 4 | `docs/DECISIONS.md` | Add the tram line and stop symbol above, and that the tram color is hot pink `#e0457b`. Add trams to the T's stripe note: the main map's T has an 11th stripe labeled "tram (Green)", so whether that stripe turns hot pink is Max's call, not yet asked |
| 5 | `docs/DECISIONS.md` | Tram network: 32 routes, stops planned for NERTA. Route ends changed: the 15 and 23 end at Nubian (not Ruggles), the 9 at City Point station, the 31 at Mattapan |
