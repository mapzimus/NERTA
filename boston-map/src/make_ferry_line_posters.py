"""Ferry route posters: one poster for every route on the Ferry Network poster, drawn like the T line posters.

Header: NERTA's multicolor T in its white roundel and the multicolor NERTA mark (make_tmap.NERTA_COLORS, Max, November 8:
"send it throughout"), a code pill in the route color (F for harbor and river boats, FF for fast ferries), the route's
rider name, and the release block at the top right. Under it the route as a strip, north (or the outbound end) at the
top: round dots for harbor and river boats, streaks for high-speed boats, a pill for every transfer, then a Key with the
pills used and the rider notes, the Charlie Points row among them. Free rides (the Fast Ferry shuttle and the river
zigzag boats) carry the white FREE tag on the line and a FREE row in the Key (research/fares-changes-for-all-maps.md).

Stops, their order, transfer pills, major ports, dock labels and route colors are all read from
make_ferry_network.py (ROUTE_STOPS, S, MAJOR, R, LOOPS), so a route poster cannot disagree with the Ferry Network
poster. Only the layout (where each dock sits on the strip) is written here. Nothing in another script is changed.

Writes only to output/copies/ferry_lines_v1/ and never overwrites, except with --replace, which re-renders the named routes
over this script's own files in that folder (nothing else). Trial renders go to a folder named with --draft.
Run: python make_ferry_line_posters.py [route ...] [--draft DIR] [--dpi N] [--replace]
"""
import sys
from functools import lru_cache
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon  # noqa: E402
from shapely.geometry import LineString, Point, box  # noqa: E402
from shapely.geometry import Polygon as SPoly  # noqa: E402
from shapely.geometry.polygon import orient  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import make_ferry_network as FN  # noqa: E402  (route tables and the ferry drawing helpers; import only)
import make_line_poster as LP  # noqa: E402  (pill colors, light(); import only)
import make_tmap as M  # noqa: E402  (accessible icon, NERTA_COLORS, WEB switch; import only)
import charlie_points as CP  # noqa: E402  (the shared Charlie Points coin, FREE tag and Key wording, November 8)
from nerta_mark import draw_nerta, draw_t  # noqa: E402
from release_tag import draw_release, release_width  # noqa: E402
from station_kit import INK, WHITE, rounded  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "output" / "copies" / "ferry_lines_v1"
P, K = 5.0, 0.075          # one grid step in drawing units; inches per drawing unit (as the line posters)
PPU = K * 72               # points per drawing unit
TLW = 7.0                  # harbor and coast boats, points
XLW = 9.6                  # the Fast Ferry shuttle, thicker as on the Ferry Network poster
RLW = 4.4                  # river loop tracks
ZLW = 3.0                  # river zigzag boat
D2 = 0.85                  # half the gap between a river loop's two tracks, units
GRAY = "#4a4f57"
PAPER = FN.PAPER
HUB = "Langone Ferryport"
DOCK = {"stop": (8.4, 1.2), "xfer": (12.6, 2.6), "major": (15.6, 3.0), "end": (15.6, 3.6)}   # diameter, edge width (points)
FS, BFS, CFS = 11.6, 12.6, 8.4                                                              # names, bold names, captions
PW, PH, PG = 6.6, 2.9, 0.35                                                                 # pill width, height, gap
ORDER = LP.ORDER           # RL OL BL GL YL CL IL SL CR HSR F AC: one order for every pill row and the Key
TITLE = {"charles": "Charles\nRiver", "mystic": "Mystic\nRiver", "chelsea": "Chelsea\nCreek", "hw": "Harbor\nWest", "express": "Fast\nFerry",
         "eb": "East\nBoston", "hi": "Harbor\nIslands", "seaport": "Seaport", "ssi": "South\nShore", "qb": "Quincy\nBay", "fore": "Fore\nRiver",
         "nse": "North Shore\nFast Ferry", "sse": "South Shore\nFast Ferry", "isl": "Nantucket and\nMartha's Vineyard"}
HUB_CAPS = [("Main hub: every major route starts here", GRAY, "normal")]  # no walkway to North Station: Lovejoy Wharf has it (Max, November 8)
# Free rides (research/fares-changes-for-all-maps.md): the Fast Ferry shuttle (Navy Yard, Langone Ferryport, Long Wharf; not the
# North or South Shore Fast Ferry) and the zigzag boats on the three river loops. Each gets one FREE tag on its line.
FREE_KEYS = {"express", "charles", "mystic", "chelsea"}
CP_R = 1.0                 # the Charlie Points coin's radius in the Key, as on the rail line posters
TAG_PAD = 0.35             # white kept between a FREE tag's edge and the dots beside it, units
LOOP_EDGE = -0.85 + 1.91 * RLW / PPU * 5 + RLW / 2 / PPU   # where a loop Key's track samples end, past the notes column
SYM_GAP = 9.0 - LOOP_EDGE  # from a Key symbol's right edge to its text, as on the loop Keys


def tag_h(key):
    """The FREE tag's height in units: 11 points, or 1.4 times the line it sits on if that is bigger (the fares spec)."""
    return max(11.0, 1.4 * (XLW if key == "express" else ZLW)) / PPU


def put_tag(ax, x, y, h, z):
    """Draw charlie_points' FREE tag centered on (x, y); return its outline as drawn, ink edge included, for the checks.
    Measured from what the shared code draws, so a change there (the coin added inside, November 8) carries through."""
    n0 = len(ax.patches)
    pts = CP.draw_free_tag(ax, x, y, h, z=z)
    edge = ax.patches[n0].get_linewidth() / PPU / 2     # the pill is the first patch it adds
    return SPoly(pts).buffer(edge)


@lru_cache(maxsize=None)
def tag_box(h):
    """The FREE tag's outline for height h, centered on (0, 0), measured once on a scratch figure."""
    fig = plt.figure(figsize=(1, 1))
    ax = fig.add_axes([0, 0, 1, 1])
    shape = put_tag(ax, 0.0, 0.0, h, 1)
    plt.close(fig)
    return shape


def tag_w(h):
    b = tag_box(h).bounds
    return b[2] - b[0]


def tag_shape(x, y, h):
    """Where the FREE tag will sit, for choosing its spot before it is drawn."""
    from shapely.affinity import translate
    return translate(tag_box(h), x, y)


def col(k):
    return FN.col(k)


def tcol(k):
    return FN.tcol(k)


def is_fast(k):
    """Code FF: the high-speed routes and the Fast Ferry shuttle."""
    return bool(FN.R[k].get("fast")) or k == "express"


def streaks(k):
    """Drawn as streaks: the high-speed routes. The Fast Ferry shuttle keeps the Ferry Network poster's thick dots."""
    return bool(FN.R[k].get("fast"))


def code(k):
    return "FF" if is_fast(k) else "F"


def curly(s):
    return s.replace("'", "’")


def label(n):
    return curly(FN.S[n]["text"].replace("\n", " "))


def slug(k):
    return "ferry_" + FN.R[k]["name"].lower().replace("'", "").replace(" ", "_")


def G(x, r):
    return (x * P, -r * P)


@lru_cache(maxsize=None)
def width(text, fs, weight="normal"):
    return LP.width(text, fs, weight)   # TextPath extents are slow: each width is measured once


def route_docks(k):
    """Every dock a route calls at, from the Ferry Network poster's table."""
    d = FN.ROUTE_STOPS[k]
    out = []
    for part in [d.get("stops", []), d.get("link", [])] + list(d.get("banks", {}).values()) + list(d.get("branches", {}).values()):
        out += [n for n in part if n not in out]
    return out


CALLS = {k: set(route_docks(k)) for k in FN.ROUTE_STOPS}


def pill_entries(n, key):
    """(text, fill) for each transfer at dock n on route key's poster: the Ferry Network poster's pills for that dock, then every
    other ferry route that calls there, in the house order. Langone Ferryport carries a caption instead of twelve ferry pills."""
    out = [(c, LP.PILL[c]) for c in FN.S[n]["pills"]]
    if n != HUB:
        out += [(code(k), col(k)) for k in FN.R if k != key and n in CALLS.get(k, ())]
    return sorted(out, key=lambda e: ORDER.index("F" if e[0] in ("F", "FF") else e[0]))


def ferry_name(fill):
    for k in FN.R:
        if col(k) == fill:
            n = curly(FN.R[k]["name"])
            return n if is_fast(k) else f"{n} ferry"
    return "Ferry"


def ink_on(textcode, fill):
    return INK if textcode == "YL" or LP.light(fill) or (textcode in ("F", "FF") and LP.pale(fill)) else WHITE  # dark on pale ferry pills


# ---------------------------------------------------------------------------------------------------------------
# Layouts. Each leg: stops in order, the drawn path and where each stop sits (grid: column, row; rows run down the sheet),
# and the name side (l or r). Pills go across the line from the name unless the dock is in "after" (then they follow the name).

def linear(key, q=None, flip=False, ends=None):
    st = list(FN.ROUTE_STOPS[key]["stops"])
    if flip:
        st = st[::-1]
    gaps = len(st) - 1
    q = q or min(3.0, max(1.0, 20 / gaps))   # short routes get taller rows so every poster stands upright
    return dict(legs=[dict(stops=st, path=[(0, 0), (0, gaps * q)], at=[(0, i * q) for i in range(len(st))], side="l")],
                ends=ends if ends is not None else {st[-1] if not flip else st[0]})


def express_layout():
    L = linear("express", q=5.0, ends=set())
    st = L["legs"][0]["stops"]
    L["ends"] = {st[0], st[-1]}
    return L


def nse_layout():
    # North at the top (Max, November 7): Salisbury up top, down the coast to Langone Ferryport
    return linear("nse", q=1.0, flip=True, ends={"Salisbury"})


def sse_layout():
    T = list(FN.ROUTE_STOPS["sse"]["stops"])
    br = FN.ROUTE_STOPS["sse"]["branches"]
    canal = next(v for k, v in br.items() if k.startswith("Canal Pass"))
    leg = next(v for k, v in br.items() if k.startswith("Buzzards Bay"))
    bass = next(v for k, v in br.items() if k.startswith("Bass River"))
    nbv = next(v for k, v in br.items() if k.startswith("New Bedford to"))
    q = 0.85
    iw = T.index(leg[0])                        # Woods Hole: the Buzzards Bay leg runs beside the nonstop crossing to New Bedford
    inner = leg[1:-1]
    extra = {HUB: 0.8}                          # room for the hub's two caption lines
    row, r = {}, 0.0
    for n in T[:iw + 1]:
        row[n] = r
        r += q + extra.get(n, 0)
    # the leg's stops, one row apart, with room under Buzzards Bay for its Canal Pass line
    weights = [1.0 + (0.45 if n == canal[1] else 0) for n in inner[:-1]]
    nb_row = row[leg[0]] + q * (0.95 * 2 + sum(weights))
    for j, n in enumerate(T[iw + 1:]):
        row[n] = nb_row + j * q
    assert T[iw + 1] == leg[-1], "the Buzzards Bay leg should rejoin at the next trunk stop"
    B = 3.0
    legs = [dict(stops=T, path=[(0, 0), (0, row[T[-1]])], at=[(0, row[n]) for n in T], side="l")]
    y0, y1 = row[leg[0]], nb_row
    leg_rows = [y0 + q * 0.95 + q * sum(weights[:k]) for k in range(len(inner))]
    legs.append(dict(stops=leg, path=[(0, y0), (B, y0), (B, y1), (0, y1)], r=2.5,
                     at=[(0, y0)] + [(B, y) for y in leg_rows] + [(0, y1)], side="r"))
    yr = row[bass[0]]
    Bb, Wb = 2.4, 1.0
    loop_stops = bass[1:-1]
    bot = yr + q * (len(loop_stops) + 0.7)
    legs.append(dict(stops=bass, path=[(0, yr), (Bb + Wb, yr), (Bb + Wb, bot), (Bb, bot), (Bb, yr)], r=1.6,
                     at=[(0, yr)] + [(Bb + Wb, yr + q * (k + 0.85)) for k in range(len(loop_stops))] + [(0, yr)], side="r"))
    # New Bedford to Vineyard Haven: down and away at 45 degrees, clear of the trunk's pills
    yn = row[nbv[0]]
    legs.append(dict(stops=nbv, path=[(0, yn), (B, yn + B), (B, yn + B + q * len(nbv[1:]) - q * 0.4)], r=2.5,
                     at=[(0, yn)] + [(B, yn + B + q * (k + 0.6)) for k in range(len(nbv) - 1)], side="r"))
    # Canal Pass, the shortcut through the Cape Cod Canal, joins two docks far apart on the strip: a line at each end names the other
    # ("CANAL PASS" in black caps, as under the canal on the Ferry Network poster)
    beside = {canal[0]: [("CANAL PASS", INK, "bold"), (f"to {label(canal[1])}", GRAY, "normal")]}
    under = {canal[1]: [[("CANAL PASS", INK, "bold"), (f"to {label(canal[0])}", GRAY, "normal")]]}
    arrows = [(legs[2]["path"], 1.6, (Bb + Wb / 2, yr)), (legs[2]["path"], 1.6, (Bb, (yr + bot) / 2))]
    caps = [((Bb, yr - 0.62 * q), "Bass River loop: one way round", "left", tcol("sse"), 8.8, "normal"),
            ((B, y0 - 0.62 * q), "Buzzards Bay leg", "left", tcol("sse"), 8.8, "normal")]
    return dict(legs=legs, ends={T[-1], nbv[-1]}, after={leg[0], leg[-1]}, under=under, beside=beside, arrows=arrows, caps=caps,
                xfer=set(canal))   # both Canal Pass docks are junctions, as on the Ferry Network poster


def isl_layout():
    T = list(FN.ROUTE_STOPS["isl"]["stops"])     # Chatham round Nantucket to Oak Bluffs
    br = FN.ROUTE_STOPS["isl"]["branches"]
    ring = next(v for k, v in br.items() if k.startswith("Martha"))        # Oak Bluffs ... Oak Bluffs, clockwise
    wh = next(v for k, v in br.items() if k == "Woods Hole link")            # Vineyard Haven, Woods Hole
    cut = next(v for k, v in br.items() if k == "Cuttyhunk link")            # New Bedford, Cuttyhunk, Aquinnah
    whc = next(v for k, v in br.items() if k.startswith("Woods Hole to"))    # Woods Hole, Cuttyhunk
    nml = next(v for k, v in br.items() if k.startswith("Noman"))            # Aquinnah, Noman's Land
    ob = T[-1]
    n0 = len(T) - 1
    R = 6.0
    right = ring[1:ring.index("Aquinnah")]                 # Edgartown down to Chilmark
    aq, vh = "Aquinnah", "Vineyard Haven"
    left_up = ring[ring.index(vh) + 1:-1]                    # Lagoon Pond
    bot = n0 + len(right) + 1.1
    legs = [dict(stops=T, path=[(0, 0), (0, n0)], at=[(0, i) for i in range(len(T))], side="l")]
    ring_at = [(0, n0)] + [(R, n0 + 1 + k) for k in range(len(right))] + [(R, bot), (0, bot)] + \
              [(0, n0 + (bot - n0) * (k + 1) / (len(left_up) + 1)) for k in range(len(left_up))][::-1] + [(0, n0)]
    legs.append(dict(stops=ring, path=[(0, n0), (R, n0), (R, bot), (0, bot), (0, n0)], r=2.5, at=ring_at,
                     side=["l"] + ["r"] * len(right) + ["r", "l"] + ["l"] * len(left_up) + ["l"]))
    # Vineyard Haven, Woods Hole, Cuttyhunk, New Bedford straight down under the ring; Cuttyhunk back up to Aquinnah at 45 degrees
    assert wh == [vh, "Woods Hole"] and whc == ["Woods Hole", "Cuttyhunk"] and cut[0] == "New Bedford" and cut[-1] == aq
    yw, yc, yn = bot + 1.3, bot + 2.6, bot + 3.9
    legs.append(dict(stops=[vh, "Woods Hole", "Cuttyhunk", "New Bedford"], path=[(0, bot), (0, yn)], at=[(0, bot), (0, yw), (0, yc), (0, yn)], side="l"))
    legs.append(dict(stops=[aq, "Cuttyhunk"], path=[(R, bot), (R - (yc - bot), yc), (0, yc)], r=2.5, at=[(R, bot), (0, yc)], side=["r", "l"]))
    legs.append(dict(stops=nml, path=[(R, bot), (R, bot + 1.3)], at=[(R, bot), (R, bot + 1.3)], side="r"))
    arrows = [(legs[1]["path"], 2.5, (R / 2, n0)), (legs[1]["path"], 2.5, (R, n0 + 2.5)), (legs[1]["path"], 2.5, (R / 2, bot)),
              (legs[1]["path"], 2.5, (0, (n0 + bot) / 2 + 1.2))]
    caps = [((R / 2, (n0 + bot) / 2 - 0.35), "MARTHA'S VINEYARD", "center", tcol("isl"), 8.8, "bold"),
            ((R / 2, (n0 + bot) / 2 + 0.25), "Ring runs clockwise", "center", GRAY, 8.0, "normal"),
            ((1.5, (n0 - 1) / 2 + 0.5), "NANTUCKET", "left", tcol("isl"), 8.8, "bold")]   # between two stop rows, so it never reads as a stop's name
    return dict(legs=legs, ends={T[0], "New Bedford", nml[-1]}, after={ob, vh, "Cuttyhunk"}, arrows=arrows, caps=caps)


# River loops, turned so the hub link comes in at the top. Turned, never mirrored, so each track runs the same way round as on
# the Ferry Network poster: outer track clockwise, inner track counterclockwise. Rows are counted down from the loop's top.
def charles_layout():
    CB, BB = FN.CB, FN.BB   # Cambridge bank Belmont Hill to Paul Revere Park; Boston bank Nashua St to Arsenal St
    # each Cambridge dock sits half a row below its Boston partner, as on the Ferry Network poster (turned), so LOOPS' zigzag
    # (Belmont Hill, Arsenal St, Winsor, ... Paul Revere Park, Nashua St) runs one way up the river, every crossing to the next dock
    left = [("Navy Yard", 0)] + [(n, len(CB) + 1 - i) for i, n in enumerate(CB)]
    # Lovejoy Wharf, North Station's ferry link, is the Boston bank's first stop out and the loop's link up to Langone Ferryport
    # (Max, November 8; make_ferry_network ROUTE_STOPS and make_tmap agree): the top-right corner, as Navy Yard is the top-left
    right = [("Lovejoy Wharf", 0)] + [(n, 1.5 + i) for i, n in enumerate(BB)]
    return dict(loop=dict(W=3.0, left=left, right=right, top="flat", rt=(0, 0), link="Lovejoy Wharf", tip=None,
                          banks=("Cambridge bank", "Boston bank"), arrow_every=3))


def mystic_layout():
    left = [("Menino", 0.9), ("Pearl St", 2.0), ("Admirals Hill", 3.0), ("Stadium", 4.0), ("Encore", 5.0)]
    right = [("Navy Yard", 0), ("Little Mystic", 1.5), ("Medford St", 2.5), ("Alford St", 3.5), ("Assembly", 4.5)]
    return dict(loop=dict(W=3.0, left=left, right=right, top="flat", rt=(2.5, 0), link="Navy Yard", tip=None,
                          banks=("Everett and Chelsea bank", "Charlestown and Somerville bank"), arrow_every=2))


def chelsea_layout():
    left = [("Boston Bay", 2.1), ("Condor St", 3.3), ("Addison St", 4.5)]
    right = [("Quigley", 2.7), ("Chelsea St", 3.9), ("Eastern Ave", 5.1)]
    return dict(loop=dict(W=3.0, left=left, right=right, top="round", link="tip", tip="Suffolk Downs",
                          banks=("East Boston bank", "Chelsea bank"), arrow_every=1))


LAYOUTS = {"charles": charles_layout, "mystic": mystic_layout, "chelsea": chelsea_layout, "hw": lambda: linear("hw"),
           "express": express_layout, "eb": lambda: linear("eb"), "hi": lambda: linear("hi"), "seaport": lambda: linear("seaport"),
           "ssi": lambda: linear("ssi"), "qb": lambda: linear("qb"), "fore": lambda: linear("fore"), "nse": nse_layout,
           "sse": sse_layout, "isl": isl_layout}


# ---------------------------------------------------------------------------------------------------------------
class Poster:
    def __init__(self, key, ax):
        self.key, self.ax = key, ax
        self.color = col(key)
        self.texts = []      # (artist, kind): kind "label" texts are checked; "inpill" texts sit inside their own pill
        self.pills = []      # shapely boxes
        self.docks = {}      # dock name -> shapely shape
        self.halos = {}      # dock name -> the dock as it shows, white underlay and ink edge included: track dots stay clear of it
        self.bars = set()    # river docks drawn as bars across both loop tracks
        self.lines = []      # (what, shapely shape)
        self.dots = []       # centers of track dots already drawn, so overlapping legs never double a dot
        self.placed = {}     # dock name -> (x, y) in units
        self.used = []       # (fill, text) pills on this poster, for the Key
        self.majors = False
        self.tags = []       # (name, shapely shape, the line names it sits on): FREE tags on the strip
        self.keepout = []    # shapes the dotted tracks leave out, besides the docks (the FREE tag)

    def free_tag(self, x, y, hosts, z=7):
        """A FREE tag on a free line, level, centered on (x, y); registered for the checks and kept clear of dots."""
        shape = put_tag(self.ax, x, y, tag_h(self.key), z)
        self.tags.append(("FREE tag", shape, set(hosts)))
        self.keepout.append(shape.buffer(TAG_PAD))
        return shape

    # --- primitives
    def text(self, x, y, s, fs, weight="normal", ha="left", va="center", color=INK, kind="label", z=11, ls=1.1):
        t = self.ax.text(x, y, curly(s), fontsize=fs, fontweight=weight, color=color, ha=ha, va=va, zorder=z, linespacing=ls)
        self.texts.append((t, kind))
        return t

    def pill_row(self, x, y, entries, sign, z=8):
        """Pills reading left to right on the page, starting at x and running away from it (sign +1 right, -1 left)."""
        tot = len(entries) * PW + (len(entries) - 1) * PG
        x0 = x if sign > 0 else x - tot
        for t, fill in entries:
            self.ax.add_patch(FancyBboxPatch((x0, y - PH / 2), PW, PH, boxstyle=f"round,pad=0,rounding_size={PH / 2}", fc=fill, ec=PAPER, lw=1.2, zorder=z))
            self.text(x0 + PW / 2, y - 0.08, t, 8.6, "bold", "center", "center", ink_on(t, fill), kind="inpill", z=z + 0.5)
            self.pills.append(box(x0, y - PH / 2, x0 + PW, y + PH / 2))
            if (fill, t) not in self.used:
                self.used.append((fill, t))
            x0 += PW + PG

    def dock(self, n, x, y, kind, major, size=None):
        """size: draw at another kind's size (a loop's top corner needs a major-size dock to cover both tracks' corners)."""
        d, lw = DOCK[size or ("end" if kind == "end" else "major" if major else kind)]
        edge = self.color if kind == "end" else INK
        ax = self.ax
        ax.scatter([x], [y], s=(d + lw + 2.6) ** 2, color=WHITE, lw=0, zorder=8.9)   # white underlay: no track peeks past the edge
        ax.scatter([x], [y], s=d ** 2, color=WHITE, edgecolor=edge, linewidths=lw, zorder=9)
        if major:
            ax.scatter([x], [y], s=(d * 0.36) ** 2, color=INK, lw=0, zorder=9.2)
            self.majors = self.majors or n != HUB
        r = (d / 2 + lw / 2) / PPU
        self.docks[n] = Point(x, y).buffer(r)
        self.halos[n] = Point(x, y).buffer((d + lw + 2.6) / 2 / PPU)
        return r

    def hub(self, x, y):
        """Langone Ferryport: the terminal bar every route leaves from, across the line, with the major-port dot."""
        hl, t, lw = 2.6, 3.8, 3.4
        self.ax.add_patch(FancyBboxPatch((x - hl - t / 2, y - t / 2), 2 * hl + t, t, boxstyle=f"round,pad=0,rounding_size={t / 2}",
                                         fc=WHITE, ec=INK, lw=lw, zorder=9))
        self.ax.scatter([x], [y], s=7.6 ** 2, color=INK, lw=0, zorder=9.2)
        e = lw / 2 / PPU
        self.docks[HUB] = box(x - hl - t / 2 - e, y - t / 2 - e, x + hl + t / 2 + e, y + t / 2 + e)
        self.halos[HUB] = self.docks[HUB]
        return hl + t / 2 + e

    def bar(self, n, a, b, thick, lw, z=9):
        """A river dock: a white bar with round ends across both tracks, from a to b (horizontal or vertical)."""
        (x0, y0), (x1, y1) = a, b
        if abs(y1 - y0) < 1e-6:
            xa, xb = sorted((x0, x1))
            bb = (xa - thick / 2, y0 - thick / 2, xb + thick / 2, y0 + thick / 2)
        else:
            ya, yb = sorted((y0, y1))
            bb = (x0 - thick / 2, ya - thick / 2, x0 + thick / 2, yb + thick / 2)
        self.ax.add_patch(FancyBboxPatch((bb[0], bb[1]), bb[2] - bb[0], bb[3] - bb[1], boxstyle=f"round,pad=0,rounding_size={thick / 2}",
                                         fc=WHITE, ec=INK, lw=lw, zorder=z))
        self.docks[n] = box(*bb)
        self.halos[n] = box(*bb).buffer(lw / 2 / PPU, join_style=2)
        self.bars.add(n)

    def casing(self, xy, lw, what, z=3):
        self.ax.plot(*np.asarray(xy).T, color=WHITE, lw=lw + 2.6, solid_capstyle="round", solid_joinstyle="round", zorder=z)
        self.lines.append((what, LineString(xy).buffer((lw + 2.6) / PPU / 2)))

    def dot_run(self, xy, cuts, lw, z=4.1):
        """Round dots about the Ferry Network poster's step apart, spread evenly between waypoints and kept off the docks
        (as make_ferry_network.dot_run), skipping any dot another leg already put there."""
        ln = LineString(xy)
        step = 1.91 * lw / PPU
        rd = lw / 2 / PPU + 0.15
        tree = STRtree(list(self.halos.values()) + self.keepout)   # clear of the dock as it shows: no dot cut by a white underlay

        def clear(t):
            return not len(tree.query(ln.interpolate(t).buffer(rd), predicate="intersects"))

        pos = sorted({0.0, ln.length} | {ln.project(Point(c)) for c in cuts})
        pts = []
        for a, b in zip(pos, pos[1:]):
            if b - a < 1e-6:
                continue
            a1, b1 = a, b
            while a1 < b and not clear(a1):
                a1 += 0.05
            while b1 > a and not clear(b1):
                b1 -= 0.05
            if a1 >= b1:
                if clear((a + b) / 2):
                    pts.append((a + b) / 2)
                continue
            gaps = round((b1 - a1) / step)
            if gaps and (b1 - a1) / gaps < 0.9 * step:
                gaps -= 1
            pts += [(a1 + b1) / 2] if gaps == 0 else list(np.linspace(a1, b1, gaps + 1))
        xs = []
        for t in pts:
            p = ln.interpolate(t)
            if all(np.hypot(p.x - u, p.y - v) > 0.7 * step for u, v in self.dots):
                xs.append((p.x, p.y))
                self.dots.append((p.x, p.y))
        if xs:
            xs = np.array(xs)
            self.ax.scatter(xs[:, 0], xs[:, 1], s=lw ** 2, color=self.color, lw=0, zorder=z)

    def ring_dots(self, ring, cuts, lw=RLW, z=4.1):
        """A river loop track: dots evenly round the closed ring at the Ferry Network poster's step (as ferry_track's dashes),
        leaving out any dot inside a cut, (start, end) along the ring, where a direction arrow sits, and any dot a round corner
        dock's white underlay would cut into a crescent: the track stops short of the ring, as a strip's dots stop short of a dock.
        Bars are left as they were: the track runs on under them, both tracks at once."""
        n = max(1, round(ring.length / (1.91 * lw / PPU)))
        tree = STRtree([h for d, h in self.halos.items() if d not in self.bars])
        rd = lw / 2 / PPU + 0.15
        pts = []
        for s in np.arange(n) * ring.length / n:
            if any((s - lo) % ring.length <= hi - lo for lo, hi in cuts):
                continue
            p = ring.interpolate(s)
            if len(tree.query(p.buffer(rd), predicate="intersects")):
                continue
            pts.append((p.x, p.y))
        if pts:
            pts = np.array(pts)
            self.ax.scatter(pts[:, 0], pts[:, 1], s=lw ** 2, color=self.color, lw=0, zorder=z)

    def name(self, n, x, y, side, bold, major, gap, under=()):
        """Stop name beside its dock; returns the far end of the name, for pills that follow it."""
        fs, weight = (BFS, "bold") if bold else (FS, "bold" if major else "normal")
        s = curly(label(n).upper() if bold else label(n))
        sg = 1 if side == "r" else -1
        self.text(x + sg * gap, y - 0.05, s, fs, weight, "left" if sg > 0 else "right", "center")
        for i, line in enumerate(under):
            self.runs(x + sg * gap, y - 2.75 - i * 1.85, line if isinstance(line, list) else [line], sg)
        return x + sg * (gap + width(s, fs, weight))

    def runs(self, x, y, parts, sign, fs=CFS):
        """One caption line in several styles, (text, color, weight) parts, starting at x and reading away from it."""
        sp = 0.3 * fs / PPU
        ws = [width(curly(t), fs, wt) for t, _, wt in parts]
        x0 = x if sign > 0 else x - sum(ws) - sp * (len(parts) - 1)
        for (t, color, wt), w in zip(parts, ws):
            self.text(x0, y, t, fs, wt, "left", "center", color)
            x0 += w + sp

    # --- the strip
    def draw_legs(self, L):
        ax, key = self.ax, self.key
        legs, ends, after = L["legs"], L.get("ends", set()), L.get("after", set())
        under = dict(L.get("under", {}))
        under.setdefault(HUB, HUB_CAPS)
        meta, touch = {}, {}
        for leg in legs:
            sides = leg["side"] if isinstance(leg["side"], list) else [leg["side"]] * len(leg["stops"])
            for n, at, sd in zip(leg["stops"], leg["at"], sides):
                touch[n] = touch.get(n, 0) + 1
                if n not in meta:
                    meta[n] = dict(at=G(*at), side=sd)
        for n, m in meta.items():
            pe = pill_entries(n, key)
            m["pills"] = pe
            m["major"] = n in FN.MAJOR
            m["kind"] = "hub" if n == HUB else "end" if n in ends else "xfer" if (pe or touch[n] > 1 or n in L.get("xfer", ())) else "stop"
        # docks first: the dotted tracks leave out any dot that would sit under one
        for n, m in meta.items():
            x, y = m["at"]
            m["r"] = self.hub(x, y) if m["kind"] == "hub" else self.dock(n, x, y, m["kind"], m["major"])
            self.placed[n] = (x, y)
        lw = XLW if key == "express" else TLW
        for i, leg in enumerate(legs):
            pts = [G(*p) for p in leg["path"]]
            xy = rounded(pts, leg.get("r", 2.5), n=40) if len(pts) > 2 else np.array(pts, float)
            self.casing(xy, lw, f"leg {i}")
        tagged = []
        if key in FREE_KEYS:
            # a FREE tag, level, on the first leg at the middle of the stretch between two docks nearest the leg's mid-length.
            # Where the mid-length is a dock (the Fast Ferry shuttle: Langone Ferryport), both stretches beside it get one, so
            # neither half of the free ride reads as paid (the fares file allows a second where one would be lost)
            leg = legs[0]
            pts = [G(*p) for p in leg["path"]]
            ln = LineString(rounded(pts, leg.get("r", 2.5), n=40) if len(pts) > 2 else np.array(pts, float))
            s = sorted(ln.project(Point(G(*a))) for a in leg["at"])
            mids = [((a + b) / 2, k) for k, (a, b) in enumerate(zip(s, s[1:])) if b - a > 1e-6]
            near = min(round(abs(e[0] - ln.length / 2), 3) for e in mids)
            for m, _ in [e for e in mids if round(abs(e[0] - ln.length / 2), 3) == near]:
                p = ln.interpolate(m)
                self.free_tag(p.x, p.y, {"leg 0"})
                tagged.append((p.x, p.y))
        for i, leg in enumerate(legs):
            pts = [G(*p) for p in leg["path"]]
            xy = rounded(pts, leg.get("r", 2.5), n=40) if len(pts) > 2 else np.array(pts, float)
            if streaks(key):
                FN.ferry_track(ax, xy, self.color, lw=lw, z=4, casing=False, fast=True)
            else:
                self.dot_run(xy, pts + [G(*a) for a in leg["at"]] + (tagged if i == 0 else []), lw)
        for path, r, near in L.get("arrows", []):
            FN.track_arrow(ax, path, r, near, tcol(key), size=1.7, lw=lw, z=6)
        for n, m in meta.items():
            x, y = m["at"]
            bold = m["kind"] in ("end", "hub")
            gap = m["r"] + (1.6 if bold else 1.3)
            far = self.name(n, x, y, m["side"], bold, m["major"], gap, under.get(n, ()))
            sg = 1 if m["side"] == "r" else -1
            if n in L.get("beside", {}):     # a caption across the line from the name, where a dock has no pills
                self.runs(x - sg * (m["r"] + 1.3), y - 0.05, L["beside"][n], -sg, fs=9.0)
            if not m["pills"]:
                continue
            if n in after:      # the pills follow the name, where a line leaves the dock on the far side
                self.pill_row(far + sg * 1.2, y, m["pills"], sg)
            else:               # across the line from the name, clear of the dock
                self.pill_row(x - sg * (m["r"] + 0.7), y, m["pills"], -sg)
        for (gx, gr), s, ha, color, fs, wt in L.get("caps", []):
            x, y = G(gx, gr)
            self.text(x, y, s, fs, wt, ha, "center", color)
        return meta

    def draw_loop(self, spec):
        """A river loop: two tracks one each way round (outer clockwise, inner counterclockwise), a white bar across both at every
        dock, the zigzag boat bank to bank, and the link up to Langone Ferryport."""
        ax, key, c = self.ax, self.key, self.color
        W = spec["W"] * P
        xL, xR = 0.0, W
        LO = 13.0                                   # the loop's top sits this far under the hub
        yt = -LO
        rows = [r for _, r in spec["left"] + spec["right"]]
        yb = yt - (max(rows) + 0.35) * P - W / 2   # bottom vertex: a round end
        if spec["top"] == "round":
            radii = [W / 2, W / 2, W / 2, W / 2]
        else:
            radii = [spec["rt"][0], W / 2, W / 2, spec["rt"][1]]
        cl = FN.round_closed([(xL, yt), (xL, yb), (xR, yb), (xR, yt)], radii, n=24)
        poly = orient(SPoly(cl), sign=-1.0)
        outer = orient(poly.buffer(D2, join_style=1), sign=-1.0).exterior
        inner = orient(poly.buffer(-D2, join_style=1), sign=-1.0).exterior
        water = poly.buffer(-D2 - 0.9, join_style=1)
        ax.add_patch(Polygon(np.array(water.exterior.coords), fc=FN.WATER, ec="none", zorder=1.6))
        for ring in (outer, inner):
            self.casing(np.array(ring.coords), RLW, "loop")
        # (the tracks' dots are drawn after the arrows, so each arrow's own track leaves a clean gap for it)
        # the link up to the hub
        tipx = W / 2
        if spec["link"] == "tip":    # into the round top: stop on the outer track, so the link's dots never bunch with the loop's
            lx, ly = tipx, yt + D2 + 0.9
        else:
            lx = xL if spec["link"] in dict(spec["left"]) else xR
            ly = yt
        hy = 0.0
        link = np.array([(lx, hy), (lx, ly)])
        self.casing(link, RLW, "link")
        hub_r = self.hub(lx, hy)
        self.placed[HUB] = (lx, hy)
        # docks
        hl, thick = D2 + 1.25, 1.6
        attach, info, half = {}, [], {}
        for side, stops in (("l", spec["left"]), ("r", spec["right"])):
            x = xL if side == "l" else xR
            for n, r in stops:
                y = yt - r * P
                pe = pill_entries(n, key)
                major = n in FN.MAJOR
                if r == 0 and spec["top"] == "flat":    # a top corner: a round dock
                    rr = self.dock(n, x, y, "xfer", major, size="major")
                    gap = rr + 1.3
                    half[n] = rr
                else:
                    self.bar(n, (x - hl, y), (x + hl, y), thick, 2.0 if pe else 1.2)
                    attach[n] = (x + hl - 0.35, y) if side == "l" else (x - hl + 0.35, y)
                    gap = hl + thick / 2 + 1.3
                    half[n] = thick / 2 + (2.0 if pe else 1.2) / 2 / PPU
                self.placed[n] = (x, y)
                info.append((n, x, y, side, gap, pe, major))
        if spec.get("tip"):
            n = spec["tip"]
            self.bar(n, (tipx, yb - hl), (tipx, yb + hl), thick, 2.0)
            attach[n] = (tipx, yb + hl - 0.35)
            self.placed[n] = (tipx, yb)
            info.append((n, tipx, yb, "b", hl + thick / 2, pill_entries(n, key), n in FN.MAJOR))
        # the link's dots, then the zigzag across the water. Into a round top the link's last dot stops one normal gap above the
        # outer track's dots (its own dot gap), so the two never read as touching
        if spec["link"] == "tip":
            dots_to = yt + D2 + RLW / 2 / PPU + 0.91 * (RLW + 0.6) / PPU + (RLW + 0.6) / 2 / PPU
            run = np.array([(lx, hy), (lx, dots_to)])
        else:
            run = link
        self.dot_run(run, [tuple(run[0]), tuple(run[1])], RLW + 0.6)
        zig = next(L["zig"] for L in FN.LOOPS if L["key"] == key)
        zz = np.array([attach[n] for n in zig if n in attach])
        ax.plot(*zz.T, color=WHITE, lw=ZLW + 2.2, solid_capstyle="round", solid_joinstyle="round", zorder=5)
        segs = [LineString([a, b]) for a, b in zip(zz[:-1], zz[1:])]
        for i, sg in enumerate(segs):   # one entry per crossing, so the FREE tag can sit on one and be checked against the rest
            self.lines.append((f"zigzag {i}", sg.buffer((ZLW + 2.2) / PPU / 2)))
        pieces = [zz]
        if key in FREE_KEYS:
            # the zigzag boat rides free: one FREE tag, level, on a crossing in the middle half of the zigzag, at the spot there with
            # the most white round it (other crossings, docks, tracks), the nearer the mid-length the better when the room is
            # about equal; the dots stop short of it on both sides (no half dots under the tag)
            cum = np.concatenate([[0], np.cumsum([sg.length for sg in segs])])
            best = None
            for i, sg in enumerate(segs):
                others = [ln for w, ln in self.lines if w != f"zigzag {i}"] + list(self.docks.values())
                for f in np.linspace(0.4, 0.6, 9):
                    off = abs(cum[i] + f * sg.length - cum[-1] / 2)
                    if off > cum[-1] / 4:
                        continue
                    p = sg.interpolate(f, normalized=True)
                    room = min(tag_shape(p.x, p.y, tag_h(key)).distance(o) for o in others)
                    score = (round(room / 0.1), -round(off, 2))
                    if best is None or score > best[0]:
                        best = (score, i, p, room)
            _, i, p, room = best
            if room < 0.3:
                print(f"  {key}: the FREE tag has only {room:.2f} units of room")
            shape = self.free_tag(p.x, p.y, {f"zigzag {i}"})
            gap = ZLW / 2 / PPU + TAG_PAD
            cut = segs[i].intersection(shape)
            lo, hi = sorted(segs[i].project(Point(q)) for q in cut.coords)
            c1, c2 = segs[i].interpolate(lo - gap), segs[i].interpolate(hi + gap)
            # both pieces start at the tag, so a dot sits the same short gap from it on each side
            pieces = [np.vstack([[c1.x, c1.y], zz[i::-1]]), np.vstack([[c2.x, c2.y], zz[i + 1:]])]
        for pc in pieces:
            ax.plot(*pc.T, color=c, lw=ZLW, ls=(0, (0.01, 1.7)), dash_capstyle="round", zorder=5.1)
        # direction arrows between docks, alternating outer and inner track: docks taken top to bottom down each column, an arrow
        # only in a gap with room for all of it, centered there; its own track leaves out the dots under it (no half dots)
        size = 1.5
        tip, back = 1.2 * size, 0.7 * size
        margin = 1.6 / PPU + RLW / 2 / PPU + 0.1     # the arrow's white edge, a dot's radius, a hair
        cuts = {"o": [], "i": []}
        k = 0
        for side, stops in (("l", spec["left"]), ("r", spec["right"])):
            x = xL if side == "l" else xR
            col_docks = sorted(((yt - r * P, half[n]) for n, r in stops), reverse=True)
            gaps = [(ya - ha, yb_ + hb) for (ya, ha), (yb_, hb) in zip(col_docks, col_docks[1:]) if (ya - ha) - (yb_ + hb) >= tip + back + 0.15]
            for i, (top, low) in enumerate(gaps):
                if i % spec["arrow_every"]:
                    continue
                which = "o" if k % 2 == 0 else "i"
                k += 1
                ring, sgn = (outer, 1) if which == "o" else (inner, -1)
                p, v = FN.ring_dir(ring, (x, (top + low) / 2))
                d = sgn * v
                a0 = p - d * (tip - back) / 2
                FN.arrow(ax, a0[0], a0[1], np.degrees(np.arctan2(d[1], d[0])), tcol(key), size, 6.5)
                s = ring.project(Point(a0))
                lo, hi = (s - back, s + tip) if sgn > 0 else (s - tip, s + back)
                cuts[which].append((lo - margin, hi + margin))
        self.ring_dots(outer, cuts["o"])
        self.ring_dots(inner, cuts["i"])
        # names and pills (pills follow the name: inside the loop is water)
        self.name(HUB, lx, hy, "l", True, True, hub_r + 1.6, HUB_CAPS)
        self.pill_row(lx + hub_r + 0.7, hy, pill_entries(HUB, key), 1)
        for n, x, y, side, gap, pe, major in info:
            if side == "b":
                s = label(n)
                self.text(x, y - gap - 0.9, s, FS, "bold" if major else "normal", "center", "top")
                if pe:
                    self.pill_row(x + width(s, FS) / 2 + 1.2, y - gap - 0.9 - 1.15, pe, 1)
                continue
            far = self.name(n, x, y, side, False, major, gap)
            if pe:
                sg = 1 if side == "r" else -1
                self.pill_row(far + sg * 1.2, y, pe, sg)
        lt, rt_ = spec["banks"]
        self.text(xL - 2.2, yb + 3.2, lt, CFS, "normal", "right", "center", GRAY)
        self.text(xR + 2.2, yb + 3.2, rt_, CFS, "normal", "left", "center", GRAY)

    # --- extents of everything drawn so far, in drawing units
    def extents(self, fig):
        rend = fig.canvas.get_renderer()
        inv = self.ax.transData.inverted()
        bounds = []
        for t, _ in self.texts:
            bb = t.get_window_extent(rend)
            (a, b), (c, d) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
            bounds.append((a, b, c, d))
        for s in list(self.docks.values()) + self.pills + [s for _, s in self.lines]:
            bounds.append(s.bounds)
        b = np.array(bounds)
        return b[:, 0].min(), b[:, 1].min(), b[:, 2].max(), b[:, 3].max()


# ---------------------------------------------------------------------------------------------------------------
NOTE_X = -3.3 + 0.85    # the notes column starts where the next pill column would (as on the line posters)


def key_layout(po):
    """Key rows: the pills on this poster in the house order, with names; split into balanced columns of up to 4. Then the notes."""
    entries = []
    t_used = sorted({t for f, t in po.used if t not in ("F", "FF")}, key=ORDER.index)
    f_used = [(f, t) for f, t in po.used if t in ("F", "FF")]
    f_used.sort(key=lambda e: [col(k) for k in FN.R].index(e[0]))
    for c in ORDER:
        if c in t_used:
            entries.append((LP.PILL[c], c, LP.NAMES[c]))
        if c == "F":
            entries += [(f, t, ferry_name(f)) for f, t in f_used]
    cols = []
    if entries:
        ncol = -(-len(entries) // 4)
        i = 0
        for k in range(ncol):
            rows = entries[i:i + len(entries) // ncol + (k < len(entries) % ncol)]
            i += len(rows)
            cols.append((max(27, 3.3 + 4.8 + max(width(curly(t), 8.8) for _, _, t in rows) + 5), rows))
    # the Charlie Points row under the driverless row, as on the rail line posters; the FREE row with it where a ride is free
    notes = [("icon", "Every dock is accessible"), ("text", "Driverless, 24 hours a day"), ("cp", CP.KEY_TEXT)]
    if po.key in FREE_KEYS:
        notes.append(("free", CP.FREE_TEXT))
    notes.append(("text", "Pods on demand at every dock"))
    if is_fast(po.key) or po.majors:  # one wording everywhere: it explains the symbol without implying the boat skips the other docks
        notes.append(("major", "Major port: fast ferries stop here"))
    if po.key == "express":
        notes.append(("text", "Nonstop between the three, at all times"))
    if FN.ROUTE_STOPS[po.key].get("loop"):
        notes += [("outer", "Outer track: boats run clockwise"), ("inner", "Inner track: boats run counterclockwise"),
                  ("zig", "Zigzag boat: bank to bank at every dock")]
    kinds = {k for k, _ in notes}
    # text the same step past every symbol; a Key with a wide symbol (track samples, the FREE tag) sets its symbols flush right
    lead = 9.0 if kinds & {"outer", "inner", "zig"} else -0.85 + tag_w(tag_h(po.key)) + SYM_GAP if "free" in kinds \
        else 4.3 if "major" in kinds else 2.4
    return entries, cols, notes, lead


def draw_key(po, x0, x1, ky, cols, notes, lead):
    ax = po.ax
    ax.plot([x0 + 4, x1 - 4], [ky + 3.4, ky + 3.4], color=INK, lw=0.8, zorder=12)
    cx = x0 + 8
    for pitch, rows in cols:
        for r, (fill, c, t) in enumerate(rows):
            cy = ky - 1.6 - r * 4.4
            ax.add_patch(FancyBboxPatch((cx - 3.3, cy - 1.45), 6.6, 2.9, boxstyle="round,pad=0,rounding_size=1.45", fc=fill, ec="none", zorder=12))
            po.pills.append(box(cx - 3.3, cy - 1.45, cx + 3.3, cy + 1.45))
            po.text(cx, cy - 0.08, c, 8.6, "bold", "center", "center", ink_on(c, fill), kind="inpill", z=13)
            po.text(cx + 4.8, cy - 0.05, t, 8.8, "normal", "left", "center", z=13)
        cx += pitch
    kx = cx + NOTE_X
    grey = "#cfd2d8"
    xa = kx - 0.85
    xs = xa + 1.91 * RLW / PPU * np.arange(6)     # a track sample's six dots, at the river tracks' step
    xr = xs[-1]
    # the symbols' right edge, SYM_GAP short of the text: on loop posters the samples end here (xr + a dot's radius) and the icon,
    # coin, tag and target are set flush with them; the Fast Ferry Key, with its wide FREE tag, does the same
    edge = kx + lead - SYM_GAP
    loopkey = lead > 5
    for i, (st, t) in enumerate(notes):
        cy = ky - 1.6 - i * 4.4
        if st == "icon":
            M.icon(ax, edge - 0.85 if loopkey else kx, cy, z=12)
        elif st == "cp":    # the Charlie Points coin where the icon sits
            cx_ = edge - CP_R if loopkey else kx
            CP.draw_cp(ax, cx_, cy, CP_R, z=12)
            po.pills.append(box(cx_ - CP_R, cy - CP_R, cx_ + CP_R, cy + CP_R))
        elif st == "free":  # the FREE tag at the size it has on the line
            h = tag_h(po.key)
            po.pills.append(put_tag(ax, edge - tag_w(h) / 2, cy, h, 12))
        elif st == "major":
            d, lw = DOCK["major"]
            mx = edge - (d / 2 + lw / 2) / PPU if loopkey else kx + 0.9
            ax.scatter([mx], [cy], s=d ** 2, color=WHITE, edgecolor=INK, linewidths=lw, zorder=12)
            ax.scatter([mx], [cy], s=(d * 0.36) ** 2, color=INK, lw=0, zorder=12.2)
        elif st in ("outer", "inner"):
            sg = 1 if st == "outer" else -1
            for off, on in ((0.85, st == "outer"), (-0.85, st == "inner")):
                ax.plot([xa, xr], [cy + off] * 2, color=WHITE, lw=RLW + 2.6, solid_capstyle="round", zorder=12)
                keep = np.delete(xs, [2, 3]) if on else xs     # the arrow's own track leaves out the two dots under it
                ax.scatter(keep, [cy + off] * len(keep), s=RLW ** 2, color=po.color if on else grey, lw=0, zorder=12.1)
            # centered in the gap: the arrowhead runs 1.2 x size ahead of its point and 0.7 x size behind
            FN.arrow(ax, (xs[1] + xs[4]) / 2 - sg * 0.25 * 1.3, cy + 0.85 * sg, 0 if st == "outer" else 180, tcol(po.key), 1.3, 12.5)
        elif st == "zig":
            zz = np.column_stack([np.linspace(xa, xr, 5), cy + np.array([1.2, -1.2, 1.2, -1.2, 1.2])])
            ax.plot(*zz.T, color=WHITE, lw=ZLW + 2.2, solid_capstyle="round", solid_joinstyle="round", zorder=12)
            ax.plot(*zz.T, color=po.color, lw=ZLW, ls=(0, (0.01, 1.7)), dash_capstyle="round", zorder=12.1)
        po.text(kx + lead, cy - 0.05, t, 8.8, "normal", "left", "center", z=13)


def header_t(ax, x, y, r):
    """The header's T: NERTA's multicolor three-layer T (the 12 NERTA_COLORS; Max, November 8) inside the black-ringed white
    roundel, drawn here so the ferry posters don't depend on make_line_poster's roundel."""
    ax.add_patch(Circle((x, y), r, fc=WHITE, ec=INK, lw=3.2, zorder=12))
    draw_t(ax, x, y, r, M.NERTA_COLORS, z=13)


def draw_header(po, x0, x1, y1, title, codetxt):
    ax, color = po.ax, po.color
    hy = y1 - 11
    header_t(ax, x0 + 10, hy, 6.4)
    # the NERTA mark in the logo's colors; the code pill below keeps the route's own color
    nb = draw_nerta(ax, x0 + 10, hy - (6.4 + 3.2 / 5.4 / 2) - 0.8, 2 * (6.4 + 3.2 / 5.4 / 2), "B", colors=M.NERTA_COLORS)
    ax.add_patch(FancyBboxPatch((x0 + 20, hy - 6), 28, 12, boxstyle="round,pad=0,rounding_size=6", fc=color, ec="none", zorder=12))
    po.pills.append(box(x0 + 20, hy - 6, x0 + 48, hy + 6))
    po.text(x0 + 34, hy - 0.4, codetxt, 38, "bold", "center", "center", ink_on(codetxt, color), kind="inpill", z=13)
    po.text(x0 + 52, hy, title, 27, "bold", "left", "center", z=13, ls=1.1)
    if M.WEB:   # nerta.fun: name under NERTA, @mapzimus faint top right (as the line posters)
        po.text(x0 + 10, nb - 1.0, "Maxwell Howe", 8.4, "normal", "center", "top", z=13)
        po.text(x1 - 5, hy, "@mapzimus", 9.6, "bold", "right", "center", "#b9b9b4", z=13)
        return hy
    before = len(ax.texts)
    left, _, _ = draw_release(ax, x1 - 5, hy, size=9.6, ppu=PPU, ink=INK)   # disclaimer, credit, hashtag, Day 8 (every map posted November 8)
    po.texts += [(t, "release") for t in ax.texts[before:]]
    room = left - (x0 + 52 + max(width(curly(t), 27, "bold") for t in title.split("\n")))
    if room < 4:
        print(f"  release block crowds the title: {room:.1f} units")
    return hy


# ---------------------------------------------------------------------------------------------------------------
def text_shape(t, rend, inv):
    bb = t.get_window_extent(rend)
    (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
    return box(x0, y0 + 0.35, x1, y1 - 0.35)


def check(fig, po, lims):
    """Overlap check with the figure's own renderer: text against text, pills, docks and tracks; pills against pills, docks and
    tracks; docks against docks; and everything inside the sheet."""
    rend = fig.canvas.get_renderer()
    inv = po.ax.transData.inverted()
    texts = [(t.get_text().replace("\n", " ")[:30], text_shape(t, rend, inv), k) for t, k in po.texts if k != "inpill"]
    bad = []
    for i, (a, sa, ka) in enumerate(texts):
        for b, sb, kb in texts[i + 1:]:
            if ka == kb == "release":   # release_tag sets its paragraph word by word: a run's box includes its trailing space
                continue
            if sa.intersection(sb).area > 0.05:
                bad.append(f"text/text: {a} | {b}")
        for what, ln in po.lines:
            if sa.intersection(ln).area > 0.05:
                bad.append(f"text/track: {a} | {what}")
        for n, d in po.docks.items():
            if sa.intersection(d).area > 0.05:
                bad.append(f"text/dock: {a} | {n}")
        for pb in po.pills:
            if sa.intersection(pb).area > 0.05:
                bad.append(f"text/pill: {a} | pill at {[round(v) for v in pb.bounds]}")
        x0, y0, x1, y1 = sa.bounds
        if x0 < lims[0] + 2 or x1 > lims[1] - 2 or y0 < lims[2] + 2 or y1 > lims[3] - 2:
            bad.append(f"text off the sheet: {a}")
    for k, pb in enumerate(po.pills):
        for what, ln in po.lines:
            if pb.intersection(ln).area > 0.05:
                bad.append(f"pill/track: pill at {[round(v) for v in pb.bounds]} | {what}")
        for n, d in po.docks.items():
            if pb.intersection(d).area > 0.05:
                bad.append(f"pill/dock: pill at {[round(v) for v in pb.bounds]} | {n}")
        for pc in po.pills[k + 1:]:
            if pb.intersection(pc).area > 0.05:
                bad.append(f"pill/pill: {[round(v) for v in pb.bounds]}")
    names = list(po.docks)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if po.docks[a].intersects(po.docks[b]):
                bad.append(f"dock/dock: {a} | {b}")
    for tn, ts, hosts in po.tags:   # a FREE tag sits on its own line and touches nothing else
        for a, sa, _ in texts:
            if sa.intersection(ts).area > 0.05:
                bad.append(f"tag/text: {tn} | {a}")
        for what, ln in po.lines:
            if what not in hosts and ts.intersection(ln).area > 0.05:
                bad.append(f"tag/track: {tn} | {what}")
        for n, d in po.docks.items():
            if ts.intersection(d).area > 0.05:
                bad.append(f"tag/dock: {tn} | {n}")
        for pb in po.pills:
            if ts.intersection(pb).area > 0.05:
                bad.append(f"tag/pill: {tn} | pill at {[round(v) for v in pb.bounds]}")
        if not (lims[0] + 2 < ts.bounds[0] and ts.bounds[2] < lims[1] - 2):
            bad.append(f"tag off the sheet: {tn}")
    return bad


def main(key, outdir, dpi, draft):
    L = LAYOUTS[key]()
    title, codetxt = curly(TITLE[key]), code(key)
    fig = plt.figure(figsize=(600 * K, 700 * K))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-300, 300)
    ax.set_ylim(-650, 50)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.patch.set_facecolor(PAPER)
    po = Poster(key, ax)
    if "loop" in L:
        po.draw_loop(L["loop"])
    else:
        po.draw_legs(L)
    missing = [n for n in route_docks(key) if n not in po.placed]
    extra = [n for n in po.placed if n not in CALLS[key]]
    if missing or extra:
        raise SystemExit(f"{key}: docks missing from the poster {missing}, docks not on the route {extra}")
    sx0, sy0, sx1, sy1 = po.extents(fig)
    entries, cols, notes, lead = key_layout(po)
    need = max(122, 8 + sum(w for w, _ in cols) + NOTE_X + lead + max(width(curly(t), 8.8) for _, t in notes) + 6,
               52 + max(width(t, 27, "bold") for t in title.split("\n")) + 6 + release_width(9.6, PPU) + 5)
    x0, x1 = sx0 - 6, sx1 + 6
    if x1 - x0 < need:
        mid = (x0 + x1) / 2
        x0, x1 = mid - need / 2, mid + need / 2
    y1 = sy1 + 29
    ky = sy0 - 8.8
    nrows = max([len(rows) for _, rows in cols] + [len(notes)])
    y0 = ky - 1.6 - 4.4 * (nrows - 1) - 8.2
    fig.set_size_inches((x1 - x0) * K, (y1 - y0) * K)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    draw_header(po, x0, x1, y1, title, codetxt)
    draw_key(po, x0, x1, ky, cols, notes, lead)
    bad = check(fig, po, (x0, x1, y0, y1))
    for b in bad:
        print("  overlap:", b)
    print(f"{key}: {len(po.placed)} docks, {len(bad)} overlaps, sheet {x1 - x0:.0f} x {y1 - y0:.0f} units")
    plt.rcParams["pdf.fonttype"] = 42
    png, pdf = outdir / f"{slug(key)}.png", outdir / f"{slug(key)}.pdf"
    if not draft and "--replace" not in sys.argv:
        for f in (png, pdf):
            if f.exists():
                raise SystemExit(f"refusing to overwrite {f}")
    outdir.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=dpi, facecolor=PAPER)
    if not draft or "--pdf" in sys.argv:
        fig.savefig(pdf, facecolor=PAPER)
    plt.close(fig)
    return len(po.placed), bad


if __name__ == "__main__":
    args = sys.argv[1:]
    draft = "--draft" in args
    outdir = Path(args[args.index("--draft") + 1]) if draft else OUT
    dpi = int(args[args.index("--dpi") + 1]) if "--dpi" in args else (150 if draft else 600)
    skip = {a for i, a in enumerate(args) if i and args[i - 1] in ("--draft", "--dpi")}
    keys = [a for a in args if not a.startswith("--") and a not in skip] or list(LAYOUTS)
    if not draft and "--replace" not in args and OUT.exists() and any(OUT.iterdir()):
        raise SystemExit(f"{OUT} already has files; renders never overwrite. Use --draft DIR for trial renders.")
    for k in keys:
        main(k, outdir, dpi, draft)
