"""Commuter Rail Network: the station display.

A portrait sheet to hang in stations, set like the Ferry Network display. Max, November 8: "make a poster map that would
hang in the stations that shows the commuter rail and its connections like the large ferry display". Every commuter line,
every station and its connections (the T, the ferries and high-speed rail), with the boxes riders read: Lines, Key,
Transfers, How the trains run, and a Passenger Notice.

It draws with the rail poster's own pieces (make_rail_poster.py: line styles, stations, pills, transfers, checks), so the
two can't disagree, on a taller layout for a portrait sheet: the Worcester and Franklin lines run south in columns instead
of long diagonals, and the North Shore sits closer in. High-speed trains stop at Lowell, Haverhill, Worcester and
Providence as well as the six stations near Boston, as the line posters and the regional map show.

Writes only to output/copies/rail_network_vN.png and .pdf and never overwrites.
Run: python make_rail_network.py [version] [--draft DIR]
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import make_rail_poster as RP  # noqa: E402  (read only: the rail poster's drawing pieces and data)
from make_rail_poster import STEP, YC, YN, YS, cut, diag_stops, col_stops, join, on, par, st, walk  # noqa: E402
from nerta_mark import draw_nerta  # noqa: E402
import make_line_poster as LP  # noqa: E402  (read only: roundel)
import make_tmap as M  # noqa: E402  (read only: WEB, the nerta.fun switch)
from station_kit import INK, WHITE  # noqa: E402

try:
    import rail_network_panels as PN  # the Lines, Key, Transfers, How the trains run and Passenger Notice boxes
except ImportError:  # pragma: no cover - the boxes are optional while the layout is tried out
    PN = None

OUT = RP.OUT
K, PPU = RP.K, RP.PPU
PURPLE, GOLD, PAPER = RP.PURPLE, RP.GOLD, RP.PAPER

# ---------------------------------------------------------------------------------------------------------------
# Layout. The trunk (North Station, Boston Central, South Station) and the north spine are the rail poster's.
SS = 86.0          # South Salem, where the Peabody line crosses the Newburyport/Rockport line (clear of North Station's pills)
WOR_X = -64.0      # the Worcester line's column; the Albany high-speed line runs 2 units east of it
FRA_X = -36.0      # the Franklin line's column
WEST_Y = -68.0     # West Station, the top of the Worcester column
FRA_Y = -78.4      # Endicott, the top of the Franklin column

N_SPINE = RP.N_SPINE
NE_SPINE = RP.NE_SPINE
A_S = RP.A_S
B_S = RP.B_S
# The Worcester pair: south out of South Station, west at Back Bay, then south in a column. The column runs 4 units west of
# this path (the Worcester line) and 2 units west (the Albany line), so names to the left never cross the high-speed line.
A_W = [(3, YN), (3, -34), (-9, -46), (-9, -58), (WOR_X + 4 + 6, -58), (WOR_X + 4, -64), (WOR_X + 4, -400)]

WORCESTER = ["West Station", "Boston Landing", "Newtonville", "West Newton", "Auburndale", "Wellesley Farms", "Wellesley Hills",
             "Wellesley Square", "Natick Center", "West Natick", "Framingham", "Ashland", "Southborough", "Westborough", "Grafton",
             "Worcester"]
FRANKLIN = ["Endicott", "Dedham Corporate Center", "Islington", "Norwood Depot", "Norwood Central", "Windsor Gardens", "Walpole", "Norfolk",
            "Franklin", "Forge Park/495"]
PROVIDENCE = ["Attleboro", "Pawtucket/Central Falls", "Providence", "TF Green Airport", "Wickford Junction"]

STACKED = {}   # end station -> (line, "above" or "below"): its line pill on a row of its own, where inline would run too far


def y_of(names, name, y0):
    return y0 - STEP * names.index(name)


def build():
    P = RP.PATHS
    # North side, as on the rail poster
    P["fit"] = join(par(cut(N_SPINE, (-7, 3)), 6), walk((-13, 3), ("NW", 55)))
    P["low"] = par(cut(N_SPINE, (-7, 52.4)), 4)
    P["hmon"] = par(cut(N_SPINE, (-7, 62)), 2)
    P["hmai"] = par(cut(N_SPINE, (-7, 62)), 0)
    P["hav"] = par(cut(N_SPINE, (-7, 20 + STEP * (len(RP.HAVERHILL) - 1))), -2)
    # North Shore, closer in: along the shore to Beverly, then the Rockport fork northeast
    P["nbp"] = join(par(cut(NE_SPINE, (SS + 44, 9)), -4), walk((SS + 44, 5), ("NE", 21)))
    P["pea"] = walk((SS + 7, -8), ("NW", 7), ("N", 33))
    # South side: the Worcester pair and the Franklin line run south in columns
    wy = y_of(WORCESTER, "Worcester", WEST_Y)
    P["wor"] = cut(par(A_W, -4), (WOR_X, wy))
    P["halb"] = cut(par(A_W, -2), (WOR_X + 2, wy - 8))
    P["fra"] = join(par(cut(A_S, (-9, -74)), 0), walk((-9, -74), ("W", -9 - FRA_X), ("S", -74 - y_of(FRANKLIN, "Forge Park/495", FRA_Y))))
    wal = y_of(FRANKLIN, "Walpole", FRA_Y)
    wick = wal - STEP * len(PROVIDENCE)
    P["pro"] = par(cut(A_S, (-9, wick)), 2)
    P["hnyc"] = par(cut(A_S, (-9, wick - 8)), 4)
    P["fr"] = par(cut(B_S, (44, -125.2)), -2)
    P["kin"] = join(par(cut(B_S, (44, -85)), 0), walk((44, -85), ("E", 28), ("S", 31.4)))
    P["grb"] = join(par(cut(B_S, (44, -77)), 2), walk((46, -77), ("E", 56), ("S", 31.4)))


def stations():
    """Every station, its lines, and where its name sits."""
    every = ["fit", "low", "hmon", "hmai", "hav", "nbp", "wor", "halb", "fra", "pro", "hnyc", "fr", "kin", "grb"]
    st("North Station", every, (0, YN), "r", "hub")
    st("Boston Central", every, (0, YC), "r", "hub")
    st("South Station", every, (0, YS), "r", "hub")

    # Fitchburg Line, northwest, names to the left, with the Marlborough branch west from South Acton
    fit = diag_stops("fit", ["Porter", "Waltham", "Brandeis/Roberts", "Kendal Green", "Lincoln", "Concord", "West Concord", "South Acton",
                             "Littleton/Route 495", "Ayer", "Shirley", "North Leominster", "Fitchburg", "Wachusett"], (-13, 3), "NW", 4.0, "l")
    sa = fit["South Acton"]
    RP.BRANCHES.append(("fit", walk(sa, ("W", 34))))
    st("Hudson", ["fit"], (sa[0] - 20, sa[1]), "b")
    st("Marlborough", ["fit"], (sa[0] - 34, sa[1]), "l", "end")
    RP.ARROWS.append(("fit", RP.PATHS["fit"], ["TO GREENFIELD, NORTH ADAMS"], "nw"))

    # Lowell and Haverhill, with the two northern high-speed lines between them. High-speed trains stop at Lowell and Haverhill.
    st("Sullivan Sq", ["low", "hmon", "hmai", "hav"], (-8, 15), "r", "pass")
    col_stops("low", ["West Medford", "Wedgemere", "Winchester", "Anderson/Woburn", "Wilmington", "North Billerica"], -11, 26, "l")
    st("Lowell", ["low", "hmon"], (-11, 26 + STEP * 6), "l", "end", lp="low")
    col_stops("hav", RP.HAVERHILL[:-1], -5, 20, "r")
    st("Haverhill", ["hav", "hmai"], (-5, 20 + STEP * (len(RP.HAVERHILL) - 1)), "r", "end", lp="hav")
    RP.peabody_meets_at_lawrence()
    RP.ARROWS.append(("hmon", RP.PATHS["hmon"], ["HIGH-SPEED RAIL TO CONCORD NH, MONTREAL", "VIA LOWELL, NASHUA, MANCHESTER NH, BURLINGTON VT"], "n-left"))
    RP.ARROWS.append(("hmai", RP.PATHS["hmai"], ["HIGH-SPEED RAIL TO BANGOR", "VIA HAVERHILL, PORTLAND, AUGUSTA"], "n-right"))

    # North Shore. The Peabody line crosses at South Salem: Marblehead and Clifton below, Peabody and Danvers above, Lawrence beyond
    for n, x in (("Chelsea", 18), ("Central Sq", 38), ("Swampscott", 58)):
        st(n, ["nbp"], (x, 5), "t")
    st("South Salem", ["nbp", "pea"], (SS, 5), "ne")
    col_stops("pea", ["Peabody", "Danversport", "Danvers", "Middleton"], SS, 14, "l")
    RP.ARROWS.append(("pea", RP.PATHS["pea"], ["PEABODY LINE", "TO LAWRENCE (HAVERHILL LINE)"], "n-left-pill"))
    st("Clifton", ["pea"], (SS + 3.5, -4.5), "r")
    st("Marblehead", ["pea"], (SS + 7, -8), "r", "end", lp="pea")
    st("Salem", ["nbp"], (SS + 18, 5), "b")
    bev = st("Beverly", ["nbp"], (SS + 34, 5), "b")[0][1]
    RP.BRANCHES.append(("nbp", walk(bev, ("NE", 4), ("N", 20.6))))
    col_stops("nbp", ["North Beverly", "Hamilton/Wenham", "Ipswich", "Rowley", "Newburyport"], SS + 38, 12.0, "l", ends=("Newburyport",))
    diag_stops("nbp", ["Montserrat", "Beverly Farms", "Manchester", "West Gloucester", "Gloucester", "Rockport"], (SS + 44, 5), "NE", 3.0, "r",
               ends=("Rockport",))
    STACKED["Rockport"] = ("nbp", "above")

    # Worcester Line in a column, with the Albany high-speed line on its east side. High-speed trains stop at West Station and Worcester.
    st("Back Bay", ["wor", "halb", "fra", "pro", "hnyc"], (-9, -50), "r", "tier2")
    st("David Ortiz", ["wor"], (-30, -54), "t")
    st("West Station", ["wor", "halb"], (WOR_X + 1, WEST_Y), "l", "tier2")
    col_stops("wor", WORCESTER[1:-1], WOR_X, WEST_Y - STEP, "l", sign=-1)
    st("Worcester", ["wor", "halb"], (WOR_X + 1, y_of(WORCESTER, "Worcester", WEST_Y)), "l", "end")
    STACKED["Worcester"] = ("wor", "below")
    RP.ARROWS.append(("halb", RP.PATHS["halb"], ["HIGH-SPEED RAIL TO ALBANY, CHICAGO", "VIA WORCESTER, SPRINGFIELD"], "s"))

    # Franklin and Providence together to Readville; then Franklin west and south in its own column
    for n, y in (("Ruggles", -60), ("Hyde Park", -65), ("Readville", -70)):
        st(n, ["fra", "pro"], (-8, y), "l")
    fra = col_stops("fra", FRANKLIN, FRA_X, FRA_Y, "l", ends=("Forge Park/495",), sign=-1)
    STACKED["Forge Park/495"] = ("fra", "below")
    st("Route 128", ["pro", "hnyc"], (-6, -77), "l")
    cj = st("Canton Junction", ["pro"], (-7, -84.5), "l")[0][1]
    st("Sharon", ["pro"], (-7, -92), "l")
    wal = fra["Walpole"]
    man = on(RP.PATHS["pro"], (-7, wal[1]))
    RP.BRANCHES.append(("fra", [wal, man]))
    st("Foxboro", ["fra"], (wal[0] + 7.0, wal[1]), "b")
    st("Mansfield", ["pro", "fra"], man, "tl")
    for i, n in enumerate(PROVIDENCE):
        y = man[1] - STEP * (i + 1)
        if n == "Providence":   # high-speed trains stop at Providence
            st(n, ["pro", "hnyc"], (-6, y), "l")
        else:
            st(n, ["pro"], (-7, y), "l", "end" if n == "Wickford Junction" else "stop", lp="pro" if n == "Wickford Junction" else None)
    RP.ARROWS.append(("hnyc", RP.PATHS["hnyc"], ["HIGH-SPEED RAIL TO NYC, PHILADELPHIA, WASHINGTON", "VIA PROVIDENCE, NEW HAVEN"], "s"))
    # Stoughton branch, east across the NYC high-speed line, then south to Taunton
    RP.BRANCHES.append(("pro", walk(cj, ("E", 12), ("S", 26.6))))
    col_stops("pro", ["Canton Center", "Stoughton", "North Easton", "Easton Village", "Raynham Place", "Taunton"], 5, cj[1] - 4.6, "r",
              ends=("Taunton",), sign=-1)

    # Old Colony lines, as on the rail poster
    st("JFK/UMass", ["fr", "kin", "grb"], (44, -68), "l")
    st("Quincy Center", ["fr", "kin", "grb"], (44, -73), "l")
    st("Braintree", ["fr", "kin"], (43, -81), "l")
    col_stops("grb", ["Weymouth Landing/East Braintree", "East Weymouth", "Hingham", "Nantasket Junction", "Cohasset", "North Scituate", "Greenbush"],
              102, -82, "r", ends=("Greenbush",), sign=-1, lp="grb")
    col_stops("kin", ["South Weymouth", "Abington", "Whitman", "Hanson", "Halifax", "Kingston", "Plymouth"], 72, -90, "r", ends=("Plymouth",),
              sign=-1, lp="kin")
    frs = col_stops("fr", ["Holbrook/Randolph", "Montello", "Brockton", "Campello", "Bridgewater", "Middleborough", "East Taunton", "Church St",
                           "New Bedford"], 42, -90, "r", ends=("New Bedford",), sign=-1, lp="fr")
    mid, et = frs["Middleborough"], frs["East Taunton"]
    cape = walk(mid, ("E", 11))
    RP.BRANCHES.append(("fr", cape))
    RP.ARROWS.append(("fr", cape, ["TO CAPE COD"], "e"))
    RP.BRANCHES.append(("fr", walk(et, ("SW", 9.4))))
    st("Freetown", ["fr"], (et[0] - 4.6, et[1] - 4.6), "l")
    st("Fall River Depot", ["fr"], (et[0] - 9.4, et[1] - 9.4), "l", "end")


def stacked_pills(ax):
    """An end station's line pill on its own row, under or over the name, lined up with the name's outer end."""
    for s in RP.STATIONS:
        if s["name"] not in STACKED:
            continue
        key, where = STACKED[s["name"]]
        xs, ys = [q[0] for _, q in s["dots"]], [q[1] for _, q in s["dots"]]
        y = sum(ys) / len(ys) + (3.7 if where == "above" else -3.7)
        side = RP.SIDE_FIX.get(s["name"], s["side"])
        if side == "r":
            RP.line_pill(ax, max(xs) + 2.6, y, key, 1)
        else:
            RP.line_pill(ax, min(xs) - 2.6, y, key, -1)


# ---------------------------------------------------------------------------------------------------------------
def header(ax, x0, y1, x1):
    """The T and NERTA mark, the CR pill and the title, as on the rail poster; the release block on the right."""
    hy = y1 - 11
    RP.nerta_roundel(ax, x0 + 10, hy, 6.4)  # the multicolor T and NERTA pill, as on every map (November 8)
    draw_nerta(ax, x0 + 10, hy - (6.4 + 3.2 / 5.4 / 2) - 0.8, 2 * (6.4 + 3.2 / 5.4 / 2), "B", colors=M.NERTA_COLORS)
    ax.add_patch(FancyBboxPatch((x0 + 20, hy - 6), 28, 12, boxstyle="round,pad=0,rounding_size=6", fc=PURPLE, ec="none", zorder=12))
    for k, col in ((0.9, GOLD), (1.9, PURPLE)):
        ax.add_patch(FancyBboxPatch((x0 + 20 + k, hy - 6 + k), 28 - 2 * k, 12 - 2 * k, boxstyle=f"round,pad=0,rounding_size={6 - k}",
                                    fc=col, ec="none", zorder=12.1 + k / 10))
    ax.text(x0 + 34, hy - 0.4, "CR", fontsize=34, fontweight="bold", color=WHITE, ha="center", va="center", zorder=13)
    ax.text(x0 + 52, hy, "Commuter Rail" + chr(10) + "Network", fontsize=27, fontweight="bold", color=INK, ha="left", va="center",
            linespacing=1.1, zorder=13)
    # the release block, or on nerta.fun (NERTA_WEB=1) the name under NERTA and @mapzimus, as the rail poster does
    return RP.web_or_release(ax, x0, x1, hy, x0 + 52 + RP.width("Commuter Rail", 27, "bold"))


def next_version():
    return RP.next_version("rail_network")   # --out DIR (the nerta.fun web renders) or output/copies


def drawing_bounds(fig, ax):
    fig.canvas.draw()
    rend, inv = fig.canvas.get_renderer(), ax.transData.inverted()
    bx = [g.bounds for _, g in RP.REG["line"] + RP.REG["dot"]] + [g.bounds for g in RP.REG["pill"]]
    for t, _ in RP.TEXTS:
        bb = t.get_window_extent(rend)
        (a, b), (c, d) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        bx.append((a, b, c, d))
    return min(b[0] for b in bx), min(b[1] for b in bx), max(b[2] for b in bx), max(b[3] for b in bx)


def main():
    v = next_version()
    png, pdf = RP.out_dir() / f"rail_network_v{v}.png", RP.out_dir() / f"rail_network_v{v}.pdf"
    draft = "--draft" in sys.argv
    if draft:  # trial renders go to a scratch folder, never into output/
        d = Path(sys.argv[sys.argv.index("--draft") + 1])
        png, pdf = d / "network_draft.png", d / "network_draft.pdf"
    for f in (png, pdf):
        if f.exists() and not draft:
            raise SystemExit(f"refusing to overwrite {f}")
    build()
    stations()
    codes = RP.t_codes()

    X0, X1, Y0, Y1 = -260, 260, -420, 160   # working sheet; trimmed to the drawing below
    fig = plt.figure(figsize=((X1 - X0) * K, (Y1 - Y0) * K))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.patch.set_facecolor(PAPER)

    for key_, pts in RP.PATHS.items():
        if key_ not in [a[0] for a in RP.ARROWS if a[1] is RP.PATHS.get(a[0])]:
            RP.draw_line(ax, key_, pts)
    for key_, pts in RP.BRANCHES:
        RP.draw_line(ax, key_, pts)
    for key_, pts, rows, where in RP.ARROWS:
        if pts is RP.PATHS.get(key_):
            RP.draw_line(ax, key_, pts)
        RP.draw_arrow(ax, key_, pts, rows, where)
    RP.crossing(ax)
    used = []
    for s in RP.STATIONS:
        c = codes.get(s["name"], [])
        used += [(x, s["name"]) for x in c]
        RP.draw_station(ax, s, c)
    stacked_pills(ax)
    RP.dig_note(ax)
    nx0, ny0, nx1, ny1 = drawing_bounds(fig, ax)
    print(f"network {nx0:.0f}..{nx1:.0f} x {ny0:.0f}..{ny1:.0f} units ({(nx1 - nx0) * K:.1f} x {(ny1 - ny0) * K:.1f} in)")

    if PN is not None:
        place_panels(ax, used, (nx0, ny0, nx1, ny1))

    X0, Y0, X1, Y1 = drawing_bounds(fig, ax)
    X0, Y0, X1, Y1 = X0 - 7, Y0 - 10, X1 + 7, Y1 + 25
    fig.set_size_inches((X1 - X0) * K, (Y1 - Y0) * K)
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    header(ax, X0, Y1, X1)
    ax.text(X1 - 5, Y0 + 4, "Layout schematic, not to scale." if (M.WEB or RP.NO_DISCLAIMER) else "Layout schematic, not to scale. Not affiliated with the MBTA.",
            fontsize=7.6, color=INK, ha="right", va="bottom", zorder=13)   # nerta.fun never says MBTA
    print(f"sheet {(X1 - X0) * K:.1f} x {(Y1 - Y0) * K:.1f} in")

    bad = RP.check(fig, ax)
    for b in bad:
        print("  ", b)
    print(f"{len(bad)} flags")
    png.parent.mkdir(parents=True, exist_ok=True)
    dpi = int(sys.argv[sys.argv.index("--dpi") + 1]) if draft and "--dpi" in sys.argv else (150 if draft else 600)
    fig.savefig(png, dpi=dpi, facecolor=PAPER)
    if not draft:
        fig.savefig(pdf, facecolor=PAPER)
    print("written", png)


def place_panels(ax, used, net):
    """The boxes riders read, set like the Ferry Network display. Transfers sits in the open ground east of the trunk, beside
    Boston Central and South Station; the rest form a band under the network: Lines on the left, then How the trains run
    over the Key and the Passenger Notice."""
    nx0, ny0, nx1, _ny1 = net
    gap = 6.0
    # Transfers: east of the trunk, under Marblehead and clear of the Greenbush column's names
    tb = PN.transfers_panel(ax, 128.0, -13.0, used)
    if tb[2] > nx1 + 1:
        print(f"  Transfers box runs past the network's right edge: {[round(v) for v in tb]}")
    top = ny0 - 10.0
    lw = 128.0
    lb = PN.lines_panel(ax, nx0, top, lw)
    hx0 = lb[2] + gap
    hb = PN.how_panel(ax, hx0, top, nx1 - hx0)
    kw = 86.0
    kb = PN.key_panel(ax, hx0, hb[1] - gap, kw)
    nb = PN.notice_panel(ax, kb[2] + gap, hb[1] - gap, nx1 - kb[2] - gap)
    print(f"  boxes: lines {lb[3] - lb[1]:.0f} tall, how {hb[3] - hb[1]:.0f}, key {kb[3] - kb[1]:.0f}, notice {nb[3] - nb[1]:.0f}, "
          f"transfers {tb[2] - tb[0]:.0f} x {tb[3] - tb[1]:.0f}")


if __name__ == "__main__":
    main()
