"""Commuter rail and high-speed rail line posters: one station-wall poster per line, in the look of the T line posters.

Stops, branches, transfers and colors are read from make_rail_poster.py (build(), stations(), t_codes(), ferry_look()),
so a line poster can never disagree with the combined rail poster. Only the layout (where each stop sits) is written here.
The look is make_line_poster.py's: 5 units a row, a 12 pt line, level names (bold capitals at the ends), a P sign after the
name of every station in make_tmap.PARKING (with a Key row when a poster has one), transfer pills butted against the line
with each further pill tucked under the one before, the T and NERTA mark, the big code pill and the title in the header, the
release block at the top right, and the Key along the bottom. The P is make_line_poster.name's own (park(), PARK_A, PARK_GAP
past the name's last letter). Names and pills sit on opposite sides of the line here, so a P pushes no pill along; the sheet
measures it like a pill, so it reaches PARK_ROOM past the name.

North is up. A line whose far end is north or northwest has its far end at the top and Boston at the bottom; every other
line has Boston at the top. A branch leaves on a 45-degree diagonal into its own column, names on the outside; where the
trunk runs on beside it, the branch's stops sit level with the trunk's (as Red's Braintree and Ashmont legs do).
Every line but the Peabody line runs on through the BIGGER Dig, so its downtown end is a plain transfer station, never a
bold terminus: on the combined poster too, no line visibly ends downtown.

Commuter lines are commuter purple with the line's own second color on both edges; high-speed lines are purple with a
gold core. Each commuter rail transfer gets its own CR pill, ringed in that line's second color, and the Key names the line.
At the three Dig hubs every commuter line stops, so there one plain CR pill stands for all of them (rail session, November 8:
ten ringed pills only repeated that). The wrapping below is kept for any stop with more than MAXROW pills: the T lines, HSR and the ferry stay in the
stop's own row against the line, and the CR pills follow in rows of up to five, each butted against the line and tucked close
beside the row before, outward (toward the line's far end, so the line always runs on behind them). Those stops get the
extra room: the next stop out sits at least a row past a hub's last row of pills, and farther from that row than the row is
from its own stop, so every row of pills reads with its own stop (checked: no pill sits nearer another stop's dot).
High-speed lines stop only at North Station, Boston Central, South Station, Back Bay, West Station and Route 128 on the
map, then at the cities beyond it (BEYOND below); Lowell, Haverhill, Worcester and Providence are also commuter stations.
They run through the Dig like the commuter lines, so their Key carries the same through-running note. Their purple edge is
the CR and HSR pills' own purple, so a paper hairline (CASE) keeps every pill off a high-speed line.

Writes only output/copies/rail_line_<key>_vN.png (600 dpi) and .pdf, at the next free N for each line, and never
overwrites; with --out DIR it writes them into DIR instead, at the next N free there. With --draft DIR it writes
DIR/rail_line_<key>.png at 150 dpi and DIR/rail_line_stops.json (stops top to bottom, branches, pills and P signs per stop)
instead. With NERTA_WEB=1 (make_tmap.WEB) it draws the nerta.fun version, as make_line_poster does: no release block,
"Maxwell Howe" under the NERTA mark and @mapzimus faint at the top right; the sheet keeps the print version's size.
make_line_poster.py, marks.py and make_tmap.py are imported read only: their main() would save over finished files.
Run: python make_rail_line_posters.py [keys...] [--draft DIR | --out DIR]
"""
import functools
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Polygon  # noqa: E402
from shapely.geometry import LineString, Point, box  # noqa: E402
from shapely.geometry import Polygon as SPoly  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from nerta_mark import draw_nerta  # noqa: E402
import release_tag  # noqa: E402  (the shared November 8 release block, read only)
from release_tag import draw_release, release_width  # noqa: E402
import make_tmap as M  # noqa: E402  (read only: paper, icon, PARKING, WEB)
import make_line_poster as LP  # noqa: E402  (read only: the line poster look)
import make_rail_poster as RP  # noqa: E402  (read only: every stop, branch, transfer and color)
from station_kit import INK, WHITE, rounded  # noqa: E402

# Measuring a word through its outline takes about half a second here, and the same words come up on every poster:
# remember each answer for this run. Nothing in those files changes; only repeat measurements are skipped.
for _mod, _fn in ((LP, "width"), (RP, "width"), (release_tag, "_w")):
    setattr(_mod, _fn, functools.lru_cache(maxsize=None)(getattr(_mod, _fn)))

OUT = Path(__file__).resolve().parents[1] / "output" / "copies"
P, K, PPU, LWP, LWU = LP.P, LP.K, LP.PPU, LP.LWP, LP.LWU   # the line posters' row, scale and line width
TRANSFER_R, END_R, RIM = LP.TRANSFER_R, LP.END_R, LP.RIM
STOP_R = (LWP * 0.56 / 2 + 0.7 / 2) / PPU                    # outer radius of a plain stop dot
PURPLE, GOLD, PAPER = RP.PURPLE, RP.GOLD, M.PAPER
EDGE = 2.2         # each edge of a commuter line in the line's own color, points
CORE = 5.0         # gold core of a high-speed line, points
PH, GAP = 2.9, 0.35  # pill height and the gap between pills, as on the line posters
UNDER = PH + GAP   # a wrapped row of pills sits this far under the row before, tucked as close as pills in a row
MAXROW = 6         # a stop with more transfers than this wraps them (only the three Dig hubs, with 14 or 15)
CR_ROW = 5         # CR pills in each wrapped row, at most
HUB_ROOM = 1.0     # the next stop sits at least this much farther from a hub's last row of pills than that row is from its own stop
CASE = 2 * RIM     # paper between a high-speed line and its pills: the same 1.2 pt as between two pills in a row
RING = (0.25, 0.5)   # a CR pill's purple edge and the ring of its line's color inside it, units: a ring wide enough for the color
#                      to carry, and room inside for the 8.2 pt letters (make_rail_poster's line pills use 0.36 and 0.42)
FAST = (0.3, 0.26)   # a fast-ferry pill's white ring, as make_rail_poster.pill draws it
D = 20.0           # a branch's column sits four rows' width off the trunk, as Red's Braintree and Waltham legs do
STEM = 2.0         # the straight run before a branch turns (Red's Braintree leg)
FORK_STEM = 3.5    # longer where the line forks, as at Red's Alewife, so a leg turns clear of the junction's own pills (Beverly)
CLEAR = 0.7        # a branch's first stop sits at least this many rows past the end of its diagonal (Red's North Quincy)
RUN = 4.0          # a line that runs on past its last stop goes on this far, then its arrowhead
HEAD_L, HEAD_W = 4.5, 3.0   # arrowhead length and half width: the combined poster's head, at this line width
ARROW_FS = 10.4
ASPECT = 1.15      # rows grow until the poster is at least this many times as tall as it is wide...
FMAX = 3.0         # ...up to 3 times the house row: the short high-speed and Peabody posters need it to stand upright (Indigo's T poster uses 2.2)
DIG = ("North Station", "Boston Central", "South Station")
ALL = "all"        # the one plain CR pill at a Dig hub: every commuter line stops there

KEYS = ["fit", "low", "hav", "pea", "nbp", "wor", "fra", "pro", "fr", "kin", "grb", "hmon", "hmai", "halb", "hnyc"]
UP = {"fit", "low", "hav", "nbp", "pea", "hmon", "hmai"}     # far end north or northwest: far end at the top
# High-speed stops past the map's edge, in order outward: the cities on the combined poster's rows (real Amtrak or studied stops).
# Manchester NH carries its state, as Concord NH does: the Rockport branch's Manchester is Manchester-by-the-Sea (audit, November 8).
BEYOND = {"hmon": ["Lowell", "Nashua", "Manchester NH", "Concord NH", "Burlington VT", "Montreal"],
          "hmai": ["Haverhill", "Portland", "Augusta", "Bangor"],
          "halb": ["Worcester", "Springfield", "Albany", "Chicago"],
          "hnyc": ["Providence", "New Haven", "New York", "Philadelphia", "Washington"]}
SHARED = {"Lowell", "Haverhill", "Worcester", "Providence"}   # also NERTA commuter stations (Manchester NH is not Manchester-by-the-Sea)
HSR_TO = {"hmon": "to Montreal", "hmai": "to Bangor", "halb": "to Albany, Chicago", "hnyc": "to New York, Washington"}
# Layout per line. side: where the trunk's names sit (pills on the other side). branch: a branch leaves the trunk at this
# junction to the left (-1) or right (+1) and the trunk runs on. fork: the line splits at the junction, the main line's leg
# to one side and the branch to the other, so neither leg's pills meet the other's diagonal. arrow: a runs-on branch.
SPEC = {"fit": dict(side="r", branch={"South Acton": -1}),                 # Marlborough to the west
        "fra": dict(side="l", branch={"Walpole": 1}),                      # Foxboro and Mansfield to the east
        "nbp": dict(side="r", fork=("Beverly", 1, -1)),                    # Rockport to the east, Newburyport to the north
        "pro": dict(side="r", fork=("Canton Junction", -1, 1)),            # Providence to the southwest, Stoughton to the southeast
        "fr": dict(side="l", fork=("East Taunton", 1, -1), arrow={"Middleborough": 1})}  # New Bedford, Fall River, Cape Cod
NOTE_X = LP.NOTE_X   # the Key's notes column starts where the next pill column would
from charlie_points import KEY_TEXT as CP_TEXT, draw_cp  # noqa: E402  (the shared Charlie Points coin and Key line, November 8)
SERVICE = [("icon", "Every station is accessible"), ("text", "Driverless maglev, 24 hours a day"), ("cp", CP_TEXT),
           ("text", "Pods on demand at every station")]
THROUGH = "Every train runs through North Station, Boston Central and South Station"
WRAP_PITCH = 2.4   # the through-running note, where it is too long for its row, goes on under itself this close: one note, two lines
FAST_NOTE = "Fast ferries stop here (major port)"

TEXTS = []                                          # (text artist, owning station or None)
REG = {"line": [], "dot": [], "pill": [], "box": []}  # (label, shapely shape) for the checks
_READY = []


# ---------------------------------------------------------------------------------------------------------------
# Data, all from make_rail_poster
def setup():
    if not _READY:
        RP.build()
        RP.stations()
        names = [s["name"] for s in RP.STATIONS]
        dup = {n for n in names if names.count(n) > 1}
        if dup:
            raise SystemExit(f"station listed twice on the rail poster: {sorted(dup)}")
        _READY.append(({s["name"]: s for s in RP.STATIONS}, RP.t_codes()))
    return _READY[0]


def hsr(key):
    return bool(RP.LINES[key].get("hsr"))


CR_KEYS = [k for k in RP.LINES if not hsr(k)]
HSR_KEYS = [k for k in RP.LINES if hsr(k)]


def line_name(key):
    """Rider name of a commuter line: "FALL RIVER / NEW BEDFORD LINE" reads "Fall River/New Bedford Line"."""
    return RP.LINES[key]["name"].title().replace(" / ", "/")


def title(key):
    if hsr(key):
        return "High-Speed Rail\n" + HSR_TO[key]
    n = line_name(key)
    if "/" in n:
        a, b = n.split("/", 1)
        return a + "/\n" + b
    return n.replace(" Line", "\nLine")


def dot_on(stn, name, key):
    for ln, xy in stn[name]["dots"]:
        if ln == key:
            return xy
    return None


def stops_at(name):
    """Every line whose trains stop at this station. High-speed trains pass a "pass" station without stopping."""
    stn, _ = setup()
    out = set()
    s = stn.get(name)
    if s:
        out |= {ln for ln, _ in s["dots"] if not (s["kind"] == "pass" and hsr(ln))}
    for h, cities in BEYOND.items():
        if name in cities and (s is None or name in SHARED):
            out.add(h)
    if name == "Lawrence":  # the Peabody line ends at Lawrence (regional map); the combined poster shows it as "TO LAWRENCE"
        out.add("pea")
    return out


def route(key):
    """Stops in order outward from Boston (from Marblehead on the Peabody line), branches from their junctions, and the
    runs-on arrows. Each station's dot on this line is projected onto the line's drawn path, or onto its branch."""
    stn, _ = setup()
    main = LineString(RP.PATHS[key])
    brs = [b for k, b in RP.BRANCHES if k == key]
    on_main, on_br = [], [[] for _ in brs]
    for s in RP.STATIONS:
        if hsr(key) and s["kind"] == "pass":
            continue
        for ln, xy in s["dots"]:
            if ln != key:
                continue
            q = Point(xy)
            if main.distance(q) < 0.05:
                on_main.append((main.project(q), s["name"]))
                continue
            i = min(range(len(brs)), key=lambda i: LineString(brs[i]).distance(q)) if brs else None
            if i is None or LineString(brs[i]).distance(q) > 0.05:
                raise SystemExit(f"{s['name']} is on {key} but on none of its paths")
            on_br[i].append((LineString(brs[i]).project(q), s["name"]))
    stops = [n for _, n in sorted(on_main)]
    if hsr(key):
        stops += BEYOND[key]
    branches = []
    for b, lst in zip(brs, on_br):
        j = min((n for n in stops if n in stn and dot_on(stn, n, key)), key=lambda n: np.hypot(*np.subtract(dot_on(stn, n, key), b[0])))
        if np.hypot(*np.subtract(dot_on(stn, j, key), b[0])) > 0.05:
            raise SystemExit(f"a {key} branch starts at no station")
        branches.append(dict(junction=j, stops=[n for _, n in sorted(lst)], pts=b, arrow=None))
    arrows = []
    if not hsr(key):  # the high-speed posters show every stop past the map instead
        for ln, pts, rows, _where in RP.ARROWS:
            if ln != key:
                continue
            text = [r for r in rows if r.startswith("TO ")]
            if pts is RP.PATHS[key]:
                arrows.append(text)
            else:
                for b in branches:
                    if b["pts"] is pts:
                        b["arrow"] = text
    if key == "pea":  # Peabody trains end at Lawrence, a transfer to the Haverhill Line, as on the regional map
        stops.append("Lawrence")
        arrows = []
    return stops, branches, arrows


def pills_for(key, name, beyond=False):
    """Transfers at a stop, in house order: T lines, one CR per other commuter line, HSR, then the ferry. (code, line)."""
    stn, tc = setup()
    if beyond and name not in SHARED:
        return []
    at = stops_at(name)
    codes = [] if beyond else tc.get(name, [])
    out = [(c, None) for c in codes if c not in ("F", "CR", "HSR")]
    if name in DIG:  # every commuter line runs through all three Dig stations: one plain CR pill says so
        if any(ln in at and ln != key for ln in CR_KEYS):
            out.append(("CR", ALL))
    else:
        out += [("CR", ln) for ln in CR_KEYS if ln in at and ln != key]
    if any(h in at and h != key for h in HSR_KEYS):
        out.append(("HSR", None))
    if "F" in codes:
        out.append(("F", None))
    return out


def pill_rows(items):
    """The rows a stop's pills are drawn in. One row, as on the T posters, up to MAXROW pills. Past that (the Dig hubs) the
    T lines, HSR and the ferry keep the stop's own row, and the CR pills follow in balanced rows of up to CR_ROW, each
    UNDER from the row before, outward along the line: 9 go 5 and 4, 10 go 5 and 5."""
    if len(items) <= MAXROW:
        return [items] if items else []
    first = [it for it in items if it[0] != "CR"]
    crs = [it for it in items if it[0] == "CR"]
    n = -(-len(crs) // CR_ROW)
    rows, i = ([first] if first else []), 0
    for k in range(n):
        m = len(crs) // n + (k < len(crs) % n)
        rows.append(crs[i:i + m])
        i += m
    return rows


def look(code, ln, station):
    """Pill text, width, fill, text color, ring color, gold core, fast-ferry ring."""
    if code == "CR":
        return "CR", 6.6, PURPLE, WHITE, None if ln == ALL else RP.LINES[ln]["hue"], False, False
    if code == "HSR":
        return "HSR", 6.6, PURPLE, PURPLE, None, True, False
    if code == "F":
        fill, fg, _name, fast = RP.ferry_look(station)
        return RP.code_text("F", station), RP.code_w("F", station), fill, fg, None, False, fast
    return code, 6.6, LP.PILL[code], INK if code == "YL" else WHITE, None, False, False


def pill_label(code, ln, station):
    """How a pill reads in the stop table: CR [Lowell Line], F via Lovejoy Wharf [Charles River ferry], and "; fast ferries
    stop" inside the brackets where they do."""
    if code == "CR":
        return "CR [every commuter line]" if ln == ALL else f"CR [{line_name(ln)}]"
    if code == "F":
        fill, fg, name, fast = RP.ferry_look(station)
        return f"{RP.code_text('F', station)} [{name}{'; fast ferries stop' if fast else ''}]"
    return code


def display(name, beyond=False):
    stn, _ = setup()
    if beyond and name not in SHARED:
        return name
    t = stn[name]["text"] or RP.TEXT.get(name, name)
    return t.replace("/\n", "/").replace("\n", " ")   # one line, as on the T line posters


# ---------------------------------------------------------------------------------------------------------------
# Layout: x across, u outward from Boston; y = u on lines that run north, -u on the rest
def layout(key, f):
    stops, branches, arrows = route(key)
    spec = SPEC.get(key, {})
    side = spec.get("side", "r")
    p = P * f
    sgn = 1 if key in UP else -1
    beyond = set(BEYOND.get(key, []))
    fork = spec.get("fork")
    pos, sides, legs, runs = {}, {}, [], []
    if fork:
        j = stops.index(fork[0])
        trunk, rest = stops[:j + 1], stops[j + 1:]
    else:
        trunk, rest = stops, []

    def hang(n):
        """How far a stop's wrapped rows of pills reach past its own row. They stack outward, along the line toward its far
        end (down on a line with Boston at the top, up on one with Boston at the bottom), so the line runs on behind them."""
        return max(0, len(pill_rows(pills_for(key, n, n in beyond))) - 1) * UNDER

    def step(n):
        """From stop n to the next stop out: a row. A hub's wrapped rows stack toward that next stop, so it sits a full row
        past the last of them, and HUB_ROOM farther from that row than the row is from the hub (at the house row height,
        1.5 rows past it): the last row then reads with its own stop, never with the one beyond."""
        h = hang(n)
        return h + max(p, h + HUB_ROOM) if h else p

    def column(names, u):
        """u of each stop in a column, from u for the first, outward (step: a row, or a hub's rows and the room past them)."""
        out = []
        for i, n in enumerate(names):
            if i:
                u += step(names[i - 1])
            out.append(u)
        if hang(names[-1]):  # its rows would stack past the column's end, where no line runs behind them
            raise SystemExit(f"{key}: {names[-1]} ends a column but its pills wrap; give it a line to stack along")
        return out

    for n, u in zip(trunk, column(trunk, 0.0)):
        pos[n], sides[n] = (0.0, u), side
    legs.append(dict(stops=trunk, path=[pos[trunk[0]], pos[trunk[-1]]], part="trunk"))

    def leg(j, names, dx, part):
        x0, u0 = pos[j]
        if hang(j):
            raise SystemExit(f"{key}: a leg leaves {j}, whose pills wrap; give it room first")
        stem = FORK_STEM if fork and j == fork[0] else STEM
        u1 = u0 + stem + D
        first = u1 + CLEAR * p
        if part == "branch" and pos[trunk[-1]][1] >= first - p / 2:
            # the trunk runs on beside the branch: its stops keep to the trunk's rows, as Red's Braintree leg keeps to Ashmont's,
            # from the first row at least half a row past the diagonal
            first = u0 + np.ceil((u1 - u0) / p + 0.5 - 1e-6) * p
        at = [(x0 + dx * D, u) for u in column(names, first)]
        for n, q in zip(names, at):
            pos[n], sides[n] = q, ("r" if dx > 0 else "l")
        legs.append(dict(stops=[j] + names, path=[(x0, u0), (x0, u0 + stem), (x0 + dx * D, u1), at[-1]], part=part, junction=j, dx=dx))

    if fork:
        leg(fork[0], rest, fork[1], "main")
    for b in branches:
        if b["stops"]:
            dx = fork[2] if fork and b["junction"] == fork[0] else spec["branch"][b["junction"]]
            leg(b["junction"], b["stops"], dx, "branch")
        if b["arrow"]:
            dx = spec["arrow"][b["junction"]]
            x0, u0 = pos[b["junction"]]
            runs.append(dict(path=[(x0, u0), (x0 + dx * (2 * P), u0)], text=b["arrow"], dir=(dx, 0)))
    for text in arrows:  # the main line runs on past its last stop
        last = (rest or trunk)[-1]
        x0, u0 = pos[last]
        runs.append(dict(path=[(x0, u0), (x0, u0 + RUN)], text=text, dir=(0, 1)))
    # Every line but the Peabody line runs on through the Dig, so its downtown end is no terminus (combined poster: no line
    # visibly ends downtown, and the Key says every train runs through all three)
    ends = set() if stops[0] in DIG else {stops[0]}
    if not arrows:
        ends.add((rest or trunk)[-1])
    for lg in legs:
        if lg["part"] == "branch":
            ends.add(lg["stops"][-1])

    def y(q):
        return (q[0], sgn * q[1])
    return dict(key=key, stops=stops, pos={n: y(q) for n, q in pos.items()}, sides=sides, ends=ends, beyond=beyond, f=f, out=sgn,
                legs=[dict(lg, path=[y(q) for q in lg["path"]]) for lg in legs],
                runs=[dict(r, path=[y(q) for q in r["path"]], dir=(r["dir"][0], sgn * r["dir"][1])) for r in runs])


def u_span(key, f):
    ys = [q[1] for q in layout(key, f)["pos"].values()]
    return max(ys) - min(ys)


# ---------------------------------------------------------------------------------------------------------------
# Drawing
def width(text, fs, weight="normal"):
    return max(LP.width(t, fs, weight) for t in text.split("\n"))


def grab(ax, n0, owner=None):
    for t in list(ax.texts)[n0:]:
        TEXTS.append((t, owner))


def signs(ax, p0, owner):
    """The P signs make_line_poster.park drew since patch p0: the sheet measures them and the checks treat them as pills
    (nothing on them, nearer their own stop than any other). Their P is text, which grab() takes."""
    for pa in list(ax.patches)[p0:]:
        REG["pill"].append((owner, box(pa.get_x(), pa.get_y(), pa.get_x() + pa.get_width(), pa.get_y() + pa.get_height())))


def txt(ax, x, y, s, fs, weight="normal", ha="left", va="center", color=INK, z=11, owner=None, ls=1.0):
    t = ax.text(x, y, s, fontsize=fs, fontweight=weight, color=color, ha=ha, va=va, zorder=z, linespacing=ls)
    TEXTS.append((t, owner))
    return t


def inset(ax, x0, x1, y, h, k, fc, z):
    ax.add_patch(FancyBboxPatch((x0 + k, y - h / 2 + k), x1 - x0 - 2 * k, h - 2 * k, boxstyle=f"round,pad=0,rounding_size={h / 2 - k}", fc=fc, ec="none", zorder=z))


def pill_shape(ax, x0, x1, y, fill, z, h=PH, ring=None, gold=False, express=False, rim=True, span=None):
    """A pill from x0 to x1. ring: the line's second color just inside the edge, as on the NERTA mark. gold: the high-speed
    core (make_line_poster.gold_core). express: a thin white ring where fast ferries stop (make_rail_poster.pill).
    span: where a ring runs on a pill tucked under the one before: the stretch you can see, so the ring closes at both ends."""
    ax.add_patch(FancyBboxPatch((x0, y - h / 2), x1 - x0, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=fill,
                                ec=PAPER if rim else "none", lw=1.2 if rim else 0, zorder=z))
    if ring or express:
        a, b = span or (x0, x1)
        k, t = FAST if express else RING
        inset(ax, a, b, y, h, k, WHITE if express else ring, z + 0.01)
        inset(ax, a, b, y, h, k + t, fill, z + 0.02)
    if gold:
        inset(ax, x0, x1, y, h, 0.55, GOLD, z + 0.05)


def code_fs(text, ring):
    """Pill type: 8.6 pt for a code, 8.2 for longer text and inside a ring, so the letters clear it."""
    return 8.2 if ring or len(text) > 3 else 8.6


def code_dy(ring):
    """How far a pill's letters sit under its middle: the line posters' 0.08, and 0.04 inside a ring, which centers the
    smaller capitals between the ring's top and bottom (measured at 600 dpi)."""
    return 0.04 if ring else 0.08


def pill_row(ax, x, y, items, sign, station, ring_r, z=4):
    """make_line_poster.pills: the first pill butts against the line, its inner end under the stop's ring (ring_r; on a
    wrapped row, the line's edge, or its paper casing's on a high-speed line); each further pill tucks under the one
    before. A ring closes on the stretch of its pill you can see. Every label is centered on that stretch; high-speed
    labels on the gold core you can see. Returns the far end."""
    near = x + sign * LWU / 2
    far = near
    for i, (code, ln) in enumerate(items):
        text, w, fill, fg, ring, gold, express = look(code, ln, station)
        far = near + sign * w
        tuck = near - sign * (LWU / 2 if i == 0 else PH / 2 + GAP)
        x0, x1 = sorted((tuck, far))
        seen = x + sign * ring_r if i == 0 else near - sign * GAP + sign * RIM
        end = far - sign * RIM
        ringed = bool(ring or express)
        pill_shape(ax, x0, x1, y, fill, z - 0.1 * i, ring=ring, gold=gold, express=express, span=tuple(sorted((seen, far))) if ringed else None)
        if gold:
            seen, end = sign * max(sign * seen, sign * (tuck + sign * 0.55)), far - sign * 0.55
        elif ringed:
            end = far
        txt(ax, (seen + end) / 2, y - code_dy(ring), text, code_fs(text, ring), "bold", "center", "center", fg, z=z + 0.5)
        a = x + sign * ring_r if i == 0 else near
        REG["pill"].append((station, box(min(a, far), y - PH / 2, max(a, far), y + PH / 2)))
        near = far + sign * GAP
    return far


def draw_lines(ax, key, paths):
    """Commuter: the line's own color at full width, purple on top, so the color shows on both edges. High-speed: purple
    with a gold core, over a paper casing CASE wider each side: its purple edge is the CR and HSR pills' own purple, so the
    casing keeps a hairline of paper between the line and every pill butted against it, as between two pills in a row (a
    commuter line's edge is its own color, so its pills already stand out). Every leg's bottom layer goes down first, so legs
    meet with no seam."""
    xys = [rounded(p_, 2.5, n=40) for p_ in paths]
    bottom, top, lw = (PURPLE, GOLD, CORE) if hsr(key) else (RP.LINES[key]["hue"], PURPLE, LWP - 2 * EDGE)
    if hsr(key):  # under the line, over the pills (z 4 and down)
        for xy in xys:
            ax.plot(*xy.T, color=PAPER, lw=LWP + 2 * CASE * PPU, solid_capstyle="round", solid_joinstyle="round", zorder=4.9)
    for xy in xys:
        ax.plot(*xy.T, color=bottom, lw=LWP, solid_capstyle="round", solid_joinstyle="round", zorder=5)
        REG["line"].append((key, LineString(xy).buffer(LWU / 2, cap_style=2)))
    for xy in xys:
        ax.plot(*xy.T, color=top, lw=lw, solid_capstyle="round", solid_joinstyle="round", zorder=5.05)


def head(ax, path):
    """Purple arrowhead where a line runs on beyond the poster. Returns the tip."""
    a, b = np.asarray(path[-2], float), np.asarray(path[-1], float)
    v = (b - a) / np.hypot(*(b - a))
    n = np.array([-v[1], v[0]])
    tip = b + v * HEAD_L
    tri = [tuple(tip), tuple(b - n * HEAD_W), tuple(b + n * HEAD_W)]
    ax.add_patch(Polygon(tri, closed=True, fc=PURPLE, ec="none", zorder=5.2))
    REG["line"].append(("arrowhead", SPoly(tri)))
    return tip


def dot(ax, xy, kind, owner):
    if kind == "end":
        ax.scatter(*xy, s=(LWP * 1.35) ** 2, color=WHITE, edgecolor=PURPLE, lw=3.4, zorder=9)
        r = END_R
    elif kind == "transfer":
        ax.scatter(*xy, s=(LWP * 1.02) ** 2, color=WHITE, edgecolor=INK, lw=2.6, zorder=9)
        r = TRANSFER_R
    else:
        ax.scatter(*xy, s=(LWP * 0.56) ** 2, color=WHITE, edgecolor=INK, lw=0.7, zorder=9)
        r = STOP_R
    REG["dot"].append((owner, Point(xy).buffer(r, 32)))


def draw_content(ax, lay):
    key = lay["key"]
    draw_lines(ax, key, [lg["path"] for lg in lay["legs"]] + [r["path"] for r in lay["runs"]])
    for r in lay["runs"]:
        tip = head(ax, r["path"])
        t = " ".join(r["text"])
        if r["dir"][0]:   # sideways: the words follow the tip
            txt(ax, tip[0] + r["dir"][0] * 1.2, tip[1] - 0.05, t, ARROW_FS, "bold", "left" if r["dir"][0] > 0 else "right", "center", PURPLE)
        else:             # up or down: centered past the tip
            up = r["dir"][1] > 0
            txt(ax, tip[0], tip[1] + (1.2 if up else -1.2), t, ARROW_FS, "bold", "center", "bottom" if up else "top", PURPLE)
    used, table, wrapped, parked = [], {}, {}, []
    edge = LWU / 2 + (CASE if hsr(key) else 0.0)   # where a wrapped row's first pill shows: the line's edge, or its casing's
    for n in lay["stops"] + [s for lg in lay["legs"] for s in lg["stops"] if s not in lay["stops"]]:
        if n in table:
            continue
        xy, side = lay["pos"][n], lay["sides"][n]
        beyond = n in lay["beyond"]
        items = pills_for(key, n, beyond)
        rows = pill_rows(items)
        bold = n in lay["ends"]
        dot(ax, xy, "end" if bold else "transfer" if items else "stop", n)
        # A P after the name of every station with public parking, as on every map (make_tmap.PARKING, Max, November 8).
        # A city past the map's edge is no map station, so it never takes one.
        has_p = n in M.PARKING and not (beyond and n not in SHARED)
        n0, p0 = len(ax.texts), len(ax.patches)
        LP.name(ax, xy, display(n, beyond), side, bold, False, parking=has_p)
        grab(ax, n0, n)
        signs(ax, p0, n)
        if has_p:
            parked.append(n)
        for r, row in enumerate(rows):  # a wrapped row butts against the line beside the first, outward, with no stop ring to hide its end
            pill_row(ax, xy[0], xy[1] + lay["out"] * r * UNDER, row, 1 if side == "l" else -1, n, (END_R if bold else TRANSFER_R) if r == 0 else edge)
        used += [(c, ln, n) for c, ln in items]
        table[n] = [pill_label(c, ln, n) for c, ln in items]
        if len(rows) > 1:
            wrapped[n] = [[pill_label(c, ln, n) for c, ln in row] for row in rows]
    return used, table, wrapped, parked


# ---------------------------------------------------------------------------------------------------------------
# Key
def key_entries(key, used):
    """One row per pill used, in house order: T lines, each commuter line by name, high-speed rail, each ferry route,
    then the fast ferry ring, drawn in the color of the route with the most fast stops on this poster. Each row:
    (pill look, name); the look's group (T, CR, other) keeps the Key's columns together."""
    entries = []
    for c in sorted({c for c, _, _ in used if c not in ("CR", "HSR", "F")}, key=LP.ORDER.index):
        entries.append((dict(code=c, fill=LP.PILL[c], fg=INK if c == "YL" else WHITE, group="T"), LP.NAMES[c]))
    if any(c == "CR" and l_ == ALL for c, l_, _ in used):
        entries.append((dict(code="CR", fill=PURPLE, fg=WHITE, group="CR"), "Every commuter line"))
    for ln in CR_KEYS:
        if any(c == "CR" and l_ == ln for c, l_, _ in used):
            entries.append((dict(code="CR", fill=PURPLE, fg=WHITE, ring=RP.LINES[ln]["hue"], group="CR"), line_name(ln)))
    if any(c == "HSR" for c, _, _ in used):
        entries.append((dict(code="HSR", fill=PURPLE, fg=PURPLE, gold=True, group="X"), "High-speed rail"))
    boats, fast = [], Counter()
    for c, _, n in used:
        if c == "F":
            fill, fg, name, f_ = RP.ferry_look(n)
            if f_:
                fast[(fill, fg)] += 1
            if (fill, fg, name) not in boats:
                boats.append((fill, fg, name))
    order = [v[1] for v in RP.FERRY_ROUTES.values()]
    rank = lambda fill: order.index(fill) if fill in order else 99  # noqa: E731
    boats.sort(key=lambda b: rank(b[0]))
    entries += [(dict(code="F", fill=fill, fg=fg, group="X"), name) for fill, fg, name in boats]
    if fast:
        fill, fg = max(fast, key=lambda c: (fast[c], -rank(c[0])))
        entries.append((dict(code="F", fill=fill, fg=fg, express=True, group="X"), FAST_NOTE))
    return entries


def fast_route(fill):
    """A ferry color whose route runs fast trips (the North Shore and South Shore Fast Ferry), tested as make_line_poster's
    Key tests it."""
    return any(rt["color"] == fill and rt.get("fast") for rt in M.FERRY_ROUTES)


def key_notes(key, stops, parking=False, fast=False):
    """Rider notes, one a row. On a poster with a P sign, the P row sits under the accessibility row, two signs together,
    as on the T line posters. On a poster with a ferry pill of a route that runs fast trips (fast), the T line posters'
    note follows the event notes: not every stop of a Fast Ferry route is a fast stop (Peabody's Clifton and Marblehead,
    audit November 8). The through-running note goes last: where it is too long for the room it wraps onto a short
    second line (key_plan), and nothing under it then falls off the Key's rows."""
    notes = list(SERVICE)
    if parking:
        notes.insert(1, ("park", LP.PARKING_NOTE))
    if "North Station" in stops:
        notes.append(("text", "Extra trains for TD Garden events"))
    if key == "fra":
        notes.append(("text", "Extra trains to Foxboro for stadium events"))
    if key == "pea":
        notes.append(("text", "Crosstown line: Marblehead to Lawrence"))
    if hsr(key):
        notes.append(("text", "High-speed trains stop only at the stations shown"))
    if fast:
        notes.append(("text", LP.EXPRESS))
    if key != "pea":  # high-speed lines too: the combined poster runs every line but Peabody's through all three
        notes.append(("through", THROUGH))
    return notes


def note_lines(st, t, wrap):
    if st == "through" and wrap:
        a, b = t.split(", ", 1)
        return [a + ",", b]
    return [t]


def key_columns(entries, rows):
    """Columns of up to `rows` rows, as few as fit, kept in groups and as even as can be: the T lines, then the commuter
    lines, then high-speed rail and the ferries. No column holds a lone row of another group (a Fitchburg Line pill under
    the T lines). Returns the columns as (pitch, rows), and the cost of the split (10 or more: a lone row was unavoidable)."""
    n = len(entries)
    if not n:
        return [], 0
    ncol = -(-n // rows)
    groups = [pl["group"] for pl, _ in entries]

    def splits(left, k):
        if k == 1:
            if 1 <= left <= rows:
                yield (left,)
            return
        for a in range(max(1, left - rows * (k - 1)), min(rows, left - (k - 1)) + 1):
            for rest in splits(left - a, k - 1):
                yield (a,) + rest

    def cost(split):
        c, i = 0, 0
        for m in split:
            gs = groups[i:i + m]
            i += m
            kinds = set(gs)
            if len(kinds) > 1:
                c += 3 if "T" in kinds else 0
                for g in kinds:
                    if gs.count(g) == 1:
                        c += 10 if (g == "T" or "T" in kinds) else 2
        return (c, max(split) - min(split), tuple(-m for m in split))
    best = min(splits(n, ncol), key=cost)
    cols, i = [], 0
    for m in best:
        part = entries[i:i + m]
        i += m
        cols.append((max(27, 3.3 + 4.8 + max(width(t, 8.8) for _, t in part) + 5), part))
    return cols, cost(best)[0]


def key_width(cols, notes, wrap):
    lines = [ln for st, t in notes for ln in note_lines(st, t, wrap)]
    return 8 + sum(w for w, _ in cols) + NOTE_X + max(2.4 + width(t, 8.8) for t in lines) + 5


def key_depth(cols, notes, wrap):
    """From the first row's center to the last's: the longest pill column or the notes, with a wrapped note's second line."""
    rows = max([len(r) for _, r in cols] + [1])
    tail = WRAP_PITCH if wrap and notes and notes[-1][0] == "through" else 0.0
    return max(4.4 * (rows - 1), 4.4 * (len(notes) - 1) + tail)


KEY_ROOM = 1.1    # the Key may run this much wider than the drawing and header, to save rows...
KEY_MIN = 142.0   # ...and always this wide (10.6 in, between the Red and Orange posters): three columns of 20-odd pills and the notes
KEY_DEEP = 7      # a pill column deeper than this reads as a list, not a Key: only where nothing shallower fits


def key_plan(entries, notes, room):
    """The Key's columns, and whether the through-running note wraps. Each pill column holds at least as many rows as the
    notes column, at least 4, as on the line posters. Within the width it may take (KEY_ROOM times the drawing and header,
    and never less than KEY_MIN), the plan keeps its groups whole (no T and commuter lines in one column, no lone row), then
    no column past KEY_DEEP rows, then keeps the poster narrowest, then the Key shallowest, then the note on one line.
    Returns (columns, wrap)."""
    limit = max(KEY_ROOM * room, KEY_MIN)
    plans = []
    for wrap in (False, True):
        if wrap and not any(st == "through" for st, _ in notes):
            continue
        for rows in range(max(4, len(notes)), max(4, len(notes), len(entries)) + 1):  # more notes than pills: one plan, notes deep
            cols, c = key_columns(entries, rows)
            w = key_width(cols, notes, wrap)
            over = w > limit + 1e-6
            deep = max(len(r) for _, r in cols) > KEY_DEEP if cols else False
            rank = (over, w if over else 0.0, 0 if c == 0 else 1 if c < 10 else 2, deep,
                    round(max(room, w), 3), round(key_depth(cols, notes, wrap), 3), wrap, rows)
            plans.append((rank, cols, wrap))
    _rank, cols, wrap = min(plans, key=lambda p_: p_[0])
    return cols, wrap


def draw_key(ax, x0, x1, ky, cols, notes, wrap):
    ax.plot([x0 + 4, x1 - 4], [ky + 3.4, ky + 3.4], color=INK, lw=0.8, zorder=12)
    REG["line"].append(("Key rule", LineString([(x0 + 4, ky + 3.4), (x1 - 4, ky + 3.4)]).buffer(0.8 / PPU / 2)))
    cx = x0 + 8
    for pitch, rows in cols:
        for r, (pl, name) in enumerate(rows):
            cy = ky - 1.6 - r * 4.4
            # every sample the same 6.6 units, the fast-ferry one too: its white ring clears a lone F, and the column's
            # pills and names stay in line
            pill_shape(ax, cx - 3.3, cx + 3.3, cy, pl["fill"], 12, ring=pl.get("ring"), gold=pl.get("gold", False),
                       express=pl.get("express", False), rim=False)
            REG["pill"].append(("Key", box(cx - 3.3, cy - PH / 2, cx + 3.3, cy + PH / 2)))
            txt(ax, cx, cy - code_dy(pl.get("ring")), pl["code"], code_fs(pl["code"], pl.get("ring")), "bold", "center", "center", pl["fg"], z=13)
            txt(ax, cx + 4.8, cy - 0.05, name, 8.8, z=13)
        cx += pitch
    kx = cx + NOTE_X  # the icon's center
    for i, (st, t) in enumerate(notes):
        cy = ky - 1.6 - i * 4.4
        if st == "icon":
            M.icon(ax, kx, cy, z=13)
            REG["pill"].append(("Key icon", box(kx - 0.85, cy - 0.85, kx + 0.85, cy + 0.85)))
        elif st == "park":  # make_line_poster's P row: the sign where the icon sits, the note as far after it
            n0, p0 = len(ax.texts), len(ax.patches)
            LP.park(ax, kx, cy, z=13)
            grab(ax, n0)
            signs(ax, p0, "Key P sign")
        elif st == "cp":    # the Charlie Points coin where the icon sits
            draw_cp(ax, kx, cy, 1.0, z=13)
            REG["pill"].append(("Key CP coin", box(kx - 1.0, cy - 1.0, kx + 1.0, cy + 1.0)))
        for j, line in enumerate(note_lines(st, t, wrap)):
            txt(ax, kx + 2.4, cy - 0.05 - j * WRAP_PITCH, line, 8.8, z=13)


# ---------------------------------------------------------------------------------------------------------------
# Header
def header_need(key):
    return 52 + max(width(t, 27, "bold") for t in title(key).split("\n")) + 6 + release_width(9.6, PPU) + 5


def draw_header(ax, x0, y1, x1, key):
    """The T and NERTA mark, the code pill, the title, and at the top right the release block, or on the nerta.fun version
    (make_tmap.WEB) @mapzimus. The sheet is header_need wide either way, so the web version keeps the print version's size."""
    hy = y1 - 11
    color = GOLD if hsr(key) else RP.LINES[key]["hue"]
    RP.nerta_roundel(ax, x0 + 10, hy, 6.4)   # the multicolor T and NERTA pill, as on every map (November 8); the line's color is in the CR pill
    nb = draw_nerta(ax, x0 + 10, hy - (6.4 + 3.2 / 5.4 / 2) - 0.8, 2 * (6.4 + 3.2 / 5.4 / 2), "B", colors=M.NERTA_COLORS)
    REG["box"].append(("T and NERTA mark", box(x0 + 10 - 6.7, nb, x0 + 10 + 6.7, hy + 6.7)))
    ax.add_patch(FancyBboxPatch((x0 + 20, hy - 6), 28, 12, boxstyle="round,pad=0,rounding_size=6", fc=PURPLE, ec="none", zorder=12))
    if hsr(key):  # gold inside purple, as on every high-speed pill
        inset(ax, x0 + 20, x0 + 48, hy, 12, 1.5, GOLD, 12.1)
        ax.text(x0 + 34, hy - 0.4, "HSR", fontsize=34, fontweight="bold", color=PURPLE, ha="center", va="center", zorder=13)
    else:         # purple, the line's own color just inside the edge, purple again: the combined poster's CR pill
        inset(ax, x0 + 20, x0 + 48, hy, 12, 0.9, color, 12.1)
        inset(ax, x0 + 20, x0 + 48, hy, 12, 1.9, PURPLE, 12.2)
        ax.text(x0 + 34, hy - 0.4, "CR", fontsize=34, fontweight="bold", color=WHITE, ha="center", va="center", zorder=13)
    REG["box"].append(("code pill", box(x0 + 20, hy - 6, x0 + 48, hy + 6)))
    t = ax.text(x0 + 52, hy, title(key), fontsize=27, fontweight="bold", color=INK, ha="left", va="center", linespacing=1.1, zorder=13)
    TEXTS.append((t, None))
    title_right = x0 + 52 + max(width(s, 27, "bold") for s in title(key).split("\n"))
    if RP.NO_DISCLAIMER:
        # the "_no-disclaimer" final (Max, November 8): one note under the NERTA logo, left edge on the logo's; the release
        # block is measured, not drawn, and keeps its room, so every name sits where it does on the version with it
        txt(ax, x0 + 10 - RP.NERTA_HALF, nb - 1.0, RP.CONCEPT_NOTE, RP.NOTE_FS, va="top", z=13)
        left, bottom, top = draw_release(RP.NoDraw(), x1 - 5, hy, size=9.6, ppu=PPU, ink=INK)
        REG["box"].append(("release block room", box(left, bottom, x1 - 5, top)))
        what = "release block room"
    elif M.WEB:
        # nerta.fun, as make_line_poster does it: no release block; Max's name under the NERTA mark, and @mapzimus faint at
        # the header's middle, right-aligned where the release block's right edge would be
        have = [t_ for t_ in ax.texts if t_.get_text() == "Maxwell Howe"]   # site/tools/render_web_maps.py's draw_nerta may have drawn it
        if have:
            TEXTS.append((have[0], None))
        else:
            txt(ax, x0 + 10, nb - 1.0, "Maxwell Howe", 8.4, ha="center", va="top", z=13)
        txt(ax, x1 - 5, hy, "@mapzimus", 9.6, "bold", "right", "center", "#b9b9b4", z=13)
        what, left, bottom, top = "@mapzimus", x1 - 5 - width("@mapzimus", 9.6, "bold"), hy, hy
    else:
        # Release block on every map posted November 8 (Max): disclaimer, credit, hashtag, Day 8
        left, bottom, top = draw_release(ax, x1 - 5, hy, size=9.6, ppu=PPU, ink=INK)
        REG["box"].append(("release block", box(left, bottom, x1 - 5, top)))
        what = "release block"
    if left < title_right + 6 - 1e-6:   # the frame is at least header_need wide, so this only fires if that is broken
        print(f"  {what} is {title_right + 6 - left:.1f} units too close to the title")
    return left, bottom, top


# ---------------------------------------------------------------------------------------------------------------
# Checks
def check(fig, ax, frame):
    """Text on text, text on lines, dots and pills, pills on lines, dots and pills, names and pills nearer another stop's
    dot than their own, tilted text, and anything off the sheet."""
    fig.canvas.draw()
    rend, inv = fig.canvas.get_renderer(), ax.transData.inverted()
    X0, X1, Y0, Y1 = frame
    sheet = box(X0 + 1, Y0 + 1, X1 - 1, Y1 - 1)
    bad, shapes = [], []
    for t, owner in TEXTS:
        if t.get_rotation() != 0:
            bad.append("TILTED " + t.get_text())
        bb = t.get_window_extent(rend)
        (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        shapes.append((t.get_text().replace("\n", " ")[:30], box(x0, y0 + 0.3, x1, y1 - 0.3), owner))
    for n, bx in REG["box"]:  # the header's T, code pill and release block (its MOST is drawn as its own word, so it counts as one piece)
        if not bx.within(sheet):
            bad.append(f"off the sheet: {n}")
    for i, (a, sa, oa) in enumerate(shapes):
        if not sa.within(sheet):
            bad.append(f"off the sheet: {a}")
        for b, sb, ob in shapes[i + 1:]:
            if sa.intersects(sb):
                bad.append(f"text/text: {a} | {b}")
            elif sa.distance(sb) < 0.6:
                bad.append(f"text close: {a} | {b} ({sa.distance(sb):.2f})")
        for k_, ln in REG["line"]:
            if sa.intersection(ln).area > 0.005 or (k_ == "arrowhead" and sa.distance(ln) < 0.4):
                bad.append(f"text/line: {a} | {k_}")
        for n, d in REG["dot"]:
            if sa.intersection(d).area > 0.02:
                bad.append(f"text/dot: {a} | {n}")
        for n, pb in REG["pill"]:
            if sa.intersection(pb).area > 0.02 and not sa.within(pb.buffer(0.05)):
                bad.append(f"text/pill: {a} | pill at {n}")
        for n, bx in REG["box"]:
            if sa.intersection(bx).area > 0.02:
                bad.append(f"text/header: {a} | {n}")
        if oa:  # every name nearer its own dot than any other
            own = min(d.distance(sa) for n, d in REG["dot"] if n == oa)
            for n, d in REG["dot"]:
                if n != oa and d.distance(sa) + 0.05 < own:
                    bad.append(f"nearer dot: {a} is {d.distance(sa):.1f} from {n}, {own:.1f} from its own")
                    break
    for k, (pn, pb) in enumerate(REG["pill"]):
        if not pb.within(sheet):
            bad.append(f"pill off the sheet: {pn}")
        for k_, ln in REG["line"]:
            if pb.intersection(ln).area > 0.05:
                bad.append(f"pill/line: pill at {pn} | {k_}")
        for n, d in REG["dot"]:
            if pb.intersection(d).area > 0.05:
                bad.append(f"pill/dot: pill at {pn} | {n}")
        for qn, pc in REG["pill"][k + 1:]:
            if pb.intersection(pc).area > 0.05:
                bad.append(f"pill/pill: {pn} | {qn}")
        for n, bx in REG["box"]:
            if pb.intersection(bx).area > 0.02:
                bad.append(f"pill/header: {pn} | {n}")
    owners = {n for n, _ in REG["dot"]}
    for pn, pb in REG["pill"]:  # every stop's pill nearer its own dot than any other, as every name is (the Key's belong to no stop)
        if pn not in owners:
            continue
        own = min(d.distance(pb) for n, d in REG["dot"] if n == pn)
        for n, d in REG["dot"]:
            if n != pn and d.distance(pb) + 0.05 < own:
                bad.append(f"pill nearer dot: a pill at {pn} is {d.distance(pb):.1f} from {n}, {own:.1f} from its own")
                break
    for k_, ln in REG["line"]:
        if k_ == "Key rule":
            continue
        for n, bx in REG["box"]:
            if ln.intersection(bx).area > 0.02:
                bad.append(f"line/header: {k_} | {n}")
    dots = REG["dot"]
    for i, (a, da) in enumerate(dots):
        if not da.within(sheet):
            bad.append(f"dot off the sheet: {a}")
        for b, db in dots[i + 1:]:
            if a != b and da.intersects(db):
                bad.append(f"dot/dot: {a} | {b}")
    return bad


# ---------------------------------------------------------------------------------------------------------------
def reset():
    TEXTS.clear()
    for v in REG.values():
        v.clear()


def render(key, f):
    """Draw one poster with rows f times the house height. Returns the figure, its frame, flags and the stop table."""
    reset()
    lay = layout(key, f)
    xs = [q[0] for q in lay["pos"].values()]
    ys = [q[1] for q in lay["pos"].values()]
    wx0, wx1, wy0, wy1 = min(xs) - 220, max(xs) + 220, min(ys) - 120, max(ys) + 120   # working sheet; trimmed below
    fig = plt.figure(figsize=((wx1 - wx0) * K, (wy1 - wy0) * K))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(wx0, wx1)
    ax.set_ylim(wy0, wy1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.patch.set_facecolor(PAPER)
    used, table, wrapped, parked = draw_content(ax, lay)

    # The sheet fits the drawing, the header and the Key. The scale never changes, so type keeps its size.
    fig.canvas.draw()
    rend, inv = fig.canvas.get_renderer(), ax.transData.inverted()
    bx = [g.bounds for _, g in REG["line"] + REG["dot"] + REG["pill"]]
    for t, _ in TEXTS:
        bb = t.get_window_extent(rend)
        (a, b), (c, d) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        bx.append((a, b, c, d))
    cx0, cy0 = min(b[0] for b in bx) - 6, min(b[1] for b in bx)
    cx1, cy1 = max(b[2] for b in bx) + 6, max(b[3] for b in bx)
    entries = key_entries(key, used)
    fast = any(pl["code"] == "F" and fast_route(pl["fill"]) for pl, _ in entries)
    notes = key_notes(key, lay["stops"], bool(parked), fast)
    room = max(122, cx1 - cx0, header_need(key))
    cols, wrap = key_plan(entries, notes, room)
    need = max(room, key_width(cols, notes, wrap))
    if cx1 - cx0 < need:
        mid = (cx0 + cx1) / 2
        cx0, cx1 = mid - need / 2, mid + need / 2
    X0, X1 = cx0, cx1
    Y1 = max(max(ys) + 30, cy1 + 27)       # the header, with the NERTA mark under the T, clears the top of the drawing
    ky = min(min(ys) - 10, cy0 - 8.2)       # the Key, a rule's width under the drawing
    Y0 = ky - 1.6 - key_depth(cols, notes, wrap) - 8.2
    fig.set_size_inches((X1 - X0) * K, (Y1 - Y0) * K)
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    draw_header(ax, X0, Y1, X1, key)
    draw_key(ax, X0, X1, ky, cols, notes, wrap)
    bad = check(fig, ax, (X0, X1, Y0, Y1))
    return dict(fig=fig, frame=(X0, X1, Y0, Y1), bad=bad, table=table, wrapped=wrapped, parked=parked, lay=lay,
                key=dict(columns=[[name for _, name in rows] for _, rows in cols],
                         notes=[ln for st, t in notes for ln in note_lines(st, t, wrap)]))


def make(key):
    """Taller rows for short lines, so every poster stands upright (make_line_poster.STRETCH, worked out here), but never
    taller than the T posters' tallest rows. The sheet grows as the stops' span does; the room past a hub grows with the
    rows only once a row outgrows it (layout's step), so the row height is found by halving, not by a straight line."""
    r = render(key, 1.0)
    X0, X1, Y0, Y1 = r["frame"]
    w, h = X1 - X0, Y1 - Y0
    need = ASPECT * w - h
    if need > 0:
        s1 = u_span(key, 1.0)
        if u_span(key, FMAX) - s1 <= need:
            f = FMAX
        else:
            lo, hi = 1.0, FMAX
            for _ in range(30):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if u_span(key, mid) - s1 < need else (lo, mid)
            f = hi
        if f > 1.0001:
            plt.close(r["fig"])
            r = render(key, f)
    return r


def summary(key, r):
    lay = r["lay"]
    pos = lay["pos"]
    order = sorted(pos, key=lambda n: (-round(pos[n][1], 3), pos[n][0]))
    legs = []
    for lg in lay["legs"]:
        if lg["part"] != "trunk":
            legs.append(dict(junction=lg["junction"], stops=lg["stops"][1:], side="right" if lg["dx"] > 0 else "left",
                             kind="the main line's leg" if lg["part"] == "main" else "branch"))
    _stops, branches, arrows = route(key)
    runs = [dict(after=lay["stops"][-1], text=" ".join(t)) for t in arrows]
    runs += [dict(after=b["junction"], text=" ".join(b["arrow"])) for b in branches if b["arrow"]]
    trunk = lay["legs"][0]["stops"]
    X0, X1, Y0, Y1 = r["frame"]
    return dict(line=RP.LINES[key]["name"], title=title(key).replace("\n", " ").replace("/ ", "/"),
                orientation="far end at the top, Boston at the bottom" if key in UP else "Boston at the top",
                sheet_in=[round((X1 - X0) * K, 2), round((Y1 - Y0) * K, 2)], rows_scaled=round(lay["f"], 3),
                stops_top_to_bottom=[dict(name=n, column="trunk" if pos[n][0] == 0 else ("right" if pos[n][0] > 0 else "left") + " leg",
                                          end=n in lay["ends"]) for n in order],
                trunk_from_the_start=trunk, legs=legs, runs_on=runs, ends=sorted(lay["ends"]),
                pills={n: v for n, v in r["table"].items() if v}, pill_rows_where_wrapped=r["wrapped"],
                parking_sign=[n for n in order if n in r["parked"]],
                key=r["key"], flags=len(r["bad"]), flag_list=r["bad"])


def next_version(key, out=None):
    """The first N with neither rail_line_<key>_vN.png nor .pdf in out (output/copies by default)."""
    out = OUT if out is None else out
    v = 1
    while (out / f"rail_line_{key}_v{v}.png").exists() or (out / f"rail_line_{key}_v{v}.pdf").exists():
        v += 1
    return v


def take(args, flag):
    """Take `flag DIR` out of the arguments. Returns DIR, or None when the flag is not given."""
    if flag not in args:
        return None
    i = args.index(flag)
    if i + 1 >= len(args):
        raise SystemExit(f"{flag} needs a folder")
    folder = Path(args[i + 1])
    del args[i:i + 2]
    return folder


def main():
    args = sys.argv[1:]
    draft, out = take(args, "--draft"), take(args, "--out")
    if draft and out:
        raise SystemExit("--draft writes 150 dpi review copies, --out the 600 dpi PNG and PDF: choose one")
    out = out or OUT   # read now, not at import: site/tools/render_web_maps.py sets OUT to its own folder
    keys = args or KEYS
    unknown = [k for k in keys if k not in RP.LINES]
    if unknown:
        raise SystemExit(f"unknown line(s): {unknown}; choose from {KEYS}")
    setup()
    plt.rcParams["pdf.fonttype"] = 42
    report = {}
    for key in keys:
        r = make(key)
        X0, X1, Y0, Y1 = r["frame"]
        print(f"{key}: {RP.LINES[key]['name']}  sheet {(X1 - X0) * K:.1f} x {(Y1 - Y0) * K:.1f} in, rows x{r['lay']['f']:.2f}")
        for b in r["bad"]:
            print("   ", b)
        print(f"  {len(r['bad'])} flags")
        if draft:
            draft.mkdir(parents=True, exist_ok=True)
            png = draft / f"rail_line_{key}.png"
            r["fig"].savefig(png, dpi=150, facecolor=PAPER)
        else:
            v = next_version(key, out)
            png, pdf = out / f"rail_line_{key}_v{v}.png", out / f"rail_line_{key}_v{v}.pdf"
            for p_ in (png, pdf):
                if p_.exists():
                    raise SystemExit(f"refusing to overwrite {p_}")
            out.mkdir(parents=True, exist_ok=True)
            r["fig"].savefig(png, dpi=600, facecolor=PAPER)
            r["fig"].savefig(pdf, facecolor=PAPER)
        print("  written", png)
        report[key] = summary(key, r)
        plt.close(r["fig"])
    if draft:  # the stop table for reviewers: every line drawn in this run, merged into what is already there
        js = draft / "rail_line_stops.json"
        old = {}
        if js.exists():
            try:
                old = json.loads(js.read_text(encoding="utf-8"))
            except ValueError:
                old = {}
        old.update(report)
        js.write_text(json.dumps({k: old[k] for k in KEYS if k in old}, indent=1, ensure_ascii=False), encoding="utf-8")
        print("written", js)


if __name__ == "__main__":
    main()
