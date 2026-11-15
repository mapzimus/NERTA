"""Marginal value of each NERTA segment: walk-zone people and jobs that only it reaches."""
import sys
import numpy as np
from shapely.geometry import Point
from shapely.ops import unary_union
import compare as C

segs = C.N_SEGS
stop_segs = {}
for i, (l, st, stops) in enumerate(segs):
    for s in stops:
        stop_segs.setdefault(s, set()).add(i)
rows = []
for i, (l, st, stops) in enumerate(segs):
    own = [s for s in stops if stop_segs[s] == {i}]
    others = [p for s, p in C.NM.items() if s not in own]
    rest = unary_union([Point(p).buffer(C.HALF) for p in others])
    mine = unary_union([Point(C.NM[s]).buffer(C.HALF) for s in own]) if own else None
    r = j = 0
    if mine is not None:
        r, j = C.served(mine.difference(rest))
    km = sum(np.linalg.norm(C.NM[a] - C.NM[b]) for a, b in zip(stops, stops[1:])) / 1000
    rows.append((l, st, stops[0], stops[-1], len(own), round(km, 1), int(r), int(j),
                 int((r + j) / km) if km else 0))
rows.sort(key=lambda r: r[-1])
print(f"{'line':7s} {'style':6s} {'from':22s} {'to':22s} own  km   res   jobs  per_km")
for r in rows:
    print(f"{r[0]:7s} {r[1]:6s} {r[2][:22]:22s} {r[3][:22]:22s} {r[4]:3d} {r[5]:5.1f} {r[6]:6d} {r[7]:6d} {r[8]:6d}")
