"""Charlie Points and free rides: the shared symbols for every NERTA map (Max, November 8, 2026).

Riders pay with Charlie Points, with monthly passes. Every Key carries the CP coin and one line; free rides carry a
white FREE tag on the line. Spec and the free list: research/fares-changes-for-all-maps.md.

    from charlie_points import draw_cp, draw_free_tag, KEY_TEXT, FREE_TEXT
    draw_cp(ax, x, y, r)                      # the coin, centered at (x, y), radius r in data units
    draw_free_tag(ax, x, y, h, angle=0)       # a FREE pill on a line; h = pill height in data units. Make it about
                                              # 11 pt tall (or 1.4 x the line width if that's bigger) so FREE reads
                                              # at normal viewing size; thin lines need the bigger floor.

Both are vector patches in data units (equal-aspect axes), so they scale with the map. Colors follow
make_tmap.NERTA_COLORS, so the coin's rim changes when the logo's colors do.
"""
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Circle, PathPatch, Wedge
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D

INK, WHITE = "#16161a", "#ffffff"
BOLD = FontProperties(fname=r"C:\Windows\Fonts\arialbd.ttf")
KEY_TEXT = "Pay with Charlie Points. Monthly passes available."
FREE_TEXT = "Free ride, no Charlie Points needed"


def _colors():
    try:
        import make_tmap as M
        return tuple(M.NERTA_COLORS)
    except Exception:  # standalone use: the line colors in Max's order, tram pink last
        return ("#da291c", "#ed8b00", "#f5c400", "#003da5", "#00796d", "#00a9c9", "#7c878e", "#ffd23f", "#3f3fb5", "#80276c",
                "#00843d", "#e0457b")


def _text(ax, s, x, y, cap, color, z, angle=0.0):
    """Arial Bold text as a vector path, centered at (x, y), cap height `cap` data units."""
    ref = TextPath((0, 0), "C", size=1, prop=BOLD).get_extents()
    tp = TextPath((0, 0), s, size=cap / ref.y1, prop=BOLD)
    e = tp.get_extents()
    t = Affine2D().translate(-(e.x0 + e.x1) / 2, -cap / 2).rotate_deg(angle).translate(x, y)
    ax.add_patch(PathPatch(t.transform_path(tp), fc=color, ec="none", lw=0, zorder=z))


BLACK = FontProperties(fname=r"C:\Windows\Fonts\ariblk.ttf")


def _letter_shape(s, cap, x, y):
    """Text as a shapely shape (holes kept), cap height `cap`, centered on (x, y)."""
    from shapely.affinity import scale, translate
    from shapely.geometry import Polygon as SP
    tp = TextPath((0, 0), s, size=1, prop=BLACK)
    shape = None
    for poly in sorted((SP(q).buffer(0) for q in tp.to_polygons() if len(q) > 2), key=lambda q: -q.area):
        if shape is None:
            shape = poly
        elif shape.contains(poly.representative_point()):
            shape = shape.difference(poly)
        else:
            shape = shape.union(poly)
    b = shape.bounds
    k = cap / (b[3] - b[1])
    shape = scale(shape, k, k, origin=(0, 0))
    b = shape.bounds
    return translate(shape, x - (b[0] + b[2]) / 2, y - (b[1] + b[3]) / 2)


def draw_cp(ax, x, y, r, z=12, colors=None):
    """The Charlie Points coin (Max, November 8): a rim of every NERTA color and an ink face, with CP lettered like the T:
    each letter in three layers, a white outline, a band of diagonal stripes in every color, and a white core."""
    import nerta_mark as NM
    cs = colors or _colors()
    n = len(cs)
    for i, c in enumerate(cs):
        ax.add_patch(Wedge((x, y), r, 90 - (i + 1) * 360 / n, 90 - i * 360 / n, width=r * 0.17, fc=c, ec="none", zorder=z))
    ax.add_patch(Circle((x, y), r * 0.83, fc=INK, ec="none", zorder=z))
    ax.add_patch(Wedge((x, y), r, 0, 360, width=r * 0.06, fc=INK, ec="none", zorder=z + 0.1))   # thin ink outer edge
    t = _letter_shape("CP", r * 0.62, x, y)
    k = r * 0.02    # outline inset; core at 3.6k = 0.072r keeps all three layers (Arial Black strokes are under 0.2r wide)
    NM._fill(ax, t, WHITE, z + 0.2)
    NM._stripes(ax, t.buffer(-k, join_style=2), r * 0.09, x + y, cs, z + 0.3)
    NM._fill(ax, t.buffer(-3.6 * k, join_style=2), WHITE, z + 0.4)
    return (x - r, y - r, x + r, y + r)


def draw_free_tag(ax, x, y, h, angle=0.0, z=12, edge_pt=1.0):
    """A white FREE pill with an ink edge, centered on (x, y), with the Charlie Points coin in its left end and the word
    FREE beside it (Max, November 8: "it should say free and have the CP symbol alongside it"). Always level, even on a
    diagonal line: Max allows no tilted text. `angle` is kept for callers but ignored."""
    angle = 0.0
    ref = TextPath((0, 0), "FREE", size=1, prop=BOLD).get_extents()
    cap = h * 0.45
    tw = (ref.x1 - ref.x0) * cap / TextPath((0, 0), "F", size=1, prop=BOLD).get_extents().y1
    r = h / 2
    rc = h * 0.36                     # coin radius: sits concentric in the pill's left round end
    gap = h * 0.16
    w = h + gap + tw + h * 0.5        # left end holds the coin, then the word, then half a height of margin
    th = np.linspace(-np.pi / 2, np.pi / 2, 24)
    right = np.column_stack([w / 2 - r + r * np.cos(th), r * np.sin(th)])
    left = np.column_stack([-w / 2 + r - r * np.cos(th), -r * np.sin(th)])
    pts = np.vstack([right, left, right[:1]])
    a = np.radians(angle)
    rot = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    pts = pts @ rot.T + [x, y]
    from matplotlib.patches import Polygon
    ax.add_patch(Polygon(pts, closed=True, fc=WHITE, ec=INK, lw=edge_pt, joinstyle="round", zorder=z))
    cx = x - w / 2 + r
    draw_cp(ax, cx, y, rc, z=z + 0.1)
    tx = cx + rc + gap + tw / 2
    _text(ax, "FREE", tx, y, cap, INK, z + 0.1, angle)
    return pts


if __name__ == "__main__":  # quick look
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 2.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)
    ax.set_aspect("equal")
    ax.axis("off")
    draw_cp(ax, 1.5, 2, 1.0)
    ax.plot([4, 11], [2, 2], color="#7c878e", lw=7, solid_capstyle="round")
    draw_free_tag(ax, 7.5, 2, 0.45)
    ax.plot([4.5, 6.5], [0.5, 1.5], color="#e0457b", lw=4)
    draw_free_tag(ax, 5.5, 1.0, 0.3, angle=26.6)
    import sys
    fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "cp_check.png", dpi=200, bbox_inches="tight")
