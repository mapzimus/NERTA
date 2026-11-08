"""Real-geography track for the regional commuter rail map.

Writes boston-map/data/rail_regional/lines.geojson (WGS84): one LineString per line piece, running OUTBOUND, so its first
coordinate is at North or South Station, at the start of a crosstown line, or on the parent line for a branch. Properties:
    line        fit, low, hav, nbp, pea, wor, fra, pro, fr, kin, grb, hmon, hmai, halb, hnyc
    piece       "main" or the branch name
    end         "end", or "runs_on" when the line carries on past the map (the renderer draws an arrow at the last point)
    sources     where the geometry came from
    straight_m  meters of straight line we drew ourselves: no track in either source, or a snap between sources

Commuter pieces start from the MBTA route shapes. Extensions and branches with no MBTA shape are routed with Dijkstra over one
graph built from today's OpenStreetMap track plus the 1826-1911 historic railroads; a leg with no track, or only track more
than DETOUR times the straight distance, becomes a straight link. Pieces that share an MBTA shape share its vertices exactly
(the Peabody line uses the Newburyport and Haverhill shapes' own vertices where it runs on their track). A branch's first
coordinate is a vertex of its parent: the junction station's point, or, where the branch's track really leaves the parent
somewhere else, that point, so the branch never repeats the parent's track.

    python boston-map/src/rail_regional_lines.py
"""
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely
from pyproj import Transformer
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point
from shapely.ops import substring

ROOT = Path(__file__).resolve().parents[2]
BM = ROOT / "boston-map"
OUT = BM / "data" / "rail_regional" / "lines.geojson"

CRS_M = 26986                     # Massachusetts State Plane, meters
FRAME = (-71.98, 41.50, -70.22, 42.92)
PAD = 30_000                      # the graph covers the frame plus this much (and every waypoint)
DENSE = 50.0                      # densify track to this spacing first, so a feature's end finds a vertex to join
JOIN = 60.0                       # join each feature's ends to the nearest vertex of another feature within this
JOIN_COST = 25.0                  # extra cost per join, so a route doesn't hop between parallel datasets for nothing
DETOUR = 1.8                      # a leg longer than this times the straight distance becomes a straight link
SIMPLIFY = 15.0
SPIKE_TURN, SPIKE_LEN = 85.0, 80.0    # drop zigzags: a turn sharper than this next to a segment shorter than this
LAM_END, LAM_VIA = 4.0, 2.0       # cost per meter that a route's end / via node sits from its waypoint
VIA_R = 2500.0                    # look this far for a route node near a waypoint
NEAR_PARENT = 25.0                # a branch point this close to its parent is on the parent's track
NEAR_HOST = 60.0                  # the Peabody line runs on Newburyport / Haverhill track within this
SHARE_OK = 150.0                  # a branch whose track runs along its parent longer than this starts where they part
PROFILES = {"today": (1.0, 1.15), "historic": (1.3, 1.0)}   # cost per meter on OSM / historic track

# Given points (lon, lat). Real stops come from mbta_stops.gpkg by name.
WP = {
    "Gardner": (-71.998, 42.575), "Athol": (-72.227, 42.594),
    "Hudson": (-71.5677, 42.3914), "Marlborough": (-71.5525, 42.3469),
    "Nashua": (-71.4676, 42.7654), "Manchester": (-71.4635, 42.9956),
    "Exeter": (-70.9468, 42.9814),
    "Marblehead": (-70.8578, 42.5001), "Clifton": (-70.8800, 42.4834), "South Salem": (-70.8926, 42.5112),
    "Peabody": (-70.9272, 42.5259), "Danvers": (-70.9356, 42.5657), "Middleton": (-71.0159, 42.5951),
    "Springfield": (-72.593, 42.106),
    "Taunton": (-71.0931, 41.9019),
    "Westerly": (-71.8273, 41.3776),
    "Cape Cod Canal bridge": (-70.6178, 41.7417),
    "Plymouth": (-70.6904, 41.9812),
    "Cotley Junction": (-70.7189, 41.9940),          # where the Plymouth Branch leaves the Kingston spur (OSM)
    "Marblehead station": (-70.856398, 42.50238),    # the station spot in stations.geojson (two sources)
}

SHAPES = {
    "fit": ("CR-Fitchburg", "North Station - Wachusett"),
    "low": ("CR-Lowell", "North Station - Lowell"),
    "hav": ("CR-Haverhill", "North Station - Haverhill via Reading"),
    "nbp": ("CR-Newburyport", "North Station - Newburyport"),
    "rock": ("CR-Newburyport", "North Station - Rockport"),
    "wor": ("CR-Worcester", "South Station - Worcester"),
    "fra": ("CR-Franklin", "South Station - Forge Park/495 via Back Bay"),
    "fox": ("CR-Foxboro", "Foxboro - Providence"),
    "pro": ("CR-Providence", "South Station - Wickford Junction via Back Bay"),
    "sto": ("CR-Providence", "South Station - Stoughton via Back Bay"),
    "nb": ("CR-NewBedford", "South Station - New Bedford"),
    "fall": ("CR-NewBedford", "South Station - Fall River Depot"),
    "kin": ("CR-Kingston", "South Station - Kingston"),
    "grb": ("CR-Greenbush", "South Station - Greenbush"),
}

TO_M = Transformer.from_crs(4326, CRS_M, always_xy=True)
TO_LL = Transformer.from_crs(CRS_M, 4326, always_xy=True)
LOG = []


def m(lonlat):
    return tuple(map(float, TO_M.transform(*lonlat)))


def dist(a, b):
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


# ---------------------------------------------------------------------------------------------------------------------
# Polylines
class Part:
    """A polyline of our own: routed, or a clipped MBTA shape. lab[i] names the source of the segment that ends at p[i]."""

    def __init__(self, p, lab):
        self.p = [tuple(map(float, q)) for q in p]
        self.lab = list(lab)

    def seglen(self):
        return np.hypot(*np.diff(np.asarray(self.p), axis=0).T)

    def length(self):
        return float(self.seglen().sum()) if len(self.p) > 1 else 0.0

    def slice(self, i, j):
        return Part(self.p[i:j + 1], [None] + self.lab[i + 1:j + 1])

    def cut_from(self, q):
        """The part from the point nearest q onward."""
        ls = LineString(self.p)
        s = ls.project(Point(q))
        cum = np.r_[0.0, np.cumsum(self.seglen())]
        i = min(int(np.searchsorted(cum, s, side="right")) - 1, len(self.p) - 2)
        x = ls.interpolate(s)
        p, lab = [(x.x, x.y)] + self.p[i + 1:], [None] + self.lab[i + 1:]
        if dist(p[0], p[1]) < 1e-6:
            p, lab = p[1:], [None] + lab[2:]
        return Part(p, lab)

    def simplified(self):
        """Simplified to SIMPLIFY, then without the little zigzags left where a route steps between datasets: an inner
        vertex that turns more than SPIKE_TURN degrees next to a segment shorter than SPIKE_LEN goes."""
        q = list(LineString(self.p).simplify(SIMPLIFY, preserve_topology=False).coords)
        q[0], q[-1] = self.p[0], self.p[-1]
        q = [tuple(map(float, x)) for x in q]
        changed = True
        while changed and len(q) > 2:
            changed = False
            for i in range(1, len(q) - 1):
                a, b, c = np.asarray(q[i - 1]), np.asarray(q[i]), np.asarray(q[i + 1])
                u, v = b - a, c - b
                lu, lv = np.hypot(*u), np.hypot(*v)
                if min(lu, lv) < SPIKE_LEN:
                    turn = np.degrees(np.arccos(np.clip(np.dot(u, v) / max(lu * lv, 1e-9), -1, 1)))
                    if turn > SPIKE_TURN:
                        del q[i]
                        changed = True
                        break
        return q


class Canon:
    """A simplified MBTA shape that pieces share. Junction points become vertices, so a branch starts exactly on it."""

    def __init__(self, coords, sid):
        self.c = [tuple(map(float, q)) for q in coords]
        self.sid = sid

    @property
    def ls(self):
        return LineString(self.c)

    def at(self, q):
        """Insert the point of the shape nearest q as a vertex (or reuse a vertex within 0.5 m) and return it."""
        s = self.ls.project(Point(q))
        a = np.asarray(self.c)
        seg = np.hypot(*np.diff(a, axis=0).T)
        cum = np.r_[0.0, np.cumsum(seg)]
        if s <= 0:
            return self.c[0]
        if s >= cum[-1]:
            return self.c[-1]
        i = min(int(np.searchsorted(cum, s, side="right")) - 1, len(self.c) - 2)
        t = (s - cum[i]) / seg[i] if seg[i] > 0 else 0.0
        x = tuple(map(float, a[i] + t * (a[i + 1] - a[i])))
        for j in (i, i + 1):
            if dist(x, self.c[j]) < 0.5:
                return self.c[j]
        self.c.insert(i + 1, x)
        return x

    def between(self, p, q):
        i, j = self.c.index(p), self.c.index(q)
        return self.c[i:j + 1] if i <= j else self.c[j:i + 1][::-1]


# ---------------------------------------------------------------------------------------------------------------------
# Track graph
class Graph:
    def __init__(self, feats):
        """feats: (LineString, kind 0 OSM / 1 historic, label)."""
        geoms = shapely.segmentize(np.array([f[0] for f in feats], dtype=object), DENSE)
        xy, fid = shapely.get_coordinates(geoms, return_index=True)
        self.flab = [f[2] for f in feats]
        fkind = np.array([f[1] for f in feats])
        self.xy, node = np.unique(np.round(xy, 2), axis=0, return_inverse=True)
        node = node.ravel()
        N = self.N = len(self.xy)
        same = fid[1:] == fid[:-1]
        u, v, f = node[:-1][same], node[1:][same], fid[:-1][same]
        kind = fkind[f]
        # Join each feature's two ends to the nearest vertex of another feature, in each dataset, within JOIN
        first = np.r_[0, np.flatnonzero(~same) + 1]
        ends = np.r_[first, np.r_[first[1:], len(fid)] - 1]
        ju, jv = [], []
        vkind = fkind[fid]
        for k in (0, 1):
            idx = np.flatnonzero(vkind == k)
            tree = cKDTree(xy[idx])
            for e, cand in zip(ends, tree.query_ball_point(xy[ends], JOIN)):
                if not cand:
                    continue
                cand = idx[cand]
                cand = cand[fid[cand] != fid[e]]
                if not len(cand):
                    continue
                j = cand[np.argmin(np.hypot(*(xy[cand] - xy[e]).T))]
                if node[j] != node[e]:
                    ju.append(node[e])
                    jv.append(node[j])
        u, v = np.r_[u, ju].astype(np.int64), np.r_[v, jv].astype(np.int64)
        f = np.r_[f, np.full(len(ju), -1)]
        kind = np.r_[kind, np.full(len(ju), 2)]
        ok = u != v
        u, v, f, kind = u[ok], v[ok], f[ok], kind[ok]
        ln = np.hypot(*(self.xy[u] - self.xy[v]).T)
        a, b = np.minimum(u, v), np.maximum(u, v)
        ek = a * N + b
        order = np.lexsort((ln, ek))
        ek, a, b, f, kind, ln = (x[order] for x in (ek, a, b, f, kind, ln))
        keep = np.r_[True, ek[1:] != ek[:-1]]
        self.ek, self.ea, self.eb, self.ef, self.ekind, self.eln = (x[keep] for x in (ek, a, b, f, kind, ln))
        self.tree = cKDTree(self.xy)
        self.mats = {}
        for name, (mo, mh) in PROFILES.items():
            w = self.eln * np.choose(self.ekind, [mo, mh, 1.0]) + JOIN_COST * (self.ekind == 2)
            w = np.maximum(w, 1e-3)
            self.mats[name] = csr_matrix((np.r_[w, w], (np.r_[self.ea, self.eb], np.r_[self.eb, self.ea])), shape=(N, N))
        print(f"graph: {N} nodes, {len(self.ek)} edges ({len(ju)} joins)")

    def nearest(self, q):
        return int(self.tree.query(q)[1])

    def sp(self, prof, src):
        return dijkstra(self.mats[prof], directed=True, indices=src, return_predecessors=True)

    def choose(self, q, dists, lam):
        """The node near q that is cheapest to route through: path cost plus lam times its distance from q."""
        cand = np.asarray(self.tree.query_ball_point(q, VIA_R), dtype=np.int64)
        if not len(cand):
            return self.nearest(q)
        cost = lam * np.hypot(*(self.xy[cand] - np.asarray(q)).T)
        for d in dists:
            cost = cost + d[cand]
        if not np.isfinite(cost).any():
            return self.nearest(q)
        return int(cand[np.argmin(cost)])

    def edge(self, a, b):
        a, b = int(a), int(b)
        k = min(a, b) * self.N + max(a, b)
        i = int(np.searchsorted(self.ek, k))
        assert self.ek[i] == k
        return i

    def label(self, a, b):
        i = self.edge(a, b)
        return "join" if self.ekind[i] == 2 else self.flab[self.ef[i]]

    def route(self, pts, prof, name, end=None, lam_end=LAM_END):
        """Route through metric points pts (first and last are ends, the rest via points). Returns a Part."""
        near = [self.nearest(q) for q in pts]
        c = self.choose(pts[0], [self.sp(prof, near[1])[0]], LAM_END)
        seq = [(c, None)]
        for i in range(1, len(pts)):
            dc, pc = self.sp(prof, c)
            if i == len(pts) - 1:
                t = end if end is not None else self.choose(pts[i], [dc], lam_end)
            else:
                t = self.choose(pts[i], [dc, self.sp(prof, near[i + 1])[0]], LAM_VIA)
            nodes = [t]
            while nodes[-1] != c and nodes[-1] >= 0:
                nodes.append(pc[nodes[-1]])
            nodes = nodes[::-1] if nodes[-1] == c else None
            straight = dist(self.xy[c], self.xy[t])
            plen = np.inf if nodes is None else sum(self.eln[self.edge(a, b)] for a, b in zip(nodes, nodes[1:]))
            if nodes is None or plen > DETOUR * max(straight, 1.0):
                LOG.append(f"{name}: leg {i} has no track within {DETOUR}x ({straight:.0f} m straight, track "
                           f"{plen:.0f} m), drawn as a straight link")
                seq.append((t, "straight"))
            else:
                seq += [(b, self.label(a, b)) for a, b in zip(nodes, nodes[1:])]
            c = t
        out = []   # drop out-and-back spurs where legs meet
        for nd, lab in seq:
            if out and out[-1][0] == nd:
                continue
            if len(out) >= 2 and out[-2][0] == nd:
                out.pop()
                continue
            out.append((nd, lab))
        return Part([tuple(self.xy[nd]) for nd, _ in out], [lab for _, lab in out])


# ---------------------------------------------------------------------------------------------------------------------
# Pieces
def run_from_start(part, line_m, d):
    """Index of the last point of the run, from the start, within d of line_m."""
    k = 0
    while k + 1 < len(part.p) and line_m.distance(Point(part.p[k + 1])) <= d:
        k += 1
    return k


def run_from_end(part, line_m, d):
    k = len(part.p) - 1
    while k - 1 >= 0 and line_m.distance(Point(part.p[k - 1])) <= d:
        k -= 1
    return k


def on_parent(part, parent, junction, name):
    """Start a branch exactly on a vertex of its parent without repeating the parent's track: at the junction station's
    point when the branch's track leaves the parent there, otherwise where the branch's track really leaves the parent."""
    k = run_from_start(part, parent.ls, NEAR_PARENT)
    shared = part.slice(0, k).length() if k else 0.0
    if shared > SHARE_OK:
        x = parent.at(part.p[k])
        way = "back toward Boston" if parent.ls.project(Point(x)) < parent.ls.project(Point(junction)) else "past it"
        LOG.append(f"{name}: its track leaves the parent {shared:.0f} m {way}, not at the junction station; it starts "
                   f"there so it does not repeat the parent's track")
        return Part([x] + part.p[k + 1:], [None] + part.lab[k + 1:])
    return Part([parent.at(junction)] + part.p[1:], [None] + part.lab[1:])


def head_on(part, host, key, start, d=NEAR_HOST):
    """Replace the run of part along host, from its start, with host's own vertices. Returns (canon piece, rest)."""
    k = run_from_start(part, host.ls, d)
    x = host.at(part.p[k])
    return ("canon", key, start, x), Part([x] + part.p[k + 1:], [None] + part.lab[k + 1:])


def tail_on(part, host, key, end, d=NEAR_HOST):
    """Replace the run of part along host, up to its end, with host's own vertices. Returns (rest, canon piece)."""
    k = run_from_end(part, host.ls, d)
    x = host.at(part.p[k])
    rest = Part(part.p[:k] + [x], part.lab[:k + 1])
    return rest, ("canon", key, x, end)


def extension(G, p0, pts, prof, name, runs_on=False):
    """Route on from p0, the end of an MBTA shape, through pts. A line that runs on past the map just has to reach its
    last town on the through track, so its end is pulled less hard toward the town and stays off side lines."""
    part = G.route([p0] + pts, prof, name, lam_end=1.5 if runs_on else LAM_END).cut_from(p0)
    if dist(part.p[0], p0) < 30:   # start exactly where the shape ends, without a stub
        part.p[0] = p0
    return part


def assemble(C, comps):
    pts, src = [], {}

    def add(lab, ln):
        src[lab] = src.get(lab, 0.0) + float(ln)

    for comp in comps:
        if isinstance(comp, tuple):
            _, key, a, b = comp
            seg = C[key].c if a is None else C[key].between(a, b)
            add("MBTA:" + C[key].sid, LineString(seg).length)
        else:
            for lab, ln in zip(comp.lab[1:], comp.seglen()):
                add(lab or "join", ln)
            seg = comp.simplified()
        if pts:
            gap = dist(pts[-1], seg[0])
            if gap > 0:
                add("straight", gap)
                pts.append(seg[0])
            seg = seg[1:]
        pts.extend(seg)
    return pts, src


def sources_text(src):
    out, osm_done = [], False
    osm = {k[4:]: v for k, v in src.items() if k.startswith("OSM:")}
    hist = {k: v for k, v in src.items() if k.startswith("H:") and v >= 500}
    hist = set(sorted(hist, key=hist.get, reverse=True)[:4])
    for k, v in src.items():
        if k.startswith("MBTA:"):
            out.append("MBTA shape " + k[5:])
        elif k.startswith("OSM:") and not osm_done and sum(osm.values()) >= 200:
            names = [n for n in sorted(osm, key=osm.get, reverse=True) if n and osm[n] >= 2000][:3]
            out.append("OSM rail" + (f" ({', '.join(names)})" if names else ""))
            osm_done = True
        elif k in hist:
            out.append("historic " + k[2:])
    if src.get("straight", 0) >= 50:
        out.append("straight link (ours)")
    return " + ".join(out)


def graph_area():
    x0, y0, x1, y1 = FRAME
    t = np.linspace(0, 1, 60)
    lon = np.r_[x0 + (x1 - x0) * t, np.full(60, x1), x1 - (x1 - x0) * t, np.full(60, x0)]
    lat = np.r_[np.full(60, y0), y0 + (y1 - y0) * t, np.full(60, y1), y1 - (y1 - y0) * t]
    X, Y = TO_M.transform(lon, lat)
    pts = np.array([m(q) for q in WP.values()])
    return shapely.box(min(X.min() - PAD, pts[:, 0].min() - 15000), min(Y.min() - PAD, pts[:, 1].min() - 15000),
                       max(X.max() + PAD, pts[:, 0].max() + 15000), max(Y.max() + PAD, pts[:, 1].max() + 15000))


def main():
    LOG.clear()
    T = gpd.read_file(ROOT / "data/shared/ne_rail_today.gpkg").to_crs(CRS_M)
    H = gpd.read_file(ROOT / "data/shared/ne_rail_1826_1911.gpkg").to_crs(CRS_M)
    L = gpd.read_file(BM / "data/mbta_lines.gpkg").to_crs(CRS_M)
    S = gpd.read_file(BM / "data/mbta_stops.gpkg").to_crs(CRS_M)

    area = graph_area()
    T = T[~T["service"].isin(["yard", "siding", "crossover"]) & T.intersects(area)]
    H = H[H.intersects(area)]
    feats = []
    for g, nm in zip(T.geometry, T["name"]):
        for part in getattr(g, "geoms", [g]):
            feats.append((part, 0, "OSM:" + (nm if isinstance(nm, str) else "")))
    for g, nm, yr in zip(H.geometry, H["rr_name"], H["year_opened"]):
        for part in getattr(g, "geoms", [g]):
            feats.append((part, 1, f"H:{int(yr)} {nm if isinstance(nm, str) else 'unnamed'}"))
    G = Graph(feats)

    def shape(key):
        route, name = SHAPES[key]
        r = L[(L["route"] == route) & (L["name"] == name)]
        assert len(r) == 1, (key, len(r))
        return r.geometry.iloc[0], str(r["shape"].iloc[0])

    def stop(name):
        r = S[S["name"] == name]
        assert len(r) == 1, name
        return (float(r.geometry.iloc[0].x), float(r.geometry.iloc[0].y))

    def clipped(key, a=None, b=None):
        g, sid = shape(key)
        sub = substring(g, g.project(Point(a)) if a else 0.0, g.project(Point(b)) if b else g.length)
        return Part(sub.coords, [None] + ["MBTA:" + sid] * (len(sub.coords) - 1))

    def wp(name):
        return m(WP[name])

    C = {}
    for key in ("fit", "low", "hav", "nbp", "wor", "fra", "pro", "nb", "kin", "grb"):
        g, sid = shape(key)
        if key == "kin":   # the shape runs on past Kingston station into the layover; the line goes on to Plymouth
            g = substring(g, 0.0, g.project(Point(stop("Kingston"))))
        C[key] = Canon(g.simplify(SIMPLIFY, preserve_topology=False).coords, sid)

    P = []   # (line, piece, end, components, parent key or None)

    # North side
    fit_ext = extension(G, C["fit"].c[-1], [wp("Gardner"), wp("Athol")], "today", "fit main", runs_on=True)
    P.append(("fit", "main", "runs_on", [("canon", "fit", None, None), fit_ext], None))
    sa = stop("South Acton")
    marl = G.route([sa, wp("Hudson"), wp("Marlborough")], "historic", "fit marlborough")
    P.append(("fit", "marlborough", "end", [on_parent(marl, C["fit"], sa, "fit marlborough")], "fit"))

    P.append(("low", "main", "end", [("canon", "low", None, None)], None))
    mon = extension(G, C["low"].c[-1], [wp("Nashua"), wp("Manchester")], "today", "hmon main", runs_on=True)
    P.append(("hmon", "main", "runs_on", [("canon", "low", None, None), mon], None))

    P.append(("hav", "main", "end", [("canon", "hav", None, None)], None))
    mai = extension(G, C["hav"].c[-1], [wp("Exeter")], "today", "hmai main", runs_on=True)
    P.append(("hmai", "main", "runs_on", [("canon", "hav", None, None), mai], None))

    P.append(("nbp", "main", "end", [("canon", "nbp", None, None)], None))
    bev = stop("Beverly")
    P.append(("nbp", "rockport", "end", [on_parent(clipped("rock", bev), C["nbp"], bev, "nbp rockport")], "nbp"))

    # Peabody line: Marblehead and Clifton on the old Swampscott branch, a straight link to South Salem on the
    # Newburyport track, that track to Salem, then the old Salem-Peabody and Essex lines to the Haverhill track and Lawrence
    pea_a = G.route([wp("Marblehead"), wp("Clifton")], "historic", "pea main")
    mst = wp("Marblehead station")
    if dist(pea_a.p[0], mst) > 30:   # the 1872 track in the historic layer stops short of the depot
        LOG.append(f"pea main: {dist(pea_a.p[0], mst):.0f} m straight from Marblehead station to the historic track")
        pea_a = Part([mst] + pea_a.p, [None, "straight"] + pea_a.lab[1:])
    ssj = C["nbp"].at(wp("South Salem"))
    law = C["hav"].at(stop("Lawrence"))
    pea_b = G.route([ssj, wp("Peabody"), wp("Danvers"), wp("Middleton"), stop("Lawrence")], "historic", "pea main")
    on_nbp, pea_b = head_on(pea_b, C["nbp"], "nbp", ssj)
    pea_b, on_hav = tail_on(pea_b, C["hav"], "hav", law)
    LOG.append(f"pea main: Clifton to South Salem is a straight link of {dist(pea_a.p[-1], ssj):.0f} m")
    P.append(("pea", "main", "end", [pea_a, on_nbp, pea_b, on_hav], None))

    # South side
    P.append(("wor", "main", "end", [("canon", "wor", None, None)], None))
    alb = extension(G, C["wor"].c[-1], [wp("Springfield")], "today", "halb main", runs_on=True)
    P.append(("halb", "main", "runs_on", [("canon", "wor", None, None), alb], None))

    P.append(("fra", "main", "end", [("canon", "fra", None, None)], None))
    wal, man = stop("Walpole"), stop("Mansfield")
    fox = on_parent(clipped("fox", wal, man), C["fra"], wal, "fra foxboro")
    fox, fox_pro = tail_on(fox, C["pro"], "pro", C["pro"].at(man), NEAR_PARENT)
    P.append(("fra", "foxboro", "end", [fox, fox_pro], "fra"))

    P.append(("pro", "main", "end", [("canon", "pro", None, None)], None))
    cj = stop("Canton Junction")
    sto = on_parent(clipped("sto", cj), C["pro"], cj, "pro stoughton")
    sto_ext = extension(G, sto.p[-1], [wp("Taunton")], "historic", "pro stoughton")
    P.append(("pro", "stoughton", "end", [sto, sto_ext], "pro"))
    nyc = extension(G, C["pro"].c[-1], [wp("Westerly")], "today", "hnyc main", runs_on=True)
    P.append(("hnyc", "main", "runs_on", [("canon", "pro", None, None), nyc], None))

    P.append(("fr", "main", "end", [("canon", "nb", None, None)], None))
    et = stop("East Taunton")
    P.append(("fr", "fall-river", "end", [on_parent(clipped("fall", et), C["nb"], et, "fr fall-river")], "nb"))
    # Cape: to the far (Cape) end of the canal bridge, so the arrow sits on the bridge
    bridge = T[T["name"] == "Cape Cod Canal Railroad Bridge"]
    ends = [q for g in bridge.geometry for q in (g.coords[0], g.coords[-1])]
    mid = stop("Middleborough")
    far = max(ends, key=lambda q: dist(q, mid))
    cape = G.route([mid, far], "today", "fr cape", end=G.nearest(far))
    P.append(("fr", "cape", "runs_on", [on_parent(cape, C["nb"], mid, "fr cape")], "nb"))

    # Kingston station is the end of a short spur. Plymouth trains (to 2021) left the spur at Cotley Junction and ran on the
    # Plymouth Branch, still in OSM, so Plymouth is a branch from the junction on real track (review, November 8).
    P.append(("kin", "main", "end", [("canon", "kin", None, None)], None))
    cotley = C["kin"].at(wp("Cotley Junction"))
    ply = G.route([cotley, wp("Plymouth")], "today", "kin plymouth")
    P.append(("kin", "plymouth", "end", [on_parent(ply, C["kin"], cotley, "kin plymouth")], "kin"))
    P.append(("grb", "main", "end", [("canon", "grb", None, None)], None))

    # Assemble after every junction is in place, so shared shapes carry all their inserted vertices
    feats_out, report = [], []
    for line, piece, end, comps, parent in P:
        pts, src = assemble(C, comps)
        lon, lat = TO_LL.transform(*np.asarray(pts).T)
        coords = [[round(float(x), 7), round(float(y), 7)] for x, y in zip(lon, lat)]
        coords = [q for i, q in enumerate(coords) if i == 0 or q != coords[i - 1]]
        straight = round(src.get("straight", 0.0))
        props = dict(line=line, piece=piece, end=end, sources=sources_text(src), straight_m=int(straight))
        feats_out.append(dict(type="Feature", properties=props, geometry=dict(type="LineString", coordinates=coords)))
        km = LineString(pts).length / 1000
        note = ""
        if parent:
            pl = C[parent].ls
            note = f"  start {pl.distance(Point(pts[0])):.3f} m off parent, vertex={pts[0] in C[parent].c}"
        if end == "runs_on":
            x, y = coords[-1]
            inside = FRAME[0] < x < FRAME[2] and FRAME[1] < y < FRAME[3]
            note += "  last point INSIDE frame" if inside else "  last point past frame"
        report.append(f"{line:5s} {piece:12s} {end:8s} {km:7.1f} km  straight {straight:6.0f} m  {props['sources']}{note}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dict(type="FeatureCollection", features=feats_out)), encoding="utf-8")
    print("\n".join(report))
    print("\n".join(LOG))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
