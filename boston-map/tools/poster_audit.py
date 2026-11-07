"""Check that every line poster matches the main map.

Fails loudly if a stop on the main map is missing from its poster, if a poster has a stop the map doesn't,
or if two lines share a stop and either poster has no pill for the other line.
Run: python poster_audit.py
"""
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import make_line_poster as P  # noqa: E402
import make_tmap as M  # noqa: E402

LINES = {M.RED: ("red", "RL"), M.ORANGE: ("orange", "OL"), M.BLUE: ("blue", "BL"), M.GREEN: ("green", "GL"),
         M.YELLOW: ("yellow", "YL"), M.CYAN: ("cyan", "CL"), M.INDIGO: ("indigo", "IL")}
on_map = collections.defaultdict(set)
for col, _style, _path, stops in M.lines():
    if col in LINES:
        on_map[LINES[col][0]].update(s.rstrip("+") for s in stops)

problems = 0
for col, (key, _code) in LINES.items():
    on_poster = {s.rstrip("+") for leg in P.LAYOUTS[key][3]() for s in leg["stops"]}
    for s in sorted(on_map[key] - on_poster):
        print(f"{key}: {s} is on the map but not the poster")
        problems += 1
    for s in sorted(on_poster - on_map[key]):
        print(f"{key}: {s} is on the poster but not the map")
        problems += 1

pills = {LINES[col][0]: P.transfers(col, LINES[col][0]) for col in LINES}
codes = {key: code for key, code in LINES.values()}
for a in codes:
    for b in codes:
        if a < b:
            for s in sorted(on_map[a] & on_map[b]):
                for x, y in ((a, b), (b, a)):
                    if codes[y] not in pills[x].get(s, []):
                        print(f"{x}: {s} needs a {codes[y]} pill")
                        problems += 1

print("problems:", problems)
sys.exit(1 if problems else 0)
