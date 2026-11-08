"""Render the maps from the current code, in either version, into a fresh folder. Nothing is ever overwritten.

    python site/tools/render_web_maps.py                        # no-disclaimer (nerta.fun) versions, every released map
    python site/tools/render_web_maps.py --release              # with-disclaimer (posting) versions: the release block stays
    python site/tools/render_web_maps.py --stamp v1.0 all       # a small "v1.0" in the bottom-left corner of every map
    python site/tools/render_web_maps.py main red ferry         # just some of them
    python site/tools/render_web_maps.py rail --into web_v2     # add to an existing run folder

Targets: main, the 8 line keys (red ... silver), ferry (network), ferrylines (14 routes), rail (poster), railregional,
railnetwork, raillines (15 lines), or "all" for every one of those. Trams aren't included until their maps are final.

No-disclaimer runs write to boston-map/output/copies/web_vN/, with-disclaimer runs to copies/release_vN/. Any save aimed
anywhere else is redirected there. The no-disclaimer version has no release block (disclaimer, credit, hashtag, Day 8), puts
"Maxwell Howe" under the NERTA mark and carries @mapzimus; every map script has its own web mode for that (make_tmap.WEB),
and this script fills in only where a script doesn't.
"""
import os
import re
import sys
from pathlib import Path

TRAM_TARGETS = {"trammap", "tramnetwork", "tramdisplay", "trams"}
if TRAM_TARGETS & set(sys.argv) and os.environ.get("PYTHONHASHSEED") != "0":
    # The tram scripts lay out by walking sets of names; a fixed hash seed makes them come out the same as the tram
    # session's own renders (make_tram_poster.py does the same when it runs on its own)
    import subprocess
    os.environ["PYTHONHASHSEED"] = "0"
    sys.exit(subprocess.call([sys.executable] + sys.argv))
RELEASE_MODE = "--release" in sys.argv
if RELEASE_MODE:
    sys.argv.remove("--release")
else:
    os.environ["NERTA_WEB"] = "1"  # read by make_tmap.WEB at import
STAMP = None
if "--stamp" in sys.argv:
    i = sys.argv.index("--stamp")
    STAMP = sys.argv[i + 1]
    del sys.argv[i:i + 2]

import matplotlib  # noqa: E402
matplotlib.use("Agg")
from matplotlib.figure import Figure  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "boston-map" / "src"
COPIES = REPO / "boston-map" / "output" / "copies"
PREFIX = "release_v" if RELEASE_MODE else "web_v"
if "--into" in sys.argv:
    OUTDIR = COPIES / sys.argv[sys.argv.index("--into") + 1]
    del sys.argv[sys.argv.index("--into"):sys.argv.index("--into") + 2]
else:
    v = 2
    while (COPIES / f"{PREFIX}{v}").exists():
        v += 1
    OUTDIR = COPIES / f"{PREFIX}{v}"
OUTDIR.mkdir(parents=True, exist_ok=True)
WEB = OUTDIR  # older name, still used below
print("rendering", "with-disclaimer" if RELEASE_MODE else "no-disclaimer", "versions into", OUTDIR.name, f"(stamp {STAMP})" if STAMP else "")
sys.path.insert(0, str(SRC))

RENAME = {"t_map.png": "system_map.png", "t_map.pdf": "system_map.pdf"}
DPI = {"system_map.png": 400}  # match the finals: the main map is 400 dpi, everything else keeps its script's own
_save = Figure.savefig


def web_name(fname):
    n = RENAME.get(Path(fname).name, Path(fname).name)
    # versioned working names become one stable name
    n = re.sub(r"^(tram_map|tram_network|tram_display)(_web|_nodisc)?_v\d+(_web|_no-disclaimer)?", r"\1", n)
    return re.sub(r"^(ferry_network|rail_poster|rail_network|rail_regional|rail_line_[a-z]+)_v\d+", r"\1", n)


def drop_dig_panel(fig):
    """Max, November 8: nerta.fun reads as canonical Boston, so the site's main map leaves out the Bigger Dig panel (its
    history and costs). make_tmap.py draws the panel inline, so it's found by its heading: the white box starts 2.2 left
    of the heading and 2.0 above it, and is 35.4 wide and 64 tall (make_tmap's DX, DY box). Everything wholly inside goes."""
    for ax in fig.axes:
        head = [t for t in ax.texts if t.get_text() == "The Bigger Dig"]
        if not head:
            continue
        hx, hy = head[0].get_position()
        x0, y1 = hx - 2.2, hy + 2.0
        x1, y0 = x0 + 35.4, y1 - 64.0
        inside = lambda x, y: x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.01 <= y <= y1 + 0.01
        gone = 0
        for t in list(ax.texts):
            if inside(*t.get_position()):
                t.remove(); gone += 1
        for ln in list(ax.lines):
            xs, ys = ln.get_xdata(), ln.get_ydata()
            if len(xs) and all(inside(float(x), float(y)) for x, y in zip(xs, ys)):
                ln.remove(); gone += 1
        for p in list(ax.patches):
            try:
                b = p.get_bbox() if hasattr(p, "get_bbox") else p.get_path().get_extents(p.get_patch_transform())
            except Exception:
                continue
            if inside(b.x0, b.y0) and inside(b.x1, b.y1):
                p.remove(); gone += 1
        print(f"  Bigger Dig panel left out of the site map ({gone} pieces)")
        return True
    return False


def safe_save(self, fname, *a, **kw):
    name = web_name(fname)
    if not RELEASE_MODE and name.startswith("system_map"):
        drop_dig_panel(self)
    dest = OUTDIR / name
    if dest.exists():
        print("skip, exists:", dest.name)
        return
    if name in DPI:
        kw["dpi"] = DPI[name]
    if not RELEASE_MODE and not any("mapzimus" in t.get_text() for ax in self.axes for t in ax.texts) \
            and not any("mapzimus" in t.get_text() for t in self.texts):
        # Every no-disclaimer map carries @mapzimus; if the script drew none, put it faint at the top right
        self.text(0.985, 0.985, "@mapzimus", fontsize=9.6, fontweight="bold", color="#b9b9b4", ha="right", va="top", zorder=20)
    if STAMP and not any(t.get_text() == STAMP for t in self.texts):
        # The version, small and quiet, in the bottom-left corner (Max, November 8). If a box or text already sits in the
        # corner, it slides right along the bottom edge until it's clear.
        stamp = self.text(0.006, 0.006, STAMP, fontsize=8, color="#8a8a90", ha="left", va="bottom", zorder=20, family="Arial")
        try:
            r = self.canvas.get_renderer()
            others = [a.get_window_extent(r) for ax in self.axes for a in list(ax.patches) + list(ax.texts) if a.get_visible()]
            for _ in range(200):
                bb = stamp.get_window_extent(r).expanded(1.15, 1.3)
                hit = [o for o in others if o.overlaps(bb) and o.width < self.bbox.width * 0.9]
                if not hit:
                    break
                x = max(o.x1 for o in hit) / self.bbox.width + 0.004
                stamp.set_x(x)
            print(f"  stamp {STAMP} at x={stamp.get_position()[0]:.3f} of the width")
            if stamp.get_position()[0] > 0.95:
                print("  WARNING: the stamp slid off the bottom edge; putting it back in the corner")
                stamp.set_x(0.006)
        except Exception as e:
            print("  stamp placement check skipped:", e)
    _save(self, dest, *a, **kw)
    print("written", dest.relative_to(REPO))


Figure.savefig = safe_save

import make_tmap as M  # noqa: E402
import make_line_poster as LP  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from station_kit import INK  # noqa: E402

assert M.WEB != RELEASE_MODE, "web mode didn't match the requested version"
LP.OUT = OUTDIR
_text = Axes.text


def with_name(draw):
    """Max's name under the NERTA mark, for a script whose web mode doesn't draw it."""
    def wrapped(ax, cx, top, width, *a, **kw):
        bottom = draw(ax, cx, top, width, *a, **kw)
        if not any(t.get_text() == "Maxwell Howe" for t in ax.texts):
            _text(ax, cx, bottom - 1.0, "Maxwell Howe", fontsize=8.4, color=INK, ha="center", va="top", zorder=13)
        return bottom
    return wrapped


def web_text(self, x, y, s, *a, **kw):
    """For scripts whose web mode still prints it: no-disclaimer maps never mention the MBTA."""
    s = str(s).replace(" Not affiliated with the MBTA.", "").replace("Not affiliated with the MBTA.", "")
    s = re.sub(r"\s*\d{4}\s*[–-]\s*\d{4}", "", s)  # no years on the site (Max, November 8): "US Railroads 1826–1911 GIS" -> "US Railroads GIS"
    if "MBTA" in s:
        print("WARNING, MBTA still in text:", s)
    return _text(self, x, y, s, *a, **kw)


def run(module_name, name_wrapper=False):
    """Run another script's main(), saving into the run folder. Its own arguments are hidden from it."""
    mod = __import__(module_name)
    mod.OUT = OUTDIR
    if name_wrapper and not RELEASE_MODE:
        mod.draw_nerta = with_name(mod.draw_nerta)
    if not RELEASE_MODE:
        Axes.text = web_text
    argv = sys.argv[:]
    sys.argv = sys.argv[:1]
    try:
        mod.main()
    finally:
        sys.argv = argv
        Axes.text = _text


ALL = {"main", *LP.LAYOUTS, "ferry", "ferrylines", "rail", "railregional", "railnetwork", "raillines"}
want = set(sys.argv[1:]) or {"main", *LP.LAYOUTS, "ferry", "ferrylines", "rail", "railregional", "railnetwork", "raillines"}
if "all" in want:
    want = ALL
if "main" in want:
    M.main()
for k in LP.LAYOUTS:
    if k in want:
        LP.main(k)
if "ferry" in want:
    run("make_ferry_network", name_wrapper=True)  # its web mode leaves out the release block but not the name
if "ferrylines" in want:
    import make_ferry_line_posters as FL
    for k in FL.LAYOUTS:
        try:
            FL.main(k, OUTDIR, 600, False)
        except SystemExit as e:  # a route mid-edit in its own session refuses to draw; skip it, keep the rest
            print("  skipped ferry route", k, "-", e)
if "trams" in want:
    want |= {"trammap", "tramnetwork", "tramdisplay"}
for t, mod_name, args in (("trammap", "make_tram_map", ["--web"]), ("tramnetwork", "make_tram_poster", ["--nodisc"]),
                          ("tramdisplay", "make_tram_poster", ["--nodisc", "--display"])):
    if t not in want:
        continue
    if not RELEASE_MODE:
        M.CONCEPT_NOTE = "Maxwell Howe"  # the site has no dates: just Max's name under the mark (@mapzimus is added on save)
    cmd = [sys.executable, __file__, "_tram1", t, "--into", OUTDIR.name] + (["--release"] if RELEASE_MODE else []) + (["--stamp", STAMP] if STAMP else [])
    if "_tram1" in sys.argv:  # this process is the one-tram-map child: draw it here
        if RELEASE_MODE:
            args = [a for a in args if a not in ("--web", "--nodisc")]
        argv = sys.argv[:]
        sys.argv = [mod_name + ".py"] + args  # set before the import: make_tram_poster reads --display at import time
        try:
            mod = __import__(mod_name)
            mod.OUT = OUTDIR
            mod.main()
        finally:
            sys.argv = argv
    else:  # each tram map in its own process, like the rail maps: the poster script keeps module-level state
        import subprocess
        subprocess.run(cmd, check=False)
# The rail scripts build their station lists when they run, so two of them in one process draw every station twice.
# Each one gets its own process, writing into this same run folder.
rail = [t for t in ("raillines", "rail", "railregional", "railnetwork") if t in want]
if len(rail) == 1:
    run({"raillines": "make_rail_line_posters", "rail": "make_rail_poster", "railregional": "make_rail_regional",
         "railnetwork": "make_rail_network"}[rail[0]])
else:
    import subprocess
    for t in rail:
        cmd = [sys.executable, __file__, t, "--into", OUTDIR.name] + (["--release"] if RELEASE_MODE else []) + (["--stamp", STAMP] if STAMP else [])
        subprocess.run(cmd, check=False)
