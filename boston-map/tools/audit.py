"""Audit both posters: stops in water, stop order and compass direction against real positions."""
import sys, types, re
from pathlib import Path
src = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(src))
import numpy as np
import geopandas as gpd
import make_tmap as T
from station_kit import place, rounded
from shapely.geometry import Point

# positions from the T map
pts = {}
for col, style, path, stops in T.lines():
    for s, p in place(rounded(path, T.CR), stops, {**T.A, **T.EXTRA}).items():
        if s not in T.EXTRA and s[-1] != "*":
            pts.setdefault(s, p)
print(len(pts), "stops on T map")

# rebuild the water the map draws, capturing polygons
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
T.real_water(ax, pts)
from shapely.geometry import Polygon as SP
from shapely.ops import unary_union
water, land = [], []
for pat in ax.patches:
    xy = pat.get_xy()
    (land if pat.get_zorder() > 1.05 else water).append(SP(xy).buffer(0))
wet = unary_union(water).difference(unary_union(land)) if land else unary_union(water)
for s, p in pts.items():
    if wet.contains(Point(p)):
        print("IN WATER:", s, p)
extra = {"purple " + n: xy for n, xy, _, _ in T.CR_STOPS}
for s, p in extra.items():
    if wet.contains(Point(p)):
        print("IN WATER:", s, p)
# real positions vs diagram: compass order between neighbors on each line
st = gpd.read_file(T.DAY / "data/mbta_stops.gpkg").to_crs(26919).drop_duplicates("name").set_index("name").geometry
alias = {"Lynn": "Lynn Interim", "Gov't Center": "Government Center", "Mass. Ave": "Massachusetts Avenue", "BU East": "Boston University East", "BU Central": "Boston University Central",
         "Tufts Medical Ctr": "Tufts Medical Center", "Hynes": "Hynes Convention Center", "Science Park": "Science Park/West End", "Sullivan Sq": "Sullivan Square", "Seaport": "World Trade Center", "Long Wharf": "Aquarium"}
def real(n):
    k = alias.get(n, n)
    for a, b in ((" Sq", " Square"), (" St", " Street"), (" Ave", " Avenue"), (" Rd", " Road")):
        if k not in st.index:
            k = k.replace(a, b)
    return st[k] if k in st.index else None
miss = [n for n in pts if real(n) is None]
print("not in MBTA data (new or renamed):", miss)
rows = []
for col, style, path, stops in T.lines():
    seq = [s for s in stops if s in pts and real(s) is not None]
    for a, b in zip(seq, seq[1:]):
        ra, rb = real(a), real(b)
        v = np.array([rb.x - ra.x, rb.y - ra.y]); u = np.array(pts[b]) - np.array(pts[a])
        if np.linalg.norm(v) == 0 or np.linalg.norm(u) == 0:
            continue
        c = v @ u / np.linalg.norm(v) / np.linalg.norm(u)
        if c < 0:
            rows.append((round(float(c), 2), a, b))
print("segments pointing the wrong way vs reality:", sorted(rows)[:25])
