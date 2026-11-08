"""Export finished NERTA maps at social media sizes.

Usage:
    python export_social.py [--carousel | --no-carousel] [--grid CxR] <out_dir> <image.png> [more.png ...]

For each input this writes six files, named from the input stem:
    <stem>_feed.jpg         1440 px wide, 4:5 at most (padded with paper,
                            never cropped), under 2 MB. Facebook, Threads,
                            LinkedIn, X.
    <stem>_ig_feed.jpg      1080x1350 (4:5), padded, under 8 MB. Instagram
                            feed from the app, the API or a scheduler.
    <stem>_ig_portrait.jpg  1080x1440 (3:4), padded, under 8 MB. Instagram
                            feed, app upload only (the API and schedulers
                            still take 4:5 at most).
    <stem>_tiktok.jpg       1080x1920 (9:16), padded, map centered, under
                            8 MB. TikTok photo post and Instagram Stories.
    <stem>_zoom.jpg         poster's own ratio, 4000 px long edge, under 2 MB
                            (5 MB fallback). Bluesky, X second image.
    <stem>_full.png         poster's own ratio, long edge up to 6000 px,
                            under 20 MB. Reddit and archive.

Every JPEG is sRGB, 4:4:4, progressive, at the highest quality from 95
down to 80 that fits its cap. Padding is the map's paper color.

Carousels (on by default for inputs wider than 3000 px; --carousel forces
them on, --no-carousel off). The map is cut into an overlapping grid of tiles
(at least 10% overlap), ordered left to right, top to bottom, sized so the
smallest station names come out about 14 px tall (cap height) at 1080 wide.
--grid CxR sets the columns and rows by hand. Each tile is written twice:
    <stem>_ig_carousel_NN.jpg      1080x1350 (4:5) region of the map
    <stem>_tiktok_carousel_NN.jpg  1080x1920 (9:16) region, same width and
                                   center, taller (shifted to stay on the map)
NN is the slide number. Slide 01 of each carousel is the whole map
(<stem>_ig_feed.jpg or <stem>_tiktok.jpg), so the disclaimer is always on
the first slide; tiles start at 02. A tile is dropped only when the part of
it that no other kept tile covers is under 0.3% ink (non-paper pixels), so
it shows nothing new; kept tiles are numbered on without gaps. A carousel holds
at most 20 slides (Instagram's limit; TikTok allows 35).

It also writes MANIFEST.txt. Nothing is ever overwritten: a taken name gets
_v2, _v3 and so on. The script only reads the input images and
make_tmap.py; it never touches boston-map/output/.
"""

import argparse
import io
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

Image.MAX_IMAGE_PIXELS = None  # 600 dpi posters are over Pillow's default limit

MAKE_TMAP = Path(__file__).resolve().parent.parent / "src" / "make_tmap.py"
SPEC_NOTE = ("Size specs come from research/social-media-sizes-2026-11-07.md (checked 2026-11-07, "
             "Instagram and TikTok section added 2026-11-08). "
             "X's crop point and Reddit's limits are unverified. "
             "Instagram 3:4 works in the app only; post ig_feed through a scheduler.")

MB = 1_000_000  # decimal MB, the stricter reading of each platform cap
FEED_W = 1440
FEED_TALLEST = 4 / 5     # width / height
FEED_WIDEST = 1.91
FEED_CAP = 2 * MB
ZOOM_EDGE = 4000
ZOOM_CAP = 2 * MB        # Bluesky
ZOOM_FALLBACK_CAP = 5 * MB  # X
FULL_EDGE = 6000
FULL_CAP = 20 * MB       # Reddit
FULL_STEP = 500
Q_HIGH, Q_FLOOR = 95, 80

# Fixed-size boxes: (width, height, byte cap). The map is scaled to fit inside
# and padded with paper, never cropped. 8 MB is Instagram's API cap for feed and
# Story images; TikTok allows 20 MB a photo, so 8 MB covers both.
BOXES = {
    "ig_feed": (1080, 1350, 8 * MB),      # 4:5
    "ig_portrait": (1080, 1440, 8 * MB),  # 3:4
    "tiktok": (1080, 1920, 8 * MB),       # 9:16
}


# Carousel tiles. Slide 1 is the whole map, so tiles fill the other slides.
IG_CAROUSEL_MAX = 20     # Instagram app and API
TIKTOK_PHOTOS_MAX = 35   # TikTok photo post
MAX_TILES = min(IG_CAROUSEL_MAX, TIKTOK_PHOTOS_MAX) - 1
CAROUSEL_MIN_W = 3000    # px; carousels are on by default above this width
OVERLAP = 0.10
TILE_CAP = 8 * MB
TILE_SHAPES = {          # kind: (width, height, whole-map slide 1)
    "ig_carousel": (1080, 1350, "ig_feed"),
    "tiktok_carousel": (1080, 1920, "tiktok"),
}
CAROUSEL_LABELS = {
    "ig_carousel": "Instagram carousel",
    "tiktok_carousel": "TikTok photo post",
}
# Station-name size. The main map's names are 9.4 pt (master: 400 dpi PNG from
# its PDF, about 7400 px wide, an 18.5 in sheet); posters are 600 dpi with
# 8.8 to 9.6 pt names. Plan for the smallest, 8.8 pt, in Arial (cap height
# 0.716 of the point size). The dpi comes from the PNG's own dpi tag; without
# one it is estimated from the pixel width as an 18.5 in wide sheet.
NAME_PT = 8.8
CAP_PER_PT = 0.716
SHEET_IN = 18.5
MIN_CAP = 14             # px cap height wanted at 1080 wide
PAPER_TOL = 8            # a pixel within this of paper on every channel counts as paper
MIN_UNIQUE_INK = 0.003   # drop a tile whose uncovered part is under 0.3% ink
INK_STEP = 4             # ink is counted in 4x4 px blocks

PLATFORMS = {
    "feed": "Facebook, Threads, LinkedIn, X",
    "ig_feed": "Instagram feed 4:5 (app, API or scheduler)",
    "ig_portrait": "Instagram feed 3:4 (app upload only; schedulers crop to 4:5)",
    "tiktok": "TikTok photo post, Instagram Stories",
    "zoom": "Bluesky, X second image",
    "full": "Reddit and archive",
}


def read_paper():
    """Find PAPER in make_tmap.py by text search, so this tool never imports the map build.

    Handles both PAPER = "#fcfcfa" and PAPER, WATER, COAST = "#fcfcfa", ...
    """
    text = MAKE_TMAP.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.lstrip().startswith("#") or "=" not in line or "==" in line:
            continue
        lhs, rhs = line.split("=", 1)
        names = [n.strip() for n in lhs.split(",")]
        if "PAPER" not in names:
            continue
        values = re.findall(r"""["'](#[0-9a-fA-F]{6})["']""", rhs)
        idx = names.index("PAPER")
        if idx < len(values):
            h = values[idx].lstrip("#")
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    sys.exit(f"Could not find PAPER = \"#rrggbb\" in {MAKE_TMAP}")


def srgb_profile():
    """Return (sRGB ICC bytes, ImageCms module) or (None, None) if unavailable."""
    try:
        from PIL import ImageCms
        return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes(), ImageCms
    except Exception:
        return None, None


def to_rgb(im, paper, icc, cms):
    """Flatten alpha onto paper and convert any embedded profile to sRGB."""
    src_icc = im.info.get("icc_profile")
    if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, paper + (255,))
        im = Image.alpha_composite(bg, im).convert("RGB")
    else:
        im = im.convert("RGB")
    if src_icc and cms and icc:
        try:
            src = cms.ImageCmsProfile(io.BytesIO(src_icc))
            dst = cms.ImageCmsProfile(io.BytesIO(icc))
            im = cms.profileToProfile(im, src, dst, outputMode="RGB")
        except Exception:
            pass  # keep pixels as they are
    return im


def unique_path(out_dir, name):
    p = out_dir / name
    n = 2
    while p.exists():
        p = out_dir / f"{Path(name).stem}_v{n}{Path(name).suffix}"
        n += 1
    return p


def fit_long_edge(im, edge):
    """Scale so the long edge is `edge`, never upscaling."""
    w, h = im.size
    s = edge / max(w, h)
    if s >= 1:
        return im
    return im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)


def jpeg_bytes(im, q, icc):
    buf = io.BytesIO()
    kw = dict(quality=q, subsampling=0, progressive=True, optimize=True)
    if icc:
        kw["icc_profile"] = icc
    im.save(buf, "JPEG", **kw)
    return buf.getvalue()


def best_jpeg(im, cap, icc):
    """Highest quality in [Q_FLOOR, Q_HIGH] under cap. Returns (bytes, q, fits)."""
    data = jpeg_bytes(im, Q_HIGH, icc)
    if len(data) <= cap:
        return data, Q_HIGH, True
    floor = jpeg_bytes(im, Q_FLOOR, icc)
    if len(floor) > cap:
        return floor, Q_FLOOR, False
    lo, hi, best = Q_FLOOR, Q_HIGH - 1, (floor, Q_FLOOR)
    while lo <= hi:
        mid = (lo + hi) // 2
        d = jpeg_bytes(im, mid, icc)
        if len(d) <= cap:
            best, lo = (d, mid), mid + 1
        else:
            hi = mid - 1
    return best[0], best[1], True


def make_feed(im, paper):
    """Pad (never crop) to between 4:5 and 1.91:1, then size to 1440 wide."""
    w, h = im.size
    ratio = w / h
    if ratio < FEED_TALLEST:
        out_ratio = FEED_TALLEST     # too tall: pad left and right
    elif ratio > FEED_WIDEST:
        out_ratio = FEED_WIDEST      # too wide: pad top and bottom
    else:
        out_ratio = ratio
    out_w, out_h = FEED_W, round(FEED_W / out_ratio)
    s = min(out_w / w, out_h / h)
    cw, ch = min(out_w, round(w * s)), min(out_h, round(h * s))
    content = im.resize((cw, ch), Image.LANCZOS)
    if (cw, ch) == (out_w, out_h):
        return content
    canvas = Image.new("RGB", (out_w, out_h), paper)
    canvas.paste(content, ((out_w - cw) // 2, (out_h - ch) // 2))
    return canvas


def make_box(im, out_w, out_h, paper):
    """Fit the whole map inside out_w x out_h, centered, padded with paper. Never crops."""
    w, h = im.size
    s = min(out_w / w, out_h / h)
    cw, ch = min(out_w, round(w * s)), min(out_h, round(h * s))
    content = im.resize((cw, ch), Image.LANCZOS)
    if (cw, ch) == (out_w, out_h):
        return content
    canvas = Image.new("RGB", (out_w, out_h), paper)
    canvas.paste(content, ((out_w - cw) // 2, (out_h - ch) // 2))
    return canvas


def name_cap_px(info, width):
    """Estimated cap height of the smallest station names, in source pixels."""
    dpi = info.get("dpi")
    dpi = float(dpi[0]) if dpi else 0.0
    if dpi > 0 and 4 <= width / dpi <= 40:    # a believable sheet width in inches
        how = f"{dpi:.0f} dpi from the file's tag"
    else:
        dpi = width / SHEET_IN
        how = f"about {dpi:.0f} dpi, estimated from {width} px wide"
    return CAP_PER_PT * NAME_PT / 72 * dpi, how


def tile_size(w, h, cols, rows):
    """Smallest 4:5 tile width that covers w x h with cols x rows at OVERLAP or more."""
    step = 1 - OVERLAP
    return max(w / (1 + step * (cols - 1)), h / (1.25 * (1 + step * (rows - 1))))


def plan_grid(w, h, cap_src, grid=None):
    """Pick (cols, rows, tile width). Fewest tiles that keep names at MIN_CAP px."""
    if grid:
        return grid[0], grid[1], tile_size(w, h, *grid)
    t_max = cap_src * TILE_SHAPES["ig_carousel"][0] / MIN_CAP
    options = [(c, r, tile_size(w, h, c, r))
               for c in range(1, MAX_TILES + 1) for r in range(1, MAX_TILES // c + 1)]
    ok = [o for o in options if o[2] <= t_max]
    if ok:
        return min(ok, key=lambda o: (o[0] * o[1], o[2]))
    return min(options, key=lambda o: (o[2], o[0] * o[1]))  # best we can do in 19 tiles


def spread(n, length, size):
    """Start positions of n windows of `size`, evenly spaced from edge to edge."""
    if n == 1:
        return [(length - size) / 2]
    return [i * (length - size) / (n - 1) for i in range(n)]


def take(im, x0, y0, w, h, paper):
    """Crop a w x h region at (x0, y0); any part off the map is paper."""
    W, H = im.size
    x0, y0, w, h = round(x0), round(y0), round(w), round(h)
    if x0 >= 0 and y0 >= 0 and x0 + w <= W and y0 + h <= H:
        return im.crop((x0, y0, x0 + w, y0 + h))
    canvas = Image.new("RGB", (w, h), paper)
    box = (max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h))
    if box[0] < box[2] and box[1] < box[3]:
        canvas.paste(im.crop(box), (box[0] - x0, box[1] - y0))
    return canvas


def ink_map(im, paper):
    """Ink density per INK_STEP x INK_STEP block (255 = every pixel differs from paper).

    A pixel is ink when any channel is more than PAPER_TOL from the paper color.
    Built in strips so a 600 dpi poster doesn't need several full-size copies.
    """
    W, H = im.size
    k = INK_STEP
    out = Image.new("L", (-(-W // k), -(-H // k)), 0)
    strip = 256 * k
    for y in range(0, H, strip):
        part = im.crop((0, y, W, min(H, y + strip)))
        diff = ImageChops.difference(part, Image.new("RGB", part.size, paper))
        r, g, b = diff.split()
        worst = ImageChops.lighter(ImageChops.lighter(r, g), b)
        ink = worst.point(lambda v: 255 if v > PAPER_TOL else 0)
        out.paste(ink.reduce(k), (0, y // k))
    return out


def unique_ink(ink, rect, others):
    """Share of ink pixels in the part of rect (on the map) that no rect in others covers."""
    k = INK_STEP
    x0, y0 = max(0, round(rect[0] / k)), max(0, round(rect[1] / k))
    x1, y1 = min(ink.width, round(rect[2] / k)), min(ink.height, round(rect[3] / k))
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return 0.0
    free = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(free)
    for o in others:
        a, b = round(o[0] / k) - x0, round(o[1] / k) - y0
        c, d = round(o[2] / k) - x0, round(o[3] / k) - y0
        if c > 0 and d > 0 and a < w and b < h:
            draw.rectangle((a, b, c - 1, d - 1), fill=0)
    area = free.histogram()[255]
    if area == 0:
        return 0.0      # fully covered by other tiles: shows nothing new
    hit = ImageChops.multiply(ink.crop((x0, y0, x1, y1)), free)
    return sum(i * n for i, n in enumerate(hit.histogram())) / 255 / area


def export_carousel(im, info, stem, out_dir, paper, icc, grid, slide1, carousels):
    W, H = im.size
    cap_src, how = name_cap_px(info, W)
    cols, rows, t = plan_grid(W, H, cap_src, grid)
    cap_out = cap_src * TILE_SHAPES["ig_carousel"][0] / t
    print(f"  carousel {stem}: grid {cols}x{rows}, tile {t:.0f} px of {W}; "
          f"smallest names about {cap_out:.0f} px cap height at 1080 wide ({how})")
    if cols * rows == 1:
        print("  NOTE: names are already big enough on the whole map; no tiles written.")
        return
    if cap_out < MIN_CAP - 0.5:
        print(f"  WARNING: names come out under {MIN_CAP} px in these tiles.")

    th = t * 1.25
    tiles = []   # (row, col, x0, y0) of each 4:5 tile, left to right, top to bottom
    for r, y0 in enumerate(spread(rows, H, th), 1):
        for c, x0 in enumerate(spread(cols, W, t), 1):
            tiles.append((r, c, x0, y0))

    # Drop a tile only when the part of it no other kept tile covers is nearly
    # empty, so it shows nothing a reader would miss. Emptiest tiles go first.
    ink = ink_map(im, paper)
    rects = [(x0, y0, x0 + t, y0 + th) for _, _, x0, y0 in tiles]
    kept = set(range(len(tiles)))
    for i in sorted(kept, key=lambda i: unique_ink(ink, rects[i], [])):
        share = unique_ink(ink, rects[i], [rects[j] for j in kept if j != i])
        if share < MIN_UNIQUE_INK:
            kept.discard(i)
            r, c = tiles[i][:2]
            print(f"  dropped tile row {r}, col {c}: {share:.2%} ink outside the other tiles")

    slides = {kind: [(slide1[base], None)] for kind, (_, _, base) in TILE_SHAPES.items()}
    n = 1
    for i, (r, c, x0, y0) in enumerate(tiles):
        if i not in kept:
            continue
        ig_region = take(im, x0, y0, t, th, paper)
        n += 1
        for kind, (ow, oh, _) in TILE_SHAPES.items():
            if kind == "ig_carousel":
                region = ig_region
            else:   # same width and center, taller; kept on the map where it fits
                rh = t * oh / ow
                ry = y0 + th / 2 - rh / 2
                ry = (H - rh) / 2 if rh >= H else min(max(ry, 0), H - rh)
                region = take(im, x0, ry, t, rh, paper)
            tile = region.resize((ow, oh), Image.LANCZOS)
            data, q, fits = best_jpeg(tile, TILE_CAP, icc)
            p = unique_path(out_dir, f"{stem}_{kind}_{n:02d}.jpg")
            nbytes = write(p, data)
            print(f"{p.name:<40} {ow:>5}x{oh:<5} {nbytes / MB:6.2f} MB  q{q}")
            if not fits:
                print(f"  WARNING: {p.name} is over {TILE_CAP // MB} MB even at q{Q_FLOOR}.")
            slides[kind].append((p.name, f"row {r}, col {c}, {nbytes / MB:.2f} MB, q{q}"))
    for kind, items in slides.items():
        carousels.append((stem, kind, cols, rows, cap_out, items))


def write(path, data):
    path.write_bytes(data)
    return len(data)


def report(kind, path, size, nbytes, q, rows):
    qtext = f"q{q}" if q else "png"
    print(f"{path.name:<40} {size[0]:>5}x{size[1]:<5} {nbytes / MB:6.2f} MB  {qtext}")
    rows.append((kind, path.name, size, nbytes, q))


def export_one(src, out_dir, paper, icc, cms, rows, carousel=None, grid=None, carousels=None):
    stem = src.stem
    with Image.open(src) as raw:
        raw.load()
        info = dict(raw.info)
        im = to_rgb(raw, paper, icc, cms)
    slide1 = {}

    # feed
    feed = make_feed(im, paper)
    data, q, fits = best_jpeg(feed, FEED_CAP, icc)
    p = unique_path(out_dir, f"{stem}_feed.jpg")
    report("feed", p, feed.size, write(p, data), q, rows)
    if not fits:
        print(f"  WARNING: {p.name} is over 2 MB even at q{Q_FLOOR}.")

    # Instagram feed (4:5 and 3:4) and TikTok / Stories (9:16)
    for kind, (bw, bh, cap) in BOXES.items():
        box = make_box(im, bw, bh, paper)
        data, q, fits = best_jpeg(box, cap, icc)
        p = unique_path(out_dir, f"{stem}_{kind}.jpg")
        report(kind, p, box.size, write(p, data), q, rows)
        slide1[kind] = p.name
        if not fits:
            print(f"  WARNING: {p.name} is over {cap // MB} MB even at q{Q_FLOOR}.")

    # carousel tiles: on by default for wide masters, forced by --carousel or --grid
    if carousel is None:
        carousel = grid is not None or im.size[0] > CAROUSEL_MIN_W
    if carousel:
        export_carousel(im, info, stem, out_dir, paper, icc, grid, slide1,
                        carousels if carousels is not None else [])

    # zoom
    zoom = fit_long_edge(im, ZOOM_EDGE)
    data, q, fits = best_jpeg(zoom, ZOOM_CAP, icc)
    if not fits:
        data, q, fits = best_jpeg(zoom, ZOOM_FALLBACK_CAP, icc)
        print(f"  WARNING: {stem}_zoom is over Bluesky's 2 MB cap at q{Q_FLOOR}; "
              f"kept under 5 MB for X. Bluesky will recompress it.")
        if not fits:
            print(f"  WARNING: {stem}_zoom is over X's 5 MB cap too.")
    p = unique_path(out_dir, f"{stem}_zoom.jpg")
    report("zoom", p, zoom.size, write(p, data), q, rows)

    # full
    edge = min(FULL_EDGE, max(im.size))
    while True:
        full = fit_long_edge(im, edge)
        buf = io.BytesIO()
        kw = {"optimize": True}
        if icc:
            kw["icc_profile"] = icc
        full.save(buf, "PNG", **kw)
        data = buf.getvalue()
        if len(data) <= FULL_CAP or edge <= FULL_STEP:
            break
        edge -= FULL_STEP
    p = unique_path(out_dir, f"{stem}_full.png")
    report("full", p, full.size, write(p, data), None, rows)
    if len(data) > FULL_CAP:
        print(f"  WARNING: {p.name} is still over 20 MB.")
    elif max(full.size) < ZOOM_EDGE and max(im.size) >= ZOOM_EDGE:
        print(f"  NOTE: {p.name} had to drop below 4000 px to fit 20 MB.")


def write_manifest(out_dir, rows, carousels=()):
    lines = ["NERTA social exports", ""]
    for kind, name, size, nbytes, q in rows:
        qtext = f", JPEG q{q}" if q else ""
        lines.append(f"{name}  {size[0]}x{size[1]}  {nbytes / MB:.2f} MB{qtext}  -> {PLATFORMS[kind]}")
    for stem, kind, cols, rows_, cap_out, items in carousels:
        w, h, _ = TILE_SHAPES[kind]
        count = f"{len(items)} slide{'s' if len(items) != 1 else ''}"
        lines += ["", f"{CAROUSEL_LABELS[kind]} for {stem}: {count} in this order, "
                      f"{w}x{h}, tiles from a {cols}x{rows_} grid (names about {cap_out:.0f} px tall)"]
        for i, (name, note) in enumerate(items, 1):
            lines.append(f"  {i:02d}  {name}  {note or 'whole map, with the disclaimer'}")
    if carousels:
        lines += ["", f"Carousels stay within {IG_CAROUSEL_MAX} slides (Instagram's limit; "
                      f"TikTok allows {TIKTOK_PHOTOS_MAX}). Post the slides in the order listed."]
    lines += ["", SPEC_NOTE, ""]
    p = unique_path(out_dir, "MANIFEST.txt")
    p.write_text("\n".join(lines), encoding="utf-8")
    print(f"{p.name}")


def parse_grid(text):
    m = re.fullmatch(r"\s*(\d+)\s*[xX]\s*(\d+)\s*", text)
    if not m or int(m[1]) < 1 or int(m[2]) < 1:
        raise argparse.ArgumentTypeError(f"--grid wants CxR, like 3x2, not {text!r}")
    c, r = int(m[1]), int(m[2])
    if c * r > MAX_TILES:
        raise argparse.ArgumentTypeError(f"--grid {c}x{r} is {c * r} tiles; the most is {MAX_TILES}")
    return c, r


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("inputs", type=Path, nargs="+")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--carousel", dest="carousel", action="store_true", default=None,
                       help="write carousel tiles (default: only for inputs wider than 3000 px)")
    group.add_argument("--no-carousel", dest="carousel", action="store_false",
                       help="never write carousel tiles")
    ap.add_argument("--grid", type=parse_grid, help="tile grid as columns x rows, like 3x2")
    ap.set_defaults(carousel=None)
    args = ap.parse_intermixed_args(argv[1:])
    if args.grid and args.carousel is False:
        ap.error("--grid and --no-carousel don't go together")
    missing = [str(p) for p in args.inputs if not p.is_file()]
    if missing:
        sys.exit("Not found: " + ", ".join(missing))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    paper = read_paper()
    icc, cms = srgb_profile()
    rows, carousels = [], []
    for src in args.inputs:
        export_one(src, args.out_dir, paper, icc, cms, rows, args.carousel, args.grid, carousels)
    write_manifest(args.out_dir, rows, carousels)


if __name__ == "__main__":
    main(sys.argv)
