"""Bend the real-geography tram network into the NERTA layout (Max, November 7: decide on a real map, then merge).

Every NERTA station has a real spot (data/tram/stations_real.geojson) and a spot on the main map (make_tmap's lines() and
place(), computed here the same way, nothing drawn). A thin-plate spline through those pairs bends real geography into
map space, the same trick that bent the coast. Tram stops at NERTA stations then snap to the station itself.

The second half is the layout engine for the tram map drawn over faded NERTA (make_tram_map.py):
  1. Read the routes (tram_draft.json, plus any new id in tram_extra.json), tidy each stop list, and merge stops that
     several routes share into one node. Stops within a few hundred meters of each other in real life are put in the
     order that doesn't zigzag on the schematic.
  2. Split the network into chains: runs of stops between NERTA stations, route ends and junctions. A chain that several
     routes share is laid out once and drawn as parallel lines, one per route.
  3. Each chain is routed on a fine 45-degree lattice by least cost: length, bends, staying near the real street (rotated
     and scaled to fit the two stations at its ends), and penalties for running along a NERTA line or another tram, for
     crossing them at a slant instead of square, and for passing over a station dot or open water.
  4. Tram-only stops are spread along their chain in real-distance proportion, kept off bends, crossings and dots.

python tram_merge.py [--raw] [--plot out.png]   prints how well the bend fits, and can plot the trams over NERTA.
"""
import itertools
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.interpolate import RBFInterpolator
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point

sys.path.insert(0, str(Path(__file__).parent))
import make_tmap as M  # noqa: E402  (read only)
from station_kit import place, rounded  # noqa: E402

DAY = Path(__file__).resolve().parents[1]
TD = DAY / "data" / "tram"
TRAM = "#e0457b"


def xy_m(lon, lat):
    return ((lon + 71.06) * 111320 * math.cos(math.radians(42.36)), (lat - 42.36) * 110540)


def nerta_positions():
    """Station -> spot on the main map, exactly as make_tmap places them (first line to place a station wins)."""
    pts = {}
    for _col, _style, path, stops in M.lines():
        xy = rounded(path, 7 if "Terminals" in stops else M.CR)
        for s, p in place(xy, stops, {**M.A, **M.EXTRA}).items():
            if s in M.EXTRA or s.endswith("*"):
                continue
            pts.setdefault(s, (float(p[0]), float(p[1])))
    for n, p, _side, _st in M.CR_STOPS:
        name = n.replace("\n", " ").replace(" ", "")
        pts.setdefault(name, (float(p[0]), float(p[1])))   # "South Salem", as the real data and the tram data spell it
        pts.setdefault(name.replace(" ", ""), (float(p[0]), float(p[1])))   # the older key, "SouthSalem"
    return pts


def real_positions():
    fs = json.loads((TD / "stations_real.geojson").read_text(encoding="utf-8"))["features"]
    return {f["properties"]["name"]: (xy_m(*f["geometry"]["coordinates"]), f["properties"]["verified"]) for f in fs}


def bender(smoothing=40.0, verified_only=False):
    """Returns f(real meters Nx2) -> map units Nx2, and the control pairs used."""
    sch, real = nerta_positions(), real_positions()
    names = [n for n in sch if n in real and (real[n][1] or not verified_only)]
    src = np.array([real[n][0] for n in names]) / 1000.0   # km keeps the spline well scaled
    dst = np.array([sch[n] for n in names])
    rbf = RBFInterpolator(src, dst, kernel="thin_plate_spline", smoothing=smoothing)
    return (lambda pts: rbf(np.asarray(pts, float) / 1000.0)), names, src, dst


def octo_leg(p, q, hint=None):
    """Two-piece 45-degree path from p to q: a diagonal and a straight. Picks the order whose bend sits nearer the hint points."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    d = q - p
    m = min(abs(d[0]), abs(d[1]))
    diag = np.array([np.sign(d[0]) * m, np.sign(d[1]) * m])
    a, b = p + diag, q - diag   # diagonal first, or straight first
    if hint is None or len(hint) == 0:
        return [p, a, q]
    hint = np.asarray(hint, float)

    def cost(bend):
        return sum(_seg_dist(h, [p, bend, q]) for h in hint)
    return [p, a, q] if cost(a) <= cost(b) else [p, b, q]


def _seg_dist(h, poly):
    best = 1e9
    for u, v in zip(poly, poly[1:]):
        uv = v - u
        t = 0.0 if not uv.any() else np.clip(np.dot(h - u, uv) / np.dot(uv, uv), 0, 1)
        best = min(best, float(np.hypot(*(h - (u + t * uv)))))
    return best


def schematize(route, f, sch, tol=4.0, grid=0.5):
    """First-pass straightening (kept for comparison; the tram map uses layout() below).
    One tram route -> (path vertices, stop names, anchors) in map units."""
    stops = route["stops"]
    warped = f([xy_m(*s["lonlat"]) for s in stops])
    fixed = {}
    for i, s in enumerate(stops):
        if s["nerta"] and s["name"] in sch:
            fixed[i] = np.array(sch[s["name"]], float)
    for i in (0, len(stops) - 1):
        fixed.setdefault(i, np.round(warped[i] / grid) * grid)
    while True:
        keys = sorted(fixed)
        worst, wi = 0.0, None
        legs = []
        for a, b in zip(keys, keys[1:]):
            hint = warped[a + 1:b]
            leg = octo_leg(fixed[a], fixed[b], hint)
            legs.append(leg)
            for k in range(a + 1, b):
                d = _seg_dist(warped[k], leg)
                if d > worst:
                    worst, wi = d, k
        if wi is None or worst <= tol:
            break
        fixed[wi] = np.round(warped[wi] / grid) * grid
    verts = [legs[0][0]]
    for leg in legs:
        for v in leg[1:]:
            if np.hypot(*(v - verts[-1])) > 1e-6:
                verts.append(v)
    clean = [verts[0]]
    for v, w in zip(verts[1:], verts[2:] + [None]):
        if w is None:
            clean.append(v)
            continue
        u1, u2 = v - clean[-1], w - v
        if abs(u1[0] * u2[1] - u1[1] * u2[0]) < 1e-6 and np.dot(u1, u2) > 0:
            continue
        clean.append(v)
    anchors = {stops[i]["name"]: tuple(fixed[i]) for i in fixed}
    return np.array(clean), [s["name"] for s in stops], anchors


# ===============================================================================================================
# Layout engine for the tram map over faded NERTA
# ===============================================================================================================
H = 0.5                       # lattice step for routing, in drawing units
DIRS = np.array([(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)])
DLEN = np.hypot(DIRS[:, 0], DIRS[:, 1])
AXIS = np.array([0, 1, 2, 3, 0, 1, 2, 3])   # level, rising, upright, falling
TURN = (0.0, 1.8, 4.0)        # cost of going straight on, a 45-degree bend, a 90-degree bend (sharper is not allowed)
# Penalty per unit of length, by the angle between the tram and what it meets: running along, 45 degrees, square, 45 degrees
P_NERTA = (45.0, 5.0, 1.2, 5.0)
P_RAIL = (14.0, 2.0, 0.5, 2.0)     # commuter rail, Silver Line, the Dig
P_TRAM = (45.0, 7.0, 0.8, 7.0)
P_DOT, P_STOP, P_WATER = 70.0, 70.0, 0.8
W_HINT, TOL_HINT = 0.30, 2.0       # pull toward the real street, beyond a tolerance
CORNER = 1.3                        # tram corner radius
GAP_PREF = 3.3   # drawing units at 6 pt per unit (scaled with the type at other scales) between stops along a line, where there is room: level names don't reach the next stop
SWING = False   # swing a crowded stretch out in a U (off: the tram stays straight and its stop circles shrink instead)


class Style:
    """Symbol sizes in points (research/tram-changes-for-all-maps.md), with their size in drawing units for one sheet scale."""

    def __init__(self, ppu, w=1.6):
        self.ppu = ppu
        self.w_pt = w                       # tram line width W
        self.hair_pt = 0.11 * w             # black center line
        self.edge_pt = 0.4 * w              # circle edge and cross arms
        self.W = w / ppu
        self.R = 3.0 * w / ppu              # stop circle radius: diameter 6 W on this map (the posters use 7.5 W); round 3 allowed smaller
        self.ARM = 1.35                     # arms reach 1.35 R from the center
        self.S = (w + 1.1) / ppu            # pitch of side-by-side trams
        self.GAP = 0.9 / ppu                # clear paper between a tram and anything it passes
        self.NW = 4.6 / ppu                 # faded NERTA line width
        self.CW = 1.9 / ppu                 # faded commuter rail width
        self.DOT = 2.6 / ppu                # faded station dot radius
        self.RING = 1.0 / ppu               # ink ring of a transfer stop: its width
        self.RING_GAP = 0.9 / ppu           # paper between the pink edge and the ink ring


# ---------------------------------------------------------------------------------------------------------------
# Data
def _read_json(p, tries=6):
    err = None
    for _ in range(tries):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:   # another session may be writing it
            err = e
            time.sleep(1.5)
    raise err


def load_routes(log=print):
    """tram_draft.json, plus any route in tram_extra.json whose id isn't there yet (de-duplicated by id)."""
    routes, seen = [], set()
    for name in ("tram_draft.json", "tram_extra.json"):
        p = TD / name
        if not p.exists():
            continue
        for r in _read_json(p).get("routes", []):
            rid = str(r.get("id"))
            if rid in seen:
                continue
            seen.add(rid)
            routes.append(r)
    log(f"{len(routes)} tram routes")
    return routes


def _dist(a, b):
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


class Net:
    """Routes as lists of node keys, and the nodes: NERTA stations (fixed spot) and tram stops (real spot only)."""

    def __init__(self, routes, sch, f):
        self.sch, self.f = sch, f
        self.nodes, self.routes, self.notes = {}, [], []
        free = []
        rp = real_positions()   # live: a stop at a station on tonight's main map is a transfer even if the tram data predates it
        for r in routes:
            rid = str(r["id"])
            stops = []
            for s in r.get("stops", []):
                ll = s.get("lonlat")
                if not ll:
                    self.notes.append(f"{rid}: {s.get('name')} has no position, left off")
                    continue
                ner = s["name"] in sch and (bool(s.get("nerta")) or (s["name"] in rp and _dist(rp[s["name"]][0], xy_m(*ll)) < 400))
                if ner and not s.get("nerta"):
                    self.notes.append(f"{rid}: {s['name']} is a station on the main map tonight; drawn as a transfer stop")
                if s.get("nerta") and not ner:
                    self.notes.append(f"{rid}: {s['name']} is marked as a NERTA station but isn't on the main map; drawn as a tram stop")
                stops.append(dict(name=s["name"], nerta=ner, real=np.array(xy_m(*ll), float)))
            clean = []
            for st in stops:   # a bus stop beside its station, or the same stop twice in a row, is one stop
                if clean:
                    pv = clean[-1]
                    d = _dist(pv["real"], st["real"])
                    if (pv["name"] == st["name"] and pv["nerta"] == st["nerta"]) or (d < 150 and pv["nerta"] != st["nerta"]):
                        keep, drop = (st, pv) if st["nerta"] else (pv, st)
                        clean[-1] = keep
                        if pv["name"] != st["name"] or pv["nerta"] != st["nerta"]:
                            self.notes.append(f"{rid}: tram stop '{drop['name']}' is {d:.0f} m from '{keep['name']}', drawn as one stop")
                        continue
                clean.append(st)
            keys = []
            for st in clean:
                if st["nerta"]:
                    k = "N|" + st["name"]
                    nd = self.nodes.setdefault(k, dict(key=k, name=st["name"], nerta=True, reals=[], routes=[], names=[st["name"]],
                                                       map=np.array(sch[st["name"]], float)))
                else:
                    k = None
                    for fk in free:
                        nd = self.nodes[fk]
                        d = _dist(np.mean(nd["reals"], axis=0), st["real"])
                        if d < 60 or (st["name"] in nd["names"] and d < 300):
                            k = fk
                            break
                    if k is None:
                        k = f"S|{st['name']}|{len(free)}"
                        self.nodes[k] = dict(key=k, name=st["name"], nerta=False, reals=[], routes=[], names=[])
                        free.append(k)
                    nd = self.nodes[k]
                    if st["name"] not in nd["names"]:
                        nd["names"].append(st["name"])
                nd["reals"].append(st["real"])
                if rid not in nd["routes"]:
                    nd["routes"].append(rid)
                if keys and keys[-1] == k:
                    continue
                keys.append(k)
            if len(keys) < 2:
                self.notes.append(f"{rid}: fewer than two stops, left off")
                continue
            self.routes.append(dict(id=rid, name=r.get("name", ""), via=r.get("via", ""), keys=keys, raw=r))
        for nd in self.nodes.values():
            nd["real"] = np.mean(nd["reals"], axis=0)
            if len(nd["names"]) > 1:
                self.notes.append(f"tram stops {' / '.join(nd['names'])} are within 60 m of each other: drawn as one stop, named '{nd['name']}'")
        self.rank = {r["id"]: i for i, r in enumerate(self.routes)}
        self._reorder_close_stations()

    def est(self, k):
        nd = self.nodes[k]
        return nd["map"] if nd["nerta"] else np.asarray(self.f([nd["real"]])[0], float)

    def _reorder_close_stations(self, near=350.0):
        """NERTA stations a few hundred meters apart in real life can sit far apart on the schematic (Melnea Cass, Northampton
        and Boston Medical). A tram calling at a run of them takes the order that makes the shortest line on the map."""
        for r in self.routes:
            ks = r["keys"]
            i = 0
            while i < len(ks):
                j = i
                if self.nodes[ks[i]]["nerta"]:
                    while (j + 1 < len(ks) and self.nodes[ks[j + 1]]["nerta"] and j + 1 - i < 5
                           and all(_dist(self.nodes[ks[a]]["real"], self.nodes[ks[j + 1]]["real"]) < near for a in range(i, j + 1))):
                        j += 1
                if j > i:
                    run = ks[i:j + 1]
                    prev = [self.est(ks[i - 1])] if i > 0 else []
                    nxt = [self.est(ks[j + 1])] if j + 1 < len(ks) else []

                    def length(p):
                        pts = prev + [self.nodes[k]["map"] for k in p] + nxt
                        return sum(_dist(a, b) for a, b in zip(pts, pts[1:]))
                    best = min(itertools.permutations(run), key=length)
                    if list(best) != run:
                        ks[i:j + 1] = list(best)
                        self.notes.append(f"{r['id']}: {', '.join(self.nodes[k]['name'] for k in run)} are within {near:.0f} m of each other; "
                                          f"drawn in the order {', '.join(self.nodes[k]['name'] for k in best)} so the line doesn't double back")
                i = j + 1


def chains_of(net):
    """Runs of stops between anchors (NERTA stations, route ends, junctions). Returns chains as dicts with nodes and routes."""
    edges, adj, ends = {}, {}, set()
    for r in net.routes:
        ks = r["keys"]
        ends.update((ks[0], ks[-1]))
        for a, b in zip(ks, ks[1:]):
            e = (a, b) if a < b else (b, a)
            edges.setdefault(e, set()).add(r["id"])
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
    anchor = set()
    for k in adj:
        nd = net.nodes[k]
        if nd["nerta"] or k in ends or len(adj[k]) != 2:
            anchor.add(k)
            continue
        a, b = sorted(adj[k])
        if edges[(min(a, k), max(a, k))] != edges[(min(b, k), max(b, k))]:
            anchor.add(k)
    chains, done = [], set()
    for (a, b), rs in edges.items():
        if (a, b) in done:
            continue
        path = [a, b]
        while path[-1] not in anchor:
            path.append(next(n for n in adj[path[-1]] if n != path[-2]))
        while path[0] not in anchor:
            path.insert(0, next(n for n in adj[path[0]] if n != path[1]))
        for u, v in zip(path, path[1:]):
            done.add((min(u, v), max(u, v)))
        routes = sorted(rs, key=net.rank.get)
        # run the chain the way its first route travels it
        ks = next(r["keys"] for r in net.routes if r["id"] == routes[0])
        for i in range(len(ks) - 1):
            if ks[i] == path[-1] and ks[i + 1] == path[-2]:
                path = path[::-1]
                break
        chains.append(dict(nodes=path, routes=routes))
    return chains, anchor, adj


def similarity(a_real, b_real, a_map, b_map, clamp=(0.0025, 0.03)):
    """Rotate and scale real meters so a_real lands on a_map and b_real on b_map. None if the two points coincide."""
    za, zb = complex(*a_real), complex(*b_real)
    wa, wb = complex(*a_map), complex(*b_map)
    if abs(zb - za) < 30:
        return None
    s = (wb - wa) / (zb - za)
    if abs(s) < clamp[0] or abs(s) > clamp[1]:
        s = s / abs(s) * min(max(abs(s), clamp[0]), clamp[1])
    t = wa - s * za

    def T(p):
        p = np.atleast_2d(np.asarray(p, float))
        z = s * (p[:, 0] + 1j * p[:, 1]) + t
        return np.column_stack([z.real, z.imag])
    return T


# ---------------------------------------------------------------------------------------------------------------
# NERTA as obstacles
def nerta_geometry(sch):
    """Every NERTA line as the main map draws it: (color, xy, kind). kind T: rapid transit, C: commuter rail, S: Silver, D: Dig."""
    out = []
    for col, _style, path, stops in M.lines():
        out.append((col, rounded(path, 7 if "Terminals" in stops else M.CR), "T"))
    for path in M.CR_PATHS:
        out.append((M.PURPLE, rounded(path, 3), "C"))
    for spur in ([(208.5, 198.5), (176, 198.5), (160, 214.5)], [(208.5, 198.5), (214.5, 198.5)], [(-21, 143), (-24, 140), (-40, 140)],
                 [(50, -7), (78, -7)], [(34, -16), (46, -16)]):
        out.append((M.PURPLE, rounded(spur, 3), "C"))
    term = sch.get("Terminals", (148.0, 104.0))
    out.append((M.SILVER, rounded([M.FERRY_SPOTS["Logan Dock"], term, (155.3, 111.3), (155.3, 116.7), (147, 125), (135, 125)], 2.4), "S"))
    out.append((M.INK, np.array([(114.0, 120.0), (114.0, 76.0)]), "D"))
    return out


def _cls(d):
    """Octilinear class of a direction: 0 level, 1 rising, 2 upright, 3 falling."""
    return int(round((math.degrees(math.atan2(d[1], d[0])) % 180) / 45)) % 4


def _sample(xy, step):
    """Points about `step` apart along a polyline, with the class of the piece each lies on."""
    xy = np.asarray(xy, float)
    pts, cls = [], []
    for a, b in zip(xy[:-1], xy[1:]):
        L = _dist(a, b)
        if L < 1e-9:
            continue
        n = max(1, int(math.ceil(L / step)))
        t = np.linspace(0, 1, n + 1)
        pts.append(a + (b - a) * t[:, None])
        cls.append(np.full(n + 1, _cls(b - a)))
    if not pts:
        return np.zeros((0, 2)), np.zeros(0, int)
    return np.vstack(pts), np.concatenate(cls)


class Field:
    """Distance rasters on the routing lattice: NERTA lines by class, rail by class, station dots, water, trams and tram stops."""

    def __init__(self, xlim, ylim, h=H):
        self.h = h
        self.x0 = math.floor(xlim[0] / h) * h
        self.y0 = math.floor(ylim[0] / h) * h
        self.nx = int(math.ceil((xlim[1] - self.x0) / h)) + 1
        self.ny = int(math.ceil((ylim[1] - self.y0) / h)) + 1
        gx = self.x0 + h * np.arange(self.nx)
        gy = self.y0 + h * np.arange(self.ny)
        X, Y = np.meshgrid(gx, gy)
        self.P = np.column_stack([X.ravel(), Y.ravel()])
        self.shape = (self.ny, self.nx)
        inf = np.full(self.shape, np.inf, np.float32)
        self.dN = [inf.copy() for _ in range(4)]
        self.dR = [inf.copy() for _ in range(4)]
        self.dT = [inf.copy() for _ in range(4)]
        self.dD = inf.copy()
        self.dS = inf.copy()
        self.water = np.zeros(self.shape, bool)

    def ij(self, p):
        return int(round((p[0] - self.x0) / self.h)), int(round((p[1] - self.y0) / self.h))

    def xy(self, i, j):
        return np.array([self.x0 + i * self.h, self.y0 + j * self.h])

    def snap(self, p):
        return self.xy(*self.ij(p))

    def window(self, lo, hi):
        i0, j0 = self.ij(lo)
        i1, j1 = self.ij(hi)
        return max(0, i0), min(self.nx, i1 + 1), max(0, j0), min(self.ny, j1 + 1)

    def _query(self, pts, sl, cap):
        i0, i1, j0, j1 = sl
        gx = self.x0 + self.h * np.arange(i0, i1)
        gy = self.y0 + self.h * np.arange(j0, j1)
        X, Y = np.meshgrid(gx, gy)
        d, _ = cKDTree(pts).query(np.column_stack([X.ravel(), Y.ravel()]), distance_upper_bound=cap)
        return d.reshape(j1 - j0, i1 - i0).astype(np.float32)

    def line_contrib(self, xy, minus=0.0, cap=6.0):
        """Distance to one polyline's pieces of each class, less `minus`, over a window round it: (window, {class: raster})."""
        pts, cls = _sample(xy, 0.1)
        if not len(pts):
            return None
        sl = self.window(pts.min(0) - cap, pts.max(0) + cap)
        out = {}
        for c in range(4):
            m = cls == c
            if m.sum():
                out[c] = self._query(pts[m], sl, cap) - minus
        return sl, out

    def fold(self, store, contrib):
        if contrib is None:
            return
        (i0, i1, j0, j1), out = contrib
        for c, d in out.items():
            store[c][j0:j1, i0:i1] = np.minimum(store[c][j0:j1, i0:i1], d)

    def add_lines(self, store, xy, minus=0.0, cap=6.0):
        """Fold one polyline into a set of class rasters (distance to the centerline, less `minus`)."""
        self.fold(store, self.line_contrib(xy, minus, cap))

    def add_points(self, store, pts, minus=0.0, cap=6.0):
        pts = np.atleast_2d(np.asarray(pts, float))
        if not len(pts):
            return
        sl = self.window(pts.min(0) - cap, pts.max(0) + cap)
        i0, i1, j0, j1 = sl
        d = self._query(pts, sl, cap) - minus
        store[j0:j1, i0:i1] = np.minimum(store[j0:j1, i0:i1], d)


# ---------------------------------------------------------------------------------------------------------------
# Routing
def _route(F, src, dst, pen):
    """Least-cost octilinear lattice path. src, dst: {(i, j): extra cost}. pen(i0, i1, j0, j1) -> (window, (4, ny, nx) penalties).
    Returns lattice points (drawing units) from a src point to a dst point."""
    (i0, i1, j0, j1), P = pen
    nwx, nwy = i1 - i0, j1 - j0
    N = nwx * nwy
    cid = np.arange(N, dtype=np.int64).reshape(nwy, nwx)
    flat = [P[c].ravel() for c in range(4)]
    R, C, Wt = [], [], []
    for dout in range(8):
        dx, dy = DIRS[dout]
        ys0, ys1 = max(0, -dy), nwy - max(0, dy)
        xs0, xs1 = max(0, -dx), nwx - max(0, dx)
        if ys1 <= ys0 or xs1 <= xs0:
            continue
        u = cid[ys0:ys1, xs0:xs1].ravel()
        v = cid[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx].ravel()
        pc = flat[AXIS[dout]]
        base = H * DLEN[dout] * (1.0 + 0.5 * (pc[u] + pc[v]))
        for din in range(8):
            t = min((dout - din) % 8, (din - dout) % 8)
            if t > 2:
                continue
            R.append(u * 8 + din)
            C.append(v * 8 + dout)
            Wt.append(base + TURN[t])
    SRC = N * 8
    sr, sc, sw = [], [], []
    for (i, j), extra in src.items():
        ii, jj = i - i0, j - j0
        if not (0 <= ii < nwx and 0 <= jj < nwy):
            continue
        u = jj * nwx + ii
        for dout in range(8):
            vi, vj = ii + DIRS[dout][0], jj + DIRS[dout][1]
            if 0 <= vi < nwx and 0 <= vj < nwy:
                v = vj * nwx + vi
                pc = flat[AXIS[dout]]
                sr.append(SRC)
                sc.append(v * 8 + dout)
                sw.append(extra + H * DLEN[dout] * (1.0 + 0.5 * (pc[u] + pc[v])))
    R.append(np.array(sr, np.int64))
    C.append(np.array(sc, np.int64))
    Wt.append(np.array(sw, float))
    G = csr_matrix((np.concatenate(Wt), (np.concatenate(R), np.concatenate(C))), shape=(SRC + 1, SRC + 1))
    dist, pred = dijkstra(G, directed=True, indices=SRC, return_predecessors=True)
    best, state = np.inf, None
    for (i, j), extra in dst.items():
        ii, jj = i - i0, j - j0
        if not (0 <= ii < nwx and 0 <= jj < nwy):
            continue
        u = jj * nwx + ii
        d8 = dist[u * 8:u * 8 + 8] + extra
        k = int(np.argmin(d8))
        if d8[k] < best:
            best, state = d8[k], u * 8 + k
    if state is None or not np.isfinite(best):
        return None, np.inf
    cells = []
    s = state
    while True:
        u, d = divmod(s, 8)
        cells.append(u)
        p = pred[s]
        if p == SRC:
            jj, ii = divmod(u, nwx)
            cells.append((jj - DIRS[d][1]) * nwx + (ii - DIRS[d][0]))
            break
        if p < 0:
            return None, np.inf
        s = p
    cells.reverse()
    pts = np.array([F.xy(i0 + c % nwx, j0 + c // nwx) for c in cells])
    return _dejog(_simplify(pts), F, pen), best


def _dejog(pts, F=None, pen=None, h=H):
    """A one-cell side step between two long parallel runs reads as a zigzag (round-3 audit, Kenmore).
    Drop the step and run straight: the line leans a few degrees instead. Kept only when the straight run
    costs no more than the stepped one (the step may be what keeps the tram off a NERTA line)."""
    pts = [np.asarray(q, float) for q in pts]

    def cost(a, b):
        if F is None or pen is None:
            return 0.0
        (i0, i1, j0, j1), P = pen
        d = b - a
        L = float(np.hypot(*d))
        if L < 1e-9:
            return 0.0
        c = int(AXIS[int(np.argmax(DIRS @ d / DLEN))])
        n = max(2, int(L / (h / 2)) + 1)
        tot = 0.0
        for t in np.linspace(0.0, 1.0, n):
            i, j = F.ij(a + t * d)
            if i0 <= i < i1 and j0 <= j < j1:
                tot += float(P[c][j - j0, i - i0])
            else:
                tot += 1e3
        return tot * L / n

    changed = True
    while changed and len(pts) >= 4:
        changed = False
        for k in range(len(pts) - 3):
            a, b, c, d = pts[k], pts[k + 1], pts[k + 2], pts[k + 3]
            A, B, C = b - a, c - b, d - c
            la, lb, lc = np.hypot(*A), np.hypot(*B), np.hypot(*C)
            if min(la, lb, lc) < 1e-9 or lb > 1.6 * h * 1.415:
                continue
            if np.dot(A, C) / (la * lc) < 0.999 or la + lc < 8 * lb:
                continue
            if cost(a, d) > cost(a, b) + cost(b, c) + cost(c, d) + 1e-6:
                continue
            del pts[k + 1:k + 3]
            changed = True
            break
    return np.array(pts)


def _simplify(pts):
    out = [pts[0]]
    for k in range(1, len(pts) - 1):
        a, b, c = out[-1], pts[k], pts[k + 1]
        u, v = b - a, c - b
        if abs(u[0] * v[1] - u[1] * v[0]) < 1e-9 and np.dot(u, v) > 0:
            continue
        out.append(b)
    out.append(pts[-1])
    return np.array(out)


def _arclen(xy):
    return np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])


def _at(xy, s):
    """Point and unit direction at arc length s along a polyline."""
    L = _arclen(xy)
    s = float(np.clip(s, 0, L[-1]))
    k = int(np.clip(np.searchsorted(L, s, side="right") - 1, 0, len(xy) - 2))
    seg = xy[k + 1] - xy[k]
    n = np.hypot(*seg)
    t = 0.0 if n < 1e-12 else (s - L[k]) / n
    d = seg / n if n > 1e-12 else np.array([1.0, 0.0])
    return xy[k] + t * seg, d


class Layout:
    """The tram network laid out over NERTA: chains with their center lines, every route's drawn line, and every stop."""

    def __init__(self, ppu, routes=None, sheet=None, w=1.6, log=print):
        self.log = log
        self.st = Style(ppu, w)
        self.sch = nerta_positions()
        self.f, *_ = bender()
        self.net = Net(routes if routes is not None else load_routes(log), self.sch, self.f)
        self.sheet = sheet or (M.XLIM[0], M.XLIM[1], M.YLIM[0], M.YLIM[1])
        self.xlim = (self.sheet[0] - 8, self.sheet[1] + 8)
        self.ylim = (self.sheet[2] - 8, self.sheet[3] + 8)
        self.F = Field(self.xlim, self.ylim)
        self.geo = nerta_geometry(self.sch)
        self.sea = None
        self.chains, self.anchor, self.adj = chains_of(self.net)
        self.pos = {}       # node -> spot the chains meet at (NERTA: the station; tram stop: a lattice point)
        self.stops = {}     # node -> symbol: center, radius, direction, kind, routes, name
        self.problems = []
        self.shrunk = []    # crowded stretches drawn with smaller stop circles

    # -- obstacles ------------------------------------------------------------------------------------------------
    def build_fields(self, sea=None):
        st, F = self.st, self.F
        t0 = time.time()
        for _col, xy, kind in self.geo:
            if kind == "T":
                F.add_lines(F.dN, xy)
            else:
                F.add_lines(F.dR, xy)
        dots = np.array([p for n, p in self.sch.items()])
        F.add_points(F.dD, dots)
        if sea is not None:
            import shapely
            self.sea = sea
            F.water = shapely.contains_xy(sea, F.P[:, 0], F.P[:, 1]).reshape(F.shape)
        self.log(f"obstacle rasters {time.time() - t0:.1f} s")

    # -- spots for tram-only junctions and route ends ---------------------------------------------------------------
    def _sim_spot(self, k):
        """Between two stations: the real spot turned and scaled so both stations land on their map spots. Past the last
        station (a route's far end, often well out on the compressed edges of the main map): the thin-plate bend, measured
        from the nearest spot already placed, stretched until the stops fit, never doubling back, kept on the sheet."""
        net, st = self.net, self.st
        nd = net.nodes[k]
        cands = []
        for r in net.routes:
            ks = r["keys"]
            for i, kk in enumerate(ks):
                if kk != k:
                    continue
                before = [j for j in range(i - 1, -1, -1) if net.nodes[ks[j]]["nerta"]]
                after = [j for j in range(i + 1, len(ks)) if net.nodes[ks[j]]["nerta"]]
                if before and after:
                    a, b = ks[before[0]], ks[after[0]]
                    T = similarity(net.nodes[a]["real"], net.nodes[b]["real"], net.nodes[a]["map"], net.nodes[b]["map"])
                    if T is not None:
                        cands.append(T(nd["real"])[0])
                    continue
                # a tail: measure from the nearest placed spot back toward the stations
                step = -1 if before else 1
                j = i + step
                while 0 <= j < len(ks) and ks[j] not in self.pos:
                    j += step
                if not (0 <= j < len(ks)):
                    continue
                B = self.pos[ks[j]]
                fb = np.asarray(self.f([net.nodes[ks[j]]["real"], nd["real"]]), float)
                v = fb[1] - fb[0]
                n_between = abs(i - j) - 1
                # the way the tram arrives at B
                jn = j + step
                u = None
                if 0 <= jn < len(ks):
                    prev = self.pos.get(ks[jn], net.est(ks[jn]))
                    u = B - np.asarray(prev, float)
                if np.hypot(*v) < 1e-6:
                    v = u if u is not None and np.hypot(*u) > 1e-6 else np.array([1.0, 0.0])
                if u is not None and np.hypot(*u) > 1e-6:
                    cu = np.dot(u, v) / np.hypot(*u) / np.hypot(*v)
                    if cu < -0.05:   # never back on itself: turn it to 80 degrees off the way in
                        ang_u, ang_v = math.atan2(u[1], u[0]), math.atan2(v[1], v[0])
                        side = 1.0 if math.sin(ang_v - ang_u) >= 0 else -1.0
                        ang = ang_u + side * math.radians(80)
                        v = np.hypot(*v) * np.array([math.cos(ang), math.sin(ang)])
                need = max(0, n_between - 1) * max(2.75 * st.R, GAP_PREF * 6.0 / st.ppu) + 6.5 * st.R   # room for every stop at full spacing
                L = np.hypot(*v)
                if L < need:
                    v = v / L * need
                p = B + v
                cands.append(self._on_sheet(B, p))
        if cands:
            return np.mean(cands, axis=0)
        return np.asarray(self.f([nd["real"]])[0], float)

    def _on_sheet(self, B, p, pad=4.0):
        """Pull a route end back inside the sheet along its own direction, and if that leaves it too short, slide it along the edge."""
        x0, x1 = self.sheet[0] + pad, self.sheet[1] - pad
        y0, y1 = self.sheet[2] + pad, self.sheet[3] - pad
        if x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
            return p
        need = _dist(B, p)
        v = p - B
        t = 1.0
        for k, (lo, hi) in enumerate(((x0, x1), (y0, y1))):
            if v[k] > 1e-9 and p[k] > hi:
                t = min(t, (hi - B[k]) / v[k])
            if v[k] < -1e-9 and p[k] < lo:
                t = min(t, (lo - B[k]) / v[k])
        q = B + max(0.0, t) * v
        rest = need - _dist(B, q)
        if rest > 1.0:   # run along the edge, the way the route was leaning
            if q[1] <= y0 + 1e-6 or q[1] >= y1 - 1e-6:
                q = q + np.array([math.copysign(rest, v[0] if abs(v[0]) > 1e-9 else 1.0), 0.0])
            else:
                q = q + np.array([0.0, math.copysign(rest, v[1] if abs(v[1]) > 1e-9 else 1.0)])
            q = np.array([min(max(q[0], x0), x1), min(max(q[1], y0), y1)])
        return q

    def _free_spot(self, p, taken):
        """Nearest lattice point to p that is off NERTA lines, dots and other stops."""
        st, F = self.st, self.F
        need_line = st.R + st.NW / 2 + st.GAP
        need_dot = st.R + st.DOT + st.GAP
        best, bq = np.inf, None
        i, j = F.ij(p)
        rad = int(5 / F.h)
        for di in range(-rad, rad + 1):
            for dj in range(-rad, rad + 1):
                ii, jj = i + di, j + dj
                if not (0 <= ii < F.nx and 0 <= jj < F.ny):
                    continue
                q = F.xy(ii, jj)
                c = _dist(p, q)
                if min(F.dN[k][jj, ii] for k in range(4)) < need_line:
                    c += 30
                if min(F.dR[k][jj, ii] for k in range(4)) < st.R + st.CW / 2 + st.GAP:
                    c += 8
                if F.dD[jj, ii] < need_dot:
                    c += 60
                if F.water[jj, ii]:
                    c += 6
                for t in taken:
                    if _dist(q, t) < 2.6 * st.R:
                        c += 60
                if c < best:
                    best, bq = c, q
        return bq

    def place_anchors(self):
        net = self.net
        for k, nd in net.nodes.items():
            if nd["nerta"]:
                self.pos[k] = nd["map"].copy()
        taken = [self.pos[k] for k in self.pos]
        # tram-only anchors, nearest to a station first so route ends can look back along the route
        todo = [k for k in self.anchor if not net.nodes[k]["nerta"]]
        todo.sort(key=lambda k: min(_dist(net.nodes[k]["real"], net.nodes[a]["real"]) for a in net.nodes if net.nodes[a]["nerta"]) if any(
            net.nodes[a]["nerta"] for a in net.nodes) else 0)
        for k in todo:
            p = self._sim_spot(k)
            q = self._free_spot(p, taken)
            self.pos[k] = q
            taken.append(q)

    # -- one chain ---------------------------------------------------------------------------------------------------
    def _hint(self, ch):
        net = self.net
        ks = ch["nodes"]
        a, b = ks[0], ks[-1]
        P, Q = self.pos[a], self.pos[b]
        reals = np.array([net.nodes[k]["real"] for k in ks])
        T = similarity(reals[0], reals[-1], P, Q)
        if T is None:
            pts = np.asarray(self.f(reals), float)
            pts[0], pts[-1] = P, Q
            return pts
        return T(reals)

    def _end_cells(self, k, P, chain_k):
        """Lattice points a chain may start or end on: a tram stop's own point, or any point under a station's circle."""
        st, F = self.st, self.F
        nd = self.net.nodes[k]
        if not nd["nerta"]:
            return {F.ij(P): 0.0}
        r_end = max(0.0, st.R - st.W / 2 - 0.12 - (chain_k - 1) * st.S / 2)
        i, j = F.ij(P)
        rad = int(math.ceil(r_end / F.h)) + 1
        out = {}
        for di in range(-rad, rad + 1):
            for dj in range(-rad, rad + 1):
                q = F.xy(i + di, j + dj)
                d = _dist(q, P)
                if d <= r_end:
                    out[(i + di, j + dj)] = 2.0 * d   # off center costs a little
        if not out:
            out[(i, j)] = 0.0
        return out

    def _penalties(self, ch, P, Q, hint, margin=7.0):
        st, F = self.st, self.F
        k = len(ch["routes"])
        half = (k - 1) * st.S / 2 + st.W / 2
        lo = np.minimum(np.min(hint, axis=0), np.minimum(P, Q)) - margin
        hi = np.maximum(np.max(hint, axis=0), np.maximum(P, Q)) + margin
        i0, i1, j0, j1 = F.window(lo, hi)
        sl = (slice(j0, j1), slice(i0, i1))
        shp = (j1 - j0, i1 - i0)
        pen = np.zeros((4,) + shp, np.float32)
        clrN = st.NW / 2 + st.GAP + half
        clrR = st.CW / 2 + st.GAP + half
        clrT = st.GAP + half + 0.7   # a little more room than needed, so trams on different streets read apart
        for c in range(4):
            nN = F.dN[c][sl] < clrN
            nR = F.dR[c][sl] < clrR
            nT = F.dT[c][sl] < clrT
            for m in range(4):
                rel = (m - c) % 4
                pen[m] += nN * P_NERTA[rel] + nR * P_RAIL[rel] + nT * P_TRAM[rel]
        common = (F.dD[sl] < st.DOT + st.GAP + half) * P_DOT + (F.dS[sl] < st.GAP + half) * P_STOP + F.water[sl] * P_WATER
        gx = F.x0 + F.h * np.arange(i0, i1)
        gy = F.y0 + F.h * np.arange(j0, j1)
        X, Y = np.meshgrid(gx, gy)
        pts = np.column_stack([X.ravel(), Y.ravel()])
        hs, _ = _sample(hint, 0.25)
        if len(hs):
            dh, _ = cKDTree(hs).query(pts)
            common = common + (W_HINT * np.maximum(0, dh - TOL_HINT)).reshape(shp)
        pen += common[None]
        # a chain with its stops close together reads better on a slant or upright: level names side by side would collide
        n_in = len(ch["nodes"]) - 2
        if n_in >= 3 and _dist(P, Q) / (n_in + 1) < 5.0:
            pen[0] += 0.9
        # under the end circles nothing counts
        for E, kk in ((P, ch["nodes"][0]), (Q, ch["nodes"][-1])):
            r = st.R * (1.25 if self.net.nodes[kk]["nerta"] else 1.0) + half
            near = (np.hypot(X - E[0], Y - E[1]) < r)
            pen[:, near] = 0
        return (i0, i1, j0, j1), pen

    def route_chain(self, ch):
        st, F = self.st, self.F
        a, b = ch["nodes"][0], ch["nodes"][-1]
        P, Q = self.pos[a], self.pos[b]
        k = len(ch["routes"])
        if _dist(P, Q) < 2 * F.h:
            ch["path"] = np.array([P, Q])
            return
        hint = self._hint(ch)
        src = self._end_cells(a, P, k)
        dst = self._end_cells(b, Q, k)
        path, cost = None, np.inf
        for margin in (7.0, 16.0):
            pen = self._penalties(ch, P, Q, hint, margin)
            path, cost = _route(F, src, dst, pen)
            if path is not None:
                break
        if path is None:
            self.problems.append(f"no lattice path for chain {self.net.nodes[a]['name']} - {self.net.nodes[b]['name']}; drawn straight")
            path = np.array([P, Q])
        # two stations too close together on the main map for the stops between them: swing out through a turning point
        n_in = len(ch["nodes"]) - 2
        need = (n_in + 1) * 2.8 * st.R + 2 * st.R
        have = float(_arclen(path)[-1])
        if SWING and n_in and have < need * 0.92:
            mid, d = (P + Q) / 2, Q - P
            nrm = np.array([-d[1], d[0]]) / (np.hypot(*d) or 1)
            side = 1.0 if np.dot(np.mean(hint, axis=0) - mid, nrm) >= 0 else -1.0
            reach = math.sqrt(max(0.0, (need / 2.2) ** 2 - (np.hypot(*d) / 2) ** 2))
            best = None
            for sgn in (side, -side):
                Wp = F.snap(mid + sgn * nrm * reach)
                wcell = {F.ij(Wp): 0.0}
                p1, c1 = _route(F, src, wcell, self._penalties(ch, P, Wp, np.array([P, Wp]), 8.0))
                if p1 is None:
                    continue
                keep = [d_.copy() for d_ in F.dT]   # the way back keeps clear of the way out: a U, never doubled back
                F.fold(F.dT, F.line_contrib(p1, minus=st.W / 2))
                p2, c2 = _route(F, wcell, dst, self._penalties(ch, Wp, Q, np.array([Wp, Q]), 8.0))
                F.dT = keep
                if p1 is not None and p2 is not None and (best is None or c1 + c2 < best[0]):
                    best = (c1 + c2, _simplify(np.vstack([p1, p2[1:]])))
            if best is not None:
                path, cost = best[1], best[0]
                self.problems.append(f"chain {self.net.nodes[a]['name']} - {self.net.nodes[b]['name']}: {n_in} stops between stations "
                                     f"{_dist(P, Q):.1f} units apart; the tram swings out to fit them")
        ch["path"], ch["cost"] = path, cost

    def commit_chain(self, ch):
        """Make a routed chain an obstacle for the chains after it."""
        st, F = self.st, self.F
        k = len(ch["routes"])
        half = (k - 1) * st.S / 2 + st.W / 2
        ch["contrib"] = F.line_contrib(ch["path"], minus=half)
        F.fold(F.dT, ch["contrib"])

    def trams_except(self, skip):
        """Rebuild the tram rasters from every routed chain but `skip`."""
        F = self.F
        F.dT = [np.full(F.shape, np.inf, np.float32) for _ in range(4)]
        for o in self.chains:
            if o is not skip and o.get("contrib") is not None:
                F.fold(F.dT, o["contrib"])

    # -- stops along a chain ------------------------------------------------------------------------------------------
    def place_stops(self, ch):
        """Spread the chain's tram-only stops along its line, in proportion to real distance, off bends, crossings and dots."""
        st, F, net = self.st, self.F, self.net
        ks = ch["nodes"]
        inner = ks[1:-1]
        ch["stop_s"] = {}
        if not inner:
            return
        xy = rounded(ch["path"], CORNER, n=8) if len(ch["path"]) > 2 else ch["path"]
        ch["xy"] = xy
        L = _arclen(xy)[-1]
        k = len(ch["routes"])
        half = (k - 1) * st.S / 2 + st.W / 2
        r_sym = max(st.R, half + 0.6 * st.W)
        ra = self._end_room(ks[0], k)
        rb = self._end_room(ks[-1], k)
        reals = np.array([net.nodes[n]["real"] for n in ks])
        cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(reals, axis=0).T))])
        frac = cum / cum[-1] if cum[-1] > 0 else np.linspace(0, 1, len(ks))
        n = len(inner)
        shrunk = False
        r0 = r_sym
        while True:   # on this map only, a crowded stretch gets smaller stop circles, evenly spaced (coordinator, round 3)
            s_lo, s_hi = ra + 1.15 * r_sym + 0.35, L - rb - 1.15 * r_sym - 0.35   # clear paper between a stop and the station circle beside it
            gap = 2.55 * r_sym + 0.3
            if s_hi - s_lo >= (n - 1) * gap - 1e-9 or r_sym <= 0.55 * r0:
                break
            r_sym *= 0.96
            shrunk = True
        if not shrunk and n > 1 and (n - 1) * GAP_PREF * 6.0 / st.ppu <= s_hi - s_lo:
            gap = max(gap, GAP_PREF * 6.0 / st.ppu)   # round-2 audit: room for a level name beside each stop, even on a 45-degree line
        if s_hi - s_lo < (n - 1) * gap:
            self.problems.append(f"chain {net.nodes[ks[0]]['name']} - {net.nodes[ks[-1]]['name']}: {n} stops in {L:.1f} units, stops crowd")
            s_lo, s_hi = ra + 0.9 * r_sym, L - rb - 0.9 * r_sym   # still clear of the station circles; the stops close up instead
            gap = (s_hi - s_lo) / max(1, n - 1) if n > 1 else 0
        if shrunk:
            self.shrunk.append((net.nodes[ks[0]]["name"], net.nodes[ks[-1]]["name"], n, r_sym / st.R))
        ideal = s_lo + (s_hi - s_lo) * frac[1:-1]   # spread over the room between the end circles, by real distance
        grid = np.arange(max(0.0, s_lo), max(s_lo, s_hi) + 1e-9, 0.1)
        if not len(grid):
            grid = np.array([L / 2])
        bad = np.zeros(len(grid))
        verts = ch["path"][1:-1]
        cps = np.array([_at(xy, s)[0] for s in grid])
        for v in verts:
            bad += 15.0 * (np.hypot(*(cps - v).T) < CORNER + 0.4 * r_sym)
        ii = np.clip(((cps[:, 0] - F.x0) / F.h).round().astype(int), 0, F.nx - 1)
        jj = np.clip(((cps[:, 1] - F.y0) / F.h).round().astype(int), 0, F.ny - 1)
        dN = np.min([F.dN[c][jj, ii] for c in range(4)], axis=0)
        dR = np.min([F.dR[c][jj, ii] for c in range(4)], axis=0)
        dT = np.min([F.dT[c][jj, ii] for c in range(4)], axis=0)
        bad += 25.0 * (dN < st.ARM * r_sym + st.NW / 2)
        bad += 6.0 * (dR < r_sym + st.CW / 2)
        bad += 60.0 * (F.dD[jj, ii] < r_sym + st.DOT + st.GAP)
        bad += 1000.0 * (F.dS[jj, ii] < r_sym * 1.6) + 40.0 * (F.dS[jj, ii] < r_sym * 2.4)   # clear of every other stop
        bad += 120.0 * (dT < st.ARM * r_sym + 0.2)
        # dynamic program: in order, at least `gap` apart, near the ideal, off the bad spots
        ng = len(grid)
        cost = np.full((n, ng), np.inf)
        back = np.zeros((n, ng), int)
        w = 1.0 / max(1.0, L / 10)
        cost[0] = w * (grid - ideal[0]) ** 2 + bad
        step = int(round(gap / 0.1))
        for i in range(1, n):
            prev = cost[i - 1]
            pm = np.minimum.accumulate(prev)
            arg = np.zeros(ng, int)
            best_k = 0
            for g in range(ng):
                if prev[g] <= prev[best_k]:
                    best_k = g
                arg[g] = best_k
            for g in range(ng):
                h = g - step
                if h < 0:
                    continue
                cost[i, g] = pm[h] + w * (grid[g] - ideal[i]) ** 2 + bad[g]
                back[i, g] = arg[h]
        g = int(np.argmin(cost[-1]))
        if shrunk or not np.isfinite(cost[-1, g]):
            sel = list(np.linspace(s_lo, s_hi, n)) if n > 1 else [(s_lo + s_hi) / 2]
        else:
            sel = [0] * n
            for i in range(n - 1, -1, -1):
                sel[i] = grid[g]
                g = back[i, g]
        for kname, s in zip(inner, sel):
            ch["stop_s"][kname] = float(s)
            p, d = _at(xy, s)
            self.stops[kname] = dict(center=p, dir=d, r=r_sym, kind="tram", chain=ch)
            F.add_points(F.dS, [p], minus=st.ARM * r_sym)

    def _end_room(self, k, kk):
        st = self.st
        nd = self.net.nodes[k]
        return st.R * (1.35 if nd["nerta"] else 1.05) + (kk - 1) * st.S / 2

    # -- whole network -------------------------------------------------------------------------------------------------
    def run(self, sea=None, passes=2):
        st, F, net = self.st, self.F, self.net
        self.build_fields(sea)
        self.place_anchors()
        # every station a tram calls at is a stop circle the other trams keep out of
        anchors_xy = [self.pos[k] for k in self.anchor]
        F.add_points(F.dS, anchors_xy, minus=st.R)
        for a_, b_ in M.CAPSULES:   # station capsules: tram stops keep off them
            a_, b_ = np.asarray(a_, float), np.asarray(b_, float)
            pts = a_ + np.linspace(0, 1, max(2, int(_dist(a_, b_) / 0.2) + 1))[:, None] * (b_ - a_)
            F.add_points(F.dS, pts, minus=st.DOT * 1.45)
        order = sorted(self.chains, key=lambda c: (-len(c["routes"]), -_dist(self.pos[c["nodes"][0]], self.pos[c["nodes"][-1]])))
        t0 = time.time()
        for ch in order:
            self.route_chain(ch)
            self.commit_chain(ch)
        self.log(f"routed {len(order)} chains in {time.time() - t0:.1f} s")
        for p in range(1, passes):   # rip up and reroute each chain with all the others in place
            t0 = time.time()
            for ch in order:
                self.trams_except(ch)
                self.route_chain(ch)
                self.commit_chain(ch)
            self.log(f"pass {p + 1}: {time.time() - t0:.1f} s")
        for ch in order:
            self._trim_ends(ch)
        for ch in order:
            self.trams_except(ch)
            self.place_stops(ch)
        self.trams_except(None)
        self.finish()
        self.repel()
        return self

    def _trim_ends(self, ch):
        """A bend just outside a station circle would curl round its edge: run the last leg straight into the circle."""
        st, net = self.st, self.net
        p = [np.asarray(q, float) for q in ch["path"]]
        for end in (0, -1):
            k_end = ch["nodes"][end]
            if net.nodes[k_end]["nerta"] and len(p) > 2:
                nb = 1 if end == 0 else -2
                if _dist(p[nb], self.pos[k_end]) < st.R * 1.6:
                    del p[nb]
        ch["path"] = np.array(p)
        ch.pop("xy", None)

    def finish(self):
        """Each route's drawn line (offset within shared chains), and the symbol for every anchor."""
        st, net = self.st, self.net
        ends_at = {}   # anchor -> list of (route, line end point, direction into the anchor)
        self.lines = {}
        for ch in self.chains:
            ch.setdefault("xy", rounded(ch["path"], CORNER, n=8) if len(ch["path"]) > 2 else np.asarray(ch["path"], float))
            k = len(ch["routes"])
            ch["offset"] = {}
            base = LineString(ch["xy"])
            for i, rid in enumerate(ch["routes"]):
                o = (i - (k - 1) / 2) * st.S
                if abs(o) < 1e-9 or base.length < 1e-6:
                    off = np.asarray(ch["xy"], float)
                else:
                    g = base.offset_curve(o, quad_segs=8, join_style="round")
                    if g.geom_type != "LineString" or g.is_empty:
                        off = np.asarray(ch["xy"], float)
                    else:
                        off = np.array(g.coords)
                        if _dist(off[0], ch["xy"][0]) > _dist(off[-1], ch["xy"][0]):
                            off = off[::-1]
                ch["offset"][rid] = off
        for r in net.routes:
            ks = r["keys"]
            parts = []
            for a, b in zip(ks, ks[1:]):
                ch, rev = self._chain_for(a, b)
                if ch is None:
                    continue
                if parts and parts[-1][0] is ch:
                    continue
                parts.append((ch, rev))
            seq = []
            for ch, rev in parts:
                off = ch["offset"][r["id"]]
                off = off[::-1] if rev else off
                a, b = (ch["nodes"][-1], ch["nodes"][0]) if rev else (ch["nodes"][0], ch["nodes"][-1])
                ends_at.setdefault(a, []).append((r["id"], off[0], off[min(1, len(off) - 1)] - off[0]))
                ends_at.setdefault(b, []).append((r["id"], off[-1], off[-1] - off[max(0, len(off) - 2)]))
                seq.append(off)
            line = np.vstack(seq) if seq else np.zeros((0, 2))
            self.lines[r["id"]] = line
        for k in self.anchor:
            nd = net.nodes[k]
            got = ends_at.get(k, [])
            if not got:
                continue
            P = self.pos[k]
            E = np.array([g[1] for g in got])
            c = E.mean(axis=0)
            if np.max(np.hypot(*(E - P).T)) < 0.35:
                c = P.copy()
            need = max(np.max(np.hypot(*(E - c).T)) + st.W / 2 + 0.08, (_dist(P, c) + st.DOT * 0.8) if nd["nerta"] else 0)
            r = max(st.R, need)
            dirs = [g[2] / (np.hypot(*g[2]) or 1) for g in got]
            d = dirs[0]
            self.stops[k] = dict(center=c, dir=d, r=r, kind="transfer" if nd["nerta"] else "tram", routes=sorted({g[0] for g in got}, key=net.rank.get))
        for k, s in self.stops.items():
            s["name"] = net.nodes[k]["name"]
            s["key"] = k
            s.setdefault("routes", [rid for rid in net.nodes[k]["routes"]])
            s["nerta"] = net.nodes[k]["nerta"]
        self.route_ends = {}
        for r in net.routes:
            for k in (r["keys"][0], r["keys"][-1]):
                self.route_ends.setdefault(k, []).append(r["id"])

    def _shape(self, c, r, d):
        """A stop as the overlap check sees it: the circle and the arm across the track."""
        u = np.asarray(d, float) / (np.hypot(*d) or 1)
        v = np.array([-u[1], u[0]])
        reach = self.st.ARM * r
        return Point(c).buffer(r + 0.12).union(LineString([c - v * reach, c + v * reach]).buffer(0.16))

    def repel(self, rounds=3):
        """Slide a tram-only stop along its own line, between its neighbors, until it clears every other stop (round 4)."""
        st = self.st
        keys = list(self.stops)
        for _ in range(rounds):
            moved = 0
            shapes = {k: self._shape(s["center"], s["r"], s["dir"]) for k, s in self.stops.items()}
            for k in keys:
                s = self.stops[k]
                ch = s.get("chain")
                if ch is None or k not in ch.get("stop_s", {}):
                    continue
                me = shapes[k]
                hits = [o for o in keys if o != k and shapes[o].intersection(me).area > 0.01]
                if not hits:
                    continue
                xy = ch["xy"]
                L = _arclen(xy)[-1]
                order = sorted(ch["stop_s"], key=ch["stop_s"].get)
                i = order.index(k)
                r = s["r"]
                lo = ch["stop_s"][order[i - 1]] + 2.3 * r if i > 0 else self._end_room(ch["nodes"][0], len(ch["routes"])) + 1.15 * r
                hi = ch["stop_s"][order[i + 1]] - 2.3 * r if i + 1 < len(order) else L - self._end_room(ch["nodes"][-1], len(ch["routes"])) - 1.15 * r
                if hi <= lo:
                    continue
                best = None
                near = [o for o in keys if o != k and np.hypot(*(self.stops[o]["center"] - s["center"])) < 12]
                for sv in np.linspace(lo, hi, max(2, int((hi - lo) / 0.05))):
                    p_, d_ = _at(xy, sv)
                    shp = self._shape(p_, r, d_)
                    bad = sum(shapes[o].intersection(shp).area for o in near)
                    score = bad * 100 + abs(sv - ch["stop_s"][k]) * 0.05
                    if best is None or score < best[0]:
                        best = (score, sv, p_, d_, shp)
                if best is not None and best[1] != ch["stop_s"][k]:
                    ch["stop_s"][k] = float(best[1])
                    s["center"], s["dir"] = best[2], best[3]
                    shapes[k] = best[4]
                    moved += 1
            if not moved:
                break

    def _chain_for(self, a, b):
        for ch in self.chains:
            ns = ch["nodes"]
            for i in range(len(ns) - 1):
                if ns[i] == a and ns[i + 1] == b:
                    return ch, False
                if ns[i] == b and ns[i + 1] == a:
                    return ch, True
        return None, False


# ---------------------------------------------------------------------------------------------------------------
def main():
    f, names, src, dst = bender()
    err = np.hypot(*(f(src * 1000) - dst).T)
    print(f"{len(names)} control stations; bend error median {np.median(err):.1f} units, 90th pct {np.percentile(err, 90):.1f}, max {err.max():.1f}")
    for i in np.argsort(-err)[:8]:
        print(f"  {names[i]:24s} off by {err[i]:.1f}")
    if "--plot" in sys.argv:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        trams = load_routes()
        fig, ax = plt.subplots(figsize=(14, 12))
        for col, _st, path, _stops in M.lines():
            xy = rounded(path, M.CR)
            ax.plot(*xy.T, color=col, lw=3, alpha=0.35)
        if "--raw" in sys.argv:
            for r in trams:
                p = f([xy_m(*c) for c in r["path"]])
                ax.plot(*p.T, color=TRAM, lw=1.2, alpha=0.4)
        lay = Layout(4.836, trams).run()
        for rid, line in lay.lines.items():
            ax.plot(*line.T, color=TRAM, lw=1.6)
        for k, s in lay.stops.items():
            ax.scatter(*s["center"], s=14, color="white", edgecolor=TRAM, zorder=5)
        ax.set_aspect("equal")
        ax.set_xlim(*M.XLIM)
        ax.set_ylim(*M.YLIM)
        out = sys.argv[sys.argv.index("--plot") + 1]
        fig.savefig(out, dpi=110, bbox_inches="tight")
        print("plot", out)


if __name__ == "__main__":
    main()
