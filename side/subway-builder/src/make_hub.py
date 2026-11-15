"""Hub diagram: every line through Government Center drawn as straight spokes,
stops evenly spaced, not to scale."""
import math
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

from kit import INK, PAPER, COLORS, OUT, ROUTES, ORDER, display, place_labels, sample_lines, wrap
from network import REGIONAL

HUB = "Government Center"
D = 7.0          # spacing between stops, plot units
UNIT_PT = 4.0
LW = 5.5
GAP = 2.0

# first stop out of the hub -> compass direction (degrees, 0 = east)
DIRS = {"Haymarket": 90, "North End": 45, "Waterfront": 0, "South Station": -45,
        "Downtown": -90, "Boston Common": -135, "Bowdoin": 180, "North Station": 135}

lines = {}
for code, (nm, ck, st) in ROUTES.items():
    if HUB in st:
        lines[code] = (nm, COLORS[ck], st)
for code, (nm, st) in REGIONAL.items():
    if HUB in st:
        lines[code] = (nm, COLORS["crtext"], st)
order = [c for c in ORDER if c in lines] + [c for c in lines if c not in ORDER]


class Node:
    def __init__(self, name, parent=None):
        self.name, self.parent, self.kids, self.routes = name, parent, {}, []


root = Node(HUB)
for code in order:
    st = lines[code][2]
    i = st.index(HUB)
    for seq in (st[i + 1:], st[:i][::-1]):
        n = root
        for s in seq:
            if s not in n.kids:
                n.kids[s] = Node(s, n)
            n = n.kids[s]
            n.routes.append(code)


def size(n):
    return 1 + sum(size(k) for k in n.kids.values())


pos = {}


R0 = 16.0       # hub radius, plot units
LANE = 7.0      # sideways spacing between parallel branches


lanes = {}       # arm -> set of lanes in use


def lay(n, p, ang, depth, arm=None, lane=0):
    pos[id(n)] = p
    kids = sorted(n.kids.values(), key=size, reverse=True)
    for i, k in enumerate(kids):
        if n is root:
            a = DIRS[k.name]
            u = np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])
            lanes[k.name] = {0}
            lay(k, u * (R0 + D * 0.7), a, depth + 1, k.name, 0)
            continue
        u = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
        nv = np.array([-u[1], u[0]])
        if i == 0:
            ln = lane
        else:
            used = lanes[arm]
            cands = sorted({lane + d for d in range(-6, 7)} - used,
                           key=lambda c: (abs(c - lane), -c))
            ln = cands[0]
            used.add(ln)
        q = p + u * D + nv * (ln - lane) * LANE
        lay(k, q, ang, depth + 1, arm, ln)


lay(root, np.zeros(2), 0, 0)


def all_nodes(n):
    yield n
    for k in n.kids.values():
        yield from all_nodes(k)


def main():
    nodes = list(all_nodes(root))
    P = np.array([pos[id(n)] for n in nodes])
    x0, y0 = P.min(axis=0) - 28; x1, y1 = P.max(axis=0) + 28
    W, H = (x1 - x0) * UNIT_PT / 72, (y1 - y0) * UNIT_PT / 72
    fig = plt.figure(figsize=(W, H), facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    ax.set_aspect("equal"); ax.axis("off"); ax._kit_unit_pt = UNIT_PT

    # lane offsets on each edge
    paths = defaultdict(list)
    at = defaultdict(dict)
    for n in nodes:
        if n is root:
            continue
        a, b = pos[id(n.parent)], pos[id(n)]
        t = (b - a) / np.linalg.norm(b - a); nv = np.array([-t[1], t[0]])
        rs = sorted(n.routes, key=order.index)
        for i, r in enumerate(rs):
            off = (i - (len(rs) - 1) / 2) * GAP
            at[id(n)][r] = b + nv * off
            at[id(n.parent)].setdefault(r, a + nv * off)
            paths[r].append((a + nv * off, b + nv * off))
    for r in order:
        col = lines[r][1]
        for a, b in paths[r]:
            ax.plot([a[0], b[0]], [a[1], b[1]], color=PAPER, lw=LW + 2, zorder=3,
                    solid_capstyle="round")
        for a, b in paths[r]:
            ax.plot([a[0], b[0]], [a[1], b[1]], color=col, lw=LW, zorder=4,
                    solid_capstyle="round")
    # stops
    items = []
    lines_pts = []
    for r in order:
        for a, b in paths[r]:
            lines_pts.append(np.array([a, b]))
    for n in nodes:
        if n is root:
            continue
        pts = list(at[id(n)].values())
        u = np.array(pts)
        c = u.mean(axis=0)
        span = np.ptp(u, axis=0)
        rr = 1.25
        if len(pts) == 1:
            ax.add_patch(plt.Circle(c, rr, facecolor="white", edgecolor=INK, lw=1.2, zorder=10))
        else:
            ends = u[np.argmax(np.linalg.norm(u - u[0], axis=1))]
            seg = np.array([u[0], ends])
            w = 2 * rr * UNIT_PT
            ax.plot(*seg.T, color=INK, lw=w + 2.4, solid_capstyle="round", zorder=10)
            ax.plot(*seg.T, color="white", lw=w, solid_capstyle="round", zorder=11)
        leaf = not n.kids
        txt = wrap(display(n.name), 16)
        items.append((n.name, txt.upper() if leaf else txt, tuple(c),
                      (span[0] / 2 + rr, span[1] / 2 + rr), "bold" if leaf else "normal"))
    # hub
    ax.add_patch(plt.Circle((0, 0), R0, facecolor="white", edgecolor=INK, lw=3, zorder=12))
    ax.text(0, 0, "GOVERNMENT\nCENTER", ha="center", va="center", fontsize=13,
            weight="bold", zorder=13, linespacing=1.0)
    lp = sample_lines([np.array(s) for s in lines_pts], step=0.8)
    hub_ring = np.array([[R0 * math.cos(t), R0 * math.sin(t)] for t in np.linspace(0, 6.3, 60)])
    place_labels(fig, ax, items, np.vstack([lp, hub_ring, np.zeros((1, 2))]), size=7.5,
                 pad=1.0, frame=(x0, y0, x1, y1))

    for ext, dpi in (("pdf", None), ("png", 200)):
        fig.savefig(OUT / f"spencer_hub_diagram.{ext}", dpi=dpi, facecolor=PAPER)
    print("saved", round(W, 1), round(H, 1), len(nodes))


if __name__ == "__main__":
    main()
