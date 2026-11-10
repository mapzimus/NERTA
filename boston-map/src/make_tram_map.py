"""The tram map: NERTA's trams drawn over a faded copy of the main map (Max, November 7 and 8).

The main map's water, coast, lines and stations sit faded behind; the trams lead in hot pink. The layout comes from
tram_merge.Layout: real routes bent into the main map's layout, routed on a 45-degree lattice, side by side where they
share a street, beside a NERTA line rather than on it. Stops, names and routes are read from the tram data at render time.

python make_tram_map.py [--web] [--ppu 6.0] [--crops]
Writes boston-map/output/copies/tram_map_vN.png (300 dpi) and tram_map_vN.pdf under the next free N; never overwrites.
--web leaves out the release block (nerta.fun). --crops also saves zoomed crops tram_map_vN_crop_<area>.png.
"""
import argparse
import math
import os
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon  # noqa: E402
from matplotlib.textpath import TextPath  # noqa: E402
from matplotlib.transforms import Bbox  # noqa: E402
from shapely.geometry import LineString, Point, box  # noqa: E402
from shapely.ops import nearest_points, unary_union  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import make_tmap as M  # noqa: E402  (read only: never call M.main())
import make_line_poster as LP  # noqa: E402  (roundel only)
import tram_merge as TM  # noqa: E402
from nerta_mark import draw_nerta, draw_t  # noqa: E402
from release_tag import draw_release, release_width  # noqa: E402
from charlie_points import FREE_TEXT, KEY_TEXT, draw_cp, draw_free_tag  # noqa: E402
from version_tag import draw_version  # noqa: E402
from station_kit import INK, WHITE, rounded, smooth_open  # noqa: E402

DAY = Path(__file__).resolve().parents[1]
OUT = DAY / "output" / "copies"
PINK = TM.TRAM
# Stops left off THIS map only (round 4, the coordinator's call after Max said "finish up"). Two stretches have more stops
# than fit between stations that sit close together on the main map: the tram stays straight, so only the stops a rider
# would know best are kept, as many as fit at full circle size. Every stop stays in tram_draft.json and on the tram posters,
# and the Key says so. Route id -> stop names dropped.
MAP_DROP = {
    # Norwood to Walpole, 4.9 units apart on the main map: East Walpole (the village center) and the Walpole end stay
    "34E": ["East Hoyle St", "Lenox St", "Weld Ave", "Short St", "Rockhill St", "Polley Ln", "Pilgrim Way", "Alexandra Way",
            "Kendall St", "Diamond St"],
    # Swampscott to South Salem, 6.4 units apart: Vinnin Sq (the square) stays
    "455": ["Boulder Way", "Ryan Pl", "Intervale Rd", "Pickman Rd", "Sumner Rd", "Forest Ave"],
    # Newmarket to Uphams Corner, 2.1 units apart: no room for a stop between the two stations
    "16": ["Edward Everett Sq"],
}
# Rounds 7 and 8, at 7.5 points per unit (round 8: the round-3 audit's center rule): found by trial renders (each round left off one stop per clash, never a route end or a stop
# two routes share, until every name sat right beside its own stop). Most are on tight 45-degree runs, where a level name
# would otherwise sit level with the next stop.
MAP_DROP_FIT = {
    "15": ["Adams St", "Magazine St", "West Cottage St"],
    "23": ["Whiting St", "Waumbeck St", "Woodbine St"],
    "34": ["Cowing St", "Birchwood St", "Granfield Ave", "Beech St", "Carol Circle"],
    "38": ["Allenwood St", "Sedgwick St", "Goldsmith St", "Whitcomb Ave"],
    "60": ["Henry St", "Catlin Rd", "Duffley Ct"],
    "64": ["Riverview Rd", "Tremont St"],
    "70": ["Palmer St", "Hillside Rd", "Louise St"],
    "75": ["Fountain Ter"],
    "78": ["Staunton Rd", "Eliot Rd"],
    "95": ["Middlesex Ave"],
    "100": ["Mystic Valley Pkwy"],
    "101": ["South Medford"],
    "106": ["Valley St"],
    "110": ["Cambridge St"],
    "111": ["Chester Ave", "Jones Ave"],
    "116": ["Chester Ave", "Eleanor St", "Stockton St"],
    "215": ["Milton St", "Guilford Rd", "Emerson Rd", "Guild St", "Stedman St", "Cross St"],
    "216": ["Newcomb St", "Southern Artery", "Roach St", "Figurehead Ln"],
    "220": ["Evans St", "Blackstone Rd", "Lincoln St", "Bradley Woods Dr", "Planters Field Ln", "Burditt Ave", "Sumner St", "Bulow Rd", "Daley Rd"],
    "222": ["Evans St", "Curtis St", "Weymouth Heights", "James Rd", "Fairmount Ave", "Lorraine St", "Moreland Rd", "Sumner St", "Maple St"],
    "225": ["Blanchard Rd", "Dartmouth St", "Arnold St", "West Howard St", "Dewey Rd", "Audubon Ave", "Allen St", "Brookside Rd", "King Ave"],
    "240": ["Brook Rd", "Clifton Rd", "Pleasant St", "North Randolph", "Fairmount St", "Frederickson Dr", "Columbine Rd", "Milton Center", "Hallen Ave", "Woodland Pkwy", "Acorn Dr", "Hilltop St", "Chickatawbut Rd"],
    "34E": ["Cowing St", "Birchwood St", "Providence Hwy", "Ellis Ave", "Achorn St", "Granfield Ave", "Beech St", "Carol Circle", "Richards St", "East Walpole"],
    "455": ["Commercial St", "Cedar St", "Chatham St", "Vinnin Sq"],
    "712": ["Teragram St", "Golden Dr", "Winthrop Beach", "Veterans Rd", "Paine St"],
}
for _rid, _names in MAP_DROP_FIT.items():
    MAP_DROP[_rid] = MAP_DROP.get(_rid, []) + [n for n in _names if n not in MAP_DROP.get(_rid, [])]
# Commuter rail transfers the main map doesn't mark with a stop of their own yet (Max, November 8: Waltham is a Red Line
# through stop with a commuter rail transfer). Station -> the commuter rail path (index in M.CR_PATHS) it links to.
CR_TRANSFER = {"Waltham": 1}   # the Fitchburg Line
FREE_H = 11.0 / 1.6   # the FREE tag's height as a share of the tram line width: about 11 pt, so FREE reads at normal view (round 6)
FREE_ROUTES = ["23"]   # free rides (Max, November 8): research/fares-changes-for-all-maps.md
SC = 1.0   # main() sets 6 / ppu: the label spacings below were tuned at 6 points per unit and scale with the type
FAR = 1.9   # drawing units at 6 pt per unit: the most paper between a name and its own stop's cross
NEAR_MARGIN = 0.35   # a name sits at least this much nearer its own stop than any other stop or station dot (drawing units)


def clearly_own(b, c_own, r_own, c_other, r_other, m=None):
    """A name's box reads as its own stop's when it is clearly nearer it, measured both from the box's nearest edge and
    from the box's middle (round-2 audit: both, not either). For a name beside its stop the edge test alone applies, as the
    audit measures it: a long name's middle lies well out from any stop."""
    m = NEAR_MARGIN * SC if m is None else m

    def edge(c, r):
        return Point(c).distance(b) - r

    def mid(c, r):
        q = b.centroid
        return math.hypot(q.x - c[0], q.y - c[1]) - r
    ok_edge = edge(c_own, r_own) + m <= edge(c_other, r_other)
    x0, _, x1, _ = b.bounds
    return ok_edge and mid(c_own, r_own) + 0.5 * m <= mid(c_other, r_other)   # round-3 audit: the center rule for every name


def row_clash(b, c_own, c_other, band=None, slack=None):
    """Round-2 audit: a name reads with whatever stop sits level with it. Another stop inside the name's height band and
    nearer the name than its own stop means a stranger reading across pairs them."""
    band = 0.15 * SC if band is None else band
    slack = 0.2 * SC if slack is None else slack
    x0, y0, x1, y1 = b.bounds
    if not (y0 - band <= c_other[1] <= y1 + band):
        return False
    return Point(c_other).distance(b) < Point(c_own).distance(b) + slack


def col_clash(b, c_own, c_other, band=None, slack=None):
    """Round-4 audit (Duffley Ct): another stop straight above or below a name, nearer it than its own stop, pairs with it."""
    band = 0.15 * SC if band is None else band
    slack = 0.2 * SC if slack is None else slack
    x0, y0, x1, y1 = b.bounds
    if not (x0 - band <= c_other[0] <= x1 + band):
        return False
    return Point(c_other).distance(b) < Point(c_own).distance(b) + slack


DROP_NOTE = "Some stops are left off this map; every stop is on the tram posters."


def map_routes(log=print):
    """The routes as this map draws them: the tram data, less MAP_DROP (and, while searching for what fits, the stop names
    listed in the JSON file named by NERTA_TRAM_DROP_TRY)."""
    import json as _json
    import os as _os
    routes = TM.load_routes(log)
    trial = set()
    if _os.environ.get("NERTA_TRAM_DROP_TRY"):
        trial = set(_json.loads(Path(_os.environ["NERTA_TRAM_DROP_TRY"]).read_text(encoding="utf-8")))
    out, dropped = [], []
    for r in routes:
        names = set(MAP_DROP.get(str(r["id"]), [])) | trial
        if not names:
            out.append(r)
            continue
        r = dict(r)
        keep = []
        for st_ in r["stops"]:
            if st_["name"] in names and not st_.get("nerta"):
                dropped.append(f"{r['id']}: {st_['name']}")
            else:
                keep.append(st_)
        r["stops"] = keep
        out.append(r)
    for rid, names in MAP_DROP.items():
        for n in names:
            if f"{rid}: {n}" not in dropped:
                log(f"  MAP_DROP: {rid} has no stop named {n} (data changed?)")
    return out, dropped
PAPER = M.PAPER
GRAY = "#6e6e74"            # NERTA station names: quiet
FS_TRAM, FS_NERTA = 6.2, 6.2
ARIAL = FontProperties(family="Arial")
ARIAL_B = FontProperties(family="Arial", weight="bold")


def mix(col, k, base=PAPER):
    """col faded toward the paper: k = 1 is full color, 0 is paper."""
    c = np.array(matplotlib.colors.to_rgb(col))
    b = np.array(matplotlib.colors.to_rgb(base))
    return matplotlib.colors.to_hex(b + k * (c - b))


_W = {}


def tw(text, fs, bold=False):
    """Ink width of one line of text, in points."""
    key = (text, fs, bold)
    if key not in _W:
        _W[key] = TextPath((0, 0), text, size=fs, prop=ARIAL_B if bold else ARIAL).get_extents().width
    return _W[key]


# ---------------------------------------------------------------------------------------------------------------
# Faded NERTA
def faded_nerta(ax, lay, ppu):
    st = lay.st
    sc = ppu / 4.836   # the main map's river widths are in points at 4.836 points per unit
    M.real_water(ax, {})
    for n, xy in M.RIVERS.items():
        ax.plot(*smooth_open(xy, 2).T, color=M.WATER, lw=M.WIDTH[n] * sc, zorder=0.95, solid_capstyle="round", solid_joinstyle="round")
    ax.plot(*smooth_open(M.BASIN, 2).T, color=M.WATER, lw=M.BASIN_PT * sc, zorder=0.95, solid_capstyle="round", solid_joinstyle="round")
    w = smooth_open(M.CHARLES_WEST, 3)
    run = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(w, axis=0).T))])
    for k in range(len(w) - 1):
        ax.plot(*w[k:k + 2].T, color=M.WATER, lw=M.WIDTH["charles"] * sc * (1 - 0.66 * run[k] / run[-1]), zorder=0.95, solid_capstyle="round")
    nw, cw = st.NW * ppu, st.CW * ppu
    for col, xy, kind in lay.geo:
        if kind == "T":
            ax.plot(*xy.T, color=mix(col, 0.36), lw=nw, zorder=4, solid_capstyle="round", solid_joinstyle="round")
        elif kind == "C":
            ax.plot(*xy.T, color=mix(M.PURPLE, 0.42), lw=cw, zorder=3, solid_capstyle="butt", solid_joinstyle="round")
        elif kind == "S":
            ax.plot(*xy.T, color=mix(M.SILVER, 0.36), lw=nw * 0.75, zorder=3.9, solid_capstyle="round", solid_joinstyle="round")
        else:   # the BIGGER Dig
            ax.plot(*xy.T, color=mix(INK, 0.22), lw=nw * 1.5, zorder=3.95, solid_capstyle="round")
    edge = mix(INK, 0.32)
    dot = st.DOT
    rings = set(M.RINGS)
    cr = {c[0].replace("\n", "").replace(" ", "").replace(" ", "") for c in M.CR_STOPS}
    seen = set()
    for n, p in lay.sch.items():
        key = (round(p[0], 2), round(p[1], 2))
        if key in seen:
            continue
        seen.add(key)
        if n.replace(" ", "") in cr:
            ax.add_patch(FancyBboxPatch((p[0] - dot * 0.8, p[1] - dot * 0.8), dot * 1.6, dot * 1.6, boxstyle="square,pad=0",
                                        fc=mix(M.PURPLE, 0.42), ec="none", zorder=5.5))
            continue
        if n in M.ENDS:   # a line's end: a faded ring in the line's color, as the main map draws it (North Reading, Bleachery...)
            ax.add_patch(Circle(p, dot * 1.45, fc=WHITE, ec=mix(M.ENDS[n], 0.5), lw=1.1, zorder=6))
            continue
        r = dot * (1.45 if n in rings else 1.0)
        if n in M.ENDS:   # a line's end: a faded ring in the line's color, as the main map draws its terminals
            ax.add_patch(Circle(p, dot * 1.6, fc=WHITE, ec=mix(M.ENDS[n], 0.55), lw=1.6, zorder=6))
            continue
        ax.add_patch(Circle(p, r, fc=WHITE, ec=edge, lw=0.55 if n not in rings else 0.9, zorder=6))
    for a, b in M.CAPSULES:   # transfer capsules, faded
        ax.plot([a[0], b[0]], [a[1], b[1]], color=edge, lw=dot * 2.9 * ppu, zorder=5.8, solid_capstyle="round")
        ax.plot([a[0], b[0]], [a[1], b[1]], color=WHITE, lw=dot * 2.9 * ppu - 1.8, zorder=5.85, solid_capstyle="round")


# ---------------------------------------------------------------------------------------------------------------
# Trams
def draw_trams(ax, lay, ppu):
    st = lay.st
    W = st.w_pt
    for rid in sorted(lay.lines, key=lay.net.rank.get):
        xy = lay.lines[rid]
        if len(xy) < 2:
            continue
        ax.plot(*xy.T, color=PAPER, lw=W + 1.5, zorder=19.5, solid_capstyle="round", solid_joinstyle="round")
    for rid in sorted(lay.lines, key=lay.net.rank.get):
        xy = lay.lines[rid]
        if len(xy) < 2:
            continue
        ax.plot(*xy.T, color=PINK, lw=W, zorder=20, solid_capstyle="round", solid_joinstyle="round")
        ax.plot(*xy.T, color=INK, lw=st.hair_pt, zorder=20.5, solid_capstyle="butt", solid_joinstyle="round")


def stop_symbol(ax, c, r, d, transfer, st, ppu, z=22):
    """White circle with a pink edge (ink edge at a NERTA station), and a pink cross: one arm along the track, one across."""
    e = st.edge_pt / ppu
    ax.add_patch(Circle(c, r - e / 2, fc=WHITE, ec=INK if transfer else PINK, lw=st.edge_pt * (1.15 if transfer else 1.0), zorder=z))
    d = np.asarray(d, float)
    n = np.hypot(*d)
    u = d / n if n > 1e-9 else np.array([1.0, 0.0])
    v = np.array([-u[1], u[0]])
    reach = st.ARM * r
    for a in (u, v):
        ax.plot([c[0] - a[0] * reach, c[0] + a[0] * reach], [c[1] - a[1] * reach, c[1] + a[1] * reach],
                color=PINK, lw=st.edge_pt, solid_capstyle="butt", zorder=z + 0.2)


def free_tags(ax, lay):
    """One level FREE tag mid-route on each free tram, at the spot nearest the middle that keeps clear of every stop."""
    st = lay.st
    boxes = []
    h = FREE_H * st.W
    from matplotlib.textpath import TextPath as _TP
    ref = _TP((0, 0), "FREE", size=1, prop=ARIAL_B).get_extents()
    capr = _TP((0, 0), "F", size=1, prop=ARIAL_B).get_extents().y1
    w = (ref.x1 - ref.x0) * h * 0.45 / capr + h
    for rid in FREE_ROUTES:
        xy = lay.lines.get(rid)
        if xy is None or len(xy) < 2:
            continue
        ln = LineString(xy)
        best = None
        for f in np.linspace(0.25, 0.75, 201):
            q = ln.interpolate(f * ln.length)
            b = box(q.x - w / 2, q.y - h / 2, q.x + w / 2, q.y + h / 2)
            clear = min(Point(s["center"]).distance(b) - st.ARM * s["r"] for s in lay.stops.values())
            near_rail = min((LineString(xy).distance(b) - (st.NW if kind_ == "T" else st.CW) / 2) for _c, xy, kind_ in lay.geo)
            if clear < 0.8 or near_rail < 0.5:
                continue
            score = abs(f - 0.5)
            if best is None or score < best[0]:
                best = (score, q, b)
        if best is None:
            print(f"  no clear spot for the FREE tag on the {rid}")
            continue
        _, q, b = best
        draw_free_tag(ax, q.x, q.y, h, z=23.5)
        print(f"  FREE tag on the {rid} at ({q.x:.1f}, {q.y:.1f})")
        boxes.append(b)
    return boxes


def snap_dir(d):
    """The cross follows the track; on a lattice track that is a multiple of 45 degrees."""
    a = math.atan2(d[1], d[0])
    a = round(a / (math.pi / 4)) * (math.pi / 4)
    return np.array([math.cos(a), math.sin(a)])


# ---------------------------------------------------------------------------------------------------------------
# Labels and route badges
class Placer:
    """Greedy label placement with a few rounds of repair. Everything is in drawing units."""

    def __init__(self, ppu, frame, hard_boxes):
        self.ppu = ppu
        self.frame = frame
        self.hard = [box(*b) for b in hard_boxes]
        self.soft = []      # (geometry, weight per unit area, tag)
        self.items = []     # placed: dict(kind, box, ...)

    def build(self):
        self.tree = STRtree([g for g, _, _ in self.soft]) if self.soft else None

    def obstacle_cost(self, b, own=None):
        c = 0.0
        if self.tree is not None:
            for i in self.tree.query(b):
                g, wgt, tag = self.soft[i]
                if own is not None and tag == own:
                    continue
                a = g.intersection(b).area
                if a > 0:
                    c += wgt * a + (wgt * 0.08 if wgt >= 50 else 0)
        for h in self.hard:
            if h.intersects(b):
                c += 1000
        x0, y0, x1, y1 = b.bounds
        f = self.frame
        if x0 < f[0] or x1 > f[1] or y0 < f[2] or y1 > f[3]:
            c += 1000
        return c


def label_variants(text):
    """One line, or two lines split at the space nearest the middle (long names only)."""
    out = [text]
    if " " in text and len(text) > 6:   # two short lines keep a name's middle near its own stop (round-3 center rule)
        words = text.split(" ")
        best = None
        for k in range(1, len(words)):
            a, b = " ".join(words[:k]), " ".join(words[k:])
            score = abs(len(a) - len(b))
            if best is None or score < best[0]:
                best = (score, a + "\n" + b)
        out.append(best[1])
    return out


def text_box(x, y, text, fs, ha, va, ppu, bold=False):
    lines = text.split("\n")
    w = max(tw(t, fs, bold) for t in lines) / ppu
    lh = fs * 1.0 / ppu
    h = lh * len(lines) + (len(lines) - 1) * fs * 0.05 / ppu
    x0 = {"left": x, "right": x - w, "center": x - w / 2}[ha]
    y0 = {"bottom": y, "top": y - h, "center": y - h / 2}[va]
    return (x0 - 0.08, y0 - 0.12 * fs / ppu - 0.05, x0 + w + 0.08, y0 + h - 0.1 * fs / ppu + 0.05)


SIDES = {"r": (1, 0, "left", "center", 0.0), "l": (-1, 0, "right", "center", 0.35), "t": (0, 1, "center", "bottom", 0.6),
         "b": (0, -1, "center", "top", 0.6), "tr": (0.75, 0.75, "left", "bottom", 0.8), "tl": (-0.75, 0.75, "right", "bottom", 0.9),
         "br": (0.75, -0.75, "left", "top", 0.8), "bl": (-0.75, -0.75, "right", "top", 0.9)}


def place_labels(ax, lay, ppu, placer, header_boxes, log):
    st = lay.st
    stops = lay.stops
    # obstacles: tram lines, every stop symbol, NERTA dots and lines (light), commuter rail (lighter)
    for rid, xy in lay.lines.items():
        if len(xy) > 1:
            placer.soft.append((LineString(xy).buffer(st.W / 2 + 0.25), 150.0, "line:" + rid))
    for k, s in stops.items():
        c, r = s["center"], s["r"]
        u = snap_dir(s["dir"])
        v = np.array([-u[1], u[0]])
        reach = st.ARM * r
        # the circle and the arm across the track; the arm along the track lies on the pink line itself
        sym = unary_union([Point(c).buffer(r + 0.12), LineString([c - v * reach, c + v * reach]).buffer(0.16)])
        s["shape"] = sym
        s["circle"] = Point(c).buffer(r + 0.05)   # a name may cross an arm of the cross at worst, never the circle
        placer.soft.append((sym, 400.0, "stop:" + k))
        placer.soft.append((LineString([c - u * reach, c + u * reach]).buffer(0.16), 400.0, "stop:" + k))
    served = {s["name"] for s in stops.values() if s["nerta"]}
    for n, p in lay.sch.items():
        if n in served:
            continue
        placer.soft.append((Point(p).buffer(st.DOT * 1.3), 40.0, "dot"))
    for col, xy, kind in lay.geo:
        wgt = 6.0 if kind == "T" else 2.0
        placer.soft.append((LineString(xy).buffer((st.NW if kind == "T" else st.CW) / 2), wgt, "nerta"))
    placer.build()
    keypts = []   # bends and crossings of the tram lines: a name over one hides where the line goes
    allstops = [(np.asarray(s_["center"], float), s_["r"]) for s_ in stops.values()]

    def _free(q):
        return all(math.hypot(q[0] - c_[0], q[1] - c_[1]) > 1.25 * r_ for c_, r_ in allstops)
    lines_ = {rid: LineString(xy) for rid, xy in lay.lines.items() if len(xy) > 1}
    for rid, ln in lines_.items():
        L = ln.length
        ss = np.arange(0.0, L, 0.1)
        if len(ss) < 7:
            continue
        pts_ = np.array([[ln.interpolate(t_).x, ln.interpolate(t_).y] for t_ in ss])
        hd = np.arctan2(*np.diff(pts_, axis=0).T[::-1])
        for i in range(3, len(hd) - 3):
            dlt = abs((hd[i + 3] - hd[i - 3] + math.pi) % (2 * math.pi) - math.pi)
            if dlt > math.radians(35) and _free(pts_[i]):
                keypts.append(pts_[i])
    rl = list(lines_.items())
    for i in range(len(rl)):
        for j in range(i + 1, len(rl)):
            if not rl[i][1].intersects(rl[j][1]):
                continue
            x_ = rl[i][1].intersection(rl[j][1])
            for g_ in getattr(x_, "geoms", [x_]):
                if g_.geom_type == "Point" and _free((g_.x, g_.y)):
                    keypts.append(np.array([g_.x, g_.y]))
    ktree = STRtree([Point(q) for q in keypts]) if keypts else None

    class Placed(list):
        """Placed label and badge boxes, with a coarse grid so each test only looks nearby."""
        CELL = 6.0

        def _cells(self, g):
            x0, y0, x1, y1 = g.bounds
            for i in range(int(math.floor(x0 / self.CELL)), int(math.floor(x1 / self.CELL)) + 1):
                for j in range(int(math.floor(y0 / self.CELL)), int(math.floor(y1 / self.CELL)) + 1):
                    yield (i, j)

        def __init__(self):
            super().__init__()
            self.grid = {}

        def append(self, item):
            super().append(item)
            for c in self._cells(item[0]):
                self.grid.setdefault(c, []).append(item)

        def remove_tag(self, tag):
            keep = [it for it in self if it[1] != tag]
            self.clear()
            self.grid = {}
            for it in keep:
                self.append(it)

        def near(self, g):
            seen = set()
            for c in self._cells(g.buffer(0.3)):
                for it in self.grid.get(c, ()):
                    if id(it) not in seen:
                        seen.add(id(it))
                        yield it

    placed = Placed()   # (box geometry, tag)

    def overlap_placed(b, tag):
        c = 0.0
        for g, t in placed.near(b):
            if t == tag:
                continue
            if g.intersects(b):
                a = g.intersection(b).area
                c += 500 + 400 * a
            elif g.distance(b) < 0.25:
                c += 25
        return c

    # route badges first: they mark where each route ends. They can move later if a name needs their spot.
    bspec = {}
    for k, rids in lay.route_ends.items():
        if k not in stops:
            continue
        s = stops[k]
        rids = sorted(set(rids), key=lay.net.rank.get)
        fsb, hb, gapb = 6.4, 9.2 / ppu, 1.0 / ppu
        ws = [max(hb * 1.25, (tw(x, fsb, True) + 4.6) / ppu) for x in rids]
        total = sum(ws) + gapb * (len(ws) - 1)
        c, r = s["center"], s["r"]
        d = snap_dir(s["dir"])
        clear = Point(c).buffer(st.ARM * r + 0.35)
        cl = []
        n1 = (len(rids) + 1) // 2
        w2 = max(sum(ws[:n1]) + gapb * (n1 - 1), sum(ws[n1:]) + gapb * max(0, len(ws) - n1 - 1))
        wcol = max(ws)
        for rows, (bw, bh) in ((1, (total, hb)), (2, (w2, 2 * hb + gapb)), (len(rids), (wcol, len(rids) * hb + (len(rids) - 1) * gapb))):
            if rows >= 2 and len(rids) < 3:
                continue
            for ang in np.arange(0, 360, 22.5):
                a_ = math.radians(ang)
                e = np.array([math.cos(a_), math.sin(a_)])
                for extra in ((0.0, 0.6, 1.2, 2.4, 3.2, 4.0) if len(rids) >= 4 else (0.0, 0.6, 1.2, 2.4)):
                    t = 0.0
                    while True:   # slide out until the badge clears the stop and its cross
                        cx, cy = c + e * t
                        bb = box(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
                        if not bb.intersects(clear):
                            break
                        t += 0.15
                    cx, cy = c + e * (t + extra)
                    bb = box(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
                    pref = (0.0 if abs(np.dot(e, d)) > 0.6 else 1.5) + 0.3 * t + 3.0 * extra + 0.8 * abs(rows - (2 if len(rids) >= 3 else 1)) + 0.4 * bw
                    cl.append((pref, cx, cy, bb, rows))
        if len(rids) >= 4:   # round-4 audit (Harvard): two short rows hugging the stop on opposite sides
            nA = (len(rids) + 1) // 2
            parts = [(rids[:nA], ws[:nA]), (rids[nA:], ws[nA:])]
            for ang in (0.0, 45.0, 90.0, 135.0):
                for flip in (0, 1):
                    for extra in (0.0, 0.3, 0.6):
                        boxes, info, tt = [], [], 0.0
                        for pi, (rr, ww) in enumerate(parts):
                            a_ = math.radians(ang + 180.0 * ((pi + flip) % 2))
                            e = np.array([math.cos(a_), math.sin(a_)])
                            bw = sum(ww) + gapb * (len(ww) - 1)
                            t = 0.0
                            while True:
                                cx, cy = c + e * t
                                bb = box(cx - bw / 2, cy - hb / 2, cx + bw / 2, cy + hb / 2)
                                if not bb.intersects(clear):
                                    break
                                t += 0.15
                            cx, cy = c + e * (t + extra)
                            boxes.append(box(cx - bw / 2, cy - hb / 2, cx + bw / 2, cy + hb / 2))
                            info.append((cx, cy, rr, ww))
                            tt += t
                        if boxes[0].buffer(0.2).intersects(boxes[1]):
                            continue
                        pref = 0.6 + 0.3 * tt / 2 + 3.0 * extra + 0.4 * max(b_.bounds[2] - b_.bounds[0] for b_ in boxes)
                        cl.append((pref, c[0], c[1], unary_union(boxes), ("split", info)))
        bspec[k] = dict(rids=rids, ws=ws, hb=hb, fsb=fsb, gapb=gapb, total=total, cands=cl)
    bchoice = {}

    def badge_score(k, cand, strict=True):
        pref, cx, cy, bb, _rows = cand
        hard = []
        for g, tg in placed.near(bb):
            if tg != "badge:" + k and g.intersection(bb).area > 0.005:
                hard.append(tg)
        for kk in near_stops(bb):
            if stops[kk]["shape"].intersection(bb).area > 0.005:
                hard.append("stop:" + kk)
        if any(h.intersects(bb) for h in placer.hard):   # the header, the Key and the FREE tags
            hard.append("frame")
        c0 = stops[k]["center"]
        r0 = stops[k]["r"]
        for part in getattr(bb, "geoms", [bb]):   # a split block: each half answers for itself
            q = part.centroid
            d_own_c = math.hypot(q.x - c0[0], q.y - c0[1])
            for kk in near_stops(part.buffer(4.0)):   # a badge block reads with the nearest stop: it must be its own, edge and center
                ck = stops[kk]["center"]
                if kk != k and (Point(ck).distance(part) < Point(c0).distance(part) + (0.3 if strict else -1.0)
                                or (strict and math.hypot(q.x - ck[0], q.y - ck[1]) < d_own_c + 0.5)):
                    hard.append("near:" + kk)
            if strict and dtree is not None:   # round-4 audit (106 at Lebanon St): nearer its stop than any station dot too
                for i in dtree.query(part.buffer(3.0)):
                    dq = dots_tree_pts[i]
                    if math.hypot(q.x - dq[0], q.y - dq[1]) < d_own_c + 0.3:
                        hard.append("near:dot")
                        break
            x0b, y0b, x1b, y1b = part.bounds
            for g, tg in placed.near(part.buffer(1.0)):   # level beside a name, it reads as that name's route
                if not tg.startswith("lab:"):
                    continue
                gx0, gy0, gx1, gy1 = g.bounds
                vo = min(y1b, gy1) - max(y0b, gy0)
                hgap = max(gx0 - x1b, x0b - gx1)
                if vo > 0.3 * min(y1b - y0b, gy1 - gy0) and 0 <= hgap < 1.2 * SC:
                    hard.append("row:" + tg)
            # round-4 audit: right by its stop (Forest Hills, Harvard), nothing drawn between (a commuter rail line)
            gap_own = Point(c0).distance(part) - r0
            if gap_own > (1.0 if strict else 1.8):
                hard.append("far")
            npt = nearest_points(Point(c0), part)[1]
            dv = np.array([npt.x - c0[0], npt.y - c0[1]])
            if np.hypot(*dv) > r0 + 0.05 and ltree is not None:
                seg = LineString([c0 + dv / np.hypot(*dv) * (r0 + 0.05), (npt.x, npt.y)])
                for i in ltree.query(seg, predicate="intersects"):
                    if lgeoms[i].distance(Point(c0)) > r0 * 0.9:
                        hard.append("across")
                        break
            # never level with another stop or a station close by (106 at Lebanon St, Quincy Center)
            others = [(stops[kk]["center"], stops[kk]["r"]) for kk in near_stops(part.buffer(2.0)) if kk != k]
            if dtree is not None:
                others += [(dots_tree_pts[i], dots_r[i]) for i in dtree.query(part.buffer(2.0))]
            for co, ro in others:
                if y0b - ro <= co[1] <= y1b + ro:
                    hg = max(co[0] - ro - x1b, x0b - (co[0] + ro))
                    if -0.01 <= hg < 1.2 * SC:
                        hard.append("level")
                        break
        if dtree is not None:   # station dots and commuter rail squares
            for i in dtree.query(bb.buffer(0.3)):
                if Point(dots_tree_pts[i]).buffer(dots_r[i] + 0.15).intersects(bb):
                    hard.append("dot")
        if ltree is not None and len(ltree.query(bb.buffer(0.12), predicate="intersects")):
            hard.append("line")   # a faded NERTA or commuter rail line
        if ctree is not None and len(ctree.query(bb.buffer(0.2))):
            hard.append("capsule")
        return pref + placer.obstacle_cost(bb, own="stop:" + k) * 0.05 + 2000.0 * len(hard), hard

    def place_badge(k, strict=True):
        best = None
        for cand in bspec[k]["cands"]:
            c_, hard = badge_score(k, cand, strict)
            if best is None or c_ < best[0]:
                best = (c_, cand, hard)
        bchoice[k] = best
        placed.append((best[1][3], "badge:" + k))

    # station and stop names
    todo = []
    for k, s in stops.items():
        name = s["name"]
        if s["nerta"]:
            text = M.TEXT.get(name, name).replace("\n", " ")
            if name == "Mass Ave":
                text = "MIT"
            todo.append((k, text, FS_NERTA, GRAY, "nerta"))
        else:
            todo.append((k, name, FS_TRAM, INK, "tram"))

    # Max, November 8: "id prefer overlapping the color before putting the text confusingly far away." A name may sit on a
    # line (with a paper halo) but always right beside its own stop; never on another name, a badge or a stop circle.
    served_xy = [s_["center"] for s_ in stops.values() if s_["nerta"]] + [lay.sch[n] for n in served if n in lay.sch]
    # every unserved station dot once (the commuter rail stops are keyed twice, "South Salem" and "SouthSalem")
    dots_tree_pts, dots_r = [], []
    for n, p in lay.sch.items():
        p = np.asarray(p, float)
        if n in served or any(np.hypot(*(p - np.asarray(q, float))) < 0.05 for q in served_xy + dots_tree_pts):
            continue
        dots_tree_pts.append(p)
        dots_r.append(st.DOT * (1.6 if n in M.ENDS else 1.45 if n in M.RINGS else 1.0))
    dtree = STRtree([Point(p) for p in dots_tree_pts]) if dots_tree_pts else None

    def cands_for(k, text, fs):
        """Level names only, right beside the stop: to its right or left at its own height, or centered above or below it
        (main-map audit, November 8: no stair-steps down a diagonal, no shrunk type). Each slides out just clear of the cross."""
        s = stops[k]
        c = s["center"]
        own = stops[k]["shape"].buffer(0.22)
        out = []
        u = snap_dir(s["dir"])
        diag = abs(abs(u[0]) - abs(u[1])) < 0.2   # the track runs at 45 degrees
        sides = [("r", (1, 0), "left", "center", 0.0), ("l", (-1, 0), "right", "center", 0.3),
                 ("t", (0, 1), "center", "bottom", 0.6), ("b", (0, -1), "center", "top", 0.6)]
        for var_i, t in enumerate(label_variants(text)):
            for side, e, ha, va, pref in sides:
                e = np.array(e, float)
                g = 0.3 * SC
                while True:
                    x, y = c + e * g
                    bx = box(*text_box(x, y, t, fs, ha, va, ppu))
                    if not bx.intersects(own):
                        break
                    g += 0.08 * SC
                for far in (0.0, 0.15 * SC):
                    x, y = c + e * (g + far)
                    bx = box(*text_box(x, y, t, fs, ha, va, ppu))
                    out.append((pref + 0.9 * var_i + 3.0 * far / SC, x, y, ha, va, t, bx, fs))
        return out

    HARD = 2000.0
    lgeoms = [LineString(xy).buffer((st.NW if kind == "T" else st.CW) / 2) for _c, xy, kind in lay.geo]
    ltree = STRtree(lgeoms) if lgeoms else None
    caps = [LineString([a_, b_]).buffer(st.DOT * 1.45) for a_, b_ in M.CAPSULES]
    ctree = STRtree(caps) if caps else None

    def nearer(k, b, own=None):
        """Hard test (main-map audit): a name must be clearly nearer its own stop than any other stop, station dot or
        station capsule, and no other stop may sit level with it and nearer."""
        c0 = stops[k]["center"]
        out = [kk for kk in near_stops(b.buffer(4.0)) if kk != k and (not clearly_own(b, c0, stops[k]["r"], stops[kk]["center"], stops[kk]["r"])
                                                                      or row_clash(b, c0, stops[kk]["center"], 0.55 * SC, 0.8 * SC)
                                                                      or col_clash(b, c0, stops[kk]["center"], 0.1 * SC, 0.8 * SC))]
        if dtree is not None:
            out += ["dot" for i in dtree.query(b.buffer(4.0))
                    if not clearly_own(b, c0, stops[k]["r"], dots_tree_pts[i], dots_r[i], NEAR_MARGIN * SC * 1.8) or row_clash(b, c0, dots_tree_pts[i], 0.55 * SC, 0.45 * SC)]
        return out

    def score(k, cand):
        p, x, y, ha, va, t, b, f_ = cand
        cost = p
        hard = []
        # lines and faded dots: allowed under a name, at a small price
        if placer.tree is not None:
            for i in placer.tree.query(b):
                g, wgt, tag = placer.soft[i]
                a_ = g.intersection(b).area
                if a_ <= 0:
                    continue
                if tag.startswith("stop:"):
                    if tag.startswith("stopc:"):
                        continue
                    cost += 8.0 * a_
                elif tag == "dot":
                    cost += 40.0 * a_
                elif tag.startswith("line:"):
                    cost += (10.0 if tag[5:] in stops[k].get("routes", []) else 90.0) * a_
                else:
                    cost += 2.0 * a_
        x0, y0, x1, y1 = b.bounds
        f = placer.frame
        if x0 < f[0] or x1 > f[1] or y0 < f[2] or y1 > f[3] or any(h.intersects(b) for h in placer.hard):
            hard.append("frame")
        for g, tg in placed.near(b):
            if tg != "lab:" + k and g.intersection(b).area > 0.005:
                hard.append(tg)
        for kk in near_stops(b):
            if stops[kk]["circle"].intersection(b).area > 0.005:
                hard.append("stop:" + kk)
            elif kk != k and stops[kk]["shape"].intersection(b).area > 0.005:
                cost += 400.0
        for ci in (ctree.query(b.buffer(0.3)) if ctree is not None else []):   # station capsules: never touched
            hard.append("capsule")
        for g, tg in placed.near(b.buffer(1.0)):   # two names (or a name and a badge row) that read as one
            if tg == "lab:" + k:
                continue
            gx0, gy0, gx1, gy1 = g.bounds
            vo = min(y1, gy1) - max(y0, gy0)
            hgap = max(gx0 - x1, x0 - gx1)
            if vo > 0.4 * min(y1 - y0, gy1 - gy0) and 0 <= hgap < 0.9 * SC:
                hard.append("row:" + tg)
            ho = min(x1, gx1) - max(x0, gx0)
            vgap = max(gy0 - y1, y0 - gy1)
            if ho > 0 and 0 <= vgap < 0.45 * SC:
                cost += 300.0   # stacked like a list
        if ktree is not None and len(ktree.query(b.buffer(0.3), predicate="intersects")):
            cost += 1500.0   # over a bend or a crossing of the tram lines: only where nothing else fits
        # right beside its own stop: nearer it than any other stop or station dot
        own = stops[k]["shape"].distance(b)
        cost += 2.0 * own
        hard += ["near:" + x for x in nearer(k, b, own)]   # a name nearer another stop than its own misleads (round 4: never)
        return cost + HARD * len(hard), hard

    stree = STRtree([stops[k]["shape"] for k in stops])
    skeys = list(stops)

    def near_stops(b):
        return [skeys[i] for i in stree.query(b.buffer(1.5))]

    late = [k for k in bspec if len(bspec[k]["rids"]) >= 4]   # a big hub's badges go after the names, round its own name
    for k in bspec:
        if k not in late:
            place_badge(k)

    # hardest first: the stops with the most stops around them
    centers = np.array([stops[k]["center"] for k, *_ in todo])
    dens = [int(np.sum(np.hypot(*(centers - stops[k]["center"]).T) < 8)) for k, *_ in todo]
    order = [todo[i] for i in np.argsort(dens)[::-1]]
    info = {k: (text, fs, col, kind) for k, text, fs, col, kind in order}
    cands = {k: cands_for(k, text, fs) for k, text, fs, col, kind in order}
    choice = {}

    def place(k):
        best = None
        for cand in cands[k]:
            c_, hard = score(k, cand)
            if best is None or c_ < best[0]:
                best = (c_, cand, hard)
        choice[k] = best
        placed.append((best[1][6], "lab:" + k))
        return best

    for k, *_ in order:
        place(k)
    # repair: any name still on another name or a stop moves, and so do the names it hits, until none are left
    for rnd in range(20):
        bad = []
        for k in choice:
            placed.remove_tag("lab:" + k)
            c_, hard = score(k, choice[k][1])
            choice[k] = (c_, choice[k][1], hard)
            placed.append((choice[k][1][6], "lab:" + k))
            if hard:
                bad.append(k)
        if not bad:
            break
        hit_badges = list(dict.fromkeys(h[6:] for k in bad for h in choice[k][2] if h.startswith("badge:")))
        for kb in hit_badges:   # move a badge out of a name's way, keeping the names where they are
            placed.remove_tag("badge:" + kb)
            for k in bad:
                cand = choice[k][1]
            place_badge(kb)
        todo_k = list(dict.fromkeys(bad + [h[4:] for k in bad for h in choice[k][2] if h.startswith("lab:")]))
        rng = np.random.default_rng(rnd)
        rng.shuffle(todo_k)
        for k in todo_k:
            placed.remove_tag("lab:" + k)
            place(k)

    # last resort for two names fighting over one spot: try their best spots in pairs
    for rnd in range(6):
        bad = [k for k in choice if choice[k][2]]
        if not bad:
            break
        for k in bad:
            if not choice[k][2]:
                continue
            others = [h[4:] for h in choice[k][2] if h.startswith("lab:")]
            for j in others[:2]:
                placed.remove_tag("lab:" + k)
                placed.remove_tag("lab:" + j)
                ranked_k = sorted(((score(k, cd)[0], cd) for cd in cands[k]), key=lambda t_: t_[0])[:120]
                ranked_j = sorted(((score(j, cd)[0], cd) for cd in cands[j]), key=lambda t_: t_[0])[:120]
                best = None
                for ck, cdk in ranked_k:
                    if ck >= HARD:
                        continue
                    for cj, cdj in ranked_j:
                        if cj >= HARD or cdk[6].intersection(cdj[6]).area > 0.005:
                            continue
                        if best is None or ck + cj < best[0]:
                            best = (ck + cj, cdk, cdj)
                        break
                if best:
                    choice[k] = (score(k, best[1])[0], best[1], [])
                    choice[j] = (score(j, best[2])[0], best[2], [])
                placed.append((choice[k][1][6], "lab:" + k))
                placed.append((choice[j][1][6], "lab:" + j))
                if best:
                    break
        for k in choice:
            placed.remove_tag("lab:" + k)
            c_, hard = score(k, choice[k][1])
            choice[k] = (c_, choice[k][1], hard)
            placed.append((choice[k][1][6], "lab:" + k))
    # kick: give a stuck name a spot blocked only by other names or a badge, and move those on
    for _kick in range(3):
        stuck = [k for k in choice if choice[k][2]]
        if not stuck:
            break
        for k in stuck:
            placed.remove_tag("lab:" + k)
            c0, h0 = score(k, choice[k][1])
            choice[k] = (c0, choice[k][1], h0)
            if not h0:
                placed.append((choice[k][1][6], "lab:" + k))
                continue
            opts = []
            for cd in cands[k]:
                c_, hard = score(k, cd)
                if all(h.startswith("lab:") or h.startswith("badge:") for h in hard):
                    opts.append((c_ - HARD * len(hard), cd, [h for h in hard]))
            opts.sort(key=lambda t_: t_[0])
            done_k = False
            for c_, cd, hs in opts[:150]:
                js = [h[4:] for h in hs if h.startswith("lab:")]
                bs = [h[6:] for h in hs if h.startswith("badge:")]
                saved = {j: choice[j] for j in js}
                bsaved = {j: bchoice[j] for j in bs}
                placed.append((cd[6], "lab:" + k))
                for j in js:
                    placed.remove_tag("lab:" + j)
                for j in bs:
                    placed.remove_tag("badge:" + j)
                ok = True
                for j in bs:
                    place_badge(j)
                    if bchoice[j][2]:
                        ok = False
                for j in js if ok else []:
                    best = None
                    for cdj in cands[j]:
                        cj, hj = score(j, cdj)
                        if not hj and (best is None or cj < best[0]):
                            best = (cj, cdj)
                    if best is None:
                        ok = False
                        break
                    choice[j] = (best[0], best[1], [])
                    placed.append((best[1][6], "lab:" + j))
                if ok:
                    choice[k] = (score(k, cd)[0], cd, [])
                    done_k = True
                    break
                for j in js:   # undo
                    placed.remove_tag("lab:" + j)
                    choice[j] = saved[j]
                    placed.append((saved[j][1][6], "lab:" + j))
                for j in bs:
                    placed.remove_tag("badge:" + j)
                    bchoice[j] = bsaved[j]
                    placed.append((bsaved[j][1][3], "badge:" + j))
                placed.remove_tag("lab:" + k)
            if not done_k:
                placed.append((choice[k][1][6], "lab:" + k))
    for k in choice:
        placed.remove_tag("lab:" + k)
        c_, hard = score(k, choice[k][1])
        choice[k] = (c_, choice[k][1], hard)
        placed.append((choice[k][1][6], "lab:" + k))
    for k in choice if os.environ.get("NERTA_TRAM_DEBUG") else []:
        if stops[k]["name"] in os.environ["NERTA_TRAM_DEBUG"].split(","):
            b = choice[k][1][6]
            c0 = stops[k]["center"]
            print("DEBUG", stops[k]["name"], np.round(b.bounds, 2), "own", np.round(c0, 2), round(Point(c0).distance(b), 3), "hard", choice[k][2])
            for kk in near_stops(b.buffer(4.0)):
                if kk != k:
                    ck = stops[kk]["center"]
                    print("   ", stops[kk]["name"], np.round(ck, 2), round(Point(ck).distance(b), 3),
                          clearly_own(b, c0, stops[k]["r"], ck, stops[kk]["r"]), row_clash(b, c0, ck, 0.55 * SC, 0.45 * SC))
    def kick_badge(k, strict):
        """Take a badge spot only names block (the hub's own name included), and move those names on."""
        opts = []
        for cand in bspec[k]["cands"]:
            c_, hard = badge_score(k, cand, strict)
            if hard and all(h.startswith("lab:") for h in hard):
                opts.append((c_ - 2000.0 * len(hard), cand, [h[4:] for h in set(hard)]))
        opts.sort(key=lambda t_: t_[0])
        placed.remove_tag("badge:" + k)
        for c_, cand, js in opts[:200]:
            saved = {j: choice[j] for j in js}
            placed.append((cand[3], "badge:" + k))
            for j in js:
                placed.remove_tag("lab:" + j)
            ok = True
            for j in js:
                best = None
                for cdj in cands[j]:
                    cj, hj = score(j, cdj)
                    if not hj and (best is None or cj < best[0]):
                        best = (cj, cdj)
                if best is None:
                    ok = False
                    break
                choice[j] = (best[0], best[1], [])
                placed.append((best[1][6], "lab:" + j))
            if ok:
                bchoice[k] = (badge_score(k, cand, strict)[0], cand, [])
                return True
            for j in js:
                placed.remove_tag("lab:" + j)
                choice[j] = saved[j]
                placed.append((saved[j][1][6], "lab:" + j))
            placed.remove_tag("badge:" + k)
        placed.append((bchoice[k][1][3], "badge:" + k))
        return False

    for k in late:
        # round-4 audit (Harvard): first the strict spots, moving names if need be; only then a looser spot
        place_badge(k)
        if bchoice[k][2]:
            kick_badge(k, True)
        if bchoice[k][2]:   # a crowded hub: let the badges sit a little nearer a neighbor, never on a name or a stop
            placed.remove_tag("badge:" + k)
            place_badge(k, strict=False)
            if bchoice[k][2]:
                kick_badge(k, False)
        if bchoice[k][2]:
            from collections import Counter as _C
            cnt = _C(h.split("|")[0] if "|" in h else h for cand in bspec[k]["cands"] for h in set(badge_score(k, cand, False)[1]))
            log(f"  badge spots at {lay.net.nodes[k]['name']}: {len(bspec[k]['cands'])} tried; blocked by {dict(cnt)}")
    for k, (c_, cand, hard) in bchoice.items():
        sp = bspec[k]
        _, cx, cy, bb, rows = cand
        if isinstance(rows, tuple):   # a split block: one row each side of the stop
            for pcx, pcy, rr, ww in rows[1]:
                x = pcx - (sum(ww) + sp["gapb"] * (len(ww) - 1)) / 2
                for rid, wdt in zip(rr, ww):
                    ax.add_patch(FancyBboxPatch((x, pcy - sp["hb"] / 2), wdt, sp["hb"], boxstyle=f"round,pad=0,rounding_size={sp['hb'] / 2}",
                                                fc=PINK, ec=PAPER, lw=0.8, zorder=24))
                    ax.text(x + wdt / 2, pcy - 0.04 * sp["hb"], rid, fontsize=sp["fsb"], fontweight="bold", color=WHITE, ha="center", va="center", zorder=24.5)
                    x += wdt + sp["gapb"]
            for part in bb.geoms:
                lay.badge_boxes.append(part)
            if hard:
                log(f"  badge at {lay.net.nodes[k]['name']} touches {', '.join(hard)}")
            continue
        per = -(-len(sp["rids"]) // rows)
        groups = [(sp["rids"][i:i + per], sp["ws"][i:i + per]) for i in range(0, len(sp["rids"]), per)]
        ng = len(groups)
        for gi, (rr, ww) in enumerate(groups):
            if not rr:
                continue
            wrow = sum(ww) + sp["gapb"] * (len(ww) - 1)
            yy = cy + (sp["hb"] + sp["gapb"]) * ((ng - 1) / 2 - gi)
            x = cx - wrow / 2
            for rid, wdt in zip(rr, ww):
                ax.add_patch(FancyBboxPatch((x, yy - sp["hb"] / 2), wdt, sp["hb"], boxstyle=f"round,pad=0,rounding_size={sp['hb'] / 2}",
                                            fc=PINK, ec=PAPER, lw=0.8, zorder=24))
                ax.text(x + wdt / 2, yy - 0.04 * sp["hb"], rid, fontsize=sp["fsb"], fontweight="bold", color=WHITE, ha="center", va="center", zorder=24.5)
                x += wdt + sp["gapb"]
        lay.badge_boxes.append(bb)
        if hard:
            log(f"  badge at {lay.net.nodes[k]['name']} touches {', '.join(hard)}")
    texts, unlabeled = [], []
    _lines = [LineString(xy).buffer(st.W / 2) for xy in lay.lines.values() if len(xy) > 1]
    _lines += [LineString(xy).buffer((st.NW if kind_ == "T" else st.CW) / 2) for _c, xy, kind_ in lay.geo]
    ltree_all = STRtree(_lines) if _lines else None
    for k, (c_, cand, hard) in choice.items():
        p, x, y, ha, va, t, b, f_ = cand
        text, fs, col, kind = info[k]
        if hard:
            unlabeled.append((lay.stops[k]["name"], f"{kind}, against {', '.join(hard)}"))
            continue
        if nearer(k, b):
            lay.ambiguous.append(lay.stops[k]["name"])
        # the halo is its own layer under the letters: drawn with the text, a second line's halo
        # clips the descenders of the first ("Edge" read "Edqe")
        ax.text(x, y, t, fontsize=f_, color=PAPER, ha=ha, va=va, zorder=24.9, linespacing=0.95,
                path_effects=[pe.withStroke(linewidth=2.2, foreground=PAPER)])
        art = ax.text(x, y, t, fontsize=f_, color=col, ha=ha, va=va, zorder=25, linespacing=0.95)
        if ltree_all is not None and len(ltree_all.query(b, predicate="intersects")):
            pad = 1.2 / ppu   # about 10 px at 600 dpi
            x0b, y0b, x1b, y1b = b.bounds
            ax.add_patch(FancyBboxPatch((x0b - pad, y0b - pad), x1b - x0b + 2 * pad, y1b - y0b + 2 * pad,
                                        boxstyle=f"round,pad=0,rounding_size={pad}", fc=PAPER, ec="none", zorder=24.8))
        texts.append((art, k, kind, c_))
    return texts, unlabeled


# ---------------------------------------------------------------------------------------------------------------
# Header and Key
def header(ax, ppu, x0, y1, web):
    """Top left, as on the main map: the T roundel in tram pink with the NERTA mark under it, the title, and the release block."""
    r = 34.0 / ppu
    ro = r + 3.2 / ppu / 2
    cx, cy = x0 + 2.2 + ro, y1 - 2.4 - ro
    ax.add_patch(Circle((cx, cy), r, fc=WHITE, ec=INK, lw=3.2, zorder=12))   # the roundel, as make_line_poster draws it
    draw_t(ax, cx, cy, r, M.NERTA_COLORS, z=13)   # the multicolor three-layer T (Max, November 8: "send it throughout")
    nb = draw_nerta(ax, cx, cy - ro - 0.9, 2 * ro, "B", colors=M.NERTA_COLORS)
    tx = cx + ro + 2.8
    base = cy - 0.36 * 34 / ppu
    ax.text(tx, base, "Boston Trams", fontsize=34, fontweight="bold", color=INK, va="baseline", zorder=30)
    right = tx + tw("Boston Trams", 34, True) / ppu
    sub = base - 15.5 / ppu - 2.0
    ax.text(tx + 0.1, sub, "Trams over the NERTA network", fontsize=13, color=INK, va="baseline", zorder=30)
    right = max(right, tx + tw("Trams over the NERTA network", 13) / ppu)
    boxes = [(x0, min(nb, sub) - 1.2, right + 1.2, y1)]
    if web:   # the no-disclaimer version: one small note under the logo, nothing else
        note = getattr(M, "CONCEPT_NOTE", "Concept map by Maxwell Howe \u2013 @mapzimus \u2013 2026")
        ax.text(x0 + 2.2, nb - 1.0, note, fontsize=9, color=INK, ha="left", va="top", zorder=30)
        boxes.append((x0, nb - 1.0 - 9 * 1.3 / ppu - 1.0, x0 + 2.2 + tw(note, 9) / ppu + 1.2, nb))
        return boxes, nb
    rw = release_width(size=9.6, ppu=ppu)
    hgt = 6 * 9.6 * 1.2 / ppu
    left, bottom, top = draw_release(ax, tx + 0.1 + rw, sub - 3.2 - hgt / 2, size=9.6, ppu=ppu, ink=INK, z=30)
    boxes.append((x0, bottom - 1.2, max(right, tx + 0.1 + rw) + 1.2, y1))
    return boxes, bottom


def key_panel(ax, lay, ppu, x1, y0, n_routes, web):
    st = lay.st
    fs = 9.0
    step = 13.2 / ppu
    rows = 11
    w = (13.0 + 2.8) + max(tw(t, 9.0) for t in ("Transfer stop, at a NERTA station", "Route number, at each end of a route", "32 tram routes. Driverless maglev, 24 hours a day.")) / ppu
    w = max(w, 2.8 + tw(DROP_NOTE, 8.1) / ppu, 13.0 + 2.8 + max(tw(KEY_TEXT, 9.0), tw(FREE_TEXT, 9.0),
                                                                tw("Tram stop (the cross turns with the line)", 9.0)) / ppu) + 1.3
    h = (rows + 1.3) * step + 1.4
    bx0, by0 = x1 - w - 1.5, y0 + 3.4
    ax.add_patch(FancyBboxPatch((bx0, by0), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=WHITE, ec=INK, lw=1.0, zorder=30))
    lx = bx0 + 2.0
    tx = lx + 13.0
    y = by0 + h - 2.2
    ax.text(lx, y, "Key", fontsize=11, fontweight="bold", color=INK, va="center", zorder=31)
    y -= step * 1.15

    def row(t, y_, bold=False):
        ax.text(tx, y_, t, fontsize=fs, fontweight="bold" if bold else "normal", va="center", color=INK, zorder=31)

    xs = np.array([[lx + 0.4, y], [lx + 10.6, y]])
    ax.plot(*xs.T, color=PAPER, lw=st.w_pt + 1.5, zorder=31, solid_capstyle="round")
    ax.plot(*xs.T, color=PINK, lw=st.w_pt, zorder=31.1, solid_capstyle="round")
    ax.plot(*xs.T, color=INK, lw=st.hair_pt, zorder=31.2, solid_capstyle="butt")
    row("Tram line", y)
    y -= step
    xs = np.array([[lx + 0.4, y], [lx + 10.6, y]])
    ax.plot(*xs.T, color=PINK, lw=st.w_pt, zorder=31.1, solid_capstyle="round")
    ax.plot(*xs.T, color=INK, lw=st.hair_pt, zorder=31.2, solid_capstyle="butt")
    stop_symbol(ax, np.array([lx + 3.2, y]), st.R, (1, 0), False, st, ppu, z=31.5)
    stop_symbol(ax, np.array([lx + 7.8, y]), st.R, (1, 1), False, st, ppu, z=31.5)
    row("Tram stop (the cross turns with the line)", y)
    y -= step
    xs = np.array([[lx + 0.4, y], [lx + 10.6, y]])
    ax.plot(*xs.T, color=mix(M.RED, 0.36), lw=st.NW * ppu, zorder=31, solid_capstyle="round")
    ys = np.array([[lx + 5.5, y - 1.0 * step / 2], [lx + 5.5, y + 1.0 * step / 2]])
    ax.plot(*ys.T, color=PINK, lw=st.w_pt, zorder=31.1, solid_capstyle="butt")
    ax.plot(*ys.T, color=INK, lw=st.hair_pt, zorder=31.2, solid_capstyle="butt")
    stop_symbol(ax, np.array([lx + 5.5, y]), st.R, (0, 1), True, st, ppu, z=31.5)
    row("Transfer stop, at a NERTA station", y)
    y -= step
    hb = 9.2 / ppu
    for i, t in enumerate(("1", "116")):
        wdt = max(hb * 1.25, (tw(t, 6.4, True) + 4.6) / ppu)
        x_ = lx + 0.4 + i * 5.2
        ax.add_patch(FancyBboxPatch((x_, y - hb / 2), wdt, hb, boxstyle=f"round,pad=0,rounding_size={hb / 2}", fc=PINK, ec="none", zorder=31))
        ax.text(x_ + wdt / 2, y - 0.04 * hb, t, fontsize=6.4, fontweight="bold", color=WHITE, ha="center", va="center", zorder=31.2)
    row("Route number, at each end of a route", y)
    y -= step
    for i, c in enumerate((M.RED, M.ORANGE, M.BLUE, M.GREEN)):
        ax.plot([lx + 0.4 + i * 2.7, lx + 2.2 + i * 2.7], [y, y], color=mix(c, 0.36), lw=st.NW * ppu, zorder=31, solid_capstyle="round")
    row("NERTA rail", y)
    y -= step
    ax.plot([lx + 0.4, lx + 10.6], [y, y], color=mix(M.PURPLE, 0.42), lw=st.CW * ppu, zorder=31)
    row("Commuter rail", y)
    y -= step
    draw_cp(ax, lx + 5.5, y, st.R * 1.15, z=31.5)   # the Charlie Points coin, about a stop symbol's height
    row(KEY_TEXT, y)
    y -= step
    xs = np.array([[lx + 0.4, y], [lx + 10.6, y]])
    ax.plot(*xs.T, color=PINK, lw=st.w_pt, zorder=31.1, solid_capstyle="round")
    ax.plot(*xs.T, color=INK, lw=st.hair_pt, zorder=31.2, solid_capstyle="butt")
    draw_free_tag(ax, lx + 5.5, y, FREE_H * st.W, z=31.5)   # the same size as on the map
    row(FREE_TEXT, y)
    y -= step * 1.1
    ax.text(lx, y, "Pods on demand at every stop.", fontsize=fs, fontweight="bold", va="center", color=INK, zorder=31)
    y -= step * 0.95
    ax.text(lx, y, f"{n_routes} tram routes. Driverless maglev, 24 hours a day.", fontsize=fs * 0.9, va="center", color=INK, zorder=31)
    y -= step * 0.95
    ax.text(lx, y, DROP_NOTE, fontsize=fs * 0.9, va="center", color=INK, zorder=31)
    return (bx0 - 0.5, by0 - 0.5, bx0 + w + 0.5, by0 + h + 0.5)


# ---------------------------------------------------------------------------------------------------------------
# Overlap check, as in make_ferry_network.check()
def check(fig, ax, lay, texts):
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    shapes = []
    for art, k, kind, _cost in texts:
        bb = art.get_window_extent(rend)
        (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        pad = 0.18 * art.get_fontsize() / lay.st.ppu
        shapes.append((art.get_text().replace("\n", " ")[:28], k, box(x0, y0 + pad, x1, y1 - pad)))
    bad = []
    for i, (a, ka, sa) in enumerate(shapes):
        for b, kb, sb in shapes[i + 1:]:
            if sa.intersection(sb).area > 0.02:
                bad.append(f"text/text: {a} | {b}")
        for k, s in lay.stops.items():
            if s["circle"].intersection(sa).area > 0.02:
                bad.append(f"text/dot: {a} | {s['name']}")
        for j, bb in enumerate(lay.badge_boxes):
            if bb.intersection(sa).area > 0.02:
                bad.append(f"text/pill: {a} | badge {j}")
        for fb in getattr(lay, "free_boxes", []):
            if fb.intersects(sa):
                bad.append(f"text/pill: {a} | FREE tag")
    served = {s["name"] for s in lay.stops.values() if s["nerta"]}
    dots = []
    taken = [np.asarray(lay.sch[n], float) for n in served if n in lay.sch]
    for n, p in lay.sch.items():
        p = np.asarray(p, float)
        if n in served or any(np.hypot(*(p - q)) < 0.05 for q in taken + dots):
            continue
        dots.append(p)
    for a, k, sa in shapes:   # hard test on every name: clearly nearer its own stop than any other stop or station dot
        so = lay.stops[k]
        for kk, s in lay.stops.items():
            if kk != k and Point(s["center"]).distance(sa) < 5 and (not clearly_own(sa, so["center"], so["r"], s["center"], s["r"], 0.1 * SC)
                                                                   or row_clash(sa, so["center"], s["center"])):
                why = "row" if row_clash(sa, so["center"], s["center"]) else "nearer"
                bad.append(f"text/near: {a} | {s['name']} ({why}; own {Point(so['center']).distance(sa):.2f}, other {Point(s['center']).distance(sa):.2f})")
        for d in dots:
            if Point(d).distance(sa) < 5 and (not clearly_own(sa, so["center"], so["r"], d, lay.st.DOT, 0.1 * SC) or row_clash(sa, so["center"], d)):
                bad.append(f"text/near: {a} | a station dot at ({d[0]:.0f}, {d[1]:.0f})")
                break
        for a_, b_ in M.CAPSULES:
            if LineString([a_, b_]).buffer(lay.st.DOT * 1.45).intersects(sa):
                bad.append(f"text/capsule: {a}")
        if Point(so["center"]).distance(sa) - so["r"] * lay.st.ARM > FAR * SC:
            bad.append(f"text/far: {a} sits {Point(so['center']).distance(sa) - so['r']:.2f} units off its stop")
    keys = list(lay.stops)
    for i, ka in enumerate(keys):
        for kb in keys[i + 1:]:
            if lay.stops[ka]["shape"].intersection(lay.stops[kb]["shape"]).area > 0.02:
                bad.append(f"dot/dot: {lay.stops[ka]['name']} | {lay.stops[kb]['name']}")
    for fb in getattr(lay, "free_boxes", []):
        for k, s in lay.stops.items():
            if s["shape"].intersects(fb):
                bad.append(f"pill/dot: FREE tag | {s['name']}")
        for bb in lay.badge_boxes:
            if bb.intersects(fb):
                bad.append("pill/pill: FREE tag | badge")
    for k, s in lay.stops.items():   # tram stops off station capsules
        for a_, b_ in M.CAPSULES:
            if s["kind"] != "transfer" and LineString([a_, b_]).buffer(lay.st.DOT * 1.45).intersects(Point(s["center"]).buffer(s["r"])):
                bad.append(f"dot/capsule: {s['name']}")
    for j, bb in enumerate(lay.badge_boxes):
        for k, s in lay.stops.items():
            if s["shape"].intersection(bb).area > 0.02:
                bad.append(f"pill/dot: badge {j} | {s['name']}")
        for bb2 in lay.badge_boxes[j + 1:]:
            if bb.intersection(bb2).area > 0.02:
                bad.append(f"pill/pill: badge {j}")
    return bad


def watermarks(fig, ax, lay, ppu, sheet, frames, n_max=12, spacing=13.0):
    """@mapzimus in open water, the main map's style (Max, November 8 evening: everywhere, more prevalent in the water):
    7 pt, make_tmap.WATERMARK, level, just above the water. Only in the sea, clear of every line, name, badge, stop, dot,
    capsule, the header, the Key and the FREE tags. Spots: the main map's own first, then the most spread-out open water."""
    st = lay.st
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    obst = []
    for t in ax.texts:
        if t.get_visible() and t.get_text().strip():
            e = t.get_window_extent(rend)
            (a0, b0), (a1, b1) = inv.transform([(e.x0, e.y0), (e.x1, e.y1)])
            obst.append(box(min(a0, a1), min(b0, b1), max(a0, a1), max(b0, b1)))
    obst += [LineString(xy).buffer(st.W) for xy in lay.lines.values() if len(xy) > 1]
    obst += [LineString(xy).buffer((st.NW if kind == "T" else st.CW)) for _c, xy, kind in lay.geo]
    obst += [s_["shape"] for s_ in lay.stops.values()]
    obst += [Point(p_).buffer(st.DOT * 2.0) for p_ in lay.sch.values()]
    obst += [LineString([a_, b_]).buffer(st.DOT * 2.0) for a_, b_ in M.CAPSULES]
    obst += list(lay.badge_boxes) + list(getattr(lay, "free_boxes", [])) + list(getattr(lay, "extra_shapes", []))
    obst += [box(*f) for f in frames]
    tree = STRtree(obst)
    sea = M.SEA
    wbox = tw("@mapzimus", 7.0) / ppu
    hbox = 7.0 * 1.05 / ppu
    x0f, x1f, y0f, y1f = sheet[0] + 1.0, sheet[1] - 1.0, sheet[2] + 1.0, sheet[3] - 1.0

    def ok(c):
        b = box(c[0] - wbox / 2, c[1] - hbox / 2, c[0] + wbox / 2, c[1] + hbox / 2)
        if b.bounds[0] < x0f or b.bounds[2] > x1f or b.bounds[1] < y0f or b.bounds[3] > y1f:
            return None
        if not sea.contains(b.buffer(0.5)):
            return None
        g = b.buffer(0.6)
        if any(obst[i].intersects(g) for i in tree.query(g)):
            return None
        return b
    cands = [np.array(p_, float) for p_ in getattr(M, "WATERMARKS", [])]
    main_n = len(cands)
    xs = np.arange(x0f + wbox / 2, x1f - wbox / 2, 2.0)
    ys = np.arange(y0f + hbox / 2, y1f - hbox / 2, 2.0)
    cands += [np.array([x, y]) for x in xs for y in ys]
    good = [(c, ok(c), i < main_n) for i, c in enumerate(cands)]
    good = [(c, b, m) for c, b, m in good if b is not None]
    chosen = []
    for c, b, m in good:   # the main map's spots first, kept apart
        if m and all(np.hypot(*(c - q)) >= spacing for q, _ in chosen):
            chosen.append((c, b))
    rest = [(c, b) for c, b, m in good if not m]
    while len(chosen) < n_max and rest:   # then the open water farthest from every mark so far
        if chosen:
            dmin = [min(np.hypot(*(c - q)) for q, _ in chosen) for c, _ in rest]
            j = int(np.argmax(dmin))
            if dmin[j] < spacing:
                break
        else:
            j = 0
        chosen.append(rest.pop(j))
    for c, b in chosen[:n_max]:
        ax.text(c[0], c[1], "@mapzimus", fontsize=7.0, color=M.WATERMARK, ha="center", va="center", zorder=1.5)
    return [b for _c, b in chosen[:n_max]], obst


# ---------------------------------------------------------------------------------------------------------------
CROPS = {   # area: (center x, center y, half width, half height) in drawing units
    "harvard": (60, 120, 16, 12),
    "nubian": (80, 54, 14, 10),
    "ashmont_codman": (88, 30, 14, 10),
    "uphams": (100, 50, 12, 9),
    "chelsea_revere": (150, 152, 24, 18),
    "quincy": (128, 14, 22, 16),
    "swampscott": (205, 197, 15, 13),
    "hingham": (140, 6, 16, 12),
    "walpole": (34, -14, 16, 14),
    "winthrop": (160, 130, 15, 12),
    "medford": (84, 166, 18, 13),
    "north_reading": (114, 192, 14, 16),
    "waltham_bleachery": (-14, 136, 14, 12),
    "kenmore_fenway": (52, 80, 12, 10),
    # round-4 audit spots
    "mission_park": (52.7, 49.7, 7, 5),
    "beth_israel": (40.7, 71.4, 7, 5),
    "forest_hills": (45, 27, 9, 7),
    "lebanon_106": (111.5, 189.5, 7, 5),
    "egleston_seaver": (72, 42, 10, 6),
    "oakwood": (131, 27, 7, 5),
    "memorial_pkwy": (79, -6.4, 7, 5),
    "sagamore": (171, 167, 7, 5),
    "duffley": (21, 65, 7, 5),
    # main-map change, November 8 evening: Red to Burlington and Hanscom, Green E to Woburn, A ends at Watertown, Seaport
    "watertown": (-10, 124, 12, 10),
    "burlington_woburn": (36, 180, 18, 12),
    "seaport": (134, 78, 12, 9),
    "cambridgeport": (64, 98, 12, 9),   # the old BU Bridge stop on the Yellow (v1.1), by the 64 and 70
}


def next_version():
    v = 1
    while (OUT / f"tram_map_v{v}.png").exists() or (OUT / f"tram_map_v{v}.pdf").exists():
        v += 1
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--web", action="store_true", help="leave out the release block (nerta.fun)")
    ap.add_argument("--ppu", type=float, default=7.5, help="points per drawing unit; the main map is 4.836")
    ap.add_argument("--crops", action="store_true")
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--name", default=None, help="file stem; default tram_map_vN")
    ap.add_argument("--draft", default=None, help="write trial renders to this folder instead of output/copies")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--stamp", action="store_true", help="draw the v1.0 mark (normally the main session's release_v1.py adds it)")
    args = ap.parse_args()
    if getattr(M, "NODISC", False):   # NERTA_NO_DISCLAIMER=1, as the main map gates it: the same as --web
        args.web = True
    global OUT, SC
    if args.draft:
        OUT = Path(args.draft)
    t0 = time.time()
    ppu = args.ppu
    SC = 6.0 / ppu
    sheet = (M.XLIM[0], M.XLIM[1], M.YLIM[0] - 10.0, M.YLIM[1])   # the main map's extent, ten units deeper at the south for the far tails
    routes, dropped = map_routes()
    lay = TM.Layout(ppu, routes=routes, sheet=sheet)
    lay.dropped = dropped
    lay.badge_boxes = []
    lay.ambiguous = []
    lay.extra_shapes = []
    w_in = (sheet[1] - sheet[0]) * ppu / 72
    h_in = (sheet[3] - sheet[2]) * ppu / 72
    fig = plt.figure(figsize=(w_in, h_in), facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(sheet[0], sheet[1])
    ax.set_ylim(sheet[2], sheet[3])
    ax.set_facecolor(PAPER)
    ax.set_axis_off()
    faded_nerta(ax, lay, ppu)
    lay.run(sea=M.SEA, passes=args.passes)
    for n in lay.net.notes:
        print("  note:", n)
    for p in dict.fromkeys(lay.problems):
        print("  layout:", p)
    draw_trams(ax, lay, ppu)
    for k, s in lay.stops.items():
        stop_symbol(ax, s["center"], s["r"], snap_dir(s["dir"]), s["kind"] == "transfer", lay.st, ppu)
    for name, ci in CR_TRANSFER.items():   # a transfer capsule out to the commuter rail line, ending in its square
        hit = [s for s in lay.stops.values() if s["name"] == name]
        if not hit:
            continue
        c = hit[0]["center"]
        cr = LineString(rounded(M.CR_PATHS[ci], 3))
        q = cr.interpolate(cr.project(Point(c)))
        q = np.array([q.x, q.y])
        cw = lay.st.R * 2 * ppu
        ax.plot([c[0], q[0]], [c[1], q[1]], color=INK, lw=cw * 0.62, zorder=19.2, solid_capstyle="round")
        ax.plot([c[0], q[0]], [c[1], q[1]], color=WHITE, lw=cw * 0.62 - 1.8, zorder=19.25, solid_capstyle="round")
        d = lay.st.DOT * 1.1
        ax.add_patch(FancyBboxPatch((q[0] - d, q[1] - d), 2 * d, 2 * d, boxstyle="square,pad=0", fc=M.PURPLE, ec="none", zorder=19.3))
        lay.extra_shapes.append(LineString([c, q]).buffer(cw * 0.31 / ppu))
    hb, bottom = header(ax, ppu, sheet[0], sheet[3], args.web)
    kb = key_panel(ax, lay, ppu, sheet[1], sheet[2], len(lay.net.routes), args.web)
    foot = "Map not to scale." if args.web else "Map not to scale. Map data: MBTA. Coastline: US Census."
    ax.text(sheet[1] - 1.5, sheet[2] + 0.6, foot, fontsize=7.2, color=INK, ha="right", va="bottom", zorder=30)
    vt = draw_version(ax, sheet[0], sheet[2], ppu)   # "v1.0", bottom left (Max, November 8). The main session stamps v1.0
    vt.set_visible(args.stamp)                       # itself (tools/release_v1.py), so normal renders keep the corner clear
                                                     # but draw the text only with --stamp.
    fig.canvas.draw()
    _bb = vt.get_window_extent(fig.canvas.get_renderer())
    (_vx0, _vy0), (_vx1, _vy1) = ax.transData.inverted().transform([(_bb.x0, _bb.y0), (_bb.x1, _bb.y1)])
    lay.version_box = box(_vx0, _vy0, _vx1, _vy1)
    hb = hb + [tuple(np.array(lay.version_box.buffer(0.4).bounds))]   # names and badges keep clear of it
    lay.free_boxes = free_tags(ax, lay)
    for i_, fb in enumerate(lay.free_boxes):   # a crop of each FREE tag
        CROPS[f"free{i_ + 1}"] = (fb.centroid.x, fb.centroid.y, 7, 5)
    placer = Placer(ppu, (sheet[0] + 0.5, sheet[1] - 0.5, sheet[2] + 0.5, sheet[3] - 0.5),
                    hb + [kb] + [tuple(np.array(b.buffer(0.25).bounds)) for b in lay.free_boxes])
    for g in lay.extra_shapes:
        placer.soft.append((g, 400.0, "capsule"))
    texts, unlabeled = place_labels(ax, lay, ppu, placer, hb, print)
    bad = check(fig, ax, lay, texts)
    vb = lay.version_box
    for art, k, kind, _c in texts:   # the version mark touches nothing
        bb_ = art.get_window_extent(fig.canvas.get_renderer())
        (a0, b0), (a1, b1) = ax.transData.inverted().transform([(bb_.x0, bb_.y0), (bb_.x1, bb_.y1)])
        if box(a0, b0, a1, b1).intersects(vb):
            bad.append(f"text/version: {art.get_text()}")
    for k, s_ in lay.stops.items():
        if s_["shape"].intersects(vb):
            bad.append(f"dot/version: {s_['name']}")
    for rid, xy in lay.lines.items():
        if len(xy) > 1 and LineString(xy).buffer(lay.st.W).intersects(vb):
            bad.append(f"line/version: {rid}")
    for bb_ in lay.badge_boxes + getattr(lay, "free_boxes", []):
        if bb_.intersects(vb):
            bad.append("pill/version")
    frames = [tuple(h_) for h_ in hb] + [tuple(kb)]
    wm_boxes, wm_obst = watermarks(fig, ax, lay, ppu, sheet, frames)
    for i_, wb in enumerate(wm_boxes):   # a watermark touches only water
        if not M.SEA.contains(wb) or any(o.intersects(wb) for o in wm_obst):
            bad.append(f"watermark/{i_}")
        if i_ < 4:
            CROPS[f"watermark{i_ + 1}"] = (wb.centroid.x, wb.centroid.y, 9, 6)
    print(f"{len(wm_boxes)} @mapzimus watermarks in open water")
    for b in bad:
        print("  overlap:", b)
    print(f"{len(bad)} overlaps among tram labels and symbols")
    for n, why in unlabeled:
        print(f"  unlabeled: {n} ({why})")
    print(f"{len(unlabeled)} stops left unlabeled")
    for n in lay.ambiguous:
        print(f"  name a little nearer a neighbor than its own stop: {n}")
    print(f"{len(lay.ambiguous)} names nearer a neighbor")
    for d in lay.dropped:
        print(f"  left off this map: {d}")
    for a, b, n, f in lay.shrunk:
        print(f"  smaller circles: {a} - {b}, {n} stops, {f:.0%} size")
    OUT.mkdir(parents=True, exist_ok=True)
    stem = args.name or f"tram_map_v{next_version()}"
    png, pdf = OUT / f"{stem}.png", OUT / f"{stem}.pdf"
    for f_ in (png, pdf):
        if f_.exists():
            raise SystemExit(f"refusing to overwrite {f_}")
    plt.rcParams["pdf.fonttype"] = 42
    fig.savefig(png, dpi=args.dpi, facecolor=PAPER)
    fig.savefig(pdf, facecolor=PAPER)
    print("written", png, pdf, f"({w_in:.1f} x {h_in:.1f} in, {ppu} pt per unit) in {time.time() - t0:.0f} s")
    if args.crops:
        for name, (cx, cy, hw, hh) in CROPS.items():
            f_ = OUT / f"{stem}_crop_{name}.png"
            if f_.exists():
                continue
            x0 = (cx - hw - sheet[0]) * ppu / 72
            x1 = (cx + hw - sheet[0]) * ppu / 72
            y0 = (cy - hh - sheet[2]) * ppu / 72
            y1 = (cy + hh - sheet[2]) * ppu / 72
            fig.savefig(f_, dpi=500, facecolor=PAPER, bbox_inches=Bbox([[x0, y0], [x1, y1]]))
            print("crop", f_)


if __name__ == "__main__":
    main()
