"""Today's MBTA lines and stops, from the public MBTA V3 API (no key needed, 20 requests a minute).

python days/08-utopia/src/fetch_mbta.py
Writes data/mbta_lines.gpkg (one row per typical route pattern) and data/mbta_stops.gpkg.
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
import geopandas as gpd
from shapely.geometry import LineString, Point

DAY = Path(__file__).resolve().parents[1]
API = "https://api-v3.mbta.com"
HEADERS = {"User-Agent": "30dmc-day08-map", "Accept": "application/vnd.api+json"}
SUBWAY = ["Red", "Mattapan", "Orange", "Blue", "Green-B", "Green-C", "Green-D", "Green-E"]
SILVER = ["741", "742", "743", "746", "749", "751"]


def get(path, **params):
    url = f"{API}/{path}?" + urllib.parse.urlencode(params, safe="[],")
    for wait in (0, 10, 30, 65):
        time.sleep(wait or 3.2)  # stay under the keyless limit
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
    raise SystemExit(f"rate limited: {url}")


def decode(poly):
    """Google encoded polyline, precision 5, to (lon, lat) pairs."""
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


def main():
    cr = [r["id"] for r in get("routes", **{"filter[type]": "2"})["data"]]
    print("commuter rail routes:", cr)
    lines, stops = [], {}
    for rid in SUBWAY + SILVER + cr:
        kind = "subway" if rid in SUBWAY else "silver" if rid in SILVER else "commuter"
        pats = get("route_patterns", **{"filter[route]": rid, "include": "representative_trip"})
        trips = {t["id"]: t for t in pats.get("included", [])}
        seen = set()
        for p in pats["data"]:
            a = p["attributes"]
            if a["typicality"] != 1 or a["direction_id"] != 0:
                continue
            trip = trips[p["relationships"]["representative_trip"]["data"]["id"]]
            sid = trip["relationships"]["shape"]["data"]["id"]
            if sid in seen:
                continue
            seen.add(sid)
            shp = get(f"shapes/{sid}")["data"]["attributes"]["polyline"]
            lines.append({"route": rid, "kind": kind, "name": a["name"], "shape": sid,
                          "geometry": LineString(decode(shp))})
        for s in get("stops", **{"filter[route]": rid})["data"]:
            st = stops.setdefault(s["id"], {"stop_id": s["id"], "name": s["attributes"]["name"],
                                            "routes": [], "geometry": Point(s["attributes"]["longitude"], s["attributes"]["latitude"])})
            st["routes"].append(rid)
        print(rid, len(seen), "shapes", flush=True)
    g = gpd.GeoDataFrame(lines, crs=4326)
    s = gpd.GeoDataFrame(stops.values(), crs=4326)
    s["routes"] = s.routes.str.join(",")
    (DAY / "data").mkdir(exist_ok=True)
    for f in ("mbta_lines.gpkg", "mbta_stops.gpkg"):
        (DAY / "data" / f).unlink(missing_ok=True)
    g.to_file(DAY / "data/mbta_lines.gpkg", layer="lines", driver="GPKG")
    s.to_file(DAY / "data/mbta_stops.gpkg", layer="stops", driver="GPKG")
    print(len(g), "lines,", len(s), "stops")


if __name__ == "__main__":
    main()
