"""Coverage map: both networks on real geography, half-mile walksheds shaded."""
import sys
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import compare as C

plt.rcParams.update({"font.family": "Liberation Sans"})
towns = gpd.read_file(C.HERE.parents[2] / "data/shared/ne_towns.gpkg").to_crs(C.CRS)
R = C.report()
fig, ax = plt.subplots(figsize=(16, 16), facecolor="#fcfcfa")
xs = [p[0] for p in list(C.SM.values()) + list(C.NM.values())]
ys = [p[1] for p in list(C.SM.values()) + list(C.NM.values())]
x0, x1, y0, y1 = min(xs) - 2500, max(xs) + 2500, min(ys) - 2500, max(ys) + 2500
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.axis("off")
ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, color="#c9e3ee", zorder=0))
towns.cx[x0:x1, y0:y1].plot(ax=ax, color="#fcfcfa", edgecolor="#dedbd3", lw=0.4, zorder=1)
gpd.GeoSeries([C.both], crs=C.CRS).plot(ax=ax, color="#cfcfcf", alpha=0.8, zorder=2)
gpd.GeoSeries([C.s_only], crs=C.CRS).plot(ax=ax, color="#f2b766", alpha=0.75, zorder=2)
gpd.GeoSeries([C.n_only], crs=C.CRS).plot(ax=ax, color="#8fb3e8", alpha=0.85, zorder=2)
for (a, b) in C.n_edges:
    p, q = C.NM[a], C.NM[b]
    ax.plot([p[0], q[0]], [p[1], q[1]], color="#1f4fa8", lw=1.6, zorder=4)
for (a, b) in C.s_edges:
    p, q = C.SM[a], C.SM[b]
    ax.plot([p[0], q[0]], [p[1], q[1]], color="#c46a00", lw=1.0, zorder=5, ls=(0, (3, 1.5)))
for p in C.NM.values():
    ax.plot(*p, "o", ms=2.6, color="#1f4fa8", zorder=6)
for p in C.SM.values():
    ax.plot(*p, "o", ms=2.2, color="#c46a00", zorder=7)
halo = [pe.withStroke(linewidth=2.5, foreground="white")]
for n, dmin, r, j in R["spencer_gaps"][:14]:
    p = C.SM[n]
    ax.text(p[0] + 500, p[1] + 300, C.display(n), fontsize=8.5, color="#7a4200", zorder=9, path_effects=halo)
for n, dmin, r, j in R["nerta_gaps"][:8]:
    p = C.NM[n]
    ax.text(p[0] + 500, p[1] - 900, n, fontsize=8.5, color="#163c80", zorder=9, path_effects=halo)
ax.text(x0 + 1500, y1 - 1500, "Spencer vs NERTA: who serves where", fontsize=24, weight="bold", va="top")
ax.text(x0 + 1500, y1 - 4300,
        "Half-mile walk around every stop.  Gray: both.  Orange: Spencer only.  Blue: NERTA only.\n"
        "Orange dashed: Spencer's subway.  Blue solid: NERTA T (all styles).  Straight lines between stops, not track.",
        fontsize=10.5, va="top", linespacing=1.4)
fig.savefig(C.HERE.parent / "private/output/comparison_map.png", dpi=150, facecolor="#fcfcfa", bbox_inches="tight")
print("ok")
