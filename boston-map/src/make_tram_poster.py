"""Tram network poster: every NERTA tram route on one sheet, the tram counterpart of the ferry network poster.

NERTA has no buses. Trams run on today's busiest bus streets and pods carry riders the rest of the way. Max approved the
routes on the real-geography web map (tools/make_tram_realmap.py). This poster bends them into a schematic: 45-degree
lines, north up, in rough geographic order.

How the layout works
  1. Routes come from data/tram/tram_draft.json, read at render time, plus any route in tram_extra.json whose id isn't in
     tram_draft.json yet. A stop's name is its key: the same name within 800 m on two routes is one stop, drawn once. The
     name shown is the stop's "label" when the data has one (Kendall for Kendall/MIT). Extra fields are ignored.
  2. Junctions (stops where routes meet, part or end) are laid out by least squares: every stretch between two junctions is
     pulled toward the 45-degree direction nearest its real one, no two leaving a junction the same way, long enough for
     its stops and their names, with junctions and stretches kept apart and the real map as a weak anchor. The real map is
     first squeezed toward downtown (log scale), so the suburbs take less room. A stretch of BEND_MIN stops or more gets one
     free 45-degree bend. Hand tuning, by stop name: AT pins a junction, DIR forces a stretch's direction, LONG lengthens it.
  3. Each stretch is drawn straight, or in two 45-degree pieces; its stops are spaced evenly, clear of its bends. Routes
     sharing a stretch run side by side, ordered so they part without crossing; a stop that lands on another route's
     line slides along its own.
  4. Labels, route badges and route names are placed by a search over spots around each stop, scored for overlaps and
     for sitting nearer their own stop than any other. SIDE forces a label's side.
  New routes need no new code: they lay themselves out, and the tables above take any fixes.

Writes only new files to output/copies/: tram_network_vN.png (600 dpi), .pdf, and zoomed crops of the densest areas.
Never overwrites. --web leaves the release block out (nerta.fun) and names the files tram_network_web_vN.
Run: python make_tram_poster.py [version] [--routes PATH] [--extra PATH | --no-extra] [--web] [--draft DIR] [--grid]
"""
import json
import math
import os
import re
import sys
import textwrap
from collections import defaultdict

# Python orders sets of names differently on every run unless the hash seed is fixed, and a few layout steps walk such
# sets: one fixed seed makes every render of the same data come out the same.
if __name__ == "__main__" and os.environ.get("PYTHONHASHSEED") != os.environ.get("TRAM_SEED", "0"):
    import subprocess
    os.environ["PYTHONHASHSEED"] = os.environ.get("TRAM_SEED", "0")
    sys.exit(subprocess.call([sys.executable] + sys.argv))
from functools import lru_cache
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch  # noqa: E402
from matplotlib.textpath import TextPath  # noqa: E402
from shapely.geometry import LineString, Point, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from nerta_mark import draw_nerta, draw_t  # noqa: E402
import make_tmap as M  # noqa: E402  (drawing helpers only: M.icon, M.CLIPPER, M.HSR, M.WEB)
import make_line_poster as LP  # noqa: E402  (CODES and EXTRA_TRANSFERS for the live pills)
from release_tag import draw_release  # noqa: E402
from charlie_points import draw_cp, draw_free_tag, KEY_TEXT, FREE_TEXT  # noqa: E402
from station_kit import INK, WHITE, rounded  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "output" / "copies"
DATA = HERE.parent / "data" / "tram" / "tram_draft.json"
EXTRA = HERE.parent / "data" / "tram" / "tram_extra.json"

P = 5.0            # one grid step, in drawing units
K = 0.075          # inches per drawing unit
PPU = K * 72       # points per drawing unit
TRAM = "#e0457b"   # hot pink (Max)
TRAM_TEXT = "#b8336a"   # the same pink, darkened for type on paper (5.4 to 1 on paper)
PAPER = "#fcfcfa"
GREY = "#4a4f57"

# The tram line and stop symbol (research/tram-changes-for-all-maps.md), in points. Every size follows W.
W = 3.2            # line width
D = 6.5 * W        # stop circle diameter (the spec says about 7.5 W; 6.5 W keeps the names in charge on a sheet this full)
EDGE = 0.4 * W     # circle edge and cross stroke
ARM = 1.35         # each cross arm reaches 1.35 radii from the center
CORE = 0.11 * W    # the super thin black center line
PAR = 1.75 * W     # center to center, for routes side by side
CASE = 1.6         # paper casing round each line, so a crossing reads as a crossing
LWU, RU = W / PPU, D / 2 / PPU
ROUT = RU + EDGE / 2 / PPU
ARMU, PARU = ARM * RU, PAR / PPU

FS, FS_END, FS_PILL, FS_BADGE = 10.8, 11.4, 8.6, 9.4
PILL_W, PILL_H, PILL_GAP = 6.6, 2.9, 0.35
BADGE_H = 3.0

# Copied from make_ferry_network.py, plus the high-speed and ferry pills the line posters use
PILL = {"RL": "#da291c", "OL": "#ed8b00", "BL": "#003da5", "GL": "#00843d", "YL": "#f5c400", "CL": "#00a9c9", "IL": "#3f3fb5",
        "SL": "#7c878e", "CR": "#80276c", "HSR": "#80276c", "F": "#00796d", "AC": M.CLIPPER["color"]}
NAMES = {"RL": "Red Line", "OL": "Orange Line", "BL": "Blue Line", "GL": "Green Line", "YL": "Yellow Line", "CL": "Cyan Line",
         "IL": "Indigo Line", "SL": "Silver Line", "CR": "Commuter rail", "HSR": "High-speed rail", "F": "Ferry",
         "AC": f"{M.CLIPPER['name']} to {M.CLIPPER['dest']}"}
ORDER = ["RL", "OL", "BL", "GL", "YL", "CL", "IL", "SL", "CR", "HSR", "F", "AC"]

# ---------------------------------------------------------------------------------------------------------------
# Layout knobs. Grid steps, y up.
CENTER = (-71.0624, 42.3564)   # Park St: the real map is squeezed toward here
RHO0 = 5.0          # km: the log squeeze starts to bite past this distance
SCALE = 6.0         # grid steps per squeezed km
GAP_V = 1.5         # grid steps per stop gap on upright and 45-degree stretches
GAP_V_OUT = 1.3     # the same, out past OUT_KM from downtown
OUT_KM = 9.0
GAP_H = 2.6         # on level stretches, where names alternate above and below
MIN_KEY = 3.2       # shortest stretch between two junctions with no stop between
MIN_KEY_H = 4.0     # the same, level
BEND_MIN = 4        # stretches with this many stops or more get one free bend
SEP_KK, SEP_KE, SEP_EE = 3.5, 2.8, 2.8   # junction to junction, junction to stretch, stop to stretch
W_GEO, W_PIN, W_SEP, W_DIR, W_COMPACT = 0.02, 60.0, 4.0, 10.0, 0.6
ITER = 120
CMIN = 0.95         # a stop keeps this far from a bend
RR = 1.6            # bend rounding, drawing units

# Hand tuning, by stop name. Junctions are stops where routes meet, part or end.
AT = {        # junction -> (x, y) grid spot that pins it
    "Orient Heights": (19.5, 11.5),   # the Winthrop tram meets no other: keep it clear of the Chelsea trunk
}
DIR = {       # (junction, junction) -> "E", "NE", "N", ...: forces that stretch's direction, read from the first name
    ("Uphams Corner", "Fields Corner"): "SE",   # the 15 leans away from the 23, so Dorchester's names have room
}
BEND = {}     # (junction, junction) -> "diag" (the 45-degree piece first, from the first name) or "flat"
VIA = {}      # (junction, junction) -> [(x, y), ...] grid bends, from the first name
LONG = {      # (junction, junction) -> factor: that stretch gets this many times its usual shortest length
    ("Nubian", "Roxbury Crossing"): 1.2,
    ("Brookline Village", "Roxbury Crossing"): 1.35,   # the Longwood names, alternating above and below
    ("Uphams Corner", "Four Corners"): 1.8,     # room for the Four Corners name between the 23 and the 15
    ("Nubian", "Four Corners"): 1.4,            # Waumbeck St and Grove Hall clear of the wedge at Four Corners
    ("Seaver St", "Four Corners"): 1.5,
    ("Malden Center", "Revere Beach Pkwy"): 1.2,
    ("Wellington", "Revere Beach Pkwy"): 1.6,
}
SPLIT = set()   # stop names that count as junctions, so a long stretch can bend there
SIDE = {      # stop name -> label side: r, l, t, b, tr, tl, br, bl
    "Mission Park": "t", "Winthrop St": "t", "Hastings Ln": "b", "Roxbury Crossing": "b", "Cambridge St": "r", "Forest Hills": "t", "Arborway": "b",
    "Richardson St": "t", "Pierce St": "b", "Wellington": "b", "Keenan St": "l",
}
BADGE_AT = {}   # terminal name -> (dx, dy) drawing units from the stop to its first badge row's left end, placed by hand
BADGE_ROW = {"Forest Hills": 5}   # terminal name -> badges to a row, where one long row sits better than two
BADGE_SIDE = {   # terminal name -> the side its route badges go on, where the automatic pick crowds a neighbor's name
}
TEXT = {      # stop name -> label text with line breaks, for names boxed in by close neighbors
}

WARN = []

# ---------------------------------------------------------------------------------------------------------------
# --display: the station display, the size and shape of the ferry display (ferry_network_v18.png, 7379 x 9135 px at
# 300 dpi), to hang beside it. Same symbols, smaller; stops closer; the layout shrinks until it fits the sheet.
DISPLAY = "--display" in sys.argv
SHEET = (30.0 / K, 37.0 / K)   # drawing units: 30 x 37 in (Max, November 8: bigger than the ferry display, same type)
AT_SCALE = 1.0      # pins are written for the big poster; the display scales them with its layout
CAP_FS = 10.2       # route names on the map


def use_display():
    """Sizes for the station display: every size follows W as on the big poster, at three quarters."""
    global W, D, EDGE, CORE, PAR, CASE, LWU, RU, ROUT, ARMU, PARU, FS, FS_END, FS_PILL, FS_BADGE, PILL_W, PILL_H, PILL_GAP
    global BADGE_H, CAP_FS, CLEAR, CMIN
    W = 1.8
    D, EDGE, CORE, PAR, CASE = 6.5 * W, 0.4 * W, 0.11 * W, 1.75 * W, 1.1
    LWU, RU = W / PPU, D / 2 / PPU
    ROUT = RU + EDGE / 2 / PPU
    ARMU, PARU = ARM * RU, PAR / PPU
    FS, FS_END, FS_PILL, FS_BADGE, CAP_FS = 8.8, 9.4, 7.2, 7.8, 8.8
    PILL_W, PILL_H, PILL_GAP, BADGE_H = 5.2, 2.3, 0.3, 2.4
    CLEAR, CMIN = 0.55, 0.6
    global NEAR, ROWGAP, LABEL_GAP
    NEAR, ROWGAP, LABEL_GAP = 0.6, 5.2, 0.4
    global BOW
    BOW = 2.0   # wider on the display: room for names between the two lines


BASE = dict(GAP_V=GAP_V, GAP_V_OUT=GAP_V_OUT, GAP_H=GAP_H, MIN_KEY=MIN_KEY, MIN_KEY_H=MIN_KEY_H, SEP_KK=SEP_KK, SEP_KE=SEP_KE,
            SEP_EE=SEP_EE, SCALE=SCALE)


def shrink(m):
    """Every spacing in the layout times m (the display's fitting knob); never closer than the stop symbols allow."""
    global AT_SCALE
    g = globals()
    for k_, v_ in BASE.items():
        g[k_] = v_ * m
    floor = dict(GAP_V=0.84, GAP_V_OUT=0.78, GAP_H=2.0, MIN_KEY=2.4, MIN_KEY_H=3.0, SEP_KK=2.6, SEP_KE=2.0, SEP_EE=2.0)
    for k_, v_ in floor.items():   # the junctions keep room for their names however tight the stops get
        g[k_] = max(g[k_], v_)
    AT_SCALE = m


# ---------------------------------------------------------------------------------------------------------------
# Data
def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def read_routes(main, extra):
    """tram_draft.json, then any route in tram_extra.json whose id isn't there yet (until the stop-naming merge lands)."""
    routes, have = [], set()
    for r in json.loads(Path(main).read_text(encoding="utf-8")).get("routes", []):
        if str(r["id"]) not in have:
            routes.append(r)
            have.add(str(r["id"]))
    n0 = len(routes)
    if extra and Path(extra).exists():
        for r in json.loads(Path(extra).read_text(encoding="utf-8")).get("routes", []):
            if str(r["id"]) not in have:
                routes.append(r)
                have.add(str(r["id"]))
    print(f"{n0} routes from {Path(main).name}, {len(routes) - n0} more from {Path(extra).name if extra else 'nowhere'}")
    return routes


def clean(name):
    s = re.sub(r"\s+", " ", str(name)).strip()
    t = re.sub(r"\s*\b[Bb]us\b\s*", " ", s).strip()   # there are no buses in NERTA
    if t != s:
        WARN.append(f"dropped 'bus' from a stop name: {s} -> {t}")
    return t or s


COSL = math.cos(math.radians(CENTER[1]))


def km(ll):
    return np.array([(ll[0] - CENTER[0]) * 111.32 * COSL, (ll[1] - CENTER[1]) * 110.57])


def squeeze(v):
    rho = float(np.hypot(*v))
    if rho < 1e-9:
        return v * SCALE
    return v / rho * RHO0 * math.log1p(rho / RHO0) * SCALE


def pkey(name):
    """A station name as a lookup key: line breaks, hair spaces and curly quotes ironed out; "Mass Ave" and "Mass. Ave" stay apart."""
    t = str(name).replace(chr(10), " ").replace("\u200a", "").replace("\u2019", "'")
    t = re.sub(r"\bSquare\b", "Sq", t)
    return re.sub(r"[^a-z0-9.'/]+", " ", t.lower()).strip()


def live_pills():
    """Station name -> transfer pills, live from the main map: every line in make_tmap lines(), commuter rail at every
    CR_STOPS stop, and the commuter rail transfers the line posters add at T stations (Waltham, Ruggles, Quincy Center...)."""
    out = defaultdict(list)

    def add(n, c):
        if c and c not in out[pkey(n)]:
            out[pkey(n)].append(c)
    for col, _style, _path, stops in M.lines():
        for n in stops:
            add(n.rstrip("+"), LP.CODES.get(col))
    for n, *_ in M.CR_STOPS:
        add(n, "CR")
    for n, extra in LP.EXTRA_TRANSFERS.items():
        if "CR" in extra:
            add(n, "CR")
    return out


def build(raw):
    nodes, byname, routes = {}, defaultdict(list), []
    for r in raw:
        rid = str(r["id"])
        seq = []
        for s in r.get("stops", []):
            name = clean(s["name"])
            ll = (float(s["lonlat"][0]), float(s["lonlat"][1]))
            k = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
            nid = next((c for c in byname[k] if np.hypot(*(km(nodes[c]["ll"]) - km(ll))) < 0.8), None)
            if nid is None:
                nid = name if name not in nodes else f"{name} ({rid})"
                nodes[nid] = dict(id=nid, name=name, nerta=False, pills=[], ll=ll, routes=[], label=None)
                byname[k].append(nid)
            nd = nodes[nid]
            if not nd["label"] and s.get("label"):   # the naming session's display name, e.g. Kendall for Kendall/MIT
                nd["label"] = clean(s["label"])
            nd["nerta"] = nd["nerta"] or bool(s.get("nerta"))
            for c in s.get("pills") or []:
                if c not in PILL:
                    WARN.append(f"unknown pill {c} at {name}")
                elif c not in nd["pills"]:
                    nd["pills"].append(c)
            if rid not in nd["routes"]:
                nd["routes"].append(rid)
            if not seq or seq[-1] != nid:
                seq.append(nid)
        if len(seq) < 2:
            WARN.append(f"route {rid} has under two stops; left off")
            continue
        routes.append(dict(id=rid, name=clean(r.get("name", rid)), via=r.get("via", ""), seq=seq))
        nodes[seq[0]]["terminal"] = nodes[seq[-1]]["terminal"] = True
    live = live_pills()
    for nd in nodes.values():
        lv = live.get(pkey(nd["name"])) or live.get(pkey(nd["label"] or nd["name"]))
        if lv and nd["nerta"]:
            if sorted(lv, key=ORDER.index) != sorted(nd["pills"], key=ORDER.index):
                WARN.append(f"pills at {nd['name']}: {' '.join(nd['pills']) or 'none'} in the tram data, {' '.join(sorted(lv, key=ORDER.index))} live from make_tmap")
            nd["pills"] = list(lv)
        elif lv:
            WARN.append(f"{nd['name']} shares a name with a NERTA station but isn't marked as one; no pills drawn")
            nd["pills"] = []
        elif nd["pills"]:
            WARN.append(f"pills at {nd['name']} come from the tram data only: no match in make_tmap lines()")
        nd["pills"].sort(key=ORDER.index)
        nd["q"] = squeeze(km(nd["ll"]))
        nd["label"] = nd["label"] or nd["name"]
    ids = list(nodes)
    xy = np.array([km(nodes[n]["ll"]) for n in ids])
    for i, a in enumerate(ids):   # different names at one spot: worth a look by the naming session
        d = np.hypot(*(xy[i + 1:] - xy[i]).T)
        for j in np.nonzero(d < 0.12)[0]:
            b = ids[i + 1 + j]
            WARN.append(f"two stops {d[j] * 1000:.0f} m apart with different names: {a} ({', '.join(nodes[a]['routes'])}) "
                        f"and {b} ({', '.join(nodes[b]['routes'])})")
    return nodes, routes


# ---------------------------------------------------------------------------------------------------------------
# Skeleton: junctions and the stretches between them
def pieces(seq, key):
    out, cur = [], [seq[0]]
    for n in seq[1:]:
        cur.append(n)
        if n in key:
            out.append(cur)
            cur = [n]
    return out


def seg_dist(p, a, b):
    ab = b - a
    L2 = ab @ ab
    t = 0.0 if L2 < 1e-12 else min(1.0, max(0.0, (p - a) @ ab / L2))
    return float(np.hypot(*(p - a - t * ab)))


def skeleton(nodes, routes):
    E, adj = defaultdict(set), defaultdict(set)
    for r in routes:
        for a, b in zip(r["seq"], r["seq"][1:]):
            E[frozenset((a, b))].add(r["id"])
            adj[a].add(b)
            adj[b].add(a)
    key = {r["seq"][0] for r in routes} | {r["seq"][-1] for r in routes}
    for n in nodes:
        nb = sorted(adj[n])
        if len(nb) != 2 or E[frozenset((nb[0], n))] != E[frozenset((n, nb[1]))]:
            key.add(n)
    key |= {n for n in nodes if nodes[n]["name"] in SPLIT}
    for r in routes:   # a route that comes back to a stop: that stop is a junction
        seen = set()
        for n in r["seq"]:
            if n in seen:
                key.add(n)
            seen.add(n)
    # a long stretch that wanders bends where it strays furthest from a straight line (Douglas-Peucker on the squeezed map)
    while True:
        added = False
        for r in routes:
            for t in pieces(r["seq"], key):
                mids = t[1:-1]
                if len(mids) < 5:
                    continue
                a, b = nodes[t[0]]["q"], nodes[t[-1]]["q"]
                ch = float(np.hypot(*(b - a)))
                dev = [seg_dist(nodes[m]["q"], a, b) for m in mids]
                i = int(np.argmax(dev))
                if dev[i] > max(0.24 * ch, 2.5):
                    key.add(mids[i])
                    added = True
        if not added:
            break
    SK = {}
    for r in routes:
        r["legs"] = []
        for t in pieces(r["seq"], key):
            t = tuple(t)
            c = min(t, t[::-1])
            if c not in SK:
                SK[c] = dict(key=c, u=c[0], v=c[-1], mids=list(c[1:-1]), routes=[])
            if r["id"] not in SK[c]["routes"]:
                SK[c]["routes"].append(r["id"])
            r["legs"].append((c, t == c))
    return key, SK


# ---------------------------------------------------------------------------------------------------------------
# Least-squares layout of the junctions
OCT = [np.array([math.cos(k * math.pi / 4), math.sin(k * math.pi / 4)]) for k in range(8)]
DIRS = {"E": 0, "NE": 1, "N": 2, "NW": 3, "W": 4, "SW": 5, "S": 6, "SE": 7}


def oct_index(v):
    return int(round(math.atan2(v[1], v[0]) / (math.pi / 4))) % 8


def gap_for(k):
    return GAP_H if k in (0, 4) else GAP_V


def by_names(table, nodes, a, b):
    """Look up a table keyed by (name, name), either way round. Returns (value, reversed)."""
    na, nb = nodes[a]["name"], nodes[b]["name"]
    if (na, nb) in table:
        return table[(na, nb)], False
    if (nb, na) in table:
        return table[(nb, na)], True
    return None, False


def label_w(nodes, n):
    """Width of a stop's name and pills, in grid steps."""
    nd = nodes[n]
    end = nd.get("terminal", False)
    text = TEXT.get(nd["name"], nd.get("label") or nd["name"])
    text = text.upper() if end else text
    fs, wt = (FS_END, "bold") if end else (FS, "normal")
    w = max(ink(ln, fs, wt)[2] - ink(ln, fs, wt)[0] for ln in curly(text).split(chr(10)))
    if nd["pills"]:
        w += 1.0 + len(nd["pills"]) * PILL_W + (len(nd["pills"]) - 1) * PILL_GAP
    return w / P


def level_gap(wid):
    """Gap between stops on a level piece, so names on the same side (every other stop) clear each other."""
    g = GAP_H
    for a, b in zip(wid, wid[2:]):
        g = max(g, (a + b) / 4 + 0.55)
    for a, b in zip(wid, wid[1:]):   # and neighbors most of the way, should two end up on one side
        g = max(g, 0.7 * (a + b) / 2)
    return g


def lsq(rows, n, coupled=False):
    """Weighted least squares. rows: (cols, bx, by, w) with cols = [(i, coef)] for the x and y systems alike;
    coupled rows: (cols, b, w) over 2n unknowns (x then y)."""
    if coupled:
        A = np.zeros((len(rows), 2 * n))
        b = np.zeros(len(rows))
        for r, (cols, bb, w) in enumerate(rows):
            s = math.sqrt(w)
            for i, c in cols:
                A[r, i] += c * s
            b[r] = bb * s
        x = np.linalg.lstsq(A, b, rcond=None)[0]
        return np.column_stack([x[:n], x[n:]])
    A = np.zeros((len(rows), n))
    bx, by = np.zeros(len(rows)), np.zeros(len(rows))
    for r, (cols, x, y, w) in enumerate(rows):
        s = math.sqrt(w)
        for i, c in cols:
            A[r, i] += c * s
        bx[r], by[r] = x * s, y * s
    return np.column_stack([np.linalg.lstsq(A, bx, rcond=None)[0], np.linalg.lstsq(A, by, rcond=None)[0]])


BEND_SPLIT = {}   # (junction, junction) -> how many of the stretch's stops sit between the first-named junction and its bend
BEND_SPLIT_DISPLAY = {("Watertown", "Harvard"): 2}   # display: only Walnut St and Irving St on the 71's upright piece, spaced wide   # display: only Walnut St and Irving St on the 71's upright piece, spaced wide


def split_h(e, nodes):
    """Stops before a stretch's free bend, counted from its u end: half, unless set by hand."""
    k = len(e["mids"])
    v, rev = by_names(BEND_SPLIT, nodes, e["u"], e["v"])
    if v is None:
        return k // 2
    return max(1, min(k - 1, k - v if rev else v))


def solve(nodes, key, SK):
    """Junction spots, plus one free bend on every stretch with BEND_MIN or more stops, by least squares."""
    keys = sorted(key)
    ix = {k: i for i, k in enumerate(keys)}
    q = [nodes[k]["q"] for k in keys]
    is_bend = [False] * len(keys)
    segs, bends = [], {}
    # two stretches between the same two junctions are laid out as one (the one with more stops); the other bows out beside it
    rep = {}
    for e in sorted(SK.values(), key=lambda e: (-len(e["mids"]), -len(e["routes"]), e["key"])):
        rep.setdefault(frozenset((e["u"], e["v"])), e["key"])
    for e in SK.values():
        if rep[frozenset((e["u"], e["v"]))] != e["key"]:
            continue
        f, rev = by_names(DIR, nodes, e["u"], e["v"])
        fdir = None if f is None else ((DIRS[f] + 4) % 8 if rev else DIRS[f])
        via, _ = by_names(VIA, nodes, e["u"], e["v"])
        k = len(e["mids"])
        i, j = ix[e["u"]], ix[e["v"]]
        wid = [label_w(nodes, n) for n in [e["u"]] + e["mids"] + [e["v"]]]
        far = np.mean([np.hypot(*km(nodes[m]["ll"])) for m in e["mids"]]) if e["mids"] else 0.0
        stretch_k = by_names(LONG, nodes, e["u"], e["v"])[0] or 1.0
        gv = GAP_V_OUT if far > OUT_KM else GAP_V   # out in the suburbs, with nothing else near, stops sit a little closer
        if k >= BEND_MIN and fdir is None and not via:
            h = split_h(e, nodes)   # stops before the bend, which sits halfway between two stops
            chain = [nodes[e["u"]]["q"]] + [nodes[m]["q"] for m in e["mids"]] + [nodes[e["v"]]["q"]]
            b = len(q)
            q.append((chain[h] + chain[h + 1]) / 2)
            # the turns this bend may make (45-degree steps): straight on, or one step either way; 90 only where listed
            is_bend.append((2, 3, 4, 5, 6) if (by_names(BEND_90, nodes, e["u"], e["v"])[0] or not DISPLAY) else BEND_TURNS)
            bends[e["key"]] = b
            segs.append(dict(i=i, j=b, gaps=h + 0.5, stops=h, edge=e["key"], fixed=None, gap_h=level_gap(wid[:h + 2]), gap_v=gv, k=stretch_k))
            segs.append(dict(i=b, j=j, gaps=k - h + 0.5, stops=k - h, edge=e["key"], fixed=None, gap_h=level_gap(wid[h:]), gap_v=gv, k=stretch_k))
        else:
            segs.append(dict(i=i, j=j, gaps=k + 1.0, stops=k, edge=e["key"], fixed=fdir, gap_h=level_gap(wid), gap_v=gv, k=stretch_k))
    q = np.array(q)
    n = len(q)
    p = q.copy()
    EI = np.array([s["i"] for s in segs])
    EJ = np.array([s["j"] for s in segs])
    for s_ in segs:   # on the display, a run of stops goes upright or at 45 degrees: level runs spread their names too wide
        s_["nolevel"] = DISPLAY and s_["stops"] >= NOLEVEL_MIN and s_["fixed"] is None
    dirs = [s["fixed"] if s["fixed"] is not None else not_level(s, oct_index(q[s["j"]] - q[s["i"]]), q[s["j"]] - q[s["i"]]) for s in segs]
    pins = {ix[k]: np.array(AT[nodes[k]["name"]], float) * AT_SCALE for k in keys if nodes[k]["name"] in AT}
    if DISPLAY:
        pins.update({ix[k]: np.array(AT_DISPLAY[nodes[k]["name"]], float) * AT_SCALE / AT_DISPLAY_M for k in keys
                     if nodes[k]["name"] in AT_DISPLAY})   # set at spacing x AT_DISPLAY_M; they scale with the fit
    inc = defaultdict(list)
    for si, s in enumerate(segs):
        inc[s["i"]].append((si, 0))
        inc[s["j"]].append((si, 1))
    nstop = np.array([s["stops"] for s in segs])
    geo = np.hypot(*(q[EJ] - q[EI]).T)

    def length(si):
        """Shortest a piece may be: room for its stops, and on a level piece for their names, which alternate above and below."""
        s = segs[si]
        level = dirs[si] in (0, 4)
        if s["stops"] == 0 and s["gaps"] == 1.0:
            return s["k"] * (max(MIN_KEY_H, s["gap_h"]) if level else MIN_KEY)
        bend_room = CMIN if (is_bend[s["i"]] or is_bend[s["j"]]) else 0.0   # stops keep clear of a free bend
        # a first stop next to a junction where another piece leaves 45 degrees away sits further out
        tight = 0.0
        for node, end in ((s["i"], 0), (s["j"], 1)):
            mine = dirs[si] if end == 0 else (dirs[si] + 4) % 8
            if not is_bend[node] and any(sj != si and (((dirs[sj] if e2 == 0 else (dirs[sj] + 4) % 8) - mine) % 8) in (1, 7)
                                         for sj, e2 in inc[node]):
                tight += 0.6
        return s["k"] * s["gaps"] * (s["gap_h"] if level else s["gap_v"]) + bend_room + (tight if s["stops"] else 0.0)

    resolve_ports(p, segs, inc, dirs, is_bend)
    for it in range(ITER):
        rows = []
        for si in range(len(segs)):
            d, L = OCT[dirs[si]], length(si)
            # a piece may stretch as far as the layout needs, but never shrinks below room for its stops
            along = (p[EJ[si]] - p[EI[si]]) @ d
            Lt = max(along, L)
            rows.append(([(EJ[si], 1.0), (EI[si], -1.0)], Lt * d[0], Lt * d[1], W_DIR))
            rows.append(([(EJ[si], 1.0), (EI[si], -1.0)], L * d[0], L * d[1], W_COMPACT))   # and is drawn back toward it
        for i in range(n):
            rows.append(([(i, 1.0)], q[i, 0], q[i, 1], W_GEO))
        for i, a in pins.items():
            rows.append(([(i, 1.0)], a[0], a[1], W_PIN))
        rows += separation(p, EI, EJ, nstop)
        p = lsq(rows, n)
        if it < ITER - 15:
            for si, s in enumerate(segs):
                if s["fixed"] is not None:
                    continue
                v = p[EJ[si]] - p[EI[si]]
                if np.hypot(*v) < 1e-6:
                    continue
                k = not_level(s, oct_index(v), v)
                if k != dirs[si] and (v @ OCT[dirs[si]]) / np.hypot(*v) < math.cos(math.radians(31)):
                    dirs[si] = k
            resolve_ports(p, segs, inc, dirs, is_bend)
    # Straighten: every piece is pulled onto its 45-degree direction, near ones hard, moving the junctions as little as can be
    for _ in range(4):
        rows = []
        for si in range(len(segs)):
            d = OCT[dirs[si]]
            nrm = np.array([-d[1], d[0]])
            v = p[EJ[si]] - p[EI[si]]
            along, perp = v @ d, v @ nrm
            w = 400.0 if (along > 0 and abs(perp) < max(1.0, 0.18 * along)) else 40.0
            i, j = EI[si], EJ[si]
            rows.append(([(j, nrm[0]), (i, -nrm[0]), (n + j, nrm[1]), (n + i, -nrm[1])], 0.0, w))
            # and keeps at least its length along that direction
            L = length(si)
            if along < L:
                rows.append(([(j, d[0]), (i, -d[0]), (n + j, d[1]), (n + i, -d[1])], L, 4.0))
        for i in range(n):
            w = 400.0 if i in pins else 1.0
            a = pins.get(i, p[i])
            rows.append(([(i, 1.0)], a[0], w))
            rows.append(([(n + i, 1.0)], a[1], w))
        p = lsq(rows, n, coupled=True)
    if os.environ.get("TRAM_DEBUG"):
        for si in range(len(segs)):
            v = p[EJ[si]] - p[EI[si]]
            if np.hypot(*v) < length(si) - 0.3:
                e = SK[segs[si]["edge"]]
                print(f"  short: {nodes[e['u']]['name']} - {nodes[e['v']]['name']} {np.hypot(*v):.2f} of {length(si):.2f}")
    for e in SK.values():
        e["bends"] = [p[bends[e["key"]]]] if e["key"] in bends else []
        e["split"] = (split_h(e, nodes), p[bends[e["key"]]]) if e["key"] in bends else None
    return {k: p[ix[k]] for k in keys}


NOLEVEL_MIN = 2   # the display keeps runs of this many stops or more off the level
BEND_TURNS = (3, 4, 5)   # on the display a free bend turns 45 degrees at most: a run of stops never swings out and back
BEND_90 = {   # (junction, junction) -> True: display stretches allowed a 90-degree bend, where no straighter way has room
}


def not_level(seg, k, v):
    """k, or the 45-degree direction nearest v when k is level and the piece mustn't be."""
    if not seg.get("nolevel") or k not in (0, 4):
        return k
    up = v[1] >= 0
    return (k + 1) % 8 if (k == 0) == up else (k - 1) % 8


def resolve_ports(p, segs, inc, dirs, is_bend):
    """No two pieces leave a junction the same way, and a free bend turns 90 degrees at most."""
    from scipy.optimize import linear_sum_assignment
    for _ in range(4):
        changed = False
        for node, lst in inc.items():
            if len(lst) < 2:
                continue
            ports = [dirs[s] if end == 0 else (dirs[s] + 4) % 8 for s, end in lst]
            ok = len(set(ports)) == len(ports)
            if ok and is_bend[node]:
                ok = (ports[1] - ports[0]) % 8 in is_bend[node]
            if ok:
                continue
            C = np.zeros((len(lst), 8))
            for a_i, (s, end) in enumerate(lst):
                other = segs[s]["j"] if end == 0 else segs[s]["i"]
                v = p[other] - p[node]
                a = math.atan2(v[1], v[0]) if np.hypot(*v) > 1e-9 else ports[a_i] * math.pi / 4
                for k in range(8):
                    C[a_i, k] = abs(wrap(a - k * math.pi / 4))
                    if segs[s].get("nolevel") and k in (0, 4):
                        C[a_i, k] += 100
                    if segs[s]["fixed"] is not None and k != (segs[s]["fixed"] if end == 0 else (segs[s]["fixed"] + 4) % 8):
                        C[a_i, k] += 100
            if is_bend[node] and len(lst) == 2:
                _, a, b = min((C[0, a] + C[1, b], a, b) for a in range(8) for b in range(8) if (b - a) % 8 in is_bend[node])
                assign = [a, b]
            else:
                rr, cc = linear_sum_assignment(C)
                assign = list(ports)
                for a_i, k in zip(rr, cc):
                    assign[a_i] = k
            for (s, end), k in zip(lst, assign):
                nd = k if end == 0 else (k + 4) % 8
                if dirs[s] != nd and segs[s]["fixed"] is None:
                    dirs[s] = nd
                    changed = True
        if not changed:
            break


def separation(p, EI, EJ, nstop):
    rows = []
    n = len(p)
    A, B = p[EI], p[EJ]
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-9)
    adjacent = set(zip(EI, EJ)) | set(zip(EJ, EI))
    nmid = nstop
    # junction to junction
    for i in range(n):
        d = np.hypot(*(p - p[i]).T)
        for k in np.nonzero((d < SEP_KK) & (np.arange(n) > i))[0]:
            if (i, k) in adjacent:
                continue
            v = p[k] - p[i]
            u = v / d[k] if d[k] > 1e-6 else np.array([1.0, 0.0])
            rows.append(([(k, 1.0), (i, -1.0)], SEP_KK * u[0], SEP_KK * u[1], W_SEP))
    # junction to stretch
    for k in range(n):
        t = ((p[k] - A) * AB).sum(1) / L2
        C = A + np.clip(t, 0, 1)[:, None] * AB
        d = np.hypot(*(p[k] - C).T)
        for ei in np.nonzero((d < SEP_KE) & (t > 0.03) & (t < 0.97))[0]:
            if k in (EI[ei], EJ[ei]):
                continue
            v = p[k] - C[ei]
            nrm = v / d[ei] if d[ei] > 1e-6 else np.array([-AB[ei, 1], AB[ei, 0]]) / math.sqrt(L2[ei])
            tt = t[ei]
            rows.append(([(k, 1.0), (EI[ei], -(1 - tt)), (EJ[ei], -tt)], SEP_KE * nrm[0], SEP_KE * nrm[1], W_SEP))
    # stops on one stretch to another stretch
    for ei in np.nonzero(nmid > 0)[0]:
        for f in np.arange(1, nmid[ei] + 1) / (nmid[ei] + 1):
            s = (1 - f) * A[ei] + f * B[ei]
            t = ((s - A) * AB).sum(1) / L2
            C = A + np.clip(t, 0, 1)[:, None] * AB
            d = np.hypot(*(s - C).T)
            for ej in np.nonzero((d < SEP_EE) & (t > 0.03) & (t < 0.97))[0]:
                if ej == ei or len({EI[ei], EJ[ei]} & {EI[ej], EJ[ej]}):
                    continue
                v = s - C[ej]
                nrm = v / d[ej] if d[ej] > 1e-6 else np.array([-AB[ej, 1], AB[ej, 0]]) / math.sqrt(L2[ej])
                tt = t[ej]
                rows.append(([(EI[ei], 1 - f), (EJ[ei], f), (EI[ej], -(1 - tt)), (EJ[ej], -tt)],
                             SEP_EE * nrm[0], SEP_EE * nrm[1], W_SEP))
    return rows


# ---------------------------------------------------------------------------------------------------------------
# Drawn geometry: stretches, stops, routes side by side
def cross2(a, b):
    return a[0] * b[1] - a[1] * b[0]


def octo(a, b, pick):
    """a to b in 45-degree pieces: straight if it can be, else the 45-degree piece first ("diag") or last ("flat")."""
    v = b - a
    dx, dy = v
    tol = 0.04
    if abs(dx) < tol or abs(dy) < tol or abs(abs(dx) - abs(dy)) < tol:
        return [a, b]
    m = min(abs(dx), abs(dy))
    diag = np.array([math.copysign(m, dx), math.copysign(m, dy)])
    return [a, a + diag, b] if pick == "diag" else [a, b - diag, b]


def leg_path(e, pos, nodes, used):
    a, b = np.asarray(pos[e["u"]], float), np.asarray(pos[e["v"]], float)
    pair = frozenset((e["u"], e["v"]))
    if pair in used:
        # a second stretch between the same two junctions bows out beside the first, so the two never lie on top of each other
        ru, rp = used[pair][0]
        base = rp if ru == e["u"] else rp[::-1]
        k = len(used[pair])
        used[pair].append(None)
        e["bow"] = (base, BOW * (1 if k % 2 else -1) * ((k + 1) // 2))
        return bow(*e["bow"])
    path = leg_path_one(e, a, b, nodes)
    used[pair] = [(e["u"], path)]
    return path


def leg_path_one(e, a, b, nodes):
    via, rev = by_names(VIA, nodes, e["u"], e["v"])
    if via:
        pts = [np.array(v, float) for v in (via[::-1] if rev else via)]
        return [a] + pts + [b]
    pick, rev = by_names(BEND, nodes, e["u"], e["v"])
    if pick and rev:
        pick = "flat" if pick == "diag" else "diag"
    if not pick:
        # a leftover bend goes on the side the real stretch bulges to
        qa, qb = nodes[e["u"]]["q"], nodes[e["v"]]["q"]
        dq = sum(cross2(qb - qa, nodes[m_]["q"] - qa) for m_ in e["mids"]) / max(1, len(e["mids"]))
        v = b - a
        m = min(abs(v[0]), abs(v[1]))
        diag = np.array([math.copysign(m, v[0]), math.copysign(m, v[1])])
        pick = "diag" if (dq >= 0) == (cross2(v, diag) >= 0) else "flat"
    way = [a] + [np.asarray(x, float) for x in e.get("bends", [])] + [b]
    path = [a]
    forced = e.get("force_pick")   # one pick per piece, set where a leftover piece would clash
    for k_, (p0, p1) in enumerate(zip(way, way[1:])):
        path += octo(p0, p1, forced[k_] if forced and k_ < len(forced) else pick)[1:]
    # drop repeated points and points where the line runs straight on
    clean_ = [path[0]]
    for k in range(1, len(path)):
        d0 = path[k] - clean_[-1]
        if np.hypot(*d0) < 1e-6:
            continue
        if k + 1 < len(path):
            d1 = path[k + 1] - path[k]
            if np.hypot(*d1) > 1e-6 and abs(cross2(d0, d1)) < 0.02 * np.hypot(*d0) * np.hypot(*d1) and d0 @ d1 > 0:
                continue
        clean_.append(path[k])
    return clean_


def end_ports(SK):
    """Junction -> [(stretch key, way out in 45-degree steps)]."""
    port = defaultdict(list)
    for e in SK.values():
        for end, nid in ((True, e["u"]), (False, e["v"])):
            port[nid].append((e["key"], round((math.degrees(angle_at_end(e["path"], end) + (0 if end else math.pi)) % 360) / 45) % 8))
    return port


def unclash(SK, nodes, pos):
    """Where a leftover 45-degree piece leaves a junction the same way as another stretch, the two would lie on top of each
    other: the piece goes at the other end of its stretch instead."""
    def clashes(port):
        return sum(len(v) - len({d for _, d in v}) for v in port.values())
    for _ in range(3):
        port = end_ports(SK)
        bad = {k_ for v in port.values() for k_, d in v if sum(1 for _, d2 in v if d2 == d) > 1}
        if not bad:
            return
        for k_ in bad:
            e = SK[k_]
            if e.get("bow"):   # a bow can go round the other side
                base, delta = e["bow"]
                old = (clashes(end_ports(SK)), e["path"])
                e["path"] = bow(base, -delta)
                if clashes(end_ports(SK)) < old[0]:
                    e["bow"] = (base, -delta)
                else:
                    e["path"] = old[1]
                continue
            if len(e["path"]) < 3:
                continue
            best = (clashes(end_ports(SK)), e["path"], e.get("force_pick"))
            a, b = np.asarray(pos[e["u"]], float), np.asarray(pos[e["v"]], float)
            n_way = 1 + len(e.get("bends", []))
            import itertools
            for pick in itertools.product(("diag", "flat"), repeat=n_way):
                e["force_pick"] = pick
                e["path"] = leg_path_one(e, a, b, nodes)
                c = clashes(end_ports(SK))
                if c < best[0]:
                    best = (c, e["path"], pick)
            _, e["path"], e["force_pick"] = best


def no_swing(path, e, nodes, pos):
    """A run of stops between two stations stays straight: a path that swings out and back (it bulges from the straight
    line between its ends by under SWING of that line's length, or doubles back on itself) is redrawn as the straight line,
    or the 45-degree pair, between its ends."""
    pts = np.asarray(path, float)
    if len(pts) < 3:
        return path
    a, b = pts[0], pts[-1]
    chord = np.hypot(*(b - a))
    if chord < 1e-6:
        return path
    dev = max(seg_dist(q_, a, b) for q_ in pts[1:-1])
    turn = 0.0
    for p0, p1, p2 in zip(pts, pts[1:], pts[2:]):
        u, v = p1 - p0, p2 - p1
        if np.hypot(*u) > 1e-9 and np.hypot(*v) > 1e-9:
            turn += abs(wrap(math.atan2(v[1], v[0]) - math.atan2(u[1], u[0])))
    if turn > math.radians(100) and dev < SWING * chord:
        pick, rev = by_names(BEND, nodes, e["u"], e["v"])
        if pick and rev:
            pick = "flat" if pick == "diag" else "diag"
        return octo(a, b, pick or "diag")
    return path


SWING = 0.3
BOW = 1.6   # grid steps a second stretch between the same two junctions bows out beside the first


def straighten(SK, nodes, pos):
    """Where a run of stops between two stations swings out and back (a V or a U, its path far longer than the straight
    or one-bend way between its ends), it is redrawn the short way, so the stops sit evenly on a straight line. Only
    where the short way keeps clear of every other stretch and station and leaves the stops room."""
    for e in sorted(SK.values(), key=lambda e: -len(e["mids"])):
        if len(e["mids"]) < 2 or e.get("bow") or by_names(VIA, nodes, e["u"], e["v"])[0]:
            continue
        if any(o is not e and {o["u"], o["v"]} == {e["u"], e["v"]} for o in SK.values()):
            continue   # a pair of stretches between the same two stations: the second bows round the first
        a, b = np.asarray(pos[e["u"]], float), np.asarray(pos[e["v"]], float)
        L = spread_len(e["path"])
        if L <= 1.15 * spread_len(octo(a, b, "diag")):
            continue
        others = [o for o in SK.values() if o is not e]
        keys = {o["u"] for o in SK.values()} | {o["v"] for o in SK.values()}
        best = None
        for pick in ("diag", "flat"):
            cand = octo(a, b, pick)
            if spread_len(cand) / (len(e["mids"]) + 1) < 0.9 * GAP_V:
                continue
            ln = LineString(cand)
            ok = True
            for o in others:
                ol = LineString(o["path"])
                shared = {e["u"], e["v"]} & {o["u"], o["v"]}
                g = ln
                for nid in shared:   # near a shared station the two may meet
                    g = g.difference(Point(pos[nid]).buffer(SEP_KK))
                if not g.is_empty and g.distance(ol) < 0.8 * SEP_EE:
                    ok = False
                    break
            if ok and any(n not in (e["u"], e["v"]) and ln.distance(Point(pos[n])) < SEP_KE for n in keys):
                ok = False
            if ok:
                pref, rev = by_names(BEND, nodes, e["u"], e["v"])
                if pref and rev:
                    pref = "flat" if pref == "diag" else "diag"
                rank = (0 if pick == (pref or pick) else 1)
                if best is None or rank < best[0]:
                    best = (rank, cand)
        if best is not None:
            e["path"] = best[1]
            e.pop("split", None)
            WARN.append(f"straightened the run {nodes[e['u']]['name']} to {nodes[e['v']]['name']} ({len(e['mids'])} stops)")


def bow(path, delta):
    """The path moved sideways by delta grid steps (left of travel is plus), joined to its ends by 45-degree ramps."""
    pts = [np.asarray(p, float) for p in path]
    o = list(offset_poly(np.array(pts), delta))
    d0 = (pts[1] - pts[0]) / np.hypot(*(pts[1] - pts[0]))
    d1 = (pts[-1] - pts[-2]) / np.hypot(*(pts[-1] - pts[-2]))
    ad = abs(delta)
    return [pts[0], o[0] + d0 * ad] + o[1:-1] + [o[-1] - d1 * ad, pts[-1]]


def spread(path, k, split=None, ends=(0.0, 0.0)):
    """k stops spaced evenly along a grid path, kept clear of its bends. Returns their distances along it.
    split: (h, bend spot) puts the first h stops before the stretch's free bend and the rest after it, as the layout sized them.
    ends: the least distance from each end junction to its nearest stop."""
    pts = np.asarray(path, float)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    L = cum[-1]
    corners = list(cum[1:-1])
    if split is None or k < 2 or not 0 < split[0] < k:
        ts = spread_range(0.0, L, k, corners)
    else:
        h, bp = split
        tb = LineString(pts).project(Point(bp))
        bent = any(abs(c - tb) < 1e-3 for c in corners)
        if bent:   # the stops sit evenly up to a short way short of the bend, and on from a short way past it
            ga, gb = (tb - CMIN) / h, (L - tb - CMIN) / (k - h)
            ts = [ga * (i + 1) for i in range(h)] + [tb + CMIN + gb * j for j in range(k - h)]
            if min(ga, gb) < 0.7 * max(ga, gb) and (min(ga, gb) < GAP_V or not DISPLAY):   # one side of the bend would be crowded: evenly along the whole run
                ts = spread_range(0.0, L, k, corners)
        else:
            ts = spread_range(0.0, tb, h, corners) + spread_range(tb, L, k - h, corners)
    if ts and (ts[0] < ends[0] or ts[-1] > L - ends[1]):
        a, b = max(ts[0], ends[0]), min(ts[-1], L - ends[1])
        if len(ts) == 1:
            ts = [min(max(ts[0], ends[0]), L - ends[1])] if ends[0] <= L - ends[1] else [L / 2]
        elif b - a > 0.6 * (ts[-1] - ts[0]):   # squeeze the run a little to clear the ends; never more than that
            t0, t1 = ts[0], ts[-1]
            ts = [a + (t - t0) * (b - a) / (t1 - t0) for t in ts]
    return ts


def spread_range(lo, hi, k, corners):
    """k stops evenly over [lo, hi] along a path, less a short length either side of every bend."""
    if k <= 0:
        return []
    cut = sorted((max(lo, c - CMIN), min(hi, c + CMIN)) for c in corners if lo - CMIN < c < hi + CMIN)
    merged = []
    for a, b in cut:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    free, x = [], lo
    for a, b in merged:
        if a > x:
            free.append((x, a))
        x = max(x, b)
    if x < hi:
        free.append((x, hi))
    total = sum(b - a for a, b in free)
    if total < 0.3 * (hi - lo):   # too bent to keep clear of the bends: just space them evenly
        free, total = [(lo, hi)], hi - lo
    ts = []
    for i in range(k):
        s_ = total * (i + 1) / (k + 1)
        for a, b in free:
            if s_ <= b - a + 1e-9:
                ts.append(a + s_)
                break
            s_ -= b - a
    return ts


def spread_len(path):
    return float(sum(np.hypot(*np.diff(np.asarray(path, float), axis=0).T)))


def point_at(path, t):
    """The spot t grid steps along a path, and the track's angle there."""
    pts = np.asarray(path, float)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    j = min(len(seg) - 1, max(0, int(np.searchsorted(cum, t, side="right") - 1)))
    f = (t - cum[j]) / seg[j] if seg[j] > 0 else 0
    d = pts[j + 1] - pts[j]
    return pts[j] + f * d, math.degrees(math.atan2(d[1], d[0]))


def seg_dist_path(p, path):
    pts = np.asarray(path, float)
    return min(seg_dist(p, a, b) for a, b in zip(pts, pts[1:]))


def off_crossings(SK, clear=0.8, step=0.3):
    """A stop that lands on another route's line slides along its own line until it is clear, keeping its order. On the
    display it also keeps clear of the stops of every other stretch."""
    pclear = 0.78 if DISPLAY else 0.0
    gap = 0.8 if DISPLAY else 0.9

    def stops_of(o):
        pts = [np.asarray(o["path"][0], float), np.asarray(o["path"][-1], float)]
        return pts + [point_at(o["path"], t)[0] for t in o["ts"]]

    for e in SK.values():
        if not e["mids"]:
            continue
        L = sum(np.hypot(*np.diff(np.asarray(e["path"], float), axis=0).T))
        ts = e["ts"]
        foreign = [o["path"] for o in SK.values() if o is not e and not set(o["routes"]) & set(e["routes"])]
        ends = [np.asarray(e["path"][0], float), np.asarray(e["path"][-1], float)]
        others = []
        if pclear:
            for o in SK.values():
                if o is not e:
                    others += [q for q in stops_of(o) if min(np.hypot(*(q - en)) for en in ends) > 1e-6]

        def ok(pt):
            if foreign and min(seg_dist_path(pt, f) for f in foreign) < clear:
                return False
            return not others or min(np.hypot(*(pt - q)) for q in others) >= pclear

        for i, t in enumerate(ts):
            if ok(point_at(e["path"], t)[0]):
                continue
            lo = (ts[i - 1] if i > 0 else 0.0) + gap
            hi = (ts[i + 1] if i + 1 < len(ts) else L) - gap
            for k in range(1, 7):
                done = False
                for t2 in (t + k * step, t - k * step):
                    if lo <= t2 <= hi and ok(point_at(e["path"], t2)[0]):
                        ts[i] = t2
                        done = True
                        break
                if done:
                    break
        def on_line(ts_):   # stops whose symbol would touch another route's line (circle and arms: about 0.4 grid steps)
            return sum(min(seg_dist_path(point_at(e["path"], t)[0], f) for f in foreign) < 0.4 for t in ts_) if foreign else 0
        if DISPLAY and foreign and on_line(ts):
            # first, the whole run slid a little along its line
            best_ = (on_line(ts), 0.0)
            for d_ in sorted(np.arange(-0.45, 0.4501, 0.05), key=abs):
                ts2 = [t + d_ for t in ts]
                if ts2[0] >= 0.45 and ts2[-1] <= L - 0.45 and on_line(ts2) < best_[0]:
                    best_ = (on_line(ts2), d_)
            if best_[1]:
                ts[:] = [t + best_[1] for t in ts]
        if DISPLAY and foreign and on_line(ts):
            # evenly again, keeping a bend's length clear either side of every other route's crossing
            mine = LineString(e["path"])
            cross = []
            for f in foreign:
                g = mine.intersection(LineString(f))
                for q in getattr(g, "geoms", [g]):
                    if not q.is_empty and q.geom_type == "Point":
                        cross.append(mine.project(q))
            pts_ = np.asarray(e["path"], float)
            seg_ = np.hypot(*np.diff(pts_, axis=0).T)
            corners = list(np.cumsum(seg_)[:-1]) + cross
            ts2 = spread_range(ts[0] - 0.4, ts[-1] + 0.4, len(ts), corners)
            if on_line(ts2) < on_line(ts) and min(np.diff([0.0] + ts2 + [L])) >= 0.75 * GAP_V:
                ts[:] = ts2


def angle_at_end(path, start):
    a, b = (path[0], path[1]) if start else (path[-2], path[-1])
    return math.atan2(b[1] - a[1], b[0] - a[0])


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def geometry(nodes, routes, SK, pos):
    """Grid paths for every stretch, spots for every stop, and each route's drawn line in drawing units."""
    if DISPLAY:   # small hand nudges after the layout, so a pin doesn't reshape the whole sheet
        for n in pos:
            if nodes[n]["name"] in NUDGE_DISPLAY:
                pos[n] = np.asarray(pos[n], float) + np.asarray(NUDGE_DISPLAY[nodes[n]["name"]], float)
    used = {}
    for e in sorted(SK.values(), key=lambda e: (-len(e["mids"]), -len(e["routes"]), e["key"])):
        e["path"] = leg_path(e, pos, nodes, used)
        if DISPLAY and e["mids"]:
            e["path"] = no_swing(e["path"], e, nodes, pos)
        e["ts"] = None
    straighten(SK, nodes, pos)
    if DISPLAY:
        unclash(SK, nodes, pos)
    port = defaultdict(list)
    for e in SK.values():
        for end, nid in ((True, e["u"]), (False, e["v"])):
            port[nid].append((e["key"], end, math.degrees(angle_at_end(e["path"], end) + (0 if end else math.pi)) % 360))
    for e in SK.values():
        clear = []
        for end, nid in ((True, e["u"]), (False, e["v"])):
            mine = math.degrees(angle_at_end(e["path"], end) + (0 if end else math.pi)) % 360
            near = any(k_ != e["key"] and abs((a - mine + 180) % 360 - 180) < 50 for k_, _, a in port[nid])
            c_ = (1.0 if DISPLAY else 2.0) if near else 0.0   # the display's stops are closer: a shorter gap will do
            if DISPLAY and len(port[nid]) >= 3:   # where lines cross or part, the first stops stand back, so the station's name has room
                c_ = (c_, max(c_, 1.3))
            clear.append(c_)
        if any(isinstance(c_, tuple) for c_ in clear):   # only where the run still keeps its stops a full gap apart
            wide = [c_[1] if isinstance(c_, tuple) else c_ for c_ in clear]
            ok_ = (spread_len(e["path"]) - sum(wide)) / (len(e["mids"]) + 1) >= GAP_V
            clear = wide if ok_ else [c_[0] if isinstance(c_, tuple) else c_ for c_ in clear]
        e["ts"] = (spread_range(clear[0], spread_len(e["path"]) - clear[1], len(e["mids"]), []) if e.get("bow")   # a bow: evenly, ramps and all
                   else spread(e["path"], len(e["mids"]), e.get("split"), tuple(clear)))
    off_crossings(SK)
    for e in SK.values():
        for nid, t in zip(e["mids"], e["ts"]):
            pos[nid], nodes[nid]["ang"] = point_at(e["path"], t)
    # junction cross direction: the way most lines pass through
    votes = defaultdict(lambda: defaultdict(float))
    for e in SK.values():
        for end, nid in ((True, e["u"]), (False, e["v"])):
            a = math.degrees(angle_at_end(e["path"], end)) % 90
            votes[nid][round(a / 45) % 2] += len(e["routes"])
    for nid in pos:
        if "ang" not in nodes[nid] or nid in votes:
            v = votes.get(nid)
            nodes[nid]["ang"] = 45.0 * max(v, key=v.get) if v else 0.0
    # order routes side by side on each shared stretch
    rleg = {}
    for r in routes:
        for i, (c, fwd) in enumerate(r["legs"]):
            rleg[(r["id"], c)] = (r, i, fwd)
    for e in SK.values():
        if len(e["routes"]) < 2:
            e["slot"] = {e["routes"][0]: 0.0}
            continue
        a0, a1 = angle_at_end(e["path"], True), angle_at_end(e["path"], False)
        score = {}
        for rid in e["routes"]:
            r, i, fwd = rleg[(rid, e["key"])]
            legs = r["legs"]
            t_u = t_v = 0.0
            # canonical u -> v; what the route does before u and after v
            prev = legs[i - 1] if i > 0 else None
            nxt = legs[i + 1] if i + 1 < len(legs) else None
            before, after = (prev, nxt) if fwd else (nxt, prev)
            if before is not None:
                pe = SK[before[0]]
                # direction into u along that leg, as the route rides it toward u
                into = angle_at_end(pe["path"], False) if pe["v"] == e["u"] else angle_at_end(pe["path"], True) + math.pi
                t_u = wrap(a0 - into)
            if after is not None:
                ne = SK[after[0]]
                out = angle_at_end(ne["path"], True) if ne["u"] == e["v"] else angle_at_end(ne["path"], False) + math.pi
                t_v = wrap(out - a1)
            score[rid] = t_u + t_v
        order = sorted(e["routes"], key=lambda rid: (-score[rid], rid))
        nr = len(order)
        e["slot"] = {rid: ((nr - 1) / 2 - s) * PARU for s, rid in enumerate(order)}
    # each route's line, in drawing units
    for e in SK.values():
        xy = np.asarray(e["path"], float) * P
        e["xy"] = rounded(xy, RR) if len(xy) > 2 else xy
    for r in routes:
        parts = []
        for c, fwd in r["legs"]:
            e = SK[c]
            off = e["slot"][r["id"]]
            xy = offset_poly(e["xy"], off) if abs(off) > 1e-6 else np.asarray(e["xy"], float)
            parts.append(xy if fwd else xy[::-1])
        r["xy"] = np.concatenate(parts)
        r["parts"] = parts


def offset_poly(xy, off):
    """A polyline moved sideways by off (left of travel is plus), with mitred corners."""
    xy = np.asarray(xy, float)
    keep = [0] + [i for i in range(1, len(xy)) if np.hypot(*(xy[i] - xy[i - 1])) > 1e-9]
    xy = xy[keep]
    d = np.diff(xy, axis=0)
    d /= np.hypot(*d.T)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    out = [xy[0] + off * nrm[0]]
    for i in range(1, len(xy) - 1):
        m = nrm[i - 1] + nrm[i]
        out.append(xy[i] + off * m / max(1e-6, 1 + nrm[i - 1] @ nrm[i]))
    out.append(xy[-1] + off * nrm[-1])
    return np.array(out)


# ---------------------------------------------------------------------------------------------------------------
# Text and furniture helpers
FP = {}


def fprop(weight):
    if weight not in FP:
        FP[weight] = FontProperties(family="Arial", weight=weight)
    return FP[weight]


@lru_cache(maxsize=None)
def ink(text, fs, weight):
    """Ink box of one line of text in drawing units, from the pen at the baseline: (x0, y0, x1, y1)."""
    if not text.strip():
        return 0.0, 0.0, 0.3 * fs / PPU, 0.7 * fs / PPU
    e = TextPath((0, 0), text, size=fs, prop=fprop(weight)).get_extents()
    return e.x0 / PPU, e.y0 / PPU, e.x1 / PPU, e.y1 / PPU


def curly(s):
    return s.replace("'", "’")


def text_block(text, fs, weight, align):
    """Lines of text centered on y = 0 (caps centered), starting at x = 0. Returns width, y0, y1, [(line, pen x, baseline)]."""
    lines = curly(text).split("\n")
    pitch, cap = fs * 1.2 / PPU, 0.716 * fs / PPU
    top = (len(lines) - 1) * pitch / 2 - cap / 2
    inks = [ink(ln, fs, weight) for ln in lines]
    w = max(i[2] - i[0] for i in inks)
    out, y0, y1 = [], 1e9, -1e9
    for k, (ln, (a, b, c, d)) in enumerate(zip(lines, inks)):
        base = top - k * pitch
        lw = c - a
        x = {"left": 0.0, "right": w - lw, "center": (w - lw) / 2}[align] - a
        out.append((ln, x, base))
        y0, y1 = min(y0, base + min(b, -0.02 * fs / PPU)), max(y1, base + max(d, cap))
    pad = 0.12 * fs / PPU   # a little paper above and below, so two names never stack into one
    return w, y0 - pad, y1 + pad, out


def badge_w(label):
    a, _, c, _ = ink(label, FS_BADGE, "bold")
    return max(BADGE_H * 1.3, c - a + 2.0)


def row_layout(items, align):
    """Lay out a level row, left to right, centered on y = 0.
    items: ("text", s, fs, weight, color) | ("pill", code) | ("badge", label). Returns width, y0, y1 and parts:
    (kind, x0, x1, y0, y1, payload) in row coordinates."""
    x, parts, prev = 0.0, [], None
    for it in items:
        kind = it[0]
        if prev is not None:
            x += {("pill", "pill"): PILL_GAP, ("badge", "badge"): 0.45}.get((prev, kind), 1.0)
        if kind == "text":
            w, y0, y1, lines = text_block(it[1], it[2], it[3], align)
            parts.append(("text", x, x + w, y0, y1, (lines, it[2], it[3], it[4])))
        elif kind == "pill":
            w = PILL_W
            parts.append(("pill", x, x + w, -PILL_H / 2, PILL_H / 2, it[1]))
        else:
            w = badge_w(it[1])
            parts.append(("badge", x, x + w, -BADGE_H / 2, BADGE_H / 2, it[1]))
        x += w
        prev = kind
    return x, min(p[3] for p in parts), max(p[4] for p in parts), parts


def row_stacked(items, align, above=False):
    """The name with its pills on a second row under it, both aligned to the stop's side: a compact block for a long row.
    The name's capitals stay centered on y = 0, so beside a stop the name is level with it."""
    _, text, fs, weight, color = items[0]
    pills = [it_[1] for it_ in items[1:] if it_[0] == "pill"]
    wt, ty0, ty1, lines = text_block(text, fs, weight, align)
    pw = len(pills) * PILL_W + max(0, len(pills) - 1) * PILL_GAP
    w = max(wt, pw)
    xt = {"left": 0.0, "right": w - wt, "center": (w - wt) / 2}[align]
    xp = {"left": 0.0, "right": w - pw, "center": (w - pw) / 2}[align]
    parts = [("text", xt, xt + wt, ty0, ty1, (lines, fs, weight, color))]
    yc = ty1 + 0.3 + PILL_H / 2 if above else ty0 - 0.3 - PILL_H / 2
    for i, c in enumerate(pills):
        x = xp + i * (PILL_W + PILL_GAP)
        parts.append(("pill", x, x + PILL_W, yc - PILL_H / 2, yc + PILL_H / 2, c))
    return w, min(p_[3] for p_ in parts), max(p_[4] for p_ in parts), parts


SIDES = {"r": (1, 0), "l": (-1, 0), "t": (0, 1), "b": (0, -1), "tr": (1, 1), "tl": (-1, 1), "br": (1, -1), "bl": (-1, -1)}


def side_box(side, w, y0, y1):
    """The row's box relative to its attach point, for a label on this side of the thing it names."""
    h = y1 - y0
    sx, sy = SIDES[side]
    x0 = 0.0 if sx > 0 else (-w if sx < 0 else -w / 2)
    ylo = 0.0 if sy > 0 else (-h if sy < 0 else y0)   # level with the stop: the caps stay centered on it
    return x0, ylo, x0 + w, ylo + h


# ---------------------------------------------------------------------------------------------------------------
# Placement of labels, badges and route names
class Board:
    """Everything already on the sheet, for the overlap search."""

    def __init__(self):
        self.static = []      # (owner, kind, shape)
        self.tree = None
        self.dyn = defaultdict(list)   # grid cell -> [(item id, kind, shape)]
        self.cell = 12.0

    def add_static(self, owner, kind, shp):
        self.static.append((owner, kind, shp))

    def freeze(self, centers):
        from scipy.spatial import cKDTree
        self.tree = STRtree([s for _, _, s in self.static])
        self.cid = list(centers)
        self.cxy = np.array([centers[c] for c in self.cid])
        self.ctree = cKDTree(self.cxy)

    def cells(self, b):
        x0, y0, x1, y1 = b
        for i in range(int(math.floor(x0 / self.cell)), int(math.floor(x1 / self.cell)) + 1):
            for j in range(int(math.floor(y0 / self.cell)), int(math.floor(y1 / self.cell)) + 1):
                yield (i, j)

    def put(self, item, shapes):
        for kind, shp in shapes:
            for c in self.cells(shp.bounds):
                self.dyn[c].append((item, kind, shp))

    def take(self, item, shapes):
        for kind, shp in shapes:
            for c in self.cells(shp.bounds):
                self.dyn[c] = [t for t in self.dyn[c] if t[0] is not item]

    def near_dyn(self, shp, pad):
        x0, y0, x1, y1 = shp.bounds
        seen = set()
        for c in self.cells((x0 - pad, y0 - pad, x1 + pad, y1 + pad)):
            for t in self.dyn.get(c, ()):
                if id(t) not in seen:
                    seen.add(id(t))
                    yield t


CLEAR = 0.7    # drawing units of clear paper wanted round every label


def box_gap(a, b):
    """Overlap area of two boxes (bounds tuples), and the gap between them when they don't overlap."""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w > 0 and h > 0:
        return w * h, 0.0
    return 0.0, math.hypot(max(0.0, -w), max(0.0, -h))


def cost(board, item, shapes, canvas):
    s = 0.0
    hits = []
    for kind, shp in shapes:
        for j in board.tree.query(shp, predicate="dwithin", distance=1.7 if item.kind == "caption" else CLEAR):
            owner, okind, o = board.static[j]
            if owner == item.owner and okind == "sym":
                continue
            if item.kind == "caption" and okind == "line":   # a route name never sits on or hugs a line
                d_ = shp.distance(o)
                if d_ < 1e-6:
                    s += 500
                    hits.append((okind, owner))
                elif d_ < (0.8 if owner == item.owner else 1.6):
                    s += 40
                continue
            if shp.intersects(o):
                a = shp.intersection(o).area
                if a > 1e-4:
                    if kind == "pill" and okind == "line" and item.kind == "label":
                        # Max: a pill over a line (its paper edge is its halo) beats a pill confusingly far away
                        s += 30 + 2 * a
                    elif kind == "text" and okind == "line":
                        # Max: better a name over a line, on a paper halo, than a name confusingly far from its stop
                        s += 14 + 2 * a
                    else:   # a name over a stop or a pill is worse than any spot a little further off
                        s += 300 + 40 * a
                        hits.append((okind, owner))
                    continue
            if okind == "line":
                if shp.distance(o) < CLEAR * 0.6:   # a name grazing a line reads as crossing it
                    s += 25
            else:
                s += 4
        b = shp.bounds
        roomy = 3.0 if item.kind == "caption" else CLEAR   # a route name keeps well clear of names and badges
        for other, okind, o in board.near_dyn(shp, max(roomy, ROWGAP)):
            if other is item:
                continue
            ob = o.bounds
            a, gap = box_gap(b, ob)
            if a > 1e-4:
                s += 300 + 40 * a
                hits.append((okind, other.owner))
                continue
            if gap < roomy:
                s += 30 if (kind == "text" and okind == "text" and gap < 0.5) else 6
            if other.owner != item.owner and run_together(b, ob):   # two rows on one level, close: they read as one
                s += 40
                hits.append(("row", other.owner))
            if (other.owner != item.owner and item.kind in ("label", "badge") and other.kind in ("label", "badge")
                    and len({kind, okind} & {"pill", "badge"}) == 1 and "text" in {kind, okind} and under_other(b, ob)):
                s += 60   # a pill or an end badge right under or over another station's name reads as that station's
                hits.append(("under", other.owner))
            if (other.owner != item.owner and item.kind == "label" and other.kind == "label" and kind == okind == "text"
                    and stacked_like_one(b, ob)):
                s += 60   # two names stacked close read as one two-line name
                hits.append(("stack", other.owner))
            if item.kind == "caption" and (okind == "badge" or (other.kind == "label" and getattr(other, "term", False))) and gap < 6.0:
                s += 80   # a route name never reads as one more end badge, nor as a terminal's route
                hits.append(("badge", other.owner))
        if canvas is not None and not canvas.contains(shp):
            s += 400
    if item.kind == "caption":   # a route name keeps off the stops, so it can't be read as a stop's name
        x0, y0, x1, y1 = unary_union([s_ for _, s_ in shapes]).bounds
        c = ((x0 + x1) / 2, (y0 + y1) / 2)
        for j in board.ctree.query_ball_point(c, math.hypot(x1 - x0, y1 - y0) / 2 + ARMU + 3.0):
            if any(s_.distance(Point(board.cxy[j])) < ARMU + 2.5 for _, s_ in shapes):
                s += 15
    for _, fshp in REG["free"]:   # the FREE tag keeps a little paper round it
        if any(sh.distance(fshp) < (4.0 if item.kind == "caption" else 1.0) for _, sh in shapes):
            s += 300
            hits.append(("free", "free"))
    # a name sits clearly nearer its own stop than any other stop or station; its whole row at least nearer
    if item.center is not None and shapes:
        for j, dj, d_own in near_others(board, item, shapes):
            s += 150 + 40 * (d_own + NEAR - dj)
            hits.append(("near", board.cid[j]))
        if item.kind == "label":
            for j, dj, d_own in near_others_row(board, item, shapes):
                s += 150
                hits.append(("near", board.cid[j]))
            for j in level_others(board, item, shapes):
                s += 80
                hits.append(("level", board.cid[j]))
            for k_, sh in shapes:
                if k_ == "text":   # the name's centre is nearer its own stop than any other
                    for j in centre_others(board, item, sh):
                        s += 80
                        hits.append(("centre", board.cid[j]))
                elif k_ == "pill":   # and so is every pill's, and no pill sits level beside another stop
                    for j in centre_others(board, item, sh, "pill"):
                        s += 80
                        hits.append(("pill", board.cid[j]))
                    for j in level_with(board, sh, item.owner, item.center, reach=2.0 * PILL_W):
                        s += 60
                        hits.append(("pill level", board.cid[j]))
        if item.kind == "badge":
            for j in centre_others(board, item, unary_union([sh for _, sh in shapes]), "badge"):
                s += 80
                hits.append(("badge", board.cid[j]))
    if item.kind == "caption":   # a route name never sits level beside a stop, where that stop's name would go
        tx = [sh for k_, sh in shapes if k_ == "text"]
        for j in level_with(board, unary_union(tx or [sh for _, sh in shapes]), None):
            s += 100
            hits.append(("level", board.cid[j]))
    if item.kind == "caption":   # a route name sits nearer its own route's line than any other route's
        own_d, other_d = 1e9, 1e9
        allsh = unary_union([s_ for _, s_ in shapes])
        for j in board.tree.query(allsh, predicate="dwithin", distance=9.0):
            ow, ok_, o = board.static[j]
            if ok_ != "line":
                continue
            d_ = allsh.distance(o)
            if ow == item.owner:
                own_d = min(own_d, d_)
            else:
                other_d = min(other_d, d_)
        if other_d < own_d + 1.5:
            s += 400
            hits.append(("line", "other route"))
    return s, hits


def near_others_row(board, item, shapes):
    """The whole row (name and pills) is at least nearer its own stop than any other."""
    row = unary_union([sh for _, sh in shapes])
    d_own = row.distance(Point(item.center))
    x0, y0, x1, y1 = row.bounds
    out = []
    for j in board.ctree.query_ball_point(((x0 + x1) / 2, (y0 + y1) / 2), math.hypot(x1 - x0, y1 - y0) / 2 + d_own + 0.5):
        if board.cid[j] != item.owner and row.distance(Point(board.cxy[j])) < d_own - 0.05:
            out.append((j, 0.0, d_own))
    return out


LABEL_GAP = 0.9   # drawing units of paper between a stop symbol and its name


def wrap2(text):
    """The name on two lines, split at the space that best balances them; None for one word or a name already broken."""
    if chr(10) in text or " " not in text or len(text) < 9:
        return None
    words = text.split(" ")
    best = min(range(1, len(words)), key=lambda i: max(len(" ".join(words[:i])), len(" ".join(words[i:]))))
    return " ".join(words[:best]) + chr(10) + " ".join(words[best:])


NEAR = 1.0     # drawing units: a name's own stop is at least this much nearer than any other
ROWGAP = 6.6   # drawing units: two rows on one level keep a pill's width apart


def near_others(board, item, shapes, margin=None):
    """(index, distance, own distance) for every stop or station the name is not clearly further from than its own.
    For a station name that is the name itself, not its pills (round-2 audit: a name with its pills reaching the stop
    still reads as the neighbor's); for badges, the whole row."""
    margin = NEAR if margin is None else margin
    parts = [sh for k_, sh in shapes if k_ == "text"] if item.kind == "label" else []
    row = unary_union(parts or [sh for _, sh in shapes])
    d_own = row.distance(Point(item.center))
    x0, y0, x1, y1 = row.bounds
    c = ((x0 + x1) / 2, (y0 + y1) / 2)
    out = []
    for j in board.ctree.query_ball_point(c, math.hypot(x1 - x0, y1 - y0) / 2 + d_own + margin + 0.5):
        if board.cid[j] == item.owner:
            continue
        dj = row.distance(Point(board.cxy[j]))
        if dj < d_own + margin:
            out.append((j, dj, d_own))
    return out


def level_others(board, item, shapes):
    """Stops a name sits level with, close beside, other than its own: the stair-step a reader pairs wrongly."""
    tx = [sh for k_, sh in shapes if k_ == "text"]
    if item.kind != "label" or not tx:
        return []
    x0, y0, x1, y1 = unary_union(tx).bounds
    h = y1 - y0
    lo, hi = y0 + 0.15 * h, y1 - 0.15 * h

    def hgap(x):
        return max(x0 - x, x - x1, 0.0)
    own = np.asarray(item.center, float)
    own_level = lo <= own[1] <= hi
    out = []
    reach = max(6.0, 3.0 * h)   # "close beside": within about three text heights
    for j in board.ctree.query_ball_point(((x0 + x1) / 2, (y0 + y1) / 2), (x1 - x0) / 2 + reach + 1.0):
        if board.cid[j] == item.owner:
            continue
        q = board.cxy[j]
        if lo <= q[1] <= hi and hgap(q[0]) < reach and (not own_level or hgap(q[0]) < hgap(own[0]) + 2.0):
            out.append(j)
    return out


def stacked_like_one(b, ob):
    """Two names one over the other, overlapping side to side, closer than about two thirds of a line: one name to a reader."""
    w = min(b[2], ob[2]) - max(b[0], ob[0])
    if w < 0.3 * min(b[2] - b[0], ob[2] - ob[0]):
        return False
    vgap = max(ob[1] - b[3], b[1] - ob[3])
    return 0 <= vgap < 0.65 * 1.2 * FS / PPU


def centre_others(board, item, part, kind="text"):
    """Stops a name's or a pill's centre belongs to more than its own stop (the audit's centre rule). A name counts only
    when it floats off its stop (further than a normal label gap); a pill when another stop is clearly nearer its centre."""
    x0, y0, x1, y1 = part.bounds
    c = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
    d_own = float(np.hypot(*(c - np.asarray(item.center, float))))
    if kind == "text":
        if part.distance(Point(item.center)) < ARMU + LABEL_GAP + 1.0:
            return []
        lim = d_own - 0.05
    else:
        lim = 0.8 * d_own
    return [j for j in board.ctree.query_ball_point(c, d_own) if board.cid[j] != item.owner
            and float(np.hypot(*(c - board.cxy[j]))) < lim]


def level_with(board, part, owner, own_xy=None, reach=None):
    """Stops a box sits level with, close beside, other than its owner: a reader pairs the box with them."""
    x0, y0, x1, y1 = part.bounds
    h = y1 - y0
    lo, hi = y0 + 0.15 * h, y1 - 0.15 * h
    reach = reach or max(6.0, 3.0 * h)

    def hgap(x):
        return max(x0 - x, x - x1, 0.0)
    own_level = own_xy is not None and lo <= own_xy[1] <= hi
    out = []
    for j in board.ctree.query_ball_point(((x0 + x1) / 2, (y0 + y1) / 2), (x1 - x0) / 2 + reach + 1.0):
        if board.cid[j] == owner:
            continue
        q = board.cxy[j]
        if lo <= q[1] <= hi and hgap(q[0]) < reach and (not own_level or hgap(q[0]) < hgap(own_xy[0]) + 2.0):
            out.append(j)
    return out


def under_other(b, ob):
    """A pill right under or over another station's name (or a name right under or over another's pill): it reads as
    that station's transfer."""
    w = min(b[2], ob[2]) - max(b[0], ob[0])
    if w < 0.3 * min(b[2] - b[0], ob[2] - ob[0]):
        return False
    vgap = max(ob[1] - b[3], b[1] - ob[3])
    return 0 <= vgap < 1.4


def run_together(a, b):
    """Two boxes on one level, closer side to side than a pill's width."""
    ov = min(a[3], b[3]) - max(a[1], b[1])
    if ov < 0.15 * min(a[3] - a[1], b[3] - b[1]):
        return False
    hgap = max(b[0] - a[2], a[0] - b[2])
    return 0 <= hgap < ROWGAP


class Item:
    def __init__(self, kind, owner, cands, center=None, prio=0.0):
        self.kind, self.owner, self.cands, self.center, self.prio = kind, owner, cands, center, prio
        self.choice = None
        self.score = 0.0


def make_cands(center, own, items_fwd, sides, pref, gap=0.9, extra=(0.0, 0.8), mirror=False, stacked=False, above=False):
    """Candidate spots for a row of text, pills and badges on each side of a symbol, pushed out until clear of it.
    The row always reads name first, pills after, as the Key says, on whichever side it sits.
    mirror: on the left, the row reads outward (pills before the name), as on the ferry poster."""
    out = []
    own_b = own.buffer(gap)
    cx, cy = center
    for side in sides:
        sx, sy = SIDES[side]
        its = items_fwd if (sx >= 0 or not mirror) else items_fwd[::-1]
        align = "left" if sx > 0 else ("right" if sx < 0 else "center")
        w, y0, y1, parts = row_stacked(its, align, above) if stacked else row_layout(its, align)
        bx0, by0, bx1, by1 = side_box(side, w, y0, y1)
        u = np.array([sx, sy], float)
        u /= np.hypot(*u)

        def at(t):
            return box(cx + u[0] * t + bx0, cy + u[1] * t + by0, cx + u[0] * t + bx1, cy + u[1] * t + by1)
        lo, hi = 0.0, 0.5
        while at(hi).intersects(own_b) and hi < 40:
            lo, hi = hi, hi * 1.6
        for _ in range(12):
            mid = (lo + hi) / 2
            if at(mid).intersects(own_b):
                lo = mid
            else:
                hi = mid
        # beside the stop a row may also sit a little high or low; above or below it, a little left or right
        nudges = [(0.0, 0.0)] + ([(0.0, -SHIFT), (0.0, SHIFT)] if side in ("r", "l") else
                                 [(-2 * SHIFT, 0.0), (2 * SHIFT, 0.0)] if side in ("t", "b") else [])
        for ex in extra:
            t = hi + ex
            for nx_, ny_ in nudges:
                # row coordinates to the sheet: the row's left edge on the box's left, its lowest point on the box's bottom
                ox, oy = cx + u[0] * t + bx0 + nx_, cy + u[1] * t + by0 - y0 + ny_
                placed = [(kind, a + ox, b + ox, p0 + oy, p1 + oy, payload) for kind, a, b, p0, p1, payload in parts]
                shapes = [(k, box(a, p0, b, p1)) for k, a, b, p0, p1, _ in placed]
                if (nx_ or ny_) and any(sh.intersects(own_b) for _, sh in shapes):
                    continue
                out.append(dict(side=side, parts=placed, shapes=shapes, pref=pref.get(side, 1.0) + 0.8 * ex + (0.4 if nx_ or ny_ else 0.0)))
    return out


SHIFT = 0.6   # drawing units a row may sit off level with its stop


def place_all(board, items, canvas, passes=8):
    items.sort(key=lambda it: -it.prio)
    by_owner = defaultdict(list)
    for it in items:
        by_owner[it.owner].append(it)
        choose(board, it, canvas)
    for _ in range(passes):
        bad = [it for it in items if it.score >= 100]
        if not bad:
            break
        for it in bad:
            # lift it and whatever it runs into, then put them back, the stuck one first
            group = [it] + [o for _, ow in it.hits for o in by_owner.get(ow, []) if o is not it and o.choice is not None]
            seen, todo = set(), []
            for g in group:
                if id(g) not in seen:
                    seen.add(id(g))
                    todo.append(g)
            for g in todo:
                board.take(g, g.choice["shapes"])
            for g in todo:
                choose(board, g, canvas)
    for _ in range(POLISH):   # then each row in turn takes its best spot given all the others, worst first
        changed = 0
        for it in sorted(items, key=lambda it: -it.score):
            old = it.choice
            board.take(it, it.choice["shapes"])
            choose(board, it, canvas)
            changed += it.choice is not old
        if not changed:
            break


POLISH = 4


def choose(board, it, canvas, only=None):
    best = None
    for c in it.cands:
        if only is not None and c["side"] != only:
            continue
        s, hits = cost(board, it, c["shapes"], canvas)
        s += c["pref"]
        if best is None or s < best[0]:
            best = (s, c, hits)
    if best is None:
        return None
    it.score, it.choice, it.hits = best
    board.put(it, it.choice["shapes"])
    return best


def harmonize(board, items, canvas, SK, nodes):
    """On an upright or 45-degree run of stops, names go on one side where they can, as on a station's line diagram."""
    lab = {it.owner: it for it in items if it.kind == "label"}
    for e in SK.values():
        mids = [m for m in e["mids"] if m in lab]
        if len(mids) < 3:
            continue
        if all(abs(math.sin(math.radians(nodes[m]["ang"]))) < 0.2 for m in mids):
            continue   # level runs alternate above and below
        count = defaultdict(int)
        for m in mids:
            count[lab[m].choice["side"]] += 1
        maj = max(count, key=count.get)
        for m in mids:
            it = lab[m]
            if it.choice["side"] == maj or it.score >= 100:
                continue
            old = (it.score, it.choice, it.hits)
            board.take(it, it.choice["shapes"])
            best = None
            for c in it.cands:
                if c["side"] != maj:
                    continue
                s, hits = cost(board, it, c["shapes"], canvas)
                s += c["pref"]
                if best is None or s < best[0]:
                    best = (s, c, hits)
            if best is not None and best[0] <= old[0] + 3 and best[0] < 100:
                it.score, it.choice, it.hits = best
            else:
                it.score, it.choice, it.hits = old
            board.put(it, it.choice["shapes"])


# ---------------------------------------------------------------------------------------------------------------
# Drawing
TEXTS = []   # (artist, owner) for the overlap check
HALO_FX = [pe.withStroke(linewidth=2.6, foreground=PAPER)]   # paper halo: a name over a line stays readable
REG = {"line": [], "sym": [], "pill": [], "badge": [], "free": []}
FREE_ROUTES = ("23",)   # Max, November 8: tram 23 is free


def FREE_H():
    """The FREE tag's height: 11 points on both sheets, so it reads (the coordinator, November 8). The spec's 1.4 times the
    line width would leave FREE about a point high on these thin tram lines."""
    return 11.0 / PPU


def free_w(h):
    from charlie_points import BOLD
    ref = TextPath((0, 0), "FREE", size=1, prop=BOLD).get_extents()
    cap = h * 0.45
    return (ref.x1 - ref.x0) * cap / TextPath((0, 0), "F", size=1, prop=BOLD).get_extents().y1 + h


def free_spot(r):
    """A spot on the route's own line, as near mid-route as can be, clear of every stop and of every other route's line."""
    h = FREE_H()
    w = free_w(h)
    xy = np.asarray(r["xy"], float)
    seg = np.hypot(*np.diff(xy, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    L = cum[-1]
    syms = STRtree([s_ for _, s_ in REG["sym"]])
    foreign = [s_ for rid, s_ in REG["line"] if rid != r["id"]]
    tree_f = STRtree(foreign) if foreign else None
    for t in sorted(np.linspace(0.08, 0.92, 169) * L, key=lambda t: abs(t - L / 2)):
        j = min(len(seg) - 1, max(0, int(np.searchsorted(cum, t, side="right") - 1)))
        f = (t - cum[j]) / seg[j] if seg[j] > 0 else 0
        x, y = xy[j] + f * (xy[j + 1] - xy[j])
        shp = box(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
        clear = shp.buffer(1.0)
        if len(syms.query(clear, predicate="intersects")):
            continue
        if tree_f is not None and len(tree_f.query(shp.buffer(0.3), predicate="intersects")):
            continue
        return (x, y), shp
    return None


def draw_row(ax, parts, owner, z=11):
    for kind, a, b, y0, y1, payload in parts:
        if kind == "text":
            lines, fs, weight, color = payload
            # row coordinates were centered on 0; the block's own y0 sits at y0 here
            _, by0, _, _ = text_block_bounds(lines, fs, weight)
            for ln, x, base in lines:
                t = ax.text(a + x, base + (y0 - by0), ln, fontsize=fs, fontweight=weight, color=color, ha="left", va="baseline",
                            zorder=z, family="Arial", path_effects=HALO_FX)
                TEXTS.append((t, owner))
        elif kind == "pill":
            draw_pill(ax, a, b, (y0 + y1) / 2, payload)
        else:
            draw_badge(ax, a, b, (y0 + y1) / 2, payload)


def text_block_bounds(lines, fs, weight):
    cap = 0.716 * fs / PPU
    y0, y1 = 1e9, -1e9
    for ln, x, base in lines:
        a, b, c, d = ink(ln, fs, weight)
        y0, y1 = min(y0, base + min(b, -0.02 * fs / PPU)), max(y1, base + max(d, cap))
    pad = 0.12 * fs / PPU
    return 0, y0 - pad, 0, y1 + pad


def draw_pill(ax, x0, x1, y, code, z=10.5):
    h = PILL_H
    ax.add_patch(FancyBboxPatch((x0, y - h / 2), x1 - x0, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=PILL[code], ec=PAPER,
                                lw=1.2, zorder=z))
    if code == "HSR":   # high-speed pills copy the map line: gold inside commuter purple
        r = 0.55
        ax.add_patch(FancyBboxPatch((x0 + r, y - h / 2 + r), x1 - x0 - 2 * r, h - 2 * r, boxstyle=f"round,pad=0,rounding_size={h / 2 - r}",
                                    fc=M.HSR, ec="none", zorder=z + 0.05))
    color = "#80276c" if code == "HSR" else (INK if code == "YL" else WHITE)
    ax.text((x0 + x1) / 2, y - 0.08, code, fontsize=FS_PILL, fontweight="bold", color=color, ha="center", va="center", zorder=z + 0.5,
            family="Arial")
    REG["pill"].append(box(x0, y - h / 2, x1, y + h / 2))


def draw_badge(ax, x0, x1, y, label, z=10.6):
    h = BADGE_H
    ax.add_patch(FancyBboxPatch((x0, y - h / 2), x1 - x0, h, boxstyle="round,pad=0,rounding_size=0.75", fc=TRAM, ec=PAPER, lw=1.0,
                                zorder=z))
    a, b, c, d = ink(label, FS_BADGE, "bold")
    ax.text((x0 + x1) / 2 - (a + c) / 2, y - (b + d) / 2, label, fontsize=FS_BADGE, fontweight="bold", color=WHITE, ha="left",
            va="baseline", zorder=z + 0.5, family="Arial")
    REG["badge"].append(box(x0, y - h / 2, x1, y + h / 2))


def stop_symbol(ax, x, y, ang, z=9.0):
    """White circle, hot-pink edge, hot-pink cross: one arm along the track, one square across it."""
    ax.add_patch(Circle((x, y), RU, fc=WHITE, ec=TRAM, lw=EDGE, zorder=z))
    for a in (ang, ang + 90):
        t = math.radians(a)
        dx, dy = math.cos(t) * ARMU, math.sin(t) * ARMU
        ax.plot([x - dx, x + dx], [y - dy, y + dy], color=TRAM, lw=EDGE, solid_capstyle="butt", zorder=z + 0.5)


def sym_shape(x, y, ang):
    arms = []
    for a in (ang, ang + 90):
        t = math.radians(a)
        dx, dy = math.cos(t) * ARMU, math.sin(t) * ARMU
        arms.append(LineString([(x - dx, y - dy), (x + dx, y + dy)]).buffer(EDGE / 2 / PPU, cap_style=2))
    return unary_union([Point(x, y).buffer(ROUT, 24)] + arms)


def draw_lines(ax, routes, stops_xy):
    for zi, r in enumerate(sorted(routes, key=lambda r: r["id"])):
        xy = r["xy"]
        z0 = 2.0 + zi * 0.02
        ax.plot(*xy.T, color=PAPER, lw=W + CASE, solid_capstyle="round", solid_joinstyle="round", zorder=z0)
        ax.plot(*xy.T, color=TRAM, lw=W, solid_capstyle="round", solid_joinstyle="round", zorder=z0 + 0.005)
        discs = unary_union([Point(*stops_xy[n]).buffer(ROUT - 0.02, 24) for n in r["seq"]])
        core = LineString(xy).difference(discs)
        near = core.intersection(unary_union([Point(*stops_xy[n]).buffer(ARMU + 0.4, 24) for n in r["seq"]]))
        for g, z in ((core, z0 + 0.01), (near, 9.7)):
            for ln in getattr(g, "geoms", [g]):
                if ln.is_empty or ln.geom_type != "LineString":
                    continue
                ax.plot(*np.asarray(ln.coords).T, color=INK, lw=CORE, solid_capstyle="butt", zorder=z)
        for a, b in zip(xy, xy[1:]):
            if np.hypot(*(b - a)) > 1e-6:
                REG["line"].append((r["id"], LineString([a, b]).buffer((W + CASE) / 2 / PPU, cap_style=1)))


# ---------------------------------------------------------------------------------------------------------------
# Furniture
PANEL_FC, PANEL_EC = "#f2f5f5", "#c9d3d3"


def panel(ax, x0, y0, x1, y1, z=1.0):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=3", fc=PANEL_FC, ec=PANEL_EC, lw=1.0,
                                zorder=z))


def txt(ax, x, y, s, fs, weight="normal", ha="left", va="center", color=INK, z=11, ls=1.05, owner="furniture"):
    t = ax.text(x, y, curly(s), fontsize=fs, fontweight=weight, color=color, ha=ha, va=va, zorder=z, linespacing=ls, family="Arial")
    TEXTS.append((t, owner))
    return t


def width(text, fs, weight="normal"):
    return max(ink(ln, fs, weight)[2] - ink(ln, fs, weight)[0] for ln in curly(text).split("\n"))


def line_sample(ax, x0, x1, y, z=12, offs=(0.0,)):
    for o in offs:
        xy = np.array([(x0, y + o), (x1, y + o)])
        ax.plot(*xy.T, color=PAPER, lw=W + CASE, solid_capstyle="round", zorder=z)
        ax.plot(*xy.T, color=TRAM, lw=W, solid_capstyle="round", zorder=z + 0.01)
        ax.plot(*xy.T, color=INK, lw=CORE, solid_capstyle="butt", zorder=z + 0.02)


def key_panel(ax, x0, y1, routes, codes, measure=False, with_routes=True):
    """The Key: symbols, then every route by number and name, then the transfer pills. Returns its width and height."""
    pad, row = 3.5, 5.0
    y = y1 - pad
    ops = []
    ops.append(("t", 0, y, "KEY", 11.6, "bold"))
    y -= 8.0
    sym_rows = [("line", "Tram line, driverless maglev"), ("par", "Routes sharing a street run side by side"),
                ("stop", "Tram stop"), ("xfer", "Transfer stop: NERTA lines in pills after, over or under the name"),
                ("end", "END OF A ROUTE: name in capitals, route number in a badge"), ("acc", "All stops accessible"),
                ("cp", KEY_TEXT)] + ([("free", FREE_TEXT)] if FREE_ROUTES else [])
    for k, t in sym_rows:
        ops.append(("sym", k, y, t))
        y -= row + (0.6 if k in ("par", "xfer") else 0)
    y -= 2.5
    rs = sorted(routes, key=route_sort)
    ncol = 2 if len(rs) > 14 else 1
    per = -(-len(rs) // ncol)
    bmax = max(badge_w(r["id"]) for r in rs)   # names line up past the widest badge
    colw = bmax + 1.4 + max(width(r["name"], 9.6) for r in rs) + 5
    if with_routes:
        ops.append(("t", 0, y, "ROUTES", 11.0, "bold"))
        y -= 6.5
        for i, r in enumerate(rs):
            c, k = divmod(i, per)
            ops.append(("route", c * colw, y - k * 4.4, r))
        y -= per * 4.4 + 2.5
    else:
        ncol = 0
    ops.append(("t", 0, y, "TRANSFERS", 11.0, "bold"))
    y -= 6.8
    tcol = 2 if len(codes) > 5 else 1
    tper = -(-len(codes) // tcol)
    tcolw = max([width(NAMES[c], 9.2) for c in codes] + [10]) + PILL_W + 7
    for i, c in enumerate(codes):
        cc, k = divmod(i, tper)
        ops.append(("pill", cc * tcolw, y - k * 4.4, c))
    y -= tper * 4.4
    wkey = max(78.0, ncol * colw, tcol * tcolw) + 2 * pad
    hkey = y1 - y + pad - 1.0
    if measure:
        return wkey, hkey
    panel(ax, x0, y1 - hkey, x0 + wkey, y1)
    X = x0 + pad
    for op in ops:
        if op[0] == "t":
            txt(ax, X + op[1], op[2], op[3], op[4], op[5], "left", "top")
        elif op[0] == "sym":
            _, k, yy, t = op
            cx = X + 5.0
            if k == "line":
                line_sample(ax, X, X + 10, yy)
            elif k == "par":
                line_sample(ax, X, X + 10, yy, offs=(PARU, 0.0, -PARU))
            elif k in ("stop", "xfer", "end"):
                line_sample(ax, X, X + 10, yy)
                stop_symbol(ax, cx, yy, 0.0, z=12.5)
            if k == "xfer":
                draw_pill(ax, X + 12.5, X + 12.5 + PILL_W, yy, "GL", z=12.6)
            if k == "end":
                draw_badge(ax, X + 12.5, X + 12.5 + badge_w("66"), yy, "66", z=12.6)
            if k == "acc":
                M.icon(ax, cx, yy, z=12)
            if k == "cp":
                draw_cp(ax, cx, yy, 2.0, z=12.6)
            if k == "free":
                line_sample(ax, X, X + 10, yy)
                draw_free_tag(ax, cx, yy, FREE_H(), z=12.7)
            tx = X + (14.0 + PILL_W if k == "xfer" else 14.0 + badge_w("66") if k == "end" else 14.0)
            if k == "end":
                txt(ax, tx, yy - 0.05, "END OF A ROUTE", 9.6, "bold", "left", "center")
                txt(ax, tx + width("END OF A ROUTE", 9.6, "bold") + 0.35, yy - 0.05, ": name in capitals, route number in a badge", 9.6,
                    "normal", "left", "center")
            else:
                txt(ax, tx, yy - 0.05, t, 9.6, "normal", "left", "center")
        elif op[0] == "route":
            _, dx, yy, r = op
            bw = badge_w(r["id"])
            draw_badge(ax, X + dx, X + dx + bw, yy, r["id"], z=12.6)
            txt(ax, X + dx + bmax + 1.4, yy - 0.05, r["name"], 9.6, "normal", "left", "center")
        elif op[0] == "pill":
            _, dx, yy, c = op
            draw_pill(ax, X + dx, X + dx + PILL_W, yy, c, z=12.6)
            txt(ax, X + dx + PILL_W + 1.5, yy - 0.05, NAMES[c], 9.2, "normal", "left", "center")
    return wkey, hkey


NOTICE = [("Trams run 24 hours a day, 7 days a week.", "bold"),
          ("Every tram is driverless maglev.", "normal"),
          ("Special events: extra trams run before and after games, concerts and shows.", "normal"),
          ("Pods on demand at every stop.", "bold")]


def notice(ax, x0, y1, measure=False):
    """A passenger notice, set like a station sign: dark title bar, short paragraphs."""
    wd, fs, ls = 56.0, 10.4, 1.25
    y = y1 - 10.6
    paras = []
    for p, wt in NOTICE:
        t = "\n".join(textwrap.wrap(p, 41))
        paras.append((t, wt, y))
        y -= (t.count("\n") + 1) * fs * ls / PPU + 2.2
    h = y1 - y + 1.2
    if measure:
        return wd, h
    x1, y0 = x0 + wd, y1 - h
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, h, boxstyle="round,pad=0,rounding_size=2", fc=WHITE, ec=INK, lw=1.4, zorder=1.2))
    ax.add_patch(FancyBboxPatch((x0, y1 - 6.6), x1 - x0, 6.6, boxstyle="round,pad=0,rounding_size=2", fc=INK, ec=INK, lw=1.4, zorder=1.3))
    ax.add_patch(FancyBboxPatch((x0, y1 - 6.6), x1 - x0, 3.0, boxstyle="square,pad=0", fc=INK, ec="none", zorder=1.35))
    txt(ax, x0 + 3.5, y1 - 3.3, "PASSENGER NOTICE", 11.4, "bold", "left", "center", color=WHITE)
    for t, wt, yy in paras:
        txt(ax, x0 + 3.5, yy, t, fs, wt, "left", "top", ls=ls)
    return wd, h


def route_sort(r):
    m = re.match(r"(\d+)(.*)", r["id"])
    return (int(m.group(1)), m.group(2)) if m else (10 ** 6, r["id"])


# ---------------------------------------------------------------------------------------------------------------
# Checks
def check(fig, ax, nodes, pos_u):
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    shapes = []
    for t, owner in TEXTS:
        if not t.get_text().strip():
            continue
        bb = t.get_window_extent(rend)
        (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        shapes.append((t.get_text().replace("\n", " ")[:28], owner, box(x0, y0 + 0.35, x1, y1 - 0.35)))
    bad = defaultdict(list)
    tree_t = STRtree([s for _, _, s in shapes])
    for i, (a, oa, sa) in enumerate(shapes):
        for j in tree_t.query(sa):
            if j <= i:
                continue
            b, ob, sb = shapes[j]
            if sa.intersection(sb).area > 0.05:
                bad["text/text"].append(f"{a} | {b}")
            elif oa != ob and sa.distance(sb) < 0.3:
                bad["text close"].append(f"{a} | {b} ({sa.distance(sb):.2f})")
    lines = REG["line"]
    tree_l = STRtree([s for _, s in lines])
    syms = REG["sym"]
    tree_s = STRtree([s for _, s in syms])
    tree_p = STRtree(REG["pill"])
    for a, oa, sa in shapes:
        for j in tree_l.query(sa):
            if sa.intersection(lines[j][1]).area > 0.05:
                bad["text over line (haloed)"].append(f"{a} | route {lines[j][0]}")
        for j in tree_s.query(sa):
            if sa.intersection(syms[j][1]).area > 0.05:
                bad["text/dot"].append(f"{a} | {syms[j][0]}")
        for j in tree_p.query(sa):
            if sa.intersection(REG["pill"][j]).area > 0.05:
                bad["text/pill"].append(f"{a} | pill at {[round(v) for v in REG['pill'][j].bounds]}")
    for k, pb in enumerate(REG["pill"] + REG["badge"]):
        for j in tree_l.query(pb):
            if pb.intersection(lines[j][1]).area > 0.3:
                bad["pill/line"].append(f"{[round(v) for v in pb.bounds]} | route {lines[j][0]}")
    allp = REG["pill"] + REG["badge"]
    tree_a = STRtree(allp)
    for k, pb in enumerate(allp):
        for j in tree_a.query(pb):
            if j > k and pb.intersection(allp[j]).area > 0.05:
                bad["pill/pill"].append(f"{[round(v) for v in pb.bounds]}")
        for j in tree_s.query(pb):
            if pb.intersection(syms[j][1]).area > 0.05:
                bad["pill/dot"].append(f"{[round(v) for v in pb.bounds]} | {syms[j][0]}")
    for i, (a, sa) in enumerate(syms):
        for j in tree_s.query(sa):
            if j > i and sa.intersects(syms[j][1]):
                bad["dot/dot"].append(f"{a} | {syms[j][0]}")
    # a stop on a line that doesn't serve it reads as a stop on that line
    for a, sa in syms:
        for j in tree_l.query(sa):
            rid = lines[j][0]
            if rid not in nodes[a]["routes"] and sa.intersection(lines[j][1]).area > 0.05:
                bad["dot/foreign line"].append(f"{a} | route {rid}")
    # every name nearest its own stop
    for a, owner, sa in shapes:
        if owner not in pos_u:
            continue
        own = syms_by.get(owner)
        if own is None:
            continue
        d_own = sa.distance(own)
        for j in tree_s.query(sa.buffer(d_own + 0.5)):
            if syms[j][0] != owner and sa.distance(syms[j][1]) < d_own - 0.05:
                bad["name nearer another stop"].append(f"{a} | {syms[j][0]}")
    for k in bad:
        bad[k] = sorted(set(bad[k]))
    return bad


syms_by = {}


# ---------------------------------------------------------------------------------------------------------------
def next_version(base="tram_network"):
    for a in sys.argv[1:]:
        if a.isdigit():
            return int(a)
    v = 1
    while any((OUT / f"{base}_v{v}{s}").exists() for s in (".png", ".pdf")) or list(OUT.glob(f"{base}_v{v}_*")):
        v += 1
    if "--web" in sys.argv and v > 1 and not (OUT / f"{base}_web_v{v - 1}.pdf").exists():
        return v - 1   # the web copy takes the number of the poster it copies
    return v


def main():
    web = "--web" in sys.argv or M.WEB
    global NODISC
    NODISC = "--nodisc" in sys.argv or M.NODISC   # Max's no-disclaimer version: no release block, no MBTA, one concept note
    web = web or NODISC
    routes_path = Path(arg("--routes", DATA))
    extra = None if "--no-extra" in sys.argv else Path(arg("--extra", EXTRA))
    raw = read_routes(routes_path, extra)
    if DISPLAY:
        use_display()
        global CONN_W
        SIDE.update(SIDE_DISPLAY)   # the display's own label sides win
        TEXT.update(TEXT_DISPLAY)
        LONG.update(LONG_DISPLAY)
        DIR.update(DIR_DISPLAY)
        BADGE_SIDE.update(BADGE_SIDE_DISPLAY)
        BADGE_ROW.update(BADGE_ROW_DISPLAY)
        BADGE_AT.update(BADGE_AT_DISPLAY)
        CAPTION_SEG.update(CAPTION_SEG_DISPLAY)
        BEND_SPLIT.update(BEND_SPLIT_DISPLAY)
        PILL_ROW.update(PILL_ROW_DISPLAY)
        CONN_W = connections_panel(None, 0, 0, connection_rows(build(raw)[0]), 1, measure=True)[0]
    m = 1.0
    while True:
        if DISPLAY:
            shrink(m)
        nodes, routes = build(raw)
        key, SK = skeleton(nodes, routes)
        pos = solve(nodes, key, SK)
        geometry(nodes, routes, SK, pos)
        pos_u = {n: np.asarray(p, float) * P for n, p in pos.items()}
        if not DISPLAY:
            break
        ext = np.array(list(pos_u.values()))
        span = ext.max(0) - ext.min(0)
        room = np.array([SHEET[0] - 2 * DISPLAY_SIDE - CONN_W - 8, SHEET[1] - DISPLAY_TOP - DISPLAY_SIDE])
        print(f"  display fit: spacing x{m:.2f} gives {span[0]:.0f} x {span[1]:.0f} units for {room[0]:.0f} x {room[1]:.0f}")
        if (span <= room).all() or m < 0.42:
            break
        m *= max(0.85, min(0.97, float(min(room / span)) ** 0.8))
    print(f"{len(routes)} routes, {len(nodes)} stops, {len(key)} junctions, {len(SK)} stretches")

    base = "tram_display" if DISPLAY else "tram_network"
    v = next_version(base)
    stem = f"{base}{'_nodisc' if NODISC else '_web' if web else ''}_v{v}"
    png, pdf = OUT / f"{stem}.png", OUT / f"{stem}.pdf"
    draft = arg("--draft")
    if draft:
        png, pdf = Path(draft) / "tram_draft.png", Path(draft) / "tram_draft.pdf"
    else:
        for f in (png, pdf):
            if f.exists():
                raise SystemExit(f"refusing to overwrite {f}")

    # ---- the sheet: the network's extent, then room for furniture
    allxy = np.array(list(pos_u.values()))
    nx0, ny0 = allxy.min(0) - 40
    nx1, ny1 = allxy.max(0) + 40
    if DISPLAY:   # the ferry display's sheet: the Connections strip down the left, the network beside it, under a header band
        spare = SHEET[0] - CONN_W - 8 - (allxy[:, 0].max() - allxy[:, 0].min())
        nx0 = allxy[:, 0].min() - CONN_W - 8 - spare / 2
        nx1 = nx0 + SHEET[0]
        ny1 = allxy[:, 1].max() + DISPLAY_TOP
        ny0 = ny1 - SHEET[1]
    plt.rcParams["pdf.fonttype"] = 42
    fig = plt.figure(figsize=((nx1 - nx0) * K, (ny1 - ny0) * K))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.patch.set_facecolor(PAPER)

    draw_lines(ax, routes, pos_u)
    board = Board()
    ends = defaultdict(list)
    for r in routes:
        ends[r["seq"][0]].append((r, True))
        ends[r["seq"][-1]].append((r, False))
    for n, p in pos_u.items():
        ang = nodes[n].get("ang", 0.0)
        stop_symbol(ax, p[0], p[1], ang)
        shp = sym_shape(p[0], p[1], ang)
        REG["sym"].append((n, shp))
        syms_by[n] = shp
        board.add_static(n, "sym", shp)
    for rid, shp in REG["line"]:
        board.add_static(rid, "line", shp)
    for r in routes:
        if r["id"] in FREE_ROUTES:
            fb = free_spot(r)
            if fb is None:
                WARN.append(f"route {r['id']} is free but found no spot for its FREE tag")
                continue
            (fx, fy), shp = fb
            draw_free_tag(ax, fx, fy, FREE_H(), z=10.8)
            REG["free"].append((r["id"], shp))
            board.add_static("free:" + r["id"], "free", shp)

    # ---- labels, badges, route names
    items = []
    for n, p in pos_u.items():
        nd = nodes[n]
        term = n in ends
        text = TEXT.get(nd["name"], nd["label"])
        if term:
            text = text.upper()
        pref = {"r": 0.0, "l": 0.3, "t": 0.5, "b": 0.5, "tr": 0.9, "br": 0.9, "tl": 1.1, "bl": 1.1}
        if nd["name"] in SIDE:
            pref = {s: (0.0 if s == SIDE[nd["name"]] else 50.0) for s in SIDES}
        cands = []
        for k_, tx in enumerate([text] + ([wrap2(text)] if wrap2(text) else [])):   # a long name may also go on two lines
            row = [("text", tx, FS_END if term else FS, "bold" if term else "normal", INK)] + [("pill", c) for c in nd["pills"]]
            want = PILL_ROW.get(nd["name"])   # "row", "under" or "over": the pills' place set by hand
            if want in (None, "row"):
                cands += make_cands(p, syms_by[n], row, list(SIDES), {s_: v_ + 1.2 * k_ for s_, v_ in pref.items()}, gap=LABEL_GAP,
                                    extra=(0.0, 0.7, 1.5))
            if nd["pills"]:   # or with its pills on a row under the name, or over it
                for ab in (False, True):
                    if want not in (None, "over" if ab else "under"):
                        continue
                    cands += make_cands(p, syms_by[n], row, list(SIDES), {s_: v_ + 0.9 + 0.3 * ab + 1.2 * k_ for s_, v_ in pref.items()},
                                        gap=LABEL_GAP, extra=(0.0, 0.7, 1.5), stacked=True, above=ab)
        prio = 3 + 8 * term + len(nd["routes"]) + 0.5 * len(nd["pills"])   # a terminal's name goes before its badges
        items.append(Item("label", n, cands, center=pos_u[n], prio=prio))
        items[-1].term = term
    for n, lst in ends.items():
        # one row of badges per terminal, for every route that ends there, best placed where the lines run out
        rs = sorted({r["id"]: r for r, _ in lst}.values(), key=route_sort)
        away = np.zeros(2)
        for r, first in lst:
            seg = r["parts"][0] if first else r["parts"][-1][::-1]   # from the terminal inward
            far = next((p for p in seg[1:] if np.hypot(*(p - seg[0])) > 1.0), seg[-1])
            v = far - seg[0]
            away -= v / max(np.hypot(*v), 1e-9)
        if np.hypot(*away) < 1e-6:
            away = np.array([0.0, 1.0])
        best = min(SIDES, key=lambda s: -np.dot(np.array(SIDES[s], float) / np.hypot(*SIDES[s]), away))
        pref = {s: (0.0 if s == best else 0.8) for s in SIDES}
        if nodes[n]["name"] in BADGE_SIDE:
            pref = {s: (0.0 if s == BADGE_SIDE[nodes[n]["name"]] else 50.0) for s in SIDES}
        per_row = BADGE_ROW.get(nodes[n]["name"], 3)
        for k0 in range(0, len(rs), per_row):   # three badges to a row at most, unless listed
            row = [("badge", r["id"]) for r in rs[k0:k0 + per_row]]
            cands = make_cands(pos_u[n], syms_by[n], row, list(SIDES), pref, gap=0.6, extra=(0.0, 0.8, 1.8, 3.2))
            if nodes[n]["name"] in BADGE_AT:   # placed by hand: rows stacked down from a spot beside the stop
                dx, dy = BADGE_AT[nodes[n]["name"]]
                w_, y0_, y1_, parts_ = row_layout(row, "left")
                ox, oy = pos_u[n][0] + dx, pos_u[n][1] + dy - (k0 // per_row) * (BADGE_H + 0.6)
                placed = [(kind, a_ + ox, b_ + ox, p0 + oy, p1 + oy, pl) for kind, a_, b_, p0, p1, pl in parts_]
                cands = [dict(side="r", parts=placed, shapes=[(k_, box(a_, p0, b_, p1)) for k_, a_, b_, p0, p1, _ in placed], pref=0.0)]
            items.append(Item("badge", n, cands, center=pos_u[n], prio=6 + len(rs)))
    for r in routes:
        cands = caption_cands(r, nodes, pos_u, SK)
        if cands:
            items.append(Item("caption", r["id"], cands, center=None, prio=1.0))

    canvas = box(nx0 + 3, ny0 + 3, nx1 - 3, ny1 - 3)
    if DISPLAY:
        panels = display_furniture(ax, board, nodes, routes, web, (nx0, ny0, nx1, ny1))
    board.freeze(pos_u)
    place_all(board, items, canvas)
    harmonize(board, items, canvas, SK, nodes)
    for it in [it for it in items if it.kind == "caption"]:
        if any(o.intersects(sh) for _, sh in it.choice["shapes"] for ow, k_, o in board.static if k_ in ("line", "free")):
            WARN.append(f"route {it.owner}'s name found no spot off the lines; left off")
            board.take(it, it.choice["shapes"])
            items.remove(it)
    why = os.environ.get("TRAM_WHY")
    if why:   # debugging: what each spot for one stop's name would cost
        for it in items:
            if it.kind == "label" and it.owner == why:
                board.take(it, it.choice["shapes"])
                for c in it.cands:
                    sc, hits = cost(board, it, c["shapes"], canvas)
                    print("  why", c["side"], round(c["pref"], 1), round(sc, 1), hits[:4])
                board.put(it, it.choice["shapes"])

    # ---- furniture in the emptiest corners
    if DISPLAY:
        furniture_done = True
    occupied = [s for _, _, s in board.static] + [s for it in items for _, s in it.choice["shapes"]]
    tree_o = STRtree(occupied)

    def free(b, pad=2.5):
        bb = b.buffer(pad)
        return not any(bb.intersects(occupied[j]) for j in tree_o.query(bb))

    def spot(w, h, corner, xr, yr):
        """The free w x h box nearest the given corner of the sheet, or None."""
        cx = nx0 if corner[0] < 0 else nx1
        cy = ny0 if corner[1] < 0 else ny1
        cands = [(math.hypot(gx + w / 2 - cx, gy + h / 2 - cy), gx, gy) for gx in np.arange(nx0 + 4, nx1 - w - 4, 4.0)
                 for gy in np.arange(ny0 + 4, ny1 - h - 4, 4.0)]
        for d, gx, gy in sorted(cands):
            if free(box(gx, gy, gx + w, gy + h)):
                return d, gx, gy
        return None

    if not DISPLAY:
        hy = None
        hdr_w, hdr_h = 120.0, 30.0
        s = spot(hdr_w, hdr_h, (-1, 1), 0, 0)
        if s is None:
            ny1 += hdr_h + 6
            hx, hy0 = nx0 + 4, ny1 - hdr_h - 4
        else:
            _, hx, hy0 = s
        hy = hy0 + hdr_h / 2
        header_t(ax, hx + 10, hy + 3, 6.4)
        nb = draw_nerta(ax, hx + 10, hy + 3 - (6.4 + 3.2 / 5.4 / 2) - 0.8, 2 * (6.4 + 3.2 / 5.4 / 2), "B", colors=M.NERTA_COLORS)
        if NODISC:
            concept_note(ax, hx + 10 - (6.4 + 3.2 / 5.4 / 2), nb - 1.0, 9.0)
        ax.text(hx + 22, hy + 1.5, "Tram" + chr(10) + "Network", fontsize=27, fontweight="bold", color=INK, ha="left", va="center",
                linespacing=0.9, zorder=13, family="Arial")
        occupied.append(box(hx, hy0, hx + hdr_w, hy0 + hdr_h))
        if not web:
            from release_tag import release_width
            rsz = 24.0   # 2.5 times the old 9.6: readable in a carousel without zooming
            rw = release_width(rsz, PPU) + 2
            rh = 16 * rsz / 9.6
            s = spot(rw, rh, (1, 1), 0, 0)
            if s is None:
                ny1 += rh + 6
                right, cy = nx1 - 5, ny1 - rh / 2 - 4
            else:
                right, cy = s[1] + rw, s[2] + rh / 2
            left, bottom, top = draw_release(ax, right=right, cy=cy, size=rsz, ppu=PPU, ink=INK)
            occupied.append(box(left, bottom, right, top))
            tree_o = STRtree(occupied)
        codes = sorted({c for nd in nodes.values() for c in nd["pills"]}, key=ORDER.index)
        kw, kh = key_panel(ax, 0, 0, routes, codes, measure=True)
        tree_o = STRtree(occupied)
        s = spot(kw, kh, (-1, -1), 0, 0)
        if s is None:
            ny0 -= kh + 8
            kx, ky0 = nx0 + 4, ny0 + 4
        else:
            _, kx, ky0 = s
        key_panel(ax, kx, ky0 + kh, routes, codes)
        occupied.append(box(kx, ky0, kx + kw, ky0 + kh))
        foot = footer_text()
        occupied.append(box(nx1 - 5 - width(foot, 7.6), ny0 + 3, nx1 - 5, ny0 + 7))   # the footer's corner stays clear
        tree_o = STRtree(occupied)
        nw, nh = notice(ax, 0, 0, measure=True)
        s = spot(nw, nh, (1, -1), 0, 0)
        if s is None:
            ny0 -= nh + 8
            ax_, ay0 = nx1 - nw - 4, ny0 + 10
        else:
            _, ax_, ay0 = s
        notice(ax, ax_, ay0 + nh)
        occupied.append(box(ax_, ay0, ax_ + nw, ay0 + nh))
        ax.text(nx1 - 5, ny0 + 4, foot, fontsize=7.6, color=INK, ha="right", va="bottom", zorder=13, family="Arial")
    ax.set_xlim(nx0, nx1)
    ax.set_ylim(ny0, ny1)
    fig.set_size_inches((nx1 - nx0) * K, (ny1 - ny0) * K)

    # ---- labels last, so they sit over everything they were placed round
    for it in items:
        draw_row(ax, it.choice["parts"], it.owner if it.kind == "label" else f"{it.kind}:{it.owner}")

    if "--grid" in sys.argv:
        for gx in range(int(nx0 / P), int(nx1 / P) + 1):
            ax.axvline(gx * P, color="#d0d0ff" if gx % 5 else "#9090ff", lw=0.3, zorder=0.5)
            if gx % 5 == 0:
                ax.text(gx * P, ny1 - 2, str(gx), fontsize=6, color="#6060c0", ha="center", va="top")
        for gy in range(int(ny0 / P), int(ny1 / P) + 1):
            ax.axhline(gy * P, color="#d0d0ff" if gy % 5 else "#9090ff", lw=0.3, zorder=0.5)
            if gy % 5 == 0:
                ax.text(nx0 + 2, gy * P, str(gy), fontsize=6, color="#6060c0", ha="left", va="center")

    bad = check(fig, ax, nodes, pos_u)
    for it in items:   # the placed rows: a name clearly nearest its own stop, rows apart, route names off the lines
        sh = it.choice["shapes"]
        if it.kind == "label":
            for j in level_others(board, it, sh):
                bad["name level with another stop, close beside it"].append(f"{nodes[it.owner]['name']} | {board.cid[j]}")
            for _, a_ in [x for x in sh if x[0] in ("pill", "text")]:
                for jt, ok_, b_ in board.near_dyn(a_, 2.0):
                    if (jt is not it and jt.kind == "label" and jt.owner != it.owner and {ok_, _} == {"pill", "text"}
                            and under_other(a_.bounds, b_.bounds)):
                        bad["pill right under or over another name"].append(" | ".join(sorted([nodes[it.owner]["name"], nodes[jt.owner]["name"]])))
        if it.kind == "label":
            for k_, a_ in sh:
                if k_ == "text":
                    for j in centre_others(board, it, a_):
                        bad["name centre nearer another stop"].append(f"{nodes[it.owner]['name']} | {board.cid[j]}")
                    for jt, ok_, b_ in board.near_dyn(a_, 2.0):
                        if (jt is not it and jt.kind == "label" and jt.owner != it.owner and ok_ == "text"
                                and stacked_like_one(a_.bounds, b_.bounds)):
                            bad["names stacked like one name"].append(" | ".join(sorted([nodes[it.owner]["name"], nodes[jt.owner]["name"]])))
                if k_ == "pill":
                    for j in centre_others(board, it, a_, "pill"):
                        bad["pill nearer another stop"].append(f"{nodes[it.owner]['name']} | {board.cid[j]}")
                    for j in level_with(board, a_, it.owner, it.center, reach=2.0 * PILL_W):
                        bad["pill level beside another stop"].append(f"{nodes[it.owner]['name']} | {board.cid[j]}")
        if it.kind == "badge":
            for _, a_ in sh:
                for jt, ok_, b_ in board.near_dyn(a_, 2.0):
                    if jt.kind == "label" and jt.owner != it.owner and ok_ == "text" and under_other(a_.bounds, b_.bounds):
                        bad["end badge right under or over another name"].append(f"{nodes[it.owner]['name']} | {nodes[jt.owner]['name']}")
        if it.kind == "caption":
            tx = [x[1] for x in sh if x[0] == "text"]
            for j in level_with(board, unary_union(tx or [x[1] for x in sh]), None):
                bad["route name level beside a stop"].append(f"route {it.owner} | {board.cid[j]}")
        if it.kind == "caption":
            allsh = unary_union([x[1] for x in sh])
            od = min([allsh.distance(o) for ow, k_, o in board.static if k_ == "line" and ow == it.owner] or [1e9])
            fd = min([allsh.distance(o) for ow, k_, o in board.static if k_ == "line" and ow != it.owner] or [1e9])
            if fd < od + 1.5:
                bad["route name nearer another route's line"].append(f"route {it.owner} ({od:.1f} vs {fd:.1f})")
        if it.kind in ("label", "badge"):
            for j, dj, d_own in near_others(board, it, sh):
                nm = nodes[it.owner]["name"]
                k_ = "name not clearly nearest its own stop" if it.kind == "label" else "route badges not clearly nearest their terminal"
                bad[k_].append(f"{nm} | {board.cid[j]} ({d_own:.1f} vs {dj:.1f})")
        if it.kind == "caption":
            for _, s_ in sh:
                for ow, k_, o in board.static:
                    if k_ == "line" and s_.distance(o) < (1e-6 if ow == it.owner else 1.0):
                        bad["route name on or hugging a line"].append(f"route {it.owner} | route {ow}")
        for _, a_ in sh:
            for jt, _, b_ in board.near_dyn(a_, ROWGAP):
                if jt is not it and jt.owner != it.owner and run_together(a_.bounds, b_.bounds):
                    pair = sorted([f"{it.kind} {it.owner}", f"{jt.kind} {jt.owner}"])
                    bad["rows run together"].append(" | ".join(pair))
    for rid_, fshp in REG["free"]:
        for t, owner in TEXTS:
            if not t.get_text().strip():
                continue
            bb = t.get_window_extent(fig.canvas.get_renderer())
            (a0, b0), (a1, b1) = ax.transData.inverted().transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
            if box(a0, b0 + 0.35, a1, b1 - 0.35).intersects(fshp):
                bad["something on the FREE tag"].append(f"text {t.get_text()[:20]}")
        for pb in REG["pill"] + REG["badge"]:
            if pb.intersects(fshp):
                bad["something on the FREE tag"].append(f"pill or badge at {[round(v) for v in pb.bounds]}")
        for n_, sh_ in REG["sym"]:
            if sh_.intersects(fshp):
                bad["something on the FREE tag"].append(f"stop {n_}")
        print(f"FREE tag on route {rid_} at {[round(v, 1) for v in fshp.bounds]}, {FREE_H() * PPU:.1f} pt high")
    for k in ("name not clearly nearest its own stop", "route badges not clearly nearest their terminal", "route name on or hugging a line",
              "rows run together", "something on the FREE tag", "name level with another stop, close beside it",
              "pill right under or over another name", "route name nearer another route's line", "name centre nearer another stop",
              "names stacked like one name", "pill nearer another stop", "pill level beside another stop",
              "end badge right under or over another name", "route name level beside a stop"):
        bad[k] = sorted(set(bad[k]))
    total = 0
    for kind in ("text/text", "text/dot", "text/pill", "dot/dot", "text close", "text over line (haloed)", "pill/line", "pill/pill", "pill/dot",
                 "dot/foreign line", "name nearer another stop", "name not clearly nearest its own stop", "rows run together",
                 "route badges not clearly nearest their terminal", "route name on or hugging a line", "something on the FREE tag",
                 "name level with another stop, close beside it", "pill right under or over another name",
                 "route name nearer another route's line", "name centre nearer another stop", "names stacked like one name",
                 "pill nearer another stop", "pill level beside another stop", "end badge right under or over another name",
                 "route name level beside a stop"):
        lst = bad.get(kind, [])
        print(f"{kind}: {len(lst)}")
        for b in lst[:40]:
            print("    ", b)
        if kind in ("text/text", "text/dot", "text/pill", "dot/dot", "something on the FREE tag"):
            total += len(lst)
    print(f"{total} overlaps (text/text, text/dot, text/pill, dot/dot)")
    for w in dict.fromkeys(WARN):
        print("  note:", w)
    png.parent.mkdir(parents=True, exist_ok=True)
    dpi = int(arg("--dpi", 600 if not draft else 120))   # the main-map session audits at 600 dpi
    fig.savefig(pdf, facecolor=PAPER)
    print(f"written {pdf}")
    print(f"png at {dpi} dpi: {round((nx1 - nx0) * K * dpi)} x {round((ny1 - ny0) * K * dpi)} px")
    if not web:   # crops first: the full sheet at 600 dpi is the step most likely to run out of memory
        crops(fig, ax, nodes, pos_u, (nx0, ny0, nx1, ny1), Path(draft) if draft else OUT, stem, dpi,
              boxes=panels if DISPLAY else None, only=DISPLAY_CROPS if DISPLAY else None)
    fig.savefig(png, dpi=dpi, facecolor=PAPER)
    print("written", png)
    if draft:   # stop spots, for looking at a draft by stop name
        Path(draft, "stops.json").write_text(json.dumps(dict(ext=[nx0, ny0, nx1, ny1], stops={nodes[n]["name"]: [float(v) for v in p_]
                                                                                              for n, p_ in pos_u.items()})), encoding="utf-8")
    LAST.update(dict(png=png, nodes=nodes, pos_u=pos_u, ext=(nx0, ny0, nx1, ny1), dpi=dpi, stem=stem, draft=draft))
    return LAST


LAST = {}
CROPS = {   # the densest parts of the sheet, by the stops each crop must hold (names missing from the data are skipped)
    "nubian": ["Nubian", "Roxbury Crossing", "Ruggles", "Uphams Corner", "Melnea Cass", "Adams St", "Roxbury St"],
    "ashmont": ["Ashmont", "Codman Sq", "Talbot Ave", "Four Corners", "Fields Corner", "Gallivan Blvd", "Cedar Grove"],
    "harvard": ["Harvard", "Central", "Putnam Ave", "West Station", "Barry's Corner", "Allston"],
    "chelsea": ["Bellingham Sq", "Chester Ave", "Woodlawn", "Park Ave", "Wonderland", "American Legion Hwy", "Revere Beach"],
    "foresthills": ["Forest Hills", "Arborway", "Seaver St", "Sedgwick St", "Aldwin Rd", "Canterbury St"],
    "quincy": ["Quincy Center", "General Dunford Dr", "Foster St", "Newcomb St", "Guild St", "Pond St"],
}


def crops(fig, ax, nodes, pos_u, ext, folder, stem, dpi, pad=28.0, boxes=None, only=None):
    """Zoomed crops of the densest areas (and any named boxes), as new PNGs beside the poster, drawn from the figure at the
    poster's own scale."""
    x0, y0, x1, y1 = ext
    byname = {nd["name"]: n for n, nd in nodes.items()}
    areas = [(a_, n_) for a_, n_ in CROPS.items() if only is None or a_ in only] + [(a_, b_) for a_, b_ in (boxes or {}).items()]
    for area, names in areas:
        if isinstance(names, tuple):
            bx0, by0, bx1, by1 = names[0] - 4, names[1] - 4, names[2] + 4, names[3] + 4
        else:
            pts = [pos_u[byname[s_]] for s_ in names if s_ in byname and byname[s_] in pos_u]
            if not pts:
                continue
            pts = np.array(pts)
            bx0, by0 = pts.min(0) - pad
            bx1, by1 = pts.max(0) + pad
            bx0, bx1 = bx0 - 18, bx1 + 32   # names and pills run off to the side
        bx0, bx1 = max(x0, bx0), min(x1, bx1)
        by0, by1 = max(y0, by0), min(y1, by1)
        out = Path(folder) / f"{stem}_crop_{area}.png"
        if out.exists() and Path(folder) == OUT:
            print("refusing to overwrite", out)
            continue
        fig.set_size_inches((bx1 - bx0) * K, (by1 - by0) * K)
        ax.set_xlim(bx0, bx1)
        ax.set_ylim(by0, by1)
        fig.savefig(out, dpi=dpi, facecolor=PAPER)
        print("crop", out)
    fig.set_size_inches((x1 - x0) * K, (y1 - y0) * K)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)


SIDE_DISPLAY = {"Arlington Ctr": "r", "Irving St": "r", "Walnut St": "r", "Hancock St": "l", "Hastings Ln": "br",
                "Brookline Village": "l", "Sylvia Rd": "b", "Dewey Rd": "r", "Audubon Ave": "r", "Allen St": "r", "Brookside Rd": "r",
                "Kingman St": "r"}   # the 225's names all on the right, like Blanchard Rd to West Howard St   # display-only label sides
BADGE_SIDE_DISPLAY = {}   # display-only badge sides
BADGE_ROW_DISPLAY = {}   # display-only badges to a row
BADGE_AT_DISPLAY = {"Quincy Center": (3.6, -5.4)}   # display-only: Quincy Center's five badges under its name, off the 215
LONG_DISPLAY = {("Allston", "Brookline Village"): 1.35, ("Brookline Village", "Kenmore"): 1.3, ("Arlington Ctr", "Medford Sq"): 1.15, ("Woodlawn", "Park Ave"): 1.4, ("Uphams Corner", "Fields Corner"): 1.5}
TEXT_DISPLAY = {"Arlington Ctr": "Arlington" + chr(10) + "Center"}   # boxed in between the 95 and the 78
AT_DISPLAY_M = 0.577   # the display's spacing factor the pins below were set at
AT_DISPLAY = {          # display-only pins, in the display's own grid steps
    "Arlington Ctr": (-13.2, 12.6),   # the end of the 95, clear of the 78
    "Watertown": (-15.9, 0.4),        # straight down-left from Barry's Corner: the 70 runs straight, no swing out and back
}
DIR_DISPLAY = {("Barry's Corner", "Watertown"): "SW"}   # display-only directions
PILL_ROW = {}   # station name -> where its pills go: "row" (after the name), "under" or "over"
PILL_ROW_DISPLAY = {"Brigham Circle": "row", "West Station": "over"}   # display: set by hand
NUDGE_DISPLAY = {"Kendall/MIT": (0.4, 0.4)}   # grid steps, after the layout: Kendall on along its own line, off the 95 and 101
DISPLAY_TOP = 36.0     # header band above the network, drawing units
CONN_W = 0.0           # the Connections strip's width, measured at run time
DISPLAY_SIDE = 13.0    # room left and right for names
DISPLAY_CROPS = ("nubian", "quincy", "foresthills")


def connection_rows(nodes):
    """Every NERTA station a tram serves: (name shown, line pills, tram routes), A to Z."""
    rows = [(nd["label"], nd["pills"], sorted(nd["routes"], key=lambda r: route_sort({"id": r}))) for nd in nodes.values() if nd["nerta"]]
    return sorted(rows, key=lambda r: r[0].lower())


def connections_panel(ax, x0, y1, rows, ncol, measure=False):
    """A station sign: dark title bar, then one row per station, its line pills, and the trams that stop there."""
    fs, pitch, pad = 9.2, 4.2, 3.0
    per = -(-len(rows) // ncol)
    name_w = max(width(r[0], fs) for r in rows)
    pill_w = 2 * PILL_W + PILL_GAP   # badges line up after two pills; a station with three pushes its badges on
    badge_w_ = max(sum(badge_w(b) for b in r[2]) + 0.45 * (len(r[2]) - 1) + max(0, len(r[1]) - 2) * (PILL_W + PILL_GAP) for r in rows)
    colw = name_w + 1.6 + pill_w + 2.0 + badge_w_ + 5.0
    w = ncol * colw - 5.0 + 2 * pad
    head = 15.0
    h = head + per * pitch + pad
    if measure:
        return w, h
    y0 = y1 - h
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0,rounding_size=2", fc=WHITE, ec=INK, lw=1.4, zorder=1.2))
    ax.add_patch(FancyBboxPatch((x0, y1 - 6.6), w, 6.6, boxstyle="round,pad=0,rounding_size=2", fc=INK, ec=INK, lw=1.4, zorder=1.3))
    ax.add_patch(FancyBboxPatch((x0, y1 - 6.6), w, 3.0, boxstyle="square,pad=0", fc=INK, ec="none", zorder=1.35))
    txt(ax, x0 + pad + 0.5, y1 - 3.3, "CONNECTIONS", 11.4, "bold", "left", "center", color=WHITE)
    txt(ax, x0 + pad + 0.5, y1 - 10.6, "NERTA stations, their lines, their trams", 8.8, "normal", "left", "center", color=GREY)
    for i, (name, pills, rids) in enumerate(rows):
        c, k = divmod(i, per)
        X = x0 + pad + c * colw
        yy = y1 - head - (k + 0.5) * pitch
        if k % 2 == 0:   # zebra rows, as on a timetable
            ax.add_patch(FancyBboxPatch((X - 1.0, yy - pitch / 2), colw - 3.0, pitch, boxstyle="square,pad=0", fc=PANEL_FC, ec="none",
                                        zorder=1.25))
        txt(ax, X, yy - 0.05, name, fs, "normal", "left", "center", z=12)
        px = X + name_w + 1.6
        for c_ in pills:
            draw_pill(ax, px, px + PILL_W, yy, c_, z=12.6)
            px += PILL_W + PILL_GAP
        bx = max(X + name_w + 1.6 + pill_w + 2.0, px + 2.0 - PILL_GAP)
        for rid in rids:
            bw = badge_w(rid)
            draw_badge(ax, bx, bx + bw, yy, rid, z=12.6)
            bx += bw + 0.45
    return w, h


NODISC = False   # set in main(): the no-disclaimer version


def footer_text():
    """The footer: no MBTA text at all on the no-disclaimer version (Max, November 8, 2:05 PM)."""
    return "Layout schematic, not to scale." if NODISC else "Layout schematic, not to scale. Not affiliated with the MBTA."


def concept_note(ax, x, top, fs):
    """make_tmap.CONCEPT_NOTE, the one note the no-disclaimer version keeps, under the NERTA mark. Returns its box."""
    t = ax.text(x, top, M.CONCEPT_NOTE, fontsize=fs, color=INK, ha="left", va="top", zorder=13, family="Arial")
    TEXTS.append((t, "furniture"))
    return (x, top - 1.25 * fs / PPU, x + width(M.CONCEPT_NOTE, fs), top)


def header_t(ax, x, y, r):
    """The header's T: NERTA's multicolor T (the 12 NERTA_COLORS, Max, November 8) inside the white roundel."""
    ax.add_patch(Circle((x, y), r, fc=WHITE, ec=INK, lw=3.2, zorder=12))
    draw_t(ax, x, y, r, M.NERTA_COLORS, z=13)


def tram_pill(ax, x, hy):
    """The header's mode pill, as the ferry display's F: hot pink, with the tram stop symbol in white."""
    ax.add_patch(FancyBboxPatch((x, hy - 6), 28, 12, boxstyle="round,pad=0,rounding_size=6", fc=TRAM, ec="none", zorder=12))
    cx, r = x + 14, 3.9
    ax.add_patch(Circle((cx, hy), r, fc=TRAM, ec=WHITE, lw=2.6, zorder=13))
    for a in (0, 90):
        t = math.radians(a)
        dx, dy = math.cos(t) * r * ARM, math.sin(t) * r * ARM
        ax.plot([cx - dx, cx + dx], [hy - dy, hy + dy], color=WHITE, lw=2.6, solid_capstyle="butt", zorder=13.1)


def display_furniture(ax, board, nodes, routes, web, ext):
    """Header, release block, Connections, Key and notice for the station display, placed before the names so the names
    work round them. Each goes in the free spot nearest its corner, clear of every line and stop."""
    nx0, ny0, nx1, ny1 = ext
    taken = [s_ for _, k_, s_ in board.static]
    tree = STRtree(taken)
    placed = {}

    def free(b, pad):
        bb = b.buffer(pad)
        return not any(bb.intersects(taken[j]) for j in tree.query(bb)) and all(not bb.intersects(o) for o in placed.values())

    def spot(w, h, corner, pad=9.0):
        cx = nx0 if corner[0] < 0 else nx1
        cy = ny0 if corner[1] < 0 else ny1
        cands = sorted((math.hypot(gx + w / 2 - cx, gy + h / 2 - cy), gx, gy) for gx in np.arange(nx0 + 4, nx1 - w - 4 + 1e-6, 3.0)
                       for gy in np.arange(ny0 + 4, ny1 - h - 4 + 1e-6, 3.0))
        for pd in (pad, 5.0, 2.5):
            for _, gx, gy in cands:
                if free(box(gx, gy, gx + w, gy + h), pd):
                    return gx, gy
        WARN.append(f"display: no free spot for a {w:.0f} x {h:.0f} panel; it overlaps the map")
        return cands[0][1], cands[0][2]

    hy = ny1 - 11
    header_t(ax, nx0 + 10, hy, 6.4)
    nb = draw_nerta(ax, nx0 + 10, hy - (6.4 + 3.2 / 5.4 / 2) - 0.8, 2 * (6.4 + 3.2 / 5.4 / 2), "B", colors=M.NERTA_COLORS)
    tram_pill(ax, nx0 + 20, hy)
    if NODISC:
        nt = concept_note(ax, nx0 + 10 - (6.4 + 3.2 / 5.4 / 2), nb - 0.8, 8.8)
        placed["note"] = (nt[0] - 1, nt[1] - 1, nt[2] + 1, nt[3] + 1)
    ax.text(nx0 + 52, hy, "Tram" + chr(10) + "Network", fontsize=27, fontweight="bold", color=INK, ha="left", va="center",
            linespacing=0.9, zorder=13, family="Arial")
    placed["header"] = (nx0, hy - 15, nx0 + 52 + width("Network", 27, "bold") + 4, ny1)
    if not web:
        left, bottom, top = draw_release(ax, right=nx1 - 5, cy=hy, size=11.5, ppu=PPU, ink=INK)   # the ferry display's size
        placed["release"] = (left - 2, bottom - 2, nx1, top + 2)
    foot = footer_text()
    ax.text(nx1 - 5, ny0 + 4, foot, fontsize=9.2, color=INK, ha="right", va="bottom", zorder=13, family="Arial")
    placed["footer"] = (nx1 - 6 - width(foot, 9.2), ny0 + 3, nx1, ny0 + 8)
    placed = {k_: box(*v_) for k_, v_ in placed.items()}
    rows = connection_rows(nodes)
    cw, ch = connections_panel(ax, 0, 0, rows, 1, measure=True)
    gx, gtop = nx0 + 4, ny1 - 28
    connections_panel(ax, gx, gtop, rows, 1)
    placed["connections"] = box(gx, gtop - ch, gx + cw, gtop)
    codes = sorted({c for nd in nodes.values() for c in nd["pills"]}, key=ORDER.index)
    kw, kh = key_panel(ax, 0, 0, routes, codes, measure=True, with_routes=False)
    kx, ky = spot(kw, kh, (1, -1))
    key_panel(ax, kx, ky + kh, routes, codes, with_routes=False)
    placed["key"] = box(kx, ky, kx + kw, ky + kh)
    nw, nh = notice(ax, 0, 0, measure=True)
    ax_, ay = spot(nw, nh, (1, -1))
    notice(ax, ax_, ay + nh)
    placed["notice"] = box(ax_, ay, ax_ + nw, ay + nh)
    for k_, b_ in placed.items():
        board.add_static("furniture", "panel", b_)
    print("  display panels: " + ", ".join(f"{k_} at {[round(v) for v in b_.bounds]}" for k_, b_ in placed.items()))
    return {"connections": placed["connections"].bounds}


CAPTION_SEG = {"9": ("Dover", "Broadway")}   # route -> (stop, stop): its name goes beside that stretch only
CAPTION_SEG_DISPLAY = {   # display: each beside a stretch of its own, clear of the lines it could be mistaken for
    "16": [("Newmarket", "Edward Everett Sq"), ("Andrew", "Newmarket"), ("Seaver St", "Four Corners"), ("Arborway", "Seaver St")], "23": ("Vassar St", "Melville Ave"), "22": [("Egleston Sq", "Harold St"), ("Wales St", "Angell St"), ("Angell St", "Talbot Ave")],
    "9": [("Broadway", "West Broadway"), ("West Broadway", "Dorchester St")],
    "116": ("Condor St", "Marginal St"), "95": [("Winthrop St", "Hastings Ln")], "1": ("Melnea Cass", "Boston Medical"),
}


def caption_cands(r, nodes, pos_u, SK):
    """Spots for the route's name, '66 Harvard St' style, beside its longest stretch of its own."""
    out = []
    row = [("badge", r["id"]), ("text", r["name"], CAP_FS, "bold", TRAM_TEXT)]
    segs = []
    for c, fwd in r["legs"]:
        e = SK[c]
        stops = [e["u"]] + e["mids"] + [e["v"]]
        alone = len(e["routes"]) == 1
        for a, b in zip(stops, stops[1:]):
            pa, pb = pos_u[a], pos_u[b]
            L = np.hypot(*(pb - pa))
            allowed = CAPTION_SEG.get(r["id"])
            if allowed and isinstance(allowed[0], str):
                allowed = [allowed]
            if allowed and {nodes[a]["name"], nodes[b]["name"]} not in [set(x) for x in allowed]:
                continue   # set by hand beside one stretch of its own
            segs.append((L * (1.0 if alone else 0.25), pa, pb))
    segs.sort(key=lambda s: -s[0])
    for rank, (L, pa, pb) in enumerate(segs[:28]):
        mid = (pa + pb) / 2
        d = pb - pa
        ang = math.degrees(math.atan2(d[1], d[0])) % 180
        if abs(ang - 90) < 10:
            sides = ["r", "l"]
        elif ang < 10 or ang > 170:
            sides = ["t", "b"]
        else:
            sides = ["tr", "bl", "tl", "br"]
        own = LineString([pa, pb]).buffer((W + CASE) / 2 / PPU)
        for c in make_cands(mid, own, row, sides, {s: 2.0 + 0.5 * rank for s in sides}, gap=1.0, extra=(0.0, 1.5, 3.0), mirror=False):
            out.append(c)
    return out


if __name__ == "__main__":
    main()
