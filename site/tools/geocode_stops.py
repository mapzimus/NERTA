"""Build site/data/locations.json: real-world lat/lon for every NERTA stop name.

Rerunnable. Every web response is cached in site/tools/.geocode_cache.json, so a
rerun from cache makes no network calls.

Sources (each is one named source under the two-source rule):
  MBTA API         api-v3.mbta.com stops (subway, light rail, commuter rail, ferry, Silver Line bus)
  OpenStreetMap    Overpass (stations, ferry terminals, airport terminals) and Nominatim. One source.
  USGS GNIS        The National Map Gazetteer (populated places, landforms, water features, crossings)
  Wikidata         wbsearchentities + P625 coordinates
Wikidata often copies GNIS for villages. When the two sit within 15 m of each other they count as
one source, and the note says so.

Reused as-is: the verified stations in boston-map/data/tram/stations_real.geojson (read only).

A verified location needs two independent sources within 250 m (stations) or 400 m (docks,
places). Docks must also sit within 200 m of mapped water (OSM coastline, water or riverbank,
checked with Overpass); a dock whose sourced point is inland is moved by hand to the waterfront
and marked unverified.

Run:  python site/tools/geocode_stops.py
"""
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAMES = ROOT / "site" / "tools" / "stop_names.json"
GEO = ROOT / "boston-map" / "data" / "tram" / "stations_real.geojson"
CACHE = ROOT / "site" / "tools" / ".geocode_cache.json"
OUT = ROOT / "site" / "data" / "locations.json"
UA = "nerta-geocoder/1.0"
# Shoreline geometry queries are heavy on Overpass. Only cached ones are used unless NERTA_FETCH_SHORE=1.
FETCH_SHORE = os.environ.get("NERTA_FETCH_SHORE") == "1"
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]

ST_TOL, PLACE_TOL, WATER_R, ISLAND_WATER_R = 250, 400, 200, 700

# ---------------------------------------------------------------- cache + http
_cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
_dirty = 0
_last = {}


def save_cache():
    CACHE.write_text(json.dumps(_cache, separators=(",", ":")), encoding="utf-8")


def http(key, url, data=None, gap=0.2, host="x"):
    global _dirty
    if key in _cache:
        return _cache[key]
    for i, wait in enumerate((0, 5, 20, 60, 5, 30)):
        time.sleep(wait)
        dt = time.time() - _last.get(host, 0)
        if dt < gap:
            time.sleep(gap - dt)
        _last[host] = time.time()
        u = OVERPASS[i % len(OVERPASS)] if host == "overpass" else url
        try:
            req = urllib.request.Request(u, data=data, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=200) as r:
                js = json.load(r)
            if "runtime error" in str(js.get("remark", "")):  # Overpass timeout: partial answer, do not cache
                continue
            break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
        except (urllib.error.URLError, TimeoutError):
            pass
    else:
        raise SystemExit(f"gave up: {url}")
    _cache[key] = js
    _dirty += 1
    if _dirty % 20 == 0:
        save_cache()
    return js


def dist(a, b):
    lat = math.radians((a[0] + b[0]) / 2)
    return math.hypot((a[1] - b[1]) * 111320 * math.cos(lat), (a[0] - b[0]) * 110574)


def norm(s):
    s = s.lower().replace("’", "'").replace("'", "").replace("&", " and ")
    s = re.sub(r"\bferry (terminal|landing|dock|pier)\b", " ", s)
    s = re.sub(r"\b(station|stop|ferry|terminal dock|mbta)\b", " ", s)
    for a, b in (("street", "st"), ("square", "sq"), ("avenue", "ave"), ("road", "rd"), ("center", "ctr"),
                 ("centre", "ctr"), ("saint", "st"), ("point", "pt"), ("mount", "mt")):
        s = re.sub(rf"\b{a}\b", b, s)
    return re.sub(r"[^a-z0-9]+", "", s)


# ---------------------------------------------------------------- sources
def mbta_index():
    out = {}
    js = http("mbta:stops", "https://api-v3.mbta.com/stops?filter[route_type]=0,1,2,4&page[limit]=5000")
    rows = list(js["data"])
    for r in ("741", "742", "743", "746"):
        rows += http(f"mbta:route:{r}", f"https://api-v3.mbta.com/stops?filter[route]={r}")["data"]
    for d in rows:
        a = d["attributes"]
        if a["latitude"] is None:
            continue
        for nm in {a["name"], a["name"].split("/")[0], re.sub(r"\s*\(.*\)", "", a["name"])}:
            out.setdefault(norm(nm), []).append((a["latitude"], a["longitude"], a["name"], a.get("vehicle_type")))
    return out


def overpass_index():
    q = ("[out:json][timeout:300];("
         'nwr["railway"~"^(station|halt)$"](40.9,-72.2,43.9,-69.6);'
         'nwr["public_transport"="station"](40.9,-72.2,43.9,-69.6);'
         'nwr["amenity"="ferry_terminal"](40.9,-72.2,43.9,-69.6);'
         'nwr["aeroway"="terminal"](42.35,-71.04,42.38,-71.0);'
         'nwr["amenity"="car_rental"](42.35,-71.04,42.38,-71.0);'
         ");out center tags;")
    js = http("overpass:index", "https://overpass-api.de/api/interpreter",
              urllib.parse.urlencode({"data": q}).encode(), gap=2, host="overpass")
    out = {}
    for el in js["elements"]:
        t = el.get("tags", {})
        lat, lon = (el["lat"], el["lon"]) if "lat" in el else (el["center"]["lat"], el["center"]["lon"])
        for k in ("name", "alt_name", "official_name", "short_name"):
            if t.get(k):
                for nm in {t[k], t[k].split("/")[0]}:
                    out.setdefault(norm(nm), []).append((lat, lon, t[k]))
    return out


def nominatim(q, hint, r_km):
    d = r_km / 111.0
    lat, lon = hint
    dl = d / math.cos(math.radians(lat))
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 6, "viewbox": f"{lon-dl},{lat+d},{lon+dl},{lat-d}", "bounded": 1})
    js = http(f"nom:{q}|{round(lat,2)},{round(lon,2)},{r_km}", url, gap=1.1, host="nominatim")
    return [(float(x["lat"]), float(x["lon"]), x.get("display_name", "")[:70]) for x in js]


def gnis(q):
    url = ("https://carto.nationalmap.gov/arcgis/rest/services/geonames/MapServer/find?" + urllib.parse.urlencode(
        {"searchText": q, "layers": "1,2,3,5,6,7,10,12,13,14", "searchFields": "gaz_name", "contains": "false",
         "sr": 4326, "f": "json"}))
    js = http("gnis:" + q, url, gap=0.3, host="gnis")
    keep = [r for r in js.get("results", []) if r["attributes"].get("state_alpha") in ("MA", "RI", "NH", "ME")]
    if len(keep) != len(js.get("results", [])):  # keep the cache small: New England rows only
        js = _cache["gnis:" + q] = {"results": keep}
    out = []
    for r in js.get("results", []):
        a = r["attributes"]
        if a.get("state_alpha") not in ("MA", "RI", "NH", "ME"):
            continue
        for lon, lat in r["geometry"].get("points", []):
            out.append((lat, lon, f'{a["gaz_name"]} ({a["gaz_featureclass"]}, {a["county_name"]} Co.)'))
    return out


def wikidata(q):
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbsearchentities", "search": q, "language": "en", "limit": 12, "format": "json", "type": "item"})
    js = http("wds:" + q, url, gap=0.3, host="wikidata")
    ids = [x["id"] for x in js.get("search", [])]
    if not ids:
        return []
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbgetentities", "ids": "|".join(ids), "props": "claims|labels", "languages": "en", "format": "json"})
    key = "wde:" + "|".join(ids)
    js = http(key, url, gap=0.3, host="wikidata")
    if "c" in js:  # compacted
        return [tuple(x) for x in js["c"]]
    ents = js.get("entities", {})
    out = []
    for i in ids:
        e = ents.get(i, {})
        for c in e.get("claims", {}).get("P625", []):
            v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
            if v:
                out.append((v["latitude"], v["longitude"], f'{e.get("labels", {}).get("en", {}).get("value", i)} ({i})'))
    _cache[key] = {"c": [list(x) for x in out]}  # keep only coordinates and labels in the cache
    return out


# Overpass water proximity, batched. Returns metres-free answer: True if mapped water within r.
def near_water(points):
    """points: list of (lat, lon, r). Returns dict key->bool."""
    todo = [p for p in points if f"water:{p[0]:.5f},{p[1]:.5f},{p[2]}" not in _cache]
    for i in range(0, len(todo), 25):
        chunk = todo[i:i + 25]
        parts = []
        for lat, lon, r in chunk:
            a = f"(around:{r},{lat},{lon})"
            parts.append(f'(way{a}["natural"="coastline"];way{a}["natural"="water"];rel{a}["natural"="water"];'
                         f'way{a}["waterway"="riverbank"];way{a}["water"];rel{a}["water"];'
                         f'way{a}["natural"="bay"];rel{a}["natural"="bay"];way{a}["man_made"="pier"];);out count;')
        q = "[out:json][timeout:300];" + "".join(parts)
        js = http(f"waterbatch:{chunk}", "https://overpass-api.de/api/interpreter",
                  urllib.parse.urlencode({"data": q}).encode(), gap=3, host="overpass")
        counts = [int(e["tags"]["total"]) for e in js["elements"] if e.get("type") == "count"]
        if len(counts) != len(chunk):
            raise SystemExit("water check: count mismatch")
        for (lat, lon, r), c in zip(chunk, counts):
            _cache[f"water:{lat:.5f},{lon:.5f},{r}"] = c > 0
    return {p: _cache[f"water:{p[0]:.5f},{p[1]:.5f},{p[2]}"] for p in points}


# river, harbor and bay water; untagged water areas count too (New Bedford Harbor is one); ponds and lakes do not
SHORE = '["water"!~"^(pond|lake|reservoir|basin|wastewater|reflecting_pool|fountain)$"]["name"!~"(Pond|Lake|Reservoir)$"]'


def _compact(key, js):
    """Keep only geometry vertices in the cache (Overpass geometry replies are large)."""
    if js.get("elements") and "v" not in js:
        js = {"v": [[round(a, 6), round(b, 6)] for a, b in _verts(js)]}
        _cache[key] = js
    return js


def _verts(js):
    if "v" in js:
        return [tuple(x) for x in js["v"]]
    out = []
    for el in js.get("elements", []):
        for g in [el.get("geometry")] + [m.get("geometry") for m in el.get("members", [])]:
            for v in g or []:
                if v:
                    out.append((v["lat"], v["lon"]))
    return out


def shoreline(lat, lon, r=2000):
    """Vertices of sea coast, riverbanks and river/harbor water areas within r m (OSM via Overpass)."""
    d = r / 111000 + 0.002
    dl = d / math.cos(math.radians(lat))
    bb = f"{lat-d},{lon-dl},{lat+d},{lon+dl}"
    a = f"(around:{r},{lat},{lon})"
    q = (f'[out:json][timeout:180];(way{a}["natural"="coastline"];way{a}["waterway"="riverbank"];'
         f'way{a}["natural"="water"]{SHORE};rel{a}["natural"="water"]{SHORE};);out geom({bb});')
    key = f"shore2:{lat:.5f},{lon:.5f},{r}"
    if key not in _cache and not FETCH_SHORE:
        return []
    try:
        js = http(key, "https://overpass-api.de/api/interpreter",
                  urllib.parse.urlencode({"data": q}).encode(), gap=3, host="overpass")
    except SystemExit:  # Overpass kept timing out: try a smaller circle, else report no shoreline
        print(f"shoreline query failed at {lat:.5f},{lon:.5f} r={r}", file=sys.stderr)
        return shoreline(lat, lon, r // 2) if r > 600 else []
    js = _compact(key, js)
    return [v for v in _verts(js) if dist(v, (lat, lon)) <= r]


def street_end(names, hint, r_km):
    """Shoreline point nearest to the named street, near the hint."""
    lat, lon = hint
    rx = "^(" + "|".join(re.escape(n) for n in names) + ")$"
    q = (f'[out:json][timeout:120];way(around:{int(r_km*1000)},{lat},{lon})["highway"]["name"~"{rx}"];out geom;')
    key = f"street:{names}|{lat:.4f},{lon:.4f},{r_km}"
    js = http(key, "https://overpass-api.de/api/interpreter",
              urllib.parse.urlencode({"data": q}).encode(), gap=3, host="overpass")
    js = _compact(key, js)
    sv = [v for v in _verts(js) if dist(v, hint) <= r_km * 1000]
    if not sv:
        return None
    shore = shoreline(lat, lon, int(r_km * 1000) + 600)
    if not shore:
        return None
    best = None
    for v in sv:
        for w in shore:
            if abs(v[0] - w[0]) > 0.01 or abs(v[1] - w[1]) > 0.013:
                continue
            dd = dist(v, w)
            if best is None or dd < best[0]:
                best = (dd, w)
    return (best[1], round(best[0])) if best else None


def snap(lat, lon, r=2000):
    sh = shoreline(lat, lon, r)
    if not sh:
        return None
    w = min(sh, key=lambda v: dist(v, (lat, lon)))
    return w, round(dist(w, (lat, lon)))


# ---------------------------------------------------------------- specs
# kind: st (station), dock, island, street (dock named for a street: placed by hand at its waterfront),
#       hand (invented: placed by hand).
# Each spec: (kind, lat, lon, radius_km, [search names], note). lat/lon is the hint: candidates must fall
# within radius_km of it, and it is the hand placement when no sourced point qualifies.
S = {}


def spec(name, kind, lat, lon, r, q=None, note=""):
    S[name] = (kind, lat, lon, r, q or [name], note)


# --- commuter rail stations missing from the geojson
for n, la, lo, q in [
    ("Andover", 42.658, -71.144, None), ("Ashland", 42.261, -71.478, None), ("Attleboro", 41.940, -71.285, None),
    ("Ballardvale", 42.627, -71.160, None), ("Bradford", 42.766, -71.088, None),
    ("Brandeis/Roberts", 42.361, -71.260, ["Brandeis/Roberts", "Brandeis"]), ("Campello", 42.060, -71.012, None),
    ("Canton Center", 42.157, -71.146, None), ("Canton Junction", 42.163, -71.153, None),
    ("Church St", 41.665, -70.930, ["Church Street", "Church St"]),
    ("Dedham Corporate Center", 42.227, -71.174, None), ("East Taunton", 41.87, -71.05, None),
    ("Fall River Depot", 41.70, -71.15, None), ("Fitchburg", 42.581, -71.792, None),
    ("Forge Park/495", 42.090, -71.439, ["Forge Park/495", "Forge Park"]), ("Framingham", 42.276, -71.420, None),
    ("Franklin", 42.084, -71.397, ["Franklin", "Franklin/Dean College"]), ("Freetown", 41.77, -71.10, None),
    ("Gloucester", 42.616, -70.668, None), ("Grafton", 42.246, -71.685, None), ("Halifax", 42.014, -70.825, None),
    ("Hamilton/Wenham", 42.610, -70.875, None), ("Haverhill", 42.773, -71.087, None),
    ("Holbrook/Randolph", 42.156, -71.027, None), ("Ipswich", 42.676, -70.840, None),
    ("Kendal Green", 42.378, -71.282, None), ("Lawrence", 42.701, -71.152, None), ("Lincoln", 42.414, -71.325, None),
    ("Littleton/Route 495", 42.519, -71.502, None), ("Lowell", 42.638, -71.315, None),
    ("Manchester", 42.574, -70.770, None), ("Middleborough", 41.88, -70.92, None),
    ("Montello", 42.106, -71.022, None), ("Montserrat", 42.562, -70.869, None),
    ("Nantasket Junction", 42.245, -70.838, None), ("Natick Center", 42.286, -71.347, None),
    ("New Bedford", 41.640, -70.927, None), ("Newburyport", 42.797, -70.878, None), ("Norfolk", 42.120, -71.325, None),
    ("North Beverly", 42.583, -70.884, None), ("North Billerica", 42.593, -71.281, None),
    ("North Leominster", 42.540, -71.739, None), ("North Wilmington", 42.569, -71.160, None),
    ("Norwood Central", 42.189, -71.199, None), ("Norwood Depot", 42.196, -71.197, None),
    ("Pawtucket/Central Falls", 41.880, -71.390, None), ("Providence", 41.829, -71.413, None),
    ("Rockport", 42.656, -70.626, None), ("Route 128", 42.210, -71.148, None), ("Rowley", 42.727, -70.860, None),
    ("Sharon", 42.124, -71.184, None), ("Shirley", 42.545, -71.648, None), ("South Weymouth", 42.153, -70.952, None),
    ("Southborough", 42.267, -71.524, None), ("TF Green Airport", 41.726, -71.443, ["TF Green Airport", "T.F. Green Airport"]),
    ("Wachusett", 42.553, -71.849, None), ("Wedgemere", 42.445, -71.141, None),
    ("Wellesley Farms", 42.323, -71.272, None), ("Wellesley Square", 42.297, -71.294, None),
    ("West Concord", 42.457, -71.392, None), ("West Gloucester", 42.611, -70.706, None),
    ("West Natick", 42.283, -71.390, None), ("Westborough", 42.269, -71.647, None),
    ("Weymouth Landing/East Braintree", 42.221, -70.968, None), ("Whitman", 42.083, -70.923, None),
    ("Wickford Junction", 41.581, -71.491, None), ("Windsor Gardens", 42.172, -71.220, None),
    ("Worcester", 42.261, -71.795, ["Worcester", "Union Station Worcester"]),
    ("Beverly Farms", 42.561, -70.812, None),
]:
    spec(n, "st", la, lo, 6, (q or [n]) + [f"{(q or [n])[0]} station"])

# commuter stations with no station today (South Coast Rail phase 2, Marlborough branch, Clifton, Plymouth)
spec("North Easton", "st", 42.068, -71.106, 4, ["North Easton station", "North Easton"],
     "South Coast Rail phase 2 site (historic North Easton depot)")
spec("Easton Village", "st", 42.030, -71.103, 4, ["Easton Village station", "South Easton"],
     "South Coast Rail phase 2 site, Easton Village")
spec("Raynham Place", "st", 41.935, -71.050, 5, ["Raynham Place station", "Raynham Place"],
     "South Coast Rail phase 2 site at Raynham Place")
spec("Taunton", "st", 41.903, -71.092, 4, ["Taunton station", "Dean Street station"],
     "South Coast Rail phase 2 Taunton (Dean St) site")
spec("Plymouth", "st", 41.981, -70.692, 4, ["Plymouth station", "Plymouth (MBTA station)"],
     "Closed since 2021, Cordage Park")
spec("Hudson", "hand", 42.3917, -71.5664, 3, ["Hudson"],
     "Invented stop on the South Acton to Marlborough branch: placed by hand in downtown Hudson on the old branch "
     "(now the Assabet River Rail Trail) near Main St")
spec("Marlborough", "hand", 42.3466, -71.5508, 3, ["Marlborough"],
     "No station today: placed by hand in downtown Marlborough by the old branch terminal near Main St")
spec("Clifton", "hand", 42.4926, -70.8876, 2, ["Clifton"],
     "Invented stop at the real Clifton neighborhood of Marblehead: placed by hand on the old Marblehead branch "
     "right-of-way (now a rail trail) at Clifton Ave")

# --- stops added after stop_names.json was written
EXTRA = [{"name": "Bleachery", "modes": ["subway:red", "subway:green"]}]
spec("Bleachery", "st", 42.3650, -71.2390, 2, ["Bleachery"],
     "NERTA Red and Green terminus named for the real Bleachery neighborhood of Waltham (Moody St and Pine St, "
     "by the Charles); placed at the neighborhood point")

# --- Silver Line at Logan
spec("Terminal A", "st", 42.3643, -71.0210, 0.8, ["Terminal A"])
spec("Terminal B", "st", 42.3629, -71.0175, 0.8, ["Terminal B", "Terminal B Stop 1"])
spec("Terminal C", "st", 42.3664, -71.0163, 0.8, ["Terminal C"])
spec("Terminal E", "st", 42.3692, -71.0199, 0.8, ["Terminal E"])
spec("Terminal D", "hand", 42.3676, -71.0168, 1, None,
     "Terminal D was folded into Terminal C in 2006 and returns here as a what-if: placed by hand on the Terminal C "
     "to E connector where it used to be")
spec("Terminal F", "hand", 42.3713, -71.0178, 1, None,
     "Invented on purpose (no real Terminal F): placed by hand on the apron north of Terminal E")
spec("Rental Cars", "st", 42.3734, -71.0322, 1, ["Rental Car Center", "Logan Rental Car Center", "Rental Car Center (Logan)"],
     "Logan Rental Car Center")
spec("Office Center", "st", 42.3640, -71.0300, 1.2, ["Logan Office Center", "Office Center"],
     "Logan Office Center, Harborside Dr")
spec("Parking", "hand", 42.3658, -71.0186, 1, None,
     "Logan central parking garage; line_audit.md calls the position schematic. Placed by hand at the Central Garage")
spec("Logan Dock", "dock", 42.3590, -71.0280, 1, ["Logan Airport", "Logan Airport Ferry Terminal", "Logan Dock"],
     "Logan ferry dock on Harborside Dr")
spec("Logan Dock (dock)", "dock", 42.3590, -71.0280, 1, ["Logan Airport", "Logan Airport Ferry Terminal", "Logan Dock"],
     "Same spot as the Silver Line stop: the Logan ferry dock on Harborside Dr")

# --- Charles River docks (Boston bank upstream, then Cambridge bank inbound)
spec("Lovejoy Wharf", "dock", 42.3668, -71.0592, 1, ["Lovejoy Wharf"])
spec("Nashua St", "dock", 42.3680, -71.0648, 1, ["Nashua Street Park"], "at Nashua Street Park")
spec("Gronk", "hand", 42.3617, -71.0722, 1, None,
     "Placeholder name (label reads 'Gronk (rename)'), no real place: placed by hand on the Boston bank between "
     "Nashua St and the Hatch Shell, at the Esplanade by the Longfellow Bridge")
spec("Hatch Shell", "dock", 42.3576, -71.0742, 1, ["Hatch Memorial Shell", "Hatch Shell"], "at the Hatch Memorial Shell")
spec("Esplanade", "dock", 42.3545, -71.0800, 2, ["Charles River Esplanade", "Esplanade"])
spec("Gloucester St", "street", 42.3519, -71.0872, 1, ["Gloucester Street"],
     "Back Bay street: dock placed by hand on the Esplanade at the foot of Gloucester St")
spec("BU Docks", "hand", 42.3522, -71.1003, 1, ["Boston University Sailing Pavilion"],
     "No place by this name: placed by hand at the Boston University sailing dock on the Boston bank behind Bay State Rd")
spec("BU Bridge (dock)", "dock", 42.3515, -71.1112, 1, ["Boston University Bridge", "BU Bridge"],
     "Boston bank at the foot of the BU Bridge")
spec("Agganis", "dock", 42.3540, -71.1185, 1.2, ["Agganis Arena"], "named for Agganis Arena")
spec("Western Ave", "street", 42.3628, -71.1265, 1, ["Western Avenue Bridge", "Western Avenue"],
     "Western Ave bridge: dock placed by hand on the Allston bank at the bridge")
spec("John W. Weeks", "dock", 42.3697, -71.1206, 1, ["John W. Weeks Bridge", "Weeks Footbridge", "John W. Weeks Footbridge"],
     "John W. Weeks footbridge")
spec("Newell", "dock", 42.3700, -71.1235, 1, ["Newell Boathouse"], "Newell Boathouse, Allston")
spec("Cumnock", "dock", 42.3690, -71.1275, 1.2, ["Cumnock Field", "Cumnock Fields"], "Harvard's Cumnock Field, Allston")
spec("Herter", "dock", 42.3650, -71.1420, 1.5, ["Herter Park", "Christian Herter Park"], "Christian Herter Park")
spec("Northeastern (dock)", "dock", 42.3640, -71.1520, 1.5, ["Henderson Boathouse"],
     "Northeastern's Henderson Boathouse on Soldiers Field Rd; the Green Line station is 5 km away in the Fenway")
spec("Arsenal St", "street", 42.3636, -71.1625, 1.5, ["Arsenal Street"],
     "Arsenal St: dock placed by hand on the Charles where Arsenal St meets Greenough Blvd and N Beacon St")
spec("Belmont Hill", "hand", 42.3729, -71.1372, 1, ["Belmont Hill School"],
     "Belmont Hill and Winsor share a boathouse on Greenough Blvd by the Eliot Bridge (Wikipedia list of Charles River "
     "boathouses): placed by hand there, just upstream of Winsor")
spec("Winsor", "hand", 42.3727, -71.1356, 1, None,
     "Shared Belmont Hill and Winsor boathouse on Greenough Blvd: placed by hand just downstream of Belmont Hill")
spec("Eliot (dock)", "dock", 42.3718, -71.1430, 1, ["Eliot Bridge"], "Charles River dock at the Eliot Bridge, Cambridge bank")
spec("Weld", "dock", 42.3697, -71.1214, 1, ["Weld Boathouse"], "Weld Boathouse")
spec("Riverside (dock)", "dock", 42.3577, -71.1155, 1, ["Riverside Boat Club"], "Riverside Boat Club, Memorial Dr")
spec("Magazine Beach", "dock", 42.3567, -71.1130, 1, ["Magazine Beach"])
spec("DeWolfe", "dock", 42.3540, -71.1066, 1, ["DeWolfe Boathouse"], "BU's DeWolfe Boathouse, Memorial Dr")
spec("Resch", "dock", 42.3562, -71.0965, 1, ["Pierce Boathouse", "Richard J. Resch Boathouse", "MIT Boathouse"],
     "MIT's Resch (old Pierce) Boathouse")
spec("Ames St", "street", 42.3594, -71.0885, 1, ["Ames Street"],
     "Ames St: dock placed by hand on Memorial Dr at the foot of Ames St")
spec("Broad Canal", "dock", 42.3627, -71.0800, 1, ["Broad Canal"], "Broad Canal, Kendall Sq")
spec("Poormans", "hand", 42.3650, -71.0752, 1, None,
     "Not found as a real place: placed by hand on the Cambridge bank between Broad Canal and the Museum of Science, "
     "on Cambridge Pkwy near the Lechmere Canal")
spec("Charlesgate", "dock", 42.3500, -71.0925, 1.5, ["Charlesgate"],
     "Real Charlesgate is on the Boston bank where the Muddy River meets the Charles; Max lists it on the Cambridge bank")
spec("Museum of Science", "dock", 42.3677, -71.0709, 1, ["Museum of Science"])
spec("North Point", "dock", 42.3700, -71.0690, 1, ["North Point Park"], "North Point Park")
spec("Duck Tours", "hand", 42.3698, -71.0674, 1, None,
     "Named for the duck boats that enter the river by the Museum of Science: placed by hand on the river between "
     "North Point Park and Paul Revere Park (no real dock)")
spec("Paul Revere Park", "dock", 42.3712, -71.0640, 1, ["Paul Revere Park"])
spec("Navy Yard (dock)", "dock", 42.3727, -71.0532, 1, ["Navy Yard", "Charlestown Navy Yard"], "Navy Yard Pier 4 ferry dock")

# --- Mystic River
spec("Menino", "dock", 42.3735, -71.0590, 1, ["Menino Park", "Thomas M. Menino Park"], "Menino Park, Charlestown Navy Yard")
spec("Little Mystic", "dock", 42.3805, -71.0560, 1.5, ["Little Mystic Channel"], "Little Mystic Channel")
spec("Medford St", "street", 42.3830, -71.0625, 1.5, ["Medford Street"],
     "Medford St, Charlestown: dock placed by hand on the Little Mystic side near Medford St and Terminal St")
spec("Alford St", "dock", 42.3890, -71.0700, 1.2, ["Alford Street Bridge", "Alford Street"],
     "Alford Street Bridge (Charlestown to Everett)")
spec("Assembly (dock)", "hand", 42.3955, -71.0790, 1, None,
     "Placed by hand on the Mystic riverfront at Assembly Row, about 300 m from the station")
spec("Encore (dock)", "hand", 42.3938, -71.0688, 1, None,
     "Placed by hand at the Encore Boston Harbor harborwalk on the Mystic, about 200 m from the station point")
spec("Stadium (dock)", "hand", 42.3880, -71.0650, 1, None,
     "Placed by hand on the Mystic shore of the former Mystic power plant site in Everett, next to the station")
spec("Admirals Hill", "dock", 42.3915, -71.0455, 1.5, ["Admirals Hill", "Admiral's Hill"], "Admirals Hill, Chelsea")
spec("Pearl St", "street", 42.3890, -71.0400, 1.5, ["Pearl Street"],
     "Not found as a waterfront place: placed by hand on the Chelsea bank of the Mystic east of Admirals Hill, "
     "near the Tobin Bridge")

# --- Chelsea Creek
spec("Quigley", "hand", 42.3880, -71.0340, 1, None,
     "Only an inland Quigley Park was found (Essex St, Chelsea): placed by hand on the Chelsea bank of Chelsea Creek "
     "at Marginal St, west of the Chelsea Street Bridge")
spec("Chelsea St", "dock", 42.3866, -71.0228, 1.2, ["Chelsea Street Bridge"], "Chelsea Street Bridge, Chelsea bank")
spec("Eastern Ave", "street", 42.3930, -71.0165, 1.5, ["Eastern Avenue"],
     "Eastern Ave, Chelsea: dock placed by hand on the upper Chelsea Creek near Eastern Ave")
spec("Suffolk Downs (dock)", "hand", 42.3895, -70.9955, 1, None,
     "Placed by hand on Belle Isle Inlet beside Suffolk Downs station; the North Shore boats come up the inlet. "
     "The Chelsea Creek loop also lists it")
spec("Addison St", "street", 42.3843, -71.0168, 1.5, ["Addison Street"],
     "Addison St, East Boston: dock placed by hand on the East Boston bank of Chelsea Creek near Addison St")
spec("Condor St", "dock", 42.3836, -71.0288, 1, ["Condor Street Urban Wild", "Condor Street"],
     "Condor Street Urban Wild on Chelsea Creek")
spec("Boston Bay", "hand", 42.3830, -71.0370, 1, None,
     "Not found as a place: placed by hand on the East Boston bank of Chelsea Creek west of Condor St, near the "
     "Meridian St bridge")

# --- Harbor West, East Boston, Seaport
spec("Langone Ferryport", "st", 42.3682, -71.0547, 0.8, ["Langone Park"],
     "Invented NERTA hub at Langone Park, North End (a real waterfront park)")
spec("Langone Ferryport (dock)", "dock", 42.3683, -71.0543, 0.8, ["Langone Park"],
     "Same spot as the station: the ferry hub is at the Langone Park waterfront")
spec("Battery Wharf", "dock", 42.3670, -71.0505, 0.8, ["Battery Wharf"])
spec("Sargent's Wharf", "dock", 42.3643, -71.0503, 0.8, ["Sargent's Wharf", "Sargents Wharf"])
spec("Long Wharf", "dock", 42.3600, -71.0500, 0.6, ["Long Wharf"])
spec("Central Wharf", "dock", 42.3591, -71.0494, 0.6, ["Central Wharf", "New England Aquarium"],
     "Central Wharf (the New England Aquarium's wharf)")
spec("Rowes Wharf", "dock", 42.3566, -71.0503, 0.6, ["Rowes Wharf"])
spec("Dorchester Ave", "street", 42.3510, -71.0553, 0.8, ["Dorchester Avenue"],
     "Dorchester Ave: dock placed by hand on Fort Point Channel by South Station, where Dorchester Ave runs along the water")
spec("White St", "street", 42.3828, -71.0375, 1.2, ["White Street"],
     "White St, East Boston: dock placed by hand where Eagle Hill meets the harbor at the mouth of Chelsea Creek")
spec("Bennington St", "street", 42.3725, -71.0415, 1.2, ["Bennington Street"],
     "Bennington St starts at Central Sq, East Boston: dock placed by hand on the inner harbor below Central Sq "
     "(by Lewis Mall)")
spec("Piers Park", "dock", 42.3640, -71.0378, 1, ["Piers Park"])
spec("Porzio", "dock", 42.3605, -71.0315, 1, ["Porzio Park", "Joseph Porzio Memorial Park"], "Porzio Park, Jeffries Point")
spec("Martins Park", "dock", 42.3513, -71.0497, 0.8, ["Martin's Park", "Martins Park"], "Martin's Park, Fort Point Channel")
spec("Fan Pier", "dock", 42.3540, -71.0435, 0.8, ["Fan Pier"])
spec("Seaport (dock)", "hand", 42.3497, -71.0393, 1, None,
     "Placed by hand at Commonwealth Pier (Seaport World Trade Center), between Fan Pier and the Pavilion; "
     "the station point is about 500 m inland")
spec("Pavilion", "dock", 42.3478, -71.0362, 1, ["Leader Bank Pavilion", "Pavilion"], "Leader Bank Pavilion")

# --- Harbor Islands
spec("Long Island", "island", 42.3270, -70.9620, 3, ["Long Island"])
spec("Georges Island", "island", 42.3195, -70.9300, 2, ["Georges Island"])
spec("Spectacle Island", "island", 42.3260, -70.9860, 2, ["Spectacle Island"])
spec("Deer Island", "island", 42.3500, -70.9570, 2.5, ["Deer Island"])

# --- South Boston, Dorchester, Quincy Bay, Fore River
spec("First St", "street", 42.3420, -71.0325, 1.5, ["East First Street"],
     "E First St, South Boston: dock placed by hand on the Reserved Channel near the east end of First St")
spec("Castle Island", "dock", 42.3380, -71.0122, 1.5, ["Castle Island"])
spec("M St", "dock", 42.3330, -71.0310, 1, ["M Street Beach"], "M Street Beach")
spec("Carson Beach", "dock", 42.3255, -71.0420, 1.5, ["Carson Beach"])
spec("Dorchester Shores", "dock", 42.3080, -71.0450, 3, ["Dorchester Shores Reservation", "Malibu Beach"],
     "Dorchester Shores Reservation (Savin Hill, Malibu and Tenean beaches)")
spec("Old Harbor", "dock", 42.3215, -71.0420, 2, ["Old Harbor"], "Old Harbor, Dorchester")
spec("UMass Boston", "hand", 42.3170, -71.0330, 1, ["University of Massachusetts Boston"],
     "Placed by hand at Fallon Pier beside the JFK Library on Columbia Point, the old 'Columbia Point' dock "
     "(research/ferry-network-audit.md); the campus center is about 500 m inland")
spec("Fox Point", "dock", 42.3075, -71.0385, 1.5, ["Fox Point"], "Fox Point, Savin Hill Cove (UMass Boston marine dock)")
spec("Finigan", "dock", 42.2918, -71.0440, 1.5, ["Joseph Finnegan Park", "Finnegan Park"],
     "Probably Senator Joseph Finnegan Park, Port Norfolk (Max's spelling kept)")
spec("Squantum Point", "dock", 42.2975, -71.0275, 1.5, ["Squantum Point", "Squantum Point Park", "Quincy"],
     "Marina Bay / Squantum Point ferry dock")
spec("Nickerson", "dock", 42.2930, -71.0120, 1.5, ["Nickerson Beach"], "Nickerson Beach, Squantum")
spec("Thompson Island", "island", 42.3150, -71.0100, 2, ["Thompson Island"])
spec("Moon Island", "island", 42.3060, -70.9990, 2, ["Moon Island"])
spec("Squantum", "dock", 42.2960, -71.0140, 2, ["Squantum"])
spec("Wollaston Beach", "dock", 42.2720, -71.0230, 2, ["Wollaston Beach"])
spec("Hough's Neck", "dock", 42.2640, -70.9620, 2, ["Houghs Neck", "Hough's Neck"])
spec("Nut Island", "dock", 42.2800, -70.9530, 1.5, ["Nut Island"])
spec("Bay Pointe", "dock", 42.2470, -70.9880, 2, ["Bay Pointe Marina", "MarineMax Boston"], "Bay Pointe Marina, Quincy")
spec("King's Cove", "dock", 42.2470, -70.9650, 2, ["Kings Cove", "King's Cove"], "King's Cove, North Weymouth")
spec("Wessagusset", "dock", 42.2535, -70.9450, 2, ["Wessagusset Beach", "Wessagusset"])
spec("Hingham (dock)", "dock", 42.2530, -70.9200, 1.5, ["Hingham", "Hingham Shipyard"], "Hingham Shipyard ferry terminal")
spec("Nantasket", "dock", 42.2730, -70.8620, 2.5, ["Nantasket Pier", "Nantasket Beach", "Nantasket"])
spec("Hull", "dock", 42.3030, -70.9200, 2, ["Hull", "Pemberton Point"], "Hull ferry dock, Pemberton Point")

# --- North Shore Express
spec("Winthrop Landing", "dock", 42.3700, -70.9770, 1.5, ["Winthrop", "Winthrop Landing"], "Winthrop ferry landing")
spec("Winthrop Beach", "dock", 42.3745, -70.9690, 1.5, ["Winthrop Beach"])
spec("Highlands Beach", "hand", 42.3870, -70.9700, 1.5, ["Winthrop Highlands"],
     "Winthrop Highlands (Homes.com guide) has no mapped 'Highlands Beach': placed by hand on the Winthrop Highlands "
     "shore north of Winthrop Beach")
spec("Revere Beach (dock)", "hand", 42.4083, -70.9897, 1, None,
     "Placed by hand on Revere Beach opposite Revere Beach station, about 250 m east")
spec("Beachmont (dock)", "hand", 42.3955, -70.9860, 1, None,
     "Placed by hand on the Short Beach shore east of Beachmont station")
spec("Wonderland (dock)", "hand", 42.4150, -70.9875, 1, None,
     "Placed by hand at the north end of Revere Beach, east of Wonderland station")
spec("Lynn Harbor", "hand", 42.4585, -70.9525, 1, None,
     "NERTA Blue Line stop at Lynn Harbor: the geojson point was the middle of the harbor (water), so placed by hand "
     "on the Lynnway at Blossom St, beside the ferry pier")
spec("Lynn Harbor (dock)", "dock", 42.4590, -70.9545, 1.5, ["Blossom Street Pier", "Lynn"], "Lynn ferry at Blossom St Pier")
spec("Nahant Harbor", "dock", 42.4255, -70.9300, 2, ["Nahant Harbor"])
spec("Swampscott (dock)", "hand", 42.4700, -70.9150, 1.5, ["Swampscott Fish House"],
     "Placed by hand at the Swampscott town pier (Fish House) on Humphrey St, about 1.3 km from the station")
spec("Clifton (dock)", "hand", 42.4877, -70.8805, 1, None,
     "Placed by hand on the Clifton shore of Marblehead at Preston Beach, about 700 m from the station")
spec("Marblehead (dock)", "hand", 42.5040, -70.8490, 1, ["Marblehead Harbor"],
     "Placed by hand at the State St town landing on Marblehead Harbor")
spec("Salem Wharf", "dock", 42.5215, -70.8835, 1.5, ["Salem Wharf", "Salem Ferry", "Salem"], "Salem ferry, Blaney St")
spec("Beverly (dock)", "dock", 42.5410, -70.8780, 1.5, ["Glover Wharf"], "Glover Wharf, Beverly")
spec("Prides Crossing", "hand", 42.5575, -70.8320, 1.5, ["Prides Crossing"],
     "Real village with a closed commuter stop; dock placed by hand on the shore below Prides Crossing")
spec("Beverly Farms (dock)", "hand", 42.5585, -70.8080, 1.5, ["West Beach"],
     "Placed by hand at West Beach, Beverly Farms, about 450 m from the station")
spec("Manchester-by-the-Sea", "dock", 42.5745, -70.7685, 1.5, ["Manchester Harbor", "Manchester-by-the-Sea"],
     "Manchester Harbor town wharf")
spec("Magnolia", "dock", 42.5770, -70.7210, 1.5, ["Magnolia"])
spec("Gloucester (dock)", "hand", 42.6105, -70.6625, 1.5, ["Gloucester Harbor"],
     "Placed by hand on the downtown Gloucester waterfront (Harbor Loop), about 800 m from the station")
spec("Brier Neck", "dock", 42.6050, -70.6340, 1.5, ["Brier Neck"])
spec("Rockport (dock)", "hand", 42.6585, -70.6155, 1, ["Rockport Harbor"],
     "Placed by hand at T Wharf on Rockport Harbor, about 900 m from the station")
spec("Annisquam", "dock", 42.6550, -70.6770, 2, ["Annisquam"])
spec("Crane Beach", "dock", 42.6840, -70.7660, 2.5, ["Crane Beach"])
spec("Ipswich (dock)", "hand", 42.6795, -70.8262, 1.5, ["Ipswich Town Wharf"],
     "Placed by hand at the Ipswich Town Wharf on the Ipswich River, about 1.2 km from the station")
spec("Plum Island South", "hand", 42.6960, -70.7800, 2, ["Sandy Point"],
     "Invented dock: placed by hand at the south end of Plum Island near Sandy Point")
spec("Plum Island Central", "hand", 42.7500, -70.7990, 2, ["Plum Island"],
     "Invented dock: placed by hand at mid-island on the Plum Island River side")
spec("Plum Island North", "hand", 42.8075, -70.8170, 2, ["Plum Island"],
     "Invented dock: placed by hand near the Plum Island bridge at the north end")
spec("Newburyport (dock)", "hand", 42.8128, -70.8705, 1.5, ["Newburyport Waterfront Park"],
     "Placed by hand at the Newburyport waterfront on the Merrimack, about 1.7 km from the station")
spec("Salisbury", "hand", 42.8195, -70.8560, 2, ["Salisbury"],
     "Placed by hand on the Salisbury bank of the Merrimack opposite Newburyport (the town center is inland)")

# --- South Shore Express, the Cape, Buzzards Bay
spec("Quincy", "hand", 42.2452, -70.9965, 1.5, ["Town River"],
     "line_audit.md: Max's invented Town River dock. Placed by hand on the Town River near Quincy Center")
spec("Quincy Point", "dock", 42.2445, -70.9690, 2, ["Fore River Shipyard", "Quincy Point"],
     "Former Quincy ferry at the Fore River Shipyard (1996 to 2013)")
spec("Minot (Scituate)", "dock", 42.2360, -70.7680, 2.5, ["Minot"], "Minot, North Scituate")
spec("Mill Wharf", "dock", 42.1990, -70.7245, 1.5, ["Mill Wharf"], "Mill Wharf, Scituate Harbor")
spec("Humarock", "dock", 42.1430, -70.6920, 2, ["Humarock"])
spec("Brant Rock / Green Harbor", "dock", 42.0800, -70.6480, 2.5, ["Green Harbor", "Brant Rock"],
     "Green Harbor and Brant Rock, Marshfield")
spec("Duxbury", "dock", 42.0505, -70.6590, 2.5, ["Powder Point Bridge", "Duxbury"], "Powder Point Footbridge, Duxbury")
spec("Plymouth Rock", "dock", 41.9583, -70.6623, 1, ["Plymouth Rock"])
spec("Sandwich Boardwalk", "dock", 41.7720, -70.4930, 1.5, ["Sandwich Boardwalk"])
spec("N. Barnstable / Sandy Neck", "dock", 41.7350, -70.3850, 3, ["Sandy Neck"], "Sandy Neck, Barnstable")
spec("Sesuit", "dock", 41.7520, -70.1550, 2, ["Sesuit Harbor", "Sesuit"], "Sesuit Harbor, Dennis")
spec("Namskaket", "dock", 41.7930, -70.0150, 2.5, ["Namskaket", "Namskaket Creek"])
spec("Thumpertown", "dock", 41.8385, -70.0010, 2, ["Thumpertown Beach", "Thumpertown"])
spec("Wellfleet Pier", "dock", 41.9300, -70.0270, 1.5, ["Wellfleet Town Pier", "Wellfleet Pier", "Wellfleet Harbor"])
spec("Provincetown", "dock", 42.0500, -70.1830, 2, ["MacMillan Pier", "Provincetown"], "MacMillan Pier, Provincetown")
spec("Race Point", "dock", 42.0760, -70.2350, 3, ["Race Point", "Race Point Beach"], "Race Point (label: Race Point / P-Town Airport)")
spec("Marconi Beach", "dock", 41.8930, -69.9630, 2, ["Marconi Beach"])
spec("Coast Guard Beach", "dock", 41.8410, -69.9460, 2, ["Coast Guard Beach"])
spec("Nauset Beach", "dock", 41.7880, -69.9370, 3, ["Nauset Beach"])
spec("Chatham", "dock", 41.6880, -69.9510, 2.5, ["Chatham Fish Pier", "Chatham"], "Chatham Fish Pier")
spec("Harwich Point", "dock", 41.6660, -70.0700, 3, ["Harwich Port", "Wychmere Harbor"],
     "No 'Harwich Point' found; taken as Harwich Port")
spec("Dennis Port", "dock", 41.6590, -70.1290, 2, ["Dennis Port"])
spec("Shad Hole Rd", "street", 41.6560, -70.1475, 1.5, ["Shad Hole Road"],
     "Shad Hole Rd, Dennis Port: dock placed by hand where it reaches Nantucket Sound")
spec("Old Wharf", "street", 41.6555, -70.1560, 1.5, ["Old Wharf Road"],
     "Old Wharf Rd, Dennis Port: dock placed by hand on the Nantucket Sound shore at its foot")
spec("West Dennis", "dock", 41.6560, -70.1700, 2.5, ["West Dennis", "West Dennis Beach"])
spec("Yarmouth", "hand", 41.6530, -70.1855, 2, ["South Yarmouth"],
     "Yarmouth's GNIS point is Yarmouth Port on the north shore; this stop is on the Nantucket Sound side where the "
     "Bass River loop starts, so it is placed by hand at the mouth of Bass River")
spec("South Yarmouth", "dock", 41.6670, -70.1850, 2, ["South Yarmouth"])
spec("Wilbur", "hand", 41.6740, -70.1800, 2, ["Wilbur Park"],
     "Not identified as a place: placed by hand on Bass River between South Yarmouth and the Route 28 bridge")
spec("Bass River / Rte 28", "hand", 41.6705, -70.1830, 1.5, ["Bass River Bridge"],
     "Placed by hand on Bass River at the Route 28 bridge")
spec("Wrinkle Point", "dock", 41.6630, -70.1780, 2, ["Wrinkle Point"])
spec("West Yarmouth", "dock", 41.6490, -70.2450, 2.5, ["West Yarmouth"])
spec("Hyannis", "dock", 41.6520, -70.2790, 2, ["Hyannis", "Hyannis Ferry Terminal"], "Hyannis ferry terminal")
spec("Hyannisport", "dock", 41.6340, -70.3040, 2, ["Hyannis Port", "Hyannisport"])
spec("Osterville", "dock", 41.6270, -70.3870, 2.5, ["Osterville"])
spec("Popponesset", "dock", 41.5670, -70.4580, 2.5, ["Popponesset", "Popponesset Beach"])
spec("Acapesket", "dock", 41.5560, -70.5630, 2.5, ["Acapesket"])
spec("Falmouth", "dock", 41.5440, -70.6090, 2.5, ["Falmouth Inner Harbor", "Falmouth"], "Falmouth Inner Harbor")
spec("Woods Hole", "dock", 41.5230, -70.6720, 1.5, ["Woods Hole"], "Woods Hole ferry terminal")
spec("New Bedford (dock)", "dock", 41.6340, -70.9215, 1.5, ["New Bedford", "State Pier"], "New Bedford State Pier ferry dock")
spec("South Dartmouth", "dock", 41.5870, -70.9450, 2, ["South Dartmouth", "Padanaram"], "Padanaram, South Dartmouth")
spec("Newport", "dock", 41.4875, -71.3170, 2, ["Newport", "Perrotti Park"], "Newport, RI ferry landing")
spec("Fall River", "dock", 41.7060, -71.1630, 2, ["Fall River", "Battleship Cove"], "Fall River waterfront")
spec("Buzzards Bay", "dock", 41.7450, -70.6170, 2, ["Buzzards Bay"], "Buzzards Bay village at the canal's west end")
spec("West Falmouth", "dock", 41.6040, -70.6430, 2, ["West Falmouth Harbor", "West Falmouth"])
spec("New Silver Beach", "dock", 41.6220, -70.6330, 2, ["New Silver Beach"])
spec("Pocasset", "dock", 41.6850, -70.6250, 2.5, ["Pocasset"])
spec("Onset", "dock", 41.7420, -70.6580, 2, ["Onset"])
spec("Wareham", "dock", 41.7600, -70.7180, 2.5, ["Wareham"])
spec("Marion", "dock", 41.7020, -70.7620, 2, ["Marion"])
spec("Mattapoisett", "dock", 41.6570, -70.8130, 2, ["Mattapoisett"])
spec("West Island", "dock", 41.5930, -70.8300, 2.5, ["West Island"])
spec("Fairhaven", "dock", 41.6360, -70.9030, 2, ["Fairhaven"])
spec("Cuttyhunk", "island", 41.4250, -70.9290, 3, ["Cuttyhunk", "Cuttyhunk Island"])
spec("Carson Beach", "dock", 42.3255, -71.0420, 1.5, ["Carson Beach"])

# --- Nantucket and Martha's Vineyard
spec("Wauwinet", "dock", 41.3320, -69.9990, 2.5, ["Wauwinet"])
spec("Siasconset", "dock", 41.2630, -69.9620, 2, ["Siasconset"])
spec("Nobadeer", "dock", 41.2480, -70.0400, 3, ["Nobadeer Beach", "Nobadeer"], "Nobadeer Beach by Nantucket Memorial Airport")
spec("South Shore", "hand", 41.2425, -70.1000, 2, None,
     "Nantucket's south shore, no single place: placed by hand at Surfside Beach between Nobadeer and Cisco. "
     "Not the South Shore of Massachusetts")
spec("Cisco", "dock", 41.2510, -70.1460, 2.5, ["Cisco Beach", "Cisco"])
spec("Smith Point", "dock", 41.2740, -70.2380, 3, ["Smith Point", "Smiths Point"])
spec("Tuckernuck Is.", "island", 41.3000, -70.2650, 3, ["Tuckernuck Island"])
spec("Brant Point", "dock", 41.2900, -70.0910, 1.5, ["Brant Point"])
spec("Nantucket Downtown", "dock", 41.2860, -70.0950, 1.5, ["Steamboat Wharf", "Nantucket", "Straight Wharf"],
     "Nantucket ferry wharves, downtown")
spec("Coskata", "dock", 41.3600, -70.0250, 4, ["Coskata", "Coskata Pond"])
spec("Oak Bluffs", "dock", 41.4580, -70.5560, 1.5, ["Oak Bluffs"], "Oak Bluffs ferry terminal")
spec("Edgartown", "dock", 41.3890, -70.5130, 1.5, ["Edgartown"])
spec("Chappaquiddick", "dock", 41.3880, -70.5060, 2, ["Chappaquiddick Ferry", "Chappy Ferry", "Chappaquiddick"],
     "Chappy ferry landing")
spec("Katama Beach", "dock", 41.3520, -70.5150, 3, ["Katama Beach", "Katama", "South Beach"])
spec("MVY Connection", "hand", 41.3560, -70.6300, 2, ["Scrubby Neck"],
     "Label 'MVY Connection via Scrubby Neck': placed by hand on the south shore at Scrubby Neck, West Tisbury, the "
     "closest shore to Martha's Vineyard Airport")
spec("Chilmark", "dock", 41.3540, -70.7680, 2.5, ["Menemsha", "Menemsha Harbor", "Chilmark"], "Menemsha harbor, Chilmark")
spec("Aquinnah", "dock", 41.3450, -70.8000, 4, ["Aquinnah"])
spec("Noman's Land", "island", 41.2560, -70.8180, 3, ["Nomans Land", "Noman's Land", "No Mans Land"])
spec("Vineyard Haven", "dock", 41.4560, -70.6000, 1.5, ["Vineyard Haven"], "Vineyard Haven ferry terminal")
spec("Lagoon Pond", "dock", 41.4440, -70.5850, 2, ["Lagoon Pond"])


# ---------------------------------------------------------------- matching
PRIORITY = ["MBTA API", "OpenStreetMap", "USGS GNIS", "Wikidata"]


def gather(kind, hint, r_km, queries, mbta, osm):
    cands = {s: [] for s in PRIORITY}
    rm = r_km * 1000
    keys = {norm(q) for q in queries}
    for k in keys:
        for la, lo, lab, vt in mbta.get(k, []):
            if (vt == 4) != (kind != "st"):  # docks use MBTA ferry stops only; stations never do
                continue
            if dist((la, lo), hint) <= rm:
                cands["MBTA API"].append((la, lo, lab))
        for la, lo, lab in osm.get(k, []):
            if dist((la, lo), hint) <= rm:
                cands["OpenStreetMap"].append((la, lo, lab))
    for q in queries:
        if kind != "st" or not cands["OpenStreetMap"]:
            cands["OpenStreetMap"] += [c for c in nominatim(q, hint, r_km) if dist(c[:2], hint) <= rm]
        cands["USGS GNIS"] += [c for c in gnis(q) if dist(c[:2], hint) <= rm]
        cands["Wikidata"] += [c for c in wikidata(q) if dist(c[:2], hint) <= rm]
    for s in cands:  # dedupe, nearest to hint first
        seen, out = set(), []
        for c in sorted(cands[s], key=lambda c: dist(c[:2], hint)):
            key = (round(c[0], 5), round(c[1], 5))
            if key not in seen:
                seen.add(key)
                out.append(c)
        cands[s] = out
    return cands


def copies(a, b, sa, sb):
    return {sa, sb} == {"USGS GNIS", "Wikidata"} and dist(a, b) < 15


def decide(cands, tol, need=None):
    """Best agreeing pair across two independent sources (one of them `need`, if given)."""
    best = None
    for i, sa in enumerate(PRIORITY):
        for sb in PRIORITY[i + 1:]:
            if need and need not in (sa, sb):
                continue
            for a in cands[sa]:
                for b in cands[sb]:
                    d = dist(a[:2], b[:2])
                    if d <= tol and not copies(a[:2], b[:2], sa, sb) and (best is None or d < best[0]):
                        best = (d, sa, a, sb, b)
    return best


def fmt(src, c):
    return f"{src}: {c[2]}" if c[2] else src


def describe_others(cands, at, used):
    bits = []
    for s in PRIORITY:
        if s in used or not cands[s]:
            continue
        c = min(cands[s], key=lambda c: dist(c[:2], at))
        bits.append(f"{s} {round(dist(c[:2], at))} m away")
    return bits


def entry(lat, lon, sources, verified, note):
    return {"lat": round(lat, 6), "lon": round(lon, 6), "sources": sources, "verified": verified, "note": note.strip()}


def resolve(name, sp, mbta, osm, prior=None):
    kind, la, lo, r, queries, base = sp
    hint = (la, lo)
    if kind == "hand":
        return entry(la, lo, ["placed by hand"], False, base), None
    cands = gather(kind, hint, r, queries, mbta, osm)
    if prior:  # an existing one-source point from the geojson
        cands[prior[0]].insert(0, (prior[1], prior[2], "stations_real.geojson"))
    tol = ST_TOL if kind == "st" else PLACE_TOL
    # A dock the MBTA serves is anchored on the MBTA ferry stop, not on the town it is named for.
    # The same goes for a station: anchor on the MBTA stop, not on the town it is named for.
    need = "MBTA API" if cands["MBTA API"] else None
    best = decide(cands, tol, need)
    pre = (base + ". ") if base else ""
    if best:
        d, sa, a, sb, b = best
        e = entry(a[0], a[1], [sa, sb], True,
                  pre + f"{sa} and {sb} agree within {round(d)} m ({a[2]}; {b[2]})")
        oth = describe_others(cands, a[:2], {sa, sb})
        if oth:
            e["note"] += ". Also " + ", ".join(oth)
    else:
        single = None
        for s in ([need] if need else PRIORITY):
            if cands[s]:
                single = (s, cands[s][0])
                break
        if single is None:
            return entry(la, lo, ["placed by hand"], False,
                         pre + "No source found: placed by hand"), None
        s, c = single
        oth = describe_others(cands, c[:2], {s})
        e = entry(c[0], c[1], [s], False,
                  pre + f"One source ({c[2]})" + ((". Others disagree: " + ", ".join(oth)) if oth else ". No second source found"))
    if kind == "street":  # street confirmed (or not); dock goes by hand at the street's waterfront end
        found = e["sources"] if e["sources"] != ["placed by hand"] else []
        conf = (" (street found in " + " and ".join(found) + ")") if found else " (street not confirmed)"
        pt = street_end(queries, hint, r)
        if pt:
            (sla, slo), gap = pt
            return entry(sla, slo, ["placed by hand"], False,
                         base + conf + f". Set on the mapped shoreline {gap} m from the street's nearest point "
                         "(OSM street and shoreline geometry)"), None
        return entry(la, lo, ["placed by hand"], False, base + conf), (la, lo, WATER_R)
    if kind in ("dock", "island"):
        return e, (e["lat"], e["lon"], ISLAND_WATER_R if kind == "island" else WATER_R)
    return e, None


def main():
    names = json.loads(NAMES.read_text(encoding="utf-8"))
    names += [e for e in EXTRA if e["name"] not in {n["name"] for n in names}]
    geo = {f["properties"]["name"]: f for f in json.loads(GEO.read_text(encoding="utf-8"))["features"]}
    mbta, osm = mbta_index(), overpass_index()

    keys = []
    for e in names:
        n, modes = e["name"], e["modes"]
        ferry = any(m.startswith("ferry:") for m in modes)
        other = any(not m.startswith("ferry:") for m in modes)
        keys.append((n, "station" if other else "dock"))
        if ferry and other:
            keys.append((n + " (dock)", "dock"))

    nospec = [k for k, _ in keys if k not in S and not (k in geo)]
    if nospec:
        raise SystemExit(f"no spec for {nospec}")
    out, water_q = {}, {}
    for key, role in keys:
        g = geo.get(key)
        if g and g["properties"]["verified"]:
            p, (lo, la) = g["properties"], g["geometry"]["coordinates"]
            out[key] = entry(la, lo, p["sources"], True, p["note"] + " (from stations_real.geojson)")
            continue
        sp = S.get(key)
        if g and not sp:
            p, (lo, la) = g["properties"], g["geometry"]["coordinates"]
            src = {"Nominatim (OSM)": "OpenStreetMap"}.get(p["sources"][0], p["sources"][0])
            if src == "placed by hand":
                q = [key, re.sub(r"\bSq\b", "Square", re.sub(r"\bCtr\b", "Center", key))]
                res, _ = resolve(key, ("st", la, lo, 0.6, list(dict.fromkeys(q)), ""), mbta, osm)
                if res["verified"] and dist((res["lat"], res["lon"]), (la, lo)) <= 400:
                    out[key] = res
                    out[key]["note"] = f"Was placed by hand ({p['note']}); now " + res["note"]
                else:
                    out[key] = entry(la, lo, ["placed by hand"], False, p["note"] + " (from stations_real.geojson)")
                continue
            q = [key, f"{key} station", re.sub(r"\bSq\b", "Square", re.sub(r"\bCtr\b", "Center", key))]
            res, _ = resolve(key, ("st", la, lo, 1.5, list(dict.fromkeys(q)), ""), mbta, osm, prior=(src, la, lo))
            out[key] = res
            continue
        if not sp:
            if key.endswith(" (dock)"):
                raise SystemExit(f"no dock spec for {key}")
            raise SystemExit(f"no spec for {key}")
        res, wq = resolve(key, sp, mbta, osm)
        out[key] = res
        if wq:
            water_q[key] = wq
    save_cache()

    # Docks must touch water. A dry point is moved to the nearest mapped shoreline (OSM) and loses "verified".
    for k, role in keys:
        if role == "dock" and k not in water_q and "Set on the mapped shoreline" not in out[k]["note"]:
            water_q[k] = (out[k]["lat"], out[k]["lon"], WATER_R)
    wet = near_water(list(water_q.values()))
    save_cache()
    for k, wq in water_q.items():
        if wet[wq]:
            continue
        e = out[k]
        sn = snap(e["lat"], e["lon"])
        if not sn:  # no shoreline geometry: fall back to the hand-set waterfront hint
            hint = (S[k][1], S[k][2])
            hk = f"water:{hint[0]:.5f},{hint[1]:.5f},{WATER_R}"
            wet_hint = _cache.get(hk)
            far = round(dist((e["lat"], e["lon"]), hint))
            if e["sources"] != ["placed by hand"]:
                e["note"] = (f"Sourced point ({', '.join(e['sources'])}{', verified' if e['verified'] else ''}) at "
                             f"{e['lat']}, {e['lon']} is over {wq[2]} m from mapped water, so the dock is placed by hand "
                             f"{far} m away at the waterfront. Sourced: " + e["note"])
            if far > 1:
                e["lat"], e["lon"] = hint
            e["sources"], e["verified"] = ["placed by hand"], False
            if wet_hint is not True:
                e["note"] += (". CHECK: hand point not confirmed within 200 m of mapped water" if wet_hint is False
                              else ". Hand point not checked against mapped water")
            continue
        (sla, slo), moved = sn
        was = ", ".join(e["sources"])
        if e["sources"] == ["placed by hand"]:
            e["note"] += f". Moved {moved} m from the hand point to the nearest mapped shoreline (OSM)"
        else:
            e["note"] = (f"Sourced point ({was}{', verified' if e['verified'] else ''}) at {e['lat']}, {e['lon']} is "
                         f"over {wq[2]} m from mapped water, so the dock is moved {moved} m to the nearest mapped "
                         "shoreline (OSM) and placed by hand there. Sourced: " + e["note"])
        e["lat"], e["lon"] = round(sla, 6), round(slo, 6)
        e["sources"], e["verified"] = ["placed by hand"], False
    save_cache()

    for k, e in out.items():
        if "(dock)" in k:
            base = k[:-7]
            if base in out:
                d = round(dist((e["lat"], e["lon"]), (out[base]["lat"], out[base]["lon"])))
                e["note"] += f". Dock for '{base}', {d} m from the station entry"

    missing = [k for k, _ in keys if k not in out]
    assert not missing, missing
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    v = sum(e["verified"] for e in out.values())
    h = sum(e["sources"] == ["placed by hand"] for e in out.values())
    print(f"{len(out)} entries ({len(names)} names): {v} verified, {len(out) - v - h} one source, {h} placed by hand")


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        save_cache()
