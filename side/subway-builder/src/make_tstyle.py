"""Spencer's network as a T-style wall map, built with the NERTA station kit.

One thick stroke per line color, evenly spaced stops, bold terminals with
line bullets, black-edged transfer capsules, and the real coast bent to the
diagram through the stops.
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "boston-map/src"))
import station_kit as sk  # noqa: E402
from station_kit import INK, WHITE, bullet, stop, stroke, transfer, MEDIUM, BOLD  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, PathPatch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402

plt.rcParams.update({"font.family": ["Arial", "Liberation Sans"]})

import t_layout as TL  # noqa: E402
import t_overrides as OV  # noqa: E402
from kit import COLORS, PRIV, OUT, offset_poly, rounded, text_extent  # noqa: E402
from network import ROUTES, LOOPS, GEO_ALIAS, display  # noqa: E402

PAPER, WATER, COAST = "#fcfcfa", "#c9e3ee", "#7fb2c6"
LW = 8.4
UNIT_PT = 4.8
GAP = LW / UNIT_PT * 1.08          # lane spacing, map units
FAM_ORDER = ["blue", "red", "orange", "green", "yellow", "silver", "teal", "violet", "pink", "brown"]
THIN = {"brown"}
BUL = {"RL-A": "RL  A", "RL-B": "RL  B", "OL-A": "OL  A", "OL-B": "OL  B", "BL-A": "BL  A",
       "BL-B": "BL  B", "GL-A": "GL  A", "GL-B": "GL  B", "GL-C": "GL  C", "GL-D": "GL  D",
       "GL-E": "GL  E", "GL-F": "GL  F", "YL": "YL", "SL": "SL", "TL": "TL", "VL": "VL",
       "PL": "PL", "BRN": "BR  N", "BRN2": "BR  N", "BRS": "BR  S"}
FS, FS_END = 8.8, 9.8


def lw_of(f):
    return LW * 0.5 if f in THIN else LW


def build_geometry():
    pos, epath, CH, A, edges = TL.build(move=OV.MOVE, rays=OV.RAYS, bends=OV.BENDS,
                                        via=OV.VIA, place=OV.PLACE)
    lane = {}
    for (a, b), fams in edges.items():
        pa, pb = pos[a], pos[b]
        if (pb[0] - pa[0]) < -1e-6 or (abs(pb[0] - pa[0]) < 1e-6 and pb[1] < pa[1]):
            a2, b2 = b, a
        else:
            a2, b2 = a, b
        path = epath[(a2, b2)]
        fs = sorted(fams, key=FAM_ORDER.index)
        for i, f in enumerate(fs):
            off = (i - (len(fs) - 1) / 2) * GAP
            op = offset_poly(path, off)
            lane[(a2, b2, f)] = op
            lane[(b2, a2, f)] = op[::-1]
    return pos, lane, edges, A


def route_path(code, lane):
    st = TL.route_stops(code)
    f = TL.fam(code)
    pts = []
    for a, b in zip(st, st[1:]):
        seg = lane[(a, b, f)]
        for p in seg:
            if not pts or np.linalg.norm(pts[-1] - p) > 1e-6:
                pts.append(np.array(p))
    return np.array(pts)


def coast(ax, pos, frame):
    """Real land, bent to the diagram with a thin-plate spline through the stops."""
    import geopandas as gpd
    from pyproj import Transformer
    from scipy.interpolate import RBFInterpolator
    import shapely
    d = json.load(open(PRIV / "bostonstations.geojson"))
    acc = defaultdict(list)
    for f in d["features"]:
        acc[f["properties"]["name"].strip()].append(f["geometry"]["coordinates"])
    tr = Transformer.from_crs(4326, 26986, always_xy=True)
    src, dst = [], []
    for n, p in pos.items():
        g = acc.get(GEO_ALIAS.get(n, n))
        if not g:
            continue
        src.append(tr.transform(*np.mean(g, axis=0))); dst.append(p)
    src, dst = np.array(src), np.array(dst)
    c = src.mean(axis=0)
    rbf = RBFInterpolator((src - c) / 1000, dst, kernel="thin_plate_spline", smoothing=60.0, degree=1)
    towns = gpd.read_file(REPO / "data/shared/ne_towns.gpkg").to_crs(26986)
    x0, y0, x1, y1 = src[:, 0].min() - 9000, src[:, 1].min() - 9000, src[:, 0].max() + 9000, src[:, 1].max() + 9000
    land = towns.cx[x0:x1, y0:y1].geometry.union_all().buffer(0)
    land = land.intersection(shapely.box(x0, y0, x1, y1)).simplify(40)
    land = shapely.segmentize(land, 250)
    def f(xy):
        return rbf((xy - c) / 1000)
    warped = shapely.transform(land, f)
    fb = shapely.box(*frame)
    warped = shapely.make_valid(warped).intersection(fb)
    gpd.GeoSeries([warped]).plot(ax=ax, color=PAPER, edgecolor=COAST, lw=0.7, zorder=1)
    return warped


class Placer:
    def __init__(self, fig, ax, frame):
        self.fig, self.ax, self.frame = fig, ax, frame
        self.boxes, self.pts = [], np.zeros((0, 2))

    def block(self, box):
        self.boxes.append(box)

    def add_points(self, p):
        self.pts = np.vstack([self.pts, p])

    def score(self, box):
        x0, y0, x1, y1 = box
        s = 0.0
        for b in self.boxes:
            if x0 < b[2] and x1 > b[0] and y0 < b[3] and y1 > b[1]:
                s += 8
        if len(self.pts):
            m = LW / UNIT_PT / 2 + 0.15       # lines have width
            s += 1.2 * int(((self.pts[:, 0] > x0 - m) & (self.pts[:, 0] < x1 + m) &
                            (self.pts[:, 1] > y0 - m) & (self.pts[:, 1] < y1 + m)).sum())
        fx0, fy0, fx1, fy1 = self.frame
        if x0 < fx0 or x1 > fx1 or y0 < fy0 or y1 > fy1:
            s += 100
        return s

    def best(self, xy, half, w, h, pad, prefer=None):
        """Bullets: 8 spots around the stop, one distance."""
        x, y = xy
        hx, hy = half
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]
        out = None
        for k, (dx, dy) in enumerate(dirs):
            if dx and dy:
                cx = x + dx * (hx * 0.75 + pad * 0.8 + w / 2); cy = y + dy * (hy * 0.75 + pad * 0.8 + h / 2)
            else:
                cx = x + dx * (hx + pad + w / 2); cy = y + dy * (hy + pad + h / 2)
            box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            sc = self.score(box) + 0.04 * k
            if out is None or sc < out[0]:
                out = (sc, cx, cy, box, (dx, dy))
        return out

    def label(self, xy, half, variants):
        """Station names. variants: list of (text, w, h). Tries straight spots at
        three distances, then 45-degree tilts. Returns the best candidate."""
        x, y = xy
        hx, hy = half
        out = None
        k = 0
        for vi, (txt, w, h) in enumerate(variants):
            for pi, pad in enumerate((0.7, 2.0, 3.6)):
                spots = []
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    spots.append((x + dx * (hx + pad + w / 2), y + dy * (hy + pad + h / 2)))
                for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
                    spots.append((x + dx * (hx * 0.75 + pad * 0.8 + w / 2), y + dy * (hy * 0.75 + pad * 0.8 + h / 2)))
                    # text starting at the stop, above or below it
                    spots.append((x + dx * (w / 2 - 0.6), y + dy * (hy + pad + h / 2)))
                for cx, cy in spots:
                    k += 1
                    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                    sc = self.score(box) + 0.02 * k + 0.9 * pi + 0.25 * vi
                    if out is None or sc < out[0]:
                        out = (sc, dict(kind="flat", text=txt, x=cx, y=cy), [box])
        # tilted, single line only
        txt, w, h = variants[0]
        if "\n" not in txt:
            for ang, sx, sy in ((45, 1, 1), (-45, 1, -1)):
                for pad in (0.9, 2.2):
                    r = max(hx, hy) * 0.8 + pad
                    ax_, ay_ = x + sx * r * 0.7, y + sy * r * 0.7
                    n = max(2, int(w / (h * 0.9)))
                    boxes = []
                    for i in range(n):
                        t = (i + 0.5) / n * w * 0.7071
                        cx, cy = ax_ + sx * t, ay_ + sy * t
                        q = h * 0.62
                        boxes.append((cx - q, cy - q, cx + q, cy + q))
                    sc = sum(self.score(b_) for b_ in boxes) / 2.0 + 1.6 + pad * 0.3
                    if out is None or sc < out[0]:
                        out = (sc, dict(kind="tilt", text=txt, x=ax_, y=ay_, ang=ang), boxes)
        return out


def wrap(name, maxlen=13):
    if len(name) <= maxlen or " " not in name:
        return name
    w = name.split()
    best = None
    for i in range(1, len(w)):
        a, b = " ".join(w[:i]), " ".join(w[i:])
        m = max(len(a), len(b))
        if best is None or m < best[0]:
            best = (m, a + "\n" + b)
    return best[1]


def capsule(ax, pts, lw):
    pts = [np.array(p) for p in pts]
    uniq = []
    for p in pts:
        if not any(np.linalg.norm(p - q) < 0.25 for q in uniq):
            uniq.append(p)
    if len(uniq) == 1:
        transfer(ax, uniq[0], lw=lw)
        return uniq
    inside, links = {0}, []
    while len(inside) < len(uniq):
        best = None
        for i in inside:
            for j in range(len(uniq)):
                if j not in inside:
                    dd = np.linalg.norm(uniq[i] - uniq[j])
                    if best is None or dd < best[0]:
                        best = (dd, i, j)
        links.append((best[1], best[2])); inside.add(best[2])
    for i, j in links:
        ax.plot([uniq[i][0], uniq[j][0]], [uniq[i][1], uniq[j][1]], color=INK, lw=lw, zorder=9, solid_capstyle="round")
    for i, j in links:
        ax.plot([uniq[i][0], uniq[j][0]], [uniq[i][1], uniq[j][1]], color=WHITE, lw=lw * 0.62, zorder=9.1, solid_capstyle="round")
    return uniq


def main():
    pos, lane, edges, A = build_geometry()
    P = np.array(list(pos.values()))
    x0, x1 = P[:, 0].min() - 22, P[:, 0].max() + 26
    y0, y1 = P[:, 1].min() - 16, P[:, 1].max() + 40
    w_in, h_in = (x1 - x0) * UNIT_PT / 72, (y1 - y0) * UNIT_PT / 72
    fig = plt.figure(figsize=(w_in, h_in), facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, color=WATER, zorder=0))
    frame = (x0 + 1.5, y0 + 1.5, x1 - 1.5, y1 - 1.5)
    coast(ax, pos, (x0, y0, x1, y1))

    # lines
    order = sorted(ROUTES, key=lambda c: FAM_ORDER.index(TL.fam(c)))
    paths = {c: rounded(route_path(c, lane), r=3.2) for c in order}
    for c in order:
        f = TL.fam(c)
        ax.plot(*paths[c].T, color=PAPER, lw=lw_of(f) + 2.0, zorder=4, solid_capstyle="round", solid_joinstyle="round")
    for c in order:
        f = TL.fam(c)
        stroke(ax, paths[c], COLORS[f], lw_of(f), "solid", z=5 + 0.05 * FAM_ORDER.index(f))

    # where each line sits at each stop
    at = defaultdict(lambda: defaultdict(list))
    for (a, b, f), op in lane.items():
        at[a][f].append(np.array(op[0]))
    fams_at = defaultdict(set)
    ends = defaultdict(list)
    for c, (_, ck, st) in ROUTES.items():
        for s in st:
            fams_at[s].add(ck)
        if c not in LOOPS:
            for s in (st[0], st[-1]):
                if c == "BRN2" and s == "Winchester Center":
                    continue
                ends[s].append(c)

    placer = Placer(fig, ax, frame)
    samples = []
    for c in order:
        p = paths[c]
        for a, b in zip(p, p[1:]):
            n = max(2, int(np.linalg.norm(b - a) / 0.7))
            samples.append(np.linspace(a, b, n))
    placer.add_points(np.vstack(samples))

    marks = {}
    for s, p in pos.items():
        pts = [q for f in fams_at[s] for q in at[s][f]]
        fams = fams_at[s]
        if len(fams) == 1:
            f = next(iter(fams))
            q = np.mean(pts, axis=0)
            if ends.get(s):
                stop(ax, q, LW, True, edge=COLORS[f], z=9)
                r = LW * 1.25 / UNIT_PT / 2 + 0.3
            else:
                ax.scatter(*q, s=(lw_of(f) * 0.62) ** 2, color=WHITE, edgecolor=INK, lw=0.5, zorder=8)
                r = LW * 0.62 / UNIT_PT / 2
            marks[s] = (q, (r, r))
        else:
            u = np.array(capsule(ax, pts, LW * 1.05))
            c = (u.min(axis=0) + u.max(axis=0)) / 2
            r = LW * 1.05 / UNIT_PT / 2
            marks[s] = (c, (np.ptp(u[:, 0]) / 2 + r, np.ptp(u[:, 1]) / 2 + r))
    for s, (c, (hx, hy)) in marks.items():
        placer.block((c[0] - hx, c[1] - hy, c[0] + hx, c[1] + hy))

    # furniture boxes first, so labels keep clear of them
    title_box = (x0 + 2, y1 - 38, x0 + 122, y1 - 2)
    key_w, key_h = 62, 86
    key_box = (x1 - key_w - 4, -296, x1 - 4, -296 + key_h)
    placer.block(title_box); placer.block(key_box)

    # terminal bullets
    for s, codes in ends.items():
        c, (hx, hy) = marks[s]
        texts = []
        for code in codes:
            t = BUL[code]
            if t not in [x[0] for x in texts]:
                texts.append((t, TL.fam(code)))
        h = 3.7
        ws = [h * (0.75 + 0.5 * len(t)) for t, _ in texts]
        W = sum(ws) + 1.0 * (len(ws) - 1)
        sc, cx, cy, box, d = placer.best(c, (hx, hy), W, h, 1.6)
        xx = cx - W / 2
        for (t, f), wv in zip(texts, ws):
            fg = INK if f in ("yellow",) else WHITE
            base, _, letter = t.partition("  ")
            if letter:
                bullet(ax, xx + wv / 2, cy, base + "    ", COLORS[f], h=h, fs=8.6, fg=fg)
                ax.add_patch(Circle((xx + wv - h / 2 - 0.15, cy), h * 0.36, fc=WHITE, ec="none", zorder=12.2))
                ax.text(xx + wv - h / 2 - 0.15, cy - 0.05, letter, color=COLORS[f], fontsize=7.8,
                        fontweight="bold", ha="center", va="center", zorder=12.3)
            else:
                bullet(ax, xx + wv / 2, cy, base, COLORS[f], h=h, fs=8.6, fg=fg)
            xx += wv + 1.0
        placer.block(box)

    # labels, crowded stops first
    names = list(marks)
    C = np.array([marks[s][0] for s in names])
    crowd = {s: int(np.sum(np.hypot(*(C - marks[s][0]).T) < 16)) for s in names}
    conflicts = []
    placed_boxes = {}
    order_l = sorted(names, key=lambda n: (-(len(fams_at[n]) > 1), -crowd[n]))
    for s in order_l:
        c, half = marks[s]
        term = bool(ends.get(s))
        size = FS_END if term else FS
        wt = "bold" if term else "normal"
        base = display(s).upper() if term else display(s)
        variants = []
        for t in dict.fromkeys([base, wrap(base)]):
            w, h = text_extent(fig, ax, t, size, wt)
            variants.append((t, w, h))
        sc, spec, boxes = placer.label(c, half, variants)
        for b_ in boxes:
            placer.block(b_)
        placed_boxes[s] = boxes[0]
        if sc >= 2.4:
            conflicts.append((round(sc, 1), s))
        fx = BOLD if term else MEDIUM
        if spec["kind"] == "flat":
            ax.text(spec["x"], spec["y"], spec["text"], fontsize=size, fontweight=wt, color=INK,
                    ha="center", va="center", zorder=11, linespacing=0.95, path_effects=fx)
        else:
            up = spec["ang"] > 0
            ax.text(spec["x"], spec["y"], spec["text"], fontsize=size, fontweight=wt, color=INK,
                    ha="left", va="bottom" if up else "top", rotation=spec["ang"],
                    rotation_mode="anchor", zorder=11, path_effects=fx)

    # title block
    tx, ty, tr = x0 + 12, y1 - 12, 7.6
    ax.text(tx - tr, ty + 1.6, "Spencer’s", fontsize=34, fontweight="bold", color=INK, va="baseline", zorder=12)
    ax.text(tx - tr, ty - 7.0, "Rapid Transit", fontsize=34, fontweight="bold", color=INK, va="baseline", zorder=12)
    for i, t in enumerate(("Network: Spencer F., built in Subway Builder", "Map: Maxwell Howe")):
        ax.text(tx - tr, ty - 12.6 - i * 3.0, t, fontsize=11, color=INK, va="baseline", zorder=12)

    # key
    kx0, ky0, kx1, ky1 = key_box
    ax.add_patch(plt.Rectangle((kx0, ky0), kx1 - kx0, ky1 - ky0, fc=WHITE, ec=INK, lw=1.0, zorder=12))
    ax.text(kx0 + 4, ky1 - 5, "Key", fontsize=12, fontweight="bold", va="center", zorder=13)
    rows = [("Red Line, branches A and B", "red"), ("Orange Line, branches A and B", "orange"),
            ("Blue Line, branches A and B", "blue"), ("Green Line, branches A to F", "green"),
            ("Yellow Line", "yellow"), ("Silver Line", "silver"), ("Teal Line", "teal"),
            ("Violet Loop", "violet"), ("Pink Loop", "pink"), ("Brown Line, North and South", "brown")]
    yy = ky1 - 11.5
    for label_, f in rows:
        ax.plot([kx0 + 4, kx0 + 14], [yy, yy], color=COLORS[f], lw=lw_of(f), solid_capstyle="butt", zorder=13)
        ax.text(kx0 + 17, yy, label_, fontsize=8.6, va="center", zorder=13)
        yy -= 5.2
    yy -= 1.0
    ax.text(kx0 + 4, yy, "Stations", fontsize=10, fontweight="bold", va="center", zorder=13)
    yy -= 5.2
    ax.scatter(kx0 + 9, yy, s=(LW * 0.62) ** 2, color=WHITE, edgecolor=INK, lw=0.5, zorder=13.2)
    ax.plot([kx0 + 4, kx0 + 14], [yy, yy], color=COLORS["red"], lw=LW, solid_capstyle="butt", zorder=13)
    ax.text(kx0 + 17, yy, "Stop", fontsize=8.6, va="center", zorder=13)
    yy -= 5.2
    ax.plot([kx0 + 7, kx0 + 11], [yy, yy], color=INK, lw=LW * 1.05, zorder=13, solid_capstyle="round")
    ax.plot([kx0 + 7, kx0 + 11], [yy, yy], color=WHITE, lw=LW * 0.65, zorder=13.1, solid_capstyle="round")
    ax.text(kx0 + 17, yy, "Transfer station", fontsize=8.6, va="center", zorder=13)
    yy -= 5.2
    ax.scatter(kx0 + 9, yy, s=(LW * 1.25) ** 2, color=WHITE, edgecolor=COLORS["red"], lw=LW * 0.26, zorder=13)
    ax.text(kx0 + 17, yy, "End of a line", fontsize=8.6, va="center", zorder=13)
    ax.text(x1 - 3, y0 + 3,
            "Layout schematic, not to scale. Regional rail not shown. Stops and lines: Spencer’s Subway Builder save, "
            "November 2026. Coast: US Census TIGER/Line.",
            fontsize=6.4, ha="right", va="bottom", color=INK, zorder=12)

    for ext, dpi in (("pdf", None), ("png", 200), ("png600", 600)):
        if ext == "png600":
            fig.savefig(OUT / "spencer_t_map_hires.png", dpi=420, facecolor=PAPER)
        else:
            fig.savefig(OUT / f"spencer_t_map.{ext}", dpi=dpi, facecolor=PAPER)
    json.dump({"labels": {k: list(map(float, v)) for k, v in placed_boxes.items()},
               "marks": {k: [list(map(float, v[0])), list(map(float, v[1]))] for k, v in marks.items()}},
              open(OUT / "spencer_t_map_layout.json", "w"))
    print(f"saved {w_in:.1f} x {h_in:.1f} in; label conflicts: {len(conflicts)}")
    for sc, s in sorted(conflicts, reverse=True)[:40]:
        print("  ", sc, s)


if __name__ == "__main__":
    main()
