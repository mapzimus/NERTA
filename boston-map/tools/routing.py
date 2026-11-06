"""Routing check on the T map: transfers and detour between every pair of stops, using diagram distance."""
import sys, heapq, itertools
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import make_tmap as M
from station_kit import rounded, place
NAMES = {M.RED: "Red", M.ORANGE: "Orange", M.BLUE: "Blue", M.GREEN: "Green", M.YELLOW: "Yellow", M.CYAN: "Cyan", M.INDIGO: "Indigo"}
base = {"Fenway+": "Fenway", "Longwood+": "Longwood Medical Area", "Sullivan Sq+": "Sullivan Sq", "South Station+": "South Station"}
pos, edges = {}, []
for col, style, path, stops in M.lines():
    xy = rounded(path, M.CR)
    got = place(xy, stops, {**M.A, **M.EXTRA})
    seq = []
    for s in stops:
        b = base.get(s, s.rstrip("*"))
        seq.append(b)
        pos.setdefault(b, np.array(got[s]))
    for a, b in zip(seq, seq[1:]):
        edges.append((a, b, NAMES[col], float(np.hypot(*(np.array(got[[k for k in stops if base.get(k, k) == a][0]]) - np.array(got[[k for k in stops if base.get(k, k) == b][0]]))))))
walk = [("Gov't Center", "State"), ("Gov't Center", "Boston Central"), ("Haymarket", "North Station"), ("North Station", "Science Park")][:2] + [("Haymarket", "North Station")]
adj = {}
for a, b, l, d in edges:
    adj.setdefault((a, l), []).append(((b, l), d, 0))
    adj.setdefault((b, l), []).append(((a, l), d, 0))
lines_at = {}
for a, b, l, d in edges:
    lines_at.setdefault(a, set()).add(l); lines_at.setdefault(b, set()).add(l)
for s, ls in lines_at.items():
    for x, y in itertools.permutations(ls, 2):
        adj.setdefault((s, x), []).append(((s, y), 0, 1))
for x, y in (("Brighton Center", "Harvard Ave"), ("South Station", "Fort Point"), ("Copley", "Prudential")):
    for lx in lines_at[x]:
        for ly in lines_at[y]:
            adj.setdefault((x, lx), []).append(((y, ly), 5, 0 if lx == ly else 1))
            adj.setdefault((y, ly), []).append(((x, lx), 5, 0 if lx == ly else 1))
PEN = 10
def run(src):
    best = {}
    h = [(0, 0, 0, (src, l)) for l in lines_at[src]]
    while h:
        c, d, t, n = heapq.heappop(h)
        if n in best:
            continue
        best[n] = (c, d, t)
        for m, w, tr in adj.get(n, []):
            if m not in best:
                heapq.heappush(h, (c + w + tr * PEN, d + w, t + tr, m))
    out = {}
    for (s, l), v in best.items():
        if s not in out or v[0] < out[s][0]:
            out[s] = v
    return out
stops = sorted(lines_at)
rows, hist = [], {}
for a in stops:
    r = run(a)
    for b in stops:
        if a >= b or b not in r:
            continue
        d0 = float(np.hypot(*(pos[a] - pos[b])))
        c, L, t = r[b]
        hist[t] = hist.get(t, 0) + 1
        rows.append((L / max(d0, 1), d0, L, t, a, b))
print(len(stops), "stops; pairs by transfers:", dict(sorted(hist.items())))
print("unreachable:", [s for s in stops if len(run(s)) < len(stops)][:5])
print("Near each other but long trip (straight 6-30 units):")
seen = set()
for ratio, d0, L, t, a, b in sorted([r for r in rows if 6 <= r[1] <= 30], reverse=True):
    k = (a.split()[0], b.split()[0])
    if a in seen or b in seen:
        continue
    seen.update((a, b))
    print(f"  {a} -> {b}: straight {d0:.0f}, ride {L:.0f}, x{ratio:.1f}, {t} transfers")
    if len(seen) > 44:
        break
print("Three-plus transfers:")
for ratio, d0, L, t, a, b in sorted([r for r in rows if r[3] >= 3], key=lambda r: -r[3])[:14]:
    print(f"  {a} -> {b}: {t} transfers, ride {L:.0f}")
