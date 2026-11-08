"""Line posters: one line drawn straight, with a pill for every transfer.

Stops, styles and colors are read from make_tmap.lines(), so a poster cannot disagree with the main map.
Only the layout (where each stop sits on the poster) is written here.
Run: python make_line_poster.py red
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Circle, FancyBboxPatch, Polygon
from matplotlib.textpath import TextPath
from shapely.geometry import LineString, Point

sys.path.insert(0, str(Path(__file__).parent))
from nerta_mark import draw_nerta, draw_t  # noqa: E402
import make_tmap as M  # noqa: E402
from station_kit import INK, WHITE, rounded, stroke  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "output"
P = 5.0        # one row of stops, in drawing units
K = 0.075      # inches per drawing unit
PPU = K * 72   # points per drawing unit
LWP = 12.0     # line width in points
LWU = LWP / PPU
CR_COLOR = M.CR_TEXT_COLOR
CODES = {M.ORANGE: "OL", M.BLUE: "BL", M.GREEN: "GL", M.YELLOW: "YL", M.CYAN: "CL", M.INDIGO: "IL", M.RED: "RL"}
PILL = {"HSR": CR_COLOR, "F": M.FERRY, "SL": M.SILVER, "OL": M.ORANGE, "BL": M.BLUE, "GL": M.GREEN, "YL": M.YELLOW, "CL": M.CYAN, "IL": M.INDIGO, "RL": M.RED, "CR": CR_COLOR}
NAMES = {"OL": "Orange Line", "BL": "Blue Line", "GL": "Green Line", "YL": "Yellow Line", "CL": "Cyan Line", "IL": "Indigo Line", "RL": "Red Line",
         "CR": "Commuter Rail", "HSR": "High-Speed Rail", "F": "Ferry", "SL": "Silver Line"}
ORDER = ["RL", "OL", "BL", "GL", "YL", "CL", "IL", "SL", "CR", "HSR", "F"]  # one order for the Key and for the pills at every station
TRANSFER_R = (LWP * 1.02 / 2 + 2.6 / 2) / PPU  # outer radius of a transfer ring, which hides the inner end of its first pill
END_R = (LWP * 1.35 / 2 + 3.4 / 2) / PPU       # outer radius of a terminal ring
RIM = 0.6 / PPU                                 # the paper edge round each pill, outside its fill


def g(x, row):
    return (x * P, -row * P)


def red_layout():
    """Each leg: stop names in main-map order, the drawn path, and where each stop sits. Label side, pill side."""
    a = 9.2                      # Alewife row
    j = a + 13                   # JFK/UMass row
    trunk = ["Alewife", "North Cambridge", "Davis", "Porter", "Harvard", "Central", "Kendall/MIT", "Charles/MGH", "Park Street", "Downtown Crossing",
             "South Station", "Broadway", "Andrew", "JFK/UMass"]
    ash = j + 4.1
    d = 0.8
    return [
        dict(stops=["Arlington Heights", "Lexington Ctr", "Lexington Route 128"], path=[g(4, 2), g(4, 0)], at=[g(4, 2), g(4, 1), g(4, 0)], side="r"),
        dict(stops=["Arlington Heights", "Arlington Ctr", "East Arlington", "Alewife"], path=[g(4, 2), g(4, 4.6), g(0, 8.6), g(0, a)],
             at=[g(4, 2), g(4, 3), g(4, 4), g(0, a)], side="r"),
        dict(stops=["Alewife", "Belmont Ctr", "Waverley Sq", "Waltham"], path=[g(0, a), g(0, 8.6), g(-4, 4.6), g(-4, 2)],
             at=[g(0, a), g(-4, 4), g(-4, 3), g(-4, 2)], side=["r", "l", "l", "l"]),
        dict(stops=trunk, path=[g(0, a), g(0, j)], at=[g(0, a + i) for i in range(14)], side="r"),
        # one path from JFK/UMass round the Ashmont bend to Mattapan, so the bend curves like every other corner (the Mattapan leg is not drawn again)
        dict(stops=["JFK/UMass", "Savin Hill", "Fields Corner", "Shawmut", "Ashmont"], path=[g(0, j), g(0, ash), g(-7 * d, ash + 7 * d)],
             at=[g(0, j)] + [g(0, j + 1.1 + i) for i in range(4)], side=["r", "l", "l", "l", "l"]),
        dict(stops=["Ashmont", "Cedar Grove", "Butler", "Milton", "Central Ave", "Valley Rd", "Capen St", "Mattapan"], path=[g(0, ash), g(-7 * d, ash + 7 * d)], draw=False,
             at=[g(-i * d, ash + i * d) for i in range(8)], side=["l"] * 7 + ["r"]),  # MATTAPAN reads right, so its OL pill sits clear of the incoming diagonal
        dict(stops=["JFK/UMass", "North Quincy", "Wollaston", "Quincy Center", "Quincy Adams", "Braintree"], path=[g(0, j), g(0, j + 0.4), g(4, j + 4.4), g(4, j + 9.1)],
             at=[g(0, j)] + [g(4, j + 5.1 + i) for i in range(5)], side="r"),
        dict(stops=["Braintree", "Weymouth"], path=[g(4, j + 9.1), g(4, j + 10.1)], at=[g(4, j + 9.1), g(4, j + 10.1)], side="r"),
    ]


def col(names, x, r0, dr=1.0):
    return [g(x, r0 + i * dr) for i in range(len(names))]


def stops_of(first, last):
    """The main-map stop list that runs from one stop to another."""
    for _, _, _, s in M.lines():
        if first in s and last in s:
            i, j = s.index(first), s.index(last)
            return s[i:j + 1] if i < j else s[j:i + 1][::-1]
    raise SystemExit(f"no line from {first} to {last}")


def orange_layout():
    r, t_ = stops_of("Reading", "Oak Grove"), stops_of("Oak Grove", "Forest Hills")
    sau, mat = stops_of("Malden Center", "Wonderland"), stops_of("Tufts Medical Ctr", "Mattapan")
    rd, vf = stops_of("Forest Hills", "Readville"), stops_of("Forest Hills", "VFW Parkway")
    k = len(r) - 1  # Oak Grove's row: the Reading section grew when Melrose/Cedar Park was added
    return [dict(stops=r, path=[g(0, 0), g(0, k)], at=col(r, 0, 0), side="l"),
            dict(stops=t_, path=[g(0, k), g(0, k + 19)], at=col(t_, 0, k), side="l"),
            # Branches drop straight down half a row before turning, so they run clear of the pills at Malden Center and Forest Hills
            dict(stops=sau, path=[g(0, k + 1), g(0, k + 1.5), g(0.5, k + 2), g(8, k + 2), g(8, k + 5)], at=[g(0, k + 1)] + col(sau[1:], 8, k + 2.6, 0.8), side="r"),
            dict(stops=mat, path=[g(0, k + 11), g(8, k + 11), g(8, k + 19)], at=[g(0, k + 11)] + col(mat[1:], 8, k + 12), side="r"),
            dict(stops=rd, path=[g(0, k + 19), g(0, k + 19.5), g(2, k + 21.5), g(2, k + 23.2)], at=[g(0, k + 19), g(2, k + 22.2), g(2, k + 23.2)], side="r"),  # Hyde Park on the straight
            dict(stops=vf, path=[g(0, k + 19), g(-6, k + 25)], at=[g(-1.2 * i, k + 19 + 1.2 * i) for i in range(6)], side=["l"] * 5 + ["r"])]  # VFW PARKWAY reads right, pill left


def blue_layout():
    w, c_, m_ = stops_of("West Station", "Charles/MGH"), stops_of("Charles/MGH", "Gov't Center"), stops_of("Gov't Center", "Wonderland")
    wi, ly, wy = stops_of("Orient Heights", "Winthrop Center"), stops_of("Wonderland", "Central Sq"), stops_of("Central Sq", "Wyoma Sq")
    return [dict(stops=w, path=[g(0, 0), g(0, 2)], at=col(w, 0, 0), side="l"),
            dict(stops=c_, path=[g(0, 2), g(0, 3)], at=col(c_, 0, 2), side="l"),
            dict(stops=m_, path=[g(0, 3), g(0, 13)], at=col(m_, 0, 3), side="l"),
            dict(stops=wi, path=[g(0, 9), g(8, 9), g(8, 10)], at=[g(0, 9), g(8, 10)], side="r"),
            dict(stops=ly, path=[g(0, 13), g(0, 15)], at=col(ly, 0, 13), side="l"),
            dict(stops=wy, path=[g(0, 15), g(0, 16)], at=col(wy, 0, 15), side="l")]


def green_layout():
    a_, b_ = stops_of("West Medford", "Medford/Tufts"), stops_of("Medford/Tufts", "Lechmere")
    tr_ = stops_of("Lechmere", "Kenmore")
    un, ha = stops_of("Lechmere", "Union Sq"), stops_of("Union Sq", "Harvard")
    hy, wa = stops_of("Hynes", "West Station"), stops_of("West Station", "Watertown")
    bl, cl = stops_of("Kenmore", "Boston College"), stops_of("St. Mary's St", "Cleveland Circle")
    dl, el = stops_of("Kenmore", "Riverside"), stops_of("Prudential", "Heath St")
    h1, h2, ne = stops_of("Heath St", "Hyde Sq"), stops_of("Hyde Sq", "Forest Hills"), stops_of("Eliot", "VFW Parkway")
    we, ba = stops_of("Boston College", "Weston"), stops_of("Riverside", "Wellesley Hills")
    return [dict(stops=a_, path=[g(0, 0), g(0, 2)], at=col(a_, 0, 0), side="r"),
            dict(stops=b_, path=[g(0, 2), g(0, 7)], at=col(b_, 0, 2), side="r"),
            dict(stops=tr_, path=[g(0, 7), g(0, 17)], at=col(tr_, 0, 7), side=["l" if n == "Copley" else "r" for n in tr_]),
            dict(stops=un, path=[g(0, 7), g(-6, 7)], at=[g(0, 7), g(-6, 7)], side="t"),
            dict(stops=ha, path=[g(-6, 7), g(-18, 7)], at=[g(-6, 7), g(-12, 7), g(-18, 7)], side="t"),
            dict(stops=hy, path=[g(0, 16), g(-9, 16)], at=[g(0, 16), g(-9, 16)], side="t"),
            dict(stops=wa, path=[g(-9, 16), g(-27, 16), g(-27, 20)], at=[g(-9, 16), g(-15, 16), g(-21, 16), g(-27, 18), g(-27, 19), g(-27, 20)], side=["t", "t", "t", "r", "r", "r"]),
            dict(stops=bl, path=[g(0, 17), g(-18, 17), g(-18, 33)], at=[g(0, 17)] + col(bl[1:], -18, 18), side="r"),
            dict(stops=cl, path=[g(-10, 17), g(-10, 30)], at=col(cl, -10, 18), side="r"),  # a column west of West Station, so CLEVELAND CIRCLE clears the Needham bend
            dict(stops=dl, path=[g(0, 17), g(0, 30)], at=col(dl, 0, 17), side="r"),
            dict(stops=el, path=[g(0, 15), g(9, 15), g(9, 26)], at=col(el, 9, 16), side="r"),
            dict(stops=h1, path=[g(9, 26), g(9, 27)], at=col(h1, 9, 26), side="r"),
            dict(stops=h2, path=[g(9, 27), g(9, 28)], at=col(h2, 9, 27), side="r"),
            dict(stops=ne, path=[g(0, 27), g(-3, 30), g(-3, 30 + len(ne))], at=[g(0, 27)] + col(ne[1:], -3, 32), side="l"),
            dict(stops=we, path=[g(-18, 33), g(-18, 36)], at=col(we, -18, 33), side="r"),
            dict(stops=ba, path=[g(0, 30), g(0, 31)], at=col(ba, 0, 30), side="r")]


def yellow_layout():
    """Yellow is a ring, drawn as a leaning parallelogram: long 45-degree sides, short top and base."""
    a_, b_ = stops_of("Lechmere", "West Station"), stops_of("West Station", "JFK/UMass")
    c_, d_ = stops_of("JFK/UMass", "Seaport"), stops_of("Seaport", "Terminals")
    e_, f_ = stops_of("Terminals", "Bellingham Sq"), stops_of("Bellingham Sq", "Lechmere")

    def left(r):
        return g(14 - r, r)

    def right(r):
        return g(25 - r, r)

    ups = [12.6 - 1.75 * k for k in range(7)]  # Seaport up to Everett Sq, clear of the base corner
    return [dict(stops=a_, path=[left(0), left(5)], at=[left(r) for r in range(6)], side=["t", "l", "l", "l", "l", "l"]),
            dict(stops=b_, path=[left(5), left(13)], at=[left(5 + k * 8 / 9) for k in range(10)], side="l"),
            dict(stops=c_, path=[left(13), left(14), right(14), right(ups[0])], at=[left(13), g(3, 14), g(8, 14), right(ups[0])], side=["l", "b", "b", "r"]),
            dict(stops=d_, path=[right(ups[0]), right(ups[1])], at=[right(ups[0]), right(ups[1])], side="r"),
            dict(stops=e_, path=[right(ups[1]), right(ups[4])], at=[right(ups[k]) for k in (1, 2, 3, 4)], side="r"),
            dict(stops=f_, path=[right(ups[4]), right(0), left(0)], at=[right(ups[k]) for k in (4, 5, 6)] + [g(23.6, 0), g(20.6, 0), g(16.7, 0), left(0)], side=["r", "r", "r", "up", "up", "up", "r"])]  # both acute corners now take one dash each, the same size (see tight_corners)


def cyan_layout():
    a_, b_ = stops_of("Assembly", "Seaport"), stops_of("Seaport", "Broadway")
    return [dict(stops=a_, path=[g(0, 0), g(0, 12)], at=col(a_, 0, 0), side="r"),
            dict(stops=b_, path=[g(0, 12), g(0, 17)], at=col(b_, 0, 12), side="r")]


def indigo_layout():
    a_ = stops_of("South Station", "Readville")
    return [dict(stops=a_, path=[g(0, 0), g(0, 8)], at=col(a_, 0, 0), side="r")]


def silver_layout():
    # Airport at the top, reading down to Logan Dock, the way the real airport maps run.
    a_ = ["Airport", "Rental Cars", "Terminal F", "Terminal E", "Terminal D", "Terminal C", "Terminal B", "Parking", "Terminals", "Terminal A", "Office Center", "Logan Dock"]
    return [dict(stops=a_, path=[g(0, 0), g(0, 11)], at=col(a_, 0, 0), side="r", style="dash")]


# Transfers a shared stop name can't reveal: commuter rail, high-speed rail, ferries, Silver, and Boston Central.
# High-speed rail only stops at Tier 1 and Tier 2 stations with a high-speed line: Boston Central, North, South, West and Back Bay.
# Wellesley Hills and Auburndale are Worcester Line stations (MBTA stop data), as on the main map.
EXTRA_TRANSFERS = {"West Medford": ["CR"], "Wellesley Hills": ["CR"], "Auburndale": ["CR"], "Porter": ["CR"], "South Station": ["CR", "HSR", "F"], "North Station": ["CR", "HSR", "F"], "Back Bay": ["CR", "HSR"], "West Station": ["CR", "HSR"],
                   "Ruggles": ["CR"], "Hyde Park": ["CR"], "Readville": ["CR"], "Sullivan Sq": ["CR"], "Chelsea": ["CR"], "Central Sq": ["CR"], "Reading": ["CR"], "Malden Center": ["CR"], "Oak Grove": ["CR"],
                   "JFK/UMass": ["CR"], "Quincy Center": ["CR"], "Braintree": ["CR"], "Waltham": ["CR"], "Aquarium": ["F"], "Maverick": ["F"], "Langone Ferryport": ["F"], "Wonderland": ["F"], "Courthouse": ["F"], "Kendall/MIT": ["F"],
                   "Lynn Harbor": ["F"], "Encore": ["F"], "Navy Yard": ["F"], "Harvard": ["F"], "BU Bridge": ["F"], "Stadium": ["F"],
                   "Suffolk Downs": ["F"], "Revere Beach": ["F"], "Beachmont": ["F"], "Airport": ["SL"], "Terminals": ["SL"], "Logan Dock": ["F"], "L Street": ["F"], "State": ["CL", "CR", "HSR"],
                   "Boston Central": ["BL", "OL", "CR", "HSR"]}
SILVER_LINKS = {"Airport": ["BL", "YL"], "Terminals": ["YL"], "Logan Dock": ["F"]}
SHOW = {"State": "Boston Central"}
FERRY_VIA = {"North Station": "Lovejoy Wharf", "Aquarium": "Long Wharf", "Maverick": "Piers Park", "Courthouse": "Fan Pier",
             "L Street": "Carson Beach", "Harvard": "Weld", "Kendall/MIT": "Ames St", "South Station": "Dorchester Ave"}  # dock has its own name
# Each ferry pill takes the color of the route that serves that station's dock on the main map (the main one where several call).
FERRY_COLOR = {"North Station": M.ROUTE_COLOR["hw"], "Aquarium": M.ROUTE_COLOR["hw"], "Langone Ferryport": M.ROUTE_COLOR["hw"], "Wonderland": M.ROUTE_COLOR["nse"], "South Station": M.ROUTE_COLOR["hw"],
               "Navy Yard": M.ROUTE_COLOR["charles"], "Harvard": M.ROUTE_COLOR["charles"], "BU Bridge": M.ROUTE_COLOR["charles"],
               "Kendall/MIT": M.ROUTE_COLOR["charles"], "Encore": M.ROUTE_COLOR["mystic"], "Stadium": M.ROUTE_COLOR["mystic"],
               "Suffolk Downs": M.ROUTE_COLOR["chelsea"], "Maverick": M.ROUTE_COLOR["eb"], "Logan Dock": M.ROUTE_COLOR["eb"],
               "Courthouse": M.ROUTE_COLOR["seaport"], "L Street": M.ROUTE_COLOR["sse"], "Revere Beach": M.ROUTE_COLOR["nse"],
               "Beachmont": M.ROUTE_COLOR["nse"], "Lynn Harbor": M.ROUTE_COLOR["nse"]}
for _dock, (_xy, _station, *_rest) in M.DOCKS.items():
    for _rt in M.FERRY_ROUTES:
        if _station and _dock in _rt["stops"]:
            FERRY_COLOR.setdefault(_station, _rt["color"])
            break
STRETCH = {"silver": 1.8, "indigo": 2.2, "cyan": 1.35, "blue": 1.35}  # short lines get taller rows so every poster stands upright
AFTER_NAME = {"Kenmore", "Lechmere"}  # a Green branch runs where the pill would sit, so it follows the station name
# Green branch letters at each terminal, as on the main map: A Watertown, B Weston, C Cleveland Circle, D Wellesley Hills and Harvard (via Union Sq), E Medford and Forest Hills, N Needham
BRANCH = {"Watertown": "A", "Weston": "B", "Cleveland Circle": "C", "Wellesley Hills": "D", "Harvard": "D", "West Medford": "E", "Forest Hills": "E", "VFW Parkway": "N"}
BRANCH_BELOW = {"Cleveland Circle"}  # the Needham line runs just past the name, so the letter sits under it
# Rider service notes in the Key's last column (Max, November 7). Every poster: the first two. An event line only where the line serves a venue.
SERVICE = [("icon", "Every station is accessible"), ("text", "Driverless maglev, 24 hours a day")]
EVENTS = {"orange": "Extra trains for TD Garden events", "green": "Extra trains for Fenway and TD Garden events",
          "yellow": "Extra trains for Stadium and Fenway events", "cyan": "Extra trains and boats for Stadium, Encore and TD Garden events"}
EXPRESS = "Express ferries stop at major ports only"  # on any poster with an express ferry pill
CAP = LWP * 0.62 / 2 / PPU  # the round cap a Key line sample grows at each end
NOTE_X = -3.3 + 0.85        # the notes column starts where the next pill column would: the icon's left edge on a pill's left edge
LAYOUTS = {"red": (M.RED, "RL", "Red" + chr(10) + "Line", red_layout, {"Mattapan", "Weymouth", "Waltham", "Lexington Route 128"}),
           "orange": (M.ORANGE, "OL", "Orange" + chr(10) + "Line", orange_layout, {"Reading", "Wonderland", "Mattapan", "Readville", "VFW Parkway"}),
           "blue": (M.BLUE, "BL", "Blue" + chr(10) + "Line", blue_layout, {"West Station", "Winthrop Center", "Wyoma Sq"}),
           "green": (M.GREEN, "GL", "Green" + chr(10) + "Line", green_layout, {"West Medford", "Harvard", "Watertown", "Weston", "Cleveland Circle", "Wellesley Hills", "Forest Hills", "VFW Parkway"}),
           "yellow": (M.YELLOW, "YL", "Yellow" + chr(10) + "Line", yellow_layout, set()),
           "cyan": (M.CYAN, "CL", "Cyan" + chr(10) + "Line", cyan_layout, {"Assembly", "Broadway"}),
           "indigo": (M.INDIGO, "IL", "Indigo" + chr(10) + "Line", indigo_layout, {"South Station", "Readville"}),
           "silver": (M.SILVER, "SL", "Silver" + chr(10) + "Line", silver_layout, {"Logan Dock", "Airport"})}


def transfers(color, key):
    out = {}
    for col, _style, _path, stops in M.lines():
        if col == color or col not in CODES:
            continue
        for n in stops:
            n = n.rstrip("+")
            out.setdefault(n, [])
            if CODES[col] not in out[n]:
                out[n].append(CODES[col])
    for n, extra in (SILVER_LINKS if key == "silver" else EXTRA_TRANSFERS).items():
        out.setdefault(n, [])
        out[n] += [c for c in extra if c not in out[n] and c != CODES.get(color, key.upper()[:2])]
    out = {n: sorted(c, key=ORDER.index) for n, c in out.items()}
    if key == "silver":
        return {n: out[n] for n in SILVER_LINKS}
    return out


def light(hexcolor):
    """True for a pale fill that needs dark text (lime, light purple): relative luminance over 0.4."""
    from matplotlib.colors import to_rgb
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in to_rgb(hexcolor)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2] > 0.4


def style_of(color, stops):
    for col_, style, _path, s in M.lines():
        if col_ == color and (set(stops) <= set(s)):
            return style
    raise SystemExit(f"poster leg not on the main map: {stops}")


def width(text, fs, weight="normal"):
    return TextPath((0, 0), text, size=fs, prop=FontProperties(family="Arial", weight=weight)).get_extents().width / PPU


def gold_core(ax, x0, x1, y, h, z):
    """High-speed pills copy the map line: gold inside commuter purple. Keeps them apart from Yellow Line pills."""
    r = 0.55
    ax.add_patch(FancyBboxPatch((x0 + r, y - h / 2 + r), x1 - x0 - 2 * r, h - 2 * r, boxstyle=f"round,pad=0,rounding_size={h / 2 - r}", fc=M.HSR, ec="none", zorder=z))


def pill_text(code, station):
    return f"F via {FERRY_VIA[station]}" if code == "F" and station in FERRY_VIA else code


def pill_w(code, station):
    text = pill_text(code, station)
    return 6.6 if text == code else width(text, 8.2, "bold") + 2.6


def pills_w(codes, station):
    """Length of a row of free pills, end to end."""
    return sum(pill_w(c, station) for c in codes) + 0.35 * (len(codes) - 1)


def pills(ax, x, y, codes, sign, station="", free=False, ring=TRANSFER_R, z=4):
    """Pills butt against the line on one side; each further pill tucks under the one before it.

    free: the row hangs on its own from x (no stop under its first pill). ring: radius of the stop's ring, which hides the first pill's inner end.
    Every label is centered on the stretch of its pill you can see along the middle row: from the ring, the pill before, or its own end, to its far end.
    High-speed pills center on their gold core.
    """
    h, gap = 2.9, 0.35
    near = x if free else x + sign * LWU / 2
    for i, code in enumerate(codes):
        w = pill_w(code, station)
        text = pill_text(code, station)
        far = near + sign * w
        tuck = near if free and i == 0 else near - sign * (LWU / 2 if i == 0 else h / 2 + gap)
        x0, x1 = sorted((tuck, far))
        ax.add_patch(FancyBboxPatch((x0, y - h / 2), x1 - x0, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=FERRY_COLOR.get(station, PILL[code]) if code == "F" else PILL[code], ec=M.PAPER, lw=1.2, zorder=z - 0.1 * i))
        if code == "HSR":
            gold_core(ax, x0, x1, y, h, z + 0.05 - 0.1 * i)
        seen = (tuck + sign * RIM if free else x + sign * ring) if i == 0 else near - sign * gap + sign * RIM
        end = far - sign * RIM
        if code == "HSR":
            seen, end = sign * max(sign * seen, sign * (tuck + sign * 0.55)), far - sign * 0.55
        ax.text((seen + end) / 2, y - 0.08, text, fontsize=8.6 if text == code else 8.2, fontweight="bold", color=CR_COLOR if code == "HSR" else INK if code == "YL" or (code == "F" and light(FERRY_COLOR.get(station, M.FERRY))) else WHITE, ha="center", va="center", zorder=z + 0.5)
        near = far + sign * gap


def branch_pill(ax, x, y, letter, sign=1):
    """GL plus the branch letter in a white circle, as on the main map, at transfer-pill size. x is the end nearest the name."""
    w, h = 9.0, 2.9
    x0 = x if sign > 0 else x - w
    ax.add_patch(FancyBboxPatch((x0, y - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=M.GREEN, ec="none", zorder=12))
    ax.text(x0 + 3.1, y - 0.08, "GL", fontsize=8.6, fontweight="bold", color=WHITE, ha="center", va="center", zorder=12.5)
    ax.add_patch(Circle((x0 + w - 2.2, y), 1.12, fc=WHITE, ec="none", zorder=12.4))
    ax.text(x0 + w - 2.2, y - 0.06, letter, fontsize=8.0, fontweight="bold", color=M.GREEN, ha="center", va="center", zorder=12.6)


def project(xy, p):
    """Distance along polyline xy to the point on it nearest p."""
    best, run = (np.inf, 0.0), 0.0
    for a, b in zip(xy, xy[1:]):
        d = b - a
        L = float(np.hypot(*d))
        t = 0.0 if L == 0 else float(np.clip(np.dot(np.asarray(p) - a, d) / L ** 2, 0, 1))
        e = float(np.hypot(*(a + t * d - p)))
        if e < best[0]:
            best = (e, run + t * L)
        run += L
    return best[1]


def piece(xy, cum, a, b):
    """The part of polyline xy (cum: running length at each vertex) from distance a to distance b."""
    def at(s):
        i = int(np.clip(np.searchsorted(cum, s) - 1, 0, len(cum) - 2))
        t = 0.0 if cum[i + 1] == cum[i] else (s - cum[i]) / (cum[i + 1] - cum[i])
        return xy[i] + t * (xy[i + 1] - xy[i])
    inner = [xy[i] for i in range(len(xy)) if a < cum[i] < b]
    return np.array([at(a)] + inner + [at(b)])


def tight_corners(path, r):
    """Corners that rounded(path, r) bends more tightly than half the line width. A dash that starts or ends on such a curve
    shows a notch on the inside, so dashed() runs one dash over the whole curve. Returns the curve's end points."""
    pts = [np.asarray(p, float) for p in path]
    out = []
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        u, v = a - b, c - b
        lu, lv = np.hypot(*u), np.hypot(*v)
        d = min(r, lu / 2, lv / 2)
        p0, p2 = b + u / lu * d, b + v / lv * d
        t = np.linspace(0, 1, 401)[:, None]
        d1 = 2 * (1 - t) * (b - p0) + 2 * t * (p2 - b)
        d2 = 2 * (p2 - 2 * b + p0)
        bend = np.abs(d1[:, 0] * d2[1] - d1[:, 1] * d2[0])
        radius = (np.hypot(*d1.T) ** 3 / np.maximum(bend, 1e-12)).min()
        if radius < LWU / 2 + 0.1:
            # run the dash on past the point where the two inside edges meet, so the inside reads as a clean V
            angle = np.arccos(np.clip(np.dot(u, v) / (lu * lv), -1, 1))
            out.append((p0, p2, max(0.4, LWU / 2 / np.tan(angle / 2) + 0.8 - d)))
    return out


def dashed(ax, xy, color, lw, marks=(), z=5, period=5.0, rings=(0.0, 0.0), corners=()):
    """Imagined service. A dash is centered on every stop in marks and on both ends of the leg; between them, evenly spaced dashes
    about one house period (5 units: 2/3 dash, 1/3 gap) apart, so no stop ever falls in a gap, however the stops are spaced.
    rings: radius of a terminal ring at the start and end, if any. There the dash is centered on the ring's edge and runs on into
    the ring, so the line visibly reaches its terminal instead of stopping a gap short of it. When that would squeeze the last
    stretch below 3.5 units a period, the dash stays centered on the terminal and the ring stands in for it.
    corners: (start, end, overrun) of curves too tight to cut (see tight_corners); one dash covers each, running on past both ends."""
    xy = np.asarray(xy, float)
    cum = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    total = cum[-1]
    reach = {}  # a corner mark's dash must reach this far either side of its center
    for p0, p2, past in corners:
        s0, s2 = project(xy, p0), project(xy, p2)
        reach[round((s0 + s2) / 2, 6)] = (s2 - s0) / 2 + past
    stops = sorted({0.0, total, *(round(project(xy, p), 6) for p in marks), *reach})
    stops = [s for i, s in enumerate(stops) if i == 0 or s - stops[i - 1] > 0.5]

    def pitch(a, b, ref=period):
        return (b - a) / max(1, round((b - a) / ref))

    refs = [period] * (len(stops) - 1)  # the period each stretch aims for; an end stretch matches its neighbor
    if len(stops) > 2:
        refs[0], refs[-1] = pitch(stops[1], stops[2]), pitch(stops[-3], stops[-2])
    skip = set()  # a dash centered on a terminal would only peek out of the ring as two corner nubs, so it is left out
    if rings[0]:
        if pitch(rings[0], stops[1], refs[0]) >= 3.5:
            stops[0] = rings[0]
        else:
            skip.add("first")
    if rings[1]:
        if pitch(stops[-2], total - rings[1], refs[-1]) >= 3.5:
            stops[-1] = total - rings[1]
        else:
            skip.add("last")
    centers = []  # (center, the spacing behind it, the spacing ahead of it)
    for (a, b), ref in zip(zip(stops, stops[1:]), refs):
        # next to a corner dash, space the stretch from the corner dash's end, so the gap beside it matches the others
        a_, b_ = a + reach.get(a, ref / 3) - ref / 3, b - reach.get(b, ref / 3) + ref / 3
        if b_ - a_ < ref / 2:
            a_, b_ = a, b
        k = max(1, round((b_ - a_) / ref))
        p = (b_ - a_) / k
        if a_ != a:
            centers.append([a, p, p])
        centers += [[a_ + j * p, p, p] for j in range(k)]
    centers.append([stops[-1], centers[-1][2], 0])
    for c0, c1 in zip(centers, centers[1:]):
        c1[1] = c0[2]
    for i, (c, back, ahead) in enumerate(centers):
        h = reach.get(round(c, 6), 0.0)
        a, b = max(0.0, c - max(back / 3, h)), min(total, c + max((ahead or back) / 3, h))
        a, b = (0.0 if i == 0 else a), (total if i == len(centers) - 1 else b)
        if (i == 0 and "first" in skip) or (i == len(centers) - 1 and "last" in skip):
            continue
        if b > a:
            pts = piece(xy, cum, a, b)
            # where this leg meets the next one at a plain stop, overlap it a little so no hairline seam shows across the dash
            if i == 0 and not rings[0]:
                pts = np.vstack([xy[0] - 0.2 * (xy[1] - xy[0]) / np.hypot(*(xy[1] - xy[0])), pts])
            if i == len(centers) - 1 and not rings[1]:
                pts = np.vstack([pts, xy[-1] + 0.2 * (xy[-1] - xy[-2]) / np.hypot(*(xy[-1] - xy[-2]))])
            # drawn as the true outline of the dash, so a dash round a tight corner keeps a clean inside edge (a stroke folds over itself there)
            shape = LineString(pts).buffer(lw / PPU / 2, cap_style=2, join_style=1, resolution=32)
            for part in getattr(shape, "geoms", [shape]):
                ax.add_patch(Polygon(np.asarray(part.exterior.coords), closed=True, fc=color, ec="none", zorder=z))


def name(ax, xy, text, side, bold, accessible, extra=0.0):
    """extra: more room between dot and name, for names beside a diagonal."""
    fs, weight = (12.6, "bold") if bold else (11.6, "normal")
    text = text.upper() if bold else text
    x, y = xy
    gap = (3.3 if not bold else 4.2) + extra
    up = 2.6 + (0.9 if bold else 0)  # names above or below a stop: bold ones sit 0.9 further out, as beside a stop
    w = width(text, fs, weight)
    if side == "up":  # level above the stop, pills run left underneath (no tilted labels)
        ax.text(x, y + up, text, fontsize=fs, fontweight=weight, color=INK, ha="center", va="bottom", zorder=11)
        return
    if side == "b":
        ax.text(x, y - up, text, fontsize=fs, fontweight=weight, color=INK, ha="center", va="top", zorder=11)
        return
    if side == "t":
        ax.text(x, y + up, text, fontsize=fs, fontweight=weight, color=INK, ha="center", va="bottom", zorder=11)
        if accessible:
            M.icon(ax, x - w / 2 - 1.5, y + 3.75)
        return
    s = 1 if side == "r" else -1
    ax.text(x + s * gap, y - 0.05, text, fontsize=fs, fontweight=weight, color=INK, ha="left" if s > 0 else "right", va="center", zorder=11)
    if accessible:
        M.icon(ax, x + s * (gap + w + 1.7), y)


def roundel(ax, x, y, r, color=None):
    ax.add_patch(Circle((x, y), r, fc=WHITE, ec=INK, lw=3.2, zorder=12))
    if color:  # NERTA's three-layer T in this line's color (Max, November 7)
        draw_t(ax, x, y, r, (color,), z=13)
        return
    a, b, c = r * 0.56, r * 0.2, r * 0.6
    ax.add_patch(Polygon([(x - a, y + c), (x + a, y + c), (x + a, y + c - 2 * b), (x + b, y + c - 2 * b), (x + b, y - c), (x - b, y - c), (x - b, y + c - 2 * b), (x - a, y + c - 2 * b)],
                         fc=INK, ec="none", zorder=13))


def leans_toward(legs, xy, side):
    """True when a 45-degree stretch of line leaves this stop on the side its name is on: the line then runs close under or over
    the name. main() moves such names 0.4 further out on Yellow's right side."""
    if side not in ("l", "r"):
        return False
    want = -1 if side == "l" else 1
    p = np.asarray(xy, float)
    for leg in legs:
        pts = np.asarray(leg["path"], float)
        for a, b in zip(pts, pts[1:]):
            d = b - a
            if abs(d[0]) < 1e-6 or abs(d[1]) < 1e-6:
                continue
            t = np.dot(p - a, d) / np.dot(d, d)
            if -1e-6 <= t <= 1 + 1e-6 and np.hypot(*(a + t * d - p)) < 1e-6:
                if (t < 1 - 1e-6 and np.sign(d[0]) == want) or (t > 1e-6 and np.sign(-d[0]) == want):
                    return True
    return False


def ferry_name(fill):
    """Key name for a ferry color, from the route list on the main map: "Inner Harbor ferry", "North Shore express ferry"."""
    for rt in M.FERRY_ROUTES:
        if rt["color"] == fill:
            head, _, tail = rt["title"].partition(", ")
            return f"{head} {'express ' if rt.get('fast') else ''}ferry" + (f", {tail}" if tail else "")
    return "Ferry"


def note_lead(st):
    """Key notes: text 2.4 after the icon's center, the same 1.5 gap a pill row leaves; plain notes line up with it.
    Line samples (only when not drawn as built) run 8 units from the icon's left edge."""
    return 2.4 if st in ("icon", "text") else -0.85 + 2 * CAP + 8 + 1.5


def key_layout(legs, tr, key):
    """Key rows: (fill, pill text, name) per transfer in ORDER, one ferry row per ferry color used; split into balanced columns of up to 4.
    Returns the rows, the columns as (pitch, rows), and the notes column: rider service notes as (kind, text)."""
    used, fills = set(), []
    for leg in legs:
        for n in leg["stops"]:
            codes = tr.get(n.rstrip("+"), [])
            used |= set(codes)
            fill = FERRY_COLOR.get(n, M.FERRY)
            if "F" in codes and fill not in fills:
                fills.append(fill)
    fills.sort(key=lambda c: [rt["color"] for rt in M.FERRY_ROUTES].index(c) if c in [rt["color"] for rt in M.FERRY_ROUTES] else 99)
    entries = []
    for c in sorted(used, key=ORDER.index):
        entries += [(f, "F", ferry_name(f)) for f in fills] if c == "F" else [(PILL[c], c, NAMES[c])]
    ncol = -(-len(entries) // 4)
    cols, i = [], 0
    for k in range(ncol):  # as even as can be: 10 rows go 4, 3, 3
        rows = entries[i:i + len(entries) // ncol + (k < len(entries) % ncol)]
        i += len(rows)
        cols.append((max(27, 3.3 + 4.8 + max(width(t, 8.8) for _, _, t in rows) + 5), rows))
    notes = ([] if M.BUILT else [("solid", "Service today"), ("stripe", "Planned: based on a real proposal"), ("dash", "Imagined")]) + SERVICE
    if key in EVENTS:
        notes.append(("text", EVENTS[key]))
    if any(c == "F" and any(rt["color"] == f and rt.get("fast") for rt in M.FERRY_ROUTES) for f, c, _ in entries):
        notes.append(("text", EXPRESS))
    return entries, cols, notes


def main(key):
    color, code, title, layout, ends = LAYOUTS[key]
    legs = layout()
    f = STRETCH.get(key, 1)
    for leg in legs:
        leg["path"] = [(p[0], p[1] * f) for p in leg["path"]]
        leg["at"] = [(p[0], p[1] * f) for p in leg["at"]]
    tr = transfers(color, key)
    xs = [p[0] for leg in legs for p in leg["path"]]
    ys = [p[1] for leg in legs for p in leg["path"]]
    x0, x1 = min(xs) - 40, max(xs) + 44
    left, right = x0, x1
    for leg in legs:
        sides = leg["side"] if isinstance(leg["side"], list) else [leg["side"]] * len(leg["stops"])
        for n, xy, side in zip(leg["stops"], leg["at"], sides):
            codes = tr.get(n.rstrip("+"), [])
            reach = LWU / 2 + sum(pill_w(c, n) + 0.35 for c in codes)
            if codes and side == "l":
                right = max(right, xy[0] + reach + 5)
            elif codes and side == "r":
                left = min(left, xy[0] - reach - 5)
    x0, x1 = left, right
    entries, cols, notes = key_layout(legs, tr, key)
    # Wide enough for the header row and the Key, centered on the drawing
    need = max(122, 8 + sum(w for w, _ in cols) + NOTE_X + max(note_lead(st) + width(t, 8.8) for st, t in notes) + 5)
    if x1 - x0 < need:
        x0, x1 = (x0 + x1) / 2 - need / 2, (x0 + x1) / 2 + need / 2
    y1 = max(ys) + 30  # the header, with the disclaimer under the NERTA mark, clears the top stop
    below = any(s == "b" for leg in legs for s in (leg["side"] if isinstance(leg["side"], list) else [leg["side"]]))
    ky = min(ys) - 10 - (3 if below else 0)  # names hung under the lowest stops need the same room above the Key as names beside them
    nrows = max([len(rows) for _, rows in cols] + [len(notes)])
    y0 = ky - 1.6 - 4.4 * (nrows - 1) - 8.2  # the Key is as tall as its longest column, with the same margin under its last row on every poster
    fig = plt.figure(figsize=((x1 - x0) * K, (y1 - y0) * K))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.patch.set_facecolor(M.PAPER)

    dot_at = {}  # a stop on a corner: its dot sits on the rounded curve, its name stays in line with the stops beside it
    for leg in legs:
        if leg.get("draw") is False:  # drawn by the leg before it
            continue
        xy_ = rounded(leg["path"], leg.get("r", 2.5), n=40)
        for n, p in zip(leg["stops"], leg["at"]):
            if p in leg["path"][1:-1]:
                q = LineString(xy_).interpolate(LineString(xy_).project(Point(p)))
                dot_at[n] = (q.x, q.y)
        style = "solid" if M.BUILT else (leg.get("style") or style_of(color, leg["stops"]))  # drawn as built (Max, November 7)
        if style == "dash":
            dashed(ax, xy_, color, LWP, leg["at"], z=5, rings=tuple(END_R if leg["stops"][k_] in ends else 0.0 for k_ in (0, -1)),
                   corners=tight_corners(leg["path"], leg.get("r", 2.5)))
        else:
            stroke(ax, xy_, color, LWP, style, z=5)
    done = set()
    for leg in legs:
        sides = leg["side"] if isinstance(leg["side"], list) else [leg["side"]] * len(leg["stops"])
        for n, xy, side in zip(leg["stops"], leg["at"], sides):
            if n in done:
                continue
            done.add(n)
            codes = tr.get(n.rstrip("+"), [])
            dot = dot_at.get(n, xy)
            if n in ends:
                ax.scatter(*dot, s=(LWP * 1.35) ** 2, color=WHITE, edgecolor=color, lw=3.4, zorder=9)
            elif codes:
                ax.scatter(*dot, s=(LWP * 1.02) ** 2, color=WHITE, edgecolor=INK, lw=2.6, zorder=9)
            else:
                ax.scatter(*dot, s=(LWP * 0.56) ** 2, color=WHITE, edgecolor=INK, lw=0.7, zorder=9)
            label = SHOW.get(n, M.TEXT.get(n, n)).replace("/" + chr(10), "/").replace(chr(10), " ").rstrip("+")  # "Charles/MGH" stays whole
            # Yellow's right side only: on its left side and on the Red and Orange branches the stops sit closer together, and the
            # extra room would carry a name toward the next stop's dot
            name(ax, xy, label, side, n in ends, False, 0.4 if key == "yellow" and side == "r" and leans_toward(legs, xy, side) else 0.0)
            bold = n in ends
            if key == "green" and n in BRANCH:
                tw = width(label.upper() if bold else label, 12.6 if bold else 11.6, "bold" if bold else "normal")
                if n in BRANCH_BELOW:
                    branch_pill(ax, xy[0] + 4.2, xy[1] - 3.6, BRANCH[n])
                elif side == "t":
                    branch_pill(ax, xy[0] + tw / 2 + 1.4, xy[1] + 2.6 + 0.9 + 0.85, BRANCH[n])
                else:
                    sg = 1 if side == "r" else -1
                    branch_pill(ax, xy[0] + sg * (4.2 + tw + 1.4), xy[1], BRANCH[n], sg)
            if not codes:
                continue
            if key == "green" and n in AFTER_NAME:
                pills(ax, xy[0] + 3.3 + width(label, 11.6) + 1.4, xy[1], codes, 1, n, free=True)
            elif side in ("l", "r"):
                # Yellow's sides lean at 45 degrees and cross the pills: there the pills sit on top of the line
                pills(ax, xy[0], xy[1], codes, 1 if side == "l" else -1, n, ring=END_R if bold else TRANSFER_R, z=6 if key == "yellow" else 4)
            elif key == "yellow" and side in ("t", "up"):
                # Yellow's top row: the pills hang under the line, away from the corner (left at the top row, right at Lechmere)
                pills(ax, xy[0], xy[1] - 3.9, codes, -1 if side == "up" else 1, n, free=True)
            else:
                # above a name on top ("t") or above the stop when the name hangs below ("b"): centered on the stop
                py = xy[1] + 7.8 + (0.9 if bold else 0) if side == "t" else xy[1] + 3.6
                pills(ax, xy[0] - pills_w(codes, n) / 2, py, codes, 1, n, free=True)

    # Header: the T, the NERTA mark under it, and the disclaimer under that on every poster (Max, November 7)
    hy = y1 - 11
    roundel(ax, x0 + 10, hy, 6.4, color)
    nb = draw_nerta(ax, x0 + 10, hy - (6.4 + 3.2 / 5.4 / 2) - 0.8, 2 * (6.4 + 3.2 / 5.4 / 2), "B", colors=(color,))  # NERTA mark under the T; returns its bottom
    if False:  # Max, November 7: the new T and NERTA style make it clear; the red tag is retired (CLAUDE.md rule pending update)
        ax.text(x0 + 10, nb - 1.0, "NOT A REAL" + chr(10) + "MBTA MAP", fontsize=9.6, fontweight="bold", color=M.RED, ha="center", va="top", linespacing=1.15, zorder=13)
    ax.add_patch(FancyBboxPatch((x0 + 20, hy - 6), 28, 12, boxstyle="round,pad=0,rounding_size=6", fc=color, ec="none", zorder=12))
    ax.text(x0 + 34, hy - 0.4, code, fontsize=38, fontweight="bold", color=INK if color == M.YELLOW else WHITE, ha="center", va="center", zorder=13)  # dark on yellow, as on every YL pill
    ax.text(x0 + 52, hy, title, fontsize=27, fontweight="bold", color=INK, ha="left", va="center", linespacing=1.1, zorder=13)  # 1.1 keeps Cyan's "y" off the dot of the "i"

    # Key: transfer pills in the house order (one ferry row per ferry color on this poster), in balanced columns, then the rider service notes
    ax.plot([x0 + 4, x1 - 4], [ky + 3.4, ky + 3.4], color=INK, lw=0.8, zorder=12)
    cx = x0 + 8
    for pitch, rows in cols:
        for r, (fill, c, t) in enumerate(rows):
            cy = ky - 1.6 - r * 4.4
            ax.add_patch(FancyBboxPatch((cx - 3.3, cy - 1.45), 6.6, 2.9, boxstyle="round,pad=0,rounding_size=1.45", fc=fill, ec="none", zorder=12))
            if c == "HSR":
                gold_core(ax, cx - 3.3, cx + 3.3, cy, 2.9, 12.5)
            ax.text(cx, cy - 0.08, c, fontsize=8.6, fontweight="bold", zorder=13, ha="center", va="center",
                    color=CR_COLOR if c == "HSR" else INK if c == "YL" or (c == "F" and light(fill)) else WHITE)
            ax.text(cx + 4.8, cy - 0.05, t, fontsize=8.8, color=INK, ha="left", va="center", zorder=13)
        cx += pitch
    kx = cx + NOTE_X  # the icon's center
    s0 = kx - 0.85 + CAP  # a line sample's round cap starts at the icon's left edge
    for i, (st, t) in enumerate(notes):
        cy = ky - 1.6 - i * 4.4
        if st == "dash":  # butt-ended, so it runs out to where the solid samples' round caps end: three dashes, two gaps
            seg = (8 + 2 * CAP) / 4
            for k_ in range(3):
                a = s0 - CAP + k_ * seg * 1.5
                ax.plot([a, a + seg], [cy, cy], color=color, lw=LWP * 0.62, solid_capstyle="butt", zorder=12)
        elif st == "icon":
            M.icon(ax, kx, cy)
        elif st != "text":
            stroke(ax, np.array([(s0, cy), (s0 + 8, cy)]), color, LWP * 0.62, st, z=12)
        ax.text(kx + note_lead(st), cy - 0.05, t, fontsize=8.8, color=INK, ha="left", va="center", zorder=13)
    if M.WEB:  # nerta.fun: name under NERTA, @mapzimus faint top right (no water on a line poster)
        ax.text(x0 + 10, nb - 1.0, "Maxwell Howe", fontsize=8.4, color=INK, ha="center", va="top", zorder=13)
        ax.text(x1 - 5, hy, "@mapzimus", fontsize=9.6, fontweight="bold", color="#b9b9b4", ha="right", va="center", zorder=13)
    else:
        ax.text(x1 - 5, hy + 2.2, "Map: Maxwell Howe", fontsize=9.6, color=INK, ha="right", va="center", zorder=13)
        ax.text(x1 - 5, hy - 2.2, "#30DayMapChallenge Day 8 \u2022 Utopia", fontsize=9.6, color=INK, ha="right", va="center", zorder=13)  # kept for the release (Max)

    plt.rcParams["pdf.fonttype"] = 42
    fig.savefig(OUT / f"line_{key}.png", dpi=600, facecolor=M.PAPER)
    fig.savefig(OUT / f"line_{key}.pdf", facecolor=M.PAPER)
    print("written", f"line_{key}.png")
    for n in done:
        if tr.get(n):
            print(f"  {n}: {' '.join(tr[n])}")


if __name__ == "__main__":
    for k in (sys.argv[1:] or LAYOUTS):
        main(k)
