"""Move a map's current finals aside before re-finalizing it, so the three final folders hold one current version per map.

Usage: supersede.py <slug> <tag>
Moves boston-map/output/final/<slug>.{pdf,png} and Downloads\\NERTA-final\\<slug>.{pdf,png} into each folder's superseded/
as <tag>_<slug>.*, and the Desktop folder NERTA-FINAL-Disclaimer\\<slug> into NERTA-FINAL-Disclaimer\\_superseded\\<slug>_<tag>.
Moves only; deletes nothing.
"""
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FOLDERS = [REPO / "output" / "final", Path(r"C:\Users\mhowe\Downloads\NERTA-final")]
DESKTOP = Path(r"C:\Users\mhowe\Desktop\NERTA-FINAL-Disclaimer")

slug, tag = sys.argv[1], sys.argv[2]
for root in FOLDERS:
    for ext in (".pdf", ".png"):
        src = root / f"{slug}{ext}"
        if src.exists():
            (root / "superseded").mkdir(exist_ok=True)
            dst = root / "superseded" / f"{tag}_{slug}{ext}"
            assert not dst.exists(), dst
            shutil.move(src, dst)
            print("moved", src, "->", dst)
src = DESKTOP / slug
if src.exists():
    (DESKTOP / "_superseded").mkdir(exist_ok=True)
    dst = DESKTOP / "_superseded" / f"{slug}_{tag}"
    assert not dst.exists(), dst
    shutil.move(src, dst)
    print("moved", src, "->", dst)
