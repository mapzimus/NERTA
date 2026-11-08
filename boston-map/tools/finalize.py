"""Save one signed-off map to its three homes (Max, November 8): the repo, Downloads, and the Desktop folder in social sizes.

Usage: finalize.py <slug> <map.pdf> [<map.png>] [--dpi N]

- Repo:      boston-map/output/final/<slug>.pdf and <slug>.png (a vector PDF and a PNG master)
- Downloads: C:\\Users\\mhowe\\Downloads\\NERTA-final\\ (same two files)
- Desktop:   C:\\Users\\mhowe\\Desktop\\NERTA-FINAL-Disclaimer\\<slug>\\ : the export_social.py set (feed, Instagram, TikTok, zoom, full)

The PNG master is the given PNG, or the PDF rasterized at --dpi (default 400) when no PNG is given.
Never overwrites: a name that exists gets _v2, _v3. Run it only for a map the master session has signed off,
with the release block (disclaimer, credit, hashtag, Day 8) drawn: never a nerta.fun web render.
"""
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FINAL = REPO / "output" / "final"
DOWNLOADS = Path(r"C:\Users\mhowe\Downloads\NERTA-final")
DESKTOP = Path(r"C:\Users\mhowe\Desktop\NERTA-FINAL-Disclaimer")


def free(p):
    """p, or p with _v2, _v3 ... so nothing is overwritten."""
    if not p.exists():
        return p
    k = 2
    while (q := p.with_name(f"{p.stem}_v{k}{p.suffix}")).exists():
        k += 1
    return q


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dpi = int(sys.argv[sys.argv.index("--dpi") + 1]) if "--dpi" in sys.argv else 400
    args = [a for a in args if a != str(dpi)]
    slug, pdf = args[0], Path(args[1])
    png = Path(args[2]) if len(args) > 2 else None
    if "web" in str(pdf).lower() or (png and "web" in str(png).lower()):
        raise SystemExit("refusing a web render: finals carry the release block")
    tmp = None
    if png is None:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf)
        tmp = REPO / "output" / "copies" / f"_finalize_{slug}.png"
        doc[0].get_pixmap(dpi=dpi).save(tmp)
        png = tmp
    for root in (FINAL, DOWNLOADS):
        root.mkdir(parents=True, exist_ok=True)
        for src, ext in ((pdf, ".pdf"), (png, ".png")):
            dst = free(root / f"{slug}{ext}")
            shutil.copy2(src, dst)
            print("saved", dst)
    social = DESKTOP / slug
    if social.exists() and any(social.iterdir()):
        social = free(social)
    social.mkdir(parents=True, exist_ok=True)
    named = social / f"{slug}.png"
    shutil.copy2(png, named)  # the export names its files from the input's stem
    py = sys.executable
    subprocess.run([py, str(REPO / "tools" / "export_social.py"), str(social), str(named)], check=True)
    named.unlink()  # the export's own _full.png stays as the full-size copy
    if tmp and tmp.exists():
        tmp.unlink()
    print("social set in", social)


if __name__ == "__main__":
    main()
