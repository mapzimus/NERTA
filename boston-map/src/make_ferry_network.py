"""Ferry network poster: every NERTA ferry route on one sheet.

Built like the line posters: stops sit on a grid of rows, each with a level name and its transfer pills, under the T
roundel header, with a credit block and a Key. The three rivers are drawn as two-bank loops: one row of docks per bank,
an outer track run clockwise, an inner track run counterclockwise, and a thin zigzag boat crossing bank to bank.
Harbor and river boats are round dots; the North Shore, South Shore and Islands boats are high-speed streaks.
Express boats stop only at major ports (bullseye docks).

Stop lists: Max's ferry_stops.pdf (12 inner routes) and the long-distance routes of the earlier poster.
Audit: research/ferry-network-audit.md.

Writes only to output/copies/ferry_network_vN and never overwrites.
Run: python make_ferry_network.py [version] [--draft DIR] [--routes routes.json]
"""
import json
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon  # noqa: E402
from matplotlib.textpath import TextPath  # noqa: E402
from matplotlib.transforms import Affine2D  # noqa: E402
from shapely.affinity import rotate as srotate  # noqa: E402
from shapely.geometry import LineString, Point, box  # noqa: E402
from shapely.geometry import Polygon as SPoly  # noqa: E402
from shapely.geometry.polygon import orient  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from nerta_mark import draw_nerta  # noqa: E402
import make_tmap as M  # noqa: E402  (drawing helper only: M.icon)
import make_line_poster as LP  # noqa: E402  (drawing helper only: LP.roundel)
from station_kit import INK, WHITE, rounded  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "output" / "copies"
P = 5.0            # one grid step (row or column), in drawing units
K = 0.075          # inches per drawing unit
PPU = K * 72       # points per drawing unit
FLW = 5.6          # harbor and coast boat track width, points
RLW = 3.2          # river loop tracks, points
ZLW = 2.2          # river zigzag boat, points
XLW = 7.6          # the Express spine, points
RR = 2.4           # corner rounding, units
LOOP_ARROW = 1.1   # river loop arrow size, units
HUB_T = 3.4        # Langone Ferryport terminal bar thickness, units
D2 = 0.62          # half the gap between a river loop's two tracks, units

# Copied here on purpose: the main map's ferry layer is being rebuilt, so nothing below reads make_tmap's ferry data.
PAPER, WATER, COAST, RED = "#fcfcfa", "#bfe3e2", "#86bcbb", "#da291c"
F_TEAL = "#00796d"
PILL = {"RL": "#da291c", "OL": "#ed8b00", "BL": "#003da5", "GL": "#00843d", "YL": "#f5c400", "CL": "#00a9c9", "IL": "#3f3fb5",
        "SL": "#7c878e", "CR": "#80276c"}
NAMES = {"RL": "Red Line", "OL": "Orange Line", "BL": "Blue Line", "GL": "Green Line", "YL": "Yellow Line", "CL": "Cyan Line",
         "IL": "Indigo Line", "SL": "Silver Line", "CR": "Commuter rail"}
ORDER = ["RL", "OL", "BL", "GL", "YL", "CL", "IL", "SL", "CR"]

# Six color families a rider can tell apart; shades inside a family tell the routes apart.
# Checked with CIEDE2000 (scratchpad ferry_build/fam.py): every color is 15.7 or more from the T lines, commuter purple,
# high-speed gold, the bus pink, water and paper; families are 16 or more apart; shades in a family 10.8 or more apart.
FAMILIES = [("river", "River loops"), ("harbor", "Harbor"), ("south", "South Boston, Dorchester and Quincy"),
            ("north", "North Shore"), ("sse", "South Shore and the Cape"), ("islands", "The Islands")]
R = {
    "charles": dict(name="Charles River", fam="river", color="#9e00ff"),
    "mystic": dict(name="Mystic River", fam="river", color="#cf8bff", text="#8a3fd1"),
    "chelsea": dict(name="Chelsea Creek", fam="river", color="#c74ae6", text="#a62cc4"),
    "hw": dict(name="Harbor West", fam="harbor", color="#00796d"),
    "express": dict(name="Fast Ferry", fam="harbor", color="#003d36"),
    "eb": dict(name="East Boston", fam="harbor", color="#26a69a", text="#1a7d73"),
    "hi": dict(name="Harbor Islands", fam="harbor", color="#005f73"),
    "seaport": dict(name="Seaport", fam="south", color="#8a4b1c"),
    "ssi": dict(name="South Shore", fam="south", color="#b5652a"),
    "qb": dict(name="Quincy Bay", fam="south", color="#4a2a14"),
    "fore": dict(name="Fore River", fam="south", color="#a07a52", text="#7d5a35"),
    "nse": dict(name="North Shore Fast Ferry", fam="north", color="#9eb000", text="#6f7c00", fast=True),
    "sse": dict(name="South Shore Fast Ferry", fam="sse", color="#611824", fast=True),
    "isl": dict(name="Nantucket and Martha's Vineyard", fam="islands", color="#0277bd", fast=True),
}


def col(k):
    return R[k]["color"]


def tcol(k):
    return R[k].get("text", R[k]["color"])


def G(x, r):
    return (x * P, -r * P)


# ---------------------------------------------------------------------------------------------------------------
# Stops. at = grid spot (column, row; rows run down the sheet). side = label side. pills after the name.
# kind: stop, xfer (routes meet), end, hub. major = express stop. span = shared dock drawn as a bar across two tracks.
S = {}
MAJOR = {"Langone Ferryport", "Long Wharf", "Navy Yard", "Quincy", "Hull", "Lynn Harbor", "Salem Wharf", "Gloucester", "Rockport",
         "Newburyport", "Salisbury", "Plymouth Rock", "Provincetown", "Hyannis", "Woods Hole", "New Bedford", "Newport", "Vineyard Haven",
         "Nantucket Downtown"}
EVENT = ["Hatch Shell", "Agganis", "Lovejoy Wharf", "Stadium", "Encore", "Pavilion"]


def stop(name, x, r, side, pills=(), kind="stop", text=None, span=None, route=None, fs=None, pm="a"):
    """pm: where the pills go. a = after the name; o = across the line from the name (under the dot for a name on top)."""
    S[name] = dict(at=(x, r), side=side, pills=list(pills), kind=kind, text=text or name, major=name in MAJOR, span=span,
                   route=route, fs=fs, pm=pm)


# --- Charles River: Boston bank on the left column (upstream, read upward), Cambridge bank on the right (inbound, read down)
CB = ["Belmont Hill", "Winsor", "Eliot", "Weld", "Riverside", "Magazine Beach", "DeWolfe", "Resch", "Ames St", "Broad Canal",
      "Poormans", "Charlesgate", "Museum of Science", "North Point", "Duck Tours", "Paul Revere Park"]
BB = ["Nashua St", "Gronk", "Hatch Shell", "Esplanade", "Gloucester St", "BU Docks", "BU Bridge", "Agganis", "Western Ave",
      "John W. Weeks", "Newell", "Cumnock", "Herter", "Northeastern", "Arsenal St"]  # Boston bank stops 2 to 16
CHP = {"Weld": ["RL", "GL"], "DeWolfe": ["YL"], "Ames St": ["RL", "YL"], "Broad Canal": ["RL", "YL"], "Museum of Science": ["GL"],
       "North Point": ["GL", "YL"], "Paul Revere Park": ["CL"], "Nashua St": ["GL"], "BU Bridge": ["GL", "YL"], "Agganis": ["GL"]}
for i, n in enumerate(CB):
    stop(n, 3, i, "r", CHP.get(n, ()), route="charles")
for i, n in enumerate(BB):
    stop(n, 0, 14.5 - i, "l", CHP.get(n, ()), route="charles", text=None)
stop("Lovejoy Wharf", 0, 17, "l", ["GL", "OL", "CL", "CR"], "xfer")
stop("Navy Yard", 3, 17, "tr", ["CL"], "xfer")
S["Navy Yard"]["nudge"] = (0, 0.7)

# --- Mystic River: Charlestown and Somerville bank on top (read right), Everett and Chelsea bank below (read left)
MY_T = [("Little Mystic", 9.5), ("Medford St", 13.2), ("Alford St", 16.9), ("Assembly", 20.6)]
MY_B = [("Pearl St", 11.3), ("Admirals Hill", 15.0), ("Stadium", 18.4), ("Encore", 23.3)]
MYP = {"Assembly": ["OL", "CL"], "Stadium": ["CL", "YL"], "Encore": ["CL"]}
for n, x in MY_T:
    stop(n, x, 17, "t", MYP.get(n, ()), route="mystic")
for n, x in MY_B:
    stop(n, x, 19.6, "b", MYP.get(n, ()), route="mystic")
stop("Menino", 4.3, 18.3, "r", route="mystic")   # on the slanted end of the loop, Charlestown side; name inside the loop end
S["Menino"]["nudge"] = (0, -0.7)

# --- Chelsea Creek: Chelsea bank on top (read right), East Boston bank below (read left)
CC_T = [("Quigley", 30.4), ("Chelsea St", 34.2), ("Eastern Ave", 38.0)]
CC_B = [("Boston Bay", 28.5), ("Condor St", 32.3), ("Addison St", 36.1)]
for n, x in CC_T:
    stop(n, x, 17, "t", route="chelsea")
for n, x in CC_B:
    stop(n, x, 19.6, "b", route="chelsea")
stop("Suffolk Downs", 41.4, 18.3, "r", ["BL"], route="chelsea")   # the loop's east end; its bar runs on across the North Shore line

# --- Langone Ferryport, the hub (Max, November 7): one long terminal bar. Every major route leaves from its own berth on the bar
# and returns there; spurs excepted. Walkway to North Station.
LFY = 20
stop("Langone Ferryport", 1.8, LFY, "l", ["OL", "GL", "CL", "CR"], "hub", text="Langone\nFerryport", span=((0, LFY), (3.6, LFY)))
# --- Harbor West, down the downtown waterfront from Langone Ferryport
for n, r, pl in (("Battery Wharf", 20.95, []), ("Sargent's Wharf", 21.6, [])):
    stop(n, 0, r, "l", pl, route="hw")
stop("Long Wharf", 0, 22.3, "l", ["BL", "CL"], "xfer", route="hw")
stop("Central Wharf", 0, 22.95, "l", ["BL", "CL"], route="hw")
stop("Rowes Wharf", 0, 23.6, "l", ["CL", "CR"], route="hw")
stop("Dorchester Ave", 0, 24.25, "l", ["RL", "IL", "CR"], "end", route="hw")

# --- Seaport and East Boston, either side of the harbor
for n, x, pl, k in (("Martins Park", 12.6, [], "stop"), ("Fan Pier", 16.2, ["CL"], "stop"), ("Seaport", 19.8, ["CL", "YL"], "stop"),
                    ("Pavilion", 23.4, [], "end")):
    stop(n, x, 23.6, "t", pl, k, route="seaport", pm="o")
for n, x, pl, k in (("White St", 27.4, [], "stop"), ("Bennington St", 31.0, [], "stop"), ("Piers Park", 34.6, ["BL"], "stop"),
                    ("Porzio", 38.2, [], "stop"), ("Logan Dock", 41.6, ["SL"], "end")):
    stop(n, x, 23.6, "t", pl, k, route="eb", pm="o")

# --- Harbor Islands, branching down between Bennington St and Piers Park
HX = 32.9
for n, r, k in (("Deer Island", 26.4, "stop"), ("Spectacle Island", 27.4, "stop"), ("Georges Island", 28.4, "stop"), ("Long Island", 29.4, "end")):
    stop(n, HX, r, "r", (), k, route="hi")

# --- South Shore trunk at x = 10 (South Shore Express), local routes beside it at x = 9
TX, LX = 10, 9
QX, FX = 10.7, 11.4   # Quincy Bay and Fore River boats run down beside the South Shore Express
CBR = 28.45           # Carson Beach row
for n, r, pl, k in (("First St", 25.9, [], "stop"), ("Castle Island", 26.75, [], "stop"), ("M St", 27.6, ["CL"], "stop"),
                    ("Dorchester Shores", 29.3, [], "stop"), ("Old Harbor", 30.15, [], "stop"), ("Fox Point", 32, [], "stop"),
                    ("Finigan", 33, [], "end")):
    stop(n, LX, r, "l", pl, k, route="ssi")
stop("Carson Beach", LX + 0.5, CBR, "l", ["CL"], "xfer", span=((LX, CBR), (TX, CBR)))
stop("UMass Boston", LX + 0.5, 31, "l", [], "xfer", span=((LX, 31), (TX, 31)))
stop("Squantum Point", TX + 0.35, 34.5, "l", [], "xfer", span=((TX, 34.5), (QX, 34.5)))
for n, r, pl, k in (("Bay Pointe", 35.5, [], "stop"), ("King's Cove", 36.5, [], "stop"), ("Wessagusset", 37.5, [], "stop"),
                    ("Nantasket", 39.5, [], "stop")):
    stop(n, LX, r, "l", pl, k, route="fore")
stop("Hingham", LX + 0.5, 38.5, "l", [], "xfer", span=((LX, 38.5), (TX, 38.5)))
stop("Hull", LX + 0.5, 40.5, "l", [], "xfer", span=((LX, 40.5), (TX, 40.5)))
stop("Quincy", TX, 36, "r", ["RL", "CR"], route="sse")
stop("Quincy Point", TX, 37, "r", route="sse")
QB = ["Nickerson", "Thompson Island", "Moon Island", "Squantum", "Wollaston Beach", "Hough's Neck", "Nut Island"]
for i, n in enumerate(QB):
    stop(n, 16, 35.5 + i, "r", (), "end" if n == "Nut Island" else "stop", route="qb")
for n, r in (("Minot (Scituate)", 41.5), ("Mill Wharf", 42.5), ("Humarock", 43.5), ("Brant Rock / Green Harbor", 44.5), ("Duxbury", 45.7)):
    stop(n, TX, r, "r", route="sse")
S["Duxbury"]["text"] = "Duxbury via\nPowder Point Footbridge"
stop("Plymouth Rock", TX, 46.9, "r", route="sse")
stop("Sandwich Boardwalk", TX, 48.5, "br", kind="xfer", text="Sandwich\nBoardwalk")

# --- The Cape, Buzzards Bay and the Islands (the earlier poster's layout, moved and tidied)
for n, x in (("N. Barnstable / Sandy Neck", 13.6), ("Sesuit", 17.2), ("Namskaket", 20.8), ("Thumpertown", 24.4)):
    stop(n, x, 48.5, "t", text="N. Barnstable /\nSandy Neck" if n.startswith("N. Barnstable") else None)
stop("Wellfleet Pier", 28.0, 48.5, "b")
PX, OX = 29.5, 38   # Provincetown column, Outer Cape column
stop("Provincetown", PX, 45.6, "r")
stop("Race Point", PX, 43.8, "r", text="Race Point /\nP-Town Airport")
stop("Marconi Beach", OX, 45.2, "r")
stop("Coast Guard Beach", OX, 47.6, "r")
stop("Nauset Beach", OX, 50, "r")
stop("Chatham", OX, 54, "r", kind="xfer")
# South side, evenly spaced from Chatham west to Woods Hole
SOUTH_N = ["Harwich Point", "Dennis Port", "Shad Hole Rd", "Old Wharf", "West Dennis", "Yarmouth", "West Yarmouth", "Hyannis", "Hyannisport",
           "Osterville", "Popponesset", "Acapesket", "Falmouth"]
SOUTH = [(n, round(OX - (i + 1) * (OX - 4) / 14, 2)) for i, n in enumerate(SOUTH_N)]
for i, (n, x) in enumerate(SOUTH):
    stop(n, x, 54, "t" if i % 2 == 0 else "b", ["CR"] if n == "Hyannis" else [], "xfer" if n == "Yarmouth" else "stop")
S["Hyannis"]["pm"] = "o"
stop("Woods Hole", 4, 54, "tl", kind="xfer")
# Bass River: a stem up from Yarmouth to a one-way loop
YX = dict(SOUTH)["Yarmouth"]
stop("South Yarmouth", YX - 1.5, 52.0, "l")
stop("Wilbur", YX - 1.5, 50.9, "l")
stop("Bass River / Rte 28", YX + 1.5, 50.9, "r")
stop("Wrinkle Point", YX + 1.5, 52.0, "r")
# Buzzards Bay leg
stop("West Falmouth", 4, 52.6, "r")
stop("New Silver Beach", 4, 51.25, "r")
stop("Pocasset", 4, 49.9, "r")
stop("Buzzards Bay", 4, 48.5, "tr", ["CR"], kind="xfer")
S["Buzzards Bay"]["nudge"] = (0, 1.8)
stop("Onset", 1, 48.5, "b")
for i, n in enumerate(("Wareham", "Marion", "Mattapoisett", "West Island", "Fairhaven")):
    stop(n, -2, 49.6 + i * 0.92, "l")
stop("New Bedford", -2, 54, "l", ["CR"], "xfer")
stop("South Dartmouth", -2, 55.5, "l")
stop("Newport", -2, 57, "l")   # major port (Max)
stop("Fall River", -2, 58.5, "l", ["CR"], "end", route="sse")
stop("Cuttyhunk", 2, 58, "bl", kind="xfer")
# Nantucket, from Chatham round to Oak Bluffs
NX = OX + 4   # Nantucket's east shore
for n, x, r, sd in (("Wauwinet", NX, 58.4, "r"), ("Siasconset", NX, 60, "r"), ("Nobadeer", NX, 61.6, "r"), ("South Shore", NX - 2, 63.5, "b"),
                    ("Cisco", NX - 4.4, 63.5, "b"), ("Smith Point", NX - 7, 63.5, "bl"), ("Tuckernuck Is.", NX - 7, 62.2, "r"), ("Brant Point", NX - 7, 60.8, "r"),
                    ("Nantucket Downtown", NX - 7, 59.4, "r"), ("Coskata", NX - 7, 58, "r")):
    stop(n, x, r, sd)
S["Nobadeer"]["text"] = "Nantucket Memorial Airport /\nNobadeer"
# Martha's Vineyard ring, clockwise from Oak Bluffs
stop("Oak Bluffs", 23, 60, "bl", kind="xfer")
stop("Edgartown", 23, 61.8, "l")
stop("Chappaquiddick", 23, 63.4, "l")
stop("Katama Beach", 23, 65, "l")
stop("MVY Connection", 18.5, 66, "b", text="MVY Connection via\nScrubby Neck")
stop("Chilmark", 14, 66, "b")
stop("Aquinnah", 10, 66, "br", kind="xfer")
stop("Vineyard Haven", 10, 60, "br", kind="xfer")
stop("Lagoon Pond", 16.5, 60, "b")
stop("Noman's Land", 10, 68.6, "b", kind="end", route="isl")

# --- North Shore Express: Winthrop and Revere folded in (Max), coastal order heading north from Langone. The first stretch runs up
# beside Chelsea Creek at x = NLX, sharing Suffolk Downs with the creek loop; from Lynn Harbor it runs up the right side at x = NSX.
NSX, NLX = 47, 43
NS_LOW = [("Winthrop Landing", 20.55, []), ("Winthrop Beach", 19.85, []), ("Highlands Beach", 19.1, []), ("Beachmont", 17.5, ["BL"]),
          ("Revere Beach", 16.7, ["BL"]), ("Wonderland", 15.9, ["BL"])]
for n, r, pl in NS_LOW:
    stop(n, NLX, r, "r", pl, route="nse")
NS = [("Lynn Harbor", ["BL"]), ("Nahant Harbor", []), ("Swampscott", ["CR"]), ("Clifton", ["CR"]), ("Marblehead", ["CR"]),
      ("Salem Wharf", ["CR"]), ("Beverly", ["CR"]), ("Prides Crossing", []), ("Beverly Farms", ["CR"]), ("Manchester-by-the-Sea", ["CR"]),
      ("Magnolia", []), ("Gloucester", ["CR"]), ("Brier Neck", []), ("Rockport", ["CR"]), ("Annisquam", []), ("Crane Beach", []),
      ("Ipswich", []), ("Plum Island South", []), ("Plum Island Central", []), ("Plum Island North", []), ("Newburyport", []), ("Salisbury", [])]
for i, (n, pl) in enumerate(NS):
    stop(n, NSX, 13.9 - i * 0.8, "r", pl, "end" if n == "Salisbury" else "stop", route="nse")
NSE_STOPS = ["Winthrop Landing", "Winthrop Beach", "Highlands Beach", "Suffolk Downs", "Beachmont", "Revere Beach", "Wonderland"] + [n for n, _ in NS]
for n in S:
    if S[n]["pills"] and S[n]["kind"] == "stop":
        S[n]["kind"] = "xfer"

# ---------------------------------------------------------------------------------------------------------------
# River loops: closed centerline (grid), corner radius per vertex (units), the stops in rider order, the zigzag order,
# and spots for the direction arrows.
LOOPS = [
    dict(key="charles", verts=[(0, 17), (0, -1.6), (3, -1.6), (3, 17)], radii=[0, 7.5, 7.5, 0],
         stops=["Lovejoy Wharf"] + BB + CB + ["Navy Yard"],
         zig=[n for pair in zip(CB, BB[::-1] + [None]) for n in pair if n],
         # o = an arrow on the outer (clockwise) track, i = on the inner (counterclockwise) track
         arrows=[((0, 3), "o"), ((0, 6), "i"), ((0, 10), "o"), ((0, 13), "i"), ((3, 2.5), "i"), ((3, 5.5), "o"), ((3, 9.5), "i"),
                 ((3, 12.5), "o"), ((0.55, -2.4), "o"), ((2.45, -2.4), "i")]),
    dict(key="mystic", verts=[(3, 17), (25, 17), (25, 19.6), (5.6, 19.6)], radii=[0, 6.5, 6.5, 4.0],
         stops=["Menino", "Navy Yard"] + [n for n, _ in MY_T] + [n for n, _ in MY_B],
         zig=["Menino", "Little Mystic", "Pearl St", "Medford St", "Admirals Hill", "Alford St", "Stadium", "Assembly", "Encore"],
         arrows=[((11.3, 17), "o"), ((15.0, 17), "i"), ((13.2, 19.6), "i"), ((16.9, 19.6), "o"), ((25.2, 18.3), "o"), ((9.4, 19.6), "i")]),
    dict(key="chelsea", verts=[(27, 17), (41.4, 17), (41.4, 19.6), (27, 19.6)], radii=[6.5, 6.5, 6.5, 6.5],
         stops=[n for n, _ in CC_T] + [n for n, _ in CC_B] + ["Suffolk Downs"],
         zig=["Boston Bay", "Quigley", "Condor St", "Chelsea St", "Addison St", "Eastern Ave", "Suffolk Downs"],
         arrows=[((32.3, 17), "o"), ((36.1, 17), "i"), ((30.4, 19.6), "i"), ((34.2, 19.6), "o"), ((38.4, 19.6), "i")]),
]
LOOP_OF = {n: L["key"] for L in LOOPS for n in L["stops"]}

# ---------------------------------------------------------------------------------------------------------------
# Line tracks: route key, waypoints (stop names or grid spots), width in points.
T = []


def track(key, pts, lw=None, r=RR):
    T.append(dict(key=key, pts=pts, lw=lw or FLW, r=r))


def offset_path(pts, off):
    """Grid polyline shifted sideways by off units (left of travel is positive), returned in grid spots."""
    ls = LineString([G(*p) for p in pts]).offset_curve(off, join_style=2)
    return [(x / P, -y / P) for x, y in ls.coords]


# The shared path out of Langone Ferryport. Each route leaves from its own berth on the terminal bar (column x), runs beside the
# others, and branches off where its boat leaves the main path. Berths right to left, routes top to bottom, so no two cross.
def berth(x, row):
    return [(x, LFY), (x, row)]


track("charles", ["Lovejoy Wharf", (0, LFY)], RLW)                      # the Charles loop meets it at its downstream end
track("mystic", ["Navy Yard", (3.0, LFY)], RLW, 0)                       # the Mystic loop reaches it from Navy Yard
track("express", ["Navy Yard", (2.4, 17.9), (2.4, LFY)], XLW)            # the Express: Navy Yard, Langone Ferryport, Long Wharf
track("express", [(0.5, LFY), (0.5, 21.85), "Long Wharf"], XLW)
track("hw", [(0, LFY), "Battery Wharf", "Sargent's Wharf", "Long Wharf", "Central Wharf", "Rowes Wharf", "Dorchester Ave"])
track("chelsea", berth(3.5, 21.0) + [(26.0, 21.0), (26.0, 18.3), (27.0, 18.3)], RLW)   # into Chelsea Creek past East Boston
track("nse", berth(3.2, 21.3) + [(NLX, 21.3), "Winthrop Landing", "Winthrop Beach", "Highlands Beach", (NLX, 18.3), "Beachmont",
                                 "Revere Beach", "Wonderland", (NLX, 15.3), (NSX, 14.6)] + [n for n, _ in NS])
track("hi", berth(2.9, 21.6) + [(HX, 21.6), "Deer Island", "Spectacle Island", "Georges Island", "Long Island"])
track("eb", berth(2.6, 21.9) + [(25.4, 21.9), (25.4, 23.6), "White St", "Bennington St", "Piers Park", "Porzio", "Logan Dock"])
track("seaport", berth(2.15, 23.6) + ["Martins Park", "Fan Pier", "Seaport", "Pavilion"])
track("fore", berth(1.85, 23.9) + [(FX, 23.9), (FX, 34.9), "Bay Pointe", "King's Cove", "Wessagusset", (LX, 38.5), "Nantasket", (LX, 40.5)])
track("qb", berth(1.55, 24.2) + [(QX, 24.2), (QX, 34.5), (16, 34.5)] + QB)
track("ssi", berth(0.95, 24.8) + [(LX, 24.8), "First St", "Castle Island", "M St", (LX, CBR), "Dorchester Shores", "Old Harbor", (LX, 31),
                                  "Fox Point", "Finigan"])
# Split at the corner stops (Sandwich Boardwalk, Chatham, New Bedford, Buzzards Bay, Cuttyhunk, Coskata, Smith Point, Oak Bluffs,
# Aquinnah, Vineyard Haven): each piece
# runs straight into the dot's center, so a rounded corner never hooks past the dot.
track("sse", berth(1.25, 24.5) + [(TX, 24.5), (TX, CBR), (TX, 31), (TX, 34.5), "Quincy", "Quincy Point", (TX, 38.5), (TX, 40.5)]
      + ["Minot (Scituate)", "Mill Wharf", "Humarock", "Brant Rock / Green Harbor", "Duxbury", "Plymouth Rock", "Sandwich Boardwalk"])
track("sse", ["Sandwich Boardwalk", "N. Barnstable / Sandy Neck", "Sesuit", "Namskaket", "Thumpertown", "Wellfleet Pier", (PX, 47), "Provincetown",
              "Race Point", (PX, 42.5), (OX, 42.5), "Marconi Beach", "Coast Guard Beach", "Nauset Beach", "Chatham"])
track("sse", ["Chatham"] + [n for n, _ in SOUTH] + ["Woods Hole", "New Bedford"])
track("sse", ["New Bedford", "South Dartmouth", "Newport", "Fall River"])
# Canal Pass: the shortcut through the Cape Cod Canal
track("sse", ["Sandwich Boardwalk", "Buzzards Bay"])
# Buzzards Bay leg, Woods Hole up to the canal and round the mainland shore to New Bedford
track("sse", ["Woods Hole", "West Falmouth", "New Silver Beach", "Pocasset", "Buzzards Bay"])
track("sse", ["Buzzards Bay", "Onset", (-2, 48.5), "Wareham", "Marion", "Mattapoisett", "West Island", "Fairhaven", "New Bedford"])
# Bass River: a stem from Yarmouth, then a loop one way round
BASS = [(YX, 52.6), (YX - 1.5, 52.6), "South Yarmouth", "Wilbur", (YX - 1.5, 50.3), (YX + 1.5, 50.3), "Bass River / Rte 28", "Wrinkle Point",
        (YX + 1.5, 52.6), (YX, 52.6)]
track("sse", ["Yarmouth", (YX, 52.6)], r=0)
track("sse", BASS, r=1.2)
# New Bedford to Cuttyhunk, shared by two routes side by side, then on to Oak Bluffs and to Aquinnah
# Side by side from New Bedford, then both run into Cuttyhunk's dot
track("sse", offset_path([(-2, 54), (1.2, 57.2)], 0.95) + ["Cuttyhunk"])
track("isl", offset_path([(-2, 54), (1.2, 57.2)], -0.95) + ["Cuttyhunk"])
track("sse", ["Cuttyhunk", (21, 58), "Oak Bluffs"])
track("isl", ["Cuttyhunk", (2, 61), (7, 66), "Aquinnah"])
track("isl", ["Aquinnah", "Noman's Land"], r=0)
track("isl", ["Chatham", (NX, 58), "Wauwinet", "Siasconset", "Nobadeer", (NX, 63.5), "South Shore", "Cisco", "Smith Point"])
track("isl", ["Smith Point", "Tuckernuck Is.", "Brant Point", "Nantucket Downtown", "Coskata"])
track("isl", ["Coskata", (25, 58), "Oak Bluffs"])
track("isl", ["Lagoon Pond", "Oak Bluffs"])
MV_RING = ["Oak Bluffs", "Edgartown", "Chappaquiddick", "Katama Beach", (23, 66), "MVY Connection", "Chilmark", "Aquinnah"]
track("isl", MV_RING)
track("isl", ["Aquinnah", "Vineyard Haven"])
track("isl", ["Vineyard Haven", "Lagoon Pond"])
track("isl", ["Vineyard Haven", "Woods Hole"], r=0)

# ---------------------------------------------------------------------------------------------------------------
REG = {"line": [], "dot": [], "pill": []}   # shapely shapes for the overlap check
TEXTS = []
FONT = FontProperties(family="Arial")


def width(text, fs, weight="normal"):
    w = 0
    for line in text.split("\n"):
        tp = TextPath((0, 0), line, size=fs, prop=FontProperties(family="Arial", weight=weight))
        w = max(w, tp.get_extents().width)
    return w / PPU


def txt(ax, x, y, s, fs, weight="normal", ha="left", va="center", color=INK, z=11, check=True, ls=1.05):
    s = s.replace("'", "’")  # curly apostrophes, as on the main map
    t = ax.text(x, y, s, fontsize=fs, fontweight=weight, color=color, ha=ha, va=va, zorder=z, linespacing=ls, family="Arial")
    if check:
        TEXTS.append((t, 0, (x, y)))
    return t


def grid_pt(p):
    return G(*S[p]["at"]) if isinstance(p, str) else G(*p)


def ferry_track(ax, xy, color, lw=3.4, z=2.6, casing=True, fast=False, phase=0.0):
    """Round dots in the route color on a white wake, so ferries never read as subway. High-speed boats are streaks."""
    xy = np.asarray(xy, float)
    if casing:
        ax.plot(*xy.T, color=WHITE, lw=lw + 2.6, solid_capstyle="round", solid_joinstyle="round", zorder=z)
    ax.plot(*xy.T, color=color, lw=lw, ls=(phase, (1.5, 1.6) if fast else (0.01, 1.9)), dash_capstyle="round", zorder=z + 0.1)


def arrow(ax, x, y, ang, color, size=1.5, z=6, edge=WHITE):
    a = np.radians(ang)
    u, v = np.array([np.cos(a), np.sin(a)]), np.array([-np.sin(a), np.cos(a)])
    p = np.array([x, y])
    tri = [p + u * size * 1.2, p - u * size * 0.7 + v * size * 0.5, p - u * size * 0.7 - v * size * 0.5]
    if edge == WHITE:
        ax.add_patch(Polygon(tri, closed=True, fc=WHITE, ec=WHITE, lw=3.2, zorder=z - 0.01, joinstyle="round"))
    ax.add_patch(Polygon(tri, closed=True, fc=color, ec=edge, lw=0.9, zorder=z, joinstyle="miter"))


def track_arrow(ax, pts, r, near, color, size=1.6, lw=FLW, z=6):
    """An arrow on a high-speed track, pointing the way the track is drawn, slid to the nearest spot where its tip and tail
    both fall in a gap between streaks, so no cut-off streak shows beside it."""
    xy = rounded([grid_pt(p) for p in pts], r) if r else np.array([grid_pt(p) for p in pts], float)
    ln = LineString(xy)
    per, gap_c = 3.1 * lw / PPU, 2.3 * lw / PPU      # dash pattern (1.5, 1.6) x lw: one period, and the middle of its gap
    tip = 1.2 * size
    sa = round((ln.project(Point(G(*near))) + tip - gap_c) / per) * per + gap_c - tip
    a, b = ln.interpolate(sa - 0.4), ln.interpolate(sa + 0.4)
    p = ln.interpolate(sa)
    arrow(ax, p.x, p.y, np.degrees(np.arctan2(b.y - a.y, b.x - a.x)), color, size, z)


def round_closed(pts, radii, n=14):
    pts = [np.array(p, float) for p in pts]
    out = []
    for i, b in enumerate(pts):
        a, c, r = pts[i - 1], pts[(i + 1) % len(pts)], radii[i]
        if r <= 0:
            out.append(b)
            continue
        u, v = a - b, c - b
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        d = min(r, lu / 2, lv / 2)
        p0, p2 = b + u / lu * d, b + v / lv * d
        for t in np.linspace(0, 1, n):
            out.append((1 - t) ** 2 * p0 + 2 * t * (1 - t) * b + t ** 2 * p2)
    return np.array(out)


def ring_dir(ring, p, step=0.8):
    s = ring.project(Point(p))
    a, b = ring.interpolate(s), ring.interpolate((s + step) % ring.length)
    v = np.array([b.x - a.x, b.y - a.y])
    return np.array([a.x, a.y]), v / np.linalg.norm(v)


# ---------------------------------------------------------------------------------------------------------------
SYM = {}   # stop name -> (shapely shape, bounding box)
DOT = {"stop": (7.0, 1.0), "xfer": (10.4, 2.0), "end": (12.6, 3.0), "major": (12.8, 2.6), "hub": (16.4, 3.2)}


def circle_sym(ax, n, x, y, kind, major, edge=INK):
    d, lw = DOT["hub" if kind == "hub" else ("major" if major and kind != "end" else kind)]
    if major and kind == "end":
        d, lw = DOT["end"]
    ax.scatter([x], [y], s=(d + lw + 2.6) ** 2, color=WHITE, lw=0, zorder=8.9)   # white underlay: no track dot peeks past the edge
    ax.scatter([x], [y], s=d ** 2, color=WHITE, edgecolor=edge, lw=lw, zorder=9)
    if major or kind == "hub":
        ax.scatter([x], [y], s=(d * 0.36) ** 2, color=INK, lw=0, zorder=9.2)
    r = (d / 2 + lw / 2) / PPU
    shp = Point(x, y).buffer(r)
    SYM[n] = (shp, shp.bounds)
    REG["dot"].append((n, shp))


def bar_sym(ax, n, a, b, thick, lw, major=False, z=9, dot=4.6):
    """A white bar with round ends from a to b (drawing units): one dock served by two tracks."""
    (x0, y0), (x1, y1) = a, b
    if abs(y1 - y0) > 1e-6 and abs(x1 - x0) > 1e-6:   # a slanted bar: drawn flat, then turned about its middle
        ln, cx, cy = np.hypot(x1 - x0, y1 - y0), (x0 + x1) / 2, (y0 + y1) / 2
        p = FancyBboxPatch((cx - ln / 2 - thick / 2, cy - thick / 2), ln + thick, thick, boxstyle=f"round,pad=0,rounding_size={thick / 2}",
                           fc=WHITE, ec=INK, lw=lw, zorder=z)
        p.set_transform(Affine2D().rotate_deg_around(cx, cy, np.degrees(np.arctan2(y1 - y0, x1 - x0))) + ax.transData)
        ax.add_patch(p)
        shp = LineString([a, b]).buffer(thick / 2)
        SYM[n] = (shp, shp.bounds)
        REG["dot"].append((n, shp))
        return
    if abs(y1 - y0) < 1e-6:
        xa, xb = sorted((x0, x1))
        bb = (xa - thick / 2, y0 - thick / 2, xb + thick / 2, y0 + thick / 2)
    else:
        ya, yb = sorted((y0, y1))
        bb = (x0 - thick / 2, ya - thick / 2, x0 + thick / 2, yb + thick / 2)
    ax.add_patch(FancyBboxPatch((bb[0], bb[1]), bb[2] - bb[0], bb[3] - bb[1], boxstyle=f"round,pad=0,rounding_size={thick / 2}",
                                fc=WHITE, ec=INK, lw=lw, zorder=z))
    if major:
        cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        ax.scatter([cx], [cy], s=dot ** 2, color=INK, lw=0, zorder=z + 0.2)
    shp = box(*bb)
    SYM[n] = (shp, bb)
    REG["dot"].append((n, shp))


def draw_loop(ax, L):
    key = L["key"]
    c = col(key)
    cl = round_closed([G(*p) for p in L["verts"]], L["radii"])
    poly = orient(SPoly(cl), sign=-1.0)
    outer = orient(poly.buffer(D2, join_style=1), sign=-1.0).exterior
    inner = orient(poly.buffer(-D2, join_style=1), sign=-1.0).exterior
    water = poly.buffer(-D2 - 0.75, join_style=1)
    ax.add_patch(Polygon(np.array(water.exterior.coords), fc=WATER, ec="none", zorder=1.6))
    for ring in (outer, inner):
        xy = np.array(ring.coords)
        ax.plot(*xy.T, color=WHITE, lw=RLW + 2.6, solid_capstyle="round", solid_joinstyle="round", zorder=3)
        REG["line"].append((key, LineString(xy).buffer((RLW + 2.6) / PPU / 2)))
    for ring in (outer, inner):
        ferry_track(ax, np.array(ring.coords), c, lw=RLW, z=4, casing=False)
    # arrows: outer track clockwise, inner track counterclockwise
    for a, which in L["arrows"]:
        ring, sgn = (outer, 1) if which == "o" else (inner, -1)
        p, v = ring_dir(ring, G(*a))
        arrow(ax, p[0], p[1], np.degrees(np.arctan2(sgn * v[1], sgn * v[0])), tcol(key), LOOP_ARROW, 6.5)
    # stops: a white bar across both tracks; corners and major ports get a round dock
    ring0 = poly.exterior
    attach = {}
    for n in L["stops"]:
        s = S[n]
        x, y = G(*s["at"])
        p, v = ring_dir(ring0, (x, y), 0.6)
        nrm = np.array([-v[1], v[0]])
        if not poly.contains(Point(x + nrm[0] * 1.0, y + nrm[1] * 1.0)):
            nrm = -nrm
        hl = D2 + 0.95
        if s["major"] or n in ("Lovejoy Wharf", "Navy Yard"):
            if n not in SYM:
                circle_sym(ax, n, x, y, "xfer", s["major"])
        elif n == "Suffolk Downs":   # one dock for the creek loop and the North Shore boat
            bar_sym(ax, n, (x - hl, y), (G(NLX, 0)[0], y), 2.1, 2.0)
        else:
            lw = 1.7 if s["pills"] else 1.0
            bar_sym(ax, n, (x - nrm[0] * hl, y - nrm[1] * hl), (x + nrm[0] * hl, y + nrm[1] * hl), 1.25, lw)
        attach[n] = (x + nrm[0] * (hl - 0.35), y + nrm[1] * (hl - 0.35))
    zz = np.array([attach[n] for n in L["zig"]])
    ax.plot(*zz.T, color=WHITE, lw=ZLW + 2.2, solid_capstyle="round", solid_joinstyle="round", zorder=5)
    ax.plot(*zz.T, color=c, lw=ZLW, ls=(0, (0.01, 1.7)), dash_capstyle="round", zorder=5.1)
    REG["line"].append((key + " zigzag", LineString(zz).buffer((ZLW + 2.2) / PPU / 2)))
    return poly


def dot_run(ax, xy, cuts, color, lw, docks, z=4.1):
    """Round dots about the dash pattern's step apart, spread evenly over the clear stretch between waypoints (docks and
    corners). No dot touches a dock, so none peeks half out from under one."""
    ln = LineString(xy)
    step = 1.91 * lw / PPU
    rd = lw / 2 / PPU + 0.15

    def clear(t):
        return not len(docks.query(ln.interpolate(t).buffer(rd), predicate="intersects"))

    pos = sorted({0.0, ln.length} | {ln.project(Point(c)) for c in cuts})
    pts = []
    for a, b in zip(pos, pos[1:]):
        if b - a < 1e-6:
            continue
        a1, b1 = a, b
        while a1 < b and not clear(a1):
            a1 += 0.05
        while b1 > a and not clear(b1):
            b1 -= 0.05
        if a1 >= b1:
            if clear((a + b) / 2):
                pts.append((a + b) / 2)
            continue
        gaps = round((b1 - a1) / step)
        if gaps and (b1 - a1) / gaps < 0.9 * step:   # never crowd the dots: one fewer gap instead
            gaps -= 1
        pts += [(a1 + b1) / 2] if gaps == 0 else list(np.linspace(a1, b1, gaps + 1))
    xs = np.array([(p.x, p.y) for p in (ln.interpolate(t) for t in pts)])
    ax.scatter(xs[:, 0], xs[:, 1], s=lw ** 2, color=color, lw=0, zorder=z)


def draw_tracks(ax):
    paths = []
    for t in T:
        pts = [grid_pt(p) for p in t["pts"]]
        xy = rounded(pts, t["r"]) if t["r"] else np.array(pts, float)
        paths.append((t["key"], xy, t["lw"], pts))
    for key, xy, lw, _ in paths:
        ax.plot(*xy.T, color=WHITE, lw=lw + 2.6, solid_capstyle="round", solid_joinstyle="round", zorder=3)
        REG["line"].append((key, LineString(xy).buffer((lw + 2.6) / PPU / 2)))
    docks = STRtree([d for _, d in REG["dot"]])
    for key, xy, lw, pts in paths:
        if R[key].get("fast"):
            ferry_track(ax, xy, col(key), lw=lw, z=4, casing=False, fast=True)
        else:
            dot_run(ax, xy, pts, col(key), lw, docks)
    return paths


def pill(ax, x0, x1, y, code, z=8):
    h = 2.9
    ax.add_patch(FancyBboxPatch((x0, y - h / 2), x1 - x0, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=PILL[code], ec=PAPER, lw=1.2, zorder=z))
    ax.text((x0 + x1) / 2, y - 0.08, code, fontsize=8.6, fontweight="bold", color=INK if code == "YL" else WHITE, ha="center", va="center",
            zorder=z + 0.5, family="Arial")
    REG["pill"].append(box(x0, y - h / 2, x1, y + h / 2))


def pills_row(ax, x, y, codes, sign):
    """Pills read outward from x, always left to right on the page."""
    w, gap = 6.6, 0.35
    codes = sorted(codes, key=ORDER.index)
    total = len(codes) * w + (len(codes) - 1) * gap
    x0 = x if sign > 0 else x - total
    for c in codes:
        pill(ax, x0, x0 + w, y, c)
        x0 += w + gap


def draw_labels(ax):
    for n, s in S.items():
        if n not in SYM:
            continue
        _, (bx0, by0, bx1, by1) = SYM[n]
        ndx, ndy = s.get("nudge", (0, 0))
        bx0, bx1, by0, by1 = bx0 + ndx, bx1 + ndx, by0 + ndy, by1 + ndy
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        bold = s["kind"] in ("end", "hub")
        text = s["text"].upper() if bold else s["text"]
        weight = "bold" if (bold or s["major"]) else "normal"
        fs = s["fs"] or (12.4 if s["kind"] == "hub" else 11.4 if bold else 11.2 if s["major"] else 10.8)
        w = width(text, fs, weight)
        nl = text.count("\n") + 1
        hgt = 0.62 * fs / PPU * 1.1 * nl
        g = 1.3
        side = s["side"]
        if side == "r":
            txt(ax, bx1 + g, cy - 0.05, text, fs, weight, "left", "center")
            tx0, tx1, ty = bx1 + g, bx1 + g + w, cy
        elif side == "l":
            txt(ax, bx0 - g, cy - 0.05, text, fs, weight, "right", "center")
            tx0, tx1, ty = bx0 - g - w, bx0 - g, cy
        elif side in ("t", "b"):
            up = side == "t"
            y = by1 + 0.9 if up else by0 - 0.9
            txt(ax, cx, y, text, fs, weight, "center", "bottom" if up else "top")
            tx0, tx1 = cx - w / 2, cx + w / 2
            ty = y + (hgt / 2 if up else -hgt / 2) if nl == 1 else (y + 0.62 * fs / PPU * 0.55 if up else y - 0.62 * fs / PPU * 0.55)
        else:
            right, up = side[1] == "r", side[0] == "t"
            x = bx1 + 0.4 if right else bx0 - 0.4
            y = by1 + 0.4 if up else by0 - 0.4
            txt(ax, x, y, text, fs, weight, "left" if right else "right", "bottom" if up else "top")
            tx0, tx1 = (x, x + w) if right else (x - w, x)
            ty = y + (0.62 * fs / PPU * 0.55 if up else -0.62 * fs / PPU * 0.55)
        if s["pills"]:
            if s["pm"] == "o" and side in ("t", "b"):  # across the line: under the dot for a name on top
                n_p = len(s["pills"])
                tot = n_p * 6.6 + (n_p - 1) * 0.35
                py = by0 - 0.7 - 1.45 if side == "t" else by1 + 0.7 + 1.45
                pills_row(ax, cx - tot / 2, py, s["pills"], 1)
            elif s["pm"] == "o" and side in ("l", "r"):  # beside the dot, on the side away from the name, set from the dot's center
                pills_row(ax, cx + 2.5, cy, s["pills"], 1) if side == "l" else pills_row(ax, cx - 2.5, cy, s["pills"], -1)  # so a column lines up
            elif side in ("l", "tl", "bl"):
                pills_row(ax, tx0 - 1.0, ty, s["pills"], -1)
            else:
                pills_row(ax, tx1 + 1.0, ty, s["pills"], 1)


def draw_stops(ax):
    for n, s in S.items():
        if n in LOOP_OF:
            continue
        x, y = G(*s["at"])
        if s["span"]:
            a, b = G(*s["span"][0]), G(*s["span"][1])
            if s["kind"] == "hub":   # Langone Ferryport: the terminal bar every route leaves from
                bar_sym(ax, n, a, b, HUB_T, 3.2, True, dot=7.4)
            else:
                bar_sym(ax, n, a, b, 2.1, 2.0, s["major"])
            continue
        key = s["route"]
        edge = col(key) if s["kind"] == "end" and key else INK
        circle_sym(ax, n, x, y, s["kind"], s["major"], edge)


# ---------------------------------------------------------------------------------------------------------------
def stadium(x0, x1, yc, r, n=30):
    top = [(x, yc + r) for x in np.linspace(x0, x1, 12)]
    right = [(x1 + r * np.cos(t), yc + r * np.sin(t)) for t in np.linspace(np.pi / 2, -np.pi / 2, n)]
    bot = [(x, yc - r) for x in np.linspace(x1, x0, 12)]
    left = [(x0 + r * np.cos(t), yc + r * np.sin(t)) for t in np.linspace(-np.pi / 2, -3 * np.pi / 2, n)]
    return np.array(top + right + bot + left + [top[0]])


PANEL_FC, PANEL_EC = "#f2f5f5", "#c9d3d3"


def panel(ax, x0, y0, x1, y1, z=1.0):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=3", fc=PANEL_FC, ec=PANEL_EC, lw=1.0, zorder=z))


def wrap(s, n):
    return "\n".join(textwrap.fill(p, n) for p in s.split("\n"))


def mini_loop(ax, x0, x1, yc, r, mode, c):
    """A small two-bank loop for the explainer. mode: cw, ccw or zig."""
    cl = stadium(x0, x1, yc, r)
    poly = orient(SPoly(cl), sign=-1.0)
    outer = orient(poly.buffer(D2, join_style=1), sign=-1.0).exterior
    inner = orient(poly.buffer(-D2, join_style=1), sign=-1.0).exterior
    ax.add_patch(Polygon(np.array(poly.buffer(-D2 - 0.75).exterior.coords), fc=WATER, ec="none", zorder=1.6))
    grey = "#cfd2d8"
    for ring, on in ((outer, mode == "cw"), (inner, mode == "ccw")):
        ferry_track(ax, np.array(ring.coords), c if on else grey, lw=RLW, z=4.2 if on else 4, casing=True)
    xs = np.linspace(x0 + 1.5, x1 - 1.5, 4)
    if mode == "zig":
        pts = []
        for k, xx in enumerate(xs):
            pts.append((xx, yc + r - 1.3))
            pts.append((xx + (xs[1] - xs[0]) / 2, yc - r + 1.3)) if k < len(xs) - 1 else None
        zz = np.array(pts)
        ax.plot(*zz.T, color=WHITE, lw=ZLW + 2.2, solid_capstyle="round", zorder=5)
        ax.plot(*zz.T, color=c, lw=ZLW, ls=(0, (0.01, 1.7)), dash_capstyle="round", zorder=5.1)
        bot = xs[:-1] + (xs[1] - xs[0]) / 2
    else:
        bot = xs
        ring, sgn = (outer, 1) if mode == "cw" else (inner, -1)
        for a in ((x0 - r, yc), (x1 + r, yc), ((xs[1] + xs[2]) / 2, yc + r), ((xs[0] + xs[1]) / 2, yc - r)):
            p, v = ring_dir(ring, a)
            arrow(ax, p[0], p[1], np.degrees(np.arctan2(sgn * v[1], sgn * v[0])), c, LOOP_ARROW, 6.5)
    for xx, yy in [(xx, yc + r) for xx in xs] + [(xx, yc - r) for xx in bot]:
        ax.add_patch(FancyBboxPatch((xx - 0.62, yy - 1.57), 1.24, 3.14, boxstyle="round,pad=0,rounding_size=0.62", fc=WHITE, ec=INK, lw=0.9, zorder=9))


def river_explainer(ax, x0, y1):
    c = col("charles")
    txt(ax, x0, y1, "HOW THE RIVER BOATS RUN", 11.6, "bold", "left", "top")
    txt(ax, x0, y1 - 5.6, "Each river is a loop of docks: one row for each bank, facing the other bank. Three kinds of boat use it.",
        9.0, "normal", "left", "top")
    rows = [("cw", "Clockwise loop boat", "Rides the outer track: along one bank, round the end,\nback along the other bank and round again."),
            ("ccw", "Counterclockwise loop boat", "Rides the inner track: the same docks,\nin the other direction."),
            ("zig", "Zigzag boat", "Rides the thin line across the water: bank to bank,\ndock to dock, so riders can cross the river.")]
    for i, (mode, head, body) in enumerate(rows):
        yc = y1 - 20.5 - i * 18.5
        mini_loop(ax, x0 + 9, x0 + 33, yc, 5.6, mode, c)
        txt(ax, x0 + 48, yc + 3.6, head, 10.2, "bold", "left", "center")
        txt(ax, x0 + 48, yc - 2.0, body, 9.0, "normal", "left", "center", ls=1.2)


def express_explainer(ax, x0, y1, w):
    txt(ax, x0, y1, "FAST FERRIES AND MAJOR PORTS", 11.0, "bold", "left", "top")
    y = y1 - 19.0
    xs = np.linspace(x0 + 3.5, x0 + w - 3.5, 7)
    big = [0, 3, 6]
    ferry_track(ax, [(xs[0], y), (xs[-1], y)], col("sse"), lw=FLW, z=4, casing=True, fast=True)
    for a, b in zip(big, big[1:]):
        xa, xb = xs[a], xs[b]
        t = np.linspace(0, np.pi, 40)
        arc = np.column_stack([(xa + xb) / 2 - (xb - xa) / 2 * np.cos(t), y + 2.0 + 7.0 * np.sin(t)])
        ax.plot(*arc.T, color=INK, lw=1.4, zorder=4.5, solid_capstyle="round")
        arrow(ax, (xa + xb) / 2, y + 9.0, 0, INK, 1.0, 4.6, edge=INK)
    for k, xx in enumerate(xs):
        if k in big:
            ax.scatter([xx], [y], s=12.8 ** 2, color=WHITE, edgecolor=INK, lw=2.6, zorder=9)
            ax.scatter([xx], [y], s=(12.8 * 0.36) ** 2, color=INK, lw=0, zorder=9.2)
        else:
            ax.scatter([xx], [y], s=7.0 ** 2, color=WHITE, edgecolor=INK, lw=1.0, zorder=9)
    txt(ax, (xs[0] + xs[3]) / 2, y + 11.4, "fast ferry trip: major ports only", 8.8, "normal", "center", "bottom")
    txt(ax, (xs[3] + xs[6]) / 2, y - 3.2, "local trip: every dock", 8.8, "normal", "center", "top")
    body = ("On the North Shore Fast Ferry, the South Shore Fast Ferry and the Islands boats, fast ferry trips stop only at the major "
            "ports, drawn as a dot inside a ring. Local trips stop at every dock. "
            "The Fast Ferry (FF) shuttle runs Navy Yard, Langone Ferryport, Long Wharf, nonstop between them, at all times.")
    t = txt(ax, x0, y - 9.5, wrap(body, 50), 9.8, "normal", "left", "top", ls=1.25)
    ports = ("Major ports: " + ", ".join(sorted(MAJOR, key=lambda n: ORDER_PORTS.index(n))) + ".")
    txt(ax, x0, y - 27.5, wrap(ports, 50), 9.8, "normal", "left", "top", ls=1.25)


ORDER_PORTS = ["Langone Ferryport", "Long Wharf", "Navy Yard", "Quincy", "Hull", "Lynn Harbor", "Salem Wharf", "Gloucester", "Rockport",
               "Newburyport", "Salisbury", "Plymouth Rock", "Provincetown", "Hyannis", "Woods Hole", "New Bedford", "Newport",
               "Vineyard Haven", "Nantucket Downtown"]


def notice(ax, x0, y0, x1, y1):
    """A passenger notice, set like a station sign: dark title bar, short paragraphs."""
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=2", fc=WHITE, ec=INK, lw=1.4, zorder=1.2))
    ax.add_patch(FancyBboxPatch((x0, y1 - 6.6), x1 - x0, 6.6, boxstyle="round,pad=0,rounding_size=2", fc=INK, ec=INK, lw=1.4, zorder=1.3))
    ax.add_patch(FancyBboxPatch((x0, y1 - 6.6), x1 - x0, 3.0, boxstyle="square,pad=0", fc=INK, ec="none", zorder=1.35))
    txt(ax, x0 + 3.5, y1 - 3.3, "PASSENGER NOTICE", 11.4, "bold", "left", "center", color=WHITE)
    paras = [("Boats run 24 hours a day, 7 days a week.", "bold"),
             ("Every major route starts and ends at Langone Ferryport.", "normal"),
             ("Every boat is automated. There is no crew on board.", "normal"),
             ("Special-event boats: extra boats run to the event docks before and after games, concerts and shows.", "normal"),
             ("Event docks: Hatch Shell, Agganis, Lovejoy Wharf, Stadium, Encore and Pavilion.", "normal"),
             ("Pods on demand at every dock.", "bold")]
    y = y1 - 10.6
    for p, wt in paras:
        t = wrap(p, 40)
        txt(ax, x0 + 3.5, y, t, 10.4, wt, "left", "top", ls=1.25)
        y -= (t.count("\n") + 1) * 10.4 * 1.25 / PPU + 2.2


def key_sample(ax, x, y, k, length=9.0):
    lw = XLW * 0.75 if k == "express" else (RLW + 0.6 if R[k]["fam"] == "river" else FLW * 0.85)
    ferry_track(ax, [(x, y), (x + length, y)], col(k), lw=lw, z=12, casing=True, fast=R[k].get("fast", False))


def key_routes(ax, x0, y1):
    txt(ax, x0, y1, "ROUTES", 11.0, "bold", "left", "top")
    y = y1 - 8.4
    for fam, fname in FAMILIES:
        txt(ax, x0, y, fname.upper(), 8.0, "bold", "left", "center", color="#4a4f57")
        y -= 4.0
        for k, d in R.items():
            if d["fam"] != fam:
                continue
            key_sample(ax, x0 + 0.5, y, k)
            txt(ax, x0 + 12.5, y - 0.05, d["name"], 9.2, "normal", "left", "center")
            y -= 4.0
        y -= 1.0
    return y


def key_symbols(ax, x0, y1):
    txt(ax, x0, y1, "KEY", 11.0, "bold", "left", "top")
    row = 4.7
    y = y1 - 9.0
    c = col("charles")
    boats = [("dots", "Harbor and river boats: round dots"),
             ("streak", "High-speed boats: streaks, on the coast and to the Islands"),
             ("express", "Fast Ferry (FF): Navy Yard, Langone Ferryport, Long Wharf, at all times"),
             ("cw", "River loop, outer track: boats run clockwise"),
             ("ccw", "River loop, inner track: boats run counterclockwise"),
             ("zig", "River zigzag: crosses bank to bank at every dock"),
             ("oneway", "Arrow on a loop: boats run one way round")]
    for i, (k, t) in enumerate(boats):
        yy = y - i * row
        xa, xb = x0 + 0.5, x0 + 9.5
        if k in ("dots", "streak"):
            ferry_track(ax, [(xa, yy), (xb, yy)], INK, lw=FLW * 0.85, z=12, casing=True, fast=k == "streak")
        elif k == "express":
            ferry_track(ax, [(xa, yy), (xb, yy)], col("express"), lw=XLW * 0.75, z=12, casing=True)
        elif k in ("cw", "ccw"):
            for off, on in ((1.0, k == "cw"), (-1.0, k == "ccw")):
                ferry_track(ax, [(xa, yy + off * 0.75), (xb, yy + off * 0.75)], c if on else "#cfd2d8", lw=RLW, z=12, casing=True)
            arrow(ax, (xa + xb) / 2, yy + (0.75 if k == "cw" else -0.75), 0 if k == "cw" else 180, c, 1.1, 12.5)
        elif k == "zig":
            zz = np.array([(xa, yy + 1.2), (xa + 2.25, yy - 1.2), (xa + 4.5, yy + 1.2), (xa + 6.75, yy - 1.2), (xb, yy + 1.2)])
            ax.plot(*zz.T, color=WHITE, lw=ZLW + 2.2, solid_capstyle="round", solid_joinstyle="round", zorder=12)
            ax.plot(*zz.T, color=c, lw=ZLW, ls=(0, (0.01, 1.7)), dash_capstyle="round", zorder=12.1)
        else:
            ferry_track(ax, [(xa, yy), (xb, yy)], INK, lw=FLW * 0.85, z=12, casing=True, fast=True)
            arrow(ax, (xa + xb) / 2, yy, 0, INK, 1.4, 12.5)
        txt(ax, x0 + 12.5, yy - 0.05, t, 9.6, "normal", "left", "center")
    x2 = x0 + 90
    docks = [("stop", "Dock"), ("xfer", "Transfer, or where routes meet"), ("major", "Major port: fast ferries stop here"),
             ("hub", "Main hub: Langone Ferryport, where every major route starts"), ("end", "End of the route"), ("bar", "Dock shared by two routes side by side"),
             ("cap", "River dock: one bar across both tracks"), ("acc", "All docks accessible")]
    for i, (k, t) in enumerate(docks):
        yy = y - i * row
        cx = x2 + 4.5
        if k == "hub":
            ax.add_patch(FancyBboxPatch((cx - 2.6 - HUB_T / 2, yy - HUB_T / 2), 5.2 + HUB_T, HUB_T,
                                        boxstyle=f"round,pad=0,rounding_size={HUB_T / 2}", fc=WHITE, ec=INK, lw=3.2, zorder=12))
            ax.scatter([cx], [yy], s=7.4 ** 2, color=INK, lw=0, zorder=12.2)
        elif k in ("stop", "xfer", "end", "major"):
            d, lw = DOT[k]
            ax.scatter([cx], [yy], s=d ** 2, color=WHITE, edgecolor=col("sse") if k == "end" else INK, lw=lw, zorder=12)
            if k in ("major", "hub"):
                ax.scatter([cx], [yy], s=(d * 0.36) ** 2, color=INK, lw=0, zorder=12.2)
        elif k == "bar":
            for dy, kk in ((1.3, "ssi"), (-1.3, "sse")):
                ferry_track(ax, [(cx - 4.0, yy + dy), (cx + 4.0, yy + dy)], col(kk), lw=FLW * 0.75, z=11.8, casing=True,
                            fast=R[kk].get("fast", False), phase=1.0)
            ax.add_patch(FancyBboxPatch((cx - 1.05, yy - 2.35), 2.1, 4.7, boxstyle="round,pad=0,rounding_size=1.05", fc=WHITE, ec=INK, lw=2.0, zorder=12))
        elif k == "cap":
            ax.add_patch(FancyBboxPatch((cx - 1.57, yy - 0.62), 3.14, 1.24, boxstyle="round,pad=0,rounding_size=0.62", fc=WHITE, ec=INK, lw=1.0, zorder=12))
        else:
            M.icon(ax, cx, yy, z=12)
        txt(ax, x2 + 10.5, yy - 0.05, t, 9.6, "normal", "left", "center")


def key_transfers(ax, x0, y1, codes):
    txt(ax, x0, y1, "TRANSFERS", 11.0, "bold", "left", "top")
    for i, c in enumerate(codes):
        px, py = x0 + 3.3, y1 - 9.0 - i * 4.4
        pill(ax, px - 3.3, px + 3.3, py, c, z=12)
        txt(ax, px + 4.8, py - 0.05, NAMES[c], 8.8, "normal", "left", "center")


def next_version():
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        return int(sys.argv[1])
    v = 1
    while (OUT / f"ferry_network_v{v}.png").exists() or (OUT / f"ferry_network_v{v}.pdf").exists():
        v += 1
    return v


def text_shape(t, rot, anchor, renderer, inv):
    bb = t.get_window_extent(renderer)
    (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
    if rot:
        return srotate(box(x0, y0 + 0.35, x1, y1 - 0.35), rot, origin=anchor)
    return box(x0, y0 + 0.35, x1, y1 - 0.35)


def check(fig, ax):
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    shapes = [(t.get_text().replace("\n", " ")[:28], text_shape(t, rot, a, rend, inv)) for t, rot, a in TEXTS]
    bad = []
    for i, (a, sa) in enumerate(shapes):
        for b, sb in shapes[i + 1:]:
            if sa.intersection(sb).area > 0.05:
                bad.append(f"text/text: {a} | {b}")
            elif sa.distance(sb) < 1.0:
                bad.append(f"text close: {a} | {b} ({sa.distance(sb):.1f})")
        for key, ln in REG["line"]:
            if sa.intersection(ln).area > 0.05:
                bad.append(f"text/line: {a} | {key}")
        for n, d in REG["dot"]:
            if sa.intersection(d).area > 0.05:
                bad.append(f"text/dot: {a} | {n}")
        for k, pb in enumerate(REG["pill"]):
            if sa.intersection(pb).area > 0.05:
                bad.append(f"text/pill: {a} | pill {k} {[round(v) for v in pb.bounds]}")
    for k, pb in enumerate(REG["pill"]):
        for key, ln in REG["line"]:
            if pb.intersection(ln).area > 0.3:
                bad.append(f"pill/line: pill {k} {[round(v) for v in pb.bounds]} | {key}")
        for j, pc in enumerate(REG["pill"][k + 1:]):
            if pb.intersection(pc).area > 0.05:
                bad.append(f"pill/pill: {k} {[round(v) for v in pb.bounds]}")
    dots = REG["dot"]
    for i, (a, da) in enumerate(dots):
        for b, db in dots[i + 1:]:
            if da.intersects(db):
                bad.append(f"dot/dot: {a} | {b}")
    return bad


# ---------------------------------------------------------------------------------------------------------------
ROUTE_STOPS = {
    "charles": {"loop": True, "link": ["Langone Ferryport", "Lovejoy Wharf"],
                "banks": {"Boston bank, upstream": ["Lovejoy Wharf"] + BB, "Cambridge bank, inbound": CB + ["Navy Yard"]}},
    "mystic": {"loop": True, "link": ["Langone Ferryport", "Navy Yard"],
               "banks": {"West bank": ["Menino", "Navy Yard", "Little Mystic", "Medford St", "Alford St", "Assembly"],
                         "East bank": ["Encore", "Stadium", "Admirals Hill", "Pearl St"]}},
    "chelsea": {"loop": True, "link": ["Langone Ferryport", "Boston Bay"],
                "banks": {"North bank": ["Quigley", "Chelsea St", "Eastern Ave"], "South bank": ["Suffolk Downs", "Addison St", "Condor St", "Boston Bay"]}},
    "hw": {"stops": ["Langone Ferryport", "Battery Wharf", "Sargent's Wharf", "Long Wharf", "Central Wharf", "Rowes Wharf", "Dorchester Ave"]},
    "express": {"stops": ["Navy Yard", "Langone Ferryport", "Long Wharf"], "note": "At all times, nonstop between the three"},
    "eb": {"stops": ["Langone Ferryport", "White St", "Bennington St", "Piers Park", "Porzio", "Logan Dock"]},
    "hi": {"stops": ["Langone Ferryport", "Deer Island", "Spectacle Island", "Georges Island", "Long Island"]},
    "seaport": {"stops": ["Langone Ferryport", "Martins Park", "Fan Pier", "Seaport", "Pavilion"]},
    "ssi": {"stops": ["Langone Ferryport", "First St", "Castle Island", "M St", "Carson Beach", "Dorchester Shores", "Old Harbor", "UMass Boston",
                      "Fox Point", "Finigan"]},
    "qb": {"stops": ["Langone Ferryport", "Squantum Point"] + QB},
    "fore": {"stops": ["Langone Ferryport", "Bay Pointe", "King's Cove", "Wessagusset", "Hingham", "Nantasket", "Hull"]},
    "nse": {"stops": ["Langone Ferryport"] + NSE_STOPS},
    "sse": {"stops": ["Langone Ferryport", "Carson Beach", "UMass Boston", "Squantum Point", "Quincy", "Quincy Point", "Hingham", "Hull", "Minot (Scituate)",
                      "Mill Wharf", "Humarock", "Brant Rock / Green Harbor", "Duxbury", "Plymouth Rock", "Sandwich Boardwalk", "N. Barnstable / Sandy Neck",
                      "Sesuit", "Namskaket", "Thumpertown", "Wellfleet Pier", "Provincetown", "Race Point", "Marconi Beach", "Coast Guard Beach",
                      "Nauset Beach", "Chatham"] + [n for n, _ in SOUTH] + ["Woods Hole", "New Bedford", "South Dartmouth", "Newport", "Fall River"],
            "branches": {"Canal Pass (shortcut)": ["Sandwich Boardwalk", "Buzzards Bay"],
                         "Buzzards Bay leg": ["Woods Hole", "West Falmouth", "New Silver Beach", "Pocasset", "Buzzards Bay", "Onset", "Wareham", "Marion",
                                              "Mattapoisett", "West Island", "Fairhaven", "New Bedford"],
                         "Bass River loop (one way)": ["Yarmouth", "South Yarmouth", "Wilbur", "Bass River / Rte 28", "Wrinkle Point", "Yarmouth"],
                         "New Bedford to Oak Bluffs": ["New Bedford", "Cuttyhunk", "Oak Bluffs"]}},
    "isl": {"stops": ["Chatham", "Wauwinet", "Siasconset", "Nobadeer", "South Shore", "Cisco", "Smith Point", "Tuckernuck Is.", "Brant Point",
                      "Nantucket Downtown", "Coskata", "Oak Bluffs"],
            "branches": {"Martha's Vineyard ring (clockwise)": ["Oak Bluffs", "Edgartown", "Chappaquiddick", "Katama Beach", "MVY Connection", "Chilmark",
                                                                "Aquinnah", "Vineyard Haven", "Lagoon Pond", "Oak Bluffs"],
                         "Woods Hole link": ["Vineyard Haven", "Woods Hole"],
                         "Cuttyhunk link": ["New Bedford", "Cuttyhunk", "Aquinnah"],
                         "Noman's Land spur": ["Aquinnah", "Noman's Land"]}},
}


def write_routes(path):
    out = []
    for k, d in ROUTE_STOPS.items():
        names = []
        for part in ([d.get("stops", [])] + [d.get("link", [])] + list(d.get("banks", {}).values()) + list(d.get("branches", {}).values())):
            names += [n for n in part if n not in names]
        e = dict(key=k, name=R[k]["name"], family=dict(FAMILIES)[R[k]["fam"]], color=col(k), style="streak" if R[k].get("fast") else "dots")
        for f in ("stops", "link", "banks", "branches", "note", "loop"):
            if f in d:
                e[f] = d[f]
        e["major_ports"] = [n for n in names if S[n]["major"]]
        e["pills"] = {n: sorted(S[n]["pills"], key=ORDER.index) for n in names if S[n]["pills"]}
        e["labels"] = {n: S[n]["text"].replace("\n", " ") for n in names if S[n]["text"] != n}
        if d.get("loop"):
            e["services"] = ["clockwise loop (outer track)", "counterclockwise loop (inner track)", "zigzag, bank to bank at every dock"]
        out.append(e)
    doc = {"source": "boston-map/src/make_ferry_network.py",
           "families": [{"key": k, "name": n, "routes": [r for r, d in R.items() if d["fam"] == k]} for k, n in FAMILIES],
           "hub": "Langone Ferryport", "hub_walkway": "North Station", "major_ports": ORDER_PORTS, "event_docks": EVENT,
           "service": "Boats run 24/7 and are automated. Every major route starts and ends at Langone Ferryport (spurs excepted). Fast "
                      "Ferry trips on the North Shore Fast Ferry, South Shore Fast Ferry and Islands boats stop only at major ports. The Fast Ferry (FF) shuttle "
                      "runs Navy Yard, Langone Ferryport, Long Wharf, nonstop between them, at all times.",
           "routes": out}
    Path(path).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print("wrote", path)


# ---------------------------------------------------------------------------------------------------------------
def main():
    v = next_version()
    png, pdf = OUT / f"ferry_network_v{v}.png", OUT / f"ferry_network_v{v}.pdf"
    if "--draft" in sys.argv:  # trial renders go to a scratch folder, never into output/
        d = Path(sys.argv[sys.argv.index("--draft") + 1])
        png, pdf = d / "ferry_draft.png", d / "ferry_draft.pdf"
    for f in (png, pdf):
        if f.exists() and "--draft" not in sys.argv:
            raise SystemExit(f"refusing to overwrite {f}")
    if "--routes" in sys.argv:
        write_routes(sys.argv[sys.argv.index("--routes") + 1])
    plt.rcParams["pdf.fonttype"] = 42
    x0, x1 = -10.6 * P, 55.0 * P
    y1, y0 = 9.8 * P, -71.4 * P
    fig = plt.figure(figsize=((x1 - x0) * K, (y1 - y0) * K))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.patch.set_facecolor(PAPER)

    # the Cape Cod Canal, under Canal Pass
    cx0, cx1 = G(4.55, 48.5)[0], G(9.45, 48.5)[0]
    cy = G(0, 48.5)[1]
    ax.add_patch(FancyBboxPatch((cx0, cy - 2.2), cx1 - cx0, 4.4, boxstyle="round,pad=0,rounding_size=2.2", fc=WATER, ec=COAST, lw=1.0, zorder=1.6))

    for L in LOOPS:
        draw_loop(ax, L)
    draw_stops(ax)    # docks first: the dotted tracks leave out any dot that would sit under one
    draw_tracks(ax)
    draw_labels(ax)

    # Bass River loop runs one way; Martha's Vineyard ring runs clockwise
    track_arrow(ax, BASS, 1.2, (YX, 50.3), col("sse"))
    track_arrow(ax, BASS, 1.2, (YX + 0.75, 52.6), col("sse"))
    track_arrow(ax, ["Vineyard Haven", "Lagoon Pond"], RR, (13.25, 60), col("isl"))
    track_arrow(ax, MV_RING, RR, (20.75, 66), col("isl"))

    def cap(x, r, s, key, ha="left", fs=10.0, va="center", wt="bold"):
        txt(ax, *G(x, r), s, fs, wt, ha, va, color=tcol(key))

    def sub(x, r, s, ha="center", fs=7.8):
        txt(ax, *G(x, r), s, fs, "normal", ha, "center", color="#4a4f57")

    cap(1.5, -3.2, "CHARLES RIVER", "charles", "center", 11.0)
    sub(-0.3, -2.1, "Boston bank", "right", 8.4)
    sub(3.3, -2.1, "Cambridge bank", "left", 8.4)
    cap(14.0, 14.85, "MYSTIC RIVER", "mystic", "center")
    sub(14.0, 15.5, "Charlestown and Somerville bank on top, Everett and Chelsea bank below")
    cap(34.2, 14.85, "CHELSEA CREEK", "chelsea", "center")
    sub(34.2, 15.5, "Chelsea bank on top, East Boston bank below")
    cap(1.15, 18.3, "FAST FERRY", "express", "center", 8.6)
    sub(1.15, 18.85, "at all times", "center", 7.6)
    sub(-0.6, 19.05, "Walkway to North Station", "right", 7.8)
    cap(NSX, -4.7, "NORTH SHORE FAST FERRY", "nse", "center")
    sub(NSX, -3.85, "to Salisbury via Gloucester, Newburyport", "center", 8.4)
    cap(-0.6, 24.95, "HARBOR WEST", "hw", "right", 9.4)
    cap(18.0, 25.4, "SEAPORT", "seaport", "center")
    cap(38.6, 25.0, "EAST BOSTON", "eb", "center")
    cap(HX - 0.6, 26.4, "HARBOR ISLANDS", "hi", "right", 9.4)
    cap(LX - 0.6, 25.35, "SOUTH SHORE", "ssi", "right", 9.4)
    cap(16.5, 33.3, "QUINCY BAY", "qb", "left", 9.4)
    cap(LX - 0.4, 41.45, "FORE RIVER", "fore", "right", 9.4)
    cap(FX + 0.5, 26.6, "SOUTH SHORE\nFAST FERRY", "sse", "left", 9.4)
    cap(20.8, 46.4, "Cape Cod Bay run", "sse", "center", 9.4, wt="normal")
    cap(7.0, 46.0, "Canal Pass", "sse", "center", 9.4, wt="normal")
    sub(7.0, 46.6, "shortcut through the canal", "center", 8.0)
    cap(YX, 49.6, "Bass River loop", "sse", "center", 8.8, wt="normal")
    cap(-2.5, 47.0, "Buzzards Bay leg", "sse", "center", 8.8, wt="normal")
    cap(12.3, 57.3, "New Bedford to Oak Bluffs via Cuttyhunk", "sse", "center", 8.8, wt="normal")
    cap(16.5, 64.2, "MARTHA'S VINEYARD", "isl", "center", 8.8)
    sub(16.5, 64.9, "Ring runs clockwise", "center", 8.0)
    cap(NX - 3.5, 65.3, "NANTUCKET", "isl", "center", 8.8)

    # Header, as on the line posters
    hy = y1 - 11
    # Three-layer T and NERTA pill in the Inner Harbor teal (Max, November 7). The red "NOT A REAL MBTA MAP" tag is retired:
    # Max says the NERTA style now makes that plain.
    LP.roundel(ax, x0 + 10, hy, 6.4, F_TEAL)
    draw_nerta(ax, x0 + 10, hy - (6.4 + 3.2 / 5.4 / 2) - 0.8, 2 * (6.4 + 3.2 / 5.4 / 2), "B", colors=(F_TEAL,))
    ax.add_patch(FancyBboxPatch((x0 + 20, hy - 6), 28, 12, boxstyle="round,pad=0,rounding_size=6", fc=F_TEAL, ec="none", zorder=12))
    ax.text(x0 + 34, hy - 0.4, "F", fontsize=38, fontweight="bold", color=WHITE, ha="center", va="center", zorder=13)
    ax.text(x0 + 52, hy, "Ferry" + chr(10) + "Network", fontsize=27, fontweight="bold", color=INK, ha="left", va="center", linespacing=0.9, zorder=13)
    ax.text(x1 - 5, hy + 2, "Map: Maxwell Howe", fontsize=9.6, color=INK, ha="right", va="center", zorder=13)
    ax.text(x1 - 5, hy - 2, "#30DayMapChallenge Day 8 \u2022 Utopia", fontsize=9.6, color=INK, ha="right", va="center", zorder=13)

    # How the river boats run, express boats and the passenger notice
    px0, py1 = G(10.2, -1.6)
    px1, py0 = G(46.0, 13.8)
    panel(ax, px0, py0, px1, py1)
    river_explainer(ax, px0 + 3.5, py1 - 3.2)
    ax.plot([px0 + 118, px0 + 118], [py0 + 4, py1 - 4], color=PANEL_EC, lw=1.0, zorder=1.1)
    express_explainer(ax, px0 + 122, py1 - 3.2, px1 - px0 - 125.5)

    # Key: routes on the left, boats and docks in the middle, transfers bottom right
    kx0, ky1 = G(-10.3, 25.4)
    kx1, ky0 = G(4.3, 46.2)
    panel(ax, kx0, ky0, kx1, ky1)
    key_routes(ax, kx0 + 3.5, ky1 - 3.2)
    sx0, sy1 = G(21.5, 30.4)
    sx1, sy0 = G(53.0, 40.6)
    panel(ax, sx0, sy0, sx1, sy1)
    key_symbols(ax, sx0 + 3.5, sy1 - 3.2)
    tx0, ty1 = G(44.2, 43.0)
    tx1, ty0 = G(53.0, 53.8)
    panel(ax, tx0, ty0, tx1, ty1)
    used = sorted({c for s in S.values() for c in s["pills"]}, key=ORDER.index)
    key_transfers(ax, tx0 + 3.5, ty1 - 3.2, used)
    nx0, ny1 = G(-10.2, 60.4)
    nx1, ny0 = G(1.2, 70.95)
    notice(ax, nx0, ny0, nx1, ny1)
    ax.text(x1 - 5, y0 + 4, "Not to scale. Not affiliated with the MBTA.", fontsize=7.6, color=INK, ha="right", va="bottom", zorder=13)

    bad = check(fig, ax)
    for b in bad:
        print("  overlap:", b)
    print(f"{len(bad)} overlaps")
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=300 if "--draft" not in sys.argv else 200, facecolor=PAPER)
    fig.savefig(pdf, facecolor=PAPER)
    print("written", png, pdf)


if __name__ == "__main__":
    main()
