"""How much of each Spencer route already has a NERTA stop within a half mile."""
import sys, numpy as np
from collections import Counter
sys.argv = [sys.argv[0], sys.argv[1]]
import compare as C
for code, (nm, ck, st) in C.S_LINES.items():
    hits, fam = 0, Counter()
    for s in st:
        p = C.SM[s]
        best = None
        for n, q in C.NM.items():
            d = np.linalg.norm(p - q)
            if d < C.HALF and (best is None or d < best[0]):
                best = (d, n)
        if best:
            hits += 1
            for l in C.n_line_of[best[1]]:
                fam[l] += 1
    print(f"{nm:20s} {len(set(st)):3d} stops  {100*hits/len(set(st)):5.0f}% near NERTA  top NERTA lines: {fam.most_common(3)}")
