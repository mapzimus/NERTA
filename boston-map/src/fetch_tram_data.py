"""Real-geography inputs for the NERTA tram network (Max, November 7: decide trams on a real map, then merge into NERTA).

python fetch_tram_data.py stations   -> data/tram/stations_real.geojson
python fetch_tram_data.py buses      -> data/tram/bus_routes.geojson, data/tram/bus_stops.geojson

Stations: every stop in make_tmap.lines(), placed at its real spot. Two sources per spot where they exist:
  1. MBTA V3 API (data/mbta_stops.gpkg, pulled November 3, 2026), and
  2. OpenStreetMap (Overpass: railway stations, halts, tram stops, public transport stations).
Names neither source knows (new NERTA stops) are geocoded from OpenStreetMap's Nominatim as one source, or left for
placing by hand. Each feature says which sources it rests on and how far apart they are.

Buses: today's frequent routes plus the planned frequent gap routes, from the public MBTA V3 API (no key, 20 calls a
minute). Typical patterns only (typicality 1), as the bus report warns.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, Point, mapping

sys.path.insert(0, str(Path(__file__).parent))
import make_tmap as M  # noqa: E402  (read only: lines() and CR_STOPS)

DAY = Path(__file__).resolve().parents[1]
OUT = DAY / "data" / "tram"
API = "https://api-v3.mbta.com"
UA = {"User-Agent": "nerta-fantasy-map/1.0", "Accept": "application/vnd.api+json"}
BBOX = (42.10, -71.45, 42.62, -70.80)  # south, west, north, east

# Main-map names that differ from the MBTA's or OSM's spelling.
ALIAS = {"Gov't Center": "Government Center", "Mass. Ave": "Massachusetts Avenue", "Tufts Medical Ctr": "Tufts Medical Center",
         "St. Mary's St": "Saint Mary's Street", "St. Paul St": "Saint Paul Street", "Kendall/MIT": "Kendall/MIT",
         "Charles/MGH": "Charles/MGH", "JFK/UMass": "JFK/UMass", "Museum of Fine Arts": "Museum of Fine Arts",
         "Sullivan Sq": "Sullivan Square", "Boston Landing": "Boston Landing", "David Ortiz": "Lansdowne",
         "Medford/Tufts": "Medford/Tufts", "Ball Sq": "Ball Square", "Magoun Sq": "Magoun Square", "Gilman Sq": "Gilman Square",
         "Union Sq": "Union Square", "Jackson Sq": "Jackson Square", "Packard's Corner": "Packard's Corner",
         "Washington Sq": "Washington Square", "Fenwood Rd": "Fenwood Road", "Sutherland Rd": "Sutherland Road",
         "Chiswick Rd": "Chiswick Road", "Chestnut Hill Ave": "Chestnut Hill Avenue", "Dean Rd": "Dean Road",
         "Englewood Ave": "Englewood Avenue", "Harvard Ave": "Harvard Avenue", "Brandon Hall": "Brandon Hall",
         "Central Ave": "Central Avenue", "Valley Rd": "Valley Road", "Capen St": "Capen Street", "Heath St": "Heath Street",
         "Green St": "Green Street", "Hawes St": "Hawes Street", "Kent St": "Kent Street", "Summit Ave": "Summit Avenue",
         "Fairbanks St": "Fairbanks Street", "Tappan St": "Tappan Street", "Griggs St": "Griggs Street",
         "Allston St": "Allston Street", "Warren St": "Warren Street", "Washington St": "Washington Street", "South St": "South Street",
         "Amory St": "Amory Street", "Babcock St": "Babcock Street", "Blandford St": "Blandford Street", "Talbot Ave": "Talbot Avenue",
         "Morton St": "Morton Street", "Blue Hill Ave": "Blue Hill Avenue", "Uphams Corner": "Uphams Corner",
         "Four Corners": "Four Corners/Geneva", "Newmarket": "Newmarket", "Quincy Center": "Quincy Center",
         "Malden Center": "Malden Center", "Arlington Ctr": "Arlington Center", "Lexington Ctr": "Lexington Center",
         "Belmont Ctr": "Belmont", "Waverley Sq": "Waverley", "Lynn Harbor": "Lynn Harbor", "Central Sq": "Lynn",
         "Chelsea": "Chelsea", "Bellingham Sq": "Bellingham Square", "Day Sq": "Day Square", "Everett Sq": "Everett Square",
         "Linden Sq": "Linden Square", "Wyoma Sq": "Wyoma Square", "Thompson Sq": "Thompson Square", "Oak Sq": "Oak Square",
         "Hyde Sq": "Hyde Square", "Wu Sq": "Wu Square", "Inman Sq": "Inman Square", "Roslindale Village": "Roslindale Village",
         "Melrose/Cedar Park": "Melrose/Cedar Park", "Melrose Highlands": "Melrose Highlands", "Wyoming Hill": "Wyoming Hill",
         "Hyde Park": "Hyde Park", "Readville": "Readville", "Fairmount": "Fairmount", "Wellington Hill": "Wellington Hill",
         "Seaver St": "Seaver Street", "Grove Hall": "Grove Hall", "Nubian": "Nubian", "Dover": "Dover", "Northampton": "Northampton",
         "Melnea Cass": "Melnea Cass Boulevard", "Boston Medical": "Boston Medical Center", "Moakley Park": "Moakley Park",
         "Convention Center": "Boston Convention and Exhibition Center", "West Broadway": "West Broadway", "L Street": "L Street Beach",
         "City Point": "City Point", "Fort Point": "Fort Point Channel", "Courthouse": "Courthouse", "Seaport": "Seaport",
         "Terminals": "Logan International Airport", "Winthrop Center": "Winthrop Center", "Navy Yard": "Charlestown Navy Yard",
         "City Square": "City Square", "Encore": "Encore Boston Harbor", "Inner Belt": "Inner Belt",
         "Community College": "Community College", "North End": "North End", "Aquarium": "Aquarium",
         "Binney": "Binney Street", "Mass Ave": "Massachusetts Institute of Technology", "BU Bridge": "Boston University Bridge",
         "West Station": "West Station", "Barrys Corner": "Barrys Corner", "Allston": "Allston", "Brighton Center": "Brighton Center",
         "Newton Corner": "Newton Corner", "Watertown": "Watertown Square", "Boston College": "Boston College",
         "Newton City Hall": "Newton City Hall", "Auburndale": "Auburndale", "Weston": "Weston", "Norumbega": "Norumbega",
         "Wellesley Hills": "Wellesley Hills", "Needham Crossing": "Needham Crossing", "Needham Heights": "Needham Heights",
         "Needham Junction": "Needham Junction", "Hersey": "Hersey", "Newton Upper Falls": "Newton Upper Falls",
         "VFW Parkway": "VFW Parkway", "West Roxbury": "West Roxbury", "Highland": "Highland", "Bellevue": "Bellevue",
         "Weymouth": "Weymouth Landing", "Lexington Route 128": "Route 128 Lexington", "Waltham": "Waltham",
         "Saugus Center": "Saugus Center", "Cliftondale": "Cliftondale Square", "Wonderland": "Wonderland",
         "Vertex Tower": "Fan Pier", "Lansdowne": "Lansdowne", "Landmark Center": "Landmark Center",
         "West Medford": "West Medford", "Medford Hillside": "Medford Hillside", "North Cambridge": "North Cambridge",
         "East Arlington": "East Arlington", "Arlington Heights": "Arlington Heights", "Science Park": "Science Park/West End",
         "Prudential": "Prudential", "Symphony": "Symphony", "Longwood Medical Area": "Longwood Medical Area", "Ruggles": "Ruggles"}


def norm(s):
    s = s.lower().replace("’", "'").replace("saint ", "st ").replace("st. ", "st ")
    for a, b in ((" street", " st"), (" square", " sq"), (" avenue", " ave"), (" road", " rd"), (" center", " ctr"), (" centre", " ctr")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "", s)


def http_json(url, headers=UA, data=None, tries=(0, 10, 30, 65)):
    for wait in tries:
        time.sleep(wait or 3.2)
        try:
            req = urllib.request.Request(url, headers=headers, data=data)
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 504):
                raise
    raise SystemExit(f"rate limited: {url}")


def nerta_stations():
    """name -> list of (color, style) for every stop on every NERTA line."""
    out = {}
    for color, style, _path, stops in M.lines():
        for n in stops:
            out.setdefault(n.rstrip("+"), []).append((color, style))
    for n, _xy, _side, style in M.CR_STOPS:
        out.setdefault(n.replace("\n", " "), []).append((M.CR_TEXT_COLOR, style))
    return out


def overpass_stations():
    s, w, n, e = BBOX
    q = (f'[out:json][timeout:120];(node["railway"~"^(station|halt|tram_stop)$"]({s},{w},{n},{e});'
         f'node["public_transport"="station"]({s},{w},{n},{e}););out;')
    js = http_json("https://overpass-api.de/api/interpreter", {"User-Agent": UA["User-Agent"]}, urllib.parse.urlencode({"data": q}).encode())
    out = {}
    for el in js["elements"]:
        name = el.get("tags", {}).get("name")
        if name:
            out.setdefault(norm(name), []).append((el["lon"], el["lat"], name))
    return out


def nominatim(name):
    s, w, n, e = BBOX
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": f"{name}, Massachusetts", "format": "json", "limit": 1, "viewbox": f"{w},{n},{e},{s}", "bounded": 1})
    js = http_json(url, {"User-Agent": UA["User-Agent"]}, tries=(1.2, 10))
    return (float(js[0]["lon"]), float(js[0]["lat"]), js[0]["display_name"]) if js else None


def dist_m(a, b):
    import math
    dx = (a[0] - b[0]) * 111320 * math.cos(math.radians(42.36))
    dy = (a[1] - b[1]) * 110540
    return math.hypot(dx, dy)


def stations():
    nerta = nerta_stations()
    mb = gpd.read_file(DAY / "data/mbta_stops.gpkg")
    mbta = {norm(r["name"]): (r.geometry.x, r.geometry.y, r["name"]) for _, r in mb.iterrows()}
    osm = overpass_stations()
    feats, todo = [], []
    for n, uses in sorted(nerta.items()):
        keys = [norm(n), norm(ALIAS.get(n, n))]
        a = next((mbta[k] for k in keys if k in mbta), None)
        o = None
        for k in keys:
            if k in osm:
                cands = osm[k]
                o = min(cands, key=lambda c: dist_m(c, a)) if a else cands[0]
                break
        srcs, xy, note = [], None, ""
        if a:
            srcs.append("MBTA API")
            xy = a[:2]
        if o:
            srcs.append("OpenStreetMap")
            xy = xy or o[:2]
            if a:
                note = f"MBTA and OSM {dist_m(a, o):.0f} m apart"
        if not xy:
            g = nominatim(ALIAS.get(n, n))
            if g:
                xy, srcs, note = g[:2], ["Nominatim (OSM)"], g[2][:80]
        if not xy:
            todo.append(n)
            continue
        styles = sorted({s for _, s in uses})
        feats.append({"type": "Feature", "geometry": mapping(Point(*xy)),
                      "properties": {"name": n, "colors": sorted({c for c, _ in uses}), "status": styles, "sources": srcs,
                                     "verified": len(srcs) >= 2, "note": note}})
        print(f"{n:28s} {', '.join(srcs):30s} {note}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "stations_real.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, indent=0), encoding="utf-8")
    print(len(feats), "placed;", len(todo), "not found:", todo)


# ---------------------------------------------------------------------------------------------------------------
# Today's frequent routes, plus planned frequent gap routes (70, 16), and the Columbus Ave routes (29, 44).
EXTRA_ROUTES = ["70", "16", "8", "29", "44"]


def decode(poly):
    coords, i, lat, lon = [], 0, 0, 0
    while i < len(poly):
        for which in (0, 1):
            shift, val = 0, 0
            while True:
                b = ord(poly[i]) - 63
                i += 1
                val |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            d = ~(val >> 1) if val & 1 else val >> 1
            if which == 0:
                lat += d
            else:
                lon += d
        coords.append((lon / 1e5, lat / 1e5))
    return coords


def buses():
    api = lambda path, **p: http_json(f"{API}/{path}?" + urllib.parse.urlencode(p, safe="[],"))  # noqa: E731
    routes = api("routes", **{"filter[type]": "3"})["data"]
    want = {r["id"]: r for r in routes if r["attributes"]["description"] == "Frequent Bus" or r["attributes"]["short_name"] in EXTRA_ROUTES}
    lines, stops = [], {}
    for rid, r in want.items():
        a = r["attributes"]
        pats = api("route_patterns", **{"filter[route]": rid, "include": "representative_trip"})
        trips = {t["id"]: t for t in pats.get("included", [])}
        for p in pats["data"]:
            pa = p["attributes"]
            if pa["typicality"] != 1 or pa["direction_id"] != 0:
                continue
            trip = trips[p["relationships"]["representative_trip"]["data"]["id"]]
            sid = trip["relationships"]["shape"]["data"]["id"]
            poly = api(f"shapes/{sid}")["data"]["attributes"]["polyline"]
            lines.append({"type": "Feature", "geometry": mapping(LineString(decode(poly))),
                          "properties": {"route": a["short_name"], "id": rid, "long_name": a["long_name"], "pattern": pa["name"],
                                         "frequent": a["description"] == "Frequent Bus"}})
        for s in api("stops", **{"filter[route]": rid, "filter[direction_id]": "0"})["data"]:
            st = stops.setdefault(s["id"], {"type": "Feature", "geometry": mapping(Point(s["attributes"]["longitude"], s["attributes"]["latitude"])),
                                            "properties": {"name": s["attributes"]["name"], "routes": []}})
            st["properties"]["routes"].append(a["short_name"])
        print(a["short_name"], a["long_name"], flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "bus_routes.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": lines}), encoding="utf-8")
    (OUT / "bus_stops.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": list(stops.values())}), encoding="utf-8")
    print(len(lines), "route shapes,", len(stops), "stops")


if __name__ == "__main__":
    {"stations": stations, "buses": buses}[sys.argv[1]]()
