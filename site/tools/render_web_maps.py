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

RENAME = {"t_map.png": "system_map.png", "t_map.pdf": "system_map.pdf"}
_save = Figure.savefig


def safe_save(self, fname, *a, **kw):
    name = RENAME.get(Path(fname).name, Path(fname).name)
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
import make_ferry_poster as FP  # noqa: E402

assert M.WEB, "web mode did not switch on"
LP.OUT = WEB
FP.OUT = WEB

want = set(sys.argv[1:]) or {"main", *LP.LAYOUTS, "ferry"}
if "main" in want:
    M.main()
for k in LP.LAYOUTS:
    if k in want:
        LP.main(k)
if "ferry" in want:
    for leg in M.FERRY_LEGS:
        if leg.get("poster") is False:
            continue
        try:
            (FP.draw_loop if leg["kind"] == "loop" else FP.draw_strip)(leg)
        except SystemExit as e:
            print(e)
