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
PILL = {"OL": M.ORANGE, "BL": M.BLUE, "GL": M.GREEN, "YL": M.YELLOW, "CL": M.CYAN, "IL": M.INDIGO, "RL": M.RED, "CR": CR_COLOR}
NAMES = {"OL": "Orange Line", "BL": "Blue Line", "GL": "Green Line", "YL": "Yellow Line", "CL": "Cyan Line", "IL": "Indigo Line", "RL": "Red Line",
         "CR": "Commuter Rail"}


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
        dict(stops=["Lexington Route 128", "Trapelo Rd", "Waltham"], path=[g(4, 0), g(4, -1.6), g(-4, -1.6), g(-4, 2)],
             at=[g(4, 0), g(0, -1.6), g(-4, 2)], side=["r", "t", "l"]),
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


# Transfers the main map draws that a shared stop name cannot reveal: commuter rail, and stations joined by a transfer pill.
EXTRA_TRANSFERS = {"red": {"Porter": ["CR"], "South Station": ["CL", "CR"], "JFK/UMass": ["CR"], "Quincy Center": ["CR"], "Braintree": ["CR"], "Waltham": ["CR"]}}
LAYOUTS = {"red": (M.RED, "RL", "Red\nLine", red_layout)}


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
    for n, extra in EXTRA_TRANSFERS.get(key, {}).items():
        out.setdefault(n, [])
        out[n] += [c for c in extra if c not in out[n]]
    return out


def style_of(color, stops):
    for col, style, _path, s in M.lines():
        if col == color and (s == stops or s == stops[::-1]):
            return style
    raise SystemExit(f"poster leg not on the main map: {stops}")


def width(text, fs, weight="normal"):
    return TextPath((0, 0), text, size=fs, prop=FontProperties(family="Arial", weight=weight)).get_extents().width / PPU


def pills(ax, x, y, codes, sign):
    """Pills butt against the line on one side; each further pill tucks under the one before it."""
    h, w, gap = 2.9, 6.6, 0.35
    for i, code in enumerate(codes):
        near = x + sign * (LWU / 2 + i * (w + gap))
        far = near + sign * w
        tuck = near - sign * (LWU / 2 if i == 0 else h / 2 + gap)
        x0, x1 = sorted((tuck, far))
        ax.add_patch(FancyBboxPatch((x0, y - h / 2), x1 - x0, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=PILL[code], ec=M.PAPER, lw=1.2, zorder=4 - 0.1 * i))
        ax.text((near + far) / 2 + sign * 0.25, y - 0.08, code, fontsize=8.6, fontweight="bold", color=INK if code == "YL" else WHITE, ha="center", va="center", zorder=4.5)


def name(ax, xy, text, side, bold, accessible):
    fs, weight = (12.6, "bold") if bold else (11.6, "normal")
    text = text.upper() if bold else text
    x, y = xy
    gap = 3.3 if not bold else 4.2
    w = width(text, fs, weight)
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
    color, code, title, layout = LAYOUTS[key]
    legs = layout()
    tr = transfers(color, key)
    barred = M.not_accessible()
    ends = {n for n, c in M.ENDS.items() if c == color}
    xs = [p[0] for leg in legs for p in leg["path"]]
    ys = [p[1] for leg in legs for p in leg["path"]]
    x0, x1 = min(xs) - 36, max(xs) + 36
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
        stroke(ax, rounded(leg["path"], 2.5), color, LWP, style_of(color, leg["stops"]), z=5)
    done, used = set(), []
    for leg in legs:
        sides = leg["side"] if isinstance(leg["side"], list) else [leg["side"]] * len(leg["stops"])
        for n, xy, side in zip(leg["stops"], leg["at"], sides):
            if n in done:
                continue
            done.add(n)
            codes = tr.get(n, [])
            used += [c for c in codes if c not in used]
            if n in ends:
                ax.scatter(*xy, s=(LWP * 1.35) ** 2, color=WHITE, edgecolor=color, lw=3.4, zorder=9)
            elif codes:
                ax.scatter(*xy, s=(LWP * 1.02) ** 2, color=WHITE, edgecolor=INK, lw=2.6, zorder=9)
            else:
                ax.scatter(*xy, s=(LWP * 0.56) ** 2, color=WHITE, edgecolor=INK, lw=0.7, zorder=9)
            name(ax, xy, n, side, n in ends, n not in barred)
            if codes:
                sign = 1 if side == "l" else -1
                pills(ax, xy[0], xy[1], codes, sign) if side != "t" else pills(ax, xy[0], xy[1] - 4.2, codes, 1)

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
        ax.text(cx, cy - 0.08, c, fontsize=8.6, fontweight="bold", color=INK if c == "YL" else WHITE, ha="center", va="center", zorder=13)
        ax.text(cx + 4.8, cy - 0.05, NAMES[c], fontsize=8.8, color=INK, ha="left", va="center", zorder=13)
    kx = x0 + 8 + ((len(used) + 3) // 4) * 27 + 3
    for i, (st, t) in enumerate((("solid", "Running today"), ("stripe", "New: real proposal"), ("dash", "New: imagined"))):
        cy = ky - 1.6 - i * 4.4
        stroke(ax, np.array([(kx - 3, cy), (kx + 5, cy)]), color, LWP * 0.62, st, z=12)
        ax.text(kx + 7.4, cy - 0.05, t, fontsize=8.8, color=INK, ha="left", va="center", zorder=13)
    M.icon(ax, kx + 1, ky - 1.6 - 3 * 4.4)
    ax.text(kx + 7.4, ky - 1.65 - 3 * 4.4, "Accessible station", fontsize=8.8, color=INK, ha="left", va="center", zorder=13)
    ax.text(x1 - 5, hy + 4, "Map: Maxwell Howe", fontsize=9.6, color=INK, ha="right", va="center", zorder=13)
    ax.text(x1 - 5, hy, "#30DayMapChallenge Day 8 • Utopia", fontsize=9.6, color=INK, ha="right", va="center", zorder=13)
    ax.text(x1 - 5, hy - 4, "NOT A REAL MBTA MAP", fontsize=9.6, fontweight="bold", color=M.RED, ha="right", va="center", zorder=13)

    plt.rcParams["pdf.fonttype"] = 42
    fig.savefig(OUT / f"line_{key}.png", dpi=200, facecolor=M.PAPER)
    fig.savefig(OUT / f"line_{key}.pdf", facecolor=M.PAPER)
    print("written", f"line_{key}.png")
    for n in done:
        if tr.get(n):
            print(f"  {n}: {' '.join(tr[n])}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "red")
