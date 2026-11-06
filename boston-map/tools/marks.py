"""Find markers that hide each other: dots, rings, capsules, pills."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import make_tmap as M

M.main()
ax = plt.gcf().axes[0]
PT = 4.84
marks = []
for c in ax.collections:
    off = c.get_offsets()
    if len(off) == 0:
        continue
    sizes = c.get_sizes()
    for i, q in enumerate(np.asarray(off)):
        s = sizes[i if len(sizes) > 1 else 0]
        marks.append((float(q[0]), float(q[1]), float(np.sqrt(s) / 2 / PT), c.get_zorder()))
inkey = lambda x, y: x > 157 and (y < 55 or 81 < y < 113)
marks = [m for m in marks if not inkey(m[0], m[1])]
print(len(marks), "markers")
names = {}
try:
    names = M.PTS
except AttributeError:
    pass


def nm(x, y):
    best = min(names.items(), key=lambda kv: np.hypot(kv[1][0] - x, kv[1][1] - y)) if names else ("?", (x, y))
    return f"{best[0]} ({x:.1f},{y:.1f})"


print("-- dots touching dots")
seen = set()
for i, a in enumerate(marks):
    for b in marks[i + 1:]:
        d = np.hypot(a[0] - b[0], a[1] - b[1])
        if 0.15 < d < a[2] + b[2] + 0.1:
            k = (round(a[0]), round(a[1]), round(b[0]), round(b[1]))
            if k not in seen:
                seen.add(k)
                print(" ", nm(a[0], a[1]), "|", nm(b[0], b[1]), f"gap {d - a[2] - b[2]:.2f}")
print("-- dots under capsules")
for (p, q) in M.CAPSULES:
    p, q = np.array(p, float), np.array(q, float)
    L = q - p
    hw = M.LW * 1.05 / 2 / PT + 0.5
    for m in marks:
        x = np.array(m[:2])
        t = np.clip(np.dot(x - p, L) / np.dot(L, L), 0, 1)
        d = np.hypot(*(x - (p + t * L)))
        if d < hw + m[2] and (d > 0.2 or (0 < t < 1)):
            print(" ", tuple(p), tuple(q), "covers", nm(m[0], m[1]), f"t={t:.2f} d={d:.2f}")
print("-- dots under pills")
for pa in ax.patches:
    if isinstance(pa, FancyBboxPatch):
        x0, y0, w, h = pa.get_x(), pa.get_y(), pa.get_width(), pa.get_height()
        if w < 3 or inkey(x0, y0):
            continue
        for m in marks:
            if x0 - m[2] < m[0] < x0 + w + m[2] and y0 - m[2] < m[1] < y0 + h + m[2]:
                print("  pill at", round(x0, 1), round(y0, 1), "covers", nm(m[0], m[1]))

print("-- text over dots")
fig = plt.gcf()
fig.canvas.draw()
r = fig.canvas.get_renderer()
inv = ax.transData.inverted()
for tx in ax.texts:
    w = tx.get_text()
    if not w.strip() or len(w) < 2:
        continue
    b = tx.get_window_extent(r)
    (x0, y0), (x1, y1) = inv.transform([(b.x0, b.y0), (b.x1, b.y1)])
    if tx.get_rotation() != 0 or inkey((x0 + x1) / 2, (y0 + y1) / 2):
        continue
    for k in marks:
        if x0 - k[2] + 0.2 < k[0] < x1 + k[2] - 0.2 and y0 - k[2] + 0.2 < k[1] < y1 + k[2] - 0.2:
            print("  ", repr(w[:22]), "on", nm(k[0], k[1]))
