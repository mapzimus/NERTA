"""Layout for the T-style map of Spencer's network.

Method, following the house style:
1. Treat each color as one line (Green A-F share one stroke where they share track).
2. Junctions, transfers and terminals are anchors. Their spots start from
   Spencer's own diagram, stretched so downtown has room, then snapped to a grid.
3. Plain stops are spread evenly along the 45-degree path between anchors.
4. Branch ends run straight out from their last junction, one stop per step.
"""
import math
from collections import defaultdict

import numpy as np

from network import ROUTES, LOOPS
from layout import T, snapped
from kit import octi

SP = 5.2          # stop spacing on branch ends, map units
SCALE = 0.26      # Spencer diagram units -> map units
CORE = (626.0, -818.0)   # Government Center in his diagram units


def fam(code):
    return ROUTES[code][1]


def route_stops(code):
    st = list(ROUTES[code][2])
    return st + [st[0]] if code in LOOPS else st


def graph():
    edges = defaultdict(set)
    for code in ROUTES:
        st = route_stops(code)
        for a, b in zip(st, st[1:]):
            edges[tuple(sorted((a, b)))].add(fam(code))
    nbr = defaultdict(set)
    for a, b in edges:
        nbr[a].add(b); nbr[b].add(a)
    return edges, nbr


def anchors(edges, nbr):
    A = set()
    for code in ROUTES:           # every route end is an anchor
        if code not in LOOPS:
            A.update([ROUTES[code][2][0], ROUTES[code][2][-1]])
    for n, ns in nbr.items():
        if len(ns) != 2:
            A.add(n)
            continue
        a, b = list(ns)
        if edges[tuple(sorted((n, a)))] != edges[tuple(sorted((n, b)))]:
            A.add(n)
    return A


def chains(edges, nbr, A):
    out, seen = [], set()
    for a in A:
        for b in nbr[a]:
            if (a, b) in seen:
                continue
            ch = [a, b]
            while ch[-1] not in A:
                nxt = [x for x in nbr[ch[-1]] if x != ch[-2]]
                ch.append(nxt[0])
            seen.add((ch[0], ch[1])); seen.add((ch[-1], ch[-2]))
            out.append(ch)
    return out


def stretch(p):
    """Give the core more room. Same curve on both axes, centered downtown."""
    out = []
    for v, c in zip(p, CORE):
        d = v - c
        out.append(c + d + 150.0 * math.tanh(d / 110.0))
    return np.array(out)


def snap8(v):
    ang = round(math.degrees(math.atan2(v[1], v[0])) / 45) * 45
    return np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])


def cut(path, n):
    """n points evenly spaced strictly inside a polyline."""
    path = [np.array(p, float) for p in path]
    seg = [np.linalg.norm(b - a) for a, b in zip(path, path[1:])]
    total = sum(seg)
    pts = []
    for i in range(1, n + 1):
        d = total * i / (n + 1)
        for (a, b), L in zip(zip(path, path[1:]), seg):
            if d <= L + 1e-9:
                pts.append(a + (b - a) * (d / L if L else 0)); break
            d -= L
    return pts


def sub(path, d0, d1):
    """Piece of a polyline between two distances along it."""
    path = [np.array(p, float) for p in path]
    out, acc = [], 0.0
    for a, b in zip(path, path[1:]):
        L = np.linalg.norm(b - a)
        s, e = acc, acc + L
        if e >= d0 - 1e-9 and s <= d1 + 1e-9 and L > 0:
            t0, t1 = max(d0, s), min(d1, e)
            p0, p1 = a + (b - a) * ((t0 - s) / L), a + (b - a) * ((t1 - s) / L)
            if not out or np.linalg.norm(out[-1] - p0) > 1e-6:
                out.append(p0)
            if np.linalg.norm(out[-1] - p1) > 1e-6:
                out.append(p1)
        acc = e
    return out


def build(move=None, rays=None, bends=None, via=None, place=None):
    """Returns stop positions, the polyline for every edge, chains and anchors.

    move:  anchor -> (dx, dy) nudge after the automatic layout
    rays:  terminal -> (angle degrees, optional length) for a branch end
    bends: (anchor a, anchor b) -> 'first' or 'last' to choose the corner
    via:   (anchor a, anchor b) -> list of absolute points to pass through
    """
    move, rays, bends, via, place = move or {}, rays or {}, bends or {}, via or {}, place or {}
    edges, nbr = graph()
    A = anchors(edges, nbr)
    CH = chains(edges, nbr, A)
    # anchors from his diagram, straightened along anchor-to-anchor links
    links = [(c[0], c[-1]) for c in CH if c[0] != c[-1]]
    P0 = snapped(list(T), [(a, b) for a, b in edges])
    Pa = {a: stretch(P0[a]) * SCALE for a in A}
    names = list(Pa)
    for _ in range(2):   # re-straighten after the stretch
        Pa = _straight(Pa, links, tol=6)
    Pa = {a: np.round(p) for a, p in Pa.items()}
    for a, d in move.items():
        Pa[a] = Pa[a] + np.array(d, float)
    for a, xy in place.items():      # exact spots, for the hand-set core
        Pa[a] = np.array(xy, float)

    pos, epath = dict(Pa), {}
    leaf = {n for n in A if len(nbr[n]) == 1}
    # interior chains first
    for ch in CH:
        a, b = ch[0], ch[-1]
        if a in leaf or b in leaf:
            continue
        others = np.array([Pa[x] for x in Pa if x not in (a, b)])
        key = (a, b) if (a, b) in via or (a, b) in bends else (b, a)
        if (a, b) in via or (b, a) in via:
            w = via[key] if key == (a, b) else via[key][::-1]
            pts = [Pa[a]] + [np.array(q, float) for q in w] + [Pa[b]]
            path = [pts[0]]
            for p_, q_ in zip(pts, pts[1:]):
                path.extend(octi(p_, q_, others)[1:])
        else:
            path = octi(Pa[a], Pa[b], others)
            want = bends.get((a, b)) or ({"first": "last", "last": "first"}.get(bends.get((b, a))))
            if want and len(path) == 3:
                d = Pa[b] - Pa[a]
                m = min(abs(d[0]), abs(d[1]))
                diag = np.array([math.copysign(m, d[0]), math.copysign(m, d[1])])
                path = [Pa[a], Pa[a] + diag, Pa[b]] if want == "first" else [Pa[a], Pa[b] - diag, Pa[b]]
        _fill(ch, path, pos, epath)
    # branch ends
    for ch in CH:
        a, b = ch[0], ch[-1]
        if not (a in leaf or b in leaf):
            continue
        if a in leaf and b not in leaf:
            ch = ch[::-1]; a, b = b, a
        n = len(ch) - 1
        r = rays.get(b)
        if r is None:
            # keep his direction, but make the branch long enough for its stops
            tgt = stretch(P0[b]) * SCALE
            v = tgt - pos[a]
            others = np.array([pos[x] for x in Pa if x not in (a, b)])
            for _ in range(60):
                path = octi(pos[a], np.round(pos[a] + v), others)
                L = sum(np.linalg.norm(q - p) for p, q in zip(path, path[1:]))
                if L >= SP * n - 0.5:
                    break
                v = v * 1.06
            if L > SP * n * 1.6:      # and not longer than it needs to be
                v = v * (SP * n * 1.3 / L)
                path = octi(pos[a], np.round(pos[a] + v), others)
        else:
            path = [pos[a]]
            for ang, steps in r:
                u = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
                path.append(path[-1] + u * SP * steps)
        pos[b] = np.array(path[-1])
        _fill(ch, path, pos, epath)
    return pos, epath, CH, A, edges


def _fill(ch, path, pos, epath):
    inner = cut(path, len(ch) - 2)
    for s, p in zip(ch[1:-1], inner):
        pos[s] = p
    seg = [np.linalg.norm(np.array(b) - np.array(a)) for a, b in zip(path, path[1:])]
    total = sum(seg)
    n = len(ch) - 1
    for i, (s, t) in enumerate(zip(ch, ch[1:])):
        piece = sub(path, total * i / n, total * (i + 1) / n)
        epath[(s, t)] = piece
        epath[(t, s)] = piece[::-1]


def _straight(P, links, tol=9):
    P = {k: np.array(v, float) for k, v in P.items()}
    for kind in ("h", "v", "d1", "d2"):
        parent = {n: n for n in P}
        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]; a = parent[a]
            return a
        want = {"h": 0, "v": 90, "d1": 45, "d2": 135}[kind]
        for a, b in links:
            d = P[b] - P[a]
            ang = math.degrees(math.atan2(d[1], d[0])) % 180
            diff = min(abs(ang - want), 180 - abs(ang - want))
            if diff < tol and np.hypot(*d) > 0.5:
                parent[find(a)] = find(b)
        groups = defaultdict(list)
        for n in P:
            groups[find(n)].append(n)
        for g in groups.values():
            if len(g) < 2:
                continue
            if kind == "h":
                m = np.mean([P[n][1] for n in g])
                for n in g: P[n][1] = m
            elif kind == "v":
                m = np.mean([P[n][0] for n in g])
                for n in g: P[n][0] = m
            elif kind == "d1":
                m = np.mean([P[n][1] - P[n][0] for n in g])
                for n in g:
                    k = P[n][1] - P[n][0] - m
                    P[n][0] += k / 2; P[n][1] -= k / 2
            else:
                m = np.mean([P[n][1] + P[n][0] for n in g])
                for n in g:
                    k = P[n][1] + P[n][0] - m
                    P[n][0] -= k / 2; P[n][1] -= k / 2
    return P


if __name__ == "__main__":
    pos, epath, CH, A, edges = build()
    print(len(A), "anchors,", len(CH), "chains,", len(pos), "stops")
    tight = []
    for ch in CH:
        L = sum(np.linalg.norm(np.array(q) - np.array(p)) for s, t in zip(ch, ch[1:])
                for p, q in zip(epath[(s, t)], epath[(s, t)][1:]))
        sp = L / (len(ch) - 1)
        if sp < 4.0:
            tight.append((round(sp, 1), ch[0], ch[-1], len(ch) - 2))
    print("tight chains:", sorted(tight)[:40])
