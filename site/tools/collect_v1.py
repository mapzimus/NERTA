"""Collect a finished map set into one folder with clear names, both versions side by side.

    python site/tools/collect_v1.py WEB_RUN RELEASE_RUN [--version v1.0] [--downloads]

WEB_RUN and RELEASE_RUN are run folders in boston-map/output/copies (e.g. web_v31 and release_v2). Writes
boston-map/output/copies/<version>/no-disclaimer/<map>_no-disclaimer.png|.pdf and .../with-disclaimer/<map>_with-disclaimer.*
using the same map names as boston-map/output/final. Never overwrites: refuses if the version folder already exists.
With --downloads, also copies the folder to Downloads/NERTA-<version>.
"""
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COPIES = REPO / "boston-map" / "output" / "copies"


def final_name(stem):
    """Working file names to the names used in boston-map/output/final."""
    if stem == "system_map":
        return "main-map"
    if re.fullmatch(r"line_[a-z]+", stem):
        return stem.replace("_", "-")
    return {"ferry_network": "ferry-network", "rail_poster": "rail-poster", "rail_regional": "rail-regional",
            "rail_network": "rail-network"}.get(stem, stem)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    version = sys.argv[sys.argv.index("--version") + 1] if "--version" in sys.argv else "v1.0"
    if "--version" in sys.argv:
        args.remove(version)
    # Each argument may list several run folders, comma-separated; a later folder's file wins
    web, rel = [COPIES / n for n in args[0].split(",")], [COPIES / n for n in args[1].split(",")]
    out = COPIES / version
    if out.exists():
        raise SystemExit(f"{out} already exists; pick a new version or remove it by hand")
    counts = {}
    for srcs, label in ((web, "no-disclaimer"), (rel, "with-disclaimer")):
        dest = out / label
        dest.mkdir(parents=True)
        pick = {}
        for src in srcs:
            for f in sorted(src.iterdir()):
                if f.suffix not in (".png", ".pdf"):
                    continue
                stem = re.sub(r"_v\d+$", "", f.stem)
                pick[(final_name(stem), f.suffix)] = f
        for (name, ext), f in sorted(pick.items()):
            shutil.copyfile(f, dest / f"{name}_{label}{ext}")
        counts[label] = len(pick)
    (out / "README.txt").write_text(
        f"NERTA maps {version}\n\n"
        "no-disclaimer/   for nerta.fun: no release block; Maxwell Howe under the NERTA mark; @mapzimus\n"
        "with-disclaimer/ for posting: the disclaimer, Map: Maxwell Howe, #30DayMapChallenge and Day 8 • Utopia\n\n"
        f"Every map carries a small {version} in the bottom-left corner. Trams aren't included yet.\n", encoding="utf-8")
    print(counts, "->", out)
    if "--downloads" in sys.argv:
        dl = Path.home() / "Downloads" / f"NERTA-{version}"
        if dl.exists():
            raise SystemExit(f"{dl} already exists")
        shutil.copytree(out, dl)
        print("copied to", dl)


if __name__ == "__main__":
    main()
