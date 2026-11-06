"""Day 8 regional map: T commuter rail extended across southern New England, in the wall-poster look.

python days/08-utopia/src/make_regional.py
Stations start at their real positions and snap to a grid, so lines run at 45-degree steps. The real coast is bent the
same way. Routes come from PROPOSAL.md. Stop lists on the new lines are judgment. Fan map, no official logo.
"""
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Polygon
from scipy.interpolate import RBFInterpolator
from shapely.geometry import LineString, Point, Polygon as ShapelyPolygon, box
from shapely.ops import unary_union
from station_kit import INK, WHITE, bullet, label, rounded, stop, stroke, transfer

DAY = Path(__file__).resolve().parents[1]
REPO = DAY.parent
CRS = 26919
PURPLE, GRAY, RED = "#80276c", "#6b7075", "#da291c"
PAPER, WATER, COAST = "#fcfcfa", "#c9e3ee", "#7fb2c6"
SUB = {"Indigo": "#3f3fb5", "Red": "#da291c", "Orange": "#ed8b00", "Blue": "#003da5", "Green": "#00843d"}
LW = 5.6
UNIT = 1620.0   # meters per diagram unit
SNAP = 4
ORIGIN = (-73.72, 40.92)
XLIM, YLIM = (-12, 226), (-2, 212)
FIPS = {"09": "CT", "23": "ME", "25": "MA", "33": "NH", "44": "RI", "50": "VT"}

# Each stop is "Town ST" or "@MBTA stop". status: solid = T today, other = another operator today, stripe = real proposal, dash = imagined.
LINES = [
    ("solid", ["Boston", "@Anderson/Woburn", "@Lowell"]),
    ("solid", ["@Anderson/Woburn", "@Wilmington", "@Lawrence", "@Haverhill"]),
    ("solid", ["Boston", "@Lynn Interim", "South Salem MA", "@Salem", "@Beverly", "@Ipswich", "@Newburyport"]),
    ("solid", ["@Beverly", "@Gloucester", "@Rockport"]),
    ("solid", ["Boston", "@Waltham", "@Littleton/Route 495", "@Fitchburg", "@Wachusett"]),
    ("solid", ["Boston", "@Framingham", "@Worcester"]),
    ("solid", ["Boston", "@Walpole", "@Franklin", "@Forge Park/495"]),
    ("solid", ["@Walpole", "@Foxboro"]),
    ("solid", ["Boston", "@Route 128", "@Canton Junction", "@Mansfield", "@Attleboro", "@Providence", "@TF Green Airport", "@Wickford Junction"]),
    ("solid", ["@Canton Junction", "@Stoughton"]),
    ("solid", ["Boston", "@Quincy Center", "@Braintree", "@Brockton", "@Middleborough"]),
    ("solid", ["@Braintree", "@Kingston"]),
    ("solid", ["@Braintree", "@Greenbush"]),
    ("solid", ["@Middleborough", "@East Taunton", "@Fall River Depot"]),
    ("solid", ["@East Taunton", "@New Bedford"]),
    ("stripe", ["@Wickford Junction", "Westerly RI", "New London CT"]),
    ("other", ["New London CT", "Old Saybrook CT", "New Haven CT", "Bridgeport CT", "Stamford CT", "Greenwich CT"]),
    ("other", ["Bridgeport CT", "Waterbury CT"]),
    ("other", ["Norwalk CT", "Danbury CT"]),
    ("stripe", ["@Lowell", "Nashua NH", "Manchester Airport NH", "Manchester NH"]),
    ("dash", ["Manchester NH", "Concord NH"]),
    ("stripe", ["@Worcester", "Palmer MA", "Springfield MA"]),
    ("dash", ["@Newburyport", "Hampton NH", "Portsmouth NH"]),
    ("stripe", ["@Forge Park/495", "Milford MA"]),
    ("stripe", ["@Haverhill", "Plaistow NH"]),
    ("other", ["Plaistow NH", "Exeter NH", "Durham NH", "Dover NH", "Wells ME", "Saco ME", "Portland ME", "Brunswick ME"]),
    ("stripe", ["Dover NH", "Rochester NH"]),
    ("dash", ["Portsmouth NH", "Dover NH"]),
    ("dash", ["@Wachusett", "Gardner MA", "Athol MA", "Greenfield MA", "North Adams MA"]),
    ("stripe", ["@Middleborough", "Wareham MA", "Bourne MA"]),
    ("stripe", ["Bourne MA", "Barnstable MA"]),
    ("stripe", ["@Kingston", "Plymouth MA"]),
    ("dash", ["South Salem MA", "Peabody MA", "Danvers MA", "Middleton MA", "@Lawrence"]),
    ("other", ["New Haven CT", "Meriden CT", "Hartford CT", "Windsor Locks CT", "Springfield MA"]),
    ("other", ["Springfield MA", "Holyoke MA", "Northampton MA", "Greenfield MA", "Brattleboro VT"]),
    ("stripe", ["Springfield MA", "Westfield MA", "Pittsfield MA"]),
    ("dash", ["Danbury CT", "New Milford CT", "Pittsfield MA"]),
    ("stripe", ["@Providence", "Pawtucket RI", "Woonsocket RI", "@Worcester"]),
    ("dash", ["New London CT", "Norwich CT", "Putnam CT", "@Worcester"]),
    ("dash", ["Hartford CT", "Windham CT", "@Providence"]),
    ("dash", ["Windsor Locks CT", "Bradley CT"]),
    ("dash", ["Waterbury CT", "Torrington CT"]),
    ("dash", ["Peabody MA", "@Anderson/Woburn", "@Waltham", "@Route 128", "@Braintree"]),
    ("dash", ["@Providence", "Bristol RI", "Newport RI"]),
    ("dash", ["Bourne MA", "Falmouth MA"]),
    ("dash", ["Barnstable MA", "Orleans MA", "Wellfleet MA", "Truro MA", "Provincetown MA"]),
]
OFF = [("to New York", "Greenwich CT", (-.4, -.4)), ("to Albany", "Pittsfield MA", (-1, 0)), ("to Montréal", "Brattleboro VT", (0, 1)), ("to Concord", "Manchester NH", (0, 0))]
NAME = {"Manchester Airport NH": "Manchester Airport", "@TF Green Airport": "T.F. Green Airport", "South Salem MA": "South Salem", "Bradley CT": "Bradley Airport", "Windham CT": "Willimantic", "Falmouth MA": "Woods Hole", "Barnstable MA": "Hyannis", "@Fall River Depot": "Fall River", "@Forge Park/495": "Forge Park", "@Littleton/Route 495": "Littleton", "@Lynn Interim": "Lynn",
        "@Anderson/Woburn": "Woburn", "@Route 128": "Route 128", "@Wickford Junction": "Wickford Jct"}
BIG = {"Providence", "Worcester", "Springfield", "Hartford", "New Haven", "Portland", "Manchester", "Bridgeport"}
FIX = {"Manchester Airport NH": (-71.436, 42.933), "South Salem MA": (-70.893, 42.508), "Bradley CT": (-72.683, 41.939), "Boston": (-71.0576, 42.3590), "Plymouth MA": (-70.6915, 41.9812)}
# Hand placement after snapping: spreads stops that landed on each other, keeps them near the true spot.
AT = {"@Anderson/Woburn": (130, 112), "South Salem MA": (157, 109), "@Wilmington": (136, 120), "@Lawrence": (140, 130), "@Quincy Center": (144, 84), "@Braintree": (148, 76), "@Route 128": (134, 80), "@Canton Junction": (132, 72), "@Haverhill": (144, 138), "@Lynn Interim": (154, 106), "@Salem": (160, 112),
      "@Beverly": (164, 116), "@Ipswich": (164, 128), "@Newburyport": (160, 140), "@Gloucester": (174, 118), "@Rockport": (180, 124), "Peabody MA": (150, 112),
      "Danvers MA": (150, 120), "Middleton MA": (146, 124), "@Fitchburg": (94, 116), "@Wachusett": (86, 116), "Gardner MA": (78, 116), "Athol MA": (68, 116), "Greenfield MA": (56, 116),
      "North Adams MA": (32, 120), "@Littleton/Route 495": (106, 112), "@Framingham": (108, 88), "@Forge Park/495": (108, 66), "@Franklin": (114, 66), "Milford MA": (102, 74),
      "@Stoughton": (137, 66), "@Mansfield": (128, 60), "@Attleboro": (124, 54), "Pawtucket RI": (110, 50), "Woonsocket RI": (104, 58),
      "@Brockton": (144, 62), "@Middleborough": (148, 46), "@East Taunton": (140, 46), "Wareham MA": (160, 40), "Bourne MA": (168, 40), "Barnstable MA": (184, 36),
      "@Kingston": (164, 56), "Plymouth MA": (172, 52), "New London CT": (84, 22), "Old Saybrook CT": (68, 25), "New Haven CT": (40, 27), "Norwalk CT": (18, 14), "Stamford CT": (10, 12), "Greenwich CT": (4, 8),
      "Meriden CT": (46, 40), "Windsor Locks CT": (54, 64), "Holyoke MA": (56, 84), "Northampton MA": (56, 94), "Springfield MA": (56, 76), "Brattleboro VT": (60, 134),
      "Westfield MA": (46, 80), "Palmer MA": (72, 84), "Waterbury CT": (34, 38), "Plaistow NH": (144, 146), "Manchester Airport NH": (112, 141), "@TF Green Airport": (114, 38), "Bradley CT": (44, 68), "Windham CT": (76, 40), "Exeter NH": (148, 152), "Durham NH": (152, 158), "Dover NH": (156, 162),
      "Hampton NH": (160, 148), "Portsmouth NH": (164, 156), "Wells ME": (168, 170), "Saco ME": (176, 178), "Rochester NH": (148, 170)}
NUDGE = {"South Salem MA": (0, -1.5), "Willimantic": (0, 0), "Windham CT": (-2, -1), "@Lynn Interim": (2, -1.5), "@Route 128": (0, -1), "Providence": (-2, 1), "Westerly RI": (-4, 0.5), "Old Saybrook CT": (0, -1), "New London CT": (-1, 1), "Stamford CT": (-2, 1),
         "Norwalk CT": (0, 1.4), "Milford MA": (-2, 0.6), "Dover NH": (1.2, 1), "Barnstable MA": (2, 2), "Holyoke MA": (0, 1.6), "Westfield MA": (-2, -1)}
SIDE = {"@Route 128": "b", "Manchester Airport NH": "l", "@TF Green Airport": "l", "South Salem MA": "br", "Bradley CT": "l", "Newport RI": "b", "Bristol RI": "l", "Falmouth MA": "b", "Orleans MA": "r", "Wellfleet MA": "r", "Truro MA": "r",  "Provincetown MA": "t", "Norwich CT": "r", "Putnam CT": "r", "Windham CT": "b", "Torrington CT": "r", "@Lawrence": "r", "@Anderson/Woburn": "tl", "@Lowell": "r", "@Waltham": "l", "@Fitchburg": "t", "@Wachusett": "b", "Gardner MA": "t", "Athol MA": "b", "North Adams MA": "t",
        "Greenfield MA": "tl", "@Littleton/Route 495": "tr", "@Framingham": "b", "@Forge Park/495": "br", "@Franklin": "t", "Milford MA": "l", "@Walpole": "r", "@Foxboro": "b",
        "Woonsocket RI": "l", "Pawtucket RI": "tr", "@Stoughton": "b", "@Mansfield": "r", "@Attleboro": "r", "@Middleborough": "tr", "@East Taunton": "tl", "@Fall River Depot": "r",
        "Wareham MA": "b", "Bourne MA": "t", "Barnstable MA": "t", "@Kingston": "l", "New London CT": "t", "Old Saybrook CT": "b", "Westerly RI": "t", "Stamford CT": "t", "Norwalk CT": "t",
        "Greenwich CT": "r", "Danbury CT": "r", "Meriden CT": "r", "Waterbury CT": "l", "Windsor Locks CT": "r", "Holyoke MA": "r", "Northampton MA": "r", "Westfield MA": "b", "Palmer MA": "b",
        "Pittsfield MA": "r", "@Lynn Interim": "br", "@Salem": "br", "@Beverly": "br", "Peabody MA": "tr", "Danvers MA": "r", "Middleton MA": "r", "@Wilmington": "r", "@Canton Junction": "r", "@Braintree": "tr", "Plaistow NH": "l", "Exeter NH": "l", "Durham NH": "l",
        "Dover NH": "tr", "Hampton NH": "r", "Portsmouth NH": "r", "Wells ME": "br", "Saco ME": "br", "Rochester NH": "l", "@Greenbush": "r", "@Quincy Center": "r",
        "Providence": "tl", "Worcester": "t", "Springfield": "br", "Hartford": "l", "New Haven": "br", "Bridgeport": "bl", "Manchester": "r", "Portland": "tl", "@Providence": "tl",
        "@Worcester": "tl", "Manchester NH": "r", "Portland ME": "tl", "Springfield MA": "br", "Hartford CT": "l", "New Haven CT": "tr", "Bridgeport CT": "bl"}
TAGS = [("Shore Line", (92, 14)), ("New Haven Line", (24, 3)), ("Valley Line", (66, 100)), ("Inland Route", (66, 90)), ("Berkshire Line", (34, 95)), ("Housatonic Line", (5, 70)),
        ("Northern Tier", (72, 122)), ("Blackstone Line", (92, 66)), ("Capitol Line", (100, 148)), ("Route 128 ring", (124, 118)), ("Downeast", (172, 164)), ("Seacoast", (176, 150)), ("Cape Line", (186, 44))]
# The T's subway reaching out from Boston, offset beside the commuter lines. (color, style, path). Fantasy lines dashed.
HUB = (140, 92)
METRO = [
    ("Red", "solid", [HUB, (132, 100)]), ("Red", "stripe", [(132, 100), (128, 104)]), ("Red", "dash", [(128, 104), (122, 110)]),
    ("Red", "dash", [(132, 100), (125, 100), (120, 95)]), ("Red", "solid", [HUB, (140, 84), (148, 76)]),
    ("Orange", "solid", [HUB, (144, 96), (144, 106)]), ("Orange", "dash", [(144, 106), (144, 114)]),
    ("Orange", "dash", [(144, 100), (146, 102), (146, 108)]),
    ("Orange", "solid", [HUB, (132, 84)]), ("Orange", "stripe", [(132, 84), (126, 84)]), ("Orange", "dash", [(126, 84), (121, 84)]),
    ("Blue", "solid", [HUB, (144, 92), (151, 99)]), ("Blue", "stripe", [(151, 99), (156, 104)]),
    ("Green", "solid", [HUB, (138, 94), (138, 102)]), ("Green", "stripe", [(138, 102), (138, 107)]),
    ("Green", "solid", [HUB, (138, 90), (123, 90)]),
    ("Indigo", "stripe", [HUB, (134, 86), (127, 79)]),
]
FERRY = [([(184, 36), (190, 26), (198, 19)], "Nantucket", (200, 13)), ([(168, 28), (165, 22)], "Martha's Vineyard", (166, 14)), ([(147, 81), (170, 79), (194, 66)], "Provincetown ferry", (183, 74.5))]
METRO_ENDS = [("Lexington", (122, 110), "Red", "l"), ("Reading", (144, 114), "Orange", "l"), ("Saugus", (146, 108), "Orange", "r"), ("Dedham", (121, 84), "Orange", "l"), ("Readville", (127, 79), "Indigo", "t"), ("Riverside", (123, 90), "Green", "b"),
              ("Mystic Valley", (138, 107), "Green", "t")]


def locate():
    towns = gpd.read_file(REPO / "data/shared/ne_towns.gpkg").to_crs(CRS)
    towns["key"] = towns.NAME.str.replace(r" Town$", "", regex=True) + " " + towns.STATEFP.map(FIPS)
    stops = gpd.read_file(DAY / "data/mbta_stops.gpkg").to_crs(CRS).drop_duplicates("name").set_index("name").geometry
    ext = gpd.read_file(DAY / "data/ext_stations.gpkg").to_crs(CRS)
    o = gpd.GeoSeries([Point(*ORIGIN)], crs=4326).to_crs(CRS).iloc[0]

    def real(s):
        if s in FIX:
            return gpd.GeoSeries([Point(*FIX[s])], crs=4326).to_crs(CRS).iloc[0]
        if s[0] == "@":
            return stops[s[1:]]
        hit = towns[towns.key == s]
        if len(hit) == 0:
            raise SystemExit(f"no town {s}")
        return hit.assign(a=hit.area).nlargest(1, "a").geometry.iloc[0].representative_point()

    hub = real("Boston")
    R, G = {}, {}
    for _, seq in LINES:
        for s in seq:
            if s not in R:
                p = real(s)
                R[s] = (p.x, p.y)
                # Fisheye: greater Boston gets more room, far stations stay near their true spots.
                bx, by = hub.x, hub.y
                r = np.hypot(p.x - bx, p.y - by)
                k = 1 + 1.7 * np.exp(-r / 42000)
                gx, gy = bx + (p.x - bx) * k, by + (p.y - by) * k
                G[s] = (round((gx - o.x) / UNIT / SNAP) * SNAP, round((gy - o.y) / UNIT / SNAP) * SNAP)
    G.update(AT)
    seen = {}
    for s, q in G.items():
        if q in seen:
            raise SystemExit(f"{s} and {seen[q]} share {q}")
        seen[q] = s
    return R, G


WAY = {("@Anderson/Woburn", "@Waltham"): [(124, 112), (116, 104), (116, 98)], ("@Waltham", "@Route 128"): [(114, 94), (114, 84), (124, 74), (130, 74)], ("New Milford CT", "Pittsfield MA"): [(28, 56)], ("Boston", "@Lynn Interim"): [(141, 96), (151, 106)], ("South Salem MA", "Peabody MA"): [(153, 112)], ("Portland ME", "Brunswick ME"): [(188, 196), (192, 200)], ("@Kingston", "Plymouth MA"): [(166, 56), (170, 56)]}


def leg(G, a, b):
    return [G[a]] + WAY[(a, b)] + [G[b]] if (a, b) in WAY else oct_path(G[a], G[b])


def oct_path(a, b):
    """One bend: long straight run first, then the 45-degree part into the stop."""
    a, b = np.array(a, float), np.array(b, float)
    dx, dy = b - a
    d = min(abs(dx), abs(dy))
    mid = (b[0] - np.sign(dx) * d, b[1] - np.sign(dy) * d) if abs(dx) != abs(dy) and d > 0 else None
    return [tuple(a), mid, tuple(b)] if mid else [tuple(a), tuple(b)]


def water(ax, R, G):
    keys = list(R)
    shore = {(-73.78, 42.65): (0, 106), (-73.95, 41.7): (-5, 46), (-73.95, 41.0): (-8, 4), (-70.985, 42.42): (157, 98), (-70.94, 42.44): (163, 103), (-70.97, 42.375): (156, 91),
             (-70.99, 42.36): (150, 86), (-70.96, 42.35): (158, 86)}
    pts = gpd.GeoSeries([Point(k) for k in shore], crs=4326).to_crs(CRS)
    A0 = np.array([R[k] for k in keys] + [(q.x, q.y) for q in pts])
    B0 = np.array([G[k] for k in keys] + list(shore.values()))
    warp = RBFInterpolator(A0, B0, kernel="thin_plate_spline", smoothing=40)
    towns = gpd.read_file(REPO / "data/shared/ne_towns.gpkg").to_crs(4326)
    world = gpd.read_file(DAY / "data/raw/ne/ne_10m_land.geojson").to_crs(4326)
    frame = box(-75.2, 39.8, -68.2, 45.0)
    ne = towns.geometry.union_all().buffer(0)
    land = unary_union([ne, gpd.clip(world, frame).geometry.union_all().difference(ne.buffer(0.05))]).buffer(0)
    sea = gpd.GeoSeries([frame.difference(land)], crs=4326).to_crs(CRS).simplify(120).iloc[0]
    bent = []
    for poly in getattr(sea, "geoms", [sea]):
        if poly.area < 4e6:
            continue
        d = poly.segmentize(2500)
        holes = [warp(np.array(r.coords)[:, :2]) for r in d.interiors if ShapelyPolygon(r).area > 3e6]
        bent.append(ShapelyPolygon(warp(np.array(d.exterior.coords)[:, :2]), holes).buffer(0))
    soft = unary_union(bent).buffer(0.4).buffer(-0.8).buffer(0.4)
    global SEA
    SEA = soft
    for g in getattr(soft, "geoms", [soft]):
        ax.add_patch(Polygon(np.array(g.exterior.coords), fc=WATER, ec=COAST, lw=1.0, zorder=1))
        for r in g.interiors:
            ax.add_patch(Polygon(np.array(r.coords), fc=PAPER, ec=COAST, lw=1.0, zorder=1.1))
    rivers = gpd.read_file(REPO / "data/shared/ne_flowlines_order3plus.gpkg", bbox=(-73.0, 41.2, -70.7, 43.3))
    for n, w in (("Connecticut River", 3.2), ("Merrimack River", 2.6), ("Thames River", 2.4), ("Blackstone River", 1.6), ("Taunton River", 1.6)):
        for g in rivers[rivers.gnis_name == n].to_crs(CRS).geometry:
            for part in getattr(g, "geoms", [g]):
                ax.plot(*warp(np.array(part.segmentize(800).coords)[:, :2]).T, color=WATER, lw=w, zorder=0.9, solid_capstyle="round")


def main():
    R, G = locate()
    w = 18.0
    fig = plt.figure(figsize=(w, w * (YLIM[1] - YLIM[0]) / (XLIM[1] - XLIM[0])), facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_facecolor(PAPER)
    ax.set_axis_off()
    water(ax, R, G)
    for status, seq in LINES:
        for a, b in zip(seq, seq[1:]):
            xy = rounded(leg(G, a, b), 3)
            stroke(ax, xy, GRAY if status == "other" else PURPLE, LW, "solid" if status == "other" else status, z=5 if status == "solid" else 4)
    for col, st, path in METRO:
        stroke(ax, rounded(path, 2), SUB[col], 4.2, st, z=6)
    ring = np.array([(HUB[0] + 9 * np.cos(t), HUB[1] + 9 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 80)])
    stroke(ax, ring, "#f5c400", 4.2, "dash", z=5.8)
    for path, name, xy in FERRY:
        ax.plot(*np.array(path).T, color="#2b7a9b", lw=1.6, ls=(0, (1, 1.4)), zorder=2.5)
        ax.text(*xy, name, fontsize=7.4, fontweight="bold", color="#2b7a9b", ha="center", zorder=3)
    for n, q, col, side in METRO_ENDS:
        stop(ax, q, 4.2, True, edge=SUB[col], z=8)
        label(ax, q, n, side, gap=2.0, fs=8.6, weight="bold", color=SUB[col])
    transfer(ax, (156, 104), (154, 106), lw=4.6)
    # Report any track or stop over open water.
    for status, seq in LINES:
        for a, b in zip(seq, seq[1:]):
            wet = LineString(rounded(leg(G, a, b), 3)).intersection(SEA).length
            if wet > 0.3:
                print(f"TRACK IN WATER {wet:.1f} units: {a} to {b}", G[a], G[b])
    for k, q in G.items():
        if SEA.contains(Point(q)):
            print("STOP IN WATER:", k, q)
    # High-speed rail: Boston Central to New York on the Shore Line
    hsr = ["Boston", "@Route 128", "@Canton Junction", "@Mansfield", "@Attleboro", "@Providence", "@TF Green Airport", "@Wickford Junction", "Westerly RI", "New London CT", "Old Saybrook CT", "New Haven CT", "Bridgeport CT", "Norwalk CT", "Stamford CT", "Greenwich CT"]
    for a, b in zip(hsr, hsr[1:]):
        ax.plot(*rounded(oct_path(G[a], G[b]), 3).T, color="#ffd23f", lw=1.6, zorder=6.5)
    for name, frm, (dx, dy) in OFF:
        if dx == 0 and dy == 0:
            continue
        p = G[frm]
        q = (p[0] + dx * 12, p[1] + dy * 12)
        ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>,head_width=0.5,head_length=0.9", color=PURPLE, lw=3), zorder=4)
        label(ax, q, name, "t" if dy > 0 else "b", gap=1.5, fs=8.5, weight="bold", color=PURPLE)
    for s, p in G.items():
        n = NAME.get(s, s[1:] if s[0] == "@" else s[:-3])
        if s == "Boston":
            continue
        big = n in BIG
        if big:
            transfer(ax, p, lw=LW * 1.5)
            label(ax, (p[0] + NUDGE.get(n, (0, 0))[0], p[1] + NUDGE.get(n, (0, 0))[1]), n, SIDE.get(s, "tr"), fs=13.5, weight="bold", gap=3.4)
        else:
            stop(ax, p, LW, z=8)
            label(ax, (p[0] + NUDGE.get(s, (0, 0))[0], p[1] + NUDGE.get(s, (0, 0))[1]), n, SIDE.get(s, "r"), fs=9.4, gap=2.4)
    b = G["Boston"]
    transfer(ax, b, lw=LW * 3.2)
    ax.scatter(*b, s=(LW * 1.5) ** 2, color=RED, zorder=11)
    label(ax, (b[0] + 16, b[1] - 2), "BOSTON\nCENTRAL", "r", gap=1, fs=15, weight="bold")
    ax.text(b[0] + 17, b[1] - 10, "The BIGGER Dig", fontsize=12, fontweight="bold", color=RED, va="center", zorder=12)
    for t, xy in TAGS:
        bullet(ax, *xy, t, PURPLE, h=3.3, fs=7.6) if False else ax.text(*xy, t, fontsize=8, fontweight="bold", color=WHITE, ha="center", va="center", zorder=12,
                                                                        bbox=dict(boxstyle="round,pad=0.32,rounding_size=0.7", fc=PURPLE, ec="none"))
    ax.text(-9, 209.8, "Commuter Rail &", fontsize=40, fontweight="bold", color=INK, va="top", zorder=12)
    ax.text(-9, 199.2, "New England", fontsize=40, fontweight="bold", color=INK, va="top", zorder=12)
    ax.plot([-9, 66], [187.2, 187.2], color=INK, lw=2.4, zorder=12, solid_capstyle="butt")
    ax.text(-9, 185.6, "What if the MBTA covered New England? The region.", fontsize=11, color=INK, va="top", zorder=12)
    lx, ly = 186, 158
    ax.add_patch(FancyBboxPatch((lx - 4, ly - 28), 42, 42, boxstyle="round,pad=0,rounding_size=1.4", fc=WHITE, ec=INK, lw=1.2, zorder=11))
    ax.text(lx, ly + 7, "Key", fontsize=11.5, fontweight="bold", color=INK, zorder=12)
    for i, (st, c, t) in enumerate((("solid", PURPLE, "T commuter rail today"), ("solid", GRAY, "Other trains today, joined to the T"), ("stripe", PURPLE, "New: real proposal or strong case"),
                                    ("dash", PURPLE, "New: imagined"), ("dash", SUB["Red"], "Subway, same styles. Yellow is the ring"), ("hsr", PURPLE, "High-speed rail to New York"))):
        y = ly + 2 - i * 5.4
        stroke(ax, [(lx, y), (lx + 7, y)], c, LW, "solid" if st == "hsr" else st, z=12)
        if st == "hsr":
            ax.plot([lx, lx + 7], [y, y], color="#ffd23f", lw=1.6, zorder=12.2)
        ax.text(lx + 9, y, t, fontsize=8.4, va="center", color=INK, zorder=12)
    ax.text(225, -0.8, "Fan map, not an official MBTA map · Layout schematic, not to scale · New stops are judgment calls · Data: MBTA V3 API; US Census TIGER/Line; Natural Earth; EPA NHDPlus · Map: Maxwell Howe · #30DayMapChallenge Day 8",
            fontsize=6.4, color="#37505c", ha="right", zorder=12)
    (DAY / "output").mkdir(exist_ok=True)
    fig.savefig(DAY / "output/regional_map.png", dpi=200, facecolor=PAPER)
    fig.savefig(DAY / "output/regional_map.pdf", facecolor=PAPER)
    print("written")


if __name__ == "__main__":
    main()
