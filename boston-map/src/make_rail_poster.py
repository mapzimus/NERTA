"""Commuter rail and high-speed rail poster: every NERTA commuter line, run through the BIGGER Dig.

Built like the line posters and the ferry network poster: the T roundel header, level station names, transfer pills and a
Key. Every commuter line is drawn in commuter purple with its own second color on both edges, like the color rim on the
NERTA pill. The second color only tells the lines apart; nobody calls a line by it (Max, November 7). High-speed rail is gold
inside purple, as on the main map, and stops only where a station's capsule takes in the gold line.

Every line runs North Station, Boston Central, South Station. North-side lines end under South Station's capsule and
south-side lines under North Station's, so no line visibly ends downtown.

Stops and names follow the main map (make_tmap.py: CR_STOPS, CR_PATHS, CR_TEXT, lines()), filled out with every real station
from the MBTA V3 API, checked against Wikipedia. Max's calls for this poster (November 7): high-speed rail to Montreal runs via
Lowell and Concord NH, and to Maine via the Haverhill Line; every real station is shown, including Natick and Framingham
(the rejection was for the main map); Newburyport and Rockport stay one line that forks at Beverly; Route 128 gets commuter
and high-speed stops; Plymouth reopens; the rows stay unbranded. What the other maps need to match is listed in
research/rail-poster-changes-for-all-maps.md. New or invented stops are logged in data/line_audit.md.

Writes only to output/copies/rail_poster_vN.png and .pdf and never overwrites.
Run: python make_rail_poster.py [version] [--draft DIR]
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon  # noqa: E402
from matplotlib.textpath import TextPath  # noqa: E402
from shapely.geometry import LineString, Point, box  # noqa: E402
from shapely.geometry import Polygon as SPoly  # noqa: E402
from shapely.ops import substring  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from nerta_mark import draw_nerta  # noqa: E402
import make_tmap as M  # noqa: E402  (read only: colors, lines(), icon)
import make_line_poster as LP  # noqa: E402  (read only: roundel, transfer and ferry tables, so pills match the line posters)
from station_kit import INK, WHITE, rounded  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "output" / "copies"
K = 0.075          # inches per drawing unit, as on the line posters
PPU = K * 72       # points per drawing unit
LW = 6.4           # line width, points
RIM = 1.2          # each edge of a commuter line in its own color, points
CORE = 2.7         # gold core of a high-speed line, points
PITCH = 2.0        # gap between parallel lines, center to center, units
R = 3.0            # corner rounding, units
STEP = 4.4         # stop spacing on a straight leg, units
DSTEP = 3.6        # stop spacing on a 45-degree leg, per axis (5.1 along the line), so each name sits nearest its own dot
FS, FS_END, FS_BIG = 9.6, 10.4, 13.0
PURPLE = M.CR_TEXT_COLOR   # commuter rail purple, #80276c
GOLD = M.HSR
PAPER = M.PAPER

# Second colors. Chosen by CIEDE2000 from a grid of hues (scratch palette.py): every pair is 19.9 or more apart, and each is 14
# or more from the T line colors, high-speed gold, both commuter purples, paper, ink and water, and 40 or more from purple.
LINES = {
    "fit": dict(name="FITCHBURG LINE", hue="#cfba84"),
    "low": dict(name="LOWELL LINE", hue="#3680c4"),
    "hav": dict(name="HAVERHILL LINE", hue="#c0630f"),
    "pea": dict(name="PEABODY LINE", hue="#3febbe"),
    "nbp": dict(name="NEWBURYPORT / ROCKPORT LINE", hue="#f99bee"),
    "wor": dict(name="FRAMINGHAM / WORCESTER LINE", hue="#71b743"),
    "fra": dict(name="FRANKLIN LINE", hue="#a6bbf2"),
    "pro": dict(name="PROVIDENCE LINE", hue="#f0ab99"),
    "fr": dict(name="FALL RIVER / NEW BEDFORD LINE", hue="#489f90"),
    "kin": dict(name="KINGSTON LINE", hue="#38e6f8"),
    "grb": dict(name="GREENBUSH LINE", hue="#937a12"),
    "hmon": dict(name="HIGH-SPEED RAIL", hsr=True),
    "hmai": dict(name="HIGH-SPEED RAIL", hsr=True),
    "halb": dict(name="HIGH-SPEED RAIL", hsr=True),
    "hnyc": dict(name="HIGH-SPEED RAIL", hsr=True),
}
DIRS = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0), "NE": (1, 1), "NW": (-1, 1), "SE": (1, -1), "SW": (-1, -1)}

# Trunk: North Station, Boston Central, South Station
YN, YC, YS = 0.0, -15.0, -30.0
TRUNK_X0, TRUNK_X1 = -15.0, 13.0


# ---------------------------------------------------------------------------------------------------------------
# Geometry helpers
def walk(p, *moves):
    """Start at p and move: ("SW", 12) moves 12 units on each axis on a diagonal, 12 units on a straight."""
    pts = [np.asarray(p, float)]
    for d, n in moves:
        pts.append(pts[-1] + np.asarray(DIRS[d], float) * n)
    return [tuple(q) for q in pts]


def par(pts, d):
    """The parallel line d units to the left of travel (mitred corners, so straights stay exactly parallel)."""
    if d == 0:
        return [tuple(map(float, q)) for q in pts]
    return list(LineString(pts).offset_curve(d, join_style=2, mitre_limit=10).coords)


def cut(pts, at):
    """pts up to the point nearest `at`."""
    ls = LineString(pts)
    return list(substring(ls, 0, ls.project(Point(at))).coords)


def join(*parts):
    out = []
    for part in parts:
        for q in part:
            q = tuple(map(float, q))
            if not out or np.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > 1e-6:
                out.append(q)
    return out


def on(path, at):
    """The point of the drawn path nearest `at`."""
    ls = LineString(path)
    q = ls.interpolate(ls.project(Point(at)))
    return (q.x, q.y)


def on_line(key, at):
    """The point nearest `at` on a line or any of its branches."""
    cands = ([PATHS[key]] if key in PATHS else []) + [b for k, b in BRANCHES if k == key]
    return min((on(c, at) for c in cands), key=lambda q: np.hypot(q[0] - at[0], q[1] - at[1]))




# ---------------------------------------------------------------------------------------------------------------
# Network. North-side spines run north from South Station; south-side spines run south from North Station. A line's
# offset is its distance to the left of travel.
N_SPINE = [(-9, YS), (-9, 80)]
NE_SPINE = [(-9, YS), (-9, 11), (300, 11)]
A_W = [(3, YN), (3, -34), (-9, -46), (-9, -58), (-64, -58), (-164, -158)]   # Worcester pair: south, southwest, west, southwest
A_S = [(3, YN), (3, -34), (-9, -46), (-9, -300)]                         # Franklin, Providence and NYC high-speed: south
B_S = [(11, YN), (11, -31), (44, -64), (44, -300)]                       # Old Colony lines: south, southeast, south

SS_X = 86                  # South Salem, where the Peabody line and the Marblehead branch leave
HAVERHILL = ["Malden Center", "Oak Grove", "Reading", "North Wilmington", "Ballardvale", "Andover", "Lawrence", "Bradford", "Haverhill"]

PATHS, BRANCHES = {}, []   # line -> drawn polyline; (line, polyline) for branches
STATIONS = []              # dict(name, dots=[(line, xy)], side, kind, text, dx, dy, lp)
ARROWS = []                # (line, polyline, rows, placement): lines that run on off the poster


def build():
    P = PATHS
    # North side
    P["fit"] = join(par(cut(N_SPINE, (-9, 3)), 6), walk((-15, 3), ("NW", 55)))
    P["low"] = par(cut(N_SPINE, (-9, 52.4)), 4)
    P["hmon"] = par(cut(N_SPINE, (-9, 62)), 2)
    P["hmai"] = par(cut(N_SPINE, (-9, 62)), 0)
    P["hav"] = par(cut(N_SPINE, (-9, 20 + STEP * (len(HAVERHILL) - 1))), -2)
    P["pea"] = join(par(cut(NE_SPINE, (SS_X + 8, 11)), -4), walk((SS_X + 8, 7), ("N", 25)))
    P["nbp"] = join(par(cut(NE_SPINE, (SS_X + 58, 11)), -6), walk((SS_X + 58, 5), ("NE", 21)))
    # South side
    P["wor"] = cut(par(A_W, -4), (-125.1, -113.4))
    P["halb"] = cut(par(A_W, -2), (-133.8, -125.0))
    P["fra"] = join(par(cut(A_S, (-9, -74)), 0), walk((-9, -74), ("W", 31), ("SW", 37)))
    P["pro"] = par(cut(A_S, (-9, -121.1)), 2)
    P["hnyc"] = par(cut(A_S, (-9, -128)), 4)
    P["fr"] = par(cut(B_S, (44, -125.2)), -2)
    P["kin"] = join(par(cut(B_S, (44, -85)), 0), walk((44, -85), ("E", 28), ("S", 31.4)))
    P["grb"] = join(par(cut(B_S, (44, -77)), 2), walk((46, -77), ("E", 56), ("S", 31.4)))


def st(name, lines, at, side, kind="stop", text=None, dx=0.0, dy=0.0, lp=None):
    dots = [(ln, on_line(ln, at)) for ln in lines]
    STATIONS.append(dict(name=name, dots=dots, side=side, kind=kind, text=text, dx=dx, dy=dy, lp=lp))
    return dots


def diag_stops(line, names, start, d, a0, side, ends=(), lp=None):
    """Stops on a 45-degree leg: from `start`, a0 then DSTEP apart along direction d."""
    v = np.asarray(DIRS[d], float)
    out = {}
    for i, n in enumerate(names):
        q = np.asarray(start, float) + v * (a0 + DSTEP * i)
        out[n] = st(n, [line], tuple(q), side, "end" if n in ends else "stop", lp=lp if n in ends else None)[0][1]
    return out


def col_stops(line, names, x, y0, side, step=STEP, ends=(), sign=1, lp=None):
    out = {}
    for i, n in enumerate(names):
        out[n] = st(n, [line], (x, y0 + sign * step * i), side, "end" if n in ends else "stop", lp=lp if n in ends else None)[0][1]
    return out


def stations():
    """Every station, its lines, and where its name sits."""
    # The BIGGER Dig
    every = ["fit", "low", "hmon", "hmai", "hav", "pea", "nbp", "wor", "halb", "fra", "pro", "hnyc", "fr", "kin", "grb"]
    st("North Station", every, (0, YN), "r", "hub")
    st("Boston Central", every, (0, YC), "r", "hub")
    st("South Station", every, (0, YS), "r", "hub")

    # Fitchburg Line, northwest, names to the left
    fit = diag_stops("fit", ["Porter", "Waltham", "Brandeis/Roberts", "Kendal Green", "Lincoln", "Concord", "West Concord", "South Acton",
                             "Littleton/Route 495", "Ayer", "Shirley", "North Leominster", "Fitchburg", "Wachusett"], (-15, 3), "NW", 4.0, "l")
    sa = fit["South Acton"]
    BRANCHES.append(("fit", walk(sa, ("W", 34))))
    st("Hudson", ["fit"], (sa[0] - 20, sa[1]), "b")
    st("Marlborough", ["fit"], (sa[0] - 34, sa[1]), "l", "end")
    ARROWS.append(("fit", PATHS["fit"], ["TO GREENFIELD, NORTH ADAMS"], "nw"))

    # Lowell and Haverhill, side by side with the two northern high-speed lines between them
    st("Sullivan Sq", ["low", "hmon", "hmai", "hav"], (-10, 15), "r", "pass")
    col_stops("low", ["West Medford", "Wedgemere", "Winchester", "Anderson/Woburn", "Wilmington", "North Billerica", "Lowell"], -13, 26, "l",
              ends=("Lowell",), lp="low")
    # Haverhill trains stop at Oak Grove as at Malden Center, and run express past the Melrose and Wakefield stops Orange took over
    col_stops("hav", HAVERHILL, -7, 20, "r", ends=("Haverhill",), lp="hav")
    ARROWS.append(("hmon", PATHS["hmon"], ["HIGH-SPEED RAIL TO CONCORD NH, MONTREAL", "VIA LOWELL, NASHUA, MANCHESTER, BURLINGTON VT"], "n-left"))
    ARROWS.append(("hmai", PATHS["hmai"], ["HIGH-SPEED RAIL TO BANGOR", "VIA HAVERHILL, PORTLAND, AUGUSTA"], "n-right"))

    # Peabody and Newburyport/Rockport: east together, then apart at South Salem
    for n, x in (("Chelsea", 20), ("Central Sq", 40), ("Swampscott", 61)):
        st(n, ["pea", "nbp"], (x, 6), "t")
    ss = st("South Salem", ["pea", "nbp"], (SS_X, 6), "t")
    col_stops("pea", ["Peabody", "Danversport", "Danvers", "Middleton"], SS_X + 8, 14, "l")
    ARROWS.append(("pea", PATHS["pea"], ["PEABODY LINE", "TO LAWRENCE"], "n-left-pill"))
    # Marblehead branch from South Salem, through Clifton (Max's stop, a Marblehead neighborhood)
    nb = dict(ss)["nbp"]
    BRANCHES.append(("nbp", walk(nb, ("SE", 10))))
    st("Clifton", ["nbp"], (nb[0] + 5, nb[1] - 5), "r")
    st("Marblehead", ["nbp"], (nb[0] + 10, nb[1] - 10), "r", "end")
    st("Salem", ["nbp"], (SS_X + 28, 5), "b")
    bev = st("Beverly", ["nbp"], (SS_X + 44, 5), "b")[0][1]
    BRANCHES.append(("nbp", walk(bev, ("NE", 4), ("N", 20.6))))
    col_stops("nbp", ["North Beverly", "Hamilton/Wenham", "Ipswich", "Rowley", "Newburyport"], SS_X + 48, 12.0, "l", ends=("Newburyport",))
    diag_stops("nbp", ["Montserrat", "Beverly Farms", "Manchester", "West Gloucester", "Gloucester", "Rockport"], (SS_X + 58, 5), "NE", 3.0, "r",
               ends=("Rockport",), lp="nbp")

    # Worcester Line, with the Albany high-speed line on its inner side
    st("Back Bay", ["wor", "halb", "fra", "pro", "hnyc"], (-9, -50), "r", "tier2")
    st("David Ortiz", ["wor"], (-30, -54), "t")
    st("West Station", ["wor", "halb"], (-69.7, -58), "l", "tier2")
    diag_stops("wor", ["Boston Landing", "Newtonville", "West Newton", "Auburndale", "Wellesley Farms", "Wellesley Hills", "Wellesley Square",
                       "Natick Center", "West Natick", "Framingham", "Ashland", "Southborough", "Westborough", "Grafton", "Worcester"],
               (-69.7, -58), "SW", 5.0, "l", ends=("Worcester",), lp="wor")
    ARROWS.append(("halb", PATHS["halb"], ["HIGH-SPEED RAIL TO ALBANY, CHICAGO", "VIA WORCESTER, SPRINGFIELD"], "sw"))

    # Franklin and Providence together to Readville
    for n, y in (("Ruggles", -60), ("Hyde Park", -65), ("Readville", -70)):
        st(n, ["fra", "pro"], (-8, y), "l")
    fra = diag_stops("fra", ["Endicott", "Dedham Corporate Center", "Islington", "Norwood Depot", "Norwood Central", "Windsor Gardens", "Walpole",
                             "Norfolk", "Franklin", "Forge Park/495"], (-40, -74), "SW", 3.5, "l", ends=("Forge Park/495",), lp="fra")
    st("Route 128", ["pro", "hnyc"], (-6, -77), "l")
    cj = st("Canton Junction", ["pro"], (-7, -84.5), "l")[0][1]
    st("Sharon", ["pro"], (-7, -92), "l")
    wal = fra["Walpole"]
    man = on(PATHS["pro"], (-7, wal[1]))
    BRANCHES.append(("fra", [wal, man]))
    st("Foxboro", ["fra"], ((wal[0] + man[0]) / 2, wal[1]), "b")
    st("Mansfield", ["pro", "fra"], man, "tl")
    col_stops("pro", ["Attleboro", "Pawtucket/Central Falls", "Providence", "TF Green Airport", "Wickford Junction"], -7, man[1] - STEP, "l",
              ends=("Wickford Junction",), sign=-1, lp="pro")
    ARROWS.append(("hnyc", PATHS["hnyc"], ["HIGH-SPEED RAIL TO NYC, PHILADELPHIA, WASHINGTON", "VIA PROVIDENCE, NEW HAVEN"], "s"))
    # Stoughton branch, east across the NYC high-speed line, then south to Taunton
    BRANCHES.append(("pro", walk(cj, ("E", 12), ("S", 26.6))))
    col_stops("pro", ["Canton Center", "Stoughton", "North Easton", "Easton Village", "Raynham Place", "Taunton"], 5, cj[1] - 4.6, "r",
              ends=("Taunton",), sign=-1)

    # Old Colony lines
    st("JFK/UMass", ["fr", "kin", "grb"], (44, -68), "l")
    st("Quincy Center", ["fr", "kin", "grb"], (44, -73), "l")
    st("Braintree", ["fr", "kin"], (43, -81), "l")
    col_stops("grb", ["Weymouth Landing/East Braintree", "East Weymouth", "Hingham", "Nantasket Junction", "Cohasset", "North Scituate", "Greenbush"],
              102, -82, "r", ends=("Greenbush",), sign=-1, lp="grb")
    col_stops("kin", ["South Weymouth", "Abington", "Whitman", "Hanson", "Halifax", "Kingston", "Plymouth"], 72, -90, "r", ends=("Plymouth",),
              sign=-1, lp="kin")
    frs = col_stops("fr", ["Holbrook/Randolph", "Montello", "Brockton", "Campello", "Bridgewater", "Middleborough", "East Taunton", "Church St",
                           "New Bedford"], 42, -90, "r", ends=("New Bedford",), sign=-1, lp="fr")
    mid, et = frs["Middleborough"], frs["East Taunton"]
    cape = walk(mid, ("E", 11))
    BRANCHES.append(("fr", cape))
    ARROWS.append(("fr", cape, ["TO CAPE COD"], "e"))
    BRANCHES.append(("fr", walk(et, ("SW", 9.4))))
    st("Freetown", ["fr"], (et[0] - 4.6, et[1] - 4.6), "l")
    st("Fall River Depot", ["fr"], (et[0] - 9.4, et[1] - 9.4), "l", "end")


# Names that differ from the station list, and per-station label tweaks
TEXT = {"Weymouth Landing/East Braintree": "Weymouth Landing/\nEast Braintree"}
SIDE_FIX = {"Middleborough": "l", "South Acton": "r"}


# ---------------------------------------------------------------------------------------------------------------
# Ferry docks at commuter stations, and where the high-speed boats stop. Docks inside the main map match the main map and the
# line posters. The coastal docks past its edge come from the ferry network poster, which gives them commuter rail pills.
# High-speed stops are the ferry poster's major ports plus Max's Langone Ferryport spec (November 7): Langone Ferryport, Salem,
# Gloucester, Rockport, Quincy and New Bedford. A white ring inside the pill marks them, after the ferry poster's bullseye docks.
FERRY_ROUTES = {"hw": ("Harbor West ferry", "#00796d", WHITE), "ns": ("North Shore ferry", "#9eb000", INK),
                "sse": ("South Shore Express ferry", "#611824", WHITE)}
FERRY = {  # station: (dock, route, high-speed boats stop)
    "North Station": ("Langone Ferryport", "hw", True), "Boston Central": ("Rowes Wharf", "hw", False),
    "South Station": ("Dorchester Ave", "hw", False), "Swampscott": ("Swampscott", "ns", False), "Clifton": ("Clifton", "ns", False),
    "Marblehead": ("Marblehead", "ns", False), "Salem": ("Salem Wharf", "ns", True), "Beverly": ("Beverly", "ns", False),
    "Beverly Farms": ("Beverly Farms", "ns", False), "Manchester": ("Manchester-by-the-Sea", "ns", False),
    "Gloucester": ("Gloucester", "ns", True), "Rockport": ("Rockport", "ns", True),
    "Quincy Center": ("Quincy", "sse", True), "New Bedford": ("New Bedford", "sse", True), "Fall River Depot": ("Fall River", "sse", False)}


def same_place(station, dock):
    """A dock named for its station's own town needs no "via": Salem Wharf at Salem, Quincy at Quincy Center."""
    a, b = station.lower(), dock.lower()
    return a.startswith(b) or b.startswith(a)


# Transfers: the same tables the line posters use, so a pill here matches the pill there.
def t_codes():
    out = {}
    for col, _style, _path, stops in M.lines():
        c = LP.CODES.get(col)
        for n in stops:
            n = n.rstrip("+")
            out.setdefault(n, [])
            if c and c not in out[n]:
                out[n].append(c)
    for n, extra in LP.EXTRA_TRANSFERS.items():
        out.setdefault(n, [])
        out[n] += [c for c in extra if c not in out[n]]
    for n in list(LP.FERRY_COLOR) + list(FERRY):
        out.setdefault(n, [])
        if "F" not in out[n]:
            out[n].append("F")
    # On this poster commuter and high-speed rail are drawn, so their pills drop out. Boston Central is State on the main map.
    out["Boston Central"] = list(set(out.get("Boston Central", []) + out.get("State", [])))
    out["David Ortiz"] = out.get("Hynes", [])  # one transfer station with Hynes
    return {n: [c for c in sorted(set(v), key=LP.ORDER.index) if c not in ("CR", "HSR")] for n, v in out.items()}


# ---------------------------------------------------------------------------------------------------------------
# Drawing
TEXTS, REG = [], {"line": [], "dot": [], "pill": []}


def width(text, fs, weight="normal"):
    w = 0
    for line in text.split("\n"):
        w = max(w, TextPath((0, 0), line, size=fs, prop=FontProperties(family="Arial", weight=weight)).get_extents().width)
    return w / PPU


def txt(ax, x, y, s, fs, weight="normal", ha="left", va="center", color=INK, z=11, owner=None, ls=1.0):
    s = s.replace("'", "’")
    t = ax.text(x, y, s, fontsize=fs, fontweight=weight, color=color, ha=ha, va=va, zorder=z, linespacing=ls, family="Arial")
    TEXTS.append((t, owner))
    return t


def stroke_line(ax, xy, key, z=4.0, lw=LW):
    d = LINES[key]
    if d.get("hsr"):
        ax.plot(*xy.T, color=PURPLE, lw=lw, solid_capstyle="butt", solid_joinstyle="round", zorder=z + 0.4)
        ax.plot(*xy.T, color=GOLD, lw=CORE * lw / LW, solid_capstyle="butt", solid_joinstyle="round", zorder=z + 0.45)
    else:
        ax.plot(*xy.T, color=d["hue"], lw=lw, solid_capstyle="butt", solid_joinstyle="round", zorder=z)
        ax.plot(*xy.T, color=PURPLE, lw=lw - 2 * RIM * lw / LW, solid_capstyle="butt", solid_joinstyle="round", zorder=z + 0.05)


def draw_line(ax, key, pts, z=4.0):
    xy = rounded(pts, R, n=16)
    stroke_line(ax, xy, key, z)
    REG["line"].append((key, LineString(xy).buffer(LW / PPU / 2, cap_style=2)))
    return xy


def head(ax, xy, z=4.6, half=1.6):
    """Purple arrowhead at the end of a line that runs on off the poster. Returns the tip."""
    a, b = np.asarray(xy[-2], float), np.asarray(xy[-1], float)
    v = (b - a) / np.hypot(*(b - a))
    n = np.array([-v[1], v[0]])
    tip = b + v * 2.4
    tri = [tuple(tip), tuple(b - n * half), tuple(b + n * half)]
    ax.add_patch(Polygon(tri, closed=True, fc=PURPLE, ec="none", zorder=z))
    REG["line"].append(("arrowhead", SPoly(tri)))
    return tip


EXPRESS_PAD = 1.6   # a high-speed ferry pill is this much wider, so its letters clear the white ring


def pill(ax, x0, y, text, fill, fg=WHITE, h=2.9, z=7, ring=None, fs=8.4, gold=False, express=False):
    """A rounded pill from x0 to the right. ring: a second color just inside the edge, as on the NERTA mark.
    express: a thin white ring inside the edge, where high-speed boats stop (the ferry poster's bullseye docks)."""
    w = (6.6 if len(text) <= 3 else width(text, fs, "bold") + 2.8) + (EXPRESS_PAD if express else 0)
    ax.add_patch(FancyBboxPatch((x0, y - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=fill, ec=PAPER, lw=1.0, zorder=z))
    if ring or express:
        k, t = (0.3, 0.26) if express else (0.36, 0.42)
        ax.add_patch(FancyBboxPatch((x0 + k, y - h / 2 + k), w - 2 * k, h - 2 * k, boxstyle=f"round,pad=0,rounding_size={h / 2 - k}", fc=WHITE if express else ring, ec="none", zorder=z + 0.01))
        k2 = k + t
        ax.add_patch(FancyBboxPatch((x0 + k2, y - h / 2 + k2), w - 2 * k2, h - 2 * k2, boxstyle=f"round,pad=0,rounding_size={h / 2 - k2}", fc=fill, ec="none", zorder=z + 0.02))
    if gold:
        k = 0.55
        ax.add_patch(FancyBboxPatch((x0 + k, y - h / 2 + k), w - 2 * k, h - 2 * k, boxstyle=f"round,pad=0,rounding_size={h / 2 - k}", fc=GOLD, ec="none", zorder=z + 0.01))
    ax.text(x0 + w / 2, y - 0.08, text, fontsize=fs, fontweight="bold", color=fg, ha="center", va="center", zorder=z + 0.5, family="Arial")
    REG["pill"].append(box(x0, y - h / 2, x0 + w, y + h / 2))
    return w


def code_text(code, station):
    if code == "F" and station in FERRY:
        dock = FERRY[station][0]
        return "F" if same_place(station, dock) else f"F via {dock}"
    return LP.pill_text(code, station) if code == "F" else code


def code_w(code, station):
    t = code_text(code, station)
    return (6.6 if len(t) <= 3 else width(t, 8.2, "bold") + 2.8) + (EXPRESS_PAD if code == "F" and ferry_look(station)[3] else 0)


def ferry_look(station):
    """Fill, text color, Key name and high-speed flag of a station's ferry pill."""
    if station in FERRY:
        _dock, route, fast = FERRY[station]
        name, fill, fg = FERRY_ROUTES[route]
        return fill, fg, name, fast
    fill = LP.FERRY_COLOR.get(station, M.FERRY)
    return fill, INK if fill == M.ROUTE_COLOR.get("north-shore") else WHITE, LP.ferry_name(fill), False


def t_pill(ax, x0, y, code, station):
    text = code_text(code, station)
    if code == "F":
        fill, fg, _name, fast = ferry_look(station)
        return pill(ax, x0, y, text, fill, fg, fs=8.6 if len(text) <= 3 else 8.2, express=fast)
    return pill(ax, x0, y, text, LP.PILL[code], INK if code == "YL" else WHITE, fs=8.6 if len(text) <= 3 else 8.2)


def pills_w(codes, station):
    return sum(code_w(c, station) for c in codes) + 0.35 * (len(codes) - 1)


def pill_row(ax, x, y, codes, sign, station):
    """Pills read outward from x: right when sign > 0, left when sign < 0, always in house order left to right. Returns the far end."""
    total = pills_w(codes, station)
    x0 = x if sign > 0 else x - total
    for c in codes:
        x0 += t_pill(ax, x0, y, c, station) + 0.35
    return x + sign * total


def lp_w(key):
    return width(LINES[key]["name"], 7.8, "bold") + 2.8


def line_pill(ax, x, y, key, sign=1):
    """The line's name in a purple pill with the line's own color just inside its edge. Returns the far end."""
    w = lp_w(key)
    x0 = x if sign > 0 else x - w
    pill(ax, x0, y, LINES[key]["name"], PURPLE, WHITE, h=3.1, ring=LINES[key]["hue"], fs=7.8, z=7.5)
    return x + sign * w


def draw_station(ax, s, codes):
    dots = [q for _, q in s["dots"]]
    junction = len(dots) > 1 and all(np.hypot(q[0] - dots[0][0], q[1] - dots[0][1]) < 0.5 for q in dots)
    if junction:  # a branch ending on another line (Foxboro trains at Mansfield): one dot, drawn as a transfer
        dots = dots[:1]
    kind, side = s["kind"], SIDE_FIX.get(s["name"], s["side"])
    xs, ys = [q[0] for q in dots], [q[1] for q in dots]
    owner = s["name"]
    if len(dots) > 1:
        a, b = dots[0], dots[-1]
        big = kind == "hub"
        lw = LW * (1.85 if big else 1.32)
        z = 4.2 if kind == "pass" else 5.0  # a capsule the gold line passes over: high-speed trains run through without stopping
        ax.plot([a[0], b[0]], [a[1], b[1]], color=INK, lw=lw, solid_capstyle="round", zorder=z)
        ax.plot([a[0], b[0]], [a[1], b[1]], color=WHITE, lw=lw * 0.62, solid_capstyle="round", zorder=z + 0.01)
        REG["dot"].append((owner, LineString([a, b]).buffer(lw / PPU / 2)))
    else:
        q = dots[0]
        if kind == "end":
            ax.scatter(*q, s=(LW * 1.5) ** 2, color=WHITE, edgecolor=PURPLE, lw=2.2, zorder=6)
            r = (LW * 1.5 / 2 + 1.1) / PPU
        elif codes or junction:
            ax.scatter(*q, s=(LW * 1.2) ** 2, color=WHITE, edgecolor=INK, lw=1.7, zorder=6)
            r = (LW * 1.2 / 2 + 0.85) / PPU
        else:
            ax.scatter(*q, s=(LW * 0.78) ** 2, color=WHITE, edgecolor=INK, lw=0.8, zorder=6)
            r = (LW * 0.78 / 2 + 0.4) / PPU
        REG["dot"].append((owner, Point(q).buffer(r)))
    # Name, then its transfer pills, then (at a line's end) the line's own pill
    text = s["text"] or TEXT.get(s["name"], s["name"])
    if kind == "hub":
        fs, weight, text = FS_BIG, "bold", text.upper()
    elif kind == "tier2":
        fs, weight, text = 11.6, "bold", text.upper()
    elif kind == "end":
        fs, weight, text = FS_END, "bold", text.upper()
    else:
        fs, weight = FS, "normal"
    gap = {"hub": 3.6, "end": 2.6, "tier2": 3.2}.get(kind, 2.3 if len(dots) == 1 else 2.6)
    w = width(text, fs, weight)
    x = max(xs) if side == "r" else min(xs) if side in ("l", "tl") else (min(xs) + max(xs)) / 2
    y = sum(ys) / len(ys)
    x, y = x + s["dx"], y + s["dy"]
    pw = pills_w(codes, s["name"]) if codes else 0
    lw_ = lp_w(s["lp"]) + 1.4 if s["lp"] else 0
    if side == "r":
        txt(ax, x + gap, y - 0.05, text, fs, weight, "left", "center", owner=owner)
        far = x + gap + w
        if codes:
            far = pill_row(ax, far + 1.4, y, codes, 1, s["name"])
        if s["lp"]:
            line_pill(ax, far + 1.4, y, s["lp"], 1)
    elif side in ("l", "tl"):
        yy = y + (1.5 if side == "tl" else 0)
        txt(ax, x - gap, yy - 0.05, text, fs, weight, "right", "center", owner=owner)
        far = x - gap - w
        if codes:
            far = pill_row(ax, far - 1.4, yy, codes, -1, s["name"])
        if s["lp"]:
            line_pill(ax, far - 1.4, yy, s["lp"], -1)
    elif side in ("t", "b"):
        top = max(ys) + 2.5 if side == "t" else min(ys) - 2.5
        va = "bottom" if side == "t" else "top"
        x0 = x - (w + (1.4 + pw if codes else 0) + lw_) / 2
        txt(ax, x0, top, text, fs, weight, "left", va, owner=owner)
        h = 2.2 if "\n" not in text else 4.2
        cy = top + (h / 2 if side == "t" else -h / 2)
        far = x0 + w
        if codes:
            far = pill_row(ax, far + 1.4, cy, codes, 1, s["name"])
        if s["lp"]:
            line_pill(ax, far + 1.4, cy, s["lp"], 1)


def draw_arrow(ax, key, pts, rows, where):
    """Arrowhead, then the rows: purple bold capitals, as on the main map's edge labels."""
    xy = rounded(pts, R, n=16)
    tip = head(ax, xy, half=0.95 if where.startswith("n-") and key in ("hmon", "hmai") else 1.6)  # the northern pair sits 2 units apart
    fs, lead = 8.2, 2.7
    if where == "nw":      # Fitchburg: the line's pill, then where it goes, to the left of the tip
        line_pill(ax, tip[0] - 1.2, tip[1] + 2.2, key, -1)
        txt(ax, tip[0] - 1.2, tip[1] - 1.2, rows[0], fs, "bold", "right", "center", color=PURPLE)
    elif where in ("n-left", "n-right"):  # high-speed rows above the tip, reading away from the other one
        sgn = -1 if where == "n-left" else 1
        for i, r in enumerate(rows):
            txt(ax, tip[0] + sgn * 1.0, tip[1] + 1.2 + lead * (len(rows) - 1 - i), r, fs, "bold", "right" if sgn < 0 else "left", "bottom", color=PURPLE)
    elif where == "n-left-pill":  # Peabody: line pill and TO row above the arrow, centered
        txt(ax, tip[0], tip[1] + 1.0, rows[1], fs, "bold", "center", "bottom", color=PURPLE)
        w = lp_w(key)
        line_pill(ax, tip[0] - w / 2, tip[1] + 1.0 + 2.6 + 1.9, key, 1)
    elif where == "sw":    # Albany: rows to the right of the tip
        for i, r in enumerate(rows):
            txt(ax, tip[0] + 3.4, tip[1] - 0.8 - lead * i, r, fs, "bold", "left", "center", color=PURPLE)
    elif where == "s":     # NYC: rows under the tip, centered
        for i, r in enumerate(rows):
            txt(ax, tip[0], tip[1] - 1.2 - lead * i, r, fs, "bold", "center", "top", color=PURPLE)
    elif where == "e":     # Cape Cod: row after the tip
        txt(ax, tip[0] + 1.2, tip[1] - 0.05, rows[0], fs, "bold", "left", "center", color=PURPLE)


def crossing(ax):
    """The Stoughton branch passes under the NYC high-speed line: a paper gap either side, like a bridge."""
    stb = [b for k, b in BRANCHES if k == "pro"][0]
    q = LineString(PATHS["hnyc"]).intersection(LineString(stb))
    if q.is_empty:
        return
    ax.plot([q.x, q.x], [q.y + 2.2, q.y - 2.2], color=PAPER, lw=LW + 3.0, solid_capstyle="butt", zorder=4.3)


# ---------------------------------------------------------------------------------------------------------------
# Header, notes and Key
PANEL_FC, PANEL_EC = "#f3f1f4", "#d9d3dc"


def panel(ax, x0, y0, x1, y1, z=1.0):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=3", fc=PANEL_FC, ec=PANEL_EC, lw=1.0, zorder=z))
    REG["pill"].append(box(x0, y0, x1, y1).exterior.buffer(0.01))  # only its edge counts for the checks


def header(ax, x0, y1, x1):
    hy = y1 - 11
    LP.roundel(ax, x0 + 10, hy, 6.4, PURPLE)
    draw_nerta(ax, x0 + 10, hy - (6.4 + 3.2 / 5.4 / 2) - 0.8, 2 * (6.4 + 3.2 / 5.4 / 2), "B", colors=(PURPLE,))
    ax.add_patch(FancyBboxPatch((x0 + 20, hy - 6), 28, 12, boxstyle="round,pad=0,rounding_size=6", fc=PURPLE, ec="none", zorder=12))
    k = 0.9
    ax.add_patch(FancyBboxPatch((x0 + 20 + k, hy - 6 + k), 28 - 2 * k, 12 - 2 * k, boxstyle=f"round,pad=0,rounding_size={6 - k}", fc=GOLD, ec="none", zorder=12.1))
    k2 = 1.9
    ax.add_patch(FancyBboxPatch((x0 + 20 + k2, hy - 6 + k2), 28 - 2 * k2, 12 - 2 * k2, boxstyle=f"round,pad=0,rounding_size={6 - k2}", fc=PURPLE, ec="none", zorder=12.2))
    ax.text(x0 + 34, hy - 0.4, "CR", fontsize=34, fontweight="bold", color=WHITE, ha="center", va="center", zorder=13)
    ax.text(x0 + 52, hy, "Commuter and" + chr(10) + "High-Speed Rail", fontsize=27, fontweight="bold", color=INK, ha="left", va="center", linespacing=1.1, zorder=13)
    ax.text(x1 - 5, hy + 2.2, "Map: Maxwell Howe", fontsize=9.6, color=INK, ha="right", va="center", zorder=13)
    ax.text(x1 - 5, hy - 2.2, "#30DayMapChallenge Day 8 • Utopia", fontsize=9.6, color=INK, ha="right", va="center", zorder=13)


def dig_note(ax):
    """The BIGGER Dig, beside the trunk."""
    x = TRUNK_X0 - 4.5
    txt(ax, x, YC + 4.6, "THE BIGGER DIG", 10.4, "bold", "right", "center")
    txt(ax, x, YC + 1.0, "Four tracks under Atlantic Ave.", 8.8, "normal", "right", "center")
    txt(ax, x, YC - 2.4, "Every train calls at North Station,", 8.8, "normal", "right", "center")
    txt(ax, x, YC - 5.8, "Boston Central and South Station.", 8.8, "normal", "right", "center")


def key(ax, kx0, ky1, used):
    """Line samples, symbols, the transfer pills used on this poster, and rider notes."""
    rows = []
    y = ky1 - 4.0
    txt(ax, kx0 + 3.5, y, "KEY", 11.0, "bold", "left", "center")
    y -= 5.4
    sx0, sx1 = kx0 + 4.0, kx0 + 13.0
    lx = kx0 + 15.5
    # commuter line sample: purple with one line's own color on its edges
    stroke_line(ax, np.array([(sx0, y), (sx1, y)]), "low")
    txt(ax, lx, y, "Commuter Rail. Each line has its own edge color", 8.8)
    y -= 4.4
    stroke_line(ax, np.array([(sx0, y), (sx1, y)]), "hmon")
    txt(ax, lx, y, "High-speed rail", 8.8)
    y -= 4.4
    ax.plot([sx0 + 2.5, sx1 - 2.5], [y, y], color=INK, lw=LW * 1.32, solid_capstyle="round", zorder=12)
    ax.plot([sx0 + 2.5, sx1 - 2.5], [y, y], color=WHITE, lw=LW * 1.32 * 0.62, solid_capstyle="round", zorder=12.01)
    txt(ax, lx, y, "Station on more than one line", 8.8)
    y -= 4.4
    ax.scatter((sx0 + sx1) / 2, y, s=(LW * 1.5) ** 2, color=WHITE, edgecolor=PURPLE, lw=2.2, zorder=12)
    txt(ax, lx, y, "End of the line", 8.8)
    y -= 4.4
    stroke_line(ax, np.array([(sx0, y), (sx1 - 2.4, y)]), "fra", z=11.5)
    tri = [(sx1, y), (sx1 - 2.4, y - 1.6), (sx1 - 2.4, y + 1.6)]
    ax.add_patch(Polygon(tri, closed=True, fc=PURPLE, ec="none", zorder=12))
    txt(ax, lx, y, "Line runs on beyond this map", 8.8)
    # Rider notes, under the samples, lined up with them
    notes = [("icon", "Every station is accessible"), ("text", "Driverless maglev, 24 hours a day"),
             ("text", "High-speed trains stop only at North Station,"), ("text", "Boston Central, South Station, Back Bay,"),
             ("text", "West Station and Route 128"), ("text", "Extra trains for TD Garden and Foxboro stadium events")]
    y -= 1.2
    for kind, t in notes:
        y -= 4.4
        if kind == "icon":
            M.icon(ax, (sx0 + sx1) / 2, y)
        txt(ax, lx, y, t, 8.8)
    y_left_end = y
    # Transfer pills, in house order, one ferry row per ferry color on this poster
    cx = kx0 + 72
    y = ky1 - 9.4
    boats, fast_any = [], False   # one row per ferry route on this poster, then the high-speed ring
    for code, station in used:
        if code == "F":
            fill, fg, name, fast = ferry_look(station)
            fast_any |= fast
            if (fill, fg, name) not in boats:
                boats.append((fill, fg, name))
    order = [v[1] for v in FERRY_ROUTES.values()]
    boats.sort(key=lambda b: order.index(b[0]) if b[0] in order else 99)
    codes = sorted({c for c, _ in used}, key=LP.ORDER.index)
    names = []
    for c in codes:
        entries = [(f, fg, n, None) for f, fg, n in boats] + ([(boats[0][0], boats[0][1], "High-speed boats stop here", WHITE)] if fast_any else []) \
            if c == "F" else [(LP.PILL[c], INK if c == "YL" else WHITE, LP.NAMES[c], None)]
        for fill, fg, name, ring in entries:
            pill(ax, cx - 3.3 - (EXPRESS_PAD / 2 if ring else 0), y, c, fill, fg, fs=8.6, z=12, express=bool(ring))
            txt(ax, cx + 4.8, y - 0.05, name, 8.8)
            names.append(name)
            y -= 4.4
    return min(y_left_end, y + 4.4) - 4.0, cx + 4.8 + max(width(n, 8.8) for n in names) + 4.0


# ---------------------------------------------------------------------------------------------------------------
def check(fig, ax):
    """Text on text, text on lines, dots and pills, pills on lines and dots, and every name nearest its own dot."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    shapes = []
    bad = []
    for t, owner in TEXTS:
        if t.get_rotation() != 0:
            bad.append("TILTED " + t.get_text())
        bb = t.get_window_extent(rend)
        (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        shapes.append((t.get_text().replace("\n", " ")[:30], box(x0, y0 + 0.3, x1, y1 - 0.3), owner))
    for i, (a, sa, oa) in enumerate(shapes):
        for b, sb, ob in shapes[i + 1:]:
            if sa.intersects(sb):
                bad.append(f"text/text: {a} | {b}")
            elif sa.distance(sb) < 0.6:
                bad.append(f"text close: {a} | {b} ({sa.distance(sb):.2f})")
        for key_, ln in REG["line"]:
            if sa.intersection(ln).area > 0.005 or (key_ == "arrowhead" and sa.distance(ln) < 0.4):
                bad.append(f"text/line: {a} | {key_}")
        for n, d in REG["dot"]:
            if sa.intersection(d).area > 0.02:
                bad.append(f"text/dot: {a} | {n}")
        for pb in REG["pill"]:
            if sa.intersection(pb).area > 0.02 and not sa.within(pb.buffer(0.05)):
                bad.append(f"text/pill: {a} | pill at {[round(v) for v in pb.bounds]}")
        if oa:  # every name nearer its own dot than any other
            own = min(d.distance(sa) for n, d in REG["dot"] if n == oa)
            for n, d in REG["dot"]:
                if n != oa and d.distance(sa) + 0.05 < own:
                    bad.append(f"nearer dot: {a} is {d.distance(sa):.1f} from {n}, {own:.1f} from its own")
                    break
    for k, pb in enumerate(REG["pill"]):
        for key_, ln in REG["line"]:
            if pb.intersection(ln).area > 0.05:
                bad.append(f"pill/line: pill at {[round(v) for v in pb.bounds]} | {key_}")
        for n, d in REG["dot"]:
            if pb.intersection(d).area > 0.05:
                bad.append(f"pill/dot: pill at {[round(v) for v in pb.bounds]} | {n}")
        for pc in REG["pill"][k + 1:]:
            if pb.intersection(pc).area > 0.05:
                bad.append(f"pill/pill: {[round(v) for v in pb.bounds]}")
    dots = REG["dot"]
    for i, (a, da) in enumerate(dots):
        for b, db in dots[i + 1:]:
            if a != b and da.intersects(db):
                bad.append(f"dot/dot: {a} | {b}")
    return bad


def next_version():
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        return int(sys.argv[1])
    v = 1
    while (OUT / f"rail_poster_v{v}.png").exists() or (OUT / f"rail_poster_v{v}.pdf").exists():
        v += 1
    return v


def main():
    v = next_version()
    png, pdf = OUT / f"rail_poster_v{v}.png", OUT / f"rail_poster_v{v}.pdf"
    draft = "--draft" in sys.argv
    if draft:  # trial renders go to a scratch folder, never into output/
        d = Path(sys.argv[sys.argv.index("--draft") + 1])
        png, pdf = d / "rail_draft.png", d / "rail_draft.pdf"
    for f in (png, pdf):
        if f.exists() and not draft:
            raise SystemExit(f"refusing to overwrite {f}")
    build()
    stations()
    codes = t_codes()

    X0, X1, Y0, Y1 = FRAME
    fig = plt.figure(figsize=((X1 - X0) * K, (Y1 - Y0) * K))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.patch.set_facecolor(PAPER)

    for key_, pts in PATHS.items():
        if key_ not in [a[0] for a in ARROWS if a[1] is PATHS.get(a[0])]:
            draw_line(ax, key_, pts)
    for key_, pts in BRANCHES:
        draw_line(ax, key_, pts)
    for key_, pts, rows, where in ARROWS:
        if pts is PATHS.get(key_):
            draw_line(ax, key_, pts)
        draw_arrow(ax, key_, pts, rows, where)
    crossing(ax)
    used = []
    for s in STATIONS:
        c = codes.get(s["name"], [])
        used += [(x, s["name"]) for x in c]
        draw_station(ax, s, c)
    dig_note(ax)
    kx0, ky1 = KEY_AT
    ky0, kx1 = key(ax, kx0, ky1, used)
    panel(ax, kx0, ky0 - 1.5, kx1, ky1)
    # The sheet fits the drawing: a margin round everything, room above for the header and below for the footer.
    # The scale (K inches a unit) never changes, so type keeps its size.
    fig.canvas.draw()
    rend, inv = fig.canvas.get_renderer(), ax.transData.inverted()
    bx = [g.bounds for _, g in REG["line"] + REG["dot"]] + [g.bounds for g in REG["pill"]]
    for t, _ in TEXTS:
        bb = t.get_window_extent(rend)
        (a, b), (c, d) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        bx.append((a, b, c, d))
    X0, Y0 = min(b[0] for b in bx) - 7, min(b[1] for b in bx) - 10
    X1, Y1 = max(b[2] for b in bx) + 7, max(b[3] for b in bx) + 25
    fig.set_size_inches((X1 - X0) * K, (Y1 - Y0) * K)
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    header(ax, X0, Y1, X1)
    ax.text(X1 - 5, Y0 + 4, "Layout schematic, not to scale. Not affiliated with the MBTA.", fontsize=7.6, color=INK, ha="right", va="bottom", zorder=13)
    print(f"sheet {(X1 - X0) * K:.1f} x {(Y1 - Y0) * K:.1f} in")

    bad = check(fig, ax)
    for b in bad:
        print("  ", b)
    print(f"{len(bad)} flags")
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=150 if draft else 600, facecolor=PAPER)
    if not draft:
        fig.savefig(pdf, facecolor=PAPER)
    print("written", png)


FRAME = (-220, 260, -200, 140)  # working sheet; main() trims it to the drawing
KEY_AT = (84, -10)              # left, top


if __name__ == "__main__":
    main()
