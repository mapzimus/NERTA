"""Ferry branch maps. Loops lie flat and wrap. Strips run left to right.

Writes only to output/copies/. Does not touch the finished map.

python make_ferry_poster.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, str(Path(__file__).parent))
import make_tmap as M  # noqa: E402
from station_kit import INK, WHITE  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "output" / "copies"
NAMES = {"OL": "Orange Line", "BL": "Blue Line", "RL": "Red Line", "GL": "Green Line", "CL": "Cyan Line", "YL": "Yellow Line", "CR": "Commuter rail", "SL": "Silver Line"}
PILL = {"OL": M.ORANGE, "BL": M.BLUE, "RL": M.RED, "GL": M.GREEN, "CL": M.CYAN, "YL": M.YELLOW, "CR": M.CR_TEXT_COLOR, "SL": M.SILVER}


def stadium(span, y_top, y_bot):
    mid = (y_top + y_bot) / 2
    r = (y_top - y_bot) / 2
    top = [(x, y_top) for x in np.linspace(0, span, 48)]
    right = [(span + r * np.cos(t), mid + r * np.sin(t)) for t in np.linspace(np.pi / 2, -np.pi / 2, 28)]
    bot = [(x, y_bot) for x in np.linspace(span, 0, 48)]
    left = [(r * np.cos(t), mid + r * np.sin(t)) for t in np.linspace(np.pi / 2, 3 * np.pi / 2, 28)]
    return np.array(top + right + bot + left + [top[0]])


def place(names, span):
    if len(names) == 1:
        return {names[0]: span / 2}
    return {name: x for name, x in zip(names, np.linspace(0, span, len(names)))}


def pills(ax, x, y, codes, used):
    if not codes:
        return
    width = 1.35 * len(codes) + 0.12 * (len(codes) - 1)
    left = x - width / 2
    for i, code in enumerate(codes):
        if code not in used:
            used.append(code)
        px = left + i * 1.47
        ax.add_patch(FancyBboxPatch((px, y - 0.34), 1.35, 0.68, boxstyle="round,pad=0,rounding_size=0.34",
                                    fc=PILL[code], ec=INK, lw=0.7, zorder=8))
        ax.text(px + 0.67, y, code, fontsize=7.2, fontweight="bold", color=WHITE if code != "YL" else INK,
                ha="center", va="center", zorder=9)


def dot(ax, x, y, hub):
    if hub:
        ax.scatter([x], [y], s=160, facecolor="none", edgecolor=INK, lw=1.3, zorder=6)
    ax.scatter([x], [y], s=46, color=WHITE, edgecolor=INK, lw=1.1, zorder=7)


def credit(ax, x0, y0, y1, title, outline, used):
    ax.text(x0, y1, title, fontsize=15, fontweight="bold", color=INK, va="top")
    ax.text(x0, y1 - 1.15, "FERRY", fontsize=9, fontweight="bold", color=outline, va="top")
    M.ferry_track(ax, [(x0 + 3.3, y1 - 1.45), (x0 + 5.1, y1 - 1.45)], outline, lw=2.4, z=3)
    key = "   ".join(f"{c}  {NAMES[c]}" for c in used)
    if key:
        ax.text(x0, y0 + 1.7, key, fontsize=7, color=INK, va="bottom")
    ax.text(x0, y0 + 0.85, "Map: Maxwell Howe", fontsize=7.5, color=INK, va="bottom")
    ax.text(x0, y0, "NOT A REAL MBTA MAP", fontsize=7.5, fontweight="bold", color=M.RED, va="bottom")


def draw_loop(leg):
    top, bottom = leg["top"], leg["bottom"]
    n = max(len(top), len(bottom))
    span = max(n - 1, 1) * 3.15
    y_top, y_bot = 1.7, -1.7
    pos = {**place(top, span), **place(bottom, span)}
    stops = set(top) | set(bottom)
    x0, x1 = -7.2, span + 7.2
    y0, y1 = -7.4, 7.6
    fig_w = max(8.5, (x1 - x0) * 0.34)
    fig = plt.figure(figsize=(fig_w, 5.6), facecolor=M.PAPER)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    M.ferry_track(ax, stadium(span, y_top, y_bot), leg["outline"], lw=2.4, z=4)
    for a, b in leg["cross"]:
        M.ferry_track(ax, [(pos[a], y_top), (pos[b], y_bot)], leg["outline"], lw=1.15, z=4.2)
    used = []
    for name in top:
        dot(ax, pos[name], y_top, name == leg["hub"])
        ax.annotate(name, (pos[name], y_top), xytext=(5, 8), textcoords="offset points",
                    rotation=58, fontsize=7.4, color=INK, ha="left", va="bottom", zorder=8)
        pills(ax, pos[name], y_top - 0.62, leg["pills"].get(name, []), used)
    for name in bottom:
        dot(ax, pos[name], y_bot, name == leg["hub"])
        ax.annotate(name, (pos[name], y_bot), xytext=(5, -8), textcoords="offset points",
                    rotation=-58, fontsize=7.4, color=INK, ha="left", va="top", zorder=8)
        pills(ax, pos[name], y_bot + 0.62, leg["pills"].get(name, []), used)
    if leg["hub"] not in stops:
        cap = span + 2.55 if leg["hub_end"] == "right" else -2.55
        ha = "left" if leg["hub_end"] == "right" else "right"
        ax.scatter([cap], [0], s=70, color=WHITE, edgecolor=INK, lw=1.2, zorder=7)
        ax.annotate(leg["hub"], (cap, 0), xytext=(8 if ha == "left" else -8, 0), textcoords="offset points",
                    fontsize=8, fontweight="bold", color=INK, ha=ha, va="center")
        ax.annotate("hub", (cap, 0), xytext=(8 if ha == "left" else -8, -11), textcoords="offset points",
                    fontsize=6.5, color=INK, ha=ha, va="top")
    credit(ax, x0 + 0.4, y0 + 0.3, y1 - 0.2, leg["title"], leg["outline"], used)
    save(fig, leg["key"])


def draw_strip(leg):
    stops = list(leg["stops"])
    hubs = set(leg.get("hubs") or [leg["hub"]])
    if leg["hub"] not in stops:
        stops = [leg["hub"]] + stops
    n = len(stops)
    span = max(n - 1, 1) * 3.4
    xs = np.linspace(0, span, n)
    x0, x1 = -5.5, span + 6.5
    y0, y1 = -4.8, 6.4  # room under the pills for the line names and credit
    fig_w = max(7.5, (x1 - x0) * 0.36)
    fig = plt.figure(figsize=(fig_w, 3.8), facecolor=M.PAPER)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    M.ferry_track(ax, list(zip(xs, np.zeros(n))), leg["outline"], lw=2.4, z=4)
    used = []
    for name, x in zip(stops, xs):
        dot(ax, x, 0, name in hubs)
        ax.annotate(name, (x, 0), xytext=(4, 9), textcoords="offset points",
                    rotation=58, fontsize=8, color=INK, ha="left", va="bottom", zorder=8)
        if name in hubs:
            ax.annotate("hub", (x, 0), xytext=(4, -12), textcoords="offset points",
                        fontsize=6.5, color=INK, ha="left", va="top")
        pills(ax, x, -1.15, leg["pills"].get(name, []), used)
    if leg.get("note"):
        ax.text(span / 2, -1.7, leg["note"], fontsize=8, color=INK, ha="center", va="top")
    credit(ax, x0 + 0.3, y0 + 0.15, y1 - 0.15, leg["title"], leg["outline"], used)
    save(fig, leg["key"])


def save(fig, key):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"ferry5_{key}.png"  # five-route set; never overwrites an existing copy
    if path.exists():
        raise SystemExit(f"refusing to overwrite {path}")
    fig.savefig(path, dpi=160, facecolor=M.PAPER)
    plt.close(fig)
    print("written", path.name)


if __name__ == "__main__":
    for leg in M.FERRY_LEGS:
        if leg.get("poster") is False:
            continue
        if leg["kind"] == "loop":
            draw_loop(leg)
        else:
            draw_strip(leg)
