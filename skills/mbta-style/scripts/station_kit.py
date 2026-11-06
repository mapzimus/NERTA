"""Drawing kit for the station-map look: thick 45-degree lines, rounded bends, white stops, capsule transfers.

Coordinates are schematic grid units, not geography. Used by make_tmap.py and make_map.py.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
from shapely.geometry import LineString, Point

plt.rcParams.update({"font.family": "Arial", "pdf.fonttype": 42, "svg.fonttype": "none"})
INK, WHITE = "#16161a", "#ffffff"
MEDIUM = [pe.withStroke(linewidth=1.9, foreground="#fcfcfa"), pe.withStroke(linewidth=0.28, foreground=INK)]  # small white halo, then Arial thickened to a medium weight
BOLD = [pe.withStroke(linewidth=1.9, foreground="#fcfcfa"), pe.Normal()]  # same halo for bold names
HALO = [pe.withStroke(linewidth=2.6, foreground="#fcfcfa"), pe.withStroke(linewidth=0.28, foreground=INK)]  # for labels that must cross a thin line


def rounded(pts, r=3.0, n=10):
    """Polyline with each corner replaced by a short curve of radius-like size r."""
    pts = [np.array(p, float) for p in pts]
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        u, v = a - b, c - b
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        d = min(r, lu / 2, lv / 2)
        p0, p2 = b + u / lu * d, b + v / lv * d
        for t in np.linspace(0, 1, n):
            out.append((1 - t) ** 2 * p0 + 2 * t * (1 - t) * b + t ** 2 * p2)
    out.append(pts[-1])
    return np.array(out)


def smooth_closed(pts, rounds=3):
    """Chaikin corner cutting, for soft water shapes."""
    p = np.array(pts, float)
    for _ in range(rounds):
        q = np.roll(p, -1, axis=0)
        p = np.column_stack([0.75 * p + 0.25 * q, 0.25 * p + 0.75 * q]).reshape(-1, 2)
    return p


def smooth_open(pts, rounds=3):
    p = np.array(pts, float)
    for _ in range(rounds):
        a, b = p[:-1], p[1:]
        p = np.vstack([p[0], np.column_stack([0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]).reshape(-1, 2), p[-1]])
    return p


def place(path, stops, anchors):
    """Spread stops along a path, evenly between the stops that have fixed spots.

    The first and last stops must be anchors or sit on the path ends.
    """
    ls = LineString(path)
    ds = [None] * len(stops)
    for i, s in enumerate(stops):
        if s in anchors:
            ds[i] = ls.project(Point(anchors[s]))
    if ds[0] is None:
        ds[0] = 0.0
    if ds[-1] is None:
        ds[-1] = ls.length
    known = [i for i, d in enumerate(ds) if d is not None]
    for a, b in zip(known, known[1:]):
        for i in range(a + 1, b):
            ds[i] = ds[a] + (ds[b] - ds[a]) * (i - a) / (b - a)
    return {s: (ls.interpolate(d).x, ls.interpolate(d).y) for s, d in zip(stops, ds)}


def stroke(ax, xy, color, lw, style="solid", z=5):
    """style: solid = runs today, stripe = real proposal, dash = imagined."""
    xy = np.asarray(xy)
    if style == "dash":
        ax.plot(*xy.T, color=color, lw=lw, zorder=z, solid_capstyle="butt", dash_capstyle="butt", ls=(0, (1.5, 0.75)))
        return
    ax.plot(*xy.T, color=color, lw=lw, zorder=z, solid_capstyle="round", solid_joinstyle="round")
    if style == "stripe":
        ax.plot(*xy.T, color=WHITE, lw=lw * 0.26, zorder=z + 0.1, solid_capstyle="butt")


def stop(ax, xy, lw, end=False, z=8, edge=None):
    """White stop dot. Terminals get a ring in the line color, like the wall maps."""
    size = (lw * (1.25 if end else 0.62)) ** 2
    ax.scatter(*xy, s=size, color=WHITE, edgecolor=edge if end else "none", lw=lw * 0.26 if end else 0, zorder=z)


def transfer(ax, a, b=None, lw=8.0, z=9):
    """Black-edged white capsule joining two lines, or a ring on a single point."""
    if b is None:
        ax.scatter(*a, s=(lw * 1.02) ** 2, color=WHITE, edgecolor=INK, lw=lw * 0.2, zorder=z)
        return
    ax.plot([a[0], b[0]], [a[1], b[1]], color=INK, lw=lw * 1.0, zorder=z, solid_capstyle="round")
    ax.plot([a[0], b[0]], [a[1], b[1]], color=WHITE, lw=lw * 0.62, zorder=z + 0.1, solid_capstyle="round")


def bullet(ax, x, y, text, color, h=3.7, fs=9, z=12, fg=WHITE):
    """Rounded line pill, e.g. RL or GL B."""
    w = h * (0.75 + 0.5 * len(text))
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=color, ec="none", zorder=z))
    ax.text(x, y - 0.1, text, color=fg, fontsize=fs, fontweight="bold", ha="center", va="center", zorder=z + 0.1)


def label(ax, xy, text, side="r", gap=2.6, fs=9.0, weight="normal", color=INK, z=11, rot=0, style="normal", halo=False):
    if side == "up":  # tilted up and to the right, for tight runs of stops
        ax.text(xy[0] + 0.3, xy[1] + gap, text, fontsize=fs, color=color, ha="left", va="bottom", rotation=45, rotation_mode="anchor", zorder=z,
                path_effects=MEDIUM)
        return
    if side == "dn":  # tilted, reading into the stop from lower left
        ax.text(xy[0] - gap * .75, xy[1] - gap * .75, text, fontsize=fs, color=color, ha="right", va="center", rotation=45, rotation_mode="anchor", zorder=z,
                path_effects=MEDIUM)
        return
    if side == "along":  # parallel to a 45-degree line, on its lower right
        ax.text(xy[0] + 1.9, xy[1] - 1.9, text, fontsize=fs, color=color, ha="left", va="top", rotation=45, rotation_mode="anchor", zorder=z, path_effects=MEDIUM)
        return
    if side == "se":  # tilted down and to the right
        ax.text(xy[0] + 0.6, xy[1] - gap * .75, text, fontsize=fs, color=color, ha="left", va="center", rotation=-45, rotation_mode="anchor", zorder=z,
                path_effects=MEDIUM)
        return
    dx, dy, ha, va = {"r": (gap, 0, "left", "center"), "l": (-gap, 0, "right", "center"), "t": (0, gap, "center", "bottom"),
                      "b": (0, -gap, "center", "top"), "tr": (gap * .8, gap * .8, "left", "bottom"), "tl": (-gap * .8, gap * .8, "right", "bottom"),
                      "br": (gap * .8, -gap * .8, "left", "top"), "bl": (-gap * .8, -gap * .8, "right", "top")}[side]
    ax.text(xy[0] + dx, xy[1] + dy, text, fontsize=fs, fontweight=weight, color=color, ha=ha, va=va, zorder=z, rotation=rot, style=style,
            rotation_mode="anchor", linespacing=0.95, path_effects=(HALO if halo else MEDIUM) if weight == "normal" else BOLD)
