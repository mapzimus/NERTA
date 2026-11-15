"""Spencer's lines as wall posters, in the NERTA poster style.

Same look as boston-map/src/make_line_poster.py: line drawn straight down,
names on the left, transfer pills tucked against the line on the right,
roundel and line pill in the header, Key at the bottom.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Circle, FancyBboxPatch, Polygon
from matplotlib.textpath import TextPath
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "boston-map/src"))
from station_kit import INK, WHITE, rounded, stroke  # noqa: E402
from kit import COLORS, OUT  # noqa: E402
from network import ROUTES, LOOPS, display  # noqa: E402

plt.rcParams.update({"font.family": ["Arial", "Liberation Sans"], "pdf.fonttype": 42})
PAPER = "#fcfcfa"
FONT = FontProperties(family=["Arial", "Liberation Sans"])
BOLDF = FontProperties(family=["Arial", "Liberation Sans"], weight="bold")
P = 5.0
K = 0.075
PPU = K * 72
LWP = 12.0
LWU = LWP / PPU

FAM = {"red": "RL", "orange": "OL", "blue": "BL", "green": "GL", "yellow": "YL", "silver": "SL",
       "teal": "TL", "violet": "VL", "pink": "PL", "brown": "BR"}
NAMES = {"RL": "Red Line", "OL": "Orange Line", "BL": "Blue Line", "GL": "Green Line",
         "YL": "Yellow Line", "SL": "Silver Line", "TL": "Teal Line", "VL": "Violet Loop",
         "PL": "Pink Loop", "BR": "Brown Line"}
DARK = {"YL"}
TITLE = {"RL-A": "Red Line\nBranch A", "RL-B": "Red Line\nBranch B", "OL-A": "Orange Line\nBranch A",
         "OL-B": "Orange Line\nBranch B", "BL-A": "Blue Line\nBranch A", "BL-B": "Blue Line\nBranch B",
         "GL-A": "Green Line\nA Branch", "GL-B": "Green Line\nB Branch", "GL-C": "Green Line\nC Branch",
         "GL-D": "Green Line\nD Branch", "GL-E": "Green Line\nE Branch", "GL-F": "Green Line\nF Branch",
         "YL": "Yellow\nLine", "SL": "Silver\nLine", "TL": "Teal\nLine", "VL": "Violet\nLoop",
         "PL": "Pink\nLoop", "BRN": "Brown Line\nNorth", "BRS": "Brown Line\nSouth"}
POSTERS = [["RL-A"], ["RL-B"], ["OL-A"], ["OL-B"], ["BL-A"], ["BL-B"], ["GL-A"], ["GL-B"],
           ["GL-C"], ["GL-D"], ["GL-E"], ["GL-F"], ["YL"], ["SL"], ["TL"], ["VL"], ["PL"],
           ["BRN", "BRN2"], ["BRS"]]

AT = {}
for code, (_, ck, st) in ROUTES.items():
    for s in st:
        AT.setdefault(s, [])
        if FAM[ck] not in AT[s]:
            AT[s].append(FAM[ck])


def width(text, fs, bold=False):
    return TextPath((0, 0), text, size=fs, prop=BOLDF if bold else FONT).get_extents().width / PPU


def pills(ax, x, y, codes, z=4):
    h, gap, near = 2.9, 0.35, x + LWU / 2
    for i, c in enumerate(codes):
        far = near + 6.6
        tuck = near - (LWU / 2 if i == 0 else h / 2 + gap)
        ax.add_patch(FancyBboxPatch((tuck, y - h / 2), far - tuck, h, boxstyle=f"round,pad=0,rounding_size={h / 2}",
                                    fc=COLORS[[k for k, v in FAM.items() if v == c][0]], ec=PAPER, lw=1.2, zorder=z - 0.1 * i))
        ax.text((near + far) / 2 + 0.25, y - 0.08, c, fontsize=8.6, fontweight="bold",
                color=INK if c in DARK else WHITE, ha="center", va="center", zorder=z + 0.5)
        near = far + gap
    return near


def roundel(ax, x, y, r):
    ax.add_patch(Circle((x, y), r, fc=WHITE, ec=INK, lw=3.2, zorder=12))
    a, b, c = r * 0.56, r * 0.2, r * 0.6
    ax.add_patch(Polygon([(x - a, y + c), (x + a, y + c), (x + a, y + c - 2 * b), (x + b, y + c - 2 * b),
                          (x + b, y - c), (x - b, y - c), (x - b, y + c - 2 * b), (x - a, y + c - 2 * b)],
                         fc=INK, ec="none", zorder=13))


def layout(codes):
    """Columns of stops. Main route straight down at x=0; a branch steps right."""
    main = list(ROUTES[codes[0]][2])
    legs = [dict(stops=main, at=[(0, -i * P) for i in range(len(main))], side="l")]
    for b in codes[1:]:
        st = ROUTES[b][2]
        j = main.index(st[0])
        bx = 34
        y0 = -j * P
        legs.append(dict(stops=st, at=[(0, y0)] + [(bx, y0 - (i + 1) * P) for i in range(len(st) - 1)],
                         side="r", turn=(bx, y0)))
    return legs


def poster(codes):
    code = codes[0]
    _, ck, st = ROUTES[code]
    color, me = COLORS[ck], FAM[ck]
    loop = code in LOOPS
    legs = layout(codes)
    ends = set() if loop else {st[0], st[-1]}
    for b in codes[1:]:
        ends.add(ROUTES[b][2][-1])
    used = []
    for leg in legs:
        for s in leg["stops"]:
            used += [c for c in AT[s] if c != me and c not in used]
    used = [c for c in NAMES if c in used]
    xs = [p[0] for leg in legs for p in leg["at"]]
    ys = [p[1] for leg in legs for p in leg["at"]]
    name_w = max(width(display(s).upper() if s in ends else display(s), 12.6 if s in ends else 11.6, s in ends)
                 for leg in legs for s in leg["stops"])
    pill_w = max(len([c for c in AT[s] if c != me]) for leg in legs for s in leg["stops"]) * 7.0
    x0 = min(xs) - name_w - 12
    x1 = max(xs) + max(pill_w + 10, 40 if codes[1:] else 0) + (name_w + 8 if codes[1:] else 0)
    need = 122
    if x1 - x0 < need:
        x0, x1 = (x0 + x1) / 2 - need / 2, (x0 + x1) / 2 + need / 2
    y1 = max(ys) + 26
    y0 = min(ys) - (14 if loop else 6) - 25
    fig = plt.figure(figsize=((x1 - x0) * K, (y1 - y0) * K))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.set_axis_off()
    fig.patch.set_facecolor(PAPER)

    for leg in legs:
        pts = leg["at"]
        if "turn" in leg:
            tx, ty = leg["turn"]
            path = [(0, ty), (tx - 2, ty), (tx, ty - 2), pts[-1]]
            stroke(ax, rounded(path, 2.5), color, LWP, "solid", z=5)
        else:
            path = [pts[0], pts[-1]]
            if loop:
                path = [pts[0], (0, pts[-1][1] - 9)]
            stroke(ax, np.array(path), color, LWP, "solid", z=5)
    if loop:
        yb = legs[0]["at"][-1][1] - 9
        ax.annotate("", xy=(0, yb - 3.2), xytext=(0, yb + 0.5),
                    arrowprops=dict(arrowstyle="-|>,head_length=1.1,head_width=0.7", color=color, lw=0), zorder=6)
        ax.text(-3.3, yb - 1.4, f"Continues to {display(st[0])}", fontsize=11.6, color=INK,
                ha="right", va="center", zorder=11)

    done = set()
    for leg in legs:
        for s, (x, y) in zip(leg["stops"], leg["at"]):
            if s in done:
                continue
            done.add(s)
            others = [c for c in AT[s] if c != me]
            end = s in ends
            if end:
                ax.scatter(x, y, s=(LWP * 1.35) ** 2, color=WHITE, edgecolor=color, lw=3.4, zorder=9)
            elif others:
                ax.scatter(x, y, s=(LWP * 1.02) ** 2, color=WHITE, edgecolor=INK, lw=2.6, zorder=9)
            else:
                ax.scatter(x, y, s=(LWP * 0.56) ** 2, color=WHITE, edgecolor=INK, lw=0.7, zorder=9)
            text = display(s).upper() if end else display(s)
            fs, bold = (12.6, True) if end else (11.6, False)
            gap = 4.2 if end else 3.3
            if leg["side"] == "l":
                ax.text(x - gap, y - 0.05, text, fontsize=fs, fontweight="bold" if bold else "normal",
                        color=INK, ha="right", va="center", zorder=11)
                if others:
                    branch_pt = any("turn" in lg and lg["stops"][0] == s for lg in legs)
                    pills(ax, x, y, others, z=6 if branch_pt else 4)
            else:
                near = pills(ax, x, y, others) if others else x + LWU / 2
                ax.text(max(near, x) + (gap - LWU / 2 if not others else 1.4), y - 0.05, text, fontsize=fs,
                        fontweight="bold" if bold else "normal", color=INK, ha="left", va="center", zorder=11)

    hy = y1 - 11
    ax.add_patch(FancyBboxPatch((x0 + 4, hy - 6), 28, 12, boxstyle="round,pad=0,rounding_size=6",
                                fc=color, ec="none", zorder=12))
    ax.text(x0 + 18, hy - 0.4, me, fontsize=38, fontweight="bold", color=INK if me in DARK else WHITE,
            ha="center", va="center", zorder=13)
    ax.text(x0 + 36, hy, TITLE[code], fontsize=27, fontweight="bold", color=INK, ha="left", va="center",
            linespacing=0.9, zorder=13)

    ky = y0 + 21
    ax.plot([x0 + 4, x1 - 4], [ky + 3.4, ky + 3.4], color=INK, lw=0.8, zorder=12)
    for i, c in enumerate(used):
        cx, cy = x0 + 8 + (i // 4) * 27, ky - 1.6 - (i % 4) * 4.4
        ax.add_patch(FancyBboxPatch((cx - 3.3, cy - 1.45), 6.6, 2.9, boxstyle="round,pad=0,rounding_size=1.45",
                                    fc=COLORS[[k for k, v in FAM.items() if v == c][0]], ec="none", zorder=12))
        ax.text(cx, cy - 0.08, c, fontsize=8.6, fontweight="bold", color=INK if c in DARK else WHITE,
                ha="center", va="center", zorder=13)
        ax.text(cx + 4.8, cy - 0.05, NAMES[c], fontsize=8.8, color=INK, ha="left", va="center", zorder=13)
    ax.text(x1 - 5, hy + 2, "Network: Spencer F.", fontsize=9.6, color=INK, ha="right", va="center", zorder=13)
    ax.text(x1 - 5, hy - 2, "Map: Maxwell Howe", fontsize=9.6, color=INK, ha="right", va="center", zorder=13)
    return fig


def main():
    with PdfPages(OUT / "spencer_line_posters.pdf") as pdf:
        for codes in POSTERS:
            fig = poster(codes)
            pdf.savefig(fig, facecolor=PAPER)
            fig.savefig(OUT / f"poster_{codes[0]}.png", dpi=200, facecolor=PAPER)
            plt.close(fig)
    print("done", len(POSTERS))


if __name__ == "__main__":
    main()
