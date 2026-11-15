"""Main subway map of Spencer's network, in the MBTA wall-poster style."""
import json

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch, FancyBboxPatch

from kit import (INK, PAPER, WATER, COAST, COLORS, OUT, PRIV, ROUTES, THIN,
                 Network, draw_station, place_labels, rounded, route_color,
                 sample_lines, station_routes, wrap, display)
from layout import T, pos, VIA, tile_to_units, snapped

UNIT_PT = 3.0           # points per map unit
LW = 4.2                # line width, points
GAP = 1.75              # parallel line spacing, map units
R = 1.05                # stop dot radius, map units

TERMINALS = set()
for code, (_, _, st) in ROUTES.items():
    if code not in ("VL", "PL", "BRN2"):
        TERMINALS.update([st[0], st[-1]])
TERMINALS.discard("Winchester Center")


def water(ax):
    polys = json.load(open(PRIV / "water_units.json"))
    verts, codes = [], []
    for p in polys:
        p = np.array(p)
        verts.extend(p.tolist()); codes.extend([MPath.MOVETO] + [MPath.LINETO] * (len(p) - 1))
    path = MPath(verts, codes)
    ax.add_patch(PathPatch(path, facecolor=WATER, edgecolor=COAST, lw=0.6,
                           zorder=1, fill=True))


def roundel(ax, x, y, r):
    ax.add_patch(plt.Circle((x, y), r, facecolor="white", edgecolor=INK, lw=r * 0.9, zorder=50))
    ax.text(x, y - r * 0.05, "T", fontsize=r * 2.6, weight="bold", ha="center",
            va="center", color=INK, zorder=51)


def main():
    codes = list(ROUTES)
    edges = set()
    for code in codes:
        st = ROUTES[code][2]
        edges.update(zip(st, st[1:]))
    edges = [e for e in edges if e not in VIA and e[::-1] not in VIA]
    P = snapped(list(T), edges)
    via = {k: [tile_to_units(*w) for w in v] for k, v in VIA.items()}
    net = Network(P, codes, gap=GAP, via=via)
    xs = np.array([p[0] for p in P.values()]); ys = np.array([p[1] for p in P.values()])
    x0, x1 = xs.min() - 70, xs.max() + 60
    y0, y1 = ys.min() - 40, ys.max() + 110
    W, H = (x1 - x0) * UNIT_PT / 72, (y1 - y0) * UNIT_PT / 72
    fig = plt.figure(figsize=(W, H), facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    ax.set_aspect("equal"); ax.axis("off"); ax._kit_unit_pt = UNIT_PT
    ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, color=PAPER, zorder=0))
    water(ax)

    # lines: white casing first so crossings read cleanly, then color
    for code in net.codes:
        p = rounded(net.paths[code], r=3.0)
        lw = 1.6 if code in THIN else LW
        ax.plot(*p.T, color=PAPER, lw=lw + 2.2, solid_capstyle="round",
                solid_joinstyle="round", zorder=4 + net.codes.index(code) * 0.01)
    for code in net.codes:
        p = rounded(net.paths[code], r=3.0)
        lw = 1.6 if code in THIN else LW
        ax.plot(*p.T, color=route_color(code), lw=lw, solid_capstyle="round",
                solid_joinstyle="round", zorder=5 + net.codes.index(code) * 0.01)

    # stops
    sr = station_routes()
    items = []
    for name, codes_here in sr.items():
        pts = [net.at[name][c] for c in codes_here if c in net.at[name]]
        uniq = []
        for p in pts:
            if not any(np.linalg.norm(p - q) < 0.3 for q in uniq):
                uniq.append(p)
        rr = R * (0.7 if all(c in THIN for c in codes_here) else 1.0)
        draw_station(ax, uniq, rr, 0.9)
        u = np.array(uniq)
        c = u.mean(axis=0)
        half = (np.ptp(u[:, 0]) / 2 + rr, np.ptp(u[:, 1]) / 2 + rr)
        txt = wrap(display(name), 15)
        weight = "bold" if name in TERMINALS else "normal"
        if name in TERMINALS:
            txt = txt.upper()
        items.append((name, txt, tuple(c), half, weight))

    line_pts = sample_lines([net.paths[c] for c in net.codes])
    frame = (x0 + 2, y0 + 2, x1 - 2, y1 - 2)
    placed = place_labels(fig, ax, items, line_pts, size=6.3, pad=0.9, frame=frame)
    bad = [p for p in placed if p[5] >= 4]
    print("labels with conflicts:", len(bad))
    for p in sorted(bad, key=lambda q: -q[5])[:25]:
        print("  ", p[0], round(p[5], 1))

    # title block, top left
    tx, ty = x0 + 22, y1 - 22
    ax.text(tx, ty - 2, "Boston Rapid Transit", fontsize=34, weight="bold",
            va="top", ha="left", color=INK, zorder=50)
    ax.text(tx, ty - 19, "A Subway Builder network by Spencer F.", fontsize=15,
            va="top", ha="left", color=INK, zorder=50)
    ax.text(tx, ty - 29, "Map: Maxwell Howe", fontsize=11, va="top", ha="left",
            color=INK, zorder=50)

    # key, bottom right
    key = [("RL", "Red Line", "red"), ("OL", "Orange Line", "orange"),
           ("BL", "Blue Line", "blue"), ("GL", "Green Line  A-F", "green"),
           ("YL", "Yellow Line", "yellow"), ("SL", "Silver Line", "silver"),
           ("TL", "Teal Line", "teal"), ("VL", "Violet Loop", "violet"),
           ("PL", "Pink Loop", "pink"), ("BR", "Brown Line", "brown")]
    kx, ky = x1 - 95, y0 + 20 + len(key) * 7.5
    ax.add_patch(FancyBboxPatch((kx - 6, y0 + 12), 92, len(key) * 7.5 + 22,
                                boxstyle="round,pad=0,rounding_size=3", facecolor="white",
                                edgecolor=INK, lw=0.8, zorder=45))
    ax.text(kx, ky + 8, "KEY", fontsize=10, weight="bold", va="center", zorder=46)
    for i, (ab, label, col) in enumerate(key):
        yy = ky - i * 7.5
        lw = 1.6 if ab == "BR" else LW
        ax.plot([kx, kx + 16], [yy, yy], color=COLORS[col], lw=lw, zorder=46,
                solid_capstyle="round")
        ax.text(kx + 21, yy, label, fontsize=8, va="center", zorder=46)
    ax.text(kx, y0 + 15.5,
            "Lines and stops: Spencer's game save (Nov 2026).\n"
            "White capsules are transfer stations.",
            fontsize=5.5, va="bottom", zorder=46, linespacing=1.3)

    for ext, dpi in (("pdf", None), ("png", 200)):
        fig.savefig(OUT / f"spencer_subway_map.{ext}", dpi=dpi, facecolor=PAPER)
    print("saved", W, H)


if __name__ == "__main__":
    main()
