"""Real-world coordinates for every NERTA T stop, for comparing with Spencer."""
import json, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "boston-map/src"))
import geopandas as gpd
import make_tmap

def norm(s):
    s = s.lower().replace("gov't", "government").replace("'", "").replace("+", "")
    s = re.sub(r"[./,-]", " ", s)
    rep = {"street": "st", "square": "sq", "avenue": "ave", "road": "rd", "center": "ctr",
           "centre": "ctr", "saint": "st", "massachusetts": "mass", "university": "u"}
    w = [rep.get(x, x) for x in s.split()]
    return "".join(w)


def nerta_lines():
    out = []
    for color, style, path, stops in make_tmap.lines():
        stops = list(stops)
        # the Beacon St branch joins at Kenmore through its drawn path, not its stop list
        if stops[0] == "St. Mary's St":
            stops = ["Kenmore"] + stops
        out.append((color, style, stops))
    return out

def geo():
    m = gpd.read_file(REPO / "boston-map/data/mbta_stops.gpkg").to_crs(4326)
    G = {}
    for _, r in m.iterrows():
        G.setdefault(norm(r["name"]), (r.geometry.x, r.geometry.y))
    for k, v in json.load(open(REPO / "boston-map/tools/stopcheck/geo.json")).items():
        if v: G.setdefault(norm(k), (v[1], v[0]))
    e = gpd.read_file(REPO / "boston-map/data/ext_stations.gpkg").to_crs(4326)
    for _, r in e.iterrows():
        G.setdefault(norm(r["label"]), (r.geometry.x, r.geometry.y))
    alias = {"BU Central": "Boston University Central", "BU East": "Boston University East",
             "Hynes": "Hynes Convention Center", "Northeastern": "Northeastern University",
             "Science Park": "Science Park/West End", "Four Corners": "Four Corners/Geneva"}
    for a, b in alias.items():
        if norm(b) in G:
            G[norm(a)] = G[norm(b)]
    # Approximate spots for planned NERTA stops with no geocode on file.
    approx = {"Boston Central": (-71.0545, 42.3585), "Cliftondale": (-71.0186, 42.4386),
              "Convention Center": (-71.0450, 42.3456), "Day Sq": (-71.0257, 42.3784),
              "Linden Sq": (-71.0476, 42.4271), "Melnea Cass": (-71.0760, 42.3330),
              "Moakley Park": (-71.0560, 42.3290), "Seaver St": (-71.0853, 42.3077),
              "Stadium": (-71.0700, 42.3920), "Terminals": (-71.0200, 42.3650),
              "Thompson Sq": (-71.0610, 42.3760), "West Station": (-71.1270, 42.3570),
              "Weymouth": (-70.9690, 42.2210), "Wyoma Sq": (-70.9580, 42.4770)}
    for a, v in approx.items():
        G.setdefault(norm(a), v)
    # bad geocodes on file (they landed hundreds of km away)
    G[norm("Belmont Ctr")] = (-71.1784, 42.3959)
    G[norm("Winthrop Center")] = (-70.9840, 42.3790)
    return G

if __name__ == "__main__":
    G = geo()
    miss = set()
    names = set()
    for c, st, stops in nerta_lines():
        for s in stops:
            names.add(s)
            if norm(s) not in G:
                miss.add(s)
    print(len(names), "NERTA stops;", len(miss), "without coordinates:")
    print(sorted(miss))
