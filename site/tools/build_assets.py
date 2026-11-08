"""Build the website's data and images from the map code and the finished release files.

    python site/tools/build_assets.py

Reads only. Writes only inside site/: stops.json, logo SVGs, and web-sized copies of the release maps.
Nothing in boston-map/output/ is touched.
"""
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from PIL import Image

SITE = Path(__file__).resolve().parents[1]
REPO = SITE.parent
SRC = REPO / "boston-map" / "src"
RELEASE = REPO / "boston-map" / "output" / "copies" / "release_2026-11-08"
FERRY = REPO / "boston-map" / "output" / "copies" / "hq_2026-11-07"
sys.path.insert(0, str(SRC))

import make_tmap as M  # noqa: E402  (import only; main() is never called, so nothing is drawn or saved)
from nerta_mark import draw_nerta, draw_t  # noqa: E402
from station_kit import INK, WHITE, place, rounded  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
OUT = SITE / "assets"
(OUT / "maps").mkdir(parents=True, exist_ok=True)
(OUT / "logo").mkdir(parents=True, exist_ok=True)

LINE_KEY = {M.RED: "red", M.ORANGE: "orange", M.BLUE: "blue", M.GREEN: "green", M.YELLOW: "yellow",
            M.CYAN: "cyan", M.INDIGO: "indigo", M.SILVER: "silver"}
LINE_COLOR = {v: k for k, v in LINE_KEY.items()}


def clean(name):
    """Map labels carry layout marks: trailing * or +, hair spaces, line breaks."""
    name = name.rstrip("*+").replace(" ", "").replace("\n", " ")
    name = re.sub(r"\s+", " ", name).strip()
    # The map labels Mass Ave as MIT (keeps it apart from Orange's Mass. Ave); the posters show State as Boston Central.
    return {"Mass Ave": "MIT", "State": "Boston Central"}.get(name, name)


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("'", "")).strip("-")


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
    def one(path, colors):
        fig = plt.figure(figsize=(2.2, 2.9))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(-11, 11)
        ax.set_ylim(-18, 11)
        ax.set_aspect("equal")
        ax.set_axis_off()
        tr = 7.6
        ax.add_patch(Circle((0, 0), tr, fc=WHITE, ec=INK, lw=4.5 * 2.2 / 3.73, zorder=12))
        draw_t(ax, 0, 0, tr, colors)
        ro = tr + 0.6
        draw_nerta(ax, 0, -ro - 1.0, 2 * ro, "B", colors=colors)
        fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.02)
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
        fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.02)
        plt.close(fig)

    system = (M.RED, M.ORANGE, M.YELLOW, M.BLUE, M.ROUTE_COLOR["inner-harbor"], M.CYAN, M.SILVER, M.HSR, M.INDIGO,
              M.CR_TEXT_COLOR, M.GREEN)
    one(OUT / "logo" / "nerta.svg", system)
    roundel_only(OUT / "logo" / "t.svg", system)
    for col, key in LINE_KEY.items():
        roundel_only(OUT / "logo" / f"t_{key}.svg", (col,))


def web_image(src, dst, width, quality=82):
    im = Image.open(src).convert("RGB")
    h = round(im.height * width / im.width)
    im.resize((width, h), Image.LANCZOS).save(dst, "WEBP", quality=quality, method=6)
    return im.size, (width, h)


def maps():
    sizes = {}
    full, web = web_image(RELEASE / "current_map.png", OUT / "maps" / "system_map.webp", 6000, 80)
    web_image(RELEASE / "current_map.png", OUT / "maps" / "system_map_thumb.webp", 900)
    sizes["system"] = {"width": web[0], "height": web[1]}
    for key in LINE_KEY.values():
        web_image(RELEASE / f"line_{key}.png", OUT / "maps" / f"line_{key}.webp", 2400)
        web_image(RELEASE / f"line_{key}.png", OUT / "maps" / f"line_{key}_thumb.webp", 700)
    for f in sorted(FERRY.glob("ferry5_*.png")):
        web_image(f, OUT / "maps" / f"{f.stem}.webp", 2400)
        web_image(f, OUT / "maps" / f"{f.stem}_thumb.webp", 700)
    return sizes


def downloads():
    """Full-quality files for the Download links: vector PDFs and the 600 dpi system map PNG."""
    import shutil
    dl = SITE / "downloads"
    dl.mkdir(exist_ok=True)
    shutil.copyfile(RELEASE / "current_map.pdf", dl / "system_map.pdf")
    shutil.copyfile(RELEASE / "current_map.png", dl / "system_map.png")
    for key in LINE_KEY.values():
        shutil.copyfile(RELEASE / f"line_{key}.pdf", dl / f"line_{key}.pdf")


if __name__ == "__main__":
    downloads()
    stops, segments = stops_and_lines()
    logos()
    sizes = maps()
    data = {"extent": {"x": list(M.XLIM), "y": list(M.YLIM)}, "image": sizes["system"],
            "lineColors": LINE_COLOR, "stops": sorted(stops.values(), key=lambda s: s["name"]), "segments": segments}
    (SITE / "data").mkdir(exist_ok=True)
    (SITE / "data" / "network.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(len(stops), "stops,", len(segments), "segments")
