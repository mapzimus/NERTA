"""Shared drawing pieces for Spencer's network maps."""
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np

from network import ROUTES, LOOPS, display

ROOT = Path(__file__).resolve().parents[1]
PRIV = ROOT / "private"
OUT = PRIV / "output"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Liberation Sans", "pdf.fonttype": 42, "svg.fonttype": "none",
})

INK, PAPER, WATER, COAST = "#16161a", "#fcfcfa", "#c9e3ee", "#7fb2c6"
COLORS = {
    "red": "#da291c", "orange": "#ed8b00", "blue": "#003da5",
    "green": "#00843d", "yellow": "#f5c400", "silver": "#7c878e",
    "teal": "#00a9c9", "violet": "#8e3fae", "pink": "#e77fa6",
    "brown": "#8a5a2b", "cr": "#a98aa8", "crtext": "#80276c",
}
# Stacking order inside shared corridors, first = left/top of the bundle.
ORDER = ["BL-A", "BL-B", "RL-A", "RL-B", "OL-A", "OL-B", "GL-A", "GL-B",
         "GL-C", "GL-D", "GL-E", "GL-F", "YL", "SL", "TL", "VL", "PL",
         "BRN", "BRN2", "BRS"]
SHORT = {"RL-A": "RL", "RL-B": "RL", "OL-A": "OL", "OL-B": "OL",
         "BL-A": "BL", "BL-B": "BL", "BRN": "BR", "BRN2": "BR", "BRS": "BR"}
THIN = {"BRN", "BRN2", "BRS"}


def route_color(code):
    return COLORS[ROUTES[code][1]]


def stops_of(code):
    st = list(ROUTES[code][2])
    if code in LOOPS:
        st = st + [st[0]]
    return st


def edges_by_route():
    """Undirected edge -> list of route codes using it."""
    e = defaultdict(list)
    for code in ROUTES:
        st = stops_of(code)
        for a, b in zip(st, st[1:]):
            k = tuple(sorted((a, b)))
            if code not in e[k]:
                e[k].append(code)
    return e


def station_routes():
    s = defaultdict(list)
    for code in ROUTES:
        for n in ROUTES[code][2]:
            if code not in s[n]:
                s[n].append(code)
    return s


# ---------- geometry ----------

def octi(p, q, avoid, tol=0.1):
    """Path from p to q using only 0/45/90 degree pieces.

    Straight when already on one of those angles; otherwise one corner,
    picking the corner that stays farther from other stops.
    """
    p, q = np.array(p, float), np.array(q, float)
    d = q - p
    ax, ay = abs(d[0]), abs(d[1])
    if ax < 1e-6 or ay < 1e-6:
        return [p, q]
    r = min(ax, ay) / max(ax, ay)
    if r < tol or r > 1 - tol:
        return [p, q]
    m = min(ax, ay)
    diag = np.array([math.copysign(m, d[0]), math.copysign(m, d[1])])
    c1 = p + diag            # diagonal first
    c2 = q - diag            # diagonal last
    def clear(c):
        if not len(avoid):
            return 1e9
        return np.min(np.hypot(*(avoid - c).T))
    c = c1 if clear(c1) >= clear(c2) else c2
    return [p, c, q]


def offset_poly(pts, off):
    """Offset a polyline sideways (left of travel) with mitred joins."""
    pts = np.array(pts, float)
    if abs(off) < 1e-9:
        return pts
    segs = []
    for a, b in zip(pts, pts[1:]):
        t = (b - a) / np.linalg.norm(b - a)
        n = np.array([-t[1], t[0]])
        segs.append((a + n * off, b + n * off, t))
    out = [segs[0][0]]
    for (a1, b1, t1), (a2, b2, t2) in zip(segs, segs[1:]):
        den = t1[0] * t2[1] - t1[1] * t2[0]
        if abs(den) < 1e-9:
            out.append(b1)
            continue
        s = ((a2 - a1)[0] * t2[1] - (a2 - a1)[1] * t2[0]) / den
        out.append(a1 + t1 * s)
    out.append(segs[-1][1])
    return np.array(out)


def rounded(pts, r=2.5, n=8):
    pts = [np.array(p, float) for p in pts]
    if len(pts) < 3:
        return np.array(pts)
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        u, v = a - b, c - b
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        if lu < 1e-9 or lv < 1e-9:
            continue
        d = min(r, lu / 2, lv / 2)
        p0, p2 = b + u / lu * d, b + v / lv * d
        for t in np.linspace(0, 1, n):
            out.append((1 - t) ** 2 * p0 + 2 * t * (1 - t) * b + t ** 2 * p2)
    out.append(pts[-1])
    return np.array(out)


class Network:
    """Builds every route's drawn path from stop positions."""

    def __init__(self, pos, codes, gap=1.9, via=None):
        self.pos = {k: np.array(v, float) for k, v in pos.items()}
        self.codes = [c for c in ORDER if c in codes]
        self.gap = gap
        allpts = np.array(list(self.pos.values()))
        names = list(self.pos)
        e = defaultdict(list)
        for code in self.codes:
            st = stops_of(code)
            for a, b in zip(st, st[1:]):
                k = tuple(sorted((a, b)))
                if code not in e[k]:
                    e[k].append(code)
        self.edges = e
        self.base = {}
        for (a, b) in e:
            pa, pb = self.pos[a], self.pos[b]
            # orient each edge east-ish so bundles keep one stacking order
            if (pb[0] - pa[0]) < -1e-6 or (abs(pb[0] - pa[0]) < 1e-6 and pb[1] < pa[1]):
                a2, b2 = b, a
            else:
                a2, b2 = a, b
            mask = np.array([n not in (a, b) for n in names])
            way = None
            if via:
                way = via.get((a2, b2))
                if way is None and via.get((b2, a2)) is not None:
                    way = list(via[(b2, a2)])[::-1]
            if way:
                pts = [self.pos[a2]] + [np.array(w, float) for w in way] + [self.pos[b2]]
                path = [pts[0]]
                for p_, q_ in zip(pts, pts[1:]):
                    path.extend(octi(p_, q_, allpts[mask])[1:])
            else:
                path = octi(self.pos[a2], self.pos[b2], allpts[mask])
            self.base[(a, b)] = (a2, b2, path)
        # where each route sits at each stop (for station capsules)
        self.at = defaultdict(dict)
        self.paths = {}
        for code in self.codes:
            st = stops_of(code)
            chain = []
            for a, b in zip(st, st[1:]):
                k = tuple(sorted((a, b)))
                a2, b2, path = self.base[k]
                users = sorted(e[k], key=self.codes.index)
                i = users.index(code)
                off = (i - (len(users) - 1) / 2) * gap
                if code in THIN or any(u in THIN for u in users):
                    thin = [u for u in users if u in THIN]
                    thick = [u for u in users if u not in THIN]
                    if code in THIN:
                        off = ((len(thick) + 1) / 2) * gap if thick else 0
                    else:
                        j = thick.index(code)
                        off = (j - (len(thick) - 1) / 2) * gap
                op = offset_poly(path, off)
                if (a2, b2) != (a, b):
                    op = op[::-1]
                self.at[a].setdefault(code, op[0])
                self.at[b].setdefault(code, op[-1])
                chain.append(op)
            pts = [chain[0][0]]
            for seg in chain:
                if np.linalg.norm(seg[0] - pts[-1]) > 1e-6:
                    pts.append(seg[0])
                pts.extend(seg[1:])
            self.paths[code] = np.array(pts)


def draw_station(ax, pts, r, lw_edge, z=20, terminal=False):
    """White stop dot, or a white capsule joining the dots of every line there."""
    pts = np.array(pts)
    if len(pts) == 1 or np.max(np.ptp(pts, axis=0)) < 1e-6:
        c = pts[0]
        ax.add_patch(plt.Circle(c, r, facecolor="white", edgecolor=INK,
                                lw=lw_edge, zorder=z))
        return
    # minimum spanning tree over the dots
    n = len(pts)
    inside, links = {0}, []
    while len(inside) < n:
        best = None
        for i in inside:
            for j in range(n):
                if j in inside:
                    continue
                d = np.linalg.norm(pts[i] - pts[j])
                if best is None or d < best[0]:
                    best = (d, i, j)
        links.append((best[1], best[2]))
        inside.add(best[2])
    pt_per_unit = ax.figure.dpi_scale_trans  # unused; widths come in points
    w = ax._kit_unit_pt * 2 * r
    for i, j in links:
        ax.plot(*np.array([pts[i], pts[j]]).T, color=INK, lw=w + 2 * lw_edge,
                solid_capstyle="round", zorder=z)
    for p in pts:
        ax.add_patch(plt.Circle(p, r + lw_edge / ax._kit_unit_pt / 2,
                                color=INK, zorder=z, lw=0))
    for i, j in links:
        ax.plot(*np.array([pts[i], pts[j]]).T, color="white", lw=w,
                solid_capstyle="round", zorder=z + 1)
    for p in pts:
        ax.add_patch(plt.Circle(p, r, color="white", zorder=z + 1, lw=0))


def text_extent(fig, ax, s, size, weight="normal"):
    """Width and height of a label in data units."""
    t = ax.text(0, 0, s, fontsize=size, weight=weight, linespacing=0.95)
    r = fig.canvas.get_renderer()
    bb = t.get_window_extent(renderer=r)
    t.remove()
    inv = ax.transData.inverted()
    (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
    return abs(x1 - x0), abs(y1 - y0)


def wrap(name, maxlen=14):
    if len(name) <= maxlen or " " not in name:
        return name
    words = name.split()
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        m = max(len(a), len(b))
        if best is None or m < best[0]:
            best = (m, a + "\n" + b)
    return best[1]


def box_hits(box, boxes):
    x0, y0, x1, y1 = box
    n = 0
    for b in boxes:
        if x0 < b[2] and x1 > b[0] and y0 < b[3] and y1 > b[1]:
            n += 1
    return n


def seg_box_hits(box, segs):
    """Count how many line segments pass through a box (sampled)."""
    x0, y0, x1, y1 = box
    inside = (segs[:, 0] > x0) & (segs[:, 0] < x1) & (segs[:, 1] > y0) & (segs[:, 1] < y1)
    return int(inside.sum())


def place_labels(fig, ax, items, line_pts, size, pad, frame=None):
    """Greedy label placement.

    items: list of (name, text, anchor xy, marker half-size (dx, dy), weight).
    Tries 8 spots around each stop and keeps the one that hits the fewest
    lines, labels and stops.
    """
    placed, boxes = [], []
    stops = np.array([it[2] for it in items])
    # crowded stops first
    def crowd(it):
        d = np.hypot(*(stops - it[2]).T)
        return -np.sum(d < 25)
    order = sorted(range(len(items)), key=lambda i: crowd(items[i]))
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]
    for i in order:
        name, txt, (x, y), (hx, hy), weight = items[i]
        w, h = text_extent(fig, ax, txt, size, weight)
        best = None
        for k, (dx, dy) in enumerate(dirs):
            cx = x + dx * (hx + pad + w / 2) if dx else x
            cy = y + dy * (hy + pad + h / 2) if dy else y
            if dx and dy:
                cx = x + dx * (hx * 0.7 + pad + w / 2)
                cy = y + dy * (hy * 0.7 + pad + h / 2)
            box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            sc = 6 * box_hits(box, boxes) + 1.0 * seg_box_hits(box, line_pts)
            others = stops[np.hypot(*(stops - (x, y)).T) > 1e-6]
            sc += 4 * int(((others[:, 0] > box[0] - 1.5) & (others[:, 0] < box[2] + 1.5) &
                           (others[:, 1] > box[1] - 1.5) & (others[:, 1] < box[3] + 1.5)).sum())
            if frame is not None:
                fx0, fy0, fx1, fy1 = frame
                if box[0] < fx0 or box[2] > fx1 or box[1] < fy0 or box[3] > fy1:
                    sc += 50
            sc += 0.05 * k  # mild preference for right, left, up, down
            if best is None or sc < best[0]:
                best = (sc, cx, cy, box)
        sc, cx, cy, box = best
        boxes.append(box)
        placed.append((name, txt, cx, cy, weight, sc))
    for name, txt, cx, cy, weight, sc in placed:
        ax.text(cx, cy, txt, fontsize=size, weight=weight, ha="center",
                va="center", color=INK, zorder=40, linespacing=0.95,
                path_effects=[pe.withStroke(linewidth=1.6, foreground=PAPER)])
    return placed


def sample_lines(paths, step=0.6):
    pts = []
    for p in paths:
        for a, b in zip(p, p[1:]):
            n = max(2, int(np.linalg.norm(b - a) / step))
            pts.append(np.linspace(a, b, n))
    return np.vstack(pts) if pts else np.zeros((0, 2))
