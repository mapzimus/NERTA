"""Swap in the 18 rail maps' v1.0 no-disclaimer finals made to Max's spec (November 8, 2:05 PM, in the rail session):
"Everything except for one small note underneath the NERTA logo that says Concept map by Maxwell Howe - @mapzimus - 2026".

The sources are the rail scripts' own renders with NERTA_NO_DISCLAIMER=1 (boston-map/output/copies/no-disclaimer/): no
release block, no MBTA text, the note under the logo, every name where it is on the version with the disclaimer. This uses
release_v1.py's own stamp, dpi and folders, so the files match the other maps' v1.0 set:
- boston-map/output/final/v1.0/<slug>_v1.0_no-disclaimer.pdf and .png
- C:\\Users\\mhowe\\Downloads\\NERTA-final\\v1.0\\ (same files)
- C:\\Users\\mhowe\\Desktop\\NERTA-FINAL-Disclaimer\\v1.0\\<slug>\\ : the export_social.py set
The no-disclaimer files release_v1.py made from 1:59 to 2:01 PM (credit and MBTA footers kept, no note) are moved, never
deleted, to each folder's superseded/ as pre_note_<name>, and the Desktop ones to v1.0\\_superseded\\<slug>_pre_note\\.
Usage: release_v1_rail_nodisc.py [<slug> ...]   (default: all 18)
"""
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_v1 as R  # noqa: E402  (the stamp, dpi rule and folders of the v1.0 set)

SRC = R.REPO / "output" / "copies" / "no-disclaimer"
TAG = "pre_note"
KEYS = ("fit", "low", "hav", "pea", "nbp", "wor", "fra", "pro", "fr", "kin", "grb", "hmon", "hmai", "halb", "hnyc")
SOURCES = {"rail-poster": "rail_poster_v2", "rail-network": "rail_network_v2", "rail-regional": "rail_regional_v2",
           **{f"rail_line_{k}": f"rail_line_{k}_v1" for k in KEYS}, "rail_line_fit": "rail_line_fit_v2"}  # v2: Waltham's GL pill (2:35 PM)
MUST_NOT = ("MBTA", "30DayMapChallenge", "Day 8", "futuristic", "Map: Maxwell Howe")
MUST = "Concept map by Maxwell Howe"
SPEC_TIME = datetime(2026, 11, 8, 14, 5)   # Max's answer; a no-disclaimer file newer than this was already redone


def check_source(pdf):
    page = fitz.open(pdf)[0]
    bad = [t for t in MUST_NOT if page.search_for(t)]
    if bad or not page.search_for(MUST):
        raise SystemExit(f"{pdf.name}: still has {bad}" if bad else f"{pdf.name}: no '{MUST}' note")


def move_aside(slug):
    stem = f"{slug}_{R.VERSION}_no-disclaimer"
    for root in (R.OUT, R.DOWNLOADS):
        for ext in (".pdf", ".png"):
            src = root / f"{stem}{ext}"
            if src.exists():
                dst = root / "superseded" / f"{TAG}_{stem}{ext}"
                dst.parent.mkdir(exist_ok=True)
                assert not dst.exists(), dst
                shutil.move(src, dst)
    social = R.DESKTOP / slug
    old = sorted(social.glob(f"{stem}_*")) + [m for m in social.glob("MANIFEST*.txt") if stem in m.read_text(encoding="utf-8")]
    if old:
        dst_dir = R.DESKTOP / "_superseded" / f"{slug}_{TAG}"
        dst_dir.mkdir(parents=True, exist_ok=False)
        for p in old:
            shutil.move(p, dst_dir / p.name)


def main():
    slugs = sys.argv[1:] or list(SOURCES)
    for slug in slugs:   # every check first, so nothing moves unless all the sources are right
        check_source(SRC / f"{SOURCES[slug]}.pdf")
        cur = R.OUT / f"{slug}_{R.VERSION}_no-disclaimer.pdf"
        if cur.exists() and datetime.fromtimestamp(cur.stat().st_mtime) > SPEC_TIME:
            raise SystemExit(f"{slug}: its no-disclaimer file is newer than Max's answer; someone redid it, so stopping")
    for slug in slugs:
        dpi = R.dpi_of(slug)
        move_aside(slug)
        doc = fitz.open(SRC / f"{SOURCES[slug]}.pdf")
        x, y, fs = R.stamp(doc[0])
        stem = f"{slug}_{R.VERSION}_no-disclaimer"
        pdf, png = R.OUT / f"{stem}.pdf", R.OUT / f"{stem}.png"
        assert not pdf.exists() and not png.exists()
        doc.save(pdf, garbage=3, deflate=True)
        fitz.open(pdf)[0].get_pixmap(dpi=dpi).save(png)
        for f in (pdf, png):
            shutil.copy2(f, R.DOWNLOADS / f.name)
        social = R.DESKTOP / slug
        shutil.copy2(png, social / png.name)
        subprocess.run([sys.executable, str(R.REPO / "tools" / "export_social.py"), str(social), str(social / png.name)], check=True,
                       stdout=subprocess.DEVNULL)
        (social / png.name).unlink()  # the export keeps its own _full.png
        disc = fitz.open(R.OUT / f"{slug}_{R.VERSION}_disclaimer.pdf")[0].search_for(R.VERSION)
        print(f"{slug} no-disclaimer: {dpi} dpi, stamp at ({x:.0f}, {y:.0f}) pt, {fs:.1f} pt; disclaimer stamp at "
              f"({disc[-1].x0:.0f}, {disc[-1].y1:.0f})" if disc else f"{slug}: stamped, but no stamp found on the disclaimer kind")


if __name__ == "__main__":
    main()
