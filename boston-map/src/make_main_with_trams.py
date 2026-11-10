"""The full-color NERTA main map with the tram network drawn over it (Max, November 8: "I also want to see a rendering of
the main map with trams too"). A preview, not a final.

make_tmap.main() saves straight over output/t_map.png and t_map.pdf. Here Figure.savefig is swapped for a guard before
main() runs: the guard keeps the figure, writes nothing, and stops main() the moment it asks for any path in
boston-map/output/ outside output/copies/. The finished map goes to output/copies/main_with_trams_vN.png (600 dpi) and .pdf
under the next free N, never over an existing file.

Usage: python make_main_with_trams.py [--dpi 600] [--draft FOLDER] [--crops]
"""
import argparse
import math
import os
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.figure  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon  # noqa: E402
import matplotlib.patheffects as pe  # noqa: E402
from matplotlib.collections import PathCollection  # noqa: E402
from shapely.geometry import LineString, Point, box  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
OUTPUT = (DAY / "output").resolve()
COPIES = (OUTPUT / "copies").resolve()
sys.path.insert(0, str(HERE))


class GuardStop(Exception):
    """make_tmap.main() asked to save into output/: stopped before anything was written."""


_real_savefig = matplotlib.figure.Figure.savefig
CAPTURED = []


def _guarded(fname):
    p = Path(os.fspath(fname)).resolve()
    inside = p == OUTPUT or OUTPUT in p.parents
    in_copies = p == COPIES or COPIES in p.parents
    return inside and not in_copies


def _guard_savefig(self, fname, *a, **k):
    CAPTURED.append(self)
    if _guarded(fname):
        raise GuardStop(str(fname))
    raise GuardStop(f"unexpected save to {fname}; nothing written")


def safe_save(fig, path, **k):
    path = Path(path)
    if _guarded(path):
        raise RuntimeError(f"refusing to write {path}: inside output/ but not output/copies/")
    if path.exists():
        raise RuntimeError(f"refusing to overwrite {path}")
    _real_savefig(fig, path, **k)


def next_free(folder, stem="main_with_trams_v"):
    n = 1
    while (folder / f"{stem}{n}.png").exists() or (folder / f"{stem}{n}.pdf").exists():
        n += 1
    return f"{stem}{n}"


def finish(fig, M, args, out_dir, before, tmap_png, t0, summary):
    stem = args.name or next_free(out_dir)
    safe_save(fig, out_dir / f"{stem}.png", dpi=args.dpi, facecolor=M.PAPER)
    safe_save(fig, out_dir / f"{stem}.pdf", facecolor=M.PAPER)
    print("wrote", out_dir / f"{stem}.png", "and .pdf")
    after = tmap_png.stat().st_mtime if tmap_png.exists() else None
    assert before == after, "output/t_map.png changed!"
    print(f"t_map.png modification time unchanged: {time.ctime(before) if before else 'no file'}")
    print(summary)
    if args.crops:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(out_dir / f"{stem}.png")
        pxu = im.width / (M.XLIM[1] - M.XLIM[0])
        for name, (cx, cy, hw, hh) in {"nubian": (80, 54, 14, 10), "harvard": (64, 122, 14, 10), "quincy": (122, 20, 16, 12),
                                       "downtown": (110, 100, 16, 12)}.items():
            bx = (int((cx - hw - M.XLIM[0]) * pxu), int((M.YLIM[1] - cy - hh) * pxu), int((cx + hw - M.XLIM[0]) * pxu), int((M.YLIM[1] - cy + hh) * pxu))
            p_ = out_dir / f"{stem}_crop_{name}.png"
            if not p_.exists():
                im.crop(bx).save(p_)
                print("crop", p_)
    print(f"done in {time.time() - t0:.0f} s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--draft", default=None, help="write to this folder instead of output/copies")
    ap.add_argument("--crops", action="store_true")
    ap.add_argument("--name", default=None, help="file stem (default main_with_trams_vN, the next free N); never overwrites")
    ap.add_argument("--full", action="store_true", help="v1 style: 3 pt trams with casing, stop crosses, names and badges")
    ap.add_argument("--w", type=float, default=None, help="tram line width in points (the T lines are 9)")
    args = ap.parse_args()
    t0 = time.time()

    tmap_png = OUTPUT / "t_map.png"
    before = tmap_png.stat().st_mtime if tmap_png.exists() else None

    matplotlib.figure.Figure.savefig = _guard_savefig
    try:
        import make_tmap as M
        try:
            M.main()
        except GuardStop as e:
            print("guard stopped make_tmap.main() before it wrote", e)
    finally:
        matplotlib.figure.Figure.savefig = _real_savefig
    if not CAPTURED:
        raise SystemExit("make_tmap.main() never reached savefig; no figure captured")
    fig = CAPTURED[0]
    ax = fig.axes[0]

    import tram_merge as TM
    import make_tram_map as TMM

    ppu = 72 * fig.get_figwidth() / (M.XLIM[1] - M.XLIM[0])   # 4.836 points per unit on the main map
    # Max on v1: "it dominates the map way too much, it should only be a thin pink line with pink triangle outlines in a tiny
    # black strip". The default is now that light background network; --full keeps the v1 look.
    w = args.w or (3.0 if args.full else 1.2)
    routes, dropped = TMM.map_routes()
    lay = TM.Layout(ppu, routes=routes, sheet=(M.XLIM[0], M.XLIM[1], M.YLIM[0], M.YLIM[1]), w=w)
    st = lay.st
    # the main map's own sizes, so the trams keep clear of what is really drawn there
    st.NW = M.LW * 1.14 / ppu
    st.CW = 3.1 / ppu
    st.DOT = M.LW * 0.62 / 2 / ppu + 0.4 / ppu
    st.R = 1.15 * w / ppu if args.full else 2.3 / ppu   # lite: a 4 pt triangle's reach
    st.GAP = 1.2 / ppu
    lay.run(sea=M.SEA, passes=2)
    for p_ in dict.fromkeys(lay.problems):
        print("  layout:", p_)

    PINK, INK, PAPER, WHITE = TMM.PINK, TMM.INK, M.PAPER, "white"
    if not args.full:
        # under the T lines, station dots, labels, pills and the Key; above the water and commuter rail
        for rid in sorted(lay.lines, key=lay.net.rank.get):
            xy = lay.lines[rid]
            if len(xy) > 1:
                ax.plot(*xy.T, color=PINK, lw=w, zorder=4.2, solid_capstyle="round", solid_joinstyle="round")
                ax.plot(*xy.T, color=INK, lw=0.25, zorder=4.21, solid_capstyle="butt", solid_joinstyle="round")
        side = 4.0 / ppu   # a level triangle, point up, 4 pt across, centered on the line
        hgt = side * math.sqrt(3) / 2
        n_sym = 0
        for k, s in lay.stops.items():
            if s["kind"] == "transfer":   # at a NERTA station the station's own dot is the stop
                continue
            cx, cy = s["center"]
            tri = [(cx - side / 2, cy - hgt / 3), (cx + side / 2, cy - hgt / 3), (cx, cy + 2 * hgt / 3)]
            ax.add_patch(Polygon(tri, closed=True, fc=WHITE, ec=PINK, lw=0.7, zorder=4.25, joinstyle="miter"))
            n_sym += 1
        # Key entry (Max, November 8: "not seeing trams labelled in the key"): a tram sample on the Key's title row
        ky, kx = 57.4, 186.0
        ax.plot([kx, kx + 7.0], [ky, ky], color=PINK, lw=w * 1.6, zorder=12.2, solid_capstyle="round")
        ax.plot([kx, kx + 7.0], [ky, ky], color=INK, lw=0.3, zorder=12.21, solid_capstyle="butt")
        tx, sd = kx + 3.5, 5.0 / ppu * 1.4
        hg = sd * math.sqrt(3) / 2
        ax.add_patch(Polygon([(tx - sd / 2, ky - hg / 3), (tx + sd / 2, ky - hg / 3), (tx, ky + 2 * hg / 3)], closed=True,
                             fc=WHITE, ec=PINK, lw=0.8, zorder=12.25, joinstyle="miter"))
        ax.text(kx + 8.6, ky, "Tram line and stop", fontsize=9.6, va="center", color=INK, zorder=12.3)
        out_dir = Path(args.draft) if args.draft else COPIES
        out_dir.mkdir(parents=True, exist_ok=True)
        finish(fig, M, args, out_dir, before, tmap_png, t0,
               f"{len(lay.net.routes)} routes; {n_sym} tram stop triangles; "
               f"{sum(1 for s in lay.stops.values() if s['kind'] == 'transfer')} more at NERTA stations, shown by the station dot")
        return
    # trams: above the water and the T lines, under every station dot and label; a thin paper casing keeps them apart
    order = sorted(lay.lines, key=lay.net.rank.get)
    for rid in order:
        xy = lay.lines[rid]
        if len(xy) > 1:
            ax.plot(*xy.T, color=PAPER, lw=w + 1.2, zorder=5.6, solid_capstyle="round", solid_joinstyle="round")
    for rid in order:
        xy = lay.lines[rid]
        if len(xy) > 1:
            ax.plot(*xy.T, color=PINK, lw=w, zorder=5.7, solid_capstyle="round", solid_joinstyle="round")
            ax.plot(*xy.T, color=INK, lw=max(0.25, st.hair_pt), zorder=5.75, solid_capstyle="butt", solid_joinstyle="round")
    n_sym = 0
    for k, s in lay.stops.items():
        if s["kind"] == "transfer":   # at a NERTA station the station's own dot is the stop
            continue
        TMM.stop_symbol(ax, s["center"], s["r"], TMM.snap_dir(s["dir"]), False, st, ppu, z=7.6)
        n_sym += 1

    # what is already on the map: text, station dots, the Key and other boxes
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()

    def dbox(ext):
        (x0, y0), (x1, y1) = inv.transform([(ext.x0, ext.y0), (ext.x1, ext.y1)])
        return box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
    obst = []
    for t in ax.texts:
        if t.get_visible() and t.get_text().strip():
            obst.append(dbox(t.get_window_extent(rend)).buffer(0.15))
    for c in ax.collections:
        if isinstance(c, PathCollection):
            sizes = c.get_sizes()
            for i, off in enumerate(c.get_offsets()):
                sz = sizes[i if i < len(sizes) else 0] if len(sizes) else 30
                obst.append(Point(off).buffer(math.sqrt(sz) / 2 / ppu + 0.2))
    for p_ in ax.patches:
        if isinstance(p_, (FancyBboxPatch, Circle)) and p_.get_zorder() >= 6:
            b_ = dbox(p_.get_window_extent(rend))
            if b_.area < 0.4 * (M.XLIM[1] - M.XLIM[0]) * (M.YLIM[1] - M.YLIM[0]):
                obst.append(b_)
    stops = lay.stops
    keys = list(stops)
    sym = {k: Point(stops[k]["center"]).buffer(stops[k]["r"] * st.ARM + 0.1) for k in keys}
    obst += [sym[k] for k in keys if stops[k]["kind"] != "transfer"]
    # the T lines, commuter rail and the trams themselves: badges and names keep off them on this busy map
    for _c, xy, kind in lay.geo:
        obst.append(LineString(xy).buffer((st.NW if kind == "T" else st.CW) / 2 + 0.1))
    n_fixed = len(obst)
    for xy in lay.lines.values():   # tram lines: badges keep off them; a name may cross one under its paper halo
        if len(xy) > 1:
            obst.append(LineString(xy).buffer(st.W / 2 + 0.15))
    placed = []
    centers = np.array([stops[k]["center"] for k in keys])

    def free(b, own=None, trams=True):
        if any(g.intersects(b) for g in placed):
            return False
        for g in otree.query(b):
            if not trams and g >= n_fixed:
                continue
            if obst[g] is not own and obst[g].intersects(b):
                return False
        return True

    def own_nearest(b, k, margin=0.3):
        q = b.centroid
        d = np.hypot(centers[:, 0] - q.x, centers[:, 1] - q.y)
        e = [Point(c).distance(b) for c in centers]
        i = keys.index(k)
        for j in np.argsort(d)[:8]:
            if j != i and (d[j] < d[i] + margin or e[j] < e[i] + margin * 0.5):
                return False
        return True
    otree = STRtree(obst)

    # route badges at each route's end, where they fit
    fsb, hb = 4.6, 6.6 / ppu
    n_badges, badge_left = 0, []
    for k, rids in lay.route_ends.items():
        if k not in stops:
            continue
        rids = sorted(set(rids), key=lay.net.rank.get)
        ws = [max(hb * 1.25, (TMM.tw(x, fsb, True) + 3.2) / ppu) for x in rids]
        gap = 0.7 / ppu
        bw, bh = sum(ws) + gap * (len(ws) - 1), hb
        c, r = np.asarray(stops[k]["center"]), stops[k]["r"]
        rr = r * st.ARM + (0.3 if stops[k]["kind"] == "transfer" else 0.1)
        done = False
        for extra in (0.15, 0.6, 1.1, 1.8, 2.6):
            for ang in range(0, 360, 30):
                e = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
                tt = rr + extra
                cx, cy = c + e * (tt + abs(e[0]) * bw / 2 + abs(e[1]) * bh / 2)
                b = box(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
                if not free(b, sym.get(k)) or not own_nearest(b, k):
                    continue
                x = cx - bw / 2
                for rid, wd in zip(rids, ws):
                    ax.add_patch(FancyBboxPatch((x, cy - bh / 2), wd, bh, boxstyle=f"round,pad=0,rounding_size={bh / 2}",
                                                fc=PINK, ec=PAPER, lw=0.5, zorder=12.4))
                    ax.text(x + wd / 2, cy - 0.04 * bh, rid, fontsize=fsb, fontweight="bold", color=WHITE, ha="center", va="center", zorder=12.5)
                    x += wd + gap
                placed.append(b.buffer(0.1))
                n_badges += 1
                done = True
                break
            if done:
                break
        if not done:
            badge_left.append(stops[k]["name"])

    # tram stop names: small, only where they fit cleanly beside their own stop
    fsn = 4.8
    n_names, name_left = 0, []
    dens = [int(np.sum(np.hypot(*(centers - stops[k]["center"]).T) < 6)) for k in keys]
    for i in np.argsort(dens):
        k = keys[i]
        s = stops[k]
        if s["kind"] == "transfer":
            continue
        c, r = np.asarray(s["center"]), s["r"] * st.ARM
        best = None
        for text in (s["name"], s["name"].replace(" ", "\n", 1)):
            lines_ = text.split("\n")
            tw_ = max(TMM.tw(t, fsn) for t in lines_) / ppu
            th = fsn * 1.15 * len(lines_) / ppu
            for side, (dx, dy), ha, va in (("r", (1, 0), "left", "center"), ("l", (-1, 0), "right", "center"),
                                            ("t", (0, 1), "center", "bottom"), ("b", (0, -1), "center", "top")):
                x, y = c + np.array([dx, dy]) * (r + 0.25)
                x0 = x if ha == "left" else x - tw_ if ha == "right" else x - tw_ / 2
                y0 = y - th / 2 if va == "center" else y if va == "bottom" else y - th
                b = box(x0, y0, x0 + tw_, y0 + th)
                if free(b, sym[k], trams=False) and own_nearest(b, k, 0.4):
                    best = (x, y, ha, va, text, b)
                    break
            if best:
                break
        if best is None:
            name_left.append(s["name"])
            continue
        x, y, ha, va, text, b = best
        ax.text(x, y, text, fontsize=fsn, color=INK, ha=ha, va=va, zorder=12.3, linespacing=0.95,
                path_effects=[pe.withStroke(linewidth=1.6, foreground=PAPER)])
        placed.append(b.buffer(0.08))
        n_names += 1

    out_dir = Path(args.draft) if args.draft else COPIES
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = next_free(out_dir)
    safe_save(fig, out_dir / f"{stem}.png", dpi=args.dpi, facecolor=PAPER)
    safe_save(fig, out_dir / f"{stem}.pdf", facecolor=PAPER)
    print("wrote", out_dir / f"{stem}.png", "and .pdf")
    after = tmap_png.stat().st_mtime if tmap_png.exists() else None
    assert before == after, "output/t_map.png changed!"
    print(f"t_map.png modification time unchanged: {time.ctime(before) if before else 'no file'}")
    print(f"{len(lay.net.routes)} routes; {n_sym} tram stop symbols ({sum(1 for s in stops.values() if s['kind'] == 'transfer')} more at NERTA stations, drawn as the station);"
          f" {n_names} names, {len(name_left)} names left off; {n_badges} badge rows, {len(badge_left)} left off")
    print("badges left off:", ", ".join(badge_left))
    if args.crops:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(out_dir / f"{stem}.png")
        pxu = im.width / (M.XLIM[1] - M.XLIM[0])
        for name, (cx, cy, hw, hh) in {"nubian": (80, 54, 14, 10), "harvard": (64, 122, 14, 10), "quincy": (122, 20, 16, 12),
                                       "downtown": (110, 100, 16, 12)}.items():
            bx = (int((cx - hw - M.XLIM[0]) * pxu), int((M.YLIM[1] - cy - hh) * pxu), int((cx + hw - M.XLIM[0]) * pxu), int((M.YLIM[1] - cy + hh) * pxu))
            p_ = out_dir / f"{stem}_crop_{name}.png"
            if not p_.exists():
                im.crop(bx).save(p_)
                print("crop", p_)
    print(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
