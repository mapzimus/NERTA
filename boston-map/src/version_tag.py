"""The version mark on every finished NERTA map (Max, November 8, 2026): a small "v1.0" in the bottom left corner.

    from version_tag import draw_version, VERSION, final_names
    draw_version(ax, x0, y0, ppu)            # x0, y0 = the sheet's bottom-left corner in data units; ppu = points per unit
    final_names("tram-network")              # -> ("tram-network_v1.0_with-disclaimer", "tram-network_v1.0_no-disclaimer")

Every map gets two finished versions, named as such: one with the release block (disclaimer, credit, hashtag, Day 8)
and one without it (the nerta.fun web copy). Both carry the version mark.
"""
VERSION = "v1.0"
INK_SOFT = "#5b616b"


def draw_version(ax, x0, y0, ppu, size=7.0, margin_pt=14.0, color=INK_SOFT, z=13, text=None):
    """Small level text, its bottom-left corner margin_pt in from the sheet's bottom-left corner."""
    m = margin_pt / ppu
    return ax.text(x0 + m, y0 + m, text or VERSION, fontsize=size, color=color, ha="left", va="bottom", zorder=z, family="Arial")


def final_names(stem):
    """File stems for the two finished versions of a map."""
    return (f"{stem}_{VERSION}_with-disclaimer", f"{stem}_{VERSION}_no-disclaimer")
