"""List label collisions on a poster: text on text, and text on the thick lines."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))
import importlib
import matplotlib.pyplot as plt
from matplotlib.text import Text
from shapely.geometry import LineString, box
name = sys.argv[1]
M = importlib.import_module(name)
M.main()
fig = plt.gcf()
ax = fig.axes[0]
fig.canvas.draw()
r = fig.canvas.get_renderer()
inv = ax.transData.inverted()
items = []
for t in ax.texts:
    s = t.get_text()
    if not s.strip() or t.get_rotation() != 0 or s == chr(0x267F):
        continue
    b = t.get_window_extent(r)
    (x0, y0), (x1, y1) = inv.transform([(b.x0, b.y0), (b.x1, b.y1)])
    items.append((s.replace("\n", " "), box(x0, y0, x1, y1).buffer(-0.1)))
for i, (a, A) in enumerate(items):
    for b, B in items[i + 1:]:
        if A.intersects(B):
            print("TEXT/TEXT:", a, "|", b)
lines = []
for l in ax.lines:
    if l.get_linewidth() >= 3 and len(l.get_xdata()) > 1:
        lines.append((l.get_color(), LineString(list(zip(l.get_xdata(), l.get_ydata())))))
seen = set()
for s, A in items:
    if len(s) > 28:
        continue
    for c, L in lines:
        if A.intersects(L) and (s, c) not in seen:
            seen.add((s, c))
            print("TEXT/LINE:", s, c)
