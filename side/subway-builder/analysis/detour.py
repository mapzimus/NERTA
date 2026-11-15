"""Detour: network distance / straight distance for crosstown trips (both ends
3-12 km from downtown, more than 60 degrees apart). Transfers cost 1.5 km."""
import math
import numpy as np
from collections import defaultdict
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
import geopandas as gpd
from shapely.geometry import Point
import compare as C

XFER = 1.5

def detour(segs, M):
    nodes, idx = [], {}
    def nid(k):
        if k not in idx:
            idx[k] = len(nodes); nodes.append(k)
        return idx[k]
    rows, cols, w = [], [], []
    line_of = defaultdict(set)
    for l, st, stops in segs:
        for s in stops:
            line_of[s].add(l)
        for a, b in zip(stops, stops[1:]):
            d = np.linalg.norm(M[a] - M[b]) / 1000
            i, j = nid((a, l)), nid((b, l))
            rows += [i, j]; cols += [j, i]; w += [d, d]
    for s, ls in line_of.items():
        nid((s, None))
        for l in ls:
            i, j = nid((s, l)), nid((s, None))
            rows += [i, j]; cols += [j, i]; w += [XFER / 2, XFER / 2]
    G = csr_matrix((w, (rows, cols)), shape=(len(nodes), len(nodes)))
    hub = M["South Station"]
    cand = []
    for s in line_of:
        v = M[s] - hub
        r = np.linalg.norm(v) / 1000
        if 3 <= r <= 12:
            cand.append((s, math.atan2(v[1], v[0])))
    src = [idx[(s, None)] for s, _ in cand]
    D = dijkstra(G, indices=src)
    ratios = []
    for i, (a, aa) in enumerate(cand):
        for j, (b, bb) in enumerate(cand):
            if j <= i:
                continue
            dang = abs((aa - bb + math.pi) % (2 * math.pi) - math.pi)
            if dang < math.radians(60):
                continue
            straight = np.linalg.norm(M[a] - M[b]) / 1000
            net = D[i, idx[(b, None)]] - XFER  # don't charge the walk in/out
            if straight > 1 and np.isfinite(net):
                ratios.append(net / straight)
    r = np.array(ratios)
    return dict(pairs=len(r), median=round(float(np.median(r)), 2), p75=round(float(np.percentile(r, 75)), 2),
                over2=round(100 * float(np.mean(r > 2)), 1))

print("NERTA:", detour(C.N_SEGS, C.NM))
arc = ["Wellington", "Medford/Tufts", "West Medford", "Alewife", "Watertown", "Brighton Center",
       "Boston College", "Reservoir", "Forest Hills", "Morton St", "Fields Corner"]
print("NERTA + middle arc:", detour(C.N_SEGS + [("Arc", "dash", arc)], C.NM))
print("NERTA without Yellow:", detour([s for s in C.N_SEGS if s[0] != "Yellow"], C.NM))
print("Spencer:", detour(C.S_SEGS, C.SM))


def worst(segs, M, top=25):
    import itertools
    nodes, idx = [], {}
    def nid(k):
        if k not in idx:
            idx[k] = len(nodes); nodes.append(k)
        return idx[k]
    rows, cols, w = [], [], []
    line_of = defaultdict(set)
    for l, st, stops in segs:
        for s in stops:
            line_of[s].add(l)
        for a, b in zip(stops, stops[1:]):
            d = np.linalg.norm(M[a] - M[b]) / 1000
            i, j = nid((a, l)), nid((b, l)); rows += [i, j]; cols += [j, i]; w += [d, d]
    for s, ls in line_of.items():
        nid((s, None))
        for l in ls:
            i, j = nid((s, l)), nid((s, None)); rows += [i, j]; cols += [j, i]; w += [XFER / 2] * 2
    G = csr_matrix((w, (rows, cols)), shape=(len(nodes), len(nodes)))
    hub = M["South Station"]
    cand = [s for s in line_of if 3 <= np.linalg.norm(M[s] - hub) / 1000 <= 12]
    D = dijkstra(G, indices=[idx[(s, None)] for s in cand])
    bad = defaultdict(int)
    for i, a in enumerate(cand):
        for b in cand:
            st = np.linalg.norm(M[a] - M[b]) / 1000
            if a < b and st > 2:
                r = (D[i, idx[(b, None)]] - XFER) / st
                if r > 2:
                    bad[a] += 1; bad[b] += 1
    return sorted(bad.items(), key=lambda x: -x[1])[:top]

print("NERTA stops in the most >2x detours:", worst(C.N_SEGS, C.NM))
