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
DSTEP = 3.11       # stop spacing on a 45-degree leg, per axis (4.4 along the line)
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


# ---------------------------------------------------------------------------------------------------------------
# Network. North-side spines run north from South Station; south-side spines run south from North Station. A line's
# offset is its distance to the left of travel.
N_SPINE = [(-9, YS), (-9, 80)]
NE_SPINE = [(-9, YS), (-9, 11), (300, 11)]
A_W = [(3, YN), (3, -34), (-9, -46), (-9, -58), (-64, -58), (-164, -158)]   # Worcester pair: south, southwest, west, southwest
A_S = [(3, YN), (3, -34), (-9, -46), (-9, -300)]                         # Franklin, Providence and NYC high-speed: south
B_S = [(11, YN), (11, -33), (31, -53), (31, -300)]                       # Old Colony lines: south, southeast, south

PATHS, BRANCHES = {}, []   # line -> drawn polyline; (line, polyline) for branches
STATIONS = []              # dict(name, dots=[(line, xy)], side, kind, text, dx, dy, pills)


def build():
    P = PATHS
    # North side
    P["fit"] = join(par(cut(N_SPINE, (-9, 3)), 6), walk((-15, 3), ("NW", 49)))
    P["low"] = par(cut(N_SPINE, (-9, 52.4)), 4)
    P["hmon"] = par(cut(N_SPINE, (-9, 61)), 2)
    P["hmai"] = par(cut(N_SPINE, (-9, 61)), 0)
    P["hav"] = par(cut(N_SPINE, (-9, 47.8)), -2)
    P["pea"] = join(par(cut(NE_SPINE, (82, 11)), -4), walk((82, 7), ("N", 25)))
    P["nbp"] = join(par(cut(NE_SPINE, (128, 11)), -6), walk((128, 5), ("NE", 21)))
    # South side
    P["wor"] = cut(par(A_W, -4), (-120, -112))
    P["halb"] = cut(par(A_W, -2), (-127, -121))
    P["fra"] = join(par(cut(A_S, (-9, -74)), 0), walk((-9, -74), ("W", 31), ("SW", 37)))
    P["pro"] = par(cut(A_S, (-9, -118.2)), 2)
    P["hnyc"] = par(cut(A_S, (-9, -125)), 4)
    P["fr"] = par(cut(B_S, (31, -117.2)), -2)
    P["kin"] = join(par(cut(B_S, (31, -77)), 0), walk((31, -77), ("E", 28), ("S", 30.4)))
    P["grb"] = join(par(cut(B_S, (31, -69)), 2), walk((33, -69), ("E", 56), ("S", 31.4)))


def st(name, lines, at, side, kind="stop", text=None, dx=0.0, dy=0.0, pills=None):
    dots = [(ln, on(PATHS[ln] if ln in PATHS else dict(BRANCHES)[ln], at)) for ln in lines]
    STATIONS.append(dict(name=name, dots=dots, side=side, kind=kind, text=text, dx=dx, dy=dy, pills=pills))
    return dots


def diag_stops(line, names, start, d, a0, side, ends=(), kinds=None):
    """Stops on a 45-degree leg: from `start`, a0 then DSTEP apart along direction d."""
    v = np.asarray(DIRS[d], float)
    out = {}
    for i, n in enumerate(names):
        q = np.asarray(start, float) + v * (a0 + DSTEP * i)
        out[n] = st(n, [line], tuple(q), side, "end" if n in ends else (kinds or {}).get(n, "stop"))[0][1]
    return out


def col_stops(line, names, x, y0, side, step=STEP, ends=(), sign=1):
    out = {}
    for i, n in enumerate(names):
        out[n] = st(n, [line], (x, y0 + sign * step * i), side, "end" if n in ends else "stop")[0][1]
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
    st("Marlborough", ["fit"], (sa[0] - 34, sa[1]), "b", "end")

    # Lowell and Haverhill, side by side with the two northern high-speed lines between them
    st("Sullivan Sq", ["low", "hmon", "hmai", "hav"], (-10, 12), "r", "pass")
    col_stops("low", ["West Medford", "Wedgemere", "Winchester", "Anderson/Woburn", "Wilmington", "North Billerica", "Lowell"], -13, 26, "l", ends=("Lowell",))
    col_stops("hav", ["Malden Center", "Reading", "North Wilmington", "Ballardvale", "Andover", "Lawrence", "Bradford", "Haverhill"], -7, 17, "r",
              step=(47.8 - 17) / 7, ends=("Haverhill",))

    # Peabody and Newburyport/Rockport: east together, then apart at South Salem
    for n, x in (("Chelsea", 24), ("Central Sq", 42), ("Swampscott", 60)):
        st(n, ["pea", "nbp"], (x, 6), "t")
    ss = st("South Salem", ["pea", "nbp"], (76, 6), "t")
    col_stops("pea", ["Peabody", "Danversport", "Danvers", "Middleton"], 82, 14, "l")
    nb = dict(ss)["nbp"]
    BRANCHES.append(("nbp", walk(nb, ("SE", 8))))
    st("Marblehead", ["nbp"], (nb[0] + 8, nb[1] - 8), "r", "end")
    st("Salem", ["nbp"], (96, 5), "b")
    bev = st("Beverly", ["nbp"], (114, 5), "b")[0][1]
    BRANCHES.append(("nbp", walk(bev, ("NE", 4), ("N", 20.6))))
    col_stops("nbp", ["North Beverly", "Hamilton/Wenham", "Ipswich", "Rowley", "Newburyport"], 118, 12.4, "l", ends=("Newburyport",))
    diag_stops("nbp", ["Montserrat", "Beverly Farms", "Manchester", "West Gloucester", "Gloucester", "Rockport"], (128, 5), "NE", 3.0, "r",
               ends=("Rockport",))

    # Worcester Line, with the Albany high-speed line on its inner side
    st("Back Bay", ["wor", "halb", "fra", "pro", "hnyc"], (-9, -50), "r", "tier2")
    st("David Ortiz", ["wor"], (-24, -54), "t")
    st("West Station", ["wor", "halb"], (-66, -57), "l", "tier2")
    wor_d = diag_stops("wor", ["Boston Landing", "Newtonville", "West Newton", "Auburndale", "Wellesley Farms", "Wellesley Hills", "Wellesley Square",
                               "Natick Center", "West Natick", "Framingham", "Ashland", "Southborough", "Westborough", "Grafton", "Worcester"],
                       (-62, -60), "SW", 3.6, "l", ends=("Worcester",))

    # Franklin and Providence together to Readville
    for n, y in (("Ruggles", -58), ("Hyde Park", -64), ("Readville", -70)):
        st(n, ["fra", "pro"], (-8, y), "l")
    fra = diag_stops("fra", ["Endicott", "Dedham Corporate Center", "Islington", "Norwood Depot", "Norwood Central", "Windsor Gardens", "Walpole",
                             "Norfolk", "Franklin", "Forge Park/495"], (-40, -74), "SW", 3.5, "l", ends=("Forge Park/495",))
    st("Route 128", ["pro", "hnyc"], (-6, -77), "l")
    cj = st("Canton Junction", ["pro"], (-7, -83.4), "l")[0][1]
    st("Sharon", ["pro"], (-7, -89.8), "l")
    wal = fra["Walpole"]
    man = on(PATHS["pro"], (-7, wal[1]))
    BRANCHES.append(("fra", [wal, man]))
    st("Foxboro", ["fra"], ((wal[0] + man[0]) / 2, wal[1]), "b")
    st("Mansfield", ["pro", "fra"], man, "tl")
    col_stops("pro", ["Attleboro", "Pawtucket/Central Falls", "Providence", "TF Green Airport", "Wickford Junction"], -7, man[1] - STEP, "l",
              ends=("Wickford Junction",), sign=-1)
    # Stoughton branch, east across the NYC high-speed line, then south to Taunton
    BRANCHES.append(("pro", walk(cj, ("E", 12), ("S", 26.6))))
    col_stops("pro", ["Canton Center", "Stoughton", "North Easton", "Easton Village", "Raynham Place", "Taunton"], 5, cj[1] - 4.6, "r",
              ends=("Taunton",), sign=-1)

    # Old Colony lines
    st("JFK/UMass", ["fr", "kin", "grb"], (31, -60), "l")
    st("Quincy Center", ["fr", "kin", "grb"], (31, -65), "l")
    st("Braintree", ["fr", "kin"], (30, -73), "l")
    col_stops("grb", ["Weymouth Landing/East Braintree", "East Weymouth", "Hingham", "Nantasket Junction", "Cohasset", "North Scituate", "Greenbush"],
              89, -74, "r", ends=("Greenbush",), sign=-1)
    col_stops("kin", ["South Weymouth", "Abington", "Whitman", "Hanson", "Halifax", "Kingston", "Plymouth"], 59, -82, "r", ends=("Plymouth",), sign=-1)
    frs = col_stops("fr", ["Holbrook/Randolph", "Montello", "Brockton", "Campello", "Bridgewater", "Middleborough", "East Taunton", "Church St",
                           "New Bedford"], 29, -82, "r", ends=("New Bedford",), sign=-1)
    mid, et = frs["Middleborough"], frs["East Taunton"]
    BRANCHES.append(("fr", walk(mid, ("E", 11))))
    BRANCHES.append(("fr", walk(et, ("SW", 9.4))))
    st("Freetown", ["fr"], (et[0] - 4.6, et[1] - 4.6), "l")
    st("Fall River Depot", ["fr"], (et[0] - 9.4, et[1] - 9.4), "l", "end")


# Names that differ from the station list, and per-station label tweaks
TEXT = {"Weymouth Landing/East Braintree": "Weymouth Landing/\nEast Braintree", "Dedham Corporate Center": "Dedham Corporate Center"}
SIDE_FIX = {"Middleborough": "l", "East Taunton": "l"}
# Arrowheads and the words beside them: (line, end point index -1 of which path, rows)
TO_ROWS = {}


# ---------------------------------------------------------------------------------------------------------------
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
    for n in LP.FERRY_COLOR:
        out.setdefault(n, [])
        if "F" not in out[n]:
            out[n].append("F")
    # On this poster commuter and high-speed rail are drawn, so their pills drop out. Boston Central is State on the main map.
    out["Boston Central"] = sorted(set(out.get("Boston Central", []) + out.get("State", [])) - {"CR", "HSR"}, key=LP.ORDER.index)
    out["David Ortiz"] = out.get("Hynes", [])  # one transfer station with Hynes
    return {n: [c for c in sorted(v, key=LP.ORDER.index) if c not in ("CR", "HSR")] for n, v in out.items()}


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


def draw_line(ax, key, pts, z=4.0):
    xy = rounded(pts, R, n=16)
    d = LINES[key]
    if d.get("hsr"):
        ax.plot(*xy.T, color=PURPLE, lw=LW, solid_capstyle="butt", solid_joinstyle="round", zorder=z + 0.4)
        ax.plot(*xy.T, color=GOLD, lw=CORE, solid_capstyle="butt", solid_joinstyle="round", zorder=z + 0.45)
    else:
        ax.plot(*xy.T, color=d["hue"], lw=LW, solid_capstyle="butt", solid_joinstyle="round", zorder=z)
        ax.plot(*xy.T, color=PURPLE, lw=LW - 2 * RIM, solid_capstyle="butt", solid_joinstyle="round", zorder=z + 0.05)
    REG["line"].append((key, LineString(xy).buffer(LW / PPU / 2, cap_style=2)))
    return xy


def arrow(ax, xy, z=4.6):
    """Purple arrowhead at the end of a line that runs on off the poster."""
    a, b = np.asarray(xy[-2], float), np.asarray(xy[-1], float)
    v = (b - a) / np.hypot(*(b - a))
    n = np.array([-v[1], v[0]])
    tip = b + v * 2.2
    ax.add_patch(Polygon([tip, b - n * 1.5, b + n * 1.5], closed=True, fc=PURPLE, ec="none", zorder=z))
    REG["line"].append(("arrow", Polygon_shape([tip, b - n * 1.5, b + n * 1.5])))
    return tip


def Polygon_shape(pts):
    from shapely.geometry import Polygon as SP
    return SP(pts)


def pill(ax, x0, y, text, fill, fg=WHITE, h=2.9, z=7, ring=None, fs=8.4, gold=False):
    """A rounded pill from x0 to the right. ring: a second color just inside the edge, as on the NERTA mark."""
    w = 6.6 if len(text) <= 2 else width(text, fs, "bold") + 2.8
    ax.add_patch(FancyBboxPatch((x0, y - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=fill, ec=PAPER, lw=1.0, zorder=z))
    if ring:
        k = 0.42
        ax.add_patch(FancyBboxPatch((x0 + k, y - h / 2 + k), w - 2 * k, h - 2 * k, boxstyle=f"round,pad=0,rounding_size={h / 2 - k}", fc=ring, ec="none", zorder=z + 0.01))
        k2 = k + 0.42
        ax.add_patch(FancyBboxPatch((x0 + k2, y - h / 2 + k2), w - 2 * k2, h - 2 * k2, boxstyle=f"round,pad=0,rounding_size={h / 2 - k2}", fc=fill, ec="none", zorder=z + 0.02))
    if gold:
        k = 0.55
        ax.add_patch(FancyBboxPatch((x0 + k, y - h / 2 + k), w - 2 * k, h - 2 * k, boxstyle=f"round,pad=0,rounding_size={h / 2 - k}", fc=GOLD, ec="none", zorder=z + 0.01))
    ax.text(x0 + w / 2, y - 0.08, text, fontsize=fs, fontweight="bold", color=fg, ha="center", va="center", zorder=z + 0.5, family="Arial")
    REG["pill"].append(box(x0, y - h / 2, x0 + w, y + h / 2))
    return w


def t_pill(ax, x0, y, code, station):
    text = LP.pill_text(code, station) if code == "F" else code
    fill = LP.FERRY_COLOR.get(station, M.FERRY) if code == "F" else LP.PILL[code]
    fg = INK if code == "YL" or (code == "F" and fill == M.ROUTE_COLOR.get("north-shore")) else WHITE
    return pill(ax, x0, y, text, fill, fg, fs=8.6 if len(text) <= 2 else 8.2)


def pills_w(codes, station):
    return sum((6.6 if len(LP.pill_text(c, station) if c == "F" else c) <= 2 else width(LP.pill_text(c, station), 8.2, "bold") + 2.8) for c in codes) + 0.35 * (len(codes) - 1)


def pill_row(ax, x, y, codes, sign, station):
    """Pills read outward from x: to the right when sign > 0, to the left when sign < 0, always in house order left to right."""
    total = pills_w(codes, station)
    x0 = x if sign > 0 else x - total
    for c in codes:
        x0 += t_pill(ax, x0, y, c, station) + 0.35


def line_pill(ax, x, y, key, sign=1):
    d = LINES[key]
    w = width(d["name"], 8.0, "bold") + 2.8
    x0 = x if sign > 0 else x - w
    pill(ax, x0, y, d["name"], PURPLE, WHITE, h=3.0, ring=d["hue"], fs=8.0, z=7.5)
    return w


def draw_station(ax, s, codes):
    dots = [q for _, q in s["dots"]]
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
        elif codes:
            ax.scatter(*q, s=(LW * 1.2) ** 2, color=WHITE, edgecolor=INK, lw=1.7, zorder=6)
            r = (LW * 1.2 / 2 + 0.85) / PPU
        else:
            ax.scatter(*q, s=(LW * 0.78) ** 2, color=WHITE, edgecolor=INK, lw=0.8, zorder=6)
            r = (LW * 0.78 / 2 + 0.4) / PPU
        REG["dot"].append((owner, Point(q).buffer(r)))
    # Name
    text = s["text"] or TEXT.get(s["name"], s["name"])
    if kind == "hub":
        fs, weight, text = FS_BIG, "bold", text.upper()
    elif kind == "tier2":
        fs, weight, text = 11.6, "bold", text.upper()
    elif kind == "end":
        fs, weight, text = FS_END, "bold", text.upper()
    else:
        fs, weight = FS, "normal"
    gap = 2.3 if len(dots) == 1 else 2.6
    if kind == "hub":
        gap = 3.6
    if kind in ("end", "tier2"):
        gap += 0.6
    w = width(text, fs, weight)
    x, y = (max(xs) if side in ("r",) else min(xs) if side in ("l", "tl") else (min(xs) + max(xs)) / 2), (sum(ys) / len(ys))
    x, y = x + s["dx"], y + s["dy"]
    pw = pills_w(codes, s["name"]) if codes else 0
    if side == "r":
        txt(ax, x + gap, y - 0.05, text, fs, weight, "left", "center", owner=owner)
        if codes:
            pill_row(ax, x + gap + w + 1.4, y, codes, 1, s["name"])
    elif side in ("l", "tl"):
        yy = y + (1.5 if side == "tl" else 0)
        txt(ax, x - gap, yy - 0.05, text, fs, weight, "right", "center", owner=owner)
        if codes:
            pill_row(ax, x - gap - w - 1.4, yy, codes, -1, s["name"])
    elif side in ("t", "b"):
        top = max(ys) + 2.5 if side == "t" else min(ys) - 2.5
        va = "bottom" if side == "t" else "top"
        x0 = x - (w + (1.4 + pw if codes else 0)) / 2
        txt(ax, x0, top, text, fs, weight, "left", va, owner=owner)
        if codes:
            h = 1.85 if "\n" not in text else 3.6
            pill_row(ax, x0 + w + 1.4, top + (h / 2 if side == "t" else -h / 2), codes, 1, s["name"])
    return w


# ---------------------------------------------------------------------------------------------------------------
def check(fig, ax):
    """Text on text, text on lines, dots and pills, pills on lines and dots, and every name nearest its own dot."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    shapes = []
    for t, owner in TEXTS:
        if t.get_rotation() != 0:
            shapes.append(("TILTED " + t.get_text(), None, owner))
        bb = t.get_window_extent(rend)
        (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        shapes.append((t.get_text().replace("\n", " ")[:30], box(x0, y0 + 0.3, x1, y1 - 0.3), owner))
    bad = [s[0] for s in shapes if s[1] is None]
    shapes = [s for s in shapes if s[1] is not None]
    for i, (a, sa, oa) in enumerate(shapes):
        for b, sb, ob in shapes[i + 1:]:
            if sa.intersects(sb):
                bad.append(f"text/text: {a} | {b}")
            elif sa.distance(sb) < 0.6:
                bad.append(f"text close: {a} | {b} ({sa.distance(sb):.2f})")
        for key, ln in REG["line"]:
            if sa.intersection(ln).area > 0.02:
                bad.append(f"text/line: {a} | {key}")
        for n, d in REG["dot"]:
            if sa.intersection(d).area > 0.02:
                bad.append(f"text/dot: {a} | {n}")
        for pb in REG["pill"]:
            if sa.intersection(pb).area > 0.02 and not sa.within(pb.buffer(0.05)):
                bad.append(f"text/pill: {a} | pill at {[round(v) for v in pb.bounds]}")
        if oa:  # nearest dot
            own = min(d.distance(sa) for n, d in REG["dot"] if n == oa)
            for n, d in REG["dot"]:
                if n != oa and d.distance(sa) + 0.05 < own:
                    bad.append(f"nearer dot: {a} is {d.distance(sa):.1f} from {n}, {own:.1f} from its own")
                    break
    for k, pb in enumerate(REG["pill"]):
        for key, ln in REG["line"]:
            if pb.intersection(ln).area > 0.05:
                bad.append(f"pill/line: pill at {[round(v) for v in pb.bounds]} | {key}")
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

    x0, x1, y0, y1 = -150, 175, -150, 95
    fig = plt.figure(figsize=((x1 - x0) * K, (y1 - y0) * K))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.patch.set_facecolor(PAPER)

    drawn = {}
    for key, pts in PATHS.items():
        drawn[key] = draw_line(ax, key, pts)
    for key, pts in BRANCHES:
        draw_line(ax, key, pts)
    for s in STATIONS:
        draw_station(ax, s, codes.get(s["name"], []) if s["kind"] != "hub" else codes.get(s["name"], []))

    bad = check(fig, ax)
    for b in bad:
        print("  ", b)
    print(f"{len(bad)} flags")
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=150 if draft else 600, facecolor=PAPER)
    if not draft:
        fig.savefig(pdf, facecolor=PAPER)
    print("written", png)


if __name__ == "__main__":
    main()
