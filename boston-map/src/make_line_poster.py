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

sys.path.insert(0, str(Path(__file__).parent))
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
         "CR": "Commuter Rail", "HSR": "High-speed rail", "F": "Ferry", "SL": "Silver Line"}


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
        dict(stops=["JFK/UMass", "Savin Hill", "Fields Corner", "Shawmut", "Ashmont"], path=[g(0, j), g(0, ash)],
             at=[g(0, j)] + [g(0, j + 1.1 + i) for i in range(4)], side=["r", "l", "l", "l", "l"]),
        dict(stops=["Ashmont", "Cedar Grove", "Butler", "Milton", "Central Ave", "Valley Rd", "Capen St", "Mattapan"], path=[g(0, ash), g(-7 * d, ash + 7 * d)],
             at=[g(-i * d, ash + i * d) for i in range(8)], side="l"),
        dict(stops=["JFK/UMass", "North Quincy", "Wollaston", "Quincy Center", "Quincy Adams", "Braintree"], path=[g(0, j), g(0, j + 0.4), g(4, j + 4.4), g(4, j + 10.1)],
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
    return [dict(stops=r, path=[g(0, 0), g(0, 5)], at=col(r, 0, 0), side="l"),
            dict(stops=t_, path=[g(0, 5), g(0, 24)], at=col(t_, 0, 5), side="l"),
            dict(stops=sau, path=[g(0, 6), g(8, 6), g(8, 10)], at=[g(0, 6)] + col(sau[1:], 8, 7), side="r"),
            dict(stops=mat, path=[g(0, 16), g(8, 16), g(8, 24)], at=[g(0, 16)] + col(mat[1:], 8, 17), side="r"),
            dict(stops=rd, path=[g(0, 24), g(2, 26), g(2, 27)], at=[g(0, 24), g(2, 26), g(2, 27)], side="r"),
            dict(stops=vf, path=[g(0, 24), g(-6, 30)], at=[g(-1.2 * i, 24 + 1.2 * i) for i in range(6)], side="l")]


def blue_layout():
    w, c_, m_ = stops_of("West Station", "Charles/MGH"), stops_of("Charles/MGH", "Gov't Center"), stops_of("Gov't Center", "Wonderland")
    wi, ly, wy = stops_of("Orient Heights", "Winthrop Center"), stops_of("Wonderland", "Lynn"), stops_of("Lynn", "Wyoma Sq")
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
    return [dict(stops=a_, path=[g(0, 0), g(0, 2)], at=col(a_, 0, 0), side="r"),
            dict(stops=b_, path=[g(0, 2), g(0, 7)], at=col(b_, 0, 2), side="r"),
            dict(stops=tr_, path=[g(0, 7), g(0, 17)], at=col(tr_, 0, 7), side=["l" if n == "Copley" else "r" for n in tr_]),
            dict(stops=un, path=[g(0, 7), g(-6, 7)], at=[g(0, 7), g(-6, 7)], side="t"),
            dict(stops=ha, path=[g(-6, 7), g(-18, 7)], at=[g(-6, 7), g(-12, 7), g(-18, 7)], side="t"),
            dict(stops=hy, path=[g(0, 16), g(-9, 16)], at=[g(0, 16), g(-9, 16)], side="t"),
            dict(stops=wa, path=[g(-9, 16), g(-27, 16), g(-27, 20)], at=[g(-9, 16), g(-15, 16), g(-21, 16), g(-27, 18), g(-27, 19), g(-27, 20)], side=["t", "t", "t", "r", "r", "r"]),
            dict(stops=bl, path=[g(0, 17), g(-18, 17), g(-18, 33)], at=[g(0, 17)] + col(bl[1:], -18, 18), side="r"),
            dict(stops=cl, path=[g(-9, 17), g(-9, 30)], at=col(cl, -9, 18), side="r"),
            dict(stops=dl, path=[g(0, 17), g(0, 30)], at=col(dl, 0, 17), side="r"),
            dict(stops=el, path=[g(0, 15), g(9, 15), g(9, 26)], at=col(el, 9, 16), side="r"),
            dict(stops=h1, path=[g(9, 26), g(9, 27)], at=col(h1, 9, 26), side="r"),
            dict(stops=h2, path=[g(9, 27), g(9, 28)], at=col(h2, 9, 27), side="r"),
            dict(stops=ne, path=[g(0, 27), g(-3, 30), g(-3, 35)], at=[g(0, 27)] + col(ne[1:], -3, 32), side="l")]


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
            dict(stops=f_, path=[right(ups[4]), right(0), left(0)], at=[right(ups[k]) for k in (4, 5, 6)] + [g(24, 0), g(22.4, 0), g(19.4, 0), g(17, 0), left(0)], side=["r", "r", "r", "up", "up", "up", "up", "r"])]


def cyan_layout():
    a_, b_ = stops_of("Assembly", "Seaport"), stops_of("Seaport", "Broadway")
    return [dict(stops=a_, path=[g(0, 0), g(0, 12)], at=col(a_, 0, 0), side="r"),
            dict(stops=b_, path=[g(0, 12), g(0, 17)], at=col(b_, 0, 12), side="r")]


def indigo_layout():
    a_ = stops_of("South Station", "Readville")
    return [dict(stops=a_, path=[g(0, 0), g(0, 8)], at=col(a_, 0, 0), side="r")]


def silver_layout():
    a_ = ["Logan Dock", "Office Center", "Terminal A", "Terminals", "Parking", "Terminal B", "Terminal C", "Terminal D", "Terminal E", "Terminal F", "Rental Cars", "Airport"]
    return [dict(stops=a_, path=[g(0, 0), g(0, 11)], at=col(a_, 0, 0), side="r", style="dash")]


# Transfers a shared stop name can't reveal: commuter rail, high-speed rail, ferries, Silver, and Boston Central.
# High-speed rail only stops at Tier 1 and Tier 2 stations with a high-speed line: Boston Central, North, South, West and Back Bay.
EXTRA_TRANSFERS = {"West Medford": ["CR"], "Porter": ["CR"], "South Station": ["CR", "HSR"], "North Station": ["CR", "HSR", "F"], "Back Bay": ["CR", "HSR"], "West Station": ["CR", "HSR"],
                   "Ruggles": ["CR"], "Hyde Park": ["CR"], "Readville": ["CR"], "Sullivan Sq": ["CR"], "Chelsea": ["CR"], "Lynn": ["CR"],
                   "JFK/UMass": ["CR", "F"], "Quincy Center": ["CR"], "Braintree": ["CR"], "Waltham": ["CR"], "North Quincy": ["F"], "Aquarium": ["F"], "Maverick": ["F"], "North End": ["F"],
                   "Lynn Harbor": ["F"], "Encore": ["F"], "Navy Yard": ["F"], "Seaport": ["F"], "Airport": ["SL"], "Terminals": ["SL"], "Logan Dock": ["F"], "State": ["CL", "CR", "HSR"],
                   "Boston Central": ["BL", "OL", "CR", "HSR"]}
SILVER_LINKS = {"Airport": ["BL", "YL"], "Terminals": ["YL"], "Logan Dock": ["F"]}
SHOW = {"State": "Boston Central"}
FERRY_VIA = {"North Station": "Lovejoy Wharf", "Aquarium": "Long Wharf", "Maverick": "Lewis Mall", "JFK/UMass": "Columbia Point", "North Quincy": "Squantum Point"}  # dock has its own name
STRETCH = {"silver": 1.8, "indigo": 2.2, "cyan": 1.35, "blue": 1.35}  # short lines get taller rows so every poster stands upright
AFTER_NAME = {"Kenmore", "Lechmere"}  # a Green branch runs where the pill would sit, so it follows the station name
LAYOUTS = {"red": (M.RED, "RL", "Red" + chr(10) + "Line", red_layout, {"Mattapan", "Weymouth", "Waltham", "Lexington Route 128"}),
           "orange": (M.ORANGE, "OL", "Orange" + chr(10) + "Line", orange_layout, {"Reading", "Wonderland", "Mattapan", "Readville", "VFW Parkway"}),
           "blue": (M.BLUE, "BL", "Blue" + chr(10) + "Line", blue_layout, {"West Station", "Winthrop Center", "Wyoma Sq"}),
           "green": (M.GREEN, "GL", "Green" + chr(10) + "Line", green_layout, {"West Medford", "Harvard", "Watertown", "Boston College", "Cleveland Circle", "Riverside", "Forest Hills", "VFW Parkway"}),
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
    if key == "silver":
        return {n: out[n] for n in SILVER_LINKS}
    return out


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


def pills(ax, x, y, codes, sign, station="", free=False):
    """Pills butt against the line on one side; each further pill tucks under the one before it."""
    h, gap = 2.9, 0.35
    near = x + sign * LWU / 2
    for i, code in enumerate(codes):
        w = pill_w(code, station)
        text = pill_text(code, station)
        far = near + sign * w
        tuck = near if free and i == 0 else near - sign * (LWU / 2 if i == 0 else h / 2 + gap)
        x0, x1 = sorted((tuck, far))
        ax.add_patch(FancyBboxPatch((x0, y - h / 2), x1 - x0, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=PILL[code], ec=M.PAPER, lw=1.2, zorder=4 - 0.1 * i))
        if code == "HSR":
            gold_core(ax, x0, x1, y, h, 4.05 - 0.1 * i)
        ax.text((near + far) / 2 + (0 if free else sign * 0.25), y - 0.08, text, fontsize=8.6 if text == code else 8.2, fontweight="bold", color=CR_COLOR if code == "HSR" else INK if code == "YL" else WHITE, ha="center", va="center", zorder=4.5)
        near = far + sign * gap


def name(ax, xy, text, side, bold, accessible):
    fs, weight = (12.6, "bold") if bold else (11.6, "normal")
    text = text.upper() if bold else text
    x, y = xy
    gap = 3.3 if not bold else 4.2
    w = width(text, fs, weight)
    if side == "up":
        ax.text(x + 0.2, y + 2.3, text, fontsize=fs, fontweight=weight, color=INK, ha="left", va="bottom", rotation=45, rotation_mode="anchor", zorder=11)
        if accessible:
            M.icon(ax, x + 0.2 + (w - 0.4) * 0.707 + 1.4, y + 2.3 + (w - 0.4) * 0.707 + 0.6)
        return
    if side == "b":
        ax.text(x, y - 2.6, text, fontsize=fs, fontweight=weight, color=INK, ha="center", va="top", zorder=11)
        return
    if side == "t":
        ax.text(x, y + 2.6, text, fontsize=fs, fontweight=weight, color=INK, ha="center", va="bottom", zorder=11)
        if accessible:
            M.icon(ax, x - w / 2 - 1.5, y + 3.75)
        return
    s = 1 if side == "r" else -1
    ax.text(x + s * gap, y - 0.05, text, fontsize=fs, fontweight=weight, color=INK, ha="left" if s > 0 else "right", va="center", zorder=11)
    if accessible:
        M.icon(ax, x + s * (gap + w + 1.7), y)


def roundel(ax, x, y, r):
    ax.add_patch(Circle((x, y), r, fc=WHITE, ec=INK, lw=3.2, zorder=12))
    a, b, c = r * 0.56, r * 0.2, r * 0.6
    ax.add_patch(Polygon([(x - a, y + c), (x + a, y + c), (x + a, y + c - 2 * b), (x + b, y + c - 2 * b), (x + b, y - c), (x - b, y - c), (x - b, y + c - 2 * b), (x - a, y + c - 2 * b)],
                         fc=INK, ec="none", zorder=13))


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
    all_codes = set()
    for leg in legs:
        sides = leg["side"] if isinstance(leg["side"], list) else [leg["side"]] * len(leg["stops"])
        for n, xy, side in zip(leg["stops"], leg["at"], sides):
            codes = tr.get(n.rstrip("+"), [])
            all_codes |= set(codes)
            reach = LWU / 2 + sum(pill_w(c, n) + 0.35 for c in codes)
            if codes and side == "l":
                right = max(right, xy[0] + reach + 5)
            elif codes and side == "r":
                left = min(left, xy[0] - reach - 5)
    x0, x1 = left, right
    # Wide enough for the header row and the Key, centered on the drawing
    need = max(122, 8 + (len(all_codes) + 3) // 4 * 27 + 3 + 7.4 + 30 + 5)
    if x1 - x0 < need:
        x0, x1 = (x0 + x1) / 2 - need / 2, (x0 + x1) / 2 + need / 2
    y1 = max(ys) + 26
    y0 = min(ys) - 31
    fig = plt.figure(figsize=((x1 - x0) * K, (y1 - y0) * K))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.patch.set_facecolor(M.PAPER)

    for leg in legs:
        stroke(ax, rounded(leg["path"], 2.5), color, LWP, leg.get("style") or style_of(color, leg["stops"]), z=5)
    done, used = set(), []
    for leg in legs:
        sides = leg["side"] if isinstance(leg["side"], list) else [leg["side"]] * len(leg["stops"])
        for n, xy, side in zip(leg["stops"], leg["at"], sides):
            if n in done:
                continue
            done.add(n)
            codes = tr.get(n.rstrip("+"), [])
            used += [c for c in codes if c not in used]
            if n in ends:
                ax.scatter(*xy, s=(LWP * 1.35) ** 2, color=WHITE, edgecolor=color, lw=3.4, zorder=9)
            elif codes:
                ax.scatter(*xy, s=(LWP * 1.02) ** 2, color=WHITE, edgecolor=INK, lw=2.6, zorder=9)
            else:
                ax.scatter(*xy, s=(LWP * 0.56) ** 2, color=WHITE, edgecolor=INK, lw=0.7, zorder=9)
            name(ax, xy, SHOW.get(n, M.TEXT.get(n, n)).replace(chr(10), " ").rstrip("+"), side, n in ends, False)
            if codes:
                sign = 1 if side == "l" else -1
                if key == "green" and n in AFTER_NAME:
                    pills(ax, xy[0] + 3.3 + width(n, 11.6) + 1.4 - LWU / 2, xy[1], codes, 1, n, free=True)
                    continue
                pills(ax, xy[0], xy[1], codes, sign, n) if side not in ("t", "b", "up") else pills(ax, xy[0], (xy[1] - 3.9 if key == "yellow" else xy[1] + 7.8) if side in ("t", "up") else xy[1] + 3.6, codes, -1 if side == "up" else 1)

    # Header
    hy = y1 - 11
    roundel(ax, x0 + 10, hy, 6.4)
    ax.add_patch(FancyBboxPatch((x0 + 20, hy - 6), 28, 12, boxstyle="round,pad=0,rounding_size=6", fc=color, ec="none", zorder=12))
    ax.text(x0 + 34, hy - 0.4, code, fontsize=38, fontweight="bold", color=WHITE, ha="center", va="center", zorder=13)
    ax.text(x0 + 52, hy, title, fontsize=27, fontweight="bold", color=INK, ha="left", va="center", linespacing=0.9, zorder=13)

    # Key
    ky = y0 + 21
    ax.plot([x0 + 4, x1 - 4], [ky + 3.4, ky + 3.4], color=INK, lw=0.8, zorder=12)
    for i, c in enumerate(used):
        cx, cy = x0 + 8 + (i // 4) * 27, ky - 1.6 - (i % 4) * 4.4
        ax.add_patch(FancyBboxPatch((cx - 3.3, cy - 1.45), 6.6, 2.9, boxstyle="round,pad=0,rounding_size=1.45", fc=PILL[c], ec="none", zorder=12))
        if c == "HSR":
            gold_core(ax, cx - 3.3, cx + 3.3, cy, 2.9, 12.5)
        ax.text(cx, cy - 0.08, c, fontsize=8.6, fontweight="bold", color=CR_COLOR if c == "HSR" else INK if c == "YL" else WHITE, ha="center", va="center", zorder=13)
        ax.text(cx + 4.8, cy - 0.05, NAMES[c], fontsize=8.8, color=INK, ha="left", va="center", zorder=13)
    kx = x0 + 8 + ((len(used) + 3) // 4) * 27 + 3
    for i, (st, t) in enumerate((("solid", "Running today"), ("stripe", "New: real proposal"), ("dash", "New: imagined"))):
        cy = ky - 1.6 - i * 4.4
        stroke(ax, np.array([(kx - 3, cy), (kx + 5, cy)]), color, LWP * 0.62, st, z=12)
        ax.text(kx + 7.4, cy - 0.05, t, fontsize=8.8, color=INK, ha="left", va="center", zorder=13)
    M.icon(ax, kx + 1, ky - 1.6 - 3 * 4.4)
    ax.text(kx + 7.4, ky - 1.65 - 3 * 4.4, "All stations accessible", fontsize=8.8, color=INK, ha="left", va="center", zorder=13)
    ax.text(x1 - 5, hy + 4, "Map: Maxwell Howe", fontsize=9.6, color=INK, ha="right", va="center", zorder=13)
    ax.text(x1 - 5, hy, "#30DayMapChallenge Day 8 • Utopia", fontsize=9.6, color=INK, ha="right", va="center", zorder=13)
    ax.text(x1 - 5, hy - 4, "NOT A REAL MBTA MAP", fontsize=9.6, fontweight="bold", color=M.RED, ha="right", va="center", zorder=13)

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
