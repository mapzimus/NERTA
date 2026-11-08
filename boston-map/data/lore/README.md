# NERTA lore layers (real geography)

These are GeoJSON layers for the fantasy "lore" parts of NERTA, in real lon/lat (WGS84), so a Leaflet working map can draw them over a real basemap. `boston-map/tools/make_tram_realmap.py` reads all five files from this folder. The posters stay schematic. Nothing here changes them.

Built November 8, 2026. The build scripts are kept outside the repo, in the session scratchpad (`lore/build.py`, `water.py`, `docks_table.py`, `geocode.py`, `fetch.py`), along with the cached downloads in `lore/raw/`.

**Data rule.** A real location counts as **verified** only when two independent sources agree within 150 m. OpenStreetMap ferry terminals and Nominatim count as one source, because both are OSM. A location backed by one source, or placed by hand, is **unverified**. **Invented** means the thing does not exist today. The place it sits at may still be real.

## Files

| File | Features | What it is |
|---|---|---|
| `ferry_routes.geojson` | 14 | One feature per ferry route, routed over water |
| `ferry_docks.geojson` | 193 | One point per dock |
| `dig.geojson` | 4 | The BIGGER Dig tunnel line and its three stations |
| `london_ferry.geojson` | 2 | Long Wharf as an international port, and the Atlantic Clipper's course out to sea |
| `landmarks.geojson` | 11 | Lore places that matter to riders but are not stations |

## ferry_routes.geojson

Stop lists come from `boston-map/src/make_ferry_network.py` (`ROUTE_STOPS`, the 14 routes on the Ferry Map). The three river loops use the stop order from `make_tmap.py` (`FERRY_ROUTES`). Colors, names and families come from `make_ferry_network.py` `R` and `FAMILIES`.

Properties:

- `name`, `key`, `color`, `family`.
- `fast`: true for the high-speed streak routes, which are the North Shore Fast Ferry, the South Shore Fast Ferry, and Nantucket and Martha's Vineyard. The "Fast Ferry" shuttle (`express`) is false: it is named fast but drawn as a harbor boat. Its `note` says so.
- `loop`: true for the Charles, Mystic and Chelsea Creek. Each loop is drawn from Langone Ferryport round its stops and back to Langone Ferryport.
- `stops`: the docks in rider order.
- `parts`: the number of line parts.
- `invented: true`: no route exists as drawn.
- `note`.

**Geometry.** Most routes are a single LineString. Two routes have branches, so they are MultiLineStrings:

- South Shore Fast Ferry: the main run plus Canal Pass, the Buzzards Bay leg, the Bass River loop, and New Bedford to Vineyard Haven via Cuttyhunk.
- Nantucket and Martha's Vineyard: the main run plus the Martha's Vineyard ring, the Woods Hole link, the two Cuttyhunk links and the Noman's Land spur.

The web map already handles both geometry types. The river zigzag crossing boats are not drawn.

**How the routes were drawn.** Each leg between docks is a shortest path over a water raster (A*), then straightened wherever the straight line stays on water.

- Water comes from the OSM coastline (Overpass, `natural=coastline`) flood-filled from open-sea seeds, plus OSM water areas (the Charles basin and tidal rivers).
- There are three rasters: inner Boston (15 m cells), the North Shore (40 m) and the South Shore with the Cape and Islands (50 m).
- Paths are steered off the shore where the channel allows.

Five links were added by hand where the data leaves no water path:

1. The Charles River Dam locks.
2. The New Bedford hurricane barrier gate.
3. The Saquatucket Harbor entrance.
4. The Bass River, which uses its OSM river centerline because the river area isn't mapped as water.
5. The Cape Cod Canal, which already comes through at 50 m.

**Check.** Every route was sampled every 20 m. Outside 150 m of a dock, 49 of about 67,000 samples touch land, roughly 0.07%. They are short links from docks that sit on piers or behind narrow entrances: Quincy Point, Cuttyhunk, Harwich Point, New Bedford and Nantasket. Routes are drawn, not surveyed. No real ferry channel was traced.

## ferry_docks.geojson

Properties:

- `name`, `routes` (route names), `major` (a fast-ferry stop, from `MAJOR` in `make_ferry_network.py`), `event` (a special-event dock).
- `sources`, `verified`, `agreement` (which two sources were compared, and how far apart they are).
- `invented`, and `status` ("boats call here today", "real past service" or "dock is ours").
- `snapped_m`: how far an invented dock was moved from its looked-up place to the nearest shoreline.
- `note`.

How each dock was placed:

- **Real docks keep their real spot.** The sources are the OSM `amenity=ferry_terminal` node, plus the MBTA V3 API (`/stops?filter[route_type]=4`) where the MBTA serves the dock, or Wikipedia coordinates.
- **Invented docks** were looked up by place name in Nominatim, with Wikipedia coordinates where an article has them. Each was then moved to the nearest shoreline cell of the route's water. A place already on open water, like "Gloucester Harbor", moves to its nearest shore first.
- 23 docks were placed by hand, because the place has no lookup or the lookup landed inland. Each says why in `note`.

Counts (193 docks):

- **33 real today, 1 real past service (Quincy Point), 159 invented.**
- **Verified (two sources within 150 m): 40.** Of these, 14 are real docks where the MBTA and OSM agree: Long Wharf, Central Wharf, Rowes Wharf, Lovejoy Wharf, Navy Yard, Logan Dock, Fan Pier, Seaport (Commonwealth Pier), Winthrop Landing, Lynn Harbor, Squantum Point, Hingham, Hull and Encore (OSM and Wikipedia). The other 26 are invented docks whose **place** is two-sourced: OSM and Wikipedia agree on the park, bridge or boathouse. The dock itself is still ours.
- **Real but unverified (one source, or sources more than 150 m apart):**
  - One source (OSM only): Battery Wharf, Salem Wharf, Woods Hole, Vineyard Haven, Oak Bluffs, Edgartown, Nantucket Downtown, Hyannis, Falmouth, New Bedford, Newport, Cuttyhunk, Harwich Point (Saquatucket) and Quincy Point.
  - Two sources too far apart: Plymouth Rock (State Pier, Nominatim; Wikipedia's Plymouth Rock is 206 m away), Georges Island (275 m), Spectacle Island (309 m), Thompson Island (566 m) and Provincetown (MacMillan Pier, 1 km). Wikipedia gives the island or town, not the dock.
  - Placed by hand: Chappaquiddick (the Chappy ferry's island side).
- **Invented and placed by hand:**
  - Inner harbor and rivers: Gronk, Poormans, Boston Bay, Dorchester Ave, First St, Bennington St, Gloucester St, Charlesgate, Pearl St, Condor St, Little Mystic.
  - Winthrop, Revere and the North Shore: Highlands Beach, Wonderland, King's Cove, Beverly (Glover Wharf, from the coordinates `make_tmap.py` bends from).
  - South Shore and the Islands: Quincy (Town River), Stadium, Wrinkle Point, Bass River / Rte 28, South Shore (Nantucket).
  - Suffolk Downs, both landings.
- **Two Suffolk Downs landings.** "Suffolk Downs" is the Chelsea Creek boats' landing at the head of the creek, about 1.5 km west of the station. "Suffolk Downs (Belle Isle Inlet)" is the North Shore boats' landing, matching `NSE_SUFFOLK` in `make_tmap.py`. Real water does not reach the site from both sides.
- Every other invented dock rests on one Nominatim lookup, so it is **unverified**.

## dig.geojson

- **The BIGGER Dig** (LineString). It runs from South Station north along Atlantic Ave, then northwest along the Greenway parcels to North Station.
  - Line: OSM `Atlantic Avenue` ways and Rose Kennedy Greenway parcel centroids. End stations: `data/tram/stations_real.geojson`.
  - The tunnel is the North-South Rail Link idea (`line_audit.md`: Two). The alignment is traced on the street and is not an engineering route. The underground walkways to Downtown Crossing and Park St are not drawn.
- **North Station:** MBTA and OSM, 95 m apart. Verified.
- **Boston Central:** invented station on Atlantic Ave at State St, by Aquarium. The site follows the rail link's Central Station near Aquarium (`line_audit.md`: Two for the site). The exact point is the Atlantic Ave vertex nearest State St. Unverified.
- **South Station:** MBTA only in `stations_real.geojson`. Unverified there.

## london_ferry.geojson

Both features are `invented: true`.

- **Long Wharf international port** (Point). The dock is real: MBTA and OSM agree within 4 m. Its role as a port for London is invented.
- **Atlantic Clipper (working name)** (LineString). It leaves Long Wharf through the harbor's main channel, passes Boston Light, then runs east-southeast to clear Cape Cod and Nova Scotia. It stops in open ocean at about 66° W.
  - The harbor part is routed over water like the ferries. The ocean part was checked against Natural Earth 10 m land.
  - Properties: `code` AC, `color` `#1b2f5b` (from `make_tmap.CLIPPER`), `destination` London. The course is ours.

## landmarks.geojson

Properties: `name`, `note`, `invented`, `sources`, `verified`, `agreement`.

| Landmark | Basis | Location check |
|---|---|---|
| Vertex Tower | **Invented** supertall with its own Cyan stop (`line_audit.md`) | Placed by hand on a line between the Seaport and City Point stations. Unverified |
| TD Garden | Event trains (Orange, Green and Cyan posters) | Nominatim and Wikipedia, 11 m. Verified |
| Fenway Park | Event trains (Green and Yellow posters) | 56 m. Verified |
| Encore Boston Harbor | Cyan stop, Mystic dock, event service | 142 m. Verified |
| Stadium site | Proposed stadium at the old Mystic power plant, Everett. Seats: 25,000 or 24,000 (sources differ, `SOURCES.md`) | Mystic Station: Nominatim and Wikipedia, 71 m. Verified |
| Hatch Memorial Shell | Event dock (ferry passenger notice) | 2 m. Verified |
| Agganis Arena | Event dock | 5 m. Verified |
| Leader Bank Pavilion | Event dock "Pavilion" | 19 m. Verified |
| Suffolk Downs | Redevelopment drawn as a larger station. Homes: 10,000 or about 7,000 (sources differ) | The point is the station (Nominatim). Wikipedia's rounded coordinates are 1 km off. Unverified |
| Long Island Recovery Campus | Real plan (`line_audit.md`: Two). The ferry stop is ours | 60 m. Verified |
| Dorchester Bay City (Columbia Point) | Real development (`research/tram-route-assessment.md`; `docs/IDEAS.md`) | One Nominatim hit at the old Bayside Expo site. Unverified |

## Rebuilding

Run the scratchpad's `build.py` with `C:\Users\mhowe\AppData\Local\Python\bin\python.exe`. It reads only the cached files in `raw/` and writes only to this folder. If the ferry stop lists in `make_ferry_network.py` change, run `dump_lore.py` first to refresh `lore_src.json`. A new dock also needs a row in `docks_table.py`, and `geocode.py` must be run for it (Nominatim, at most 1 request a second).
