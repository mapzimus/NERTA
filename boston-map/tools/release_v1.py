"""Release set v1.0 (Max, November 8): every final map in two versions, with and without the disclaimer, each with a
small "v1.0" in its bottom-left corner.

Usage: release_v1.py <slug> [<slug> ...]      (slugs as in boston-map/output/final/, e.g. main-map line-red)

Works from the signed-off vector PDF in output/final/<slug>.pdf, so nothing is redrawn:
- disclaimer:     the PDF as signed off, plus the version stamp
- no-disclaimer:  the six disclaimer lines removed (text only; the paper, lines and the credit "Map: Maxwell Howe",
                  "#30DayMapChallenge" and "Day 8 • Utopia" stay), plus the version stamp
Each is rasterized at the same dpi as the signed-off PNG and saved to
- boston-map/output/final/v1.0/<slug>_v1.0_<kind>.pdf and .png
- C:\\Users\\mhowe\\Downloads\\NERTA-final\\v1.0\\ (same files)
- C:\\Users\\mhowe\\Desktop\\NERTA-FINAL-Disclaimer\\v1.0\\<slug>\\ : the export_social.py set for both kinds
Never overwrites: refuses a slug whose v1.0 files already exist.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
VERSION = "v1.0"
REPO = Path(__file__).resolve().parents[1]
FINAL = REPO / "output" / "final"
OUT = FINAL / VERSION
DOWNLOADS = Path(r"C:\Users\mhowe\Downloads\NERTA-final") / VERSION
DESKTOP = Path(r"C:\Users\mhowe\Desktop\NERTA-FINAL-Disclaimer") / VERSION
ARIAL = r"C:\Windows\Fonts\arial.ttf"
DISCLAIMER = ("This is a futuristic concept map", "and is not affiliated with the MBTA", "in any way. MOST of the map decisions",
              "are grounded in real data & studies,", "proposals made, or projections for", "future projects or development.")
STAMP_INK = (0.29, 0.29, 0.29)  # a quiet dark gray


def disclaimer_rects(page):
    """The six disclaimer lines, as found in the PDF text layer. Exactly six, or stop."""
    found = []
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            t = " ".join("".join(s["text"] for s in ln["spans"]).split())
            if t in DISCLAIMER:
                found.append((t, fitz.Rect(ln["bbox"])))
    if sorted(t for t, _ in found) != sorted(DISCLAIMER):
        raise SystemExit(f"disclaimer not found cleanly: {[t for t, _ in found]}")
    return [r for _, r in found]


def strip_disclaimer(page):
    for r in disclaimer_rects(page):
        page.add_redact_annot(fitz.Rect(r.x0, r.y0 + 1.0, r.x1, r.y1 - 1.0), fill=False)  # inset, so no neighbor is touched
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE, text=fitz.PDF_REDACT_TEXT_REMOVE)
    if page.search_for("futuristic concept"):
        raise SystemExit("disclaimer text still there")


def stamp_spot(page, fs):
    """Bottom-left corner, as close to the corner as is clear: the box under the text must be one flat color."""
    W, H = page.rect.width, page.rect.height
    m = max(6.0, 0.011 * min(W, H))
    w, h = fs * 2.2, fs * 1.25
    for dy in range(0, 12):
        for dx in range(0, 12):
            x, y = m + dx * fs, H - m - dy * fs  # y = text baseline
            box = fitz.Rect(x - 2, y - h, x + w + 2, y + 0.35 * fs + 2)
            pix = page.get_pixmap(clip=box, dpi=150)
            a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)[:, :, :3].astype(int)
            if (a.max(axis=(0, 1)) - a.min(axis=(0, 1))).max() <= 6:
                return x, y
    raise SystemExit("no clear spot for the version stamp near the bottom-left corner")


def stamp(page):
    fs = float(np.clip(0.0068 * min(page.rect.width, page.rect.height), 6.5, 13.0))
    x, y = stamp_spot(page, fs)
    page.insert_font(fontname="arialv", fontfile=ARIAL)
    page.insert_text((x, y), VERSION, fontname="arialv", fontsize=fs, color=STAMP_INK)
    return x, y, fs


def dpi_of(slug):
    pdf, png = fitz.open(FINAL / f"{slug}.pdf")[0], Image.open(FINAL / f"{slug}.png")
    return round(png.width / pdf.rect.width * 72)


def main():
    slugs = sys.argv[1:]
    for d in (OUT, DOWNLOADS, DESKTOP):
        d.mkdir(parents=True, exist_ok=True)
    for slug in slugs:
        dpi = dpi_of(slug)
        social = DESKTOP / slug
        if social.exists() and any(social.iterdir()) or (OUT / f"{slug}_{VERSION}_disclaimer.pdf").exists():
            raise SystemExit(f"{slug}: v1.0 files exist already; refusing to overwrite")
        social.mkdir(parents=True, exist_ok=True)
        for kind in ("disclaimer", "no-disclaimer"):
            own = FINAL / "no-disclaimer" / f"{slug}.pdf"  # a render made to Max's no-disclaimer spec (note under the logo, no credit or MBTA text)
            doc = fitz.open(own if kind == "no-disclaimer" and own.exists() else FINAL / f"{slug}.pdf")
            page = doc[0]
            if kind == "no-disclaimer" and not own.exists():
                strip_disclaimer(page)
            x, y, fs = stamp(page)
            stem = f"{slug}_{VERSION}_{kind}"
            pdf = OUT / f"{stem}.pdf"
            doc.save(pdf, garbage=3, deflate=True)
            png = OUT / f"{stem}.png"
            fitz.open(pdf)[0].get_pixmap(dpi=dpi).save(png)
            for f in (pdf, png):
                shutil.copy2(f, DOWNLOADS / f.name)
            shutil.copy2(png, social / png.name)
            subprocess.run([sys.executable, str(REPO / "tools" / "export_social.py"), str(social), str(social / png.name)], check=True,
                           stdout=subprocess.DEVNULL)
            (social / png.name).unlink()  # the export keeps its own _full.png
            print(f"{slug} {kind}: {dpi} dpi, stamp at ({x:.0f}, {y:.0f}) pt, {fs:.1f} pt")


if __name__ == "__main__":
    main()
