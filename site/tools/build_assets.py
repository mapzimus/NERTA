"""Build the website's data and images from the map code and the finished release files.

    python site/tools/build_assets.py

Reads only. Writes only inside site/: stops.json, logo SVGs, and web-sized copies of the release maps.
Nothing in boston-map/output/ is touched.
"""
import json
import re
import sys
from pathlib import Path
from shutil import copyfile as shutil_copy

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from PIL import Image

SITE = Path(__file__).resolve().parents[1]
REPO = SITE.parent
SRC = REPO / "boston-map" / "src"
_COPIES = REPO / "boston-map" / "output" / "copies"


def _run_no(p):
    return int(p.name[5:]) if p.name.startswith("web_v") else 1


RUNS = sorted([p for p in _COPIES.glob("web*") if p.is_dir()], key=_run_no, reverse=True)


class _Newest:
    """Web versions of the maps, from site/tools/render_web_maps.py. Each file comes from the newest run folder that has it."""
    def __truediv__(self, name):
        stem, ext = Path(name).stem, Path(name).suffix
        for run in RUNS:
            if (run / name).exists():
                return run / name
            versions = sorted(run.glob(f"{stem}_v*{ext}"), key=lambda p: int(p.stem.rsplit("_v", 1)[1]) if p.stem.rsplit("_v", 1)[1].isdigit() else 0)
            if versions:
                return versions[-1]
        return RUNS[0] / name


RELEASE = _Newest()
sys.path.insert(0, str(SRC))

import make_tmap as M  # noqa: E402  (import only; main() is never called, so nothing is drawn or saved)
from nerta_mark import draw_nerta, draw_t  # noqa: E402
from station_kit import INK, WHITE, place, rounded  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
OUT = SITE / "assets"
(OUT / "maps").mkdir(parents=True, exist_ok=True)
(OUT / "logo").mkdir(parents=True, exist_ok=True)

# Which networks' maps are released on nerta.fun (Max, November 8: only the main map and the 8 subway posters today).
# Flip one to True and rebuild to publish that network's map images. Stops, connections and pages stay live either way.
RELEASED = {"ferry": True, "rail": True, "tram": True}  # Max, November 8: everything, trams included ("tram maps on the site asap")

LINE_KEY = {M.RED: "red", M.ORANGE: "orange", M.BLUE: "blue", M.GREEN: "green", M.YELLOW: "yellow",
            M.CYAN: "cyan", M.INDIGO: "indigo", M.SILVER: "silver"}
LINE_COLOR = {v: k for k, v in LINE_KEY.items()}


def clean(name):
    """Map labels carry layout marks: trailing * or +, hair spaces, line breaks."""
    name = name.rstrip("*+").replace(" ", "").replace("\n", " ")
    name = re.sub(r"\s+", " ", name).strip()
    # The map labels Mass Ave as MIT (keeps it apart from Orange's Mass. Ave); the posters show State as Boston Central.
    return {"Mass Ave": "MIT", "State": "Boston Central"}.get(name, name)


def caps(text):
    """POSTER CAPS to normal case, keeping state and city codes: CONCORD NH, MONTREAL -> Concord NH, Montreal."""
    keep = {"NH", "VT", "NYC", "TF", "US"}
    def cap(w):
        lead = len(w) - len(w.lstrip("(\"'"))  # keep an opening bracket or quote, capitalize what follows
        return w if w.strip(",()") in keep else w[:lead] + w[lead:].capitalize()
    return " ".join(cap(w) for w in text.split())


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("'", "")).strip("-")


# The Green Line's C and E branches leave the trunk between drawn stops: on the main map the C leg starts at (50, 84), just
# past Kenmore (54, 84) on the way to Blandford St, and the E leg at (69, 84), between Copley (75, 84) and Hynes (59, 84).
JOIN = {"green": {"St. Mary's St": "Kenmore", "Prudential": "Copley"}}
SUBWAY_NAMES = {"red": "Red Line", "orange": "Orange Line", "blue": "Blue Line", "green": "Green Line", "yellow": "Yellow Line",
                "cyan": "Cyan Line", "indigo": "Indigo Line", "silver": "Silver Line"}


def track_ends(legs):
    """Stops at an end of track: they touch only one other stop on the line. A closed loop has none."""
    nbr = {}
    for leg in legs:
        for a, b in zip(leg, leg[1:]):
            nbr.setdefault(a, set()).add(b)
            nbr.setdefault(b, set()).add(a)
    return list(dict.fromkeys(sid for leg in legs for sid in (leg[0], leg[-1]) if len(nbr.get(sid, ())) == 1))


def full_network():
    """The whole network as the maps draw it. Every line is a list of legs (stop ids in order) plus its terminals.

    Subway: each line poster's own legs, in poster order, with its terminals (make_line_poster.LAYOUTS).
    Regional Rail and High-Speed Rail: each line walked along its own drawn track on the rail poster, branches as their
    own legs starting at the junction (make_rail_poster.PATHS, BRANCHES, STATIONS).
    Ferry: each route's stops, banks and branches (make_ferry_network.write_routes).
    Diagram x, y (for the system map image) come from the main map (make_tmap.lines, CR_STOPS) where a stop is drawn there.
    """
    import tempfile
    from shapely.geometry import LineString, Point
    import make_line_poster as LP
    import make_rail_poster as RP
    import make_ferry_network as F

    xy, _segs = stops_and_lines()  # diagram positions and today's transfer pills, from the main map
    stops, lines = {}, {}

    def stop(name, kind="station"):
        n = clean(name)
        sid = slug(n) if kind == "station" else "dock-" + slug(n)
        if sid not in stops:
            s = {"id": sid, "name": n, "kind": kind, "lines": []}
            if kind == "station" and sid in xy:
                s.update(x=xy[sid]["x"], y=xy[sid]["y"])
                for k in ("hsr", "ferry"):
                    if k in xy[sid]:
                        s[k] = xy[sid][k]
            stops[sid] = s
        return sid

    def serve(sid, key):
        if key not in stops[sid]["lines"]:
            stops[sid]["lines"].append(key)

    # Subway, from lines() in make_tmap.py: the project's single source for stops and their order (the posters are drawn
    # from it). Silver isn't on the main map, so it comes from its poster. Ends are worked out from the track itself.
    by_color = {}
    for col, _style, _path, names in M.lines():
        if col in LINE_KEY:
            by_color.setdefault(LINE_KEY[col], []).append(names)
    for key, (color, code, _title, layout, _ends) in LP.LAYOUTS.items():
        raw = by_color.get(key) or [leg["stops"] for leg in layout()]
        legs = []
        for names in raw:
            ids = [stop(n) for n in names]
            ids = [i for j, i in enumerate(ids) if j == 0 or i != ids[j - 1]]
            for i in ids:
                serve(i, key)
            legs.append(ids)
        for first, junction in JOIN.get(key, {}).items():  # branches that leave the trunk between two drawn stops
            for leg in legs:
                if leg[0] == slug(first):
                    leg.insert(0, slug(junction))
        lines[key] = {"key": key, "mode": "subway", "name": SUBWAY_NAMES[key], "short": code, "color": color,
                      "legs": legs, "terminals": track_ends(legs)}

    # Regional Rail and High-Speed Rail, walked along the rail poster's track
    RP.build()
    RP.stations()
    for k, d in RP.LINES.items():
        main = LineString(RP.PATHS[k])
        branches = [LineString(b) for bk, b in RP.BRANCHES if bk == k]
        on_main, on_branch = [], {i: [] for i in range(len(branches))}
        for s in RP.STATIONS:
            for ln, p in s["dots"]:
                if ln != k:
                    continue
                if s["kind"] == "pass" and d.get("hsr"):  # high-speed trains run through Sullivan Sq without stopping
                    continue
                pt = Point(p)
                if main.distance(pt) < 0.5 or not branches:
                    on_main.append((main.project(pt), s["name"]))
                else:
                    b = min(range(len(branches)), key=lambda i: branches[i].distance(pt))
                    on_branch[b].append((branches[b].project(pt), s["name"]))
        order = [n for _, n in sorted(on_main)]
        legs = [[stop(n) for n in dict.fromkeys(order)]]
        for i, pts in on_branch.items():
            if not pts:
                continue
            start = Point(branches[i].coords[0])
            junction = min(order, key=lambda n: next(Point(q).distance(start) for ln, q in
                                                      next(x for x in RP.STATIONS if x["name"] == n)["dots"] if ln == k))
            legs.append([stop(junction)] + [stop(n) for n in dict.fromkeys(n for _, n in sorted(pts))])
        key = "hsr-" + HSR_TO[k].lower().replace(" ", "-") if d.get("hsr") else "rail-" + k
        for leg in legs:
            for i in leg:
                serve(i, key)
                serve(i, "rail")
        ends = track_ends(legs)
        beyond = None
        for ak, apts, rows, _place in RP.ARROWS:  # the line runs on past the poster's edge, as its arrow label says
            if ak != k:
                continue
            start = Point(apts[-1])  # the arrow tip, at the far end
            at = min(on_main, key=lambda t: next(Point(q).distance(start) for ln, q in
                                                  next(x for x in RP.STATIONS if x["name"] == t[1])["dots"] if ln == k))[1]
            to = next(r for r in rows if "TO " in r).split("TO ", 1)[1]
            via = next((r[4:] for r in rows if r.startswith("VIA ")), "")
            beyond = {"at": slug(clean(at)), "to": caps(to), "via": caps(via)}
            ends = [e for e in ends if e != beyond["at"]]
        name = f"High-Speed Rail to {beyond['to']}" if d.get("hsr") else d["name"].title()
        if (RELEASE / f"rail_line_{k}.png").exists():
            poster = f"rail_line_{k}"
        else:
            poster = None
        lines[key] = {"key": key, "mode": "hsr" if d.get("hsr") else "rail", **({"poster": poster} if poster else {}), "name": name, "short": "HSR" if d.get("hsr") else "RR",
                      "color": M.CR_TEXT_COLOR, "hue": M.HSR if d.get("hsr") else d.get("hue"), "legs": legs, "terminals": ends,
                      **({"beyond": beyond} if beyond else {})}

    # Ferries, from the ferry network's own route list
    tmp = Path(tempfile.mkdtemp()) / "routes.json"
    F.write_routes(tmp)
    fd = json.loads(tmp.read_text(encoding="utf-8"))
    for r in fd["routes"]:
        parts = ([r["stops"]] if r.get("stops") else []) + list(r.get("banks", {}).values()) + list(r.get("branches", {}).values())
        legs = [[stop(n, "dock") for n in part] for part in parts]
        if r.get("loop") and len(legs) == 2:  # a river loop: up one bank, round the end, back down the other, and round again
            legs = [legs[0] + legs[1] + [legs[0][0]]]
        key = "ferry-" + r["key"]
        for leg in legs:
            for i in leg:
                serve(i, key)
                serve(i, "ferry")
                stops[i].setdefault("label", r["labels"].get(stops[i]["name"])) if r["labels"].get(stops[i]["name"]) else None
                if stops[i]["name"] in r["major_ports"]:
                    stops[i]["major"] = True
                pills = r["pills"].get(stops[i]["name"])
                if pills:
                    stops[i]["transfers"] = sorted(set(stops[i].get("transfers", [])) | set(pills))
        ends = [] if r.get("loop") else track_ends(legs)
        lines[key] = {"key": key, "mode": "ferry", "name": r["name"], "short": "F", "color": r["color"], "family": r["family"],
                      "style": r["style"], "loop": bool(r.get("loop")), "services": r.get("services", []), "note": r.get("note", ""),
                      "legs": legs, "terminals": ends}
    families = [{"name": f["name"], "routes": ["ferry-" + k for k in f["routes"]]} for f in fd["families"]]
    import make_ferry_line_posters as FL
    for k in FL.LAYOUTS:
        if "ferry-" + k in lines and (RELEASE / f"{FL.slug(k)}.png").exists():
            lines["ferry-" + k]["poster"] = FL.slug(k)

    # Trams, from the tram session's export (boston-map/data/tram/tram_network.json). Stops join stations by their internal
    # key (the main map's own name); other tram stops are their own places, kind "tram". Real street paths go to geo/.
    tn = REPO / "boston-map" / "data" / "tram" / "tram_network.json"
    trams = None
    if tn.exists():
        trams = json.loads(tn.read_text(encoding="utf-8"))
        tram_paths = []
        for tl in trams["lines"]:
            key = "tram-" + slug(tl["id"])
            legs = []
            for br in tl["branches"]:
                ids = []
                for st in br["stops"]:
                    sid = slug(clean(st["key"]))
                    if st.get("station") and sid in stops and stops[sid]["kind"] == "station":
                        pass
                    else:
                        sid = "tram-" + slug(st["key"])
                        if sid not in stops:
                            # The tram map itself defines where these stops are, so their spot is exact, not approximate
                            stops[sid] = {"id": sid, "name": st["name"], "kind": "tram", "lines": [],
                                          "geo": {"lat": round(st["lat"], 6), "lon": round(st["lon"], 6), "verified": True}}
                    serve(sid, key)
                    serve(sid, "tram")
                    if not ids or ids[-1] != sid:
                        ids.append(sid)
                legs.append(ids)
            lines[key] = {"key": key, "mode": "tram", "name": f"Tram {tl['id']}: {tl['name']}", "short": tl["id"],
                          "number": tl["id"], "title": tl["name"], "via": tl.get("via", ""), "color": tl.get("color", trams["color"]),
                          "legs": legs, "terminals": track_ends(legs)}
            tram_paths.append({"type": "Feature", "properties": {"line": key, "id": tl["id"], "name": tl["name"], "color": tl.get("color", trams["color"])},
                               "geometry": {"type": "LineString", "coordinates": [[round(lon, 6), round(lat, 6)] for lat, lon in tl["path"]]}})
        geo_dir = SITE / "data" / "geo"
        geo_dir.mkdir(exist_ok=True)
        (geo_dir / "tram_lines.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": tram_paths}), encoding="utf-8")
    # Public parking garage or lot: exactly the stations the main map marks with a P (make_tmap.PARKING).
    for n in getattr(M, "PARKING", []):
        sid = slug(clean(n))
        if sid in stops and stops[sid]["kind"] == "station":
            stops[sid]["parking"] = True
        else:
            print("  parking station not in the network:", n)
    # A station's ferry dock, by the dock name the posters give it.
    for s in stops.values():
        if s["kind"] == "station" and s.get("ferry"):
            dock = "dock-" + slug(clean(s["ferry"]))
            s["dock"] = dock if dock in stops else None
    # Regional Rail stations on the main map that the rail poster doesn't carry keep the generic rail mark.
    for sid, s in xy.items():
        if sid in stops:
            if "rail" in s["lines"]:
                serve(sid, "rail")
        else:
            stops[sid] = {**{k: v for k, v in s.items() if k not in ("mode", "status")}, "kind": "station"}
    # A stop no real line serves is a stale label (e.g. the main map's "Norwood" and "Wellesley", which the rail poster names
    # Norwood Central and Wellesley Square): leave it out.
    for sid in [k for k, v in stops.items() if not [l for l in v["lines"] if l not in ("rail", "ferry", "tram")]]:
        print("  dropped, no line stops here:", stops[sid]["name"])
        del stops[sid]
    return stops, lines, families, (trams or {}).get("service", "")


def stops_and_lines():
    stops, segments = {}, []
    for col, style, path, names in M.lines():
        key = LINE_KEY.get(col)
        if key is None:
            continue
        xy = rounded(path, 7 if "Terminals" in names else M.CR)
        spots = place(xy, names, {**M.A, **M.EXTRA})
        seg = []
        for raw in names:
            if raw in M.EXTRA:  # a hidden second spot for a station drawn elsewhere
                raw_name = clean(raw)
            else:
                raw_name = clean(raw)
            sid = slug(raw_name)
            if sid not in stops:
                p = spots.get(raw) if raw not in M.EXTRA else None
                p = p if p is not None else spots.get(raw)
                stops[sid] = {"id": sid, "name": raw_name, "x": round(float(p[0]), 2), "y": round(float(p[1]), 2),
                              "lines": [], "mode": "subway", "status": style}
            if key not in stops[sid]["lines"]:
                stops[sid]["lines"].append(key)
            seg.append(sid)
        segments.append({"line": key, "status": style, "stops": seg})
    for name, xy, _side, style in M.CR_STOPS:
        n = clean(name)
        sid = slug(n)
        if sid in stops:
            stops[sid].setdefault("modes", []).append("rail")
            continue
        stops[sid] = {"id": sid, "name": n, "x": xy[0], "y": xy[1], "lines": ["rail"], "mode": "rail", "status": style}
    # Rail, high-speed and ferry transfers, from the line posters (import only; nothing is drawn).
    import make_line_poster as LP
    for name, pills in LP.EXTRA_TRANSFERS.items():
        s = stops.get(slug(clean(name)))
        if not s:
            continue
        if "CR" in pills and "rail" not in s["lines"]:
            s["lines"].append("rail")
        if "HSR" in pills:
            s["hsr"] = True
        if "F" in pills:
            s["ferry"] = LP.FERRY_VIA.get(name, s["name"])
    return stops, segments


def logos():
    """The three-layer T over the NERTA pill, as SVG: the system version (11 stripes) and one per line."""
    def one(path, colors, grid=1):
        fig = plt.figure(figsize=(2.2, 2.9))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(-11, 11)
        ax.set_ylim(-18, 11)
        ax.set_aspect("equal")
        ax.set_axis_off()
        tr = 7.6
        ax.add_patch(Circle((0, 0), tr, fc=WHITE, ec=INK, lw=4.5 * 2.2 / 3.73, zorder=12))
        draw_t(ax, 0, 0, tr, colors, grid=grid)
        ro = tr + 0.6
        draw_nerta(ax, 0, -ro - 1.0, 2 * ro, "B", colors=colors, grid=grid)
        fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.02, metadata={"Date": None})
        plt.close(fig)

    def roundel_only(path, colors):
        fig = plt.figure(figsize=(2.2, 2.2))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(-8.6, 8.6)
        ax.set_ylim(-8.6, 8.6)
        ax.set_aspect("equal")
        ax.set_axis_off()
        ax.add_patch(Circle((0, 0), 7.6, fc=WHITE, ec=INK, lw=4.5 * 2.2 / 3.73 * 1.25, zorder=12))
        draw_t(ax, 0, 0, 7.6, colors)
        fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.02, metadata={"Date": None})
        plt.close(fig)

    def app_icon(path, px, colors, pad=0.10):
        """The multicolor T on white, square, for home screens and browser tabs (iPhone and Android ignore SVG icons)."""
        fig = plt.figure(figsize=(1, 1), dpi=px)
        ax = fig.add_axes([0, 0, 1, 1])
        lim = 7.6 / (1 - 2 * pad) + 0.3
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_axis_off()
        fig.patch.set_facecolor(WHITE)
        ax.add_patch(Circle((0, 0), 7.6, fc=WHITE, ec=INK, lw=max(1.0, px / 180 * 3.2), zorder=12))
        draw_t(ax, 0, 0, 7.6, colors)
        fig.savefig(path, dpi=px, facecolor=WHITE, metadata={"Software": None})
        plt.close(fig)

    system = M.NERTA_COLORS  # every line color, tram pink included (Max, November 8); the stripe direction lives in nerta_mark.py
    icons = OUT / "icons"
    icons.mkdir(exist_ok=True)
    for px in (32, 180, 192, 512):
        app_icon(icons / f"t-{px}.png", px, system, pad=0.04 if px == 32 else 0.10)
    Image.open(icons / "t-180.png").convert("RGBA").save(SITE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    one(OUT / "logo" / "nerta.svg", system)
    # The 37-color alternate: every line color, on a grid twice as fine. Site only, now and then; never on a map image.
    if hasattr(M, "NERTA_COLORS_ALL"):
        one(OUT / "logo" / "nerta_37.svg", M.NERTA_COLORS_ALL, grid=2)
    # The Charlie Points coin, drawn by the maps' own code so every map and the site match
    try:
        import charlie_points as CPM
        fig = plt.figure(figsize=(1, 1))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(-1.05, 1.05)
        ax.set_ylim(-1.05, 1.05)
        ax.set_aspect("equal")
        ax.set_axis_off()
        CPM.draw_cp(ax, 0, 0, 1.0)
        fig.savefig(OUT / "logo" / "cp.svg", transparent=True, bbox_inches="tight", pad_inches=0.01, metadata={"Date": None})
        plt.close(fig)
    except Exception as e:  # the coin is a nicety; never stop the build for it
        print("  CP coin not drawn:", e)
    roundel_only(OUT / "logo" / "t.svg", system)
    for col, key in LINE_KEY.items():
        roundel_only(OUT / "logo" / f"t_{key}.svg", (col,))



def retry(fn, *a, tries=6):
    """Windows briefly locks a freshly written file (virus scan, indexer). Wait and try again rather than fail."""
    import time
    for i in range(tries):
        try:
            return fn(*a)
        except OSError:
            if i == tries - 1:
                raise
            time.sleep(2 + 2 * i)


def web_image(src, dst, width, quality=82):
    im = Image.open(src).convert("RGB")
    h = round(im.height * width / im.width)
    tmp = dst.with_suffix(".tmp.webp")  # write beside, then swap in: a file held open elsewhere can't half-write
    im.resize((width, h), Image.LANCZOS).save(tmp, "WEBP", quality=quality, method=6)
    retry(tmp.replace, dst)
    return im.size, (width, h)


def maps():
    sizes = {}
    full, web = web_image(RELEASE / "system_map.png", OUT / "maps" / "system_map.webp", 6000, 80)
    web_image(RELEASE / "system_map.png", OUT / "maps" / "system_map_thumb.webp", 900)
    sizes["system"] = {"width": web[0], "height": web[1]}
    for key in LINE_KEY.values():
        web_image(RELEASE / f"line_{key}.png", OUT / "maps" / f"line_{key}.webp", 2400)
        web_image(RELEASE / f"line_{key}.png", OUT / "maps" / f"line_{key}_thumb.webp", 700)
    return sizes


HSR_TO = {"hmon": "Montreal", "hmai": "Bangor", "halb": "Albany", "hnyc": "New York"}


def rail():
    """Regional Rail and High-Speed Rail lines with stations in order, from make_rail_poster.py (read only, nothing drawn)."""
    import make_rail_poster as RP
    RP.build()
    RP.stations()
    lines = {k: [] for k in RP.LINES}
    for s in RP.STATIONS:
        for ln, _xy in s["dots"]:
            if ln in lines and clean(s["name"]) not in lines[ln]:
                lines[ln].append(clean(s["name"]))
    out = []
    for k, d in RP.LINES.items():
        name = d["name"].title().replace(" / ", " / ")
        if d.get("hsr"):
            name = f"High-Speed Rail to {HSR_TO[k]}"
        out.append({"key": k, "name": name, "hue": d.get("hue"), "hsr": bool(d.get("hsr")), "stops": lines[k],
                    "ends": [n for n in lines[k] if any(clean(s["name"]) == n and s["kind"] == "end" for s in RP.STATIONS)]})
    return {"lines": out}


def ferry():
    """Every ferry route with its docks, from make_ferry_network.py's own route export."""
    import json as _j
    import tempfile
    import make_ferry_network as F
    tmp = Path(tempfile.mkdtemp()) / "routes.json"
    F.write_routes(tmp)
    return _j.loads(tmp.read_text(encoding="utf-8"))


def downloads():
    """Full-quality files for the Download links: vector PDFs and the 600 dpi system map PNG."""
    import shutil
    dl = SITE / "downloads"
    dl.mkdir(exist_ok=True)
    retry(shutil.copyfile, RELEASE / "system_map.pdf", dl / "system_map.pdf")
    retry(shutil.copyfile, RELEASE / "system_map.png", dl / "system_map.png")
    for key in LINE_KEY.values():
        retry(shutil.copyfile, RELEASE / f"line_{key}.pdf", dl / f"line_{key}.pdf")


if __name__ == "__main__":
    data_only = "--data-only" in sys.argv
    if not data_only:
        logos()  # no downloads: Max doesn't want any map downloadable
        sizes = maps()
    stops, lines, families, tram_service = full_network()
    # Real-world locations, from site/tools/geocode_stops.py (two sources where possible, each one marked).
    loc_file = SITE / "data" / "locations.json"
    locs = json.loads(loc_file.read_text(encoding="utf-8")) if loc_file.exists() else {}
    # Hand-kept additions for stops added after the geocoding run (two sources each, or marked unverified)
    extra = SITE / "tools" / "locations_extra.json"
    if extra.exists():
        locs.update(json.loads(extra.read_text(encoding="utf-8")))
    missing = []
    for s in stops.values():
        if s["kind"] == "tram":  # tram stops come with the tram session's own coordinates
            continue
        L = locs.get(s["name"] + " (dock)") if s["kind"] == "dock" else None
        L = L or locs.get(s["name"]) or locs.get({"MIT": "Mass Ave"}.get(s["name"], ""))  # the code's own name for it
        if L:
            s["geo"] = {"lat": round(L["lat"], 6), "lon": round(L["lon"], 6), "verified": L.get("verified", False)}
        else:
            missing.append(s["name"])
    # Regional Rail stations: the rail session's real-geography layer (two sources per station, checked within 150 m) wins.
    rr = REPO / "boston-map" / "data" / "rail_regional"
    if (rr / "cr_stations.geojson").exists():
        by_name = {s["name"]: s for s in stops.values() if s["kind"] == "station"}
        for f in json.loads((rr / "cr_stations.geojson").read_text(encoding="utf-8"))["features"]:
            p, (lon, lat) = f["properties"], f["geometry"]["coordinates"][:2]
            s = by_name.get(p["name"])
            if s:
                s["geo"] = {"lat": round(lat, 6), "lon": round(lon, 6), "verified": bool(p.get("verified")) and not p.get("approx")}
                if s["name"] in missing:
                    missing.remove(s["name"])
        geo = SITE / "data" / "geo"
        geo.mkdir(exist_ok=True)
        keep = {"line", "name", "piece", "kind", "color", "edge", "end", "lines", "hsr"}  # what the street map uses; no source notes
        for f in ("cr_lines.geojson", "cr_stations.geojson"):
            g = json.loads((rr / f).read_text(encoding="utf-8"))
            for feat in g["features"]:
                feat["properties"] = {k: v for k, v in feat["properties"].items() if k in keep}
            (geo / f).write_text(json.dumps(g), encoding="utf-8")
    size = {"width": 6000, "height": round(6000 * (M.YLIM[1] - M.YLIM[0]) / (M.XLIM[1] - M.XLIM[0]))}
    # Free rides (Max, November 8): the whole Silver Logan shuttle, tram 23, the Fast Ferry shuttle, and the river zigzag boats
    for k in ("silver", "tram-23", "ferry-express"):
        if k in lines:
            lines[k]["free"] = True
    for l in lines.values():
        if l["mode"] == "ferry" and l.get("loop"):
            l["freeService"] = "zigzag"
    for l in lines.values():  # route and line posters only show for released networks
        net = {"ferry": "ferry", "rail": "rail", "hsr": "rail", "tram": "tram"}.get(l["mode"])
        if net and not RELEASED[net]:
            l.pop("poster", None)
    data = {"extent": {"x": list(M.XLIM), "y": list(M.YLIM)}, "image": size, "lines": lines, "families": families, "tramService": tram_service,
            "released": RELEASED,
            "stops": sorted(stops.values(), key=lambda s: (s["name"], s["kind"]))}
    (SITE / "data").mkdir(exist_ok=True)
    (SITE / "data" / "network.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    for old in ("rail.json", "ferry.json"):
        (SITE / "data" / old).unlink(missing_ok=True)
    print(len(stops), "stops,", len(lines), "lines,", len(missing), "without a location")
    # Unreleased networks' map images don't sit in the site folder at all (they'd still be reachable by URL otherwise)
    for net, pats in {"ferry": ["ferry_*.webp"], "rail": ["rail_*.webp"], "tram": ["tram_*.webp"]}.items():
        if not RELEASED[net]:
            for pat in pats:
                for f in (OUT / "maps").glob(pat):
                    f.unlink()
    # A ferry network map rendered by render_web_maps.py ("ferry"), when there is one.
    fn = RELEASE / "ferry_network.png"
    if fn.exists() and not data_only and RELEASED["ferry"]:
        web_image(fn, OUT / "maps" / "ferry_network.webp", 3600)
        web_image(fn, OUT / "maps" / "ferry_network_thumb.webp", 900)
        retry(shutil_copy, RELEASE / "ferry_network.pdf", SITE / "downloads" / "ferry_network.pdf")
    # Ferry route posters (make_ferry_line_posters.py), one per route, when rendered
    import make_ferry_line_posters as FL
    for k in FL.LAYOUTS:
        name = FL.slug(k)
        src = RELEASE / f"{name}.png"
        if src.exists() and not data_only and RELEASED["ferry"]:
            web_image(src, OUT / "maps" / f"{name}.webp", 2400)
            web_image(src, OUT / "maps" / f"{name}_thumb.webp", 700)
            if (RELEASE / f"{name}.pdf").exists():
                retry(shutil_copy, RELEASE / f"{name}.pdf", SITE / "downloads" / f"{name}.pdf")
    # Rail line posters (make_rail_line_posters.py), one per commuter and high-speed line, when rendered
    import make_rail_poster as _RP
    for k in _RP.LINES:
        src = RELEASE / f"rail_line_{k}.png"
        if src.exists() and not data_only and RELEASED["rail"]:
            web_image(src, OUT / "maps" / f"rail_line_{k}.webp", 2400)
            web_image(src, OUT / "maps" / f"rail_line_{k}_thumb.webp", 700)
            if (RELEASE / f"rail_line_{k}.pdf").exists():
                retry(shutil_copy, RELEASE / f"rail_line_{k}.pdf", SITE / "downloads" / f"rail_line_{k}.pdf")
    for src_name, out_name in (("rail_regional.png", "rail_regional"), ("rail_network.png", "rail_network")):
        src = RELEASE / src_name
        if src.exists() and not data_only and RELEASED["rail"]:
            web_image(src, OUT / "maps" / f"{out_name}.webp", 4800)
            web_image(src, OUT / "maps" / f"{out_name}_thumb.webp", 1000)
    # Tram maps, rendered for the site by render_web_maps.py ("trams")
    for src_name, out_name, wide in (("tram_map.png", "tram_map", 4800), ("tram_network.png", "tram_network", 4800), ("tram_display.png", "tram_display", 4800)):
        src = RELEASE / src_name
        if src.exists() and not data_only and RELEASED["tram"]:
            web_image(src, OUT / "maps" / f"{out_name}.webp", wide)
            web_image(src, OUT / "maps" / f"{out_name}_thumb.webp", 1000)
    rp = RELEASE / "rail_poster.png"
    if rp.exists() and not data_only and RELEASED["rail"]:
        web_image(rp, OUT / "maps" / "rail_map.webp", 4800)
        web_image(rp, OUT / "maps" / "rail_map_thumb.webp", 1000)
        retry(shutil_copy, RELEASE / "rail_poster.pdf", SITE / "downloads" / "rail_map.pdf")
