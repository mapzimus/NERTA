"""Information boxes for the NERTA Commuter Rail Network station display, a portrait poster that hangs in stations.

The sheet layout (make_rail_network.py) calls these: lines_panel, key_panel, transfers_panel, how_panel and notice_panel.
Each draws its own rounded panel behind its content and returns the panel's bounds (x0, y0, x1, y1) in drawing units, with
(x0, y1) the top-left corner. The height always fits the content; so does the width of the Transfers box.

Units, colors and drawing helpers come from make_rail_poster (RP), so every box matches the rail posters: 1 unit is
0.075 in (RP.K), 5.4 points (RP.PPU). Station symbols are drawn at exactly the sizes RP.draw_station uses. The look follows
the finished ferry display (make_ferry_network.py: notice, key_routes, key_symbols, key_transfers and the two explainers):
box titles 11.0 pt bold capitals, small gray group headers, rows 4.4 units apart, short paragraphs, and a PASSENGER NOTICE
box with a dark title bar. All text is level and upright.

Every text goes through RP.txt, and every line sample, symbol and pill is registered in RP.REG, so RP.check covers the boxes
along with the network. Draw on axes set up as RP.main sets them up (RP.K inches a unit, equal aspect): wrapped text is
measured with the figure's renderer. transfers_panel takes `used`, the (code, station) pairs RP.main builds from
RP.t_codes() and RP.STATIONS, so call RP.build() and RP.stations() first.

Reads make_rail_poster, make_line_poster and make_tmap; changes none of them.
Test render (scratch only, never into output/): python rail_network_panels.py OUT.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Polygon  # noqa: E402
from shapely.geometry import LineString, Point, box  # noqa: E402
from shapely.geometry import Polygon as SPoly  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import make_rail_poster as RP  # noqa: E402  (read only: units, helpers, line colors, symbols, ferry looks, the checks)
import make_line_poster as LP  # noqa: E402  (read only: T pill colors, names and order; the parking sign)
import make_tmap as M  # noqa: E402  (read only: the accessible-station icon)
from charlie_points import KEY_TEXT as CP_TEXT, draw_cp  # noqa: E402  (the shared Charlie Points coin and Key line, November 8)
from station_kit import INK, WHITE, rounded  # noqa: E402

PPU, LW, PITCH = RP.PPU, RP.LW, RP.PITCH
PURPLE = RP.PURPLE

PAD = 3.5            # panel edge to its content, as on the ferry display
TOP = 3.2            # panel top to the top of the box title
TITLE_FS = 11.0      # box titles, bold capitals
HEAD_FS, HEAD_C = 8.0, "#4a4f57"   # group headers, as in the ferry display's ROUTES box
FS = 8.8             # row text
ROW = 4.4            # row to row
FIRST = 12.2         # panel top to the first row of a box without group headers (ferry: the title's top, then 9.0)
FIRST_HEAD = 11.6    # panel top to the first group header (ferry: the title's top, then 8.4)
HEAD_ROW = 4.2       # group header to its first row
GROUP_GAP = 5.4      # last row of a group to the next header
BOTTOM = 4.6         # last row to the panel bottom
SAMPLE = 9.0         # length of a line sample
TXT_GAP = 3.0        # end of a sample to its words
Z = 11.0             # samples and symbols, above the panel (z=1)

CAP = LW * 1.32 / 2 / PPU      # half the thickness of a station capsule, units
HUB = LW * 1.85 / 2 / PPU      # half the thickness of a main hub capsule


# ---------------------------------------------------------------------------------------------------------------
# Small helpers
def _title(ax, x0, y1, s):
    RP.txt(ax, x0 + PAD, y1 - TOP, s, TITLE_FS, "bold", "left", "top")


def _header(ax, x, y, s):
    RP.txt(ax, x, y, s, HEAD_FS, "bold", "left", "center", color=HEAD_C)


def _units(ax, px):
    """Pixels on this figure to drawing units."""
    return px * 72.0 / ax.figure.dpi / PPU


def _h(ax, t):
    """A drawn text's height, in units."""
    return _units(ax, t.get_window_extent(ax.figure.canvas.get_renderer()).height)


def _w(ax, t):
    """A drawn text's width, in units."""
    return _units(ax, t.get_window_extent(ax.figure.canvas.get_renderer()).width)


def _line_step(ax, fs, ls, weight="normal"):
    """Baseline to baseline in wrapped text, in units, measured: it depends on the font."""
    r = ax.figure.canvas.get_renderer()
    one = ax.text(0, 0, "Ag", fontsize=fs, fontweight=weight, linespacing=ls, family="Arial")
    two = ax.text(0, 0, "Ag\nAg", fontsize=fs, fontweight=weight, linespacing=ls, family="Arial")
    step = _units(ax, two.get_window_extent(r).height - one.get_window_extent(r).height)
    one.remove()
    two.remove()
    return step


def _wrap(s, fs, max_w, weight="normal"):
    """Break s into lines no wider than max_w units, by measured width."""
    out = []
    for para in s.split("\n"):
        cur = ""
        for word in para.split():
            t = f"{cur} {word}" if cur else word
            if cur and RP.width(t, fs, weight) > max_w:
                out.append(cur)
                cur = word
            else:
                cur = t
        out.append(cur)
    return "\n".join(out)


def _wrap_even(s, fs, max_w, weight="normal"):
    """As _wrap, then narrowed as far as it goes without adding a line, so the lines come out even and no word sits alone."""
    n = _wrap(s, fs, max_w, weight).count("\n")
    lo, hi = max_w * 0.5, max_w
    for _ in range(14):
        mid = (lo + hi) / 2
        if _wrap(s, fs, mid, weight).count("\n") == n:
            hi = mid
        else:
            lo = mid
    return _wrap(s, fs, hi, weight)


def _sample(ax, xy, key, z=Z):
    """A piece of line, drawn as RP draws the line `key`, and registered for the checks."""
    xy = np.asarray(xy, float)
    RP.stroke_line(ax, xy, key, z=z)
    RP.REG["line"].append((f"panel {key}", LineString(xy).buffer(LW / PPU / 2, cap_style=2)))
    return xy


def _stop(ax, q, kind, owner, z=Z + 2.0):
    """A station on one line, exactly as RP.draw_station draws it. kind: "stop", "xfer" (with a transfer) or "end"."""
    if kind == "end":
        ax.scatter(*q, s=(LW * 1.5) ** 2, color=WHITE, edgecolor=PURPLE, lw=2.2, zorder=z)
        r = (LW * 1.5 / 2 + 1.1) / PPU
    elif kind == "xfer":
        ax.scatter(*q, s=(LW * 1.2) ** 2, color=WHITE, edgecolor=INK, lw=1.7, zorder=z)
        r = (LW * 1.2 / 2 + 0.85) / PPU
    else:
        ax.scatter(*q, s=(LW * 0.78) ** 2, color=WHITE, edgecolor=INK, lw=0.8, zorder=z)
        r = (LW * 0.78 / 2 + 0.4) / PPU
    RP.REG["dot"].append((owner, Point(q).buffer(r)))
    return r


def _capsule(ax, a, b, owner, big=False, z=Z + 1.0):
    """A station on more than one line (big: a main hub), exactly as RP.draw_station draws it. Drawn at Z + 0.2, between
    the commuter lines and the high-speed lines, it is a station the high-speed trains pass without stopping."""
    lw = LW * (1.85 if big else 1.32)
    ax.plot([a[0], b[0]], [a[1], b[1]], color=INK, lw=lw, solid_capstyle="round", zorder=z)
    ax.plot([a[0], b[0]], [a[1], b[1]], color=WHITE, lw=lw * 0.62, solid_capstyle="round", zorder=z + 0.01)
    RP.REG["dot"].append((owner, LineString([a, b]).buffer(lw / PPU / 2)))


def _head(ax, a, b, half=1.6, z=Z + 0.6):
    """The purple arrowhead RP.head puts on a line that runs on, after the segment a-b. Returns the tip."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    v = (b - a) / np.hypot(*(b - a))
    n = np.array([-v[1], v[0]])
    tip = b + v * 2.4
    tri = [tuple(tip), tuple(b - n * half), tuple(b + n * half)]
    ax.add_patch(Polygon(tri, closed=True, fc=PURPLE, ec="none", zorder=z))
    RP.REG["line"].append(("arrowhead", SPoly(tri)))
    return tip


def _sign(owner, x, y, a, kind="dot"):
    """Register a small square sign for the checks: the accessible icon as a dot, the parking P as a pill (as
    RP.park_sign registers it)."""
    sq = box(x - a, y - a, x + a, y + a)
    RP.REG[kind].append((owner, sq) if kind == "dot" else sq)


# ---------------------------------------------------------------------------------------------------------------
# 1. Lines
COMMUTER = [
    ("NORTH", [("fit", "Wachusett, on to Greenfield and North Adams; branch to Marlborough"), ("low", "Lowell"), ("hav", "Haverhill"),
               ("nbp", "Newburyport and Rockport, forking at Beverly")]),
    ("WEST AND SOUTH", [("wor", "Worcester"), ("fra", "Forge Park/495; Foxboro to Mansfield"),
                        ("pro", "Wickford Junction; Stoughton branch to Taunton")]),
    ("SOUTH SHORE", [("fr", "New Bedford and Fall River Depot; on to Cape Cod"), ("kin", "Plymouth"),
                     ("grb", "Greenbush")]),
    ("CROSSTOWN", [("pea", "Marblehead to Lawrence, crosstown")]),
]
HIGH_SPEED = ["To Concord NH and Montreal, via Lowell", "To Bangor, via Haverhill and Portland",
              "To Albany and Chicago, via Worcester and Springfield",
              "To New York, Philadelphia and Washington, via Providence and New Haven"]


def lines_panel(ax, x0, y1, w):
    """LINES: each commuter line in its group (a line sample, the line's ringed pill, where it goes), then the four
    high-speed lines (a gold-core sample, where they go). Words that would pass the panel's edge wrap."""
    x1 = x0 + w
    _title(ax, x0, y1, "LINES")
    sx0, sx1 = x0 + PAD, x0 + PAD + SAMPLE
    px = sx1 + 2.0                                                          # the pills start here
    dx = px + max(RP.lp_w(k) for _, rows in COMMUTER for k, _ in rows) + 2.4  # where-it-goes column, past the widest pill
    step = _line_step(ax, FS, 1.15)
    groups = COMMUTER + [("HIGH-SPEED RAIL", [("hmon", t) for t in HIGH_SPEED])]
    y, prev = y1 - FIRST_HEAD, 0.0
    for g, (head, rows) in enumerate(groups):
        if g:
            y -= GROUP_GAP + prev
        _header(ax, x0 + PAD, y, head)
        for i, (k, words) in enumerate(rows):
            hsr = RP.LINES[k].get("hsr", False)
            tx = px if hsr else dx              # high-speed rows have no pill, so their words follow the sample
            t = _wrap(words, FS, x1 - PAD - tx - 0.6)
            extra = t.count("\n") * step / 2    # a wrapped row grows evenly above and below its line
            y -= (HEAD_ROW if i == 0 else ROW + prev) + extra
            _sample(ax, [(sx0, y), (sx1, y)], k)
            if not hsr:
                RP.line_pill(ax, px, y, k)
            RP.txt(ax, tx, y - 0.05, t, FS, ls=1.15)
            prev = extra
    y0 = y - BOTTOM - prev
    RP.panel(ax, x0, y0, x1, y1)
    return (x0, y0, x1, y1)


# ---------------------------------------------------------------------------------------------------------------
# 2. Key
KEY_ROWS = [("stop", "Station"), ("xfer", "Station with a transfer"), ("multi", "Station on more than one line"),
            ("pass", "High-speed trains pass without stopping"), ("end", "End of the line"), ("hub", "Main hub"),
            ("arrow", "Line continues"), ("acc", "Every station is accessible"), ("park", LP.PARKING_NOTE), ("cp", CP_TEXT)]
# how far each symbol reaches above and below its row's center, units (a row of text reaches about 1.0)
REACH = {"stop": 1.0, "xfer": 1.0, "multi": PITCH / 2 + CAP, "pass": PITCH + CAP, "end": (LW * 1.5 / 2 + 1.1) / PPU,
         "hub": PITCH + HUB, "arrow": 1.6, "acc": 1.0, "park": 1.0, "cp": 1.0}


def _key_symbol(ax, kind, sx0, sx1, y):
    cx = (sx0 + sx1) / 2
    own = f"key {kind}"
    if kind in ("stop", "xfer"):
        _sample(ax, [(sx0, y), (sx1, y)], "low")
        _stop(ax, (cx, y), kind, own)
    elif kind == "multi":              # a capsule across two lines, like Readville
        _sample(ax, [(sx0, y + PITCH / 2), (sx1, y + PITCH / 2)], "fra")
        _sample(ax, [(sx0, y - PITCH / 2), (sx1, y - PITCH / 2)], "pro")
        _capsule(ax, (cx, y + PITCH / 2), (cx, y - PITCH / 2), own)
    elif kind == "pass":               # as at Sullivan Sq: a platform dot on each commuter line, joined by a thin link the gold line runs over
        _sample(ax, [(sx0, y + PITCH), (sx1, y + PITCH)], "low")
        _sample(ax, [(sx0, y), (sx1, y)], "hmon")
        _sample(ax, [(sx0, y - PITCH), (sx1, y - PITCH)], "hav")
        ax.plot([cx, cx], [y + PITCH, y - PITCH], color=INK, lw=1.7, solid_capstyle="round", zorder=Z + 0.2)
        _stop(ax, (cx, y + PITCH), "xfer", own)
        _stop(ax, (cx, y - PITCH), "xfer", own)
    elif kind == "end":                # the line stops at its ring
        _sample(ax, [(sx0, y), (cx, y)], "low")
        _stop(ax, (cx, y), "end", own)
    elif kind == "hub":
        for dy, k in ((PITCH, "hav"), (0.0, "wor"), (-PITCH, "nbp")):
            _sample(ax, [(sx0, y + dy), (sx1, y + dy)], k)
        _capsule(ax, (cx, y + PITCH), (cx, y - PITCH), own, big=True)
    elif kind == "arrow":
        _sample(ax, [(sx0, y), (sx1 - 2.4, y)], "low")
        _head(ax, (sx0, y), (sx1 - 2.4, y))
    elif kind == "acc":
        M.icon(ax, cx, y, z=Z + 1.0)
        _sign(own, cx, y, 0.85)
    elif kind == "park":
        LP.park(ax, cx, y, z=12)
        _sign(own, cx, y, LP.PARK_A, "pill")
    elif kind == "cp":                 # the shared Charlie Points coin (November 8)
        draw_cp(ax, cx, y, 1.0, z=Z + 1.0)
        _sign(own, cx, y, 1.0, "pill")


def key_panel(ax, x0, y1, w):
    """KEY: the station symbols, drawn exactly as on the network, then the accessible and parking signs. Two columns when w
    has room for them, on one even grid so rows side by side share a line; otherwise one column, with the same space
    between every pair of symbols."""
    x1 = x0 + w
    _title(ax, x0, y1, "KEY")
    need = [SAMPLE + TXT_GAP + RP.width(t, FS) + 0.5 for _, t in KEY_ROWS]
    n1 = (len(KEY_ROWS) + 1) // 2
    if PAD + max(need[:n1]) + 8.0 + max(need[n1:]) + PAD <= w:
        x2 = x0 + max(w / 2, PAD + max(need[:n1]) + 8.0)
        cols = [(x0 + PAD, KEY_ROWS[:n1]), (x2, KEY_ROWS[n1:])]
    else:
        cols = [(x0 + PAD, KEY_ROWS)]
    bands = max(len(rows) for _, rows in cols)
    reach = [max(max(REACH[rows[i][0]], 1.0) for _, rows in cols if i < len(rows)) for i in range(bands)]
    steps = [max(ROW, reach[i - 1] + reach[i] + 1.5) for i in range(1, bands)]
    if len(cols) > 1:
        steps = [max(steps)] * len(steps)
    y = y1 - FIRST - (reach[0] - 1.0)
    for i in range(bands):
        if i:
            y -= steps[i - 1]
        for cx0, rows in cols:
            if i < len(rows):
                kind, t = rows[i]
                _key_symbol(ax, kind, cx0, cx0 + SAMPLE, y)
                RP.txt(ax, cx0 + SAMPLE + TXT_GAP, y - 0.05, t, FS)
    y0 = y - reach[-1] - (BOTTOM - 1.0)
    RP.panel(ax, x0, y0, x1, y1)
    return (x0, y0, x1, y1)


# ---------------------------------------------------------------------------------------------------------------
# 3. Transfers
VIA_NOTE = ("F via Lovejoy Wharf, Rowes Wharf or",            # all three F-via docks (audit round 2), on two lines so
            "Dorchester Ave: the dock is a short walk away")  # the box keeps its width
VIA_LINE = 2.9       # line to line inside the note


def transfers_panel(ax, x0, y1, used):
    """TRANSFERS: one row per T line used, in house order; one row per ferry route on the map, named as RP.ferry_look names
    it; the fast-ferry ring; then what "F via" means. used: (code, station) pairs, as RP.main builds them. The width fits."""
    boats, fast_boats, via = [], [], False
    for c, station in used:
        if c == "F":
            fill, fg, name, fast = RP.ferry_look(station)
            via |= RP.code_text(c, station) != "F"
            if (fill, fg, name) not in boats:
                boats.append((fill, fg, name))
            if fast and (fill, fg, name) not in fast_boats:
                fast_boats.append((fill, fg, name))
    order = [v[1] for v in RP.FERRY_ROUTES.values()]
    boats.sort(key=lambda b: order.index(b[0]) if b[0] in order else 99)
    fast_boats.sort(key=boats.index)
    rows = []   # (pill text, fill, text color, name, fast-ferry ring)
    for c in sorted({c for c, _ in used}, key=LP.ORDER.index):
        if c == "F":
            rows += [("F", f, fg, n, False) for f, fg, n in boats]
            if fast_boats:   # the ringed pill in the colors of a route whose fast ferries do stop on this map
                rows.append(("F", fast_boats[0][0], fast_boats[0][1], "Fast ferries stop here (major port)", True))
        else:
            rows.append((c, LP.PILL[c], INK if c == "YL" else WHITE, LP.NAMES[c], False))

    _title(ax, x0, y1, "TRANSFERS")
    cx = x0 + PAD + 3.3 + RP.EXPRESS_PAD / 2    # pill centers: the wider fast-ferry pill starts at the margin
    tx = cx + 4.8
    right = x0 + PAD + RP.width("TRANSFERS", TITLE_FS, "bold")
    y = y1 - FIRST
    for i, (c, fill, fg, name, fast) in enumerate(rows):
        if i:
            y -= ROW
        RP.pill(ax, cx - 3.3 - (RP.EXPRESS_PAD / 2 if fast else 0), y, c, fill, fg, fs=8.6, z=12, express=fast)
        right = max(right, tx + _w(ax, RP.txt(ax, tx, y - 0.05, name, FS)))
    if via:   # a footnote under the pills: "F via Rowes Wharf" and the like
        for k, ln in enumerate(VIA_NOTE):
            y -= VIA_LINE if k else ROW
            right = max(right, x0 + PAD + _w(ax, RP.txt(ax, x0 + PAD, y - 0.05, ln, FS)))
    x1, y0 = right + PAD, y - BOTTOM
    RP.panel(ax, x0, y0, x1, y1)
    return (x0, y0, x1, y1)


# ---------------------------------------------------------------------------------------------------------------
# 4. How the trains run
HOW = [("Through the BIGGER Dig",
        "Every line but the Peabody line runs through North Station, Boston Central and South Station, under Atlantic Ave. "
        "Change trains at any of the three."),
       ("High-speed rail",
        "High-speed trains run on their own tracks beside the commuter lines. Near Boston they stop only at North Station, Boston Central, South "
        "Station, Back Bay, West Station and Route 128; farther out at Lowell, Haverhill, Worcester and Providence."),
       ("Crosstown",
        "The Peabody line runs crosstown, Marblehead to Lawrence, and never downtown. Change at South Salem for the "
        "Newburyport/Rockport Line and at Lawrence for the Haverhill Line.")]
SEC_FS = 10.2        # section names, as the ferry explainer's "Clockwise loop boat"
BODY_FS = 9.4        # paragraphs
TINY = 8.0           # names in the diagrams
DIAGRAM_H = 22.0     # every diagram sits in a band this tall, so the paragraphs line up
GUTTER = 8.0         # between sections; a thin rule runs down its middle


def _dig(ax, bx0, bx1, by0, by1):
    """Three lines, each with its own rim color, through the three hub capsules: North Station on top."""
    names = ["North Station", "Boston Central", "South Station"]
    reach = PITCH + HUB                                   # trunk center to a capsule's end
    comp = 2 * reach + 1.4 + max(RP.width(n, TINY) for n in names)
    tx = (bx0 + bx1) / 2 - comp / 2 + reach
    yc = (by0 + by1) / 2
    for dx, k in ((-PITCH, "hav"), (0.0, "wor"), (PITCH, "low")):
        _sample(ax, [(tx + dx, by1 - 0.5), (tx + dx, by0 + 0.5)], k)
    for n, y in zip(names, (yc + 6.5, yc, yc - 6.5)):
        _capsule(ax, (tx - PITCH, y), (tx + PITCH, y), f"how {n}", big=True)
        RP.txt(ax, tx + reach + 1.4, y - 0.05, n, TINY)


def _high_speed(ax, bx0, bx1, by0, by1):
    """A commuter line beside a high-speed line. Where a capsule spans both, high-speed trains stop; where the station is on
    the commuter line alone, the gold line runs past it and high-speed trains pass."""
    words = ["stops", "passes"]
    comp = PITCH + 2 * CAP + 1.4 + max(RP.width(s, TINY) for s in words)
    xl = (bx0 + bx1) / 2 - comp / 2 + CAP                 # the commuter line; the high-speed line runs PITCH to its right
    xr = xl + PITCH
    yc = (by0 + by1) / 2
    _sample(ax, [(xl, by1 - 0.5), (xl, by0 + 0.5)], "pro")
    _sample(ax, [(xr, by1 - 0.5), (xr, by0 + 0.5)], "hnyc")
    _capsule(ax, (xl, yc + 5.0), (xr, yc + 5.0), "how stops", z=Z + 1.0)
    RP.txt(ax, xr + CAP + 1.4, yc + 5.0 - 0.05, "stops", TINY)
    _stop(ax, (xl, yc - 5.0), "xfer", "how passes")
    RP.txt(ax, xr + CAP + 1.4, yc - 5.0 - 0.05, "passes", TINY)


def _crosstown(ax, bx0, bx1, by0, by1):
    """The Peabody line (teal rim) up from Marblehead, across the Newburyport/Rockport line (pink rim) at South Salem and on
    toward Lawrence."""
    xc = (bx0 + bx1) / 2 - 5.0                            # the crossing, left of center: the names go to its right
    yc = (by0 + by1) / 2 + 1.0
    half = min((bx1 - bx0) / 2 - 2.0, 20.0)
    _sample(ax, [(xc - half + 5.0, yc), (xc + half + 5.0, yc)], "nbp")
    mh = (xc + 4.0, by0 + 1.6)                             # Marblehead, the end of the line
    pts = [mh, (xc, mh[1] + 4.0), (xc, by1 - 3.4)]
    xy = rounded(pts, RP.R, n=16)
    _sample(ax, xy, "pea")
    tip = _head(ax, xy[-2], xy[-1])
    _stop(ax, (xc, yc), "xfer", "how South Salem")   # as the map draws it: one transfer dot where the lines cross
    r = _stop(ax, mh, "end", "how Marblehead")
    RP.txt(ax, xc + PITCH / 2 + CAP + 0.8, yc + LW / PPU / 2 + 1.0, "South Salem", TINY, va="bottom")
    RP.txt(ax, mh[0] + r + 1.2, mh[1] - 0.05, "Marblehead", TINY)
    RP.txt(ax, xc + 1.6 + 1.0, tip[1] - 1.2, "to Lawrence", TINY)


def how_panel(ax, x0, y1, w):
    """HOW THE TRAINS RUN: three short sections side by side, each a small diagram over a short paragraph, like the
    ferry display's river and fast-ferry explainers."""
    x1 = x0 + w
    _title(ax, x0, y1, "HOW THE TRAINS RUN")
    sw = (w - 2 * PAD - 2 * GUTTER) / 3
    hy = y1 - FIRST_HEAD                 # section names
    dtop = hy - 3.4
    dbot = dtop - DIAGRAM_H
    ptop = dbot - 2.8                    # paragraphs
    low = ptop
    for i, ((head, body), draw) in enumerate(zip(HOW, (_dig, _high_speed, _crosstown))):
        sx = x0 + PAD + i * (sw + GUTTER)
        RP.txt(ax, sx, hy, head, SEC_FS, "bold", "left", "center")
        draw(ax, sx, sx + sw, dbot, dtop)
        t = RP.txt(ax, sx, ptop, _wrap_even(body, BODY_FS, sw - 0.6), BODY_FS, "normal", "left", "top", ls=1.25)
        low = min(low, ptop - _h(ax, t))
    y0 = low - 3.6
    for i in (1, 2):
        gx = x0 + PAD + i * (sw + GUTTER) - GUTTER / 2
        ax.plot([gx, gx], [y0 + 4.0, hy + 2.0], color=RP.PANEL_EC, lw=1.0, zorder=1.1)
        RP.REG["line"].append(("panel rule", LineString([(gx, y0 + 4.0), (gx, hy + 2.0)]).buffer(0.1)))
    RP.panel(ax, x0, y0, x1, y1)
    return (x0, y0, x1, y1)


# ---------------------------------------------------------------------------------------------------------------
# 5. Passenger notice
NOTICE = [("Trains run 24 hours a day, 7 days a week.", "bold"),
          ("Every train is a driverless maglev.", "normal"),
          ("Every station is accessible.", "normal"),
          ("Extra trains run for TD Garden and Foxboro stadium events.", "normal"),
          ("Pods on demand at every station.", "bold")]


def notice_panel(ax, x0, y1, w):
    """PASSENGER NOTICE, set like the ferry display's: a white box, a dark title bar, short paragraphs at 10.4 pt."""
    x1 = x0 + w
    txt_fs, ls = 10.4, 1.25
    y = y1 - 10.6
    for p, wt in NOTICE:
        t = _wrap(p, txt_fs, w - 2 * PAD - 0.6, wt)
        RP.txt(ax, x0 + PAD, y, t, txt_fs, wt, "left", "top", ls=ls)
        y -= (t.count("\n") + 1) * txt_fs * ls / PPU + 2.2
    y0 = y - 1.2
    ax.add_patch(FancyBboxPatch((x0, y0), w, y1 - y0, boxstyle="round,pad=0,rounding_size=2", fc=WHITE, ec=INK, lw=1.4, zorder=1.2))
    ax.add_patch(FancyBboxPatch((x0, y1 - 6.6), w, 6.6, boxstyle="round,pad=0,rounding_size=2", fc=INK, ec=INK, lw=1.4, zorder=1.3))
    ax.add_patch(FancyBboxPatch((x0, y1 - 6.6), w, 3.0, boxstyle="square,pad=0", fc=INK, ec="none", zorder=1.35))
    RP.txt(ax, x0 + PAD, y1 - 3.3, "PASSENGER NOTICE", 11.4, "bold", "left", "center", color=WHITE)
    RP.REG["pill"].append(box(x0, y0, x1, y1).exterior.buffer(0.01))     # its edge, as RP.panel registers a panel's
    RP.REG["pill"].append(box(x0 + 0.1, y1 - 6.6, x1 - 0.1, y1 - 0.1))     # the title bar: only its own title may sit on it
    return (x0, y0, x1, y1)


# ---------------------------------------------------------------------------------------------------------------
def _test(out):
    """All five boxes on a scratch sheet set up as RP.main sets one up, then RP.check."""
    import matplotlib.pyplot as plt
    RP.build()
    RP.stations()
    codes = RP.t_codes()
    used = [(c, s["name"]) for s in RP.STATIONS for c in codes.get(s["name"], [])]
    X0, X1, Y0, Y1 = -20.0, 420.0, -260.0, 20.0     # working sheet; trimmed to the boxes below
    fig = plt.figure(figsize=((X1 - X0) * RP.K, (Y1 - Y0) * RP.K))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.patch.set_facecolor(RP.PAPER)
    gap = 8.0
    lb = lines_panel(ax, 0.0, 0.0, 150.0)
    kb = key_panel(ax, 0.0, lb[1] - gap, 150.0)
    tb = transfers_panel(ax, lb[2] + gap, 0.0, used)
    nb = notice_panel(ax, tb[2] + gap, 0.0, 95.0)
    hb = how_panel(ax, lb[2] + gap, min(tb[1], nb[1]) - gap, 200.0)
    boxes = {"lines (w=150)": lb, "key (w=150)": kb, "transfers": tb, "notice (w=95)": nb, "how (w=200)": hb}
    X0, X1 = min(b[0] for b in boxes.values()) - 6, max(b[2] for b in boxes.values()) + 6
    Y0, Y1 = min(b[1] for b in boxes.values()) - 6, max(b[3] for b in boxes.values()) + 6
    fig.set_size_inches((X1 - X0) * RP.K, (Y1 - Y0) * RP.K)
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    for n, b in boxes.items():
        print(f"{n}: {b[2] - b[0]:.1f} x {b[3] - b[1]:.1f} units, top-left ({b[0]:.1f}, {b[3]:.1f})")
    bad = RP.check(fig, ax)
    for b in bad:
        print("  ", b)
    print(f"{len(bad)} flags")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, facecolor=RP.PAPER)
    print("written", out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python rail_network_panels.py OUT.png")
    _test(sys.argv[1])
