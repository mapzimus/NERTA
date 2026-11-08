"""The release block for the November 8 #30DayMapChallenge posts (Max, November 7).

Every map published that day carries the same four things the main map has at its top left:
the disclaimer paragraph, "Map: Maxwell Howe", "#30DayMapChallenge" and "Day 8 • Utopia".
The main map draws its own copy to Max's Illustrator layout; posters call draw_release().
The nerta.fun web versions leave it out (see WEB in make_tmap.py).
"""
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

CREDIT = ("Map: Maxwell Howe", "#30DayMapChallenge", "Day 8 \u2022 Utopia")
DISCLAIMER = ("This is a futuristic concept map", "and is not affiliated with the MBTA", "in any way. MOST of the map decisions",
              "are grounded in real data & studies,", "proposals made, or projections for", "future projects or development.")
NARROW = FontProperties(fname=r"C:\Windows\Fonts\ARIALNI.TTF")        # Arial Narrow Italic, as on the main map
NARROW_BOLD = FontProperties(fname=r"C:\Windows\Fonts\ARIALNBI.TTF")  # MOST in bold (Max, November 7)
ARIAL = FontProperties(family="Arial")


def _w(text, fp, size, ppu):
    """Ink width of text in drawing units."""
    return TextPath((0, 0), text, size=size, prop=fp).get_extents().x1 / ppu


def release_width(size=9.6, ppu=4.836, gap=3.0):
    """Width of the whole block in drawing units, for callers that need to make room."""
    para = max(_w(t, NARROW, size, ppu) for t in DISCLAIMER)
    cred = max(_w(t, ARIAL, size, ppu) for t in CREDIT)
    return para + gap + cred


def draw_release(ax, right, cy, size=9.6, ppu=4.836, gap=3.0, ink="#1a1a1a", z=13):
    """Draw the block with its right edge at `right`, centered on `cy`.

    Two columns, as on the main map: the disclaimer paragraph, then the credit lines flush right.
    Returns (left, bottom, top) in drawing units so the caller can check it clears the title and the first stop.
    """
    pitch = size * 1.2 / ppu
    cap = size * 0.72 / ppu  # cap height above a baseline
    cred_w = max(_w(t, ARIAL, size, ppu) for t in CREDIT)
    para_w = max(_w(t, NARROW, size, ppu) for t in DISCLAIMER)
    left = right - cred_w - gap - para_w
    # Paragraph: six baselines centered on cy (cap height counted, so the ink is centered)
    top_base = cy + (len(DISCLAIMER) - 1) * pitch / 2 - cap / 2
    for k, t in enumerate(DISCLAIMER):
        x, y = left, top_base - k * pitch
        for part in t.replace("MOST", "|MOST|").split("|"):
            fp = NARROW_BOLD if part == "MOST" else NARROW
            ax.text(x, y, part, fontproperties=fp, fontsize=size, color="#000000", va="baseline", zorder=z)
            x += _w(part, fp, size, ppu)
            if part.endswith(" "):  # ink width leaves out the trailing space
                x += 0.27 * size / ppu
    # Credit column: three baselines, top-aligned with the paragraph
    for k, t in enumerate(CREDIT):
        ax.text(right, top_base - k * pitch, t, fontproperties=ARIAL, fontsize=size, color=ink, ha="right", va="baseline", zorder=z)
    bottom = top_base - (len(DISCLAIMER) - 1) * pitch - 0.22 * size / ppu
    return left, bottom, top_base + cap
