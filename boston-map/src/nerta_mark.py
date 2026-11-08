"""NERTA wordmark: a small, wide mark that sits under the T roundel.

Everything is drawn as vector patches in data units (letters are TextPath
outlines of Arial Bold), so the mark is scale-free: the same call works on the
main map (4.836 pt per unit) and on the line posters (5.4 pt per unit), and it
stays crisp in the PDF. Assumes an equal-aspect axis.

    bottom = draw_nerta(ax, cx, top, width, variant="A", z=12)

Variants
    A  tracked bold caps between two thin ink rules
    B  white tracked caps in a rounded ink bar (pill)
    C  tracked bold caps over a five-color line stripe
"""
from matplotlib.font_manager import FontProperties
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D

INK, WHITE = "#16161a", "#ffffff"
STRIPE = ("#da291c", "#ed8b00", "#00843d", "#003da5", "#f5c400")  # red, orange, green, blue, yellow

BOLD = FontProperties(fname=r"C:\Windows\Fonts\arialbd.ttf")
WORD = "NERTA"
# Optical kerning, as a share of the base gap: open shapes (T arms, A slopes)
# already carry white space, so the gaps beside them close up a little.
KERN = {("N", "E"): 1.0, ("E", "R"): 0.84, ("R", "T"): 0.66, ("T", "A"): 0.40}

# Height of the whole mark as a share of its width, per variant.
RATIO = {"A": 0.215, "B": 0.215, "C": 0.235}


def _glyphs(cap):
    """Return [(letter, path, x0, x1)] with cap height = cap, baseline at y=0."""
    ref = TextPath((0, 0), "N", size=1, prop=BOLD).get_extents()
    size = cap / ref.y1
    out = []
    for ch in WORD:
        p = TextPath((0, 0), ch, size=size, prop=BOLD)
        e = p.get_extents()
        out.append((ch, p, e.x0, e.x1))
    return out


def _word(ax, cx, base, cap, track, color, z):
    """Draw NERTA centered on cx (ink edges), base gap = track * cap. Returns ink width."""
    g = _glyphs(cap)
    weights = [KERN[(a[0], b[0])] for a, b in zip(g, g[1:])]
    gap = track * cap
    span = sum(x1 - x0 for _, _, x0, x1 in g) + gap * sum(weights)
    x = cx - span / 2
    for i, (ch, p, x0, x1) in enumerate(g):
        t = Affine2D().translate(x - x0, base)
        ax.add_patch(PathPatch(t.transform_path(p), fc=color, ec="none", lw=0, zorder=z + 0.1))
        x += (x1 - x0) + (gap * weights[i] if i < len(weights) else 0)
    return span


def _stadium(x0, y0, w, h):
    """A true pill: straight sides with full half-circle ends."""
    r = h / 2
    left = Path.arc(90, 270)
    right = Path.arc(-90, 90)
    lv = left.vertices * r + (x0 + r, y0 + r)
    rv = right.vertices * r + (x0 + w - r, y0 + r)
    verts = list(rv) + list(lv) + [rv[0]]
    codes = [Path.MOVETO] + list(right.codes[1:]) + [Path.LINETO] + list(left.codes[1:]) + [Path.CLOSEPOLY]
    return Path(verts, codes)


def _ring(ax, cx, cy, w, h, colors, z, k_out, k_col):
    """A stadium-shaped ring of color inside the pill's black edge: one color solid, several as 45-degree stripes."""
    from shapely.affinity import rotate
    from shapely.geometry import LineString, box
    r = h / 2
    pill = LineString([(cx - w / 2 + r, cy), (cx + w / 2 - r, cy)]).buffer(r, resolution=32)
    outer, inner = pill.buffer(-h * k_out, resolution=32), pill.buffer(-h * (k_out + k_col), resolution=32)
    ring = outer.difference(inner)
    if len(colors) == 1:
        _fill(ax, ring, colors[0], z)
        return
    gap = h * (1 - 2 * k_out) - h * k_col  # between the centerlines of the top and bottom straights
    pitch = gap / max(1, round(gap / ((w + h) / 22)))
    x0, y0, _, _ = ring.bounds
    _stripes(ax, ring, pitch, x0 + y0, colors, z)


def draw_nerta(ax, cx, top, width, variant="A", z=12, colors=None):
    """Draw the NERTA mark with its top edge at `top`, centered on cx.

    `width` is the full outer width of the mark in data units (match the
    roundel's outer diameter). Returns the bottom y of the mark.
    """
    v = variant.upper()
    h = width * RATIO[v]
    bottom = top - h
    x0 = cx - width / 2

    if v == "A":
        rule = h * 0.075
        cap = h * 0.54
        ax.add_patch(Rectangle((x0, top - rule), width, rule, fc=INK, ec="none", lw=0, zorder=z))
        ax.add_patch(Rectangle((x0, bottom), width, rule, fc=INK, ec="none", lw=0, zorder=z))
        # Letters centered between the inner edges of the rules.
        mid = (top - rule + bottom + rule) / 2
        _word(ax, cx, mid - cap / 2, cap, 0.62, INK, z)

    elif v == "B":
        ax.add_patch(PathPatch(_stadium(x0, bottom, width, h), fc=INK, ec="none", lw=0, zorder=z))
        if colors:  # like the T: black edge, a ring of line color, then the black pill (Max, November 7)
            _ring(ax, cx, bottom + h / 2, width, h, colors, z + 0.01, k_out=0.075, k_col=0.10)
        cap = h * 0.50
        _word(ax, cx, bottom + (h - cap) / 2, cap, 0.34, WHITE, z)

    elif v == "C":
        cap = h * 0.56
        bar = h * 0.14
        _word(ax, cx, top - cap, cap, 0.62, INK, z)
        n = len(STRIPE)
        seg_gap = width * 0.012
        seg = (width - seg_gap * (n - 1)) / n
        sy = bottom
        for i, c in enumerate(STRIPE):
            ax.add_patch(Rectangle((x0 + i * (seg + seg_gap), sy), seg, bar, fc=c, ec="none", lw=0, zorder=z))
    else:
        raise ValueError(f"unknown NERTA variant {variant!r}")
    return bottom


# ---------------------------------------------------------------------------------------------------------------
# The T (Max, November 7): a bold block T in three layers, a black outline, a band of color, and a white core.
# Line posters use their line's color; the main map uses a diagonal rainbow of the line colors.
RAINBOW = ("#da291c", "#ed8b00", "#f5c400", "#00843d", "#00a9c9", "#003da5", "#3f3fb5")  # red, orange, yellow, green, cyan, blue, indigo


T_OUT, T_COL, T_PITCH = 0.08, 0.072, 0.09   # black edge, color band, stripe pitch (in x + y), all as shares of the roundel radius


def _t_dims(r):
    """Band corners on a diagonal grid of pitch w: half stem 1.5w, half bar 6.5w, bar height 3w, stem below the bar 11w.
    22 stripes in all, so each of 11 colors shows exactly twice. Returns the T outline numbers and the vertical shift that centers it."""
    o, w = T_OUT * r, T_PITCH * r
    S, A, TB, BD, B = 1.5 * w, 6.5 * w, 3 * w, 11 * w, 0.28 * r
    a, s, bar, top, bot = A + o, S + o, B - o, B + TB + o, BD - B + o
    return a, s, bar, top, bot, (bot - top) / 2


def _t_shape(cx, cy, r):
    from shapely.geometry import Polygon as SP
    a, s, bar, top, bot, lift = _t_dims(r)
    cy = cy + lift  # centered in the roundel
    return SP([(cx - a, cy + top), (cx + a, cy + top), (cx + a, cy + bar), (cx + s, cy + bar), (cx + s, cy - bot), (cx - s, cy - bot),
               (cx - s, cy + bar), (cx - a, cy + bar)])


def _stripes(ax, shape, w, phase, colors, z):
    """45-degree stripes over a shapely shape: edges on the lines x + y = phase + k w, colors in order, repeating."""
    import math
    from shapely.geometry import Polygon as SP
    x0, y0, x1, y1 = shape.bounds
    big = 10 * (x1 - x0 + y1 - y0 + 1)
    for k in range(math.floor((x0 + y0 - phase) / w) - 1, math.ceil((x1 + y1 - phase) / w) + 1):
        ua, ub = phase + k * w, phase + (k + 1) * w
        cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
        band = SP([(ua - cy_ + big, cy_ - big), (ub - cy_ + big, cy_ - big), (ub - cy_ - big, cy_ + big), (ua - cy_ - big, cy_ + big)])
        _fill(ax, shape.intersection(band), colors[k % len(colors)], z)


def _fill(ax, geom, fc, z):
    """Fill shapely polygons, holes included (a solid ring has one)."""
    for g in getattr(geom, "geoms", [geom]):
        if g.geom_type in ("MultiPolygon", "GeometryCollection"):
            _fill(ax, g, fc, z)
            continue
        if g.is_empty or g.geom_type != "Polygon":  # stripe cuts that only touch along an edge leave lines and points; skip them
            continue
        rings = [g.exterior] + list(g.interiors)
        verts, codes = [], []
        for ring_ in rings:
            pts = list(ring_.coords)
            verts += pts
            codes += [Path.MOVETO] + [Path.LINETO] * (len(pts) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec="none", lw=0, zorder=z))


def draw_t(ax, cx, cy, r, colors=RAINBOW, z=12.1, k_out=0.08, k_col=0.072, core=WHITE):
    """Draw the T inside a roundel of radius r centered at (cx, cy). One color: a solid band. Several: diagonal stripes at 45 degrees,
    like the map's lines."""
    r = r * 0.9  # the T fills 90% of the roundel, clear of the ring; every proportion scales with it, so the stripes stay aligned
    t = _t_shape(cx, cy, r)
    band = t.buffer(-r * k_out, join_style=2)
    inner = t.buffer(-r * (k_out + k_col), join_style=2)
    _fill(ax, t, INK, z)
    if len(colors) == 1:
        _fill(ax, band, colors[0], z + 0.01)
    else:
        _, s, _, _, bot, lift = _t_dims(r)
        phase = (cx - (s - r * k_out)) + (cy + lift - (bot - r * k_out))  # the band's bottom-left corner: red starts there
        _stripes(ax, band, T_PITCH * r, phase, colors, z + 0.01)
    _fill(ax, inner, core, z + 0.02)
