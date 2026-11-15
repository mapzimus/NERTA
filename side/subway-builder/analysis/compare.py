"""Compare Spencer's Subway Builder network with NERTA's T map.

Coverage uses Census LODES 2021 (jobs by workplace, working residents by home)
summed to 2020 tracts and split by area inside a half-mile walk of any stop.
"""
import json
import math
import sys
from collections import defaultdict, deque
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point, LineString
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))
from network import ROUTES, LOOPS, REGIONAL, GEO_ALIAS, display  # noqa
from nerta_geo import geo, norm, nerta_lines  # noqa

CEN = Path(sys.argv[1])
CRS = 26986  # Mass State Plane, meters
HALF = 804.67

# ---------------- Spencer ----------------
d = json.load(open(HERE.parent / "private/bostonstations.geojson"))
acc = defaultdict(list)
for f in d["features"]:
    acc[f["properties"]["name"].strip()].append(f["geometry"]["coordinates"])
SG = {k: tuple(np.mean(v, axis=0)) for k, v in acc.items()}
def sxy(n):
    return SG[GEO_ALIAS.get(n, n)]

S_LINES = {}
for code, (nm, ck, st) in ROUTES.items():
    if code == "BRN2":
        continue
    S_LINES[code] = (nm, ck, list(st) + ([st[0]] if code in LOOPS else []))
S_LINES["BRN"] = ("Brown Line North", "brown", ROUTES["BRN"][2])
S_EXTRA = [("BRN", ROUTES["BRN2"][2])]

# ---------------- NERTA ----------------
NG = geo()
COLORNAME = {}
import make_tmap as mt
for nm in ["RED", "ORANGE", "BLUE", "GREEN", "YELLOW", "CYAN", "INDIGO", "SILVER"]:
    if hasattr(mt, nm):
        COLORNAME[getattr(mt, nm)] = nm.title()
N_SEGS = [(COLORNAME.get(c, c), style, stops) for c, style, stops in nerta_lines()]
def nxy(n):
    return NG[norm(n)]


def proj(pts):
    g = gpd.GeoSeries([Point(p) for p in pts], crs=4326).to_crs(CRS)
    return np.array([[q.x, q.y] for q in g])


def network(segs, xy):
    """segs: list of (line, style, [stops]). Returns stops, edges, graph."""
    stops, edges, line_of = {}, {}, defaultdict(set)
    for line, style, st in segs:
        for s in st:
            stops[s] = xy(s)
            line_of[s].add(line)
        for a, b in zip(st, st[1:]):
            k = tuple(sorted((a, b)))
            edges.setdefault(k, set()).add((line, style))
    return stops, edges, line_of


S_SEGS = [(ck.title(), "imagined", st) for code, (_, ck, st) in S_LINES.items()] + \
         [("Brown", "imagined", st) for c, st in S_EXTRA]
s_stops, s_edges, s_line_of = network(S_SEGS, sxy)
n_stops, n_edges, n_line_of = network(N_SEGS, nxy)

def to_m(stops):
    names = list(stops)
    P = proj([stops[n] for n in names])
    return dict(zip(names, P))
SM, NM = to_m(s_stops), to_m(n_stops)

def km(edges, M):
    return sum(np.linalg.norm(M[a] - M[b]) for a, b in edges) / 1000

def km_by(edges, M):
    out = defaultdict(float)
    for (a, b), ls in edges.items():
        styles = {s for _, s in ls}
        st = "solid" if "solid" in styles else ("stripe" if "stripe" in styles else "dash")
        out[st] += np.linalg.norm(M[a] - M[b]) / 1000
    return out

# real T today, for "how much is already built"
real = gpd.read_file(HERE.parents[2] / "boston-map/data/mbta_stops.gpkg").to_crs(CRS)
real = real[real.routes.str.contains("Red|Orange|Blue|Green|Mattapan", na=False)]
RP = np.array([[g.x, g.y] for g in real.geometry])

def near_real(M, r=300):
    return sum(1 for p in M.values() if np.min(np.hypot(*(RP - p).T)) < r)

# ---------------- census ----------------
tr = gpd.read_file(f"zip://{CEN/'tracts.zip'}").to_crs(CRS)
wac = pd.read_csv(CEN / "wac.csv.gz", dtype={"w_geocode": str}, usecols=["w_geocode", "C000"])
rac = pd.read_csv(CEN / "rac.csv.gz", dtype={"h_geocode": str}, usecols=["h_geocode", "C000"])
jobs = wac.groupby(wac.w_geocode.str[:11]).C000.sum()
res = rac.groupby(rac.h_geocode.str[:11]).C000.sum()
tr["JOBS"] = tr.GEOID.map(jobs).fillna(0)
tr["RES"] = tr.GEOID.map(res).fillna(0)
tr["A"] = tr.area
sidx = tr.sindex

def served(geom):
    t = tr.iloc[sidx.query(geom, predicate="intersects")]
    a = t.intersection(geom).area / t.A
    return float((t.RES * a).sum()), float((t.JOBS * a).sum())

def catch(M):
    return unary_union([Point(p).buffer(HALF) for p in M.values()])

S_C, N_C = catch(SM), catch(NM)
both = S_C.intersection(N_C)
s_only = S_C.difference(N_C)
n_only = N_C.difference(S_C)

def walkshed_people(M):
    return {n: served(Point(p).buffer(HALF)) for n, p in M.items()}

# ---------------- transfers to downtown ----------------
def transfers_to(core, line_of, segs):
    """Fewest line changes from each stop to any core stop."""
    stops_on = defaultdict(set)
    for line, _, st in segs:
        stops_on[line].update(st)
    best = {}
    start = set()
    for c in core:
        start |= line_of.get(c, set())
    dist = {l: 0 for l in start}
    q = deque(start)
    while q:
        l = q.popleft()
        for s in stops_on[l]:
            for l2 in line_of[s]:
                if l2 not in dist:
                    dist[l2] = dist[l] + 1
                    q.append(l2)
    for s, ls in line_of.items():
        best[s] = 0 if s in core else min(dist.get(l, 9) for l in ls)
    return best

S_CORE = {"Government Center", "Downtown", "Boston Common", "Haymarket", "South Station",
          "North Station", "Chinatown", "Bowdoin", "Waterfront", "Public Garden"}
N_CORE = {"Gov't Center", "Park Street", "Downtown Crossing", "State", "South Station",
          "North Station", "Haymarket", "Boston Central", "Chinatown", "Aquarium", "Boylston"}

def pair_transfers(line_of, segs):
    """Fewest line changes between every pair of stops (line families)."""
    stops_on = defaultdict(set)
    for line, _, st in segs:
        stops_on[line].update(st)
    lines = list(stops_on)
    L = {l: i for i, l in enumerate(lines)}
    D = np.full((len(lines), len(lines)), 9)
    for l in lines:
        dist = {l: 0}; q = deque([l])
        while q:
            a = q.popleft()
            for s_ in stops_on[a]:
                for b in line_of[s_]:
                    if b not in dist:
                        dist[b] = dist[a] + 1; q.append(b)
        for b, v in dist.items():
            D[L[l], L[b]] = v
    names = list(line_of)
    vals = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            vals.append(min(D[L[x], L[y]] for x in line_of[a] for y in line_of[b]))
    v = np.array(vals)
    return dict(pairs=len(v), zero=round(100 * np.mean(v == 0), 1), le1=round(100 * np.mean(v <= 1), 1),
                le2=round(100 * np.mean(v <= 2), 1), mean=round(float(v.mean()), 2))


def report():
    out = {}
    for tag, stops, edges, line_of, M, segs, core in (
            ("spencer", s_stops, s_edges, s_line_of, SM, S_SEGS, S_CORE),
            ("nerta", n_stops, n_edges, n_line_of, NM, N_SEGS, N_CORE)):
        lines = {l for l, _, _ in segs}
        hubs = sorted(((len(v), k) for k, v in line_of.items()), reverse=True)
        xfer = transfers_to(core, line_of, segs)
        C = catch(M)
        r, j = served(C)
        far = max(np.linalg.norm(p - M["South Station"]) for p in M.values()) / 1000
        spacing = np.median([np.linalg.norm(M[a] - M[b]) for a, b in edges])
        out[tag] = dict(
            lines=len(lines), stops=len(stops), km=round(km(edges, M), 1),
            km_by={k: round(v, 1) for k, v in km_by(edges, M).items()},
            median_spacing_m=int(spacing), transfer_stations=sum(1 for v in line_of.values() if len(v) > 1),
            top_hubs=[(k, n) for n, k in hubs[:6]],
            at_real_T=near_real(M), reach_km=round(far, 1),
            area_km2=round(C.area / 1e6, 1), res=int(r), jobs=int(j),
            one_seat_core=round(100 * np.mean([v <= 0 for v in xfer.values()]), 0),
            le1_core=round(100 * np.mean([v <= 1 for v in xfer.values()]), 0),
            xfer=xfer, pairs=pair_transfers(line_of, segs),
            line_names=sorted(lines),
        )
    for k in ("res", "jobs"):
        pass
    br, bj = served(both); sr, sj = served(s_only); nr, nj = served(n_only)
    out["overlap"] = dict(both=(int(br), int(bj)), spencer_only=(int(sr), int(sj)),
                          nerta_only=(int(nr), int(nj)),
                          both_km2=round(both.area / 1e6, 1), s_only_km2=round(s_only.area / 1e6, 1),
                          n_only_km2=round(n_only.area / 1e6, 1))
    # places only one network reaches
    def gaps(Ma, Mb):
        rows = []
        Pb = np.array(list(Mb.values()))
        for n, p in Ma.items():
            dmin = np.min(np.hypot(*(Pb - p).T))
            if dmin > HALF * 1.5:
                r, j = served(Point(p).buffer(HALF).difference(catch(Mb)))
                rows.append((n, int(dmin), int(r), int(j)))
        return sorted(rows, key=lambda x: -(x[2] + x[3]))
    out["spencer_gaps"] = gaps(SM, NM)
    out["nerta_gaps"] = gaps(NM, SM)
    return out


if __name__ == "__main__":
    R = report()
    for k in ("spencer", "nerta"):
        r = dict(R[k]); r.pop("xfer")
        print(k, json.dumps(r, indent=1))
    print("overlap", R["overlap"])
    print("SPENCER-ONLY places:")
    for row in R["spencer_gaps"][:30]:
        print("  ", row)
    print("NERTA-ONLY places:")
    for row in R["nerta_gaps"][:30]:
        print("  ", row)
    json.dump({k: (v if k not in ("spencer", "nerta") else {a: b for a, b in v.items() if a != "xfer"})
               for k, v in R.items()}, open(HERE.parent / "private/output/comparison_results.json", "w"), indent=1, default=str)
