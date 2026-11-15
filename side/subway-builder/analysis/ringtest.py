"""Connectivity value: transfers between all stop pairs, with and without pieces."""
import numpy as np
from collections import defaultdict
import compare as C

def stats(segs):
    line_of = defaultdict(set)
    for l, st, stops in segs:
        for s in stops:
            line_of[s].add(l)
    return C.pair_transfers(line_of, segs)

base = C.N_SEGS
print("NERTA today:", stats(base))
# without the Yellow ring
print("no Yellow:", stats([s for s in base if s[0] != "Yellow"]))
# without Blue's west link
print("no Blue west link:", stats([s for s in base if not (s[0] == "Blue" and "West Station" in s[2])]))
# a middle arc on existing/planned NERTA stops, along Spencer's Teal corridor
arc = ["Wellington", "Medford/Tufts", "West Medford", "Alewife", "Watertown", "Brighton Center",
       "Boston College", "Reservoir", "Forest Hills", "Morton St", "Fields Corner"]
missing = [s for s in arc if C.norm(s) not in C.NG]
print("arc stops w/o coords:", missing)
print("with middle arc:", stats(base + [("Arc", "dash", arc)]))
P = [C.NG[C.norm(s)] for s in arc]
import geopandas as gpd
from shapely.geometry import Point
g = gpd.GeoSeries([Point(p) for p in P], crs=4326).to_crs(C.CRS)
km = sum(a.distance(b) for a, b in zip(g, g[1:])) / 1000
print("arc length km (straight):", round(km, 1))
# trips that need a change at downtown today but not with the arc
