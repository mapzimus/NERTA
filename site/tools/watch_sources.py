"""Wait until the map sources the site is built from change, then report what changed and exit.

    python site/tools/watch_sources.py [--settle 120] [--every 30] [--max-hours 8]

Watches the map and poster scripts, the network data files, and new finished renders in output/copies/ (rail, ferry,
tram and line posters). It waits until changes have stopped for --settle seconds, so a session mid-edit isn't caught
halfway, then prints the changed paths and exits. Read-only: it never writes anything.
"""
import argparse
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WATCH = [
    ("boston-map/src", "*.py"),
    ("boston-map/data", "*.md"),
    ("boston-map/data/tram", "tram_network.json"),
    ("boston-map/data/tram", "stations_real.geojson"),
    ("boston-map/data/rail_regional", "cr_*.geojson"),
    ("boston-map/output/copies", "*.png"),
]
SKIP = ("web", "archive")  # the site's own renders and old drafts


def snapshot():
    out = {}
    for folder, pattern in WATCH:
        for p in (REPO / folder).glob(pattern):
            if any(part.startswith(SKIP) for part in p.relative_to(REPO).parts[:-1]):
                continue
            try:
                out[str(p.relative_to(REPO))] = p.stat().st_mtime
            except OSError:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--settle", type=int, default=120)
    ap.add_argument("--every", type=int, default=30)
    ap.add_argument("--max-hours", type=float, default=8)
    a = ap.parse_args()
    base = snapshot()
    changed, last_change = set(), None
    stop = time.time() + a.max_hours * 3600
    while time.time() < stop:
        time.sleep(a.every)
        now = snapshot()
        diff = {k for k in set(base) | set(now) if base.get(k) != now.get(k)}
        if diff:
            changed |= diff
            last_change = time.time()
            base = now
        if changed and time.time() - last_change >= a.settle:
            print("CHANGED:")
            for k in sorted(changed):
                print(" ", k, "(new)" if k in now and k not in snapshot_at_start else "(removed)" if k not in now else "")
            return 0
    print("no changes")
    return 0


if __name__ == "__main__":
    snapshot_at_start = snapshot()
    sys.exit(main())
