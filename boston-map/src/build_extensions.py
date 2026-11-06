"""Route every line in PROPOSAL.md along real corridors.

python days/08-utopia/src/build_extensions.py
Each leg runs station to station on Atack's 1911 tracks, so curves follow true rights-of-way.
Writes data/extensions.gpkg, data/ext_stations.gpkg and output/draft_network.png.
"""
from pathlib import Path
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import LineString

DAY = Path(__file__).resolve().parents[1]
REPO = DAY.parent
CRS = 5070
SNAP_M = 40
GAP_M = 1500
FIPS = {"09": "CT", "23": "ME", "25": "MA", "33": "NH", "44": "RI", "50": "VT"}

# Status: other = runs today under another operator; new = real proposal or strong case;
# imagined = fantasy-only verdict that closes a real gap.
# A stop is a town + state, or "@Name" for an MBTA stop of that name.
LEGS = [
    ("Shore", "new", ["@Wickford Junction", "Westerly RI"]),
    ("Shore", "new", ["Westerly RI", "New London CT"]),
    ("Shore", "other", ["New London CT", "Old Saybrook CT", "New Haven CT"]),
    ("New Haven Line", "other", ["New Haven CT", "Bridgeport CT", "Stamford CT", "Greenwich CT"]),
    ("Branches", "other", ["Bridgeport CT", "Waterbury CT"]),
    ("Branches", "other", ["Norwalk CT", "Danbury CT"]),
    ("Capitol", "new", ["@Lowell", "Nashua NH", "Manchester NH"]),
    ("Capitol", "imagined", ["Manchester NH", "Concord NH"]),
    ("Inland", "new", ["@Worcester", "~Spencer MA", "~Warren MA", "Palmer MA", "Springfield MA"]),
    ("Seacoast", "imagined", ["@Newburyport", "~Seabrook NH", "~Hampton NH", "Portsmouth NH"]),
    ("Milford", "new", ["@Forge Park/495", "Milford MA"]),
    ("Downeast", "new", ["@Haverhill", "Plaistow NH"]),
    ("Downeast", "other", ["Plaistow NH", "Exeter NH", "Dover NH", "Biddeford ME", "Portland ME", "Brunswick ME"]),
    ("Downeast", "new", ["Brunswick ME", "Bath ME", "Rockland ME"]),
    ("Seacoast", "new", ["Dover NH", "Rochester NH"]),
    ("Northern Tier", "imagined", ["@Wachusett", "Gardner MA", "Athol MA", "Greenfield MA", "North Adams MA"]),
    ("Cape", "new", ["@Middleborough", "Wareham MA", "Bourne MA"]),
    ("Cape", "imagined", ["Bourne MA", "Barnstable MA"]),
    ("Plymouth", "new", ["@Kingston", "Plymouth MA"]),
    ("Peabody", "new", ["Salem MA", "Peabody MA"]),
    ("Valley", "other", ["New Haven CT", "Meriden CT", "Hartford CT", "Springfield MA"]),
    ("Valley", "other", ["Springfield MA", "Holyoke MA", "Northampton MA", "Greenfield MA", "Brattleboro VT",
                         "Hartford VT", "Montpelier VT", "Essex VT", "St. Albans VT"]),
    ("Champlain", "new", ["Essex VT", "Burlington VT"]),
    ("Champlain", "other", ["Burlington VT", "Middlebury VT", "Rutland VT"]),
    ("Champlain", "imagined", ["Rutland VT", "Bennington VT"]),
    ("Berkshire", "new", ["Springfield MA", "Westfield MA", "Pittsfield MA"]),
    ("Housatonic", "imagined", ["Danbury CT", "New Milford CT", "Pittsfield MA"]),
    ("Blackstone", "new", ["Providence RI", "Pawtucket RI", "Woonsocket RI", "Worcester MA"]),
    ("Granite", "imagined", ["Concord NH", "Lebanon NH", "Hartford VT"]),
    ("Pine Tree", "imagined", ["Brunswick ME", "Augusta ME", "Waterville ME", "Bangor ME"]),
    ("Pine Tree", "imagined", ["Portland ME", "Lewiston ME"]),
]
# Drawn straight: the old line isn't in the rail data. Plymouth's town center point is far from its station.
STRAIGHT = {("Kingston", "Plymouth")}
FIXED = {"Plymouth MA": (-70.6915, 41.9812)}  # Cordage Park station area, approximate
LABEL = {"Hartford VT": "White River Jct", "Barnstable MA": "Hyannis", "Essex VT": "Essex Jct"}
COLOR = {"other": "#555555", "new": "#c8102e", "imagined": "#1f6fb2"}


def towns():
    t = gpd.read_file(REPO / "data/shared/ne_towns.gpkg").to_crs(CRS)
    t["key"] = t.NAME.str.replace(r" Town$", "", regex=True) + " " + t.STATEFP.map(FIPS)  # MA cities styled as towns
    return t


def graph():
    """1911 track plus today's running lines, vertex by vertex, with short gaps joined.

    Loose ends within GAP_M of another piece of track get a costlier link.
    """
    old = gpd.read_file(REPO / "data/shared/ne_rail_1826_1911.gpkg").to_crs(CRS)
    new = gpd.read_file(REPO / "data/shared/ne_rail_today.gpkg").to_crs(CRS)
    geoms = list(old[old.year_opened <= 1911].geometry) + list(new[new.service.isna()].geometry)
    G = nx.Graph()
    snap = lambda c: (round(c[0] / SNAP_M) * SNAP_M, round(c[1] / SNAP_M) * SNAP_M)
    for geom in geoms:
        c = [snap(x) for x in geom.simplify(30).coords]
        for u, v in zip(c, c[1:]):
            if u != v:
                G.add_edge(u, v, w=float(np.hypot(u[0] - v[0], u[1] - v[1])))
    # Atack's lines break at river bridges: tie each loose end to the nearest other piece of track.
    comp = {n: i for i, c in enumerate(nx.connected_components(G)) for n in c}
    pts = np.array(list(G.nodes))
    tree = cKDTree(pts)
    for n in [n for n, d in G.degree if d == 1]:
        near = tree.query_ball_point(n, GAP_M)
        other = [tuple(pts[i]) for i in near if comp[tuple(pts[i])] != comp[n]]
        if other:
            v = min(other, key=lambda o: np.hypot(o[0] - n[0], o[1] - n[1]))
            G.add_edge(n, v, w=3 * float(np.hypot(v[0] - n[0], v[1] - n[1])))
    return G.subgraph(max(nx.connected_components(G), key=len)).copy()


def main():
    t = towns()
    stops = gpd.read_file(DAY / "data/mbta_stops.gpkg").to_crs(CRS)
    G = graph()
    nodes = np.array(list(G.nodes))

    def locate(s):
        s = s.lstrip("~")
        if s in FIXED:
            return gpd.GeoSeries(gpd.points_from_xy(*zip(FIXED[s])), crs=4326).to_crs(CRS).iloc[0], s[:-3]
        if s.startswith("@"):
            hit = stops[stops.name == s[1:]]
            if len(hit) < 1:
                raise SystemExit(f"no MBTA stop {s}")
            return hit.geometry.iloc[0], s[1:]
        hit = t[t.key == s]
        if len(hit) == 0:
            raise SystemExit(f"no town {s}")
        if len(hit) > 1:  # e.g. Essex town vs Essex Junction city: take the biggest
            hit = hit.assign(a=hit.area).nlargest(1, "a")
        return hit.geometry.iloc[0].representative_point(), LABEL.get(s, s[:-3])

    legs, st = [], {}
    for line, status, seq in LEGS:
        for u, v in zip(seq, seq[1:]):
            hidden = [x.startswith("~") for x in (u, v)]
            a, la = locate(u)
            b, lb = locate(v)
            na = tuple(nodes[np.argmin(np.hypot(*(nodes - [a.x, a.y]).T))])
            nb = tuple(nodes[np.argmin(np.hypot(*(nodes - [b.x, b.y]).T))])
            geom = LineString([a, b]) if (la, lb) in STRAIGHT else LineString(nx.shortest_path(G, na, nb, weight="w")).simplify(60)
            legs.append({"line": line, "status": status, "a": la, "b": lb, "km": geom.length / 1000,
                         "detour": geom.length / a.distance(b), "geometry": geom})
            if not hidden[0]:
                st.setdefault(la, a)
            if not hidden[1]:
                st.setdefault(lb, b)
    r = gpd.GeoDataFrame(legs, crs=CRS)
    s = gpd.GeoDataFrame({"label": list(st), "geometry": list(st.values())}, crs=CRS)
    for f in ("extensions.gpkg", "ext_stations.gpkg"):
        (DAY / "data" / f).unlink(missing_ok=True)
    r.to_file(DAY / "data/extensions.gpkg", layer="legs", driver="GPKG")
    s.to_file(DAY / "data/ext_stations.gpkg", layer="stations", driver="GPKG")
    print(r.groupby("status").km.sum().div(1.609).round(0).to_dict(), "miles;", len(r), "legs;", len(s), "stations")
    print(r[r.detour > 1.5][["line", "a", "b", "km", "detour"]].round(1).to_string(index=False))

    mb = gpd.read_file(DAY / "data/mbta_lines.gpkg").to_crs(CRS)
    fig, ax = plt.subplots(figsize=(10, 12))
    t.dissolve().plot(ax=ax, color="#efece4", lw=0)
    mb[mb.kind == "commuter"].plot(ax=ax, color="#80276c", lw=1.4)
    mb[mb.kind == "subway"].plot(ax=ax, color="#111", lw=1)
    for k, g in r.groupby("status"):
        g.plot(ax=ax, color=COLOR[k], lw=1.5, ls="--" if k == "imagined" else "-", label=k)
    s.plot(ax=ax, color="white", edgecolor="#222", markersize=10, zorder=5)
    for p, n in zip(s.geometry, s.label):
        ax.annotate(n, (p.x, p.y), xytext=(3, 2), textcoords="offset points", fontsize=5)
    ax.legend(loc="lower right", frameon=False)
    ax.set_axis_off()
    (DAY / "output").mkdir(exist_ok=True)
    fig.savefig(DAY / "output/draft_network.png", dpi=170, bbox_inches="tight")


if __name__ == "__main__":
    main()
