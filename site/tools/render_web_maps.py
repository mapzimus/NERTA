"""Render the nerta.fun versions of the maps: no hashtag, Day 8 tag, disclaimer or sources; Max's name under NERTA; @mapzimus.

    python site/tools/render_web_maps.py            # main map, eight line posters, ferry posters
    python site/tools/render_web_maps.py main red   # just some of them

Every file goes to boston-map/output/copies/web/. Any save aimed anywhere else is redirected there, and an existing
file is never overwritten: delete it by hand first if a fresh render is wanted.
"""
import os
import sys
from pathlib import Path

os.environ["NERTA_WEB"] = "1"  # read by make_tmap.WEB at import

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "boston-map" / "src"
WEB = REPO / "boston-map" / "output" / "copies" / "web"
WEB.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SRC))

import re  # noqa: E402

RENAME = {"t_map.png": "system_map.png", "t_map.pdf": "system_map.pdf"}
_save = Figure.savefig


def web_name(fname):
    n = RENAME.get(Path(fname).name, Path(fname).name)
    return re.sub(r"^(ferry_network|rail_poster)_v\d+", r"\1", n)  # versioned working names become one stable web name


def safe_save(self, fname, *a, **kw):
    name = web_name(fname)
    dest = WEB / name
    if dest.exists():
        print("skip, exists:", dest.name)
        return
    if name == "system_map.png":
        kw["dpi"] = 600  # print quality, like the release set
    _save(self, dest, *a, **kw)
    print("written", dest.relative_to(REPO))


Figure.savefig = safe_save

import make_tmap as M  # noqa: E402
import make_line_poster as LP  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from station_kit import INK  # noqa: E402

assert M.WEB, "web mode did not switch on"
LP.OUT = WEB

# The ferry network and rail posters are other sessions' work in progress, so their files aren't edited for web mode.
# Instead, while they draw, credit text is swapped on the way to the page and Max's name goes under the NERTA mark.
_text = Axes.text


def web_text(self, x, y, s, *a, **kw):
    s = str(s)
    if "30DayMapChallenge" in s or "Utopia" in s:
        s = ""
    elif s.strip() == "Map: Maxwell Howe":
        s, kw = "@mapzimus", {**kw, "color": "#b9b9b4", "fontweight": "bold"}
    s = s.replace(" Not affiliated with the MBTA.", "").replace("Not affiliated with the MBTA.", "")
    if "MBTA" in s:
        print("WARNING, MBTA still in text:", s)
    return _text(self, x, y, s, *a, **kw)


def with_name(draw):
    def wrapped(ax, cx, top, width, *a, **kw):
        bottom = draw(ax, cx, top, width, *a, **kw)
        _text(ax, cx, bottom - 1.0, "Maxwell Howe", fontsize=8.4, color=INK, ha="center", va="top", zorder=13)
        return bottom
    return wrapped


def borrowed(module_name):
    """Run another script's main() in web mode, saving into copies/web/."""
    mod = __import__(module_name)
    mod.OUT = WEB
    mod.draw_nerta = with_name(mod.draw_nerta)
    Axes.text = web_text
    try:
        mod.main()
    finally:
        Axes.text = _text


want = set(sys.argv[1:]) or {"main", *LP.LAYOUTS, "ferry"}
if "main" in want:
    M.main()
for k in LP.LAYOUTS:
    if k in want:
        LP.main(k)
if "ferry" in want:
    borrowed("make_ferry_network")
if "rail" in want:  # not in the default set until the rail poster is finished
    borrowed("make_rail_poster")
