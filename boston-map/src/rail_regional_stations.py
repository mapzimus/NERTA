"""Real positions for every station on the commuter rail poster, for the regional rail map (data/rail_regional).

Max's data rule: a position is called accurate only when two named sources agree. Here "agree" means the two points are
under 150 m apart. A station with one source is labeled unverified, and one placed only from a town point is approx.

Sources, in order of use
  1. MBTA V3 API stops, from data/mbta_stops.gpkg (parent stations, fetched by fetch_mbta.py).
  2. OpenStreetMap stations from Overpass, matched by name. Cached in data/rail_regional/osm_stations.json together with
     the OSM streets and old rail lines used to place sites that written sources describe (pass --refetch to rebuild).
  3. data/tram/stations_real.geojson: Boston Central and West Station, placed by hand on this map.
  4. research() below: stations that aren't MBTA stops today. Each lists its sources: Wikipedia, Wikidata and Wikimedia
     Commons, Sanborn fire insurance maps (Library of Congress, copies on Commons), town history pages, City of Salem slides.
Where MBTA and OSM disagree, the Wikipedia article's coordinates break the tie (WIKI_CHECK).

Writes data/rail_regional/stations.geojson and data/rail_regional/station_sources.md. Imports make_rail_poster.py only to
read the station list (read only).
Run: python rail_regional_stations.py [--refetch]
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import geopandas as gpd
from pyproj import Geod, Transformer
from shapely.geometry import LineString, Point, Polygon, mapping
from shapely.ops import nearest_points, unary_union

SRC = Path(__file__).resolve().parent
DATA = SRC.parent / "data"
OUT = DATA / "rail_regional"
CACHE = OUT / "osm_stations.json"
UA = "nerta-rail-regional-map"
AGREE = 150.0      # meters: two sources closer than this agree
FAR = 3000.0       # meters: an OSM station with the right name but farther than this is a different place
GEOD = Geod(ellps="WGS84")
TO_M = Transformer.from_crs(4326, 26986, always_xy=True)    # Massachusetts State Plane, meters
TO_LL = Transformer.from_crs(26986, 4326, always_xy=True)

# Poster names that differ from MBTA names
MBTA_NAME = {"Central Sq": "Lynn Interim", "David Ortiz": "Lansdowne", "Winchester": "Winchester Center",
             "Hingham": "West Hingham", "Church St": "Church Street", "Sullivan Sq": "Sullivan Square"}
# OSM names that differ from both
OSM_NAME = {"Back Bay": "Back Bay Station", "Anderson/Woburn": "Anderson Regional Transportation Center",
            "Beverly": "Beverly Depot", "Franklin": "Franklin/Dean", "TF Green Airport": "T. F. Green Airport"}
NAME_KEYS = ("name", "official_name", "alt_name", "old_name", "short_name")

# Wikipedia article coordinates (read November 7, 2026), the tie-breaker where MBTA and OSM are 150 m or more apart
WIKI_CHECK = {
    "South Station": ("South Station", 42.35194444, -71.05527778),
    "Littleton/Route 495": ("Littleton/Route 495 station", 42.52147, -71.50348),
    "North Wilmington": ("North Wilmington station", 42.57105, -71.16094),
    "Manchester": ("Manchester station (MBTA)", 42.574, -70.7691),
    "Wellesley Farms": ("Wellesley Farms station", 42.32319444, -71.27194444),
}
WEST_STATION_WIKI = (42.35478056, -71.12156111)   # Wikipedia: West Station (MBTA)

# ---------------------------------------------------------------------------------------------------------------
# OpenStreetMap (Overpass): stations, plus geometry around the researched sites
BBOX = (41.3, -72.0, 43.0, -70.5)
STATION_TAGS = ['["railway"~"^(station|halt)$"]', '["public_transport"="station"]', '["disused:railway"~"^(station|halt)$"]',
                '["abandoned:railway"~"^(station|halt)$"]', '["razed:railway"~"^(station|halt)$"]',
                '["demolished:railway"~"^(station|halt)$"]', '["removed:railway"~"^(station|halt)$"]',
                '["was:railway"~"^(station|halt)$"]', '["historic:railway"~"^(station|halt)$"]',
                '["railway:historic"~"^(station|halt)$"]', '["historic"="railway_station"]', '["building"="train_station"]',
                '["proposed:railway"~"^(station|halt)$"]', '["construction:railway"~"^(station|halt)$"]',
                '["railway"="proposed"]["proposed:railway"="station"]']
RAIL = 'way["railway"]{a};way["highway"~"^(cycleway|path|footway|track)$"]["name"]{a};'
SITES = {  # key: (lat, lon, radius m, Overpass parts with {a} for the around filter)
    "south_salem": (42.5076, -70.8981, 450, 'way["railway"]{a};way["highway"]["name"]{a};'),
    "north_easton": (42.0891, -71.0977, 700, RAIL + 'way["highway"]["name"~"Roche"]{a};nwr["name"~"Roche"]{a};'),
    "raynham_place": (41.9800, -71.0754, 900, RAIL + 'nwr["name"~"Raynham Park|Raynham-Taunton|Greyhound|Simulcast",i]{a};'),
    "taunton": (41.9044, -71.0822, 350, RAIL + 'nwr["building"]["name"]{a};nwr["historic"]{a};way["highway"]["name"~"Dean"]{a};'),
    "danvers": (42.5658, -70.9412, 250, RAIL + 'way["building"]{a};nwr["historic"]{a};'),
    "clifton": (42.4826, -70.8779, 450, RAIL + 'way["highway"]["name"~"Clifton"]{a};'),
    "marblehead": (42.5005, -70.8570, 600, RAIL + 'way["highway"]["name"~"^(Pleasant|School|Sewall) Street$"]{a};'
                                               'nwr["addr:street"="Pleasant Street"]["addr:housenumber"~"^(89|91|93)$"]{a};'
                                               'nwr["military"]{a};nwr["name"~"National Guard|Armory",i]{a};'),
    "hudson": (42.3934, -71.5686, 900, RAIL + 'nwr["historic"]{a};nwr["name"~"Depot|Station",i]{a};'),
    "marlborough": (42.3482, -71.5549, 700, RAIL + 'way["highway"]["name"~"^(Lincoln|Mechanic) Street$"]{a};'
                                                 'nwr["name"~"Depot|Station",i]{a};'),
    "peabody": (42.5272, -70.9290, 500, RAIL + 'nwr["place"]{a};'),
    "danversport": (42.5580, -70.9320, 1500, RAIL + 'nwr["place"]{a};'),
    "middleton": (42.5960, -71.0120, 1500, RAIL + 'nwr["place"]{a};'),
    "boston_central": (42.3594, -71.0520, 250, 'way["highway"]["name"~"^(Atlantic Avenue|State Street)$"]{a};'),
    "hudson_streets": (42.3915, -71.5650, 700, 'way["highway"]["name"~"^(Main|High|Maple|Broad|Loring|Cherry) Street$"]{a};'
                                               'way["highway"]["name"~"Loring"]{a};way["name"="Assabet River Rail Trail"]{a};'
                                               'way["railway"]{a};'),
    "peabody_streets": (42.5265, -70.9285, 450, 'way["highway"]["name"~"^(Central|Mill|Walnut|Foster|Main|Lowell|Railroad) '
                                                '(Street|Avenue)$"]{a};way["railway"]{a};nwr["place"]{a};'
                                                'nwr["name"~"Peabody Square"]{a};'),
    "danversport_streets": (42.5575, -70.9310, 500, 'way["highway"]["name"~"^(Water|Mill|Cheever|Clinton) (Street|Avenue)$"]{a};'
                                                    'way["railway"]{a};way["waterway"]["name"~"Crane"]{a};'),
}


def overpass(q):
    data = urllib.parse.urlencode({"data": q}).encode()
    for wait in (0, 45, 90, 120):
        time.sleep(wait)
        for url in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):
            try:
                req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=300) as r:
                    return json.load(r)
            except Exception as e:  # noqa: BLE001 (retry on any network error, then give up below)
                print("overpass:", url, e, file=sys.stderr)
    raise SystemExit("Overpass failed; try again later")


def keep_site_element(t):
    if any(k in t for k in ("railway", "place", "historic")) or "name" in t:
        return True
    return t.get("addr:street") == "Pleasant Street" and "addr:housenumber" in t


def refetch():
    s, w, n, e = BBOX
    bb = f"({s},{w},{n},{e})"
    q = "[out:json][timeout:240];(" + "".join(f"nwr{t}{bb};" for t in STATION_TAGS) + ");out center tags;"
    els = []
    for el in overpass(q)["elements"]:
        lat = el.get("lat", el.get("center", {}).get("lat"))
        lon = el.get("lon", el.get("center", {}).get("lon"))
        if lat is not None:
            els.append({"osm": f'{el["type"]}/{el["id"]}', "lat": lat, "lon": lon, "tags": el.get("tags", {})})
    sites = {}
    for key, (lat, lon, r, parts) in SITES.items():
        sq = f"[out:json][timeout:90];({parts.format(a=f'(around:{r},{lat},{lon})')});out tags geom;"
        kept = []
        for el in overpass(sq)["elements"]:
            if not keep_site_element(el.get("tags", {})):
                continue
            x = {"type": el["type"], "id": el["id"], "tags": el.get("tags", {})}
            if el["type"] == "node":
                x["lat"], x["lon"] = el["lat"], el["lon"]
            else:
                geo = el.get("geometry") or [g for m in el.get("members", []) for g in m.get("geometry", [])]
                x["geometry"] = [[round(g["lat"], 7), round(g["lon"], 7)] for g in geo if g]
            kept.append(x)
        sites[key] = {"center": [lat, lon], "radius": r, "query": sq, "elements": kept}
        time.sleep(8)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"query": q, "fetched": time.strftime("%Y-%m-%d"),
                                 "source": "OpenStreetMap contributors, via Overpass API (ODbL)", "elements": els,
                                 "sites": sites}, indent=0), encoding="utf-8")


# ---------------------------------------------------------------------------------------------------------------
# Geometry helpers. Points are (lat, lon).
def dist(a, b):
    return GEOD.inv(a[1], a[0], b[1], b[0])[2]


def to_ll(p):
    x, y = TO_LL.transform(p.x, p.y)
    return (round(y, 6), round(x, 6))


def mid(*pts):
    return (round(sum(p[0] for p in pts) / len(pts), 6), round(sum(p[1] for p in pts) / len(pts), 6))


class Sites:
    """OSM geometry around one researched site: find where two streets meet, or the nearest point on an old line."""

    def __init__(self, sites):
        self.sites = sites

    @staticmethod
    def geom(e):
        if e["type"] == "node":
            return Point(*TO_M.transform(e["lon"], e["lat"]))
        pts = [TO_M.transform(lon, lat) for lat, lon in e.get("geometry", [])]
        if len(pts) >= 4 and pts[0] == pts[-1] and "building" in e["tags"]:
            return Polygon(pts)
        return LineString(pts) if len(pts) > 1 else Point(pts[0])

    def pick(self, key, pred):
        g = [self.geom(e) for e in self.sites[key]["elements"] if pred(e)]
        if not g:
            raise SystemExit(f"OSM site {key}: nothing matched; rebuild the cache with --refetch")
        return unary_union(g)

    def crossing(self, key, pa, pb):
        p, q = nearest_points(self.pick(key, pa), self.pick(key, pb))
        return to_ll(Point((p.x + q.x) / 2, (p.y + q.y) / 2))

    def snap(self, key, pred, ll):
        x, y = TO_M.transform(ll[1], ll[0])
        return to_ll(nearest_points(self.pick(key, pred), Point(x, y))[0])

    def centroid(self, key, pred):
        return to_ll(self.pick(key, pred).centroid)


def named(*names):
    return lambda e: e["tags"].get("name") in names


def osm_id(*ids):
    return lambda e: e["id"] in ids


def rail_named(part):
    return lambda e: "railway" in e["tags"] and part in e["tags"].get("name", "")


def any_rail(e):
    return "railway" in e["tags"]


# ---------------------------------------------------------------------------------------------------------------
# Stations that aren't MBTA stops today. Each source is (short label, what it says, (lat, lon)); the first one is the
# position used. "check" is a third point that isn't counted as a source.
def research(S, osm_by_id):
    def osm_pt(i):
        e = osm_by_id[i]
        return (e["lat"], e["lon"])

    eastern = lambda e: e["tags"].get("name") == "Eastern Route" and e["tags"].get("railway") == "rail"  # noqa: E731
    marlborough_branch = (lambda e: e["tags"].get("name") == "Assabet River Rail Trail"
                          or (e["tags"].get("railway") == "abandoned" and "Central" not in e["tags"].get("name", "")))
    essex_line = lambda e: e["tags"].get("name") == "Middleton Rail Trail" and e["tags"].get("railway") == "abandoned"  # noqa: E731
    hud_main = S.crossing("hudson_streets", named("Main Street"), named("High Street"))
    ne_store = S.centroid("north_easton", named("Roche Bros."))
    danvers_photos = mid((42.565887, -70.941127), (42.565743, -70.941293), (42.565731, -70.941322))

    return {
        "Plymouth": dict(
            status="reopened", mbta_name="Plymouth", approx=False, note="closed 2021, at Cordage Park",
            sources=[("MBTA V3 API place-PB-0356", "MBTA still lists the stop after the 2021 closure", (41.981278, -70.690421)),
                     ("OSM node/7005396587", "tagged a disused station", osm_pt("node/7005396587")),
                     ("Wikipedia: Plymouth station (MBTA)", "article coordinates", (41.9812, -70.6903))]),
        "South Salem": dict(
            status="proposed", mbta_name=None, approx=False, note="City of Salem design at Ocean Ave West",
            sources=[("City of Salem slides 2025, placed with OSM",
                      "the January 28, 2025 community update puts the stop at Ocean Ave West, with side platforms and a "
                      "Jefferson Ave access option; OSM gives where Ocean Ave West meets the Eastern Route",
                      S.crossing("south_salem", named("Ocean Avenue West"), eastern)),
                     ("Wikipedia: South Salem station", "article coordinates, address Ocean Ave", (42.50762, -70.89806))]),
        "North Easton": dict(
            status="proposed", mbta_name=None, approx=False, note="South Coast Rail Phase 2, Roche Brothers Way",
            sources=[("Wikipedia: North Easton station (MBTA), rev. 1279156129",
                      "coordinates in the article's last version before it was cut to a redirect in March 2025; address "
                      "Roche Brothers Way", (42.089150, -71.097722)),
                     ("2013 Final EIS figure 3.2-22, placed with OSM",
                      "the figure (copy on Commons) shows an 800 ft platform on the old Stoughton Branch below the Roche "
                      "Bros. store, at the Easton/Stoughton line; OSM gives the old bed's nearest point to the store",
                      S.snap("north_easton", named("Stoughton Branch"), ne_store))]),
        "Easton Village": dict(
            status="proposed", mbta_name=None, approx=False, note="South Coast Rail Phase 2, at the 1881 depot",
            sources=[("Wikipedia: North Easton station", "Easton Village station redirects here; the South Coast Rail "
                      "article puts the stop at H.H. Richardson's depot on Oliver St", (42.06926944, -71.10331944)),
                     ("OSM way/212962983", "North Easton Station building (may share a source with Wikipedia: they are "
                      "1 m apart)", osm_pt("way/212962983")),
                     ("Commons photo 2017", "camera GPS of a June 2017 photo of the depot", (42.068985, -71.103518))]),
        "Raynham Place": dict(
            status="proposed", mbta_name=None, approx=False, note="South Coast Rail Phase 2, behind Raynham Park",
            sources=[("Wikipedia: Raynham Place station", "article coordinates, behind the Raynham Park racing center",
                      (41.980011, -71.075425)),
                     ("Commons photo 2017", "camera GPS of a June 2017 photo of the proposed site (both sources are "
                      "Wikimedia, possibly one editor)", (41.980555, -71.075717))],
            check=("OSM's old Dighton and Somerset bed", S.snap("raynham_place", any_rail, (41.980011, -71.075425)))),
        "Taunton": dict(
            status="proposed", mbta_name=None, approx=False, note="South Coast Rail Phase 2, Dean St depot",
            sources=[("Wikipedia: Dean Street station", "Taunton station (MBTA) redirects here; the platform would sit "
                      "north of the 1876 Old Colony depot off Dean St (Route 44)", (41.904444, -71.082222)),
                     ("Commons photo 2017", "camera GPS of a June 2017 photo of the proposed platform area (both sources "
                      "are Wikimedia)", (41.904414, -71.081546))],
            check=("OSM: the Dean Street Industrial Track meets Dean St",
                   S.crossing("taunton", named("Dean Street Industrial Track"), named("Dean Street")))),
        "Peabody": dict(
            status="revived", mbta_name=None, approx=False, note="Peabody Square depot, trains to 1958",
            sources=[("Sanborn 1920, Peabody sheet 11, placed with OSM",
                      "passenger station on Central St between the tracks and Mill St (Library of Congress); OSM gives "
                      "the two corners", mid(S.crossing("peabody_streets", named("Central Street"), any_rail),
                                             S.crossing("peabody_streets", named("Central Street"), named("Mill Street")))),
                     ("Peabody Historical Society, placed with OSM",
                      "station at Peabody Square (William Powers, Peabody's Railroads, 1998; last passenger train May 16, "
                      "1958); OSM gives the square where Central St meets Main St",
                      S.crossing("peabody_streets", named("Central Street"), named("Main Street")))]),
        "Danversport": dict(
            status="revived", mbta_name=None, approx=False, note="Essex Railroad, by the Creese & Cook tannery",
            sources=[("Sanborn 1927, Danvers sheet 13, placed with OSM",
                      "Danversport R.R. Station where the Creese & Cook tannery siding left the line (Library of Congress); "
                      "OSM gives the siding switch. Powers (1998) and Wikipedia's Essex Railroad route map list the stop "
                      "but don't place it; OSM's Danversport neighborhood point is 0.7 km away",
                      S.crossing("danversport_streets", osm_id(1051440097), rail_named("Lawrence Branch")))]),
        "Danvers": dict(
            status="revived", mbta_name=None, approx=False, note="Danvers Plains depot, at Danvers Junction from 1923",
            sources=[("Commons photos 2015", "camera GPS of three June 2015 photos of the depot, averaged. Commons: built as "
                      "Danvers Plains station on the Essex Railroad, moved in 1923 to serve the Newburyport Branch too; the "
                      "Friends of the Danvers Rail Trail say it has since been moved to a lot off Cherry St",
                      danvers_photos),
                     ("OSM Danvers Junction node", "where the Essex line met the Newburyport Branch",
                      S.centroid("danversport", named("Danvers Junction")))]),
        "Middleton": dict(
            status="revived", mbta_name=None, approx=True, note="town point placed on the old Essex line",
            sources=[("OSM town point, on the old line",
                      "OSM's Middleton town point, moved onto the Middleton Rail Trail (the old Essex Railroad). "
                      "Wikipedia's route map and the Middleton Rail Trail's history list the station; nothing found places it",
                      S.snap("middleton", essex_line, S.centroid("middleton", named("Middleton"))))]),
        "Marblehead": dict(
            status="revived", mbta_name=None, approx=False, note="depot site, now 91 Pleasant St",
            sources=[("Marblehead Weekly News, placed with OSM",
                      "National Grand Bank bought the old B&M depot site on Pleasant St in 1962 and is at 91 Pleasant St; "
                      "OSM gives the bank building", S.centroid("marblehead", osm_id(214418463))),
                     ("Sanborn 1915, Marblehead sheet 10, placed with OSM",
                      "passenger station on Pleasant St just north of School St (Library of Congress); OSM gives the corner",
                      S.crossing("marblehead", named("Pleasant Street"), named("School Street")))]),
        "Clifton": dict(
            status="revived", mbta_name=None, approx=False, note="Swampscott Branch stop at Clifton Ave",
            sources=[("Commons photo 2017", "camera GPS of a photo of the former station site, granite platform edge in "
                      "view", (42.482646, -70.877943)),
                     ("Wikipedia: Clifton, Massachusetts, placed with OSM",
                      "the site is seen from Clifton Ave and the track bed is now a bike path; OSM gives where the "
                      "Marblehead Rail Trail crosses Clifton Ave",
                      S.crossing("clifton", named("Clifton Avenue"), named("Marblehead Rail Trail")))]),
        "Hudson": dict(
            status="revived", mbta_name=None, approx=False, note="Marlborough Branch depot, Main St at High St",
            sources=[("Sanborn 1916, Hudson sheet 3, placed with OSM",
                      "Fitchburg Division passenger station on Main St opposite High St (Library of Congress); OSM gives the "
                      "spot between Main St and the old line",
                      mid(hud_main, S.snap("hudson_streets", marlborough_branch, hud_main)))],
            check=("B&M's other Hudson station, on the Central Mass line (Wikidata Q133296526, MACRIS HUD.24; Hudson's stop "
                   "1939 to 1958, building still standing)", (42.393390, -71.568555))),
        "Marlborough": dict(
            status="revived", mbta_name=None, approx=False, note="Marlborough Branch terminal, Lincoln St",
            sources=[("Wikidata Q133501665 (MACRIS MRB.103)", "Marlboro station, B&M, built 1893, since torn down",
                      (42.348200, -71.554856)),
                     ("Sanborn 1920, Marlborough sheet 4, placed with OSM",
                      "B&M passenger station on Lincoln St at Mechanic St (Library of Congress); OSM gives the corner",
                      S.crossing("marlborough", named("Lincoln Street"), named("Mechanic Street")))]),
    }


# ---------------------------------------------------------------------------------------------------------------
def norm(s):
    s = s.lower().replace("’", "'").replace(".", "")
    for a, b in ((" street", " st"), (" square", " sq"), (" avenue", " ave"), (" road", " rd"), (" center", " ctr"),
                 (" centre", " ctr")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "", s)


def osm_rank(e):
    """Station nodes first, then station ways, stop areas, public transport stations, then buildings or old stations."""
    t, kind = e["tags"], e["osm"].split("/")[0]
    if t.get("railway") in ("station", "halt"):
        return 0 if kind == "node" else (2 if t.get("public_transport") == "stop_area" else 1)
    return 3 if t.get("public_transport") == "station" else 4


def osm_match(osm, names, near):
    keys = {norm(n) for n in names if n}
    cands = [e for e in osm if any(norm(v) in keys for k in NAME_KEYS for v in e["tags"].get(k, "").split(";") if v)]
    cands = [e for e in cands if dist(near, (e["lat"], e["lon"])) <= FAR]
    return min(cands, key=lambda e: (osm_rank(e), dist(near, (e["lat"], e["lon"])))) if cands else None


def poster_names():
    sys.path.insert(0, str(SRC))
    import make_rail_poster as RP  # noqa: E402  (read only: the station list)
    RP.build()
    RP.stations()
    names = [s["name"] for s in RP.STATIONS]
    if "Lawrence" not in names:
        names.append("Lawrence")  # also the Peabody line's end
    return names


def hand_points():
    js = json.loads((DATA / "tram" / "stations_real.geojson").read_text(encoding="utf-8"))
    out = {}
    for f in js["features"]:
        p = f["properties"]
        if "placed by hand" in p.get("sources", []):
            lon, lat = f["geometry"]["coordinates"]
            out[p["name"]] = ((lat, lon), p.get("note", ""))
    return out


def m(d):
    return f"{round(d)} m"


def main():
    if "--refetch" in sys.argv or not CACHE.exists():
        refetch()
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    osm = cache["elements"]
    S = Sites(cache["sites"])
    mb = gpd.read_file(DATA / "mbta_stops.gpkg")
    mbta = {r["name"]: ((r.geometry.y, r.geometry.x), r["stop_id"]) for _, r in mb.iterrows()}
    hand = hand_points()
    R = research(S, {e["osm"]: e for e in osm})

    feats, rows, notes = [], [], []

    def add(name, pos, mbta_name, status, sources, agree_m, approx, note, cells):
        feats.append({"type": "Feature", "geometry": mapping(Point(pos[1], pos[0])),
                      "properties": dict(name=name, mbta_name=mbta_name, status=status, sources=sources, agree_m=agree_m,
                                         approx=approx, note=note)})
        rows.append((name,) + cells + (status,))

    for name in poster_names():
        mname = MBTA_NAME.get(name, name)
        if name == "Boston Central":
            pos, why = hand[name]
            corner = S.crossing("boston_central", named("Atlantic Avenue"), named("State Street"))
            add(name, pos, None, "new", ["placed by hand on this map (tram/stations_real.geojson)"], None, False,
                "placed by hand, Atlantic Ave at State St", ("Placed by hand", "None", "Our own station"))
            notes.append(f"**Boston Central**: the map's own station, placed by hand under the Dig at Atlantic Ave and State "
                         f"St. OSM puts that corner {m(dist(pos, corner))} away.")
            continue
        if name == "West Station":
            pos, why = hand[name]
            d = dist(pos, WEST_STATION_WIKI)
            add(name, pos, None, "proposed", ["placed by hand on this map (tram/stations_real.geojson)",
                                              "Wikipedia: West Station (MBTA)"], round(d), False,
                "placed by hand in Beacon Park Yard", ("Placed by hand", "Wikipedia", f"Differ, {m(d)}"))
            notes.append(f"**West Station**: kept where it was placed by hand ({why}). Wikipedia's point for MassDOT's "
                         f"planned station is {m(d)} away, at {WEST_STATION_WIKI[0]:.5f}, {WEST_STATION_WIKI[1]:.5f}.")
            continue

        if name in R:
            r = R[name]
            src = r["sources"]
            pos = src[0][2]
            agree = round(dist(pos, src[1][2])) if len(src) > 1 else None
            if agree is None:
                verdict = "Town point only" if r["approx"] else "One source, unverified"
            else:
                verdict = f"{'Agree' if agree < AGREE else 'Differ'}, {agree} m"
            add(name, pos, r["mbta_name"], r["status"], [s[0] for s in src], agree, r["approx"], r["note"],
                (src[0][0], src[1][0] if len(src) > 1 else "None", verdict))
            txt = f"**{name}** ({pos[0]:.5f}, {pos[1]:.5f}). {src[0][0]}: {src[0][1]}."
            for lab, said, pt in src[1:]:
                txt += f" {lab}, {m(dist(pos, pt))} away: {said}."
            if "check" in r:
                lab, pt = r["check"]
                txt += f" Check: {lab}, {m(dist(pos, pt))} away."
            notes.append(txt)
            continue

        status = "new" if name == "Sullivan Sq" else "exists"
        new_note = "Orange Line station; commuter stop new on this map" if status == "new" else ""
        if mname not in mbta:
            raise SystemExit(f"no MBTA stop and no research entry for {name}")
        mpos, sid = mbta[mname]
        mlab = f"MBTA V3 API {sid}"
        o = osm_match(osm, [name, mname, OSM_NAME.get(name)], mpos)
        if o is None:
            add(name, mpos, mname, status, [mlab], None, False, new_note or "one source, unverified",
                ("MBTA", "None", "One source, unverified"))
            continue
        opos, olab = (o["lat"], o["lon"]), f"OSM {o['osm']}"
        d = dist(mpos, opos)
        if d < AGREE:
            add(name, mpos, mname, status, [mlab, olab], round(d), False, new_note, ("MBTA", "OSM", f"Agree, {m(d)}"))
            continue
        if name not in WIKI_CHECK:
            add(name, mpos, mname, status, [mlab, olab], round(d), False, "MBTA and OSM differ, unresolved",
                ("MBTA", "OSM", f"Differ, {m(d)}"))
            notes.append(f"**{name}**: MBTA and OSM are {m(d)} apart and nothing else was checked.")
            continue
        wt, wlat, wlon = WIKI_CHECK[name]
        wpos, wlab = (wlat, wlon), f"Wikipedia: {wt}"
        dmw, dow = dist(mpos, wpos), dist(opos, wpos)
        if dmw < AGREE or dow >= AGREE:   # Wikipedia sides with MBTA (or with neither): keep MBTA's point
            add(name, mpos, mname, status, [mlab, wlab, olab], round(dmw), False, f"OSM point {m(d)} off",
                ("MBTA", "Wikipedia", f"{'Agree' if dmw < AGREE else 'Differ'}, {m(dmw)}"))
            used = "MBTA"
        else:                              # Wikipedia sides with OSM: MBTA's point is off the platform
            add(name, opos, mname, status, [olab, wlab, mlab], round(dow), False,
                f"MBTA point {m(d)} off; OSM used", ("OSM", "Wikipedia", f"Agree, {m(dow)}"))
            used = "OSM"
        notes.append(f"**{name}**: MBTA and OSM are {m(d)} apart. Wikipedia's point is {m(dmw)} from MBTA and {m(dow)} "
                     f"from OSM, so the {used} point is used.")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "stations.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, indent=1),
                                          encoding="utf-8")
    write_md(rows, notes, feats)
    summary(feats)


def bucket(p):
    if p["sources"][0].startswith("placed by hand"):
        return "placed by hand"
    if p["approx"]:
        return "approx"
    if p["agree_m"] is None:
        return "one source"
    return "agree" if p["agree_m"] < AGREE else "differ"


def summary(feats):
    c = Counter(bucket(f["properties"]) for f in feats)
    print(len(feats), "stations:", dict(c))
    for f in feats:
        p = f["properties"]
        if bucket(p) != "agree":
            print(f"  {p['name']:24s} {bucket(p):15s} agree_m={p['agree_m']}  {p['note']}")


def write_md(rows, notes, feats):
    c = Counter(bucket(f["properties"]) for f in feats)
    lines = [
        "# Regional rail station positions",
        "",
        "Where each station on the commuter rail poster really sits, and what backs the spot. The points are in "
        "`stations.geojson`, built by `src/rail_regional_stations.py`. **Agree** = two sources under 150 m apart. "
        "**One source** = unverified. **Town point only** = approx: a town point set on the old line. The first source is "
        "the position used. \"Placed with OSM\" means a written or mapped description (a corner, a siding) turned into a "
        "point with OpenStreetMap's streets and old rail lines.",
        "",
        f"{len(feats)} stations: {c['agree']} with two sources that agree, {c['differ']} where they differ, "
        f"{c['one source']} with one source (unverified), {c['approx']} town point only, {c['placed by hand']} placed by "
        "hand on this map.",
        "",
        "| Station | Position source 1 | Source 2 | Agree or differ | Status |",
        "|---|---|---|---|---|",
    ]
    lines += [f"| {' | '.join(r)} |" for r in rows]
    lines += ["", "## Notes", "", "Stations not plain MBTA and OSM agreements, in poster order.", ""]
    lines += [f"- {n}" for n in notes]
    lines += [
        "",
        "## Sources",
        "",
        "- **MBTA**: MBTA V3 API stops (`data/mbta_stops.gpkg`, fetched November 3, 2026). Plymouth from the API's "
        "`/stops/place-PB-0356`, still listed after the 2021 closure.",
        "- **OSM**: OpenStreetMap through Overpass, November 7 and 8, 2026, cached in `osm_stations.json` with the streets "
        "and old rail lines used to place described sites. A name match more than 3 km from the MBTA point is ignored.",
        "- **Wikipedia, Wikidata and Wikimedia Commons**: article coordinates, item coordinates and photo camera GPS, read "
        "November 7 and 8, 2026.",
        "- **Sanborn**: Sanborn Fire Insurance Maps, Library of Congress, copies on Wikimedia Commons: Peabody 1920 "
        "sheet 11, Danvers 1927 sheet 13, Marblehead 1915 sheet 10, Hudson 1916 sheet 3, Marlborough 1920 sheet 4.",
        "- **Town and city sources**: City of Salem, South Salem stop community update slides (January 28, 2025); Peabody "
        "Historical Society (\"Ticket to Ride\", and William Powers, *Peabody's Railroads*, 1998); Marblehead Weekly News on "
        "the National Grand Bank and the depot site; Friends of the Danvers Rail Trail history page; South Coast Rail 2013 "
        "Final EIS figure 3.2-22 (copy on Commons).",
    ]
    (OUT / "station_sources.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
