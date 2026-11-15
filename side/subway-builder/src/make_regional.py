"""Regional map: Spencer's five regional rail lines over his subway.

Geographic, with a gentle zoom on the core (distance from Government Center
is compressed) so downtown still fits. Land is the Census town layer.
"""
import json
from collections import defaultdict

import geopandas as gpd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from pyproj import Transformer
from shapely.ops import transform as shp_transform
from shapely.geometry import box

from kit import (INK, PAPER, WATER, COAST, COLORS, OUT, PRIV, ROOT, ROUTES,
                 THIN, Network, draw_station, place_labels, route_color,
                 sample_lines, wrap, display, rounded)
import network
from network import REGIONAL, GEO_ALIAS

UNIT_PT = 2.0
TO_M = Transformer.from_crs(4326, 26919, always_xy=True)


def geo_points():
    d = json.load(open(PRIV / "bostonstations.geojson"))
    acc = defaultdict(list)
    for f in d["features"]:
        acc[f["properties"]["name"].strip()].append(f["geometry"]["coordinates"])
    return {k: np.mean(v, axis=0) for k, v in acc.items()}


GEO = geo_points()
C0 = np.array(TO_M.transform(*GEO["Government Center"]))


def squash(x, y, r0=40000.0, k=0.62):
    dx, dy = np.asarray(x) - C0[0], np.asarray(y) - C0[1]
    r = np.hypot(dx, dy)
    s = np.where(r > 0, r0 * (np.maximum(r, 1e-6) / r0) ** k / np.maximum(r, 1e-6), 1.0)
    return dx * s / 1000.0, dy * s / 1000.0   # km-like map units


def where(name):
    lo, la = GEO[GEO_ALIAS.get(name, name)]
    x, y = TO_M.transform(lo, la)
    u, v = squash(x, y)
    return float(u), float(v)


def main():
    # every stop on every line, regional or subway
    names = set()
    for _, _, st in ROUTES.values():
        names.update(st)
    for _, st in REGIONAL.values():
        names.update(st)
    P = {n: where(n) for n in names}

    xs = np.array([p[0] for p in P.values()]); ys = np.array([p[1] for p in P.values()])
    x0, x1 = xs.min() - 8, xs.max() + 12
    y0, y1 = ys.min() - 8, ys.max() + 16
    scale = 8.0   # map units -> plot units
    fig_w = (x1 - x0) * scale * UNIT_PT / 72
    fig_h = (y1 - y0) * scale * UNIT_PT / 72
    fig = plt.figure(figsize=(fig_w, fig_h), facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x0 * scale, x1 * scale); ax.set_ylim(y0 * scale, y1 * scale)
    ax.set_aspect("equal"); ax.axis("off"); ax._kit_unit_pt = UNIT_PT
    ax.add_patch(plt.Rectangle((x0 * scale, y0 * scale), (x1 - x0) * scale,
                               (y1 - y0) * scale, color=WATER, zorder=0))
    P = {k: (v[0] * scale, v[1] * scale) for k, v in P.items()}

    # land
    towns = gpd.read_file(ROOT.parents[1] / "data/shared/ne_towns.gpkg")
    lo0, la0 = TO_M.transform(*GEO["Government Center"], direction="INVERSE") if False else GEO["Government Center"]
    towns = towns.cx[lo0 - 1.4:lo0 + 1.1, la0 - 0.9:la0 + 0.8]
    def f(x, y, z=None):
        mx, my = TO_M.transform(x, y)
        u, v = squash(np.array(mx), np.array(my))
        return u * scale, v * scale
    land = shp_transform(f, towns.geometry.union_all().buffer(0))
    gpd.GeoSeries([land]).plot(ax=ax, color=PAPER, edgecolor=COAST, lw=0.7, zorder=1)
    borders = shp_transform(f, towns.geometry.boundary.union_all())
    gpd.GeoSeries([borders]).plot(ax=ax, color="#e4e2dc", lw=0.35, zorder=1.5)

    # subway, thin and underneath
    sub = Network(P, list(ROUTES), gap=1.1)
    for code in sub.codes:
        lw = 0.7 if code in THIN else 1.5
        ax.plot(*np.array(sub.paths[code]).T, color=route_color(code), lw=lw,
                alpha=0.75, zorder=3, solid_capstyle="round")

    # regional rail
    saved = dict(ROUTES)
    for code, (nm, st) in REGIONAL.items():
        network.ROUTES[code] = (nm, "cr", st)
    import kit
    kit.ORDER.extend([c for c in REGIONAL if c not in kit.ORDER])
    cr = Network(P, list(REGIONAL), gap=2.6)
    CR = COLORS["crtext"]
    for code in cr.codes:
        p = rounded(cr.paths[code], r=4)
        ax.plot(*p.T, color=PAPER, lw=5.4, zorder=6, solid_capstyle="round")
    for code in cr.codes:
        p = rounded(cr.paths[code], r=4)
        ax.plot(*p.T, color=CR, lw=3.4, zorder=7, solid_capstyle="round")

    # stops
    items = []
    crstops = defaultdict(list)
    for code, (_, st) in REGIONAL.items():
        for n in st:
            crstops[n].append(code)
    for n, codes in crstops.items():
        pts = []
        for c in codes:
            p = cr.at[n][c]
            if not any(np.linalg.norm(p - q) < 0.3 for q in pts):
                pts.append(p)
        draw_station(ax, pts, 1.6, 0.8, z=20)
        u = np.array(pts)
        term = any(REGIONAL[c][1][0] == n or REGIONAL[c][1][-1] == n for c in codes)
        txt = wrap(display(n), 16)
        items.append((n, txt.upper() if term else txt, tuple(u.mean(axis=0)),
                      (np.ptp(u[:, 0]) / 2 + 1.6, np.ptp(u[:, 1]) / 2 + 1.6),
                      "bold" if term else "normal"))
    for n in sub.at:
        if n in crstops:
            continue
        for p in list(sub.at[n].values())[:1]:
            ax.add_patch(plt.Circle(p, 0.55, facecolor="white", edgecolor=INK,
                                    lw=0.3, zorder=8))
    line_pts = sample_lines([cr.paths[c] for c in cr.codes])
    place_labels(fig, ax, items, line_pts, size=7, pad=1.0,
                 frame=(x0 * scale, y0 * scale, x1 * scale, y1 * scale))

    # line names at the outer ends
    for code, (nm, st) in REGIONAL.items():
        a, b = nm.replace(" Line", "").split(" / ")
        for end, label in ((st[0], a), (st[-1], b)):
            pass

    # title and key
    X0, Y1 = x0 * scale, y1 * scale
    ax.text(X0 + 14, Y1 - 12, "Regional Rail", fontsize=40, weight="bold", va="top", zorder=50)
    ax.text(X0 + 14, Y1 - 36, "A Subway Builder network by Spencer F.", fontsize=17, va="top", zorder=50)
    ax.text(X0 + 14, Y1 - 49, "Map: Maxwell Howe", fontsize=12, va="top", zorder=50)
    ax.text(X0 + 14, Y1 - 60,
            "Distance from downtown is compressed so the core fits;\n"
            "outer stops are in their true direction.",
            fontsize=8.5, va="top", zorder=50, linespacing=1.35)
    kx, ky = x1 * scale - 150, y0 * scale + 120
    ax.add_patch(plt.Rectangle((kx - 8, y0 * scale + 10), 152, 122, facecolor="white",
                               edgecolor=INK, lw=0.8, zorder=45))
    ax.text(kx, ky, "REGIONAL RAIL", fontsize=11, weight="bold", va="center", zorder=46)
    for i, (code, (nm, st)) in enumerate(REGIONAL.items()):
        yy = ky - 13 - i * 12
        ax.plot([kx, kx + 18], [yy, yy], color=CR, lw=3.4, zorder=46)
        ax.text(kx + 24, yy, f"{code[-1]}  {nm.upper()}", fontsize=7.5, va="center", zorder=46)
    ax.plot([kx, kx + 18], [ky - 78, ky - 78], color=COLORS["red"], lw=1.5, zorder=46)
    ax.text(kx + 24, ky - 78, "Subway lines (see subway map)", fontsize=7.5, va="center", zorder=46)
    ax.text(kx, ky - 94,
            "Regional rail stops are rebuilt from Spencer's map\n"
            "screenshots and transfer lists. Check with him.",
            fontsize=6.5, va="top", zorder=46, linespacing=1.3)

    for ext, dpi in (("pdf", None), ("png", 200)):
        fig.savefig(OUT / f"spencer_regional_map.{ext}", dpi=dpi, facecolor=PAPER)
    print("saved", round(fig_w, 1), round(fig_h, 1))


if __name__ == "__main__":
    main()
