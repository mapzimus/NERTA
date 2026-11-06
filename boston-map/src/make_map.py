"""Day 8 main map: What if the MBTA covered all of New England.

python days/08-utopia/src/make_map.py
Needs data from fetch_mbta.py and build_extensions.py. Writes output/map.png and output/map.pdf.
No state borders. Coordinates marked approx are placed by hand for the fantasy lines.
"""
from pathlib import Path
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
from shapely.geometry import LineString, Point, box

DAY = Path(__file__).resolve().parents[1]
REPO = DAY.parent
CRS = 26919
W, H = 12.0, 10.0  # inches; 3600 x 3000 at 300 dpi
VIEW = gpd.GeoSeries([Point(-73.56, 40.72), Point(-65.1, 46.0)], crs=4326).to_crs(CRS)
BOX = (-71.27, 42.235, -70.89, 42.49)  # Boston inset, lon/lat

PAPER, LAND, WATER, INK, MUTED = "#fbfaf6", "#f1eee6", "#dce8ee", "#1d1d1b", "#5f5f5f"
T_PURPLE, OTHER, NEW = "#80276c", "#6f7378", "#e4572e"
SUBWAY = {"Red": "#da291c", "Mattapan": "#da291c", "Orange": "#ed8b00", "Blue": "#003da5", "Green-B": "#00843d",
          "Green-C": "#00843d", "Green-D": "#00843d", "Green-E": "#00843d"}
YELLOW, SILVER, DIG = "#f2c200", "#7c878e", "#111111"
plt.rcParams.update({"font.family": "Arial", "pdf.fonttype": 42, "svg.fonttype": "none"})

HUBS = ["Providence", "Worcester", "Springfield", "Hartford", "New Haven", "Portland", "Manchester", "Burlington", "Bangor"]
TOWNS = ["Stamford", "Bridgeport", "Danbury", "Waterbury", "New London", "Westerly", "Woonsocket", "Pittsfield",
         "Greenfield", "North Adams", "Northampton", "Brattleboro", "White River Jct", "Montpelier", "Rutland",
         "Bennington", "St. Albans", "Concord", "Nashua", "Lowell", "Dover", "Rochester", "Portsmouth", "Biddeford",
         "Brunswick", "Lewiston", "Augusta", "Waterville", "Rockland", "Hyannis", "Plymouth", "Milford", "Palmer",
         "Gardner", "Essex Jct", "Middlebury", "Lebanon", "New Milford", "Bourne"]
NUDGE = {"Providence": (-6, -3, "right"), "Portland": (-6, 2, "right"), "Hartford": (6, 1, "left"),
         "Springfield": (6, -6, "left"), "New Haven": (6, -7, "left"), "Bridgeport": (2, -8, "center"),
         "Stamford": (6, -7, "left"), "Danbury": (6, 1, "left"), "Waterbury": (-5, 2, "right"),
         "New London": (0, -9, "center"), "Westerly": (6, -7, "left"), "Worcester": (5, 3, "left"),
         "Lowell": (-5, 3, "right"), "Nashua": (-5, 0, "right"), "Dover": (5, 0, "left"), "Rochester": (-5, 2, "right"),
         "Portsmouth": (6, -1, "left"), "Woonsocket": (-5, 0, "right"), "Greenfield": (5, 4, "left"),
         "Northampton": (5, -2, "left"), "Pittsfield": (-5, 3, "right"), "North Adams": (6, 6, "left"),
         "Essex Jct": (5, 4, "left"), "Burlington": (-5, -5, "right"), "St. Albans": (5, 2, "left"),
         "Lebanon": (6, 5, "left"), "White River Jct": (-5, -6, "right"), "Palmer": (0, -9, "center"),
         "Gardner": (2, 5, "center"), "Milford": (-5, -1, "right"), "Plymouth": (6, 1, "left"), "Bourne": (0, -9, "center"),
         "Hyannis": (6, -7, "left"), "Brunswick": (-5, 3, "right"), "Rockland": (6, -1, "left"),
         "Biddeford": (6, -1, "left"), "Lewiston": (-5, 3, "right"), "New Milford": (6, 2, "left")}

# Boston box: fantasy subway. Stop names resolve to MBTA stops; (lon, lat) tuples are hand-placed, approx.
P = {"Lynn": (-70.9454, 42.4623), "West Lynn": (-70.9700, 42.4470), "Arlington Center": (-71.1565, 42.4154),
     "Arlington Heights": (-71.1835, 42.4256), "Route 16": (-71.1115, 42.4115), "Hyde Square": (-71.1065, 42.3235),
     "VFW Parkway": (-71.1745, 42.2620), "Everett Square": (-71.0545, 42.4075), "Encore": (-71.0740, 42.3948),
     "Inner Belt": (-71.0850, 42.3790), "Binney": (-71.0850, 42.3665), "Mass Ave/MIT": (-71.0940, 42.3590),
     "Cambridgeport": (-71.1065, 42.3570), "BU Bridge": (-71.1100, 42.3502), "BMC": (-71.0720, 42.3350),
     "Logan West": (-71.0200, 42.3656), "Mystic Mall": (-71.0390, 42.3925), "Melnea Cass": (-71.0780, 42.3310),
     "D Street": (-71.0450, 42.3460), "West Station": (-71.1180, 42.3560), "Barrys Corner": (-71.1250, 42.3640),
     "Boston Central": (-71.0576, 42.3590)}
SUB_NEW = [  # (color, dashed, stops)
    (SUBWAY["Blue"], False, ["Wonderland", "River Works", "West Lynn", "Lynn"]),
    (SUBWAY["Blue"], False, ["Bowdoin", "Charles/MGH"]),
    (SUBWAY["Orange"], False, ["Forest Hills", "Roslindale Village", "Bellevue", "Highland", "West Roxbury", "VFW Parkway"]),
    (SUBWAY["Red"], False, ["Alewife", "Arlington Center", "Arlington Heights"]),
    (SUBWAY["Green-B"], False, ["Medford/Tufts", "Route 16"]),
    (SUBWAY["Green-B"], False, ["Heath Street", "Hyde Square"]),
    (SUBWAY["Green-B"], True, ["Newton Highlands", "Needham Junction", "Needham Heights"]),
    (SUBWAY["Green-B"], True, ["Boylston", "Nubian"]),
    (SUBWAY["Green-B"], True, ["Boylston", "South Station", "Courthouse", "World Trade Center"]),
    (SILVER, False, ["Chelsea", "Everett Square", "Sullivan Square"]),
]
YELLOW_LINE = ["Logan West", "Airport", "Bellingham Square", "Mystic Mall", "Everett Square", "Encore", "Assembly",
               "Sullivan Square", "Inner Belt", "Lechmere", "Binney", "Kendall/MIT", "Mass Ave/MIT", "Cambridgeport",
               "BU Bridge", "Lansdowne", "Fenway", "Longwood Medical Area", "Ruggles", "Melnea Cass", "Nubian", "BMC",
               "Newmarket", "JFK/UMass", "World Trade Center", "D Street"]
YELLOW_BRANCH = ["BU Bridge", "West Station", "Barrys Corner", "Harvard"]
BOX_LABELS = {"Lynn": (0, 7), "Arlington Heights": (0, 7), "VFW Parkway": (0, -11), "Chelsea": (6, 5),
              "Everett Square": (-2, 7), "Kendall/MIT": (0, -11), "Longwood Medical Area": (-30, -11), "Nubian": (-2, -11),
              "Harvard": (-4, 7), "Airport": (8, -9), "Route 16": (-6, 7), "Sullivan Square": (2, 8), "Wonderland": (22, 2)}

# City systems: schematic stop lists. All fantasy except Providence, which has a real study.
CITIES = [
    ("Providence", "#e4572e", ["College Hill", "Kennedy Plaza", "Providence Sta.", "Downcity", "Hospitals", "Park Ave"]),
    ("Hartford", "#00843d", ["Union Station", "Parkville", "Elmwood", "Newington", "New Britain"]),
    ("Worcester", "#7b3fa0", ["Clark Univ.", "Main South", "Union Station", "Shrewsbury St", "Lake Quinsigamond"]),
    ("Portland", "#0b6e8a", ["Gorham", "Westbrook", "Rock Row", "USM", "Maine Med", "Eastern Prom"]),
    ("New Haven", "#c8102e", ["Union Station", "Yale Med", "Green", "Yale", "Whitney Ave"]),
    ("Springfield", "#b5651d", ["Union Station", "Court Sq", "Forest Park"]),
    ("Burlington", "#1f6fb2", ["Waterfront", "Church St", "UVM", "Winooski"]),
    ("Manchester", "#6d4c41", ["Airport", "Union Station", "Millyard", "Elliot"]),
    ("Bridgeport", "#00838f", ["Station", "Downtown", "East Side"]),
]


def resolve(stops):
    named = stops.drop_duplicates("name").set_index("name").geometry

    def pt(n):
        if n in P:
            return Point(gpd.GeoSeries([Point(P[n])], crs=4326).to_crs(CRS).iloc[0])
        if n in named.index:
            return named[n]
        raise SystemExit(f"no location for {n}")
    return pt


def base(ax, land, lakes, water=WATER):
    ax.set_facecolor(water)
    land.plot(ax=ax, color=LAND, lw=0, zorder=1)
    if len(lakes):
        lakes.plot(ax=ax, color=water, lw=0, zorder=2)


def casing(w, color=PAPER):
    return [pe.Stroke(linewidth=w, foreground=color), pe.Normal()]


def halo(w=1.6):
    return [pe.withStroke(linewidth=w, foreground=LAND)]


def card(fig, x, y, w, h, alpha=0.94):
    fig.add_artist(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.006", transform=fig.transFigure,
                                  fc=PAPER, ec="#cfcabd", lw=0.7, alpha=alpha, zorder=20))


def main():
    ne = gpd.read_file(REPO / "data/shared/ne_towns.gpkg").to_crs(CRS)
    world = gpd.read_file(DAY / "data/raw/ne/ne_10m_land.geojson").to_crs(4326)
    lakes = gpd.read_file(DAY / "data/raw/ne/ne_10m_lakes.geojson").to_crs(4326)
    frame4326 = box(-75.5, 39.5, -63.5, 47.0)
    world = gpd.clip(world, frame4326).to_crs(CRS)
    lakes = gpd.clip(lakes, frame4326).to_crs(CRS)
    outline = ne.geometry.union_all()
    outside = world.geometry.union_all().difference(outline.buffer(6000))  # keep the finer New England coast
    land = gpd.GeoSeries([outline.union(outside)], crs=CRS)
    land = gpd.GeoDataFrame(geometry=land)

    lines = gpd.read_file(DAY / "data/mbta_lines.gpkg").to_crs(CRS)
    stops = gpd.read_file(DAY / "data/mbta_stops.gpkg").to_crs(CRS)
    legs = gpd.read_file(DAY / "data/extensions.gpkg").to_crs(CRS)
    stn = gpd.read_file(DAY / "data/ext_stations.gpkg").to_crs(CRS)
    pt = resolve(stops)

    fig = plt.figure(figsize=(W, H), facecolor=WATER)
    ax = fig.add_axes([0, 0, 1, 1])
    base(ax, land, lakes)
    x0, y0, x1, y1 = VIEW.x[0], VIEW.y[0], VIEW.x[1], VIEW.y[1]
    x1 = x0 + (y1 - y0) * W / H
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_axis_off()

    # Off-map connections, ruled straight to each city.
    gates = {"Albany": ((-73.75, 42.65), "Pittsfield"), "Montréal": ((-73.57, 45.5), "St. Albans"),
             "New York": ((-73.99, 40.75), "Stamford")}
    for name, (ll, frm) in gates.items():
        g = gpd.GeoSeries([Point(ll)], crs=4326).to_crs(CRS).iloc[0]
        a = stn[stn.label == frm].geometry.iloc[0]
        ax.plot([a.x, g.x], [a.y, g.y], color=OTHER if name == "New York" else NEW, lw=1.5, zorder=4,
                ls=(0, (1, 1.3)), solid_capstyle="round")

    # Regional lines, newest on top.
    for st, col, lw in (("other", OTHER, 1.25), ("new", NEW, 1.8)):
        legs[legs.status == st].plot(ax=ax, color=col, lw=lw, zorder=5, capstyle="round")
    legs[legs.status == "imagined"].plot(ax=ax, color=NEW, lw=1.5, zorder=5, linestyle=(0, (3.2, 1.8)))
    lines[lines.kind == "commuter"].plot(ax=ax, color=T_PURPLE, lw=1.5, zorder=6, capstyle="round")
    for r, c in SUBWAY.items():
        g = lines[lines.route == r]
        if len(g):
            g.plot(ax=ax, color=c, lw=1.0, zorder=7)

    # Stations and labels.
    big = stn[stn.label.isin(HUBS)]
    small = stn[stn.label.isin(TOWNS)]
    small.plot(ax=ax, color=PAPER, edgecolor=INK, lw=0.6, markersize=9, zorder=9)
    big.plot(ax=ax, color=PAPER, edgecolor=INK, lw=1.0, markersize=26, zorder=9)
    for _, r in stn.iterrows():
        if r.label not in HUBS and r.label not in TOWNS:
            continue
        hub = r.label in HUBS
        dx, dy, ha = NUDGE.get(r.label, (5, 2, "left"))
        ax.annotate(r.label, (r.geometry.x, r.geometry.y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                    fontsize=8.6 if hub else 5.8, fontweight="bold" if hub else "normal", color=INK, zorder=10,
                    path_effects=halo(1.8))
    b = pt("State")
    ax.annotate("Boston", (b.x, b.y), xytext=(46, 2), textcoords="offset points", ha="left", va="center", fontsize=11, fontweight="bold",
                color=INK, zorder=12, path_effects=halo(2.2))

    # Water names and off-map labels.
    for t, lon, lat, sz in (("Atlantic Ocean", -69.75, 42.75, 11), ("Long Island Sound", -72.42, 41.08, 5.5),
                            ("Cape Cod Bay", -70.28, 41.88, 5.2), ("Lake Champlain", -73.33, 44.32, 4.8)):
        p = gpd.GeoSeries([Point(lon, lat)], crs=4326).to_crs(CRS).iloc[0]
        ax.text(p.x, p.y, t, fontsize=sz, style="italic", color="#6c8797", ha="center", zorder=3)
    def edge(text, lon, lat, ha):
        p = gpd.GeoSeries([Point(lon, lat)], crs=4326).to_crs(CRS).iloc[0]
        ax.annotate(text, (p.x, p.y), fontsize=7.2, fontweight="bold", color=INK, ha=ha, va="center", zorder=12,
                    path_effects=halo(2))
    edge("↑ to Montréal", -73.46, 45.60, "left")
    edge("← to Albany", -73.52, 42.69, "left")
    edge("← to New York", -73.49, 40.92, "left")

    # Title block.
    tx0 = 0.115
    fig.text(tx0, 0.968, "What if the MBTA covered", fontsize=24, fontweight="bold", color=INK, va="top", zorder=25)
    fig.text(tx0, 0.927, "all of New England?", fontsize=24, fontweight="bold", color=INK, va="top", zorder=25)
    new_mi = legs[legs.status == "new"].km.sum() / 1.609
    img_mi = legs[legs.status == "imagined"].km.sum() / 1.609
    fig.text(tx0 + 0.001, 0.884, f"Built out from today's T: {new_mi:,.0f} miles of real proposals, {img_mi:,.0f} miles imagined.",
             fontsize=9, color=INK, va="top", zorder=25)
    fig.text(tx0 + 0.001, 0.864, "North Station and South Station finally connect at Boston Central.", fontsize=9, color=INK, va="top", zorder=25)

    # Legend.
    lx, ly, lw_, lh = 0.632, 0.553, 0.356, 0.118
    card(fig, lx, ly, lw_, lh)
    lg = fig.add_axes([lx, ly, lw_, lh], zorder=21)
    lg.set_axis_off()
    lg.set_xlim(0, 1)
    lg.set_ylim(0, 1)
    rows = [(T_PURPLE, "-", 2.4, "Commuter rail today"), (OTHER, "-", 2.0, "Other trains running today, joined to the T"),
            (NEW, "-", 2.6, "New line: real proposal or strong case"), (NEW, (0, (3, 1.6)), 2.2, "Imagined: needs big money or new track")]
    for i, (c, ls, w, t) in enumerate(rows):
        y = 0.86 - i * 0.205
        lg.add_line(Line2D([0.03, 0.12], [y, y], color=c, ls=ls, lw=w))
        lg.text(0.145, y, t, fontsize=7.4, va="center", color=INK)
    lg.text(0.03, 0.07, "Dotted lines leave for cities just off the map. Lines follow real rail corridors.", fontsize=5.8, color=MUTED, va="center")

    # Boston box.
    bx, by, bw, bh = 0.632, 0.036, 0.356, 0.507
    card(fig, bx - 0.0, by - 0.0, bw, bh, alpha=1)
    corners = gpd.GeoSeries([Point(BOX[0], BOX[1]), Point(BOX[2], BOX[3])], crs=4326).to_crs(CRS)
    cx0, cy0, cx1, cy1 = corners.x[0], corners.y[0], corners.x[1], corners.y[1]
    ax.add_patch(Rectangle((cx0, cy0), cx1 - cx0, cy1 - cy0, fill=False, ec=INK, lw=0.8, zorder=13))
    inner = fig.add_axes([bx + 0.006, by + 0.052, bw - 0.012, bh - 0.058], zorder=22)
    land2 = gpd.GeoDataFrame(geometry=[outline], crs=CRS)
    base(inner, land2, lakes)
    aspect = (bw - 0.012) * W / ((bh - 0.058) * H)
    my = (cy0 + cy1) / 2
    hh = (cy1 - cy0) / 2
    mx = (cx0 + cx1) / 2 + (cx1 - cx0) * 0.03
    inner.set_xlim(mx - hh * aspect, mx + hh * aspect)
    inner.set_ylim(my - hh, my + hh)
    inner.set_xticks([])
    inner.set_yticks([])
    ax.set_xlabel("")
    for sp in inner.spines.values():
        sp.set_edgecolor("#cfcabd")
    lines[lines.kind == "commuter"].plot(ax=inner, color=T_PURPLE, lw=0.8, alpha=0.5, zorder=3)
    lines[lines.route.isin(SILVER_ROUTES)].plot(ax=inner, color=SILVER, lw=1.1, zorder=4)

    def drawn(names):
        return LineString([pt(n) for n in names])
    for c, dashed, seq in SUB_NEW:
        gpd.GeoSeries([drawn(seq)], crs=CRS).plot(ax=inner, color=c, lw=1.9, zorder=5, linestyle=(0, (2.6, 1.5)) if dashed else "-")
    gpd.GeoSeries([drawn(YELLOW_LINE)], crs=CRS).plot(ax=inner, color=YELLOW, lw=2.6, zorder=6, path_effects=casing(3.6, "#8a7000"), linestyle="-")
    gpd.GeoSeries([drawn(YELLOW_BRANCH)], crs=CRS).plot(ax=inner, color=YELLOW, lw=2.2, zorder=6, linestyle=(0, (2.6, 1.5)))
    for r, c in SUBWAY.items():
        g = lines[lines.route == r]
        if len(g):
            g.plot(ax=inner, color=c, lw=2.1, zorder=7)
    for names, col in ((YELLOW_LINE, "#8a7000"),):
        pts = [pt(n) for n in names]
        inner.scatter([p.x for p in pts], [p.y for p in pts], s=5, color=PAPER, edgecolor=col, lw=0.5, zorder=8)
    for n, (dx, dy) in BOX_LABELS.items():
        p = pt(n)
        inner.annotate(n.replace(" Medical Area", ""), (p.x, p.y), xytext=(dx, dy), textcoords="offset points", ha="center",
                       fontsize=5.4, color=INK, zorder=11, path_effects=halo(1.4))

    # The BIGGER Dig, marked in the box and drawn large in a downtown close-up.
    n_st, c_st, s_st = pt("North Station"), pt("Boston Central"), pt("South Station")
    dig = ([n_st.x, c_st.x, s_st.x], [n_st.y, c_st.y, s_st.y])
    inner.plot(*dig, color=DIG, lw=4.6, zorder=12, solid_capstyle="round")
    inner.scatter([c_st.x], [c_st.y], s=46, color=PAPER, edgecolor=DIG, lw=1.6, zorder=15)
    inner.set_xlabel("")
    inner.set_ylabel("")
    lens = inner.inset_axes([0.585, 0.012, 0.405, 0.43], zorder=30)
    land3 = gpd.GeoDataFrame(geometry=[outline], crs=CRS)
    base(lens, land3, lakes)
    half = 1500
    lc = (c_st.y + 40)
    asp = 0.405 * (bw - 0.012) * W / (0.43 * (bh - 0.058) * H)
    lens.set_xlim(c_st.x + 300 - half * asp, c_st.x + 300 + half * asp)
    lens.set_ylim(lc - half, lc + half)
    lens.set_xticks([])
    lens.set_yticks([])
    lens.set_xlabel("")
    lens.set_ylabel("")
    for sp in lens.spines.values():
        sp.set_edgecolor(INK)
        sp.set_linewidth(1.2)
    for r, c in SUBWAY.items():
        g = lines[lines.route == r]
        if len(g):
            g.plot(ax=lens, color=c, lw=2.2, zorder=4, alpha=0.9)
    lines[lines.route.isin(SILVER_ROUTES)].plot(ax=lens, color=SILVER, lw=1.6, zorder=3)
    lens.set_xlim(c_st.x + 300 - half * asp, c_st.x + 300 + half * asp)
    lens.set_ylim(lc - half, lc + half)
    lens.plot(*dig, color=DIG, lw=8.5, zorder=6, solid_capstyle="round")
    lens.plot(*dig, color="#ffffff", lw=2.2, ls=(0, (2.4, 2.4)), zorder=7)
    lens.scatter([n_st.x, s_st.x], [n_st.y, s_st.y], s=70, color=PAPER, edgecolor=DIG, lw=1.8, zorder=8)
    lens.scatter([c_st.x], [c_st.y], s=230, color=PAPER, edgecolor=DIG, lw=2.8, zorder=9)
    lens.scatter([c_st.x], [c_st.y], s=60, color=NEW, zorder=10)
    lens.annotate("North Station", (n_st.x, n_st.y), xytext=(9, 7), textcoords="offset points", fontsize=6.2, fontweight="bold", zorder=11, path_effects=halo(1.6))
    lens.annotate("South Station", (s_st.x, s_st.y), xytext=(9, -9), textcoords="offset points", fontsize=6.2, fontweight="bold", zorder=11, path_effects=halo(1.6))
    lens.annotate("Boston Central", (c_st.x, c_st.y), xytext=(13, 3), textcoords="offset points", fontsize=7.4, fontweight="bold", zorder=11, path_effects=halo(2))
    lens.text(0.03, 0.965, "The BIGGER Dig", transform=lens.transAxes, fontsize=10.6, fontweight="bold", color=NEW, va="top", zorder=11, path_effects=halo(2.2))
    lens.text(0.03, 0.885, "Four tracks under downtown", transform=lens.transAxes, fontsize=5.6, color=INK, va="top", zorder=11, path_effects=halo(1.4))

    fig.text(bx + 0.008, by + 0.034, "Boston: the T, extended", fontsize=9.4, fontweight="bold", color=INK, va="center", zorder=23)
    keyax = fig.add_axes([bx + 0.008, by + 0.004, bw - 0.016, 0.02], zorder=23)
    keyax.set_axis_off()
    keyax.set_xlim(0, 1)
    keyax.set_ylim(0, 1)
    keyax.add_line(Line2D([0, 0.05], [0.5, 0.5], color=YELLOW, lw=2.6, path_effects=casing(3.4, "#8a7000")))
    keyax.text(0.06, 0.5, "New Yellow Line", fontsize=5.8, va="center")
    keyax.add_line(Line2D([0.29, 0.34], [0.5, 0.5], color=SUBWAY["Blue"], lw=2))
    keyax.text(0.35, 0.5, "Extensions solid", fontsize=5.8, va="center")
    keyax.add_line(Line2D([0.57, 0.62], [0.5, 0.5], color=SUBWAY["Blue"], lw=2, ls=(0, (2.6, 1.5))))
    keyax.text(0.63, 0.5, "dashed = imagined", fontsize=5.8, va="center")

    # City systems.
    cx, cy, cw, ch = 0.632, 0.685, 0.356, 0.297
    card(fig, cx, cy, cw, ch, alpha=0.96)
    fig.text(cx + 0.008, cy + ch - 0.014, "City lines: light rail and streetcars (diagrams, not to scale)", fontsize=6.8,
             fontweight="bold", color=INK, va="center", zorder=23)
    ca = fig.add_axes([cx + 0.006, cy + 0.003, cw - 0.012, ch - 0.024], zorder=22)
    ca.set_axis_off()
    ca.set_xlim(0, 2)
    ca.set_ylim(0, 5)
    for i, (city, col, st_) in enumerate(CITIES):
        c, r = i % 2, 4 - i // 2
        ca.text(c + 0.03, r + 0.8, city, fontsize=6.6, fontweight="bold", color=col, va="center")
        xs = [c + 0.08 + (0.8 * k / (len(st_) - 1)) for k in range(len(st_))]
        ca.plot(xs, [r + 0.42] * len(xs), color=col, lw=1.8, solid_capstyle="round")
        ca.scatter(xs, [r + 0.42] * len(xs), s=6, color=PAPER, edgecolor=col, lw=0.7, zorder=3)
        for k, (x, s) in enumerate(zip(xs, st_)):
            ca.text(x, r + 0.25 if k % 2 == 0 else r + 0.06, s, fontsize=3.9, ha="center", va="center", color=INK)

    # Scale, north arrow, credit.
    sb = gpd.GeoSeries([Point(-71.1, 41.03)], crs=4326).to_crs(CRS).iloc[0]
    miles = 50 * 1609.34
    ax.plot([sb.x, sb.x + miles], [sb.y, sb.y], color=INK, lw=1.6, zorder=12)
    ax.text(sb.x + miles / 2, sb.y + 5000, "50 miles", fontsize=5.8, ha="center", color=INK, zorder=12)
    ax.annotate("N", xy=(sb.x - 9000, sb.y + 15000), xytext=(sb.x - 9000, sb.y - 3000), ha="center", fontsize=6.4, zorder=12,
                arrowprops=dict(arrowstyle="-|>", lw=0.8, color=INK))
    fig.text(0.012, 0.012, "Data: MBTA V3 API; © OpenStreetMap contributors (ODbL); Jeremy Atack, US Railroads 1826–1911 GIS; Natural Earth; US Census TIGER/Line. Plan and verdicts from public studies; see project notes.",
             fontsize=4.9, color=MUTED, zorder=25)
    fig.text(0.987, 0.012, "Fan map, not an official MBTA map · Map: Maxwell Howe · #30DayMapChallenge Day 8", fontsize=4.9, color=MUTED, ha="right", zorder=25)

    for a_ in (inner, lens):
        a_.set_xlabel("")
        a_.set_ylabel("")
    (DAY / "output").mkdir(exist_ok=True)
    fig.savefig(DAY / "output/map.png", dpi=300, facecolor=fig.get_facecolor())
    fig.savefig(DAY / "output/map.pdf", facecolor=fig.get_facecolor())
    print("written")


SILVER_ROUTES = ["741", "742", "743", "746", "749", "751"]

if __name__ == "__main__":
    main()
