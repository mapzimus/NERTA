"""Regional rail map: every NERTA commuter and high-speed line on the real map, drawn to scale.

The companion to the rail line poster (make_rail_poster.py). It reads the poster for the line list, the line colors, which
lines stop where, and the transfer and ferry pills, so the two can't disagree. Geography is real and unbent: NAD83
Massachusetts Mainland (EPSG:26986), with US Census towns for land and coast (as the tram session suggested). Shared track
is drawn as parallel lines, in one fixed order everywhere, so a line keeps its side all the way out.

Inputs, built by two helper scripts (Max asked for several agents, November 7):
  data/rail_regional/lines.geojson     rail_regional_lines.py: MBTA route shapes, and new or revived branches routed over
                                       today's track (OpenStreetMap) or the 1826-1911 railroads, straight only where neither
                                       has track
  data/rail_regional/stations.geojson  rail_regional_stations.py: every station's real spot, with its sources
Until those exist, it falls back to the MBTA shapes and stops alone, for trial renders.

Writes only to output/copies/rail_regional_vN.png and .pdf (or into DIR with --out DIR, at the next version free there)
and never overwrites.
Run: python make_rail_regional.py [version] [--draft DIR] [--out DIR]
With NERTA_WEB=1 (make_tmap.WEB) it draws the nerta.fun version: no release block; "Maxwell Howe" under the NERTA mark
and "@mapzimus" faint at the top right, as on the line posters.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.patheffects as pe  # noqa: E402
import numpy as np  # noqa: E402
import geopandas as gpd  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import FancyBboxPatch, PathPatch, Polygon, Rectangle  # noqa: E402
from matplotlib.transforms import Affine2D  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402
from matplotlib.textpath import TextPath  # noqa: E402
from shapely.geometry import LineString, Point, box, shape  # noqa: E402
from shapely.geometry import Polygon as SPoly  # noqa: E402
from shapely.ops import nearest_points, substring, unary_union  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from nerta_mark import draw_nerta  # noqa: E402
from release_tag import draw_release, release_width  # noqa: E402  (the shared November 8 release block, read only)
import make_tmap as M  # noqa: E402  (read only: colors, icon)
import make_line_poster as LP  # noqa: E402  (read only: roundel, pill tables)
import make_rail_poster as RP  # noqa: E402
from charlie_points import KEY_TEXT as CP_TEXT, draw_cp  # noqa: E402  (the shared Charlie Points coin and Key line, November 8)  (read only: lines, stations, transfers, ferry pills)
from station_kit import INK, WHITE  # noqa: E402

MAP = Path(__file__).resolve().parents[1]
REPO = MAP.parent
DATA = MAP / "data" / "rail_regional"
OUT = MAP / "output" / "copies"
CRS = 26986
FRAME_LL = (-71.98, 41.50, -70.12, 42.92)       # west, south, east, north
CORE_LL = (-71.133, 42.300, -70.990, 42.402)    # the inset: downtown, where the main map is too tight to label (west edge clear of Boston Landing)
INCH_M = 4800.0                                 # meters per inch on the main map, about 1:189,000
INSET_F = 2.9                                   # the inset is this much larger in scale
PAPER, WATER, COAST = M.PAPER, M.WATER, M.COAST
PURPLE, GOLD = RP.PURPLE, RP.GOLD
LW_PT, RIM_PT, CORE_PT, SP_PT = 4.2, 0.85, 1.8, 5.2   # line width, edge color, gold core, spacing between parallel lines (points)
FS, FS_END, FS_HUB, FS_T2 = 7.2, 7.8, 9.6, 8.4
HSR_LINES = ("hmon", "hmai", "halb", "hnyc")
LINE_COST = 0.05   # how much a colored line under a name counts against a spot, next to 1.0 for a dot, pill or name
RINGS = (1.0, 1.9, 3.0, 4.4)  # how far out a name may sit from its stop, in steps of the 2.6-point gap
RING_PEN = 60.0    # square points: one step farther out costs more than a name crossing a line (Max: near and on a line beats far)
HSR_STOPS = {"North Station", "Boston Central", "South Station", "Back Bay", "West Station", "Route 128",   # near Boston
             "Lowell", "Haverhill", "Worcester", "Providence"}   # farther out, as the individual high-speed posters show
HSR_AT = {"Lowell": "hmon", "Haverhill": "hmai", "Worcester": "halb", "Providence": "hnyc"}  # the combined poster draws these apart
# Order across shared track, left to right looking outbound. A line that turns off to the left sits on the left the whole way:
# the Peabody line leaves the Newburyport line westward at Salem, and the Old Colony lines leave South Station east of the
# Back Bay lines (review, November 8: the old order crossed them under the Salem dot and in a knot south of South Station).
RANK = ["fit", "low", "hmon", "hmai", "hav", "pea", "nbp", "grb", "kin", "fr", "hnyc", "pro", "fra", "wor", "halb"]
NORTH = {"fit", "low", "hmon", "hmai", "hav", "nbp"}
WIN_PT = 24.0      # a line eases into or out of its slot over this many points of length
TAPER_PT = 22.0    # lines that start at a hub fan into it over this many points
HUBS = ("North Station", "South Station")
FLYOVER = {("pro", "stoughton")}   # crosses the high-speed line beside it at Canton Junction: drawn over it, with a paper edge
SPUR_ENDS = {"Kingston"}           # on the real map Kingston ends its own short spur; Plymouth trains leave it at Cotley Junction
REGIONAL_LP = {"Lawrence": "pea"}  # the Peabody line's far end gets the line's pill, as on the line posters
NEAR_PT, NEAR_COST = 3.0, 0.5      # a name within this of another name costs a little, so two names don't stack into one
PARK = set(M.PARKING)              # stations with a public garage or lot (make_tmap.PARKING): a P sign beside the name (Max, November 8)
PARK_PT, PARK_GAP = 3.5, 1.0       # the sign's half side (a 7-point square beside the 7.2-point names) and its gap from the name's ink, points
SIDE = {"West Newton": ("N", "S"),  # its name sat between its own dot and Auburndale's (review, November 8)
        "Winchester": ("NE", "E"), "Wedgemere": ("SW", "W"),   # stacked dots: each name level with its own (review of v2)
        "Kingston": ("W", "SW", "S"),   # its name sat right under Plymouth's stop (audit, November 8)
        "Peabody": ("N", "NW", "W"),    # it leaned toward Salem's stop (audit, November 8)
        "Sullivan Sq": ("TOP",),        # inset: the pink line ran between the capsule and its name (audit, November 8)
        "Nantasket Junction": ("N",)}   # its name ran on from Quincy Center's fast-ferry pill in the same row (audit round 2)
NUDGE_PT = {"Montserrat": -2.4}   # points up (+) or down (-): Montserrat's halo bit a notch out of the line end (audit round 2)
WEST = ("W", "NW", "SW")   # left of the stop the row runs outward the other way: line pill, pills, P sign, then the name nearest its stop
WATER_FILE = Path(__file__).resolve().parents[2] / "data" / "shared" / "ne_water.gpkg"   # Census TIGER area water
PLACES = [  # light names for the neighbors and the water, so the real geography reads at a glance (upright, as house style)
    ("NEW HAMPSHIRE", (-71.74, 42.79), "state"), ("RHODE ISLAND", (-71.62, 41.63), "state"), ("CONNECTICUT", (-71.885, 41.62), "state"),
    ("ATLANTIC OCEAN", (-70.38, 42.76), "water"), ("MASSACHUSETTS BAY", (-70.45, 42.53), "water"), ("CAPE COD BAY", (-70.33, 41.90), "water"),
    ("BUZZARDS BAY", (-70.80, 41.57), "water"), ("NARRAGANSETT BAY", (-71.33, 41.60), "water")]

# Fallback only, for trial renders before rail_regional_lines.py has run: today's MBTA shapes, by line.
FALLBACK_SHAPES = {"fit": ("CR-Fitchburg", "Wachusett"), "low": ("CR-Lowell", "Lowell"), "hmon": ("CR-Lowell", "Lowell"),
                   "hav": ("CR-Haverhill", "Haverhill"), "hmai": ("CR-Haverhill", "Haverhill"), "nbp": ("CR-Newburyport", "Newburyport"),
                   "wor": ("CR-Worcester", "Worcester"), "halb": ("CR-Worcester", "Worcester"), "fra": ("CR-Franklin", "Forge Park"),
                   "pro": ("CR-Providence", "Wickford"), "hnyc": ("CR-Providence", "Wickford"), "fr": ("CR-NewBedford", "New Bedford"),
                   "kin": ("CR-Kingston", "- Kingston"), "grb": ("CR-Greenbush", "Greenbush")}
ALIAS = {"Central Sq": "Lynn Interim", "David Ortiz": "Lansdowne", "Winchester": "Winchester Center", "Hingham": "West Hingham",
         "Church St": "Church Street", "Sullivan Sq": "Sullivan Square"}


# ---------------------------------------------------------------------------------------------------------------
# Data
def to_m(gdf):
    return gdf.to_crs(CRS)


def ll(lon, lat):
    """A lon/lat point in map meters."""
    p = gpd.GeoSeries([Point(lon, lat)], crs=4326).to_crs(CRS).iloc[0]
    return (p.x, p.y)


INSET_LL = (-70.62, 42.13)      # lower-left corner of the downtown inset, in Massachusetts Bay, clear of Cape Cod and Marshfield
KEY_LL = (-71.96, 41.97)        # top-left corner of the Key, over Connecticut and Rhode Island, clear of every line
KEY_IN = (3.9, 7.2)             # the Key's room, inches (it draws about 3.8 x 7.05, with the parking and pass-without-stopping rows)


def frame_m():
    w, s, e, n = FRAME_LL
    g = gpd.GeoSeries([box(w, s, e, n).segmentize(0.01)], crs=4326).to_crs(CRS)
    return g.total_bounds  # x0, y0, x1, y1


def load_lines():
    """Pieces as dicts: line, piece, end, sources, geom (meters, outbound)."""
    f = DATA / "lines.geojson"
    if f.exists():
        g = to_m(gpd.read_file(f))
        return [dict(line=r.line, piece=r.piece, end=r.end, sources=r.sources, geom=r.geometry) for r in g.itertuples()], True
    shp = to_m(gpd.read_file(MAP / "data" / "mbta_lines.gpkg"))
    out = []
    for key, (route, pat) in FALLBACK_SHAPES.items():
        m = shp[(shp.route == route) & shp["name"].str.contains(pat)]
        out.append(dict(line=key, piece="main", end="end", sources="MBTA shape (fallback)", geom=m.geometry.iloc[0]))
    return out, False


def load_stations():
    """name -> (point in meters, sources, approx)."""
    f = DATA / "stations.geojson"
    if f.exists():
        g = to_m(gpd.read_file(f))
        return {r.name: (r.geometry, r.sources, bool(r.approx)) for r in g.itertuples()}, True
    stops = to_m(gpd.read_file(MAP / "data" / "mbta_stops.gpkg")).drop_duplicates("name").set_index("name")
    tram = to_m(gpd.read_file(MAP / "data" / "tram" / "stations_real.geojson")).drop_duplicates("name").set_index("name")
    out = {}
    for s in RP.STATIONS:
        n = s["name"]
        k = ALIAS.get(n, n)
        if k in stops.index:
            out[n] = (stops.geometry[k], ["MBTA (fallback)"], False)
        elif n in tram.index:
            out[n] = (tram.geometry[n], ["tram file (fallback)"], True)
    return out, False


# ---------------------------------------------------------------------------------------------------------------
# Parallel lines on shared track
def smooth(a, w):
    if w < 2 or len(a) < 3:
        return a
    k = np.ones(w) / w
    pad = w // 2
    if a.ndim == 1:
        return np.convolve(np.pad(a, pad, mode="edge"), k, mode="same")[pad:-pad or None][:len(a)]
    return np.column_stack([smooth(a[:, i], w) for i in range(a.shape[1])])


def hold(offs, size, h):
    """Give each sample the slot it has in the biggest group within h samples (the nearest such sample). A line then keeps
    its slot through a whole shared stretch and a little past either end, and only eases where it runs alone. Without it a
    short shared run (Salem to South Salem, 1.2 km) never reached full spacing, a line joining another (the Peabody line at
    Lawrence) ran into it before easing out, and a line ending beside another (Wickford Junction) let the other ease back
    under its end ring (review, November 8)."""
    from scipy.ndimage import maximum_filter1d
    big = maximum_filter1d(size, 2 * h + 1, mode="nearest")
    out = offs.copy()
    for k in np.nonzero(big > size)[0]:
        a, b = max(0, k - h), min(len(size), k + h + 1)
        idx = np.nonzero(size[a:b] == big[k])[0] + a
        out[k] = offs[idx[np.argmin(np.abs(idx - k))]]
    return out


def unloop(xy, look=80):
    """Close the little loops a parallel line makes on the inside of a tight curve, where its offset is wider than the
    curve (a swallowtail: the Worcester lines leaving South Station inside the 8-line bundle). Where a segment crosses a
    later one, every point between collapses onto the crossing, so the path keeps its length and its sample index."""
    xy = np.array(xy, float)
    for _ in range(50):
        n = len(xy)
        if n < 4:
            break
        a, b = xy[:-1], xy[1:]
        best = None
        for k in range(2, min(look, n - 1)):
            p, r = a[:-k], b[:-k] - a[:-k]
            q, t2 = a[k:], b[k:] - a[k:]
            den = r[:, 0] * t2[:, 1] - r[:, 1] * t2[:, 0]
            ok = np.abs(den) > 1e-9
            dd = np.where(ok, den, 1.0)
            qp = q - p
            t = (qp[:, 0] * t2[:, 1] - qp[:, 1] * t2[:, 0]) / dd
            u = (qp[:, 0] * r[:, 1] - qp[:, 1] * r[:, 0]) / dd
            hit = np.nonzero(ok & (t > 1e-9) & (t < 1 - 1e-9) & (u > 1e-9) & (u < 1 - 1e-9))[0]
            if len(hit) and (best is None or hit[0] < best[0]):
                i = int(hit[0])
                best = (i, i + k, p[i] + t[i] * r[i])
        if best is None:
            break
        i, j, x = best
        xy[i + 1:j + 1] = x
    return xy


def bundle(pieces, sp, step, share=70.0, win=1600.0, clip=None, hubs=(), taper=0.0):
    """Sample every piece, find which other lines share its track (close and running the same way), and offset it to its
    slot in RANK order, right of travel. A line holds its slot through a shared stretch (see hold) and eases in and out
    over `win` meters where it runs alone. Lines that start at a hub fan into it over `taper` meters."""
    dens = []
    for p in pieces:
        g = p["geom"]
        if clip is not None and not g.intersects(clip):
            continue
        n = max(3, int(g.length // step) + 1)
        d = np.linspace(0, g.length, n)
        pts = np.array([g.interpolate(t).coords[0] for t in d])
        tan = np.gradient(pts, axis=0)
        tan /= np.maximum(np.linalg.norm(tan, axis=1), 1e-9)[:, None]
        dens.append(dict(p, d=d, pts=pts, tan=tan))
    tree = STRtree([x["geom"] for x in dens])
    cosmax = np.cos(np.radians(25))
    w = max(1, int(win / step))
    for x in dens:
        offs = np.zeros(len(x["pts"]))
        size = np.ones(len(x["pts"]), dtype=int)
        for k, q in enumerate(x["pts"]):
            pt = Point(q)
            group = {x["line"]: x["tan"][k]}
            for j in tree.query(pt.buffer(share)):
                y = dens[j]
                if y["line"] in group or y["geom"].distance(pt) > share:
                    continue
                i = min(int(np.searchsorted(y["d"], y["geom"].project(pt))), len(y["d"]) - 1)
                if abs(np.dot(y["tan"][i], x["tan"][k])) < cosmax:  # crossing, not sharing
                    continue
                group[y["line"]] = y["tan"][i]
            g = sorted(group, key=RANK.index)
            # Slots run left to right across the first-ranked line's direction. A line running the other way on the same
            # track counts them from its own side, so the two still sit side by side.
            sign = 1.0 if np.dot(x["tan"][k], group[g[0]]) >= 0 else -1.0
            offs[k] = sign * (g.index(x["line"]) - (len(g) - 1) / 2) * sp
            size[k] = len(g)
        x["off"] = smooth(hold(offs, size, w), w)
        if taper > 0 and any(np.hypot(*(x["pts"][0] - np.asarray(h))) < 1.0 for h in hubs):
            x["off"] = x["off"] * np.clip(x["d"] / taper, 0.0, 1.0)   # fan into the hub circle
        t = smooth(x["tan"], max(1, int(400 / step)))
        t /= np.maximum(np.linalg.norm(t, axis=1), 1e-9)[:, None]
        x["nrm"] = np.column_stack([t[:, 1], -t[:, 0]])
        x["opts"] = unloop(x["pts"] + x["nrm"] * x["off"][:, None])
    return dens


def near_piece(dens, line, p):
    """(distance, piece) for the line's piece nearest p, or None."""
    best = None
    for x in dens:
        if x["line"] != line:
            continue
        dist = x["geom"].distance(p)
        if best is None or dist < best[0]:
            best = (dist, x)
    return best


def dot_on(dens, line, p, far=2500.0):
    """Where a station sits on one line's drawn (offset) path: the sample nearest the station on that line's nearest piece."""
    best = near_piece(dens, line, p)
    if best is None or best[0] > far:
        return None
    x = best[1]
    k = int(np.argmin(np.abs(x["d"] - x["geom"].project(p))))
    return tuple(x["opts"][k])


def square_up(dens, dots, sp):
    """Set a station's dots on one line straight across its bundle, so the capsule runs square to the lines (Hyde Park and
    Ruggles sat askew). A station whose lines run apart (Sullivan Sq) keeps its dots."""
    if len(dots) < 2:
        return dots
    pts = np.array([q for _, q in dots])
    if max(np.hypot(*(a - b)) for a in pts for b in pts) > 1.6 * sp * len(dots):
        return dots
    ln0, q0 = dots[0]
    x0 = near_piece(dens, ln0, Point(q0))[1]
    k = int(np.argmin(np.hypot(*(x0["opts"] - np.asarray(q0)).T)))
    a, b = x0["opts"][max(k - 2, 0)], x0["opts"][min(k + 2, len(x0["opts"]) - 1)]
    v = (b - a) / max(np.hypot(*(b - a)), 1e-9)
    n = np.array([-v[1], v[0]])
    L = 3 * sp * len(dots)
    cross = LineString([tuple(np.asarray(q0) - n * L), tuple(np.asarray(q0) + n * L)])
    out = []
    for ln, q in dots:
        x = near_piece(dens, ln, Point(q))[1]
        hit = cross.intersection(LineString(x["opts"]))
        cand = [g for g in getattr(hit, "geoms", [hit]) if not g.is_empty and g.geom_type == "Point"]
        if cand:
            best = min(cand, key=lambda g: g.distance(Point(q)))
            if best.distance(Point(q)) <= 2.5 * sp:
                q = (best.x, best.y)
        out.append((ln, q))
    return out


# ---------------------------------------------------------------------------------------------------------------
# Drawing helpers (sizes in points; each axes knows its meters per point)
class Sheet:
    def __init__(self, ax, mpp):
        self.ax, self.mpp = ax, mpp
        self.texts, self.lines, self.dots, self.pills = [], [], [], []
        self.blocks = []  # furniture names must keep clear of (inset, Key, header); not part of the checks
        self.serves = {}  # station -> the lines its dot or capsule may touch (None: a hub, every line runs into it)
        self.piece_polys = {}  # (line, piece) -> its stroke
        self.clip = None       # a patch every line stroke is clipped to (main map: all but the downtown box)

    def w(self, text, fs, weight="normal"):
        m = 0
        for line in text.split("\n"):
            m = max(m, TextPath((0, 0), line, size=fs, prop=FontProperties(family="Arial", weight=weight)).get_extents().width)
        return m * self.mpp

    def ink_end(self, text, fs, weight="normal"):
        """Where a left-aligned name's ink ends, from its anchor: w() plus the first letter's side bearing."""
        m = 0
        for line in text.split("\n"):
            m = max(m, TextPath((0, 0), line, size=fs, prop=FontProperties(family="Arial", weight=weight)).get_extents().x1)
        return m * self.mpp

    def txt(self, x, y, s, fs, weight="normal", ha="left", va="center", color=INK, z=11, owner=None, ls=1.0, halo=False):
        """halo: a paper outline, so a name that sits on a colored line still reads (Max, November 8)."""
        t = self.ax.text(x, y, s.replace("'", "’"), fontsize=fs, fontweight=weight, color=color, ha=ha, va=va, zorder=z,
                         linespacing=ls, family="Arial",
                         path_effects=[pe.withStroke(linewidth=3.4, foreground=PAPER)] if halo else None)
        self.texts.append((t, owner))
        return t

    def stroke(self, xy, key, z=4.0, scale=1.0, clip=False):
        lw = LW_PT * scale
        d = RP.LINES[key]
        if d.get("hsr"):
            arts = self.ax.plot(*xy.T, color=PURPLE, lw=lw, solid_capstyle="butt", solid_joinstyle="round", zorder=z + 0.4)
            arts += self.ax.plot(*xy.T, color=GOLD, lw=CORE_PT * scale, solid_capstyle="butt", solid_joinstyle="round", zorder=z + 0.45)
        else:
            arts = self.ax.plot(*xy.T, color=d["hue"], lw=lw, solid_capstyle="butt", solid_joinstyle="round", zorder=z)
            arts += self.ax.plot(*xy.T, color=PURPLE, lw=lw - 2 * RIM_PT * scale, solid_capstyle="butt", solid_joinstyle="round", zorder=z + 0.05)
        if clip and self.clip is not None:
            for a in arts:
                a.set_clip_path(self.clip)

    def pill(self, x0, y, text, fill, fg=WHITE, h_pt=9.6, fs=6.4, ring=None, express=False, z=7):
        h = h_pt * self.mpp
        w = pill_w(self, text, fs, ring=bool(ring), express=express)
        r = h / 2
        self.ax.add_patch(FancyBboxPatch((x0, y - r), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fill, ec=PAPER, lw=0.8, zorder=z))
        if ring or express:
            k, t = (0.9 * self.mpp, 0.8 * self.mpp) if express else (1.0 * self.mpp, 1.3 * self.mpp)
            self.ax.add_patch(FancyBboxPatch((x0 + k, y - r + k), w - 2 * k, h - 2 * k, boxstyle=f"round,pad=0,rounding_size={r - k}",
                                             fc=WHITE if express else ring, ec="none", zorder=z + 0.01))
            k2 = k + t
            self.ax.add_patch(FancyBboxPatch((x0 + k2, y - r + k2), w - 2 * k2, h - 2 * k2, boxstyle=f"round,pad=0,rounding_size={r - k2}",
                                             fc=fill, ec="none", zorder=z + 0.02))
        self.ax.text(x0 + w / 2, y - (0.5 if ring else 0.25) * self.mpp, text, fontsize=fs, fontweight="bold", color=fg, ha="center", va="center", zorder=z + 0.5,
                     family="Arial")
        self.pills.append(box(x0, y - r, x0 + w, y + r))
        return w


def pill_w(sh, text, fs=6.4, ring=False, express=False):
    """A pill's width. A ringed pill gets 3.5 points more, so its letters clear the colored ring (review, November 8)."""
    w = 16.5 * sh.mpp if len(text) <= 3 else sh.w(text, fs, "bold") + (9.5 if ring else 6.0) * sh.mpp
    return w + (4.0 * sh.mpp if express else 0.0)


def code_parts(code, station):
    text = RP.code_text(code, station)
    if code == "F":
        fill, fg, _name, fast = RP.ferry_look(station)
        return text, fill, fg, fast
    return text, LP.PILL[code], INK if code == "YL" else WHITE, False


def pills_width(sh, codes, station):
    tot = 0.0
    for c in codes:
        text, _f, _g, fast = code_parts(c, station)
        tot += pill_w(sh, text, 6.4, express=fast) + 1.0 * sh.mpp
    return tot


def draw_pills(sh, x0, y, codes, station):
    for c in codes:
        text, fill, fg, fast = code_parts(c, station)
        x0 += sh.pill(x0, y, text, fill, fg, express=fast) + 1.0 * sh.mpp
    return x0


# ---------------------------------------------------------------------------------------------------------------
def base(sh, x0, y0, x1, y1):
    """Land from Census towns (used straight, not bent), with Census area water cut back out of it (the towns include their
    rivers, harbors and ponds: the Charles, the Taunton estuary, New Bedford harbor, the Cape Cod Canal), faint town and
    state lines, and the larger rivers."""
    ax = sh.ax
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=WATER, ec="none", zorder=0))  # the sea (an axes switched off draws no background)
    fr = box(x0, y0, x1, y1)
    towns = to_m(gpd.read_file(REPO / "data" / "shared" / "ne_towns.gpkg"))
    towns = towns[towns.intersects(fr.buffer(20000))]
    states = towns.dissolve("STATEFP")
    for g in states.geometry:
        for poly in getattr(g, "geoms", [g]):
            ax.add_patch(Polygon(np.asarray(poly.exterior.coords), closed=True, fc=PAPER, ec=COAST, lw=0.5, zorder=1))
            for hole in poly.interiors:
                ax.add_patch(Polygon(np.asarray(hole.coords), closed=True, fc=WATER, ec=COAST, lw=0.4, zorder=1.01))
    for g in towns.geometry.boundary:
        for part in getattr(g, "geoms", [g]):
            ax.plot(*np.asarray(part.coords).T, color="#ece9e4", lw=0.3, zorder=1.1)
    if WATER_FILE.exists():
        wat = to_m(gpd.read_file(WATER_FILE))
        wat = wat[wat.intersects(fr.buffer(2000))]
        fine = sh.mpp < 40   # the inset shows smaller water
        lo, lake = (0.005, 0.1) if fine else (0.05, 0.6)
        sea = (wat["sea_hops"] >= 0) if "sea_hops" in wat else False   # a "lake" joined to the sea: the lower Mystic is coded as a pond
        keep = ((wat["kind"] != "lake") & (wat["area_km2"] >= lo)) | ((wat["kind"] == "lake") & ((wat["area_km2"] >= lake) | (sea & (wat["area_km2"] >= lo))))
        merged = unary_union(list(wat[keep].geometry)).intersection(fr.buffer(2000))
        for poly in getattr(merged, "geoms", [merged]):
            if poly.geom_type != "Polygon" or poly.is_empty:
                continue
            ax.add_patch(Polygon(np.asarray(poly.exterior.coords), closed=True, fc=WATER, ec="none", zorder=1.12))
            for hole in poly.interiors:   # islands
                ax.add_patch(Polygon(np.asarray(hole.coords), closed=True, fc=PAPER, ec="none", zorder=1.13))
    sl = states.geometry.boundary
    inner = unary_union([a.intersection(b) for i, a in enumerate(sl) for b in list(sl)[i + 1:]])
    for part in getattr(inner, "geoms", [inner]):
        if part.geom_type == "LineString":
            ax.plot(*np.asarray(part.coords).T, color="#b9b4ad", lw=0.7, ls=(0, (4, 2)), zorder=1.2)
    rivers = to_m(gpd.read_file(REPO / "data" / "shared" / "ne_flowlines_order3plus.gpkg"))
    rivers = rivers[(rivers.stream_order >= 5) & rivers.intersects(fr)]
    for r in rivers.itertuples():
        for part in getattr(r.geometry, "geoms", [r.geometry]):
            ax.plot(*np.asarray(part.coords).T, color=WATER, lw=0.5 + 0.35 * (r.stream_order - 5), solid_capstyle="round", zorder=1.15)
    return states


def draw_network(sh, dens, scale=1.0, z=4.0):
    for x in dens:
        over = (x["line"], x["piece"]) in FLYOVER   # drawn above the high-speed lines, in one stroke
        sh.stroke(x["opts"], x["line"], z=4.55 if over else z, scale=scale, clip=True)
        poly = LineString(x["opts"]).buffer(LW_PT * scale * sh.mpp / 2, cap_style=2)
        sh.lines.append((x["line"], poly))
        sh.piece_polys[(x["line"], x["piece"])] = unary_union([sh.piece_polys[(x["line"], x["piece"])], poly]) \
            if (x["line"], x["piece"]) in sh.piece_polys else poly


def arrowhead(sh, xy, z=4.6, chord=None):
    """An arrowhead at the end of a path. chord: aim it along the last `chord` meters, so a last little bend (the Cape line
    coming off the canal bridge) doesn't turn it."""
    b = np.asarray(xy[-1], float)
    if chord:
        ls = LineString(xy)
        a = np.asarray(ls.interpolate(max(0.0, ls.length - chord)).coords[0])
    else:
        a = np.asarray(xy[-6], float)
    v = (b - a) / max(np.hypot(*(b - a)), 1e-9)
    n = np.array([-v[1], v[0]])
    L, H = 7.0 * sh.mpp, 4.4 * sh.mpp
    tip = b + v * L
    tri = [tuple(tip), tuple(b - n * H), tuple(b + n * H)]
    sh.ax.add_patch(Polygon(tri, closed=True, fc=PURPLE, ec="none", zorder=z))
    sh.lines.append(("arrowhead", SPoly(tri)))
    return tip, v


def flyovers(sh, cl, scale):
    """Where a branch crosses a high-speed line it doesn't share (the Stoughton branch at Canton Junction), draw it over
    that line with a paper edge, so it reads as a crossing, not a join (review, November 8)."""
    hs = [ln for k, ln in sh.lines if k in HSR_LINES]
    if not hs:
        return
    hs = unary_union(hs).buffer(1.5 * sh.mpp * scale)
    for x in cl:
        if (x["line"], x["piece"]) not in FLYOVER:
            continue
        cross = LineString(x["opts"]).intersection(hs)
        for part in getattr(cross, "geoms", [cross]):
            if part.is_empty or part.geom_type != "LineString" or part.length < 1.0:
                continue
            xy = np.asarray(part.coords)
            host = sh.piece_polys.get((x["line"], "main"))   # the line it leaves: the paper edge stays off it
            band = part.buffer((LW_PT + 2.4) * scale * sh.mpp / 2, cap_style=2)
            if host is not None:
                band = band.difference(host.buffer(0.3 * sh.mpp))
            for poly in getattr(band, "geoms", [band]):
                if poly.geom_type == "Polygon" and not poly.is_empty:
                    sh.ax.add_patch(Polygon(np.asarray(poly.exterior.coords), closed=True, fc=PAPER, ec="none", zorder=4.5))


def fit_ends(pieces, pos):
    """Join line ends to their stations. Lines from North and South Station start at the hub's own point (the MBTA shapes
    stop at the platforms, a few hundred meters out, so the lines stopped short of the hub circles), and a line that ends
    at a station stops at it: cut where the track runs on past (Taunton), or carried straight on when the track stops a
    little short (700 m at most)."""
    ends = {}
    for st in RP.STATIONS:
        if st["kind"] == "end" or st["name"] in SPUR_ENDS:
            for ln in stop_lines(st):
                if ln not in HSR_LINES:
                    ends.setdefault(ln, []).append(st["name"])
    out = []
    for p in pieces:
        c = list(p["geom"].coords)
        for h in HUBS:
            if h in pos and 5.0 < Point(c[0]).distance(pos[h][0]) < 1200.0:
                c = [(pos[h][0].x, pos[h][0].y)] + c
        g = LineString(c)
        if p["end"] == "end":
            for name in ends.get(p["line"], []):
                if name not in pos or Point(c[-1]).distance(pos[name][0]) > 1500.0:
                    continue
                q = pos[name][0]
                t = g.project(q)
                if t >= g.length - 1.0:
                    if 5.0 < Point(c[-1]).distance(q) <= 700.0:
                        g = LineString(c + [(q.x, q.y)])
                elif g.length - t > 5.0:
                    g = substring(g, 0.0, t)
        out.append(dict(p, geom=g))
    return out


def clear_of(sh, q, r, own, most=2.5, paths=(), slide_gap=1.5, slide_most=6.0):
    """Keep a dot of radius r off every line it doesn't serve, so it can't read as a stop on that line. First slide it
    along its own drawn line, up to `slide_most` points either way, to a spot `slide_gap` points clear (Salem sat inside
    the Peabody line's bend: review of v2). Where that can't work (a line running alongside all the way), nudge it
    sideways by at most `most` points (an end ring beside a high-speed line: Wickford Junction, Mansfield)."""
    q0 = np.asarray(q, float)
    near = [ln for key, ln in sh.lines if key not in own and key not in ("arrowhead", "dig")
            and ln.intersects(Point(q0).buffer(r + (slide_gap + slide_most + 2) * sh.mpp))]
    if paths and near:
        need = r + slide_gap * sh.mpp
        if min(ln.distance(Point(q0)) for ln in near) < need:
            path = min(paths, key=lambda pth: pth.distance(Point(q0)))
            s0 = path.project(Point(q0))
            for k in range(1, int(slide_most / 0.5) + 1):
                for sgn in (1, -1):
                    s1 = s0 + sgn * k * 0.5 * sh.mpp
                    if not 0 <= s1 <= path.length:
                        continue
                    c1 = path.interpolate(s1)
                    if all(ln.distance(c1) >= need for ln in near):
                        return np.array([c1.x, c1.y])
    c = q0.copy()
    for _ in range(4):
        moved = False
        for key, ln in sh.lines:
            if key in own or key in ("arrowhead", "dig"):
                continue
            dd = ln.distance(Point(c))
            need = r + 0.4 * sh.mpp
            if 0 < dd < need:
                a, _b = nearest_points(ln, Point(c))
                v = c - np.array([a.x, a.y])
                c = c + v / np.hypot(*v) * (need - dd)
                moved = True
        if not moved:
            break
    return c if np.hypot(*(c - q0)) <= most * sh.mpp else q0


def wheel_icon(sh, x, y, a_pt=3.6, z=12):
    """The blue accessible-station square, sized in points (make_tmap.icon draws in poster units, too small here)."""
    a = a_pt * sh.mpp
    sh.ax.add_patch(FancyBboxPatch((x - a, y - a), 2 * a, 2 * a, boxstyle=f"round,pad=0,rounding_size={0.3 * a}", fc="#165c96",
                                   ec="none", zorder=z))
    k = a / 0.85
    sh.ax.add_patch(PathPatch(Affine2D().scale(k).translate(x, y - 0.03 * k).transform_path(M.WHEEL), fc=WHITE, ec="none", zorder=z + 0.1))


def park_sign(sh, x, y, a_pt=PARK_PT, z=11.6):
    """The parking sign centered on (x, y), sized in points: make_tmap.parking_icon's rounded square in parking blue with a
    bold white P, every part scaled together, as make_line_poster.park does at poster scale. Over the names (z 11), so the
    name's paper halo can't nick it. It counts as a pill: the checks keep it off lines, pills and names."""
    a = a_pt * sh.mpp
    s = a_pt / (0.78 * LP.MAP_PPU)   # make_tmap's sign: a 0.78-unit half side at the main map's points per unit
    sh.ax.add_patch(FancyBboxPatch((x - a, y - a), 2 * a, 2 * a, boxstyle=f"round,pad=0,rounding_size={a * 0.3}", fc=M.PARK_BLUE,
                                   ec=WHITE, lw=0.6 * s, zorder=z))
    sh.ax.text(x, y - a * 0.06, "P", fontsize=0.78 * 9.0 * s, fontweight="bold", color=WHITE, ha="center", va="center", zorder=z + 0.1,
               family="Arial")
    sh.pills.append(box(x - a, y - a, x + a, y + a))


def places(sh):
    """Names for the neighbor states and the water, light and upright, kept out of the way of station names."""
    for text, (lon, lat), kind in PLACES:
        x, y = ll(lon, lat)
        t = "   ".join(" ".join(word) for word in text.split())
        fs, col, wt = (9.6, "#a39d95", "bold") if kind == "state" else (8.6, "#4f97a5", "normal")
        sh.txt(x, y, t, fs, wt, "center", "center", color=col, z=2)
        w = sh.w(t, fs, wt)
        sh.blocks.append(box(x - w / 2 - 2 * sh.mpp, y - fs * 0.7 * sh.mpp, x + w / 2 + 2 * sh.mpp, y + fs * 0.7 * sh.mpp))


def clip_to(dens, fr):
    """Cut every drawn path at the frame. Paths that leave it get an arrowhead there."""
    out = []
    for x in dens:
        ls = LineString(x["opts"])
        inside = ls.intersection(fr)
        if inside.is_empty:
            continue
        parts = list(getattr(inside, "geoms", [inside]))
        part = max(parts, key=lambda g: g.length) if x["end"] == "runs_on" else parts[0]
        if len(parts) > 1 and x["end"] != "runs_on":
            part = unary_union(parts) if False else max(parts, key=lambda g: g.length)
        out.append(dict(x, opts=np.asarray(part.coords), cut=part.length < ls.length - 1.0))
    return out


# ---------------------------------------------------------------------------------------------------------------
def stop_lines(s):
    """The lines that stop at a poster station: high-speed lines only at their six stops; Lawrence also ends the Peabody line."""
    lines = []
    for ln, _xy in s["dots"]:
        if (ln in HSR_LINES and s["name"] not in HSR_STOPS) or ln in lines:
            continue
        lines.append(ln)
    if s["name"] in HSR_AT and HSR_AT[s["name"]] not in lines:
        lines.append(HSR_AT[s["name"]])
    if s["name"] == "Lawrence" and "pea" not in lines:
        lines.append("pea")  # the Peabody line ends at Lawrence on the real map
    return lines


LINE_TITLES = {"fit": "Fitchburg Line", "low": "Lowell Line", "hav": "Haverhill Line", "nbp": "Newburyport/Rockport Line",
               "pea": "Peabody Line", "wor": "Framingham/Worcester Line", "fra": "Franklin Line", "pro": "Providence Line",
               "fr": "Fall River/New Bedford Line", "kin": "Kingston Line", "grb": "Greenbush Line",
               "hmon": "High-Speed Rail to Concord NH and Montreal", "hmai": "High-Speed Rail to Bangor",
               "halb": "High-Speed Rail to Albany and Chicago", "hnyc": "High-Speed Rail to New York and Washington"}


def export_layers():
    """The shared rail layer for the tram session's web map and nerta.fun (WGS84): cr_lines.geojson and cr_stations.geojson.
    Built from the two helper files plus the poster's own line and stop data, so every map reads the same thing."""
    raw = json.loads((DATA / "lines.geojson").read_text(encoding="utf-8"))
    feats = []
    for f in raw["features"]:
        p = f["properties"]
        hsr = p["line"] in HSR_LINES
        feats.append(dict(type="Feature", geometry=f["geometry"], properties=dict(
            line=p["line"], name=LINE_TITLES[p["line"]], piece=p.get("piece", "main"), kind="hsr" if hsr else "commuter", color=PURPLE,
            edge=GOLD if hsr else RP.LINES[p["line"]]["hue"], end=p.get("end", "end"), sources=p.get("sources", ""))))
    (DATA / "cr_lines.geojson").write_text(json.dumps(dict(type="FeatureCollection", features=feats)), encoding="utf-8")
    raw = json.loads((DATA / "stations.geojson").read_text(encoding="utf-8"))
    spot = {f["properties"]["name"]: f for f in raw["features"]}
    feats = []
    seen = set()
    for s in RP.STATIONS + ([dict(name="Lawrence", dots=[("hav", None)], kind="stop")] if not any(x["name"] == "Lawrence" for x in RP.STATIONS) else []):
        f = spot.get(s["name"])
        if f is None or s["name"] in seen:
            continue
        seen.add(s["name"])
        p = f["properties"]
        lines = stop_lines(s)
        agree = p.get("agree_m")
        feats.append(dict(type="Feature", geometry=f["geometry"], properties=dict(
            name=s["name"], lines=lines, hsr=s["name"] in HSR_STOPS, kind="stop" if s["kind"] == "pass" else s["kind"],
            status=p.get("status"), sources=p.get("sources"), verified=bool(agree is not None and agree <= 150),
            approx=bool(p.get("approx")), mbta_name=p.get("mbta_name"))))
    (DATA / "cr_stations.geojson").write_text(json.dumps(dict(type="FeatureCollection", features=feats)), encoding="utf-8")
    print(f"exported cr_lines.geojson ({len(json.loads((DATA / 'cr_lines.geojson').read_text())['features'])} pieces) and "
          f"cr_stations.geojson ({len(feats)} stations)")


def station_table(dens, pos, sp):
    """Every poster station with its drawn dots: which lines stop, and where each line's dot is. On this map Kingston ends
    its own spur, and every end station carries its line's pill (Marlborough, Newburyport, Taunton and Fall River Depot had
    none), as does Lawrence, the Peabody line's far end."""
    rows = []
    for s in RP.STATIONS:
        name = s["name"]
        if name not in pos:
            print("  no position:", name)
            continue
        p = pos[name][0]
        lines = stop_lines(s)
        dots = [(ln, dot_on(dens, ln, p)) for ln in lines]
        dots = square_up(dens, [(ln, q) for ln, q in dots if q is not None], sp)
        kind = "end" if name in SPUR_ENDS else s["kind"]
        lp = REGIONAL_LP.get(name, s["lp"])
        if lp is None and kind == "end":
            cr = [ln for ln in lines if ln not in HSR_LINES]
            lp = cr[0] if len(cr) == 1 else None
        rows.append(dict(name=name, kind=kind, lp=lp, p=(p.x, p.y), dots=dots))
    if "Lawrence" not in [r["name"] for r in rows] and "Lawrence" in pos:
        p = pos["Lawrence"][0]
        dots = [(ln, dot_on(dens, ln, p)) for ln in ("hav", "pea")]
        rows.append(dict(name="Lawrence", kind="stop", lp="pea", p=(p.x, p.y), dots=[(a, b) for a, b in dots if b is not None]))
    return rows


def draw_station(sh, st, codes, scale=1.0, hub_scale=1.0, paths=None):
    dots = [q for _, q in st["dots"]]
    if not dots:
        return None
    mpp = sh.mpp
    owner = st["name"]
    own = {ln for ln, _ in st["dots"]}
    spread = max(np.hypot(a[0] - b[0], a[1] - b[1]) for a in dots for b in dots)
    if st["kind"] == "hub":
        q = np.asarray(st["p"])
        r = 6.2 * mpp * hub_scale
        sh.ax.add_patch(plt.Circle(q, r, fc=WHITE, ec=INK, lw=2.0 * hub_scale, zorder=6))
        geom = Point(q).buffer(r + 1.0 * mpp * hub_scale)
        sh.serves[owner] = None   # every line runs into a hub
    elif len(dots) > 1 and spread > 1.5 * mpp:
        # capsule across the parallel lines: from the outermost dot to the outermost dot
        a, b = max(((a, b) for a in dots for b in dots), key=lambda ab: np.hypot(ab[0][0] - ab[1][0], ab[0][1] - ab[1][1]))
        lw = LW_PT * 1.45 * scale
        thru = {k for k, ln in sh.lines if k in HSR_LINES and k not in own and ln.intersects(LineString([a, b]))}
        a, b = np.asarray(a, float), np.asarray(b, float)
        foreign = [ln for k, ln in sh.lines if k not in own and k not in thru and k not in ("arrowhead", "dig")]
        for _ in range(12):   # pull an end back while its round cap touches a line the station doesn't serve
            cap = LineString([a, b]).buffer(lw * mpp / 2 + 1.0 * mpp)   # keep a point of paper
            hit = [ln for ln in foreign if ln.intersection(cap).area > (0.2 * mpp) ** 2]
            if not hit or np.hypot(*(b - a)) < 2 * mpp:
                break
            v = (b - a) / np.hypot(*(b - a))
            if min(Point(a).distance(ln) for ln in hit) <= min(Point(b).distance(ln) for ln in hit):
                a = a + v * 0.3 * mpp
            else:
                b = b - v * 0.3 * mpp
        seg = LineString([a, b])
        if thru:   # high-speed trains pass without stopping: two platform dots and a thin link under the gold lines, as on the posters
            d_, lw_ = LW_PT * 1.25 * scale, 1.2 * scale
            sh.ax.plot(*seg.xy, color=INK, lw=1.4 * scale, solid_capstyle="round", zorder=4.2)
            for q in (a, b):
                sh.ax.scatter(*q, s=d_ ** 2, color=WHITE, edgecolor=INK, lw=lw_, zorder=6)
            geom = seg.buffer((d_ / 2 + lw_ / 2) * mpp)
        else:
            sh.ax.plot(*seg.xy, color=INK, lw=lw, solid_capstyle="round", zorder=5)
            sh.ax.plot(*seg.xy, color=WHITE, lw=lw * 0.6, solid_capstyle="round", zorder=5.01)
            geom = seg.buffer(lw * mpp / 2)
        sh.serves[owner] = own | thru
    else:
        if st["kind"] == "end":
            d, ec, lw = LW_PT * 1.45, PURPLE, 1.5
        elif codes or len(dots) > 1:
            d, ec, lw = LW_PT * 1.25, INK, 1.2
        else:
            d, ec, lw = LW_PT * 0.85, INK, 0.6
        d, lw = d * scale, lw * scale
        own_paths = [pth for ln in own for pth in (paths or {}).get(ln, [])]
        q = clear_of(sh, dots[0], (d / 2 + lw / 2) * mpp, own, paths=own_paths)
        sh.ax.scatter(*q, s=d ** 2, color=WHITE, edgecolor=ec, lw=lw, zorder=6)
        geom = Point(q).buffer((d / 2 + lw / 2) * mpp)
        sh.serves[owner] = own
    sh.dots.append((owner, geom))
    return geom


def place_label(sh, st, geom, codes, blocked, scale=1.0):
    """Try level spots around the station, nearest first; keep the first that clears lines, dots, pills and names.
    A name always sits next to its stop. Right of the stop (and above or below it) the row reads name, P sign, pills, line
    pill. Left of it (WEST) the row runs outward the other way, "[FRAMINGHAM / WORCESTER LINE] WORCESTER o": drawn name
    first, the pills sat between the name and its stop, and WORCESTER ended about 115 points from it (audit, November 8)."""
    kind = st["kind"]
    name = st["name"]
    text = RP.TEXT.get(name, name)
    if kind == "hub":
        fs, weight, text = FS_HUB * scale ** 0.3, "bold", text.upper()
    elif kind == "tier2":
        fs, weight, text = FS_T2 * scale ** 0.3, "bold", text.upper()
    elif kind == "end":
        fs, weight, text = FS_END * scale ** 0.3, "bold", text.upper()
    else:
        fs, weight = FS * scale ** 0.3, "normal"
    mpp = sh.mpp
    tw = sh.w(text, fs, weight)
    th = fs * 1.2 * mpp * (text.count("\n") + 1)
    pw = pills_width(sh, codes, name) if codes else 0.0
    lpw = (pill_w(sh, RP.LINES[st["lp"]]["name"], 5.8, ring=True) + 2.5 * mpp) if st.get("lp") else 0.0
    # A parking station's P sign sits right beside the name, PARK_GAP clear of its ink, between the name and the pills. Its
    # room is part of every spot scored, on the pill side: like a pill, it may not sit on a line.
    pk = sh.ink_end(text, fs, weight) - tw + (PARK_GAP + 2 * PARK_PT) * mpp if name in PARK else 0.0
    total = tw + pk + (2.5 * mpp + pw if codes else 0) + lpw
    gx0, gy0, gx1, gy1 = geom.bounds
    cx, cy = (gx0 + gx1) / 2, (gy0 + gy1) / 2
    top_x = max(geom.exterior.coords, key=lambda c: c[1])[0]   # the stop's highest point: a slanted capsule's top end
    cands = []
    for ring in RINGS:  # nearest first; farther rings only when the near ones are taken
        gap = 2.6 * mpp * ring
        for side in SIDE.get(name, ("E", "W", "NE", "SE", "NW", "SW", "N", "S")):
            for dy in ((0.0, 0.6 * th, -0.6 * th) if side in ("E", "W") and name not in SIDE else (0.0,)):
                if side == "E":
                    x0, y = gx1 + gap, cy + dy
                elif side == "W":
                    x0, y = gx0 - gap - total, cy + dy
                elif side == "NE":
                    x0, y = gx1 + gap * 0.6, gy1 + th / 2 + gap * 0.3
                elif side == "SE":
                    x0, y = gx1 + gap * 0.6, gy0 - th / 2 - gap * 0.3
                elif side == "NW":
                    x0, y = gx0 - gap * 0.6 - total, gy1 + th / 2 + gap * 0.3
                elif side == "SW":
                    x0, y = gx0 - gap * 0.6 - total, gy0 - th / 2 - gap * 0.3
                elif side == "N":
                    x0, y = cx - total / 2, gy1 + gap + th / 2
                elif side == "TOP":   # above the stop, the name starting right over its top end, reading away from it
                    x0, y = top_x - gap, gy1 + gap + th / 2
                else:
                    x0, y = cx - total / 2, gy0 - gap - th / 2
                y += NUDGE_PT.get(name, 0.0) * mpp
                cands.append((side, x0, y, box(x0, y - th / 2, x0 + total, y + th / 2), ring, len(cands)))
    others = [d for n, d in sh.dots if n != name]

    def score(side, bx, ring, order):
        """Lower is better. Max (November 8): "id prefer overlapping the color before putting the text confusingly far away".
        So a name may sit on a colored line (a small cost), but each step farther from its stop costs more than that.
        Touching a dot, pill, name, the furniture or the sheet edge, or sitting nearer another stop's dot, is ruled out.
        Nearness is measured on the name where it is drawn: the box's right-hand end on a WEST side, its left-hand end elsewhere."""
        hard = soft = 0.0
        tx0, ty0, tx1, ty1 = bx.bounds
        if side in WEST:   # the name itself may sit on a line, its P sign and pills may not
            text_part, pill_part = box(tx1 - tw, ty0, tx1, ty1), box(tx0, ty0, tx1 - tw, ty1)
        else:
            text_part, pill_part = box(tx0, ty0, tx0 + tw, ty1), box(tx0 + tw, ty0, tx1, ty1)
        for g, kind_ in blocked(bx):
            if kind_ == "line":
                soft += g.intersection(text_part).area / mpp ** 2 * LINE_COST
                hard += g.intersection(pill_part).area / mpp ** 2
            elif kind_ == "near":
                soft += g.intersection(bx).area / mpp ** 2 * NEAR_COST
            else:
                hard += g.intersection(bx).area / mpp ** 2
        own = geom.distance(text_part)
        near = min((d.distance(text_part) for d in others), default=1e12)
        doubt = max(0.0, own * 1.5 + 1.0 * mpp - near) / mpp * 4.0  # another stop almost as near as this one: confusing
        return hard * 1e6 + (1e9 if near + 0.4 * mpp < own else 0) + soft + doubt + RINGS.index(ring) * RING_PEN + order * 0.01
    best = min(cands, key=lambda c: score(c[0], c[3], c[4], c[5]))
    side, x0, y, bx = best[:4]
    lp = RP.LINES[st["lp"]] if st.get("lp") else None
    if side in WEST:   # from the stop outward, leftward: the name (ending one gap from its stop), P sign, pills, line pill
        x = x0 + total
        sh.txt(x, y - 0.3 * mpp, text, fs, weight, "right", "center", owner=name, halo=True)
        x -= tw + pk
        if pk:
            park_sign(sh, x + PARK_PT * mpp, y)
        if codes:
            x -= 2.5 * mpp + pw
            draw_pills(sh, x + 1.0 * mpp, y, codes, name)   # still in house order, left to right
        if lp:
            sh.pill(x - 1.5 * mpp - pill_w(sh, lp["name"], 5.8, ring=True), y, lp["name"], PURPLE, WHITE, h_pt=9.2, fs=5.8,
                    ring=lp["hue"], z=7.5)
        return bx
    sh.txt(x0, y - 0.3 * mpp, text, fs, weight, "left", "center", owner=name, halo=True)
    x = x0 + tw
    if pk:
        park_sign(sh, x + pk - PARK_PT * mpp, y)
        x += pk
    if codes:
        x = draw_pills(sh, x + 2.5 * mpp, y, codes, name)
    if lp:
        sh.pill(x + 1.5 * mpp, y, lp["name"], PURPLE, WHITE, h_pt=9.2, fs=5.8, ring=lp["hue"], z=7.5)
    return bx


# ---------------------------------------------------------------------------------------------------------------
def check(fig, sh):
    """Same checks as the poster: text on text, lines, dots and pills; pills on lines; every name nearest its own dot."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = sh.ax.transData.inverted()
    bad, shapes, on_line = [], [], []
    lim = box(*sh.ax.get_xlim()[:1], sh.ax.get_ylim()[0], sh.ax.get_xlim()[1], sh.ax.get_ylim()[1])
    for t, owner in sh.texts:
        if t.get_rotation() != 0:
            bad.append("TILTED " + t.get_text())
        bb = t.get_window_extent(rend)
        (a, b), (c, d) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        pad = 0.3 * sh.mpp
        shapes.append((t.get_text().replace("\n", " ")[:28], box(a, b + pad, c, d - pad), owner))
    for i, (a, sa, oa) in enumerate(shapes):
        if not lim.contains(sa):
            bad.append(f"off the sheet: {a}")
        for b, sb, _ob in shapes[i + 1:]:
            if sa.intersects(sb):
                bad.append(f"text/text: {a} | {b}")
        for key, ln in sh.lines:
            if sa.intersection(ln).area > (0.4 * sh.mpp) ** 2:
                on_line.append(f"{a} | {key}")  # allowed (Max, November 8), counted apart
        for n, d in sh.dots:
            if sa.intersection(d).area > (0.4 * sh.mpp) ** 2:
                bad.append(f"text/dot: {a} | {n}")
        for pb in sh.pills:
            if sa.intersection(pb).area > (0.4 * sh.mpp) ** 2 and not sa.within(pb.buffer(0.2 * sh.mpp)):
                bad.append(f"text/pill: {a}")
        if oa and any(n == oa for n, _ in sh.dots):
            own = min(d.distance(sa) for n, d in sh.dots if n == oa)
            for n, d in sh.dots:
                if n != oa and d.distance(sa) + 0.2 * sh.mpp < own:
                    bad.append(f"nearer dot: {a} is nearer {n}")
                    break
    if on_line:
        print(f"  ({len(on_line)} names sit on a colored line, allowed: " + "; ".join(on_line[:6]) + ("..." if len(on_line) > 6 else "") + ")")
    for n, d in sh.dots:   # a dot on a line it doesn't serve reads as a stop on that line (review, November 8)
        ok = sh.serves.get(n, set())
        if ok is None:
            continue
        for key, ln in sh.lines:
            if key not in ok and key not in ("arrowhead", "dig") and d.intersection(ln).area > (0.3 * sh.mpp) ** 2:
                bad.append(f"dot/line: {n} touches {key}")
                break
    for k, pb in enumerate(sh.pills):
        for key, ln in sh.lines:
            if pb.intersection(ln).area > (0.6 * sh.mpp) ** 2:
                bad.append(f"pill/line: {key} at {[round(v) for v in pb.bounds[:2]]}")
                break
        for pc in sh.pills[k + 1:]:
            if pb.intersection(pc).area > (0.4 * sh.mpp) ** 2:
                bad.append(f"pill/pill at {[round(v) for v in pb.bounds[:2]]}")
    return bad


def dig(sh, pos, scale=1.0):
    """The BIGGER Dig under Atlantic Ave: black casing, white local tracks outside, gold express tracks inside."""
    names = ("North Station", "Boston Central", "South Station")
    if not all(n in pos for n in names):
        return
    pts = np.array([(pos[n][0].x, pos[n][0].y) for n in names])
    lw = LW_PT * 2.2 * scale
    sh.ax.plot(*pts.T, color=INK, lw=lw, solid_capstyle="round", solid_joinstyle="round", zorder=5.5)
    for a, b in zip(pts, pts[1:]):
        v = (b - a) / np.hypot(*(b - a))
        n = np.array([-v[1], v[0]])
        for off, col in ((-1.55, WHITE), (-0.55, GOLD), (0.55, GOLD), (1.55, WHITE)):
            o = n * off * scale * sh.mpp
            sh.ax.plot([a[0] + o[0], b[0] + o[0]], [a[1] + o[1], b[1] + o[1]], color=col, lw=0.8 * scale, solid_capstyle="butt", zorder=5.6)
    sh.lines.append(("dig", LineString(pts).buffer(lw * sh.mpp / 2)))


def inset(fig, main, pieces, pos, codes, at):
    """Downtown at a larger scale, set in open water, with its own 1-mile bar. `at`: lower-left corner on the main map, in meters."""
    cx0, cy0, cx1, cy1 = gpd.GeoSeries([box(*CORE_LL)], crs=4326).to_crs(CRS).total_bounds
    X0, X1 = main.ax.get_xlim()
    Y0, Y1 = main.ax.get_ylim()
    w, h = (cx1 - cx0) * INSET_F, (cy1 - cy0) * INSET_F
    ix0, iy0 = at
    main.ax.add_patch(Rectangle((ix0, iy0), w, h, fc=PAPER, ec=INK, lw=1.2, zorder=20))
    main.blocks.append(box(ix0, iy0, ix0 + w, iy0 + h))
    ax2 = fig.add_axes([(ix0 - X0) / (X1 - X0), (iy0 - Y0) / (Y1 - Y0), w / (X1 - X0), h / (Y1 - Y0)], zorder=21)
    ax2.set_xlim(cx0, cx1)
    ax2.set_ylim(cy0, cy1)
    ax2.set_aspect("equal")
    ax2.set_axis_off()
    sh2 = Sheet(ax2, INCH_M / INSET_F / 72)
    base(sh2, cx0, cy0, cx1, cy1)
    core = box(cx0, cy0, cx1, cy1)
    mi = 1609.344
    bx0, by = cx1 - 12 * sh2.mpp - mi, cy0 + 10 * sh2.mpp
    sh2.blocks += [box(bx0 - 4 * sh2.mpp, by - 4 * sh2.mpp, bx0 + mi + 16 * sh2.mpp, by + 16 * sh2.mpp),
                   box(cx0, cy1 - 18 * sh2.mpp, cx0 + 80 * sh2.mpp, cy1)]   # the bar, and the DOWNTOWN title
    dig(sh2, pos)  # before the names, so they keep clear of it
    draw_map(sh2, pieces, pos, codes, core, SP_PT * sh2.mpp, 25.0)
    sh2.txt(cx0 + 6 * sh2.mpp, cy1 - 6 * sh2.mpp, "DOWNTOWN", 9.6, "bold", "left", "top")
    scale_bar(sh2, bx0, by, [(0, "0"), (0.5, "1/2"), (1, "1 mile")])
    ax2.add_patch(Rectangle((cx0, cy0), cx1 - cx0, cy1 - cy0, fc="none", ec=INK, lw=1.2, zorder=30))
    return sh2


def scale_bar(sh, x, y, marks):
    """A bar of alternating black and white steps, 3 points tall, with a label at every step: marks are (miles, label)."""
    mi = 1609.344
    for i, ((a, _la), (b, _lb)) in enumerate(zip(marks, marks[1:])):
        sh.ax.add_patch(Rectangle((x + a * mi, y), (b - a) * mi, 3.0 * sh.mpp, fc=INK if i % 2 == 0 else PAPER, ec=INK, lw=0.5, zorder=12))
    for k, label in marks:
        sh.txt(x + k * mi, y + 4.6 * sh.mpp, label, 6.4, "normal", "center", "bottom")


class _NoDraw:
    """Stands in for the axes where the release block is measured but not drawn (the web version)."""
    def text(self, *args, **kwargs):
        return None


def header(sh, x0, y1, x1):
    """The T and NERTA mark, the title, and the release block, as on the posters, 15% larger than first drawn (the title
    was small for the sheet). Returns the boxes names must keep clear of: the title block and the release block, not the
    whole top band, so the words at the top-edge arrows can sit between them.
    Web version (make_tmap.WEB): no release block. Its room stays clear, so every name sits where it does on the posted map."""
    u = 6.2 * sh.mpp                 # one header unit: the posters' 5.4 points, 15% larger
    hy = y1 - 11 * u
    RP.nerta_roundel(sh.ax, x0 + 10 * u, hy, 6.4 * u)   # the multicolor T and NERTA pill, as on every map (November 8)
    nb = draw_nerta(sh.ax, x0 + 10 * u, hy - (6.4 + 3.2 / 5.4 / 2) * u - 0.8 * u, 2 * (6.4 + 3.2 / 5.4 / 2) * u, "B", colors=M.NERTA_COLORS)
    sh.ax.add_patch(FancyBboxPatch((x0 + 20 * u, hy - 6 * u), 28 * u, 12 * u, boxstyle=f"round,pad=0,rounding_size={6 * u}", fc=PURPLE, ec="none", zorder=12))
    for k, col in ((0.9, GOLD), (1.9, PURPLE)):
        sh.ax.add_patch(FancyBboxPatch((x0 + (20 + k) * u, hy - (6 - k) * u), (28 - 2 * k) * u, (12 - 2 * k) * u,
                                       boxstyle=f"round,pad=0,rounding_size={(6 - k) * u}", fc=col, ec="none", zorder=12.1 + k / 10))
    sh.ax.text(x0 + 34 * u, hy - 0.4 * u, "CR", fontsize=39, fontweight="bold", color=WHITE, ha="center", va="center", zorder=13)
    title, sub_ = "Regional Rail", "Commuter and high-speed rail, drawn to scale"
    sh.ax.text(x0 + 52 * u, hy + 1.2 * u, title, fontsize=31, fontweight="bold", color=INK, ha="left", va="center", zorder=13)
    sh.ax.text(x0 + 52.4 * u, hy - 5.2 * u, sub_, fontsize=12, color=INK, ha="left", va="center", zorder=13)
    title_r = x0 + 52.4 * u + max(sh.w(title, 31, "bold"), sh.w(sub_, 12))
    if RP.NO_DISCLAIMER:   # the "_no-disclaimer" final (Max, November 8): one note under the NERTA logo, scaled like the header
        sh.ax.text(x0 + (10 - RP.NERTA_HALF) * u, nb - 1.0 * u, RP.CONCEPT_NOTE, fontsize=RP.NOTE_FS * 6.2 / 5.4, color=INK,
                   ha="left", va="top", zorder=13)
    if M.WEB:  # nerta.fun, as make_line_poster's web header, its sizes scaled from the posters' 5.4-point unit to this one
        sh.ax.text(x0 + 10 * u, nb - 1.0 * u, "Maxwell Howe", fontsize=9.6, color=INK, ha="center", va="top", zorder=13)
        sh.ax.text(x1 - 5 * u, hy, "@mapzimus", fontsize=11.0, fontweight="bold", color="#b9b9b4", ha="right", va="center", zorder=13)
    # The release block on every map posted November 8 (Max): disclaimer, "Map: Maxwell Howe", "#30DayMapChallenge", "Day 8 • Utopia"
    left, bottom, _top = draw_release(_NoDraw() if (M.WEB or RP.NO_DISCLAIMER) else sh.ax, x1 - 5 * u, hy, size=11.0, ppu=1 / sh.mpp, ink=INK)
    return [box(x0, y1 - 24 * u, title_r + 3 * u, y1), box(left - 3 * u, bottom - 3 * u, x1, y1)]


def key(sh, kx0, ky1, used):
    """Each line by name, every symbol on the map, the transfer pills on this map, and the rider notes.
    Returns (bottom, right) of what it drew, so the box fits it."""
    mpp = sh.mpp
    y = ky1 - 8 * mpp
    lx = kx0 + 8 * mpp
    tx = lx + 27 * mpp
    right = [lx]

    def text(yy, t, x=None):
        x = tx if x is None else x
        sh.txt(x, yy, t, 7.4)
        right.append(x + sh.w(t, 7.4))

    sh.txt(lx, y, "KEY", 10.4, "bold", "left", "center")
    y -= 14 * mpp
    order = [k for k in RANK if k not in HSR_LINES]
    for k in sorted(order, key=lambda k: RP.LINES[k]["name"]):
        d = RP.LINES[k]
        sh.stroke(np.array([(lx, y), (lx + 22 * mpp, y)]), k, z=12)
        right.append(tx + sh.pill(tx, y, d["name"], PURPLE, WHITE, h_pt=9.2, fs=5.8, ring=d["hue"], z=12.5))
        y -= 12.5 * mpp
    y -= 3 * mpp
    sh.stroke(np.array([(lx, y), (lx + 22 * mpp, y)]), "hmon", z=12)
    for t in ("High-speed rail. Near Boston it stops only at North Station, Boston",
              "Central, South Station, Back Bay, West Station and Route 128;",
              "farther out at Lowell, Haverhill, Worcester and Providence"):
        text(y, t)
        y -= 10 * mpp
    y -= 4 * mpp
    sh.ax.scatter(lx + 11 * mpp, y, s=(LW_PT * 0.85) ** 2, color=WHITE, edgecolor=INK, lw=0.6, zorder=12)
    text(y, "Station")
    y -= 12 * mpp
    sh.ax.scatter(lx + 11 * mpp, y, s=(LW_PT * 1.25) ** 2, color=WHITE, edgecolor=INK, lw=1.2, zorder=12)
    text(y, "Station with a transfer")
    y -= 12 * mpp
    lw = LW_PT * 1.45
    sh.ax.plot([lx + 5 * mpp, lx + 17 * mpp], [y, y], color=INK, lw=lw, solid_capstyle="round", zorder=12)
    sh.ax.plot([lx + 5 * mpp, lx + 17 * mpp], [y, y], color=WHITE, lw=lw * 0.6, solid_capstyle="round", zorder=12.01)
    text(y, "Station on more than one line (lines side by side share one track)")
    y -= 12 * mpp
    xa, xb = lx + 3 * mpp, lx + 19 * mpp   # Sullivan Sq's drawing: two platform dots, a thin link, a gold line over it
    sh.ax.plot([xa, xb], [y, y], color=INK, lw=1.4, solid_capstyle="round", zorder=12)
    sh.stroke(np.array([(lx + 11 * mpp, y - 5 * mpp), (lx + 11 * mpp, y + 5 * mpp)]), "hmon", z=12)
    for q in (xa, xb):
        sh.ax.scatter(q, y, s=(LW_PT * 1.25) ** 2, color=WHITE, edgecolor=INK, lw=1.2, zorder=13)
    text(y, "High-speed trains pass without stopping")
    y -= 12 * mpp
    sh.ax.scatter(lx + 11 * mpp, y, s=(LW_PT * 1.45) ** 2, color=WHITE, edgecolor=PURPLE, lw=1.5, zorder=12)
    text(y, "End of the line")
    y -= 14 * mpp
    sh.ax.add_patch(plt.Circle((lx + 11 * mpp, y), 5.0 * mpp, fc=WHITE, ec=INK, lw=1.6, zorder=12))
    text(y, "Main hub: North Station, Boston Central, South Station")
    y -= 14 * mpp
    xs = np.array([lx + 1 * mpp, lx + 21 * mpp])
    sh.ax.plot(xs, [y, y], color=INK, lw=LW_PT * 2.2 * 0.6, solid_capstyle="round", zorder=12)
    for off, col in ((-1.55, WHITE), (-0.55, GOLD), (0.55, GOLD), (1.55, WHITE)):
        sh.ax.plot(xs, [y + off * 0.6 * mpp] * 2, color=col, lw=0.5, solid_capstyle="butt", zorder=12.1)
    text(y, "The BIGGER Dig, the tunnel joining the three hubs")
    y -= 12 * mpp
    sh.ax.plot([lx, lx + 15 * mpp], [y, y], color=PURPLE, lw=LW_PT, solid_capstyle="butt", zorder=11.5)
    sh.ax.add_patch(Polygon([(lx + 22 * mpp, y), (lx + 15 * mpp, y - 4.4 * mpp), (lx + 15 * mpp, y + 4.4 * mpp)], closed=True, fc=PURPLE, ec="none", zorder=12))
    text(y, "Line continues")
    y -= 12 * mpp
    sh.ax.add_patch(Rectangle((lx + 3 * mpp, y - 4.5 * mpp), 16 * mpp, 9 * mpp, fc="none", ec=INK, lw=0.8, ls=(0, (3, 2)), zorder=12))
    text(y, "Downtown, shown larger in the inset")
    y -= 12 * mpp
    sh.ax.plot([lx + 1 * mpp, lx + 21 * mpp], [y, y], color="#b9b4ad", lw=0.9, ls=(0, (4, 2)), zorder=12)
    text(y, "State line")
    y -= 16 * mpp
    codes = sorted({c for c, _ in used if c != "F"}, key=LP.ORDER.index)
    col = 0
    for c in codes:
        cx = lx + col * 70 * mpp
        sh.pill(cx, y, c, LP.PILL[c], INK if c == "YL" else WHITE, z=12)
        text(y, LP.NAMES[c], x=cx + 20 * mpp)
        col += 1
        if col == 3:
            col, y = 0, y - 12 * mpp
    if col:
        y -= 12 * mpp
    boats, fast_boat = [], None   # the high-speed ring sample takes a route that really has fast stops
    for c, st in used:
        if c == "F":
            fill, fg, name, fast = RP.ferry_look(st)
            if fast and fast_boat is None:
                fast_boat = (fill, fg)
            if (fill, fg, name) not in boats:
                boats.append((fill, fg, name))
    for fill, fg, name in boats:
        sh.pill(lx, y, "F", fill, fg, z=12)
        text(y, name, x=lx + 20 * mpp)
        y -= 12 * mpp
    if fast_boat:
        sh.pill(lx - 2 * mpp, y, "F", fast_boat[0], fast_boat[1], express=True, z=12)
        text(y, "Fast ferries stop here (major port)", x=lx + 20 * mpp)
        y -= 14 * mpp
    for kind, t in (("icon", "Every station is accessible"), ("park", LP.PARKING_NOTE), ("text", "Driverless maglev, 24 hours a day"), ("cp", CP_TEXT),
                    ("text", "Pods on demand at every station"), ("text", "The Peabody line runs crosstown, Marblehead to Lawrence"),
                    ("text", "Extra trains for TD Garden and Foxboro stadium events")):
        if kind == "icon":
            wheel_icon(sh, lx + 11 * mpp, y)
        elif kind == "park":   # the same sign as on the map
            park_sign(sh, lx + 11 * mpp, y, z=12)
        elif kind == "cp":     # the shared Charlie Points coin
            draw_cp(sh.ax, lx + 11 * mpp, y, 4.0 * mpp, z=12)
        text(y, t)
        y -= 11 * mpp
    y -= 8 * mpp
    scale_bar(sh, lx, y, [(0, "0"), (2, "2"), (4, "4"), (6, "6"), (8, "8"), (10, "10 miles")])
    right.append(lx + 10 * 1609.344 + 14 * mpp)
    return y - 10 * mpp, max(right)


def next_version(out=OUT):
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        return int(sys.argv[1])
    v = 1
    while (out / f"rail_regional_v{v}.png").exists() or (out / f"rail_regional_v{v}.pdf").exists():
        v += 1
    return v


def cut_out(cl, area):
    """The main map's lines with the downtown box cut out: they stop at its dashed edge, and the inset draws what's inside.
    (Drawn through the box, South Station's 8-line bundle tangled at the main map's scale: review of v2.) A piece's
    arrowhead stays with the part that holds its far end."""
    out = []
    for x in cl:
        ls = LineString(x["opts"])
        rest = ls.difference(area)
        parts = [g for g in getattr(rest, "geoms", [rest]) if not g.is_empty and g.geom_type == "LineString" and g.length > 1.0]
        far = Point(x["opts"][-1])
        for g in parts:
            keep_end = g.distance(far) < 1.0
            out.append(dict(x, opts=np.asarray(g.coords), cut=x["cut"] if keep_end else False, end=x["end"] if keep_end else "end"))
    return out


def draw_map(sh, pieces, pos, codes, fr, sp, step, scale=1.0, label_skip=None, arrows=False):
    """Lines, stations and names on one axes. label_skip: an area whose stations are named elsewhere (the inset)."""
    hubs = [(pos[h][0].x, pos[h][0].y) for h in HUBS if h in pos]
    dens = bundle(pieces, sp, step, win=WIN_PT * sh.mpp, clip=fr.buffer(20000) if label_skip is None else fr.buffer(3000),
                  hubs=hubs, taper=TAPER_PT * sh.mpp)
    cl = clip_to(dens, fr.buffer(-16 * sh.mpp, join_style=2) if arrows else fr)  # main map: arrowheads and their words stay on the sheet
    if label_skip is not None:   # main map: downtown is the inset's job
        cl = cut_out(cl, label_skip.buffer(-4 * sh.mpp, join_style=2))
        X0, X1 = sh.ax.get_xlim()
        Y0, Y1 = sh.ax.get_ylim()
        bx0, by0, bx1, by1 = label_skip.bounds
        verts = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1), (X0, Y0), (bx0, by0), (bx0, by1), (bx1, by1), (bx1, by0), (bx0, by0)]
        pcodes = [MPath.MOVETO] + [MPath.LINETO] * 3 + [MPath.CLOSEPOLY] + [MPath.MOVETO] + [MPath.LINETO] * 3 + [MPath.CLOSEPOLY]
        sh.clip = PathPatch(MPath(verts, pcodes), transform=sh.ax.transData, fc="none", ec="none")
    draw_network(sh, cl, scale)
    flyovers(sh, cl, scale)
    tips = []
    if arrows:  # main map only: lines leaving the inset aren't running on
        for x in cl:
            if x["cut"] or x["end"] == "runs_on":
                tip, v = arrowhead(sh, x["opts"], chord=None if x["cut"] else 2000.0)
                tips.append((x["line"], x["piece"], tip, v))
    rows = station_table(dens, pos, sp)
    geoms = {}
    hub_scale = 0.6 if label_skip is not None else 1.0   # main map: the hubs sit in the Dig, drawn at 0.6 there
    paths = {}
    for x in cl:
        paths.setdefault(x["line"], []).append(LineString(x["opts"]))
    for st in rows:
        if not all(fr.contains(Point(q)) for _, q in st["dots"]):
            continue
        if label_skip is not None and label_skip.contains(Point(st["p"])):
            continue   # main map: stations inside the downtown box are drawn in the inset
        g = draw_station(sh, st, codes.get(st["name"], []), scale, hub_scale, paths)
        if g is not None:
            geoms[st["name"]] = (st, g)
    # names: biggest first
    order = {"hub": 0, "tier2": 1, "end": 2}
    placed = []

    def blocked(bx):
        """What a name's box would cover, as (shape, kind): "line", a colored line (Max, November 8: a name may sit on a line
        when that's the clearest spot; its pills may not); "near", the few points around another name (allowed at a small
        cost, so two names don't stack into what reads as one); "hard", dots, pills, names, furniture and the sheet's edge."""
        out = [(ln, "line") for _, ln in sh.lines if ln.intersects(bx)] + [(d, "hard") for _, d in sh.dots if d.intersects(bx)]
        out += [(p, "hard") for p in sh.pills + sh.blocks if p.intersects(bx)]
        for b in placed:
            if b.intersects(bx):
                out.append((b, "hard"))
            else:
                halo = b.buffer(NEAR_PT * sh.mpp, join_style=2)
                if halo.intersects(bx):
                    out.append((halo, "near"))
        out += [] if fr.buffer(-4 * sh.mpp).contains(bx) else [(bx.difference(fr.buffer(-4 * sh.mpp)), "hard")]
        return out
    for name, (st, g) in sorted(geoms.items(), key=lambda kv: (order.get(kv[1][0]["kind"], 3), kv[0])):
        if label_skip is not None and label_skip.contains(Point(st["p"])):
            continue
        placed.append(place_label(sh, st, g, codes.get(name, []), blocked, scale).buffer(1.6 * sh.mpp, join_style=2))  # a small gap between names
    # Where the running-on lines go, from the poster's own arrow rows. The Peabody line ends at Lawrence on this map.
    words = {k: [r for r in rws if r != RP.LINES[k]["name"]] for k, _p, rws, _w in RP.ARROWS if k != "pea"}
    for line, _piece, tip, v in tips:
        if words.get(line):
            placed.append(arrow_rows(sh, tip, words[line], None if line in HSR_LINES else line, blocked).buffer(1.6 * sh.mpp, join_style=2))
    return dens, cl, rows


def arrow_rows(sh, tip, rows, pill_key, blocked):
    """The words beside an arrowhead: a commuter line's own pill, then where it goes, in purple bold capitals."""
    mpp = sh.mpp
    fs, lead = 6.8, 10.0 * mpp
    items = ([("pill", pill_key)] if pill_key else []) + [("text", r) for r in rows]
    ws = [pill_w(sh, RP.LINES[k]["name"], 5.8, ring=True) if kind == "pill" else sh.w(k, fs, "bold") for kind, k in items]
    W, H = max(ws), lead * len(items)
    best = None
    for g in (5 * mpp, 12 * mpp, 22 * mpp):  # nearest first
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1), (0, 2), (0, -2)):
            x0 = tip[0] + g if dx > 0 else tip[0] - g - W if dx < 0 else tip[0] - W / 2
            y1 = tip[1] + H / 2 if dy == 0 else (tip[1] + abs(dy) * g + H if dy > 0 else tip[1] - abs(dy) * g)
            bx = box(x0, y1 - H, x0 + W, y1)
            hit = sum(o.intersection(bx).area for o, _k in blocked(bx))  # the words by an arrow have room to keep clear of every line
            hit += sum(o.intersection(bx.buffer(2.5 * mpp)).area for k_, o in sh.lines if k_ == "arrowhead")  # and of the arrowheads
            if best is None or hit < best[1]:
                best = (bx, hit)
            if hit == 0:
                break
        if best[1] == 0:
            break
    bx = best[0]
    x0, _, _, y1 = bx.bounds
    for i, (kind, k) in enumerate(items):
        y = y1 - lead * (i + 0.5)
        if kind == "pill":
            sh.pill(x0, y, RP.LINES[k]["name"], PURPLE, WHITE, h_pt=9.2, fs=5.8, ring=RP.LINES[k]["hue"], z=7.5)
        else:
            sh.txt(x0, y - 0.3 * mpp, k, fs, "bold", "left", "center", color=PURPLE)
    return bx


def main():
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else OUT   # --out DIR: the same 600-dpi PNG and PDF, into DIR
    v = next_version(out)
    png, pdf = out / f"rail_regional_v{v}.png", out / f"rail_regional_v{v}.pdf"
    draft = "--draft" in sys.argv
    if draft:
        d = Path(sys.argv[sys.argv.index("--draft") + 1])
        png, pdf = d / "regional_draft.png", d / "regional_draft.pdf"
    for f in (png, pdf):
        if f.exists() and not draft:
            raise SystemExit(f"refusing to overwrite {f}")
    RP.build()
    RP.stations()
    codes = RP.t_codes()
    pieces, real_lines = load_lines()
    pos, real_pos = load_stations()
    if not (real_lines and real_pos):
        print("TRIAL: using fallback data (lines.geojson or stations.geojson not built yet)")
    else:
        export_layers()
    pieces = fit_ends(pieces, pos)

    x0, y0, x1, y1 = frame_m()
    fr = box(x0, y0, x1, y1)
    W, H = (x1 - x0) / INCH_M, (y1 - y0) / INCH_M
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.patch.set_facecolor(PAPER)
    sh = Sheet(ax, INCH_M / 72)
    base(sh, x0, y0, x1, y1)

    cx0, cy0, cx1, cy1 = gpd.GeoSeries([box(*CORE_LL)], crs=4326).to_crs(CRS).total_bounds
    core = box(cx0, cy0, cx1, cy1)
    # Furniture first, so names keep clear of it: the header and release block, the inset in open water, the Key, the
    # names of the states and the water
    inset_at = ll(*INSET_LL)
    iw, ih = (cx1 - cx0) * INSET_F, (cy1 - cy0) * INSET_F
    kx0, ky1 = ll(*KEY_LL)
    kw, kh = KEY_IN[0] * INCH_M, KEY_IN[1] * INCH_M
    sh.blocks += [box(inset_at[0], inset_at[1], inset_at[0] + iw, inset_at[1] + ih), box(kx0, ky1 - kh, kx0 + kw, ky1)]
    sh.blocks += header(sh, x0, y1, x1)
    sh.blocks.append(core)   # the downtown box: drawn in the inset, so no names here
    places(sh)
    draw_map(sh, pieces, pos, codes, fr, SP_PT * sh.mpp, 80.0, label_skip=core, arrows=True)
    ax.add_patch(Rectangle((cx0, cy0), cx1 - cx0, cy1 - cy0, fc="none", ec=INK, lw=0.8, ls=(0, (3, 2)), zorder=9))
    mx, my = (cx0 + cx1) / 2, (cy0 + cy1) / 2
    cw = max(sh.w("DOWNTOWN", 9.6, "bold"), sh.w("shown larger", 7.4), sh.w("in the inset", 7.4)) + 10 * sh.mpp
    ax.add_patch(FancyBboxPatch((mx - cw / 2, my - 21 * sh.mpp), cw, 35 * sh.mpp, boxstyle=f"round,pad=0,rounding_size={4 * sh.mpp}",
                                fc=PAPER, ec="none", zorder=10.5))
    sh.txt(mx, my + 7 * sh.mpp, "DOWNTOWN", 9.6, "bold", "center", "center", halo=True)
    sh.txt(mx, my - 5 * sh.mpp, "shown larger", 7.4, "normal", "center", "center", halo=True)
    sh.txt(mx, my - 15 * sh.mpp, "in the inset", 7.4, "normal", "center", "center", halo=True)
    used = [(c, s["name"]) for s in RP.STATIONS for c in codes.get(s["name"], [])]
    ky0, kright = key(sh, kx0, ky1, used)
    ax.add_patch(FancyBboxPatch((kx0, ky0), kright - kx0 + 8 * sh.mpp, ky1 - ky0, boxstyle=f"round,pad=0,rounding_size={10 * sh.mpp}",
                                fc=PAPER, ec="#d9d3dc", lw=1.0, zorder=10))
    print(f"  Key {(kright - kx0 + 8 * sh.mpp) / INCH_M:.2f} x {(ky1 - ky0) / INCH_M:.2f} in (room {KEY_IN[0]} x {KEY_IN[1]})")
    if ky1 - ky0 > kh or kright - kx0 + 8 * sh.mpp > kw:
        print("  Key is bigger than its room: names may sit under it")
    water = "US Census (towns; TIGER/Line water)" if WATER_FILE.exists() else "US Census (towns)"
    ax.text(x1 - 5 * 5.4 * sh.mpp, y0 + 4 * 5.4 * sh.mpp,
            # nerta.fun never says MBTA; the OpenStreetMap credit stays everywhere (OSM's license)
            f"Drawn to scale: NAD83 Massachusetts Mainland. Map data: {'' if (M.WEB or RP.NO_DISCLAIMER) else 'MBTA, '}© OpenStreetMap contributors, {water}, EPA NHDPlus (rivers),\n"
            "Jeremy Atack, US Railroads 1826–1911 GIS. Track drawn straight where no railroad runs is ours." + ("" if (M.WEB or RP.NO_DISCLAIMER) else " Not affiliated with the MBTA."),
            fontsize=7.4, color=INK, ha="right", va="bottom", zorder=13, linespacing=1.4)
    sh2 = inset(fig, sh, pieces, pos, codes, inset_at)

    bad = check(fig, sh)
    for b in bad:
        print("  ", b)
    print(f"{len(bad)} flags (main)")
    bad2 = check(fig, sh2)
    for b in bad2:
        print("  inset:", b)
    print(f"{len(bad2)} flags (inset)")
    png.parent.mkdir(parents=True, exist_ok=True)
    dpi = int(sys.argv[sys.argv.index("--dpi") + 1]) if draft and "--dpi" in sys.argv else (120 if draft else 600)
    fig.savefig(png, dpi=dpi, facecolor=PAPER)
    if not draft:
        fig.savefig(pdf, facecolor=PAPER)
    print("written", png, f"{W:.1f} x {H:.1f} in")


if __name__ == "__main__":
    main()
