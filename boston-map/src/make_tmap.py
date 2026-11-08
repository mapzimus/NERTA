"""Day 8 Boston metro map: the T wall poster, with the extensions and The BIGGER Dig.

python days/08-utopia/src/make_tmap.py
Stop order for today's lines comes from the MBTA V3 data (data/mbta_stops.gpkg). Positions are schematic, set by hand
on a 45-degree grid. Fan map, no official logo. Silver Line and buses left off.
"""
from pathlib import Path
import os
import geopandas as gpd
import csv
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch, Polygon
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D
from scipy.interpolate import RBFInterpolator, splev, splprep
from scipy.ndimage import distance_transform_edt
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
import shapely
from shapely.geometry import LineString, Point, Polygon as ShapelyPolygon, box
from shapely.ops import substring, unary_union
from nerta_mark import draw_nerta, draw_t
from station_kit import INK, WHITE, bullet, label, place, rounded, smooth_closed, smooth_open, stop, stroke, transfer

DAY = Path(__file__).resolve().parents[1]
REPO = DAY.parent
RED, ORANGE, BLUE, GREEN, YELLOW, PURPLE = "#da291c", "#ed8b00", "#003da5", "#00843d", "#f5c400", "#a98aa8"
CR_TEXT_COLOR = "#80276c"
WATERMARK = "#a6d6dc"  # a shade darker than the water
WEB = os.environ.get("NERTA_WEB") == "1"  # nerta.fun version (Max): no hashtag, Day 8, disclaimer or sources; name under NERTA, @mapzimus in the water
BUILT = True  # Max, November 7: drawn as built and real. lines() and CR_STOPS keep each piece's status (solid today, stripe real proposal,
              # dash invented) for line_audit.md; the drawing ignores it. Set False to show status again.
CYAN, INDIGO = "#00a9c9", "#3f3fb5"
PAPER, WATER, COAST = "#fcfcfa", "#b6e2e7", "#7dbcc2"  # teal-leaning water; Day 8 draft was #c9e3ee / #7fb2c6
LW, CR = 9.0, 3.4
HSR = "#ffd23f"
SILVER = "#7c878e"
XLIM, YLIM = (-46, 229.4), (-20, 215.4)  # Day 8 was (-46, 222), (-20, 208)

# Spots shared between lines, or that fix the shape of a line.
CR_STOPS = [("Beverly", (212, 211.6), None, "solid"), ("Swampscott", (204, 194), "l", "solid"), ("Marblehead", (214.5, 198.5), None, "dash"), 
            ("South Salem", (208.5, 198.5), None, "stripe"), ("Clifton", (211.5, 198.5), None, "dash"), ("Salem", (212, 203.8), None, "solid"), ("Peabody", (194, 198.5), "t", "dash"), ("Danversport", (187.5, 198.5), None, "dash"), ("Danvers", (181, 198.5), "t", "dash"), ("Middleton", (169, 205.5), "r", "dash"),
            ("Boston Landing", (15, 122), "t", "solid"), ("David Ortiz", (61.7, 86.3), "r", "solid"),
            
            ("Walpole", (34, -13), "l", "solid"), ("Foxboro", (34, -16), None, "solid"), ("Stoughton", (50, -7), None, "solid"),
            ("Newtonville", (6, 122), "b", "solid"), ("West Newton", (-3.5, 122), "t", "solid"), ("Wellesley", (-30, 122), "b", "solid"), ("Concord", (-15, 137), "l", "solid"), ("South\nActon", (-21, 143), "r", "solid"), ("Ayer", (-38, 160), "r", "solid"), ("Winchester", (53, 184), "r", "solid"), ("Anderson/\u200aWoburn", (53, 189), "l", "solid"), ("Wilmington", (53, 194), "l", "solid"), ("Endicott", (43.5, -3.5), "l", "solid"), ("Islington", (40.5, -6.5), "l", "solid"), ("Norwood", (37.5, -9.5), "l", "solid"), ("Brockton", (121.6, -2), "r", "solid"), ("Bridgewater", (121.6, -8), "r", "solid"), ("Abington", (127.6, 2), "r", "solid"), ("Hanson", (133, -3.4), "r", "solid"), ("Kingston", (138.4, -8.8), "r", "solid"), ("East Weymouth", (130, 8), None, "solid"), ("Hingham", (142, 4), "r", "solid"), ("Cohasset", (146.5, -0.5), "r", "solid"), ("North\nScituate", (149.8, -3.8), "l", "solid"), ("Greenbush", (153, -7), None, "solid"), ("Hudson", (-29, 140), "b", "dash"), ("Marlborough", (-40, 140), "b", "dash"), ("Mansfield", (46, -16), None, "solid"), ("North Easton", (57, -7), "t", "dash"), ("Easton Village", (64, -7), "b", "dash"), ("Raynham Place", (71, -7), "t", "dash"), ("Taunton", (78, -7), "b", "dash")]

A = {"Moakley Park": (124.9, 58.9), "Day Sq": (135, 133.6), "Arlington Ctr": (30, 160), "East Arlington": (38, 152), "Alewife": (44, 146), "Weymouth": (118, -7), "Bellingham Sq": (135, 137), "Wyoma Sq": (188, 192), "East Saugus": (160.5, 174), "Brighton Center": (20, 111), "Allston": (38, 111), "West Medford": (53, 175), "Eliot": (8, 38), "Porter": (58, 132), "Harvard": (66, 124), "Kendall/MIT": (80, 110),
     "Charles/MGH": (90, 100), "Park Street": (96, 94), "Downtown Crossing": (103, 87), "South Station": (114, 76),
     "JFK/UMass": (118, 52), "Ashmont": (94, 26), "Braintree": (118, 8), "Arlington Heights": (20, 170),
     "Inner Belt": (94, 142), "Oak Grove": (110, 182), "Malden Center": (110, 174), "Saugus Center": (150, 186), "Lynn Common": (195, 188), "Reading": (110, 202), "Assembly": (110, 157), "Sullivan Sq": (110, 150), "Community College": (110, 136), "North Station": (110, 120),
     "Haymarket": (110, 112), "State": (110, 100), "Back Bay": (82, 66), "Ruggles": (72, 56), "Broadway": (118, 64), "Andrew": (118, 58), "Forest Hills": (43, 27), "VFW Parkway": (12, -4),
     "Bowdoin": (96, 100), "Gov't Center": (102, 100), "Airport": (135, 125), "Encore": (121, 150), "Mass Ave": (75, 105), "Mattapan": (66, 14), "Dedham": (-2, -16), "Lexington Route 128": (-26, 170), "Waltham": (-30, 146), "Watertown": (-18, 117), "Wonderland": (176, 166), "Lynn Harbor": (188, 178), "Central Sq": (195, 185),
     "Medford/Tufts": (63, 165), "Lechmere": (90, 138), "Union Sq": (80, 138), "Linden Sq": (121, 174), "Cliftondale": (131, 181), "Boston Medical": (94.5, 56), "Boylston": (90, 88), "Arlington": (81, 84),
     "Copley": (75, 84), "Hynes": (59, 84), "Kenmore": (54, 84), "Fenway": (46, 76), "Longwood Medical Area": (59, 56), "Prudential": (69, 75), "Symphony": (69, 69), "Blandford St": (39, 89), "St. Mary's St": (39, 84),
     "Riverside": (-8, 22), "Harvard Ave": (20, 108), "Boston College": (-22, 66), "Norumbega": (-40, 92), "Newton City Hall": (-25, 63), "Weston": (-31, 57), "Wellesley Hills": (-14, 16), "Cleveland Circle": (-14, 48),
     "Newton Highlands": (12, 42), "Heath St": (40, 37), "Hyde Sq": (40, 32), "Hyde Park": (43, 14), "Nubian": (84, 56), "Tufts Medical Ctr": (92, 76), "Dover": (92, 71), "Northampton": (92, 67.6), "Four Corners": (92, 48), "Grove Hall": (84, 50), "Seaver St": (78, 44), "Wellington Hill": (71, 37), "Melnea Cass": (89, 56), "Inman Sq": (74.5, 124), "Auburndale": (-28, 60), "BU Bridge": (66, 96), "West Station": (59, 89), "Barrys Corner": (52, 110), "Lansdowne": (59, 89),
     "Terminals": (148, 104), "Newmarket": (100, 56), "Broadway": (118, 64), "Readville": (46, 2), "Winthrop Center": (164, 124), "Orient Heights": (149, 139), "Maverick": (129, 119), "City Point": (152, 70), "Convention Center": (130, 64), "L Street": (145, 64), "West Broadway": (124, 64), "Boston Central": (118, 100), "Aquarium": (118, 108), "Langone Ferryport": (118, 114), "City Square": (122, 132), "Navy Yard": (124, 135), "Thompson Sq": (124, 141), "Stadium": (124, 150), "Encore": (116, 157), "Everett Sq": (130, 150), "Chelsea": (135, 150), "Fort Point": (125, 76), "Uphams Corner": (98, 54), "Bellingham Sq": (135, 141), "Talbot Ave": (79, 35), "Morton St": (71, 27), "Blue Hill Ave": (66, 22), "Fairmount": (50.5, 6.5),  "Mass. Ave": (79.5, 63.5), "Northeastern": (69, 65), "Seaport": (140, 76), "Courthouse": (133, 76)}


def lines():
    """Each entry: color, style, path, stops. Styles: solid today, stripe real proposal, dash imagined."""
    x = []
    x += [(RED, "dash", [(118, 8), (118, -7)], ["Braintree", "Weymouth"])]  # one source only (track map); dashed by Max, November 7
    x += [(RED, "stripe", [(20, 170), (44, 146)], ["Arlington Heights", "Arlington Ctr", "East Arlington", "Alewife"]),
          (RED, "stripe", [(20, 170), (-26, 170)], ["Arlington Heights", "Lexington Ctr", "Lexington Route 128"]),
          (RED, "stripe", [(44, 146), (-30, 146)], ["Alewife", "Belmont Ctr", "Waverley Sq", "Waltham"]),
          (RED, "solid", [(44, 146), (118, 72), (118, 52)], ["Alewife", "North Cambridge", "Davis", "Porter", "Harvard", "Central", "Kendall/MIT", "Charles/MGH", "Park Street",
                                                             "Downtown Crossing", "South Station", "Broadway", "Andrew", "JFK/UMass"]),
          (RED, "solid", [(118, 52), (94, 28), (94, 26)], ["JFK/UMass", "Savin Hill", "Fields Corner", "Shawmut", "Ashmont"]),
          (RED, "solid", [(118, 52), (118, 8)], ["JFK/UMass", "North Quincy", "Wollaston", "Quincy Center", "Quincy Adams", "Braintree"]),
          (RED, "solid", [(94, 26), (94, 18), (90, 14), (66, 14)], ["Ashmont", "Cedar Grove", "Butler", "Milton", "Central Ave", "Valley Rd", "Capen St", "Mattapan"])]
    x += [(ORANGE, "solid", [(110, 182), (110, 94), (43, 27)],
           ["Oak Grove", "Malden Center", "Wellington", "Assembly", "Sullivan Sq", "Community College", "North Station", "Haymarket", "State",
            "Downtown Crossing", "Chinatown", "Tufts Medical Ctr", "Back Bay", "Mass. Ave", "Ruggles", "Roxbury Crossing", "Jackson Sq",
            "Stony Brook", "Green St", "Forest Hills"]),
          (ORANGE, "dash", [(92, 76), (92, 64), (84, 56), (84, 50), (66, 32), (66, 14)],
           ["Tufts Medical Ctr", "Dover", "Northampton", "Nubian", "Grove Hall", "Seaver St", "Wellington Hill", "Blue Hill Ave", "Mattapan"]),
          (ORANGE, "stripe", [(110, 202), (110, 182)], ["Reading", "Wakefield", "Greenwood", "Melrose Highlands", "Melrose/Cedar Park", "Wyoming Hill", "Oak Grove"]),
          (ORANGE, "dash", [(110, 174), (124, 174), (136, 186), (162, 186), (176, 172), (176, 166)], ["Malden Center", "Linden Sq", "Cliftondale", "Saugus Center", "Wonderland"]),
          (ORANGE, "stripe", [(43, 27), (43, 6), (46, 2)], ["Forest Hills", "Hyde Park", "Readville"]),
          (ORANGE, "stripe", [(43, 27), (12, -4)], ["Forest Hills", "Roslindale Village", "Wu Sq", "Bellevue", "Highland", "West Roxbury", "VFW Parkway"])]
    x += [(INDIGO, "stripe", [(114, 76), (114, 70), (110, 66), (46, 2)], ["South Station", "Newmarket", "Uphams Corner", "Four Corners", "Talbot Ave", "Morton St", "Blue Hill Ave", "Fairmount", "Readville"])]
    x += [(CYAN, "dash", [(140, 76), (122, 76), (118, 80), (118, 128), (124, 134), (124, 157), (110, 157)],
           ["Seaport", "Courthouse", "Fort Point", "Boston Central", "Aquarium", "Langone Ferryport", "North Station", "City Square", "Navy Yard", "Thompson Sq", "Stadium", "Encore", "Assembly"])]
    x += [(CYAN, "dash", [(140, 76), (149, 76), (152, 73), (152, 67), (149, 64), (122, 64), (118, 64)],
           ["Seaport", "Vertex Tower", "City Point", "L Street", "Convention Center", "West Broadway", "Broadway"])]
    x += [(BLUE, "solid", [(102, 100), (114, 100), (118, 108), (176, 166)], ["Gov't Center", "State", "Aquarium", "Maverick", "Airport", "Wood Island",
                                                                "Orient Heights", "Suffolk Downs", "Beachmont", "Revere Beach", "Wonderland"]),
          (BLUE, "stripe", [(90, 100), (102, 100)], ["Charles/MGH", "Gov't Center"]),
          (BLUE, "dash", [(90, 100), (84, 100), (79, 105), (64, 105), (59, 100), (59, 89)], ["Charles/MGH", "Mass Ave", "West Station"]),
          (BLUE, "dash", [(149, 139), (164, 124)], ["Orient Heights", "Winthrop Center"]),
          (BLUE, "stripe", [(176, 166), (195, 185)], ["Wonderland", "Lynn Harbor", "Central Sq"]),
          (BLUE, "dash", [(195, 185), (188, 192)], ["Central Sq", "Wyoma Sq"])]
    x += [(GREEN, "solid", [(90, 138), (106, 122), (106, 104), (102, 100), (86, 84), (54, 84)],
           ["Lechmere", "Science Park", "North Station", "Haymarket", "Gov't Center", "Park Street", "Boylston", "Arlington", "Copley", "Hynes", "Kenmore"]),
          (GREEN, "solid", [(63, 165), (90, 138)], ["Medford/Tufts", "Ball Sq", "Magoun Sq", "Gilman Sq", "East Somerville", "Lechmere"]),
          (GREEN, "stripe", [(53, 175), (63, 165)], ["West Medford", "Medford Hillside", "Medford/Tufts"]),
          (GREEN, "stripe", [(59, 89), (59, 84)], ["West Station", "Hynes"]),
          (GREEN, "stripe", [(59, 89), (56, 89), (50, 95), (50, 111), (-12, 111), (-18, 117)], ["West Station", "Allston", "Brighton Center", "Oak Sq", "Newton Corner", "Watertown"]),
          (GREEN, "solid", [(80, 138), (90, 138)], ["Union Sq", "Lechmere"]),
          (GREEN, "dash", [(66, 124), (77, 124), (80, 127), (80, 138)], ["Harvard", "Inman Sq", "Union Sq"]),
          (GREEN, "solid", [(54, 84), (44, 84), (20, 108), (-22, 66)],
           ["Kenmore", "Blandford St", "BU East", "BU Central", "Amory St", "Babcock St", "Packard's Corner", "Harvard Ave", "Griggs St", "Allston St",
            "Warren St", "Washington St", "Sutherland Rd", "Chiswick Rd", "Chestnut Hill Ave", "South St", "Boston College"]),
          (GREEN, "solid", [(50, 84), (36, 84), (29, 91), (-14, 48)],
           ["St. Mary's St", "Hawes St", "Kent St", "St. Paul St", "Coolidge Corner", "Summit Ave", "Brandon Hall", "Fairbanks St",
            "Washington Sq", "Tappan St", "Dean Rd", "Englewood Ave", "Cleveland Circle"]),
          (GREEN, "solid", [(54, 84), (-8, 22)], ["Kenmore", "Fenway", "Longwood", "Brookline Village", "Brookline Hills", "Beaconsfield", "Reservoir",
                                                  "Chestnut Hill", "Newton Centre", "Newton Highlands", "Eliot", "Waban", "Woodland", "Riverside"]),
          (GREEN, "solid", [(69, 84), (69, 66), (40, 37)], ["Prudential", "Symphony", "Northeastern", "Museum of Fine Arts", "Longwood Medical Area", "Brigham Circle",
                                                            "Fenwood Rd", "Mission Park", "Riverway", "Back of the Hill", "Heath St"]),
          (GREEN, "stripe", [(40, 37), (40, 32)], ["Heath St", "Hyde Sq"]),
          (GREEN, "stripe", [(40, 32), (40, 30), (43, 27)], ["Hyde Sq", "Forest Hills"]),
          (GREEN, "stripe", [(8, 38), (8, 2), (12, -4)], ["Eliot", "Newton Upper Falls", "Needham Crossing", "Needham Heights", "Needham Junction", "Hersey", "VFW Parkway"]),
          (GREEN, "dash", [(-22, 66), (-31, 57)], ["Boston College", "Newton City Hall", "Auburndale", "Weston"]),  # along Comm Ave, roughly the old streetcar to Norumbega
          (GREEN, "dash", [(-8, 22), (-14, 16)], ["Riverside", "Wellesley Hills"])]
    # Yellow, the Urban Ring. Grand Junction section striped, the rest dashed.
    x += [(YELLOW, "dash", [(148, 104), (148, 105), (135, 118), (135, 137)], ["Terminals", "Airport", "Day Sq", "Bellingham Sq"]),
          (YELLOW, "dash", [(135, 137), (135, 150), (102, 150), (90, 138)],
           ["Bellingham Sq", "Chelsea", "Everett Sq", "Stadium", "Sullivan Sq", "Inner Belt", "Lechmere"]),
          (YELLOW, "dash", [(140, 76), (148, 84), (148, 104)], ["Seaport", "Terminals"]),
          (YELLOW, "stripe", [(90, 138), (90, 120), (59, 89)], ["Lechmere", "Binney", "Kendall/MIT", "Mass Ave", "BU Bridge", "West Station"]),
          (YELLOW, "dash", [(59, 89), (54, 84), (50, 80), (50, 56), (114, 56), (118, 52)],
           ["West Station", "Kenmore", "Fenway+", "Longwood Medical Area", "Ruggles", "Nubian", "Melnea Cass", "Boston Medical", "Newmarket", "JFK/UMass"]),
          (YELLOW, "dash", [(118, 52), (140, 74), (140, 76)], ["JFK/UMass", "Moakley Park", "Convention Center", "Seaport"])]
    return x


EXTRA = {"Sullivan Sq+": (102, 150), "Fenway+": (50, 76), "South Station+": (114, 78.5)}

# Commuter rail, thin purple. All of it now runs through the tunnel, so no line ends downtown.
CR_PATHS = [
    [(114, 120), (114, 149)],                                      # trunk to the Sullivan superstation
    [(-44, 166), (-10, 132), (88, 132), (100, 120), (114, 120)],               # Fitchburg
    [(53, 213.2), (53, 175), (88, 175), (114, 149)],               # Lowell, via the Wildcat
    [(114, 139), (121, 146), (139, 146), (178, 185), (195, 185), (212, 202), (212, 213.2)],  # Newburyport, Rockport
    [(114, 76), (114, 72), (108, 66), (82, 66), (26, 122), (-44, 122)],  # Worcester
    [(82, 66), (76, 66), (46, 36), (46, -19.6)],                     # Providence
    [(46, -1), (34, -13), (29, -18)],                              # Franklin, leaves at Readville
    [(34, -13), (34, -16)],                                        # Foxboro, leaves Franklin at Walpole
    [(114, 72), (120, 72), (121.6, 70.4), (121.6, -18)],                 # Fall River, New Bedford
    [(121.6, 8), (146, -16.4)],                                    # Kingston, Plymouth, Cape Cod
    [(121.6, 14), (127.6, 8), (138, 8), (153, -7)],                             # Greenbush, ends at Greenbush in Scituate
    [(46, -3), (50, -7)],                                          # Stoughton
    [(114, 149), (114, 160), (121, 160), (121, 167), (114, 167), (114, 213.2)],  # Haverhill, beside Orange, jogged past the Cyan pill
]
CR_TEXT = [("LOWELL LINE", (51, 204.6), "right"), ("HAVERHILL LINE", (116.2, 210.2), "left"), ("HIGH-SPEED RAIL TO CONCORD NH", (51, 201.9), "right"), ("VIA LOWELL, NASHUA, MANCHESTER", (51, 199.2), "right"), ("FITCHBURG LINE TO GREENFIELD, NORTH ADAMS", (-7, 135.8), "left"), ("HIGH-SPEED RAIL TO MONTREAL VIA BURLINGTON VT", (-7, 133.2), "left"),
           ("FRAMINGHAM / WORCESTER LINE", (-44, 128.2), "left"), ("HIGH-SPEED RAIL TO ALBANY", (-44, 125.7), "left"), ("VIA WORCESTER, SPRINGFIELD", (-44, 123.2), "left"), ("NEWBURYPORT / ROCKPORT LINE", (209.6, 211.6), "right"), ("HIGH-SPEED RAIL TO BANGOR", (209.6, 209.1), "right"), ("VIA PORTSMOUTH, PORTLAND, AUGUSTA", (209.6, 206.6), "right"), ("PEABODY LINE TO LAWRENCE", (164, 204.5), "right"), ("PROVIDENCE LINE", (48, -13.2), "left"), ("FRANKLIN LINE", (27.6, -18), "right"), ("HIGH-SPEED RAIL TO NYC", (48, -15.9), "left"), ("VIA PROVIDENCE, NEW HAVEN", (48, -18.6), "left"),
           ("GREENBUSH LINE", (126.8, 9.4), "left"), ("KINGSTON LINE", (140.4, -12.8), "right"), ("TO PLYMOUTH", (142.8, -15.4), "right"), ("FALL RIVER / NEW BEDFORD LINE TO CAPE COD", (120, -18), "right")]

BIG_CAPSULES = [(106, 120), (110, 100), (114.2, 77.2)]  # Tier 1 and Tier 2 capsules: North, Boston Central, South
CAPSULES = [((110, 202), (114, 202)), ((110, 174), (114, 174)), ((118, 8), (121.6, 8)), ((43, 14), (46, 14)), ((118, 52), (121.6, 52)), ((118, 25.6), (121.6, 25.6)), ((20, 111), (20, 107.4)), ((106, 112), (110, 112)), ((106, 120), (118, 120)), ((110, 100), (118, 100)), ((46, 76), (50, 76)), ((114.2, 77.2), (116.4, 78.8)), ((135, 150), (135, 146))]
RINGS = [r for r in ["Langone Ferryport", "Suffolk Downs", "Gov't Center", "Longwood Medical Area", "Braintree", "Central Sq", "VFW Parkway", "Wonderland", "Stadium", "Park Street", "Downtown Crossing", "Kendall/MIT", "Harvard", "Lechmere", "Assembly", "Back Bay", "Ruggles", "Forest Hills", "JFK/UMass",
         "Ashmont", "Airport", "Kenmore", "Seaport", "Porter", "Charles/MGH", "Newmarket", "BU Bridge", "Terminals", "Alewife", "Mattapan", "Blue Hill Ave", "Convention Center", "Readville", "Orient Heights", "Aquarium", "Broadway", "Sullivan Sq", "Mass Ave", "Nubian", "Tufts Medical Ctr"] if r != "Airport"]
ENDS = {"Lexington Route 128": RED, "Waltham": RED, "Winthrop Center": BLUE, "Weymouth": RED, "Mattapan": RED, "Readville": INDIGO, "VFW Parkway": ORANGE, "Wyoma Sq": BLUE, "West Medford": GREEN, "Weston": GREEN, "Wellesley Hills": GREEN,
        "Cleveland Circle": GREEN, "Reading": ORANGE, "Watertown": GREEN}
NEW_ON_OLD = set()
HIDE = {"Langone Ferryport", "Airport", "Back Bay", "Ruggles", "West Station", "Boston Central", "Nubian", "Melnea Cass", "Lynn Common", "Gov't Center", "State", "North Station", "South Station", "Haymarket", "Longwood Medical Area"}
TEXT = {"Park Street": "Park\nStreet", "Kendall/MIT": "Kendall", "Newton City Hall": "Newton\nCity Hall", "Four Corners": "Four\nCorners", "Melnea Cass": "Melnea\nCass", "Mass Ave": "MIT", "Convention Center": "Convention\nCenter", "Boston Medical": "Boston\nMedical", "Community College": "Community\nCollege", "Science Park": "Science\nPark", "Museum of Fine Arts": "MFA", "Needham Junction": "Needham Jct",
        "Tufts Medical Ctr": "Tufts Medical Ctr", "Downtown Crossing": "Downtown\nCrossing"}
SIDE = {}
for names, s in ((["Porter"], "bl"), (["Davis", "Harvard", "Kendall/MIT"], "tr"), (["Central"], "r"), (["Alewife"], "tr"), (["Arlington Ctr", "East Arlington", "North Cambridge"], "tr"), (["Arlington Heights"], "tr"),
                 (["Broadway", "Andrew", "North Quincy", "Wollaston", "Quincy Center", "Quincy Adams"], "r"), (["Braintree"], "l"),
                 (["Savin Hill", "Fields Corner", "Shawmut"], "bl"), (["Ashmont"], "l"), (["Cedar Grove", "Butler"], "r"), (["Milton", "Central Ave", "Valley Rd", "Capen St"], "up"), (["Mattapan"], "b"),
                 (["Oak Grove", "Malden Center", "Community College"], "l"), (["Wellington", "Assembly"], "r"), (["Chinatown", "Tufts Medical Ctr", "Mass. Ave"], "r"), (["Back Bay"], "up"), (["Bowdoin"], "up"), (["Nubian"], "br"), (["Newmarket"], "br"), (["Melnea Cass"], "b"), (["Boston Medical"], "t"),
                 (["Ruggles"], "l"), (["Roxbury Crossing", "Jackson Sq", "Stony Brook", "Green St", "Forest Hills", "Roslindale Village", "Bellevue", "Highland", "West Roxbury", "VFW Parkway"], "br"), (["Dedham"], "r"), (["Lexington Ctr", "Lexington Route 128", "Belmont Ctr", "Waverley Sq", "Waltham"], "b"), (["Seaver St", "Terminals"], "x2"), (["South Bay"], "l"), (["Uphams Corner", "Four Corners"], "br"), (["Talbot Ave", "Morton St", "Blue Hill Ave", "Fairmount"], "along"), (["Readville"], "r"), (["City Point"], "br"), (["West Broadway"], "t"), (["Convention Center"], "br"), (["Winthrop Center"], "r"), (["Eagle Hill"], "tl"), (["Linden Sq", "Cliftondale", "Saugus Center"], "t"), (["East Saugus"], "tl"),
                 (["Aquarium", "Maverick", "Wood Island", "Orient Heights", "Suffolk Downs", "Beachmont", "Revere Beach", "Wonderland", "Central Sq"], "br"),
                 (["Medford/Tufts", "Ball Sq", "Magoun Sq", "Gilman Sq", "East Somerville"], "l"), (["West Medford"], "tr"), (["Lechmere"], "bl"), (["Science Park"], "r"),
                 (["Griggs St", "Allston St", "Warren St", "Washington St", "Sutherland Rd", "Chiswick Rd", "Chestnut Hill Ave", "South St"], "l"), (["Boston College"], "bl"), (["Newton City Hall"], "r"), (["Norumbega"], "r"),
                 (["Kent St", "St. Paul St", "Coolidge Corner", "Summit Ave", "Brandon Hall", "Fairbanks St", "Washington Sq", "Tappan St", "Dean Rd", "Englewood Ave", "Cleveland Circle"], "l"),
                 (["Fenway", "Longwood", "Brookline Village", "Brookline Hills", "Beaconsfield", "Reservoir", "Chestnut Hill", "Newton Centre", "Newton Highlands", "Eliot", "Waban", "Woodland", "Riverside"], "l"),
                 (["Prudential", "Symphony", "Northeastern", "Museum of Fine Arts", "Longwood Medical Area", "Brigham Circle", "Fenwood Rd", "Mission Park", "Riverway", "Back of the Hill", "Heath St", "Hyde Sq"], "l"),
                 (["Blandford St", "BU East", "BU Central", "Amory St", "Babcock St", "Packard's Corner", "Harvard Ave"], "r"),
                 (["St. Mary's St", "Hawes St"], "dn"), (["Copley", "Arlington", "Boylston"], "up"), (["Hynes"], "b"), (["Kenmore"], "tl"),
                 (["Needham Heights"], "r"), (["Needham Junction"], "l"), (["Courthouse"], "b"), (["Seaport"], "r"), (["Mass Ave"], "tl"), (["Inner Belt", ], "r"), (["Bellingham Sq"], "l"), (["Chelsea", "Everett Sq", "Stadium", "Encore"], "up"), (["Binney"], "l"), (["Allston", "Oak Sq"], "t"), (["Brighton Center"], "t"), (["Newton Corner"], "r"), (["Watertown"], "l"), (["Reading", "Wakefield", "Greenwood", "Melrose Highlands", "Wyoming Hill"], "l"),
                 (["West Station"], "tr"), (["Barrys Corner"], "r"), (["BU Bridge"], "r"), (["Lansdowne"], "tr"),
                 (["Charles/MGH"], "bl"), (["Park Street"], "br"),
                 (["Downtown Crossing"], "l"), (["Sullivan Sq"], "x"), (["JFK/UMass"], "br"), (["Airport"], "br")):
    for n in names:
        SIDE[n] = s
NUDGE = {"Langone Ferryport": (2.4, -1.9), "North Cambridge": (1.5, 1.4), "Lechmere": (2.4, 0), "East Somerville": (4.5, 1.6), "Union Sq": (-3, 0), "Four Corners": (-0.5, 2.6), "Uphams Corner": (0.6, -0.4), "Chinatown": (-1, 0), "Savin Hill": (-1.5, 0), "Fields Corner": (-1.5, 0), "Shawmut": (-1.5, 0), "Park Street": (1.4, 0.8), "Charles/MGH": (-1.5, 0), "Navy Yard": (-0.8, 0), "Airport": (2.5, -1),
         "Brigham Circle": (0, -1.6), "Bellingham Sq": (-1.5, -2), "Lansdowne": (0.6, 0.7)}
HALOED = {"Thompson Sq", "West Broadway", "Assembly", "Lansdowne"}
SIDE.update({"Langone Ferryport": "r", "Dover": "r", "Northampton": "r", "Grove Hall": "r", "Wellington Hill": "along", "Blue Hill Ave": "l", "Inman Sq": "b", "Davis": "l", "Auburndale": "l", "Riverside": "l", "Union Sq": "t", "Lynn Harbor": "br", "Broadway": "br", "Charles/MGH": "tl", "Kendall/MIT": "l", "Assembly": "tr", "Encore": "b", "Lansdowne": "br", "Ruggles": "bl", "Brigham Circle": "l", "L Street": "t", "Seaport": "br", "Newmarket": "br", "Roslindale Village": "tl", "Hyde Park": "tr", "Heath St": "l", "Newton Corner": "t", "Courthouse": "t", "Hyde Sq": "l", "Forest Hills": "x", "Orient Heights": "r", "Seaver St": "l", "Terminals": "bl", "Roxbury Crossing": "br", "Broadway": "bl", "Thompson Sq": "l", "Navy Yard": "r", "City Square": "r", "Fort Point": "b", "Aquarium": "br", "Convention Center": "br", "City Point": "r", "West Broadway": "t", "Bellingham Sq": "r", "Stadium": "up", "Assembly": "tl", "Encore": "t", "Chelsea": "up", "Everett Sq": "up", "Nubian": "up"})


def water(ax, z=1):
    ax.add_patch(Polygon(smooth_closed([(117, 121), (122, 112), (121, 92), (128, 86), (150, 84), (156, 74), (146, 62), (141, 48), (145, 30), (140, 10), (142, -40),
                                        (260, -40), (260, 240), (222, 240), (196, 164), (172, 136), (154, 116), (138, 110), (127, 118), (129, 133), (121, 134)]),
                         fc=WATER, ec="none", zorder=z))
    for pts, w in (([(-70, 100), (-10, 118), (30, 116), (46, 106), (62, 103), (78, 96), (92, 110), (104, 126), (120, 127)], 11),
                   ([(122, 130), (130, 144), (124, 167), (98, 176), (80, 190)], 7)):
        ax.plot(*smooth_open(pts).T, color=WATER, lw=w * 1.4, zorder=z, solid_capstyle="round")


def glpill(ax, x, y, letter):
    """Green Line pill: GL plus the branch letter in a white circle, as on the poster."""
    h, w = 3.7, 9.2  # same height and type size as the other line bullets; GL and the letter centered as one group
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=GREEN, ec="none", zorder=12))
    ax.text(x - 1.3, y - 0.19, "GL", color=WHITE, fontsize=9.0, fontweight="bold", ha="center", va="center", zorder=12.1)
    ax.scatter([x + 1.75], [y], s=56, color=WHITE, zorder=12.2)
    ax.text(x + 1.75, y - 0.05, letter, color=GREEN, fontsize=8.2, fontweight="bold", ha="center", va="center", zorder=12.3)


def not_accessible():
    out = set()
    with (DAY / "data/wheelchair.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["wheelchair_boarding"] == "2":
                n = row["name"]
                for a, b in (("Saint ", "St. "), (" Street", " St"), (" Square", " Sq"), (" Avenue", " Ave"), (" Road", " Rd"), ("Hynes Convention Center", "Hynes")):
                    n = n.replace(a, b)
                out.add(n)
    return out


WHEEL = TextPath((0, 0), chr(0x267F), size=1.34, prop=FontProperties(family="DejaVu Sans"))
WHEEL = Affine2D().translate(*(-(WHEEL.get_extents().min + WHEEL.get_extents().max) / 2)).transform_path(WHEEL)


def icon(ax, x, y, z=11):
    """Small blue accessible-station square, as on the wall map."""
    a = 0.85
    ax.add_patch(FancyBboxPatch((x - a, y - a), 2 * a, 2 * a, boxstyle="round,pad=0,rounding_size=0.25", fc="#165c96", ec="none", zorder=z))
    ax.add_patch(PathPatch(Affine2D().translate(x, y - 0.03).transform_path(WHEEL), fc=WHITE, ec="none", zorder=z + 0.1))


SIDE["Broadway"] = "br"
SIDE.update({"Charles/MGH": "tr", "Chinatown": "l", "Grove Hall": "l", "Fields Corner": "r", "Navy Yard": "r", "Thompson Sq": "l"})
TEXT.update({"Bellingham Sq": "Bellingham\nSq", "Navy Yard": "Navy\nYard", "Uphams Corner": "Uphams\nCorner"})
HALOED.update({"Downtown Crossing", "Park Street"})
SIDE["Landmark Center"] = "l"
SIDE["City Square"] = "r"
NUDGE["City Square"] = (0, -1.4)
TEXT["City Square"] = "City\nSquare"
NUDGE["Landmark Center"] = (0.8, 0)
TEXT["Landmark Center"] = "Landmark\nCenter"
SIDE["Medford Hillside"] = "l"
SIDE.update({"East Saugus": "b", "Saugus Center": "t", "Lexington Route 128": "l", "Waltham": "l"})
TEXT["Lexington Route 128"] = "Lexington\nRoute 128"
TEXT["Saugus Center"] = "Saugus\nCenter"
NUDGE["Hyde Park"] = (3.8, 0)
SIDE.update({"Hersey": "l", "Hyde Park": "r", "VFW Parkway": "br", "Needham Junction": "l"})
for n in ("Broadway", "Andrew", "JFK/UMass", "North Quincy", "Wollaston", "Quincy Center", "Quincy Adams"):
    NUDGE[n] = (NUDGE.get(n, (0, 0))[0] + 2.6, NUDGE.get(n, (0, 0))[1])
TEXT["Hyde Park"] = "Hyde\nPark"
SIDE.update({"Andrew": "l", "Fields Corner": "l"})
NUDGE["Andrew"] = (0, 0)
NUDGE["Mass. Ave"] = (-1.6, -0.9)  # clear of the larger Back Bay ring
NUDGE["Fields Corner"] = (0, 0)
NUDGE["East Saugus"] = (-1.6, 0)
NUDGE["East Somerville"] = (3, 1.6)
HALOED.update({"Charles/MGH", "Mass. Ave", "Northampton", "Newmarket", "East Saugus", "Broadway", "East Somerville"})
SIDE["Wyoma Sq"] = "l"
SIDE["Terminals"] = "l"
TEXT["Terminals"] = "Logan Terminals"  # plain "Terminals" read oddly beside the lettered terminals
NUDGE["Terminals"] = (0, 1.5)
HALOED.update({"Terminals", "Maverick"})
SIDE["Stadium"] = "bl"
TEXT["Thompson Sq"] = "Thompson\nSq"
NUDGE["Bellingham Sq"] = (-1, 1.8)
NUDGE["Airport"] = (-0.5, 0)
SIDE["Maverick"] = "br"
NUDGE["Maverick"] = (-5, -0.8)
NUDGE["Downtown Crossing"] = (1.2, -1.6)
SIDE["Weymouth"] = "l"
NUDGE["Weymouth"] = (0, -1.4)
SIDE["Braintree"] = "l"
SIDE["Broadway"] = "bl"
NUDGE["West Broadway"] = (3.6, 0)
NUDGE["Broadway"] = (0, 0)
SIDE["Museum of Fine Arts"] = "r"
NUDGE.pop("Brigham Circle", None)
SIDE["Encore"] = "x"
SIDE["Park Street"] = "r"
NUDGE["Park Street"] = (0.4, -0.5)
SIDE["Downtown Crossing"] = "x"
TEXT.update({"Arlington Ctr": "Arlington Center", "Belmont Ctr": "Belmont Center", "Lexington Ctr": "Lexington Center", "Tufts Medical Ctr": "Tufts Medical\nCenter", "Park Street": "Park St", "L Street": "L St", "City Square": "City Sq", "Mass. Ave": "Mass Ave"})
SIDE["Moakley Park"] = "br"
SIDE["Day Sq"] = "r"
# Max's review, Nov 7: level labels and tidier spots
SIDE.update({"Boston College": "l", "Newton City Hall": "r", "Auburndale": "l", "Weston": "l", "Riverside": "l", "Wellesley Hills": "l",
             "Newton Upper Falls": "r", "Needham Crossing": "l", "Needham Heights": "r"})
TEXT["Needham Crossing"] = "Needham\nCrossing"
SIDE.update({"Chinatown": "r", "Navy Yard": "l", "Lynn Harbor": "r", "Boylston": "tl", "Copley": "t", "Arlington": "b"})
NUDGE["Copley"] = (0.8, 0)
NUDGE.update({"Lechmere": (0.4, 0), "Roxbury Crossing": (-2.6, 0), "Uphams Corner": (0.6, -0.4), "Kenmore": (0.8, -0.2), "Blandford St": (0, 0.7), "Chinatown": (-0.7, 0),
              "Navy Yard": (0, 0), "Lynn Harbor": (0, -1.8), "Chelsea": (1.5, 0), "East Somerville": (0, 0.4)})
NUDGE["Day Sq"] = (-1.1, 0.5)


# Final audit, November 7: level labels everywhere, and clear of lines
SIDE.update({"St. Mary's St": "b", "Fairmount": "r", "Hawes St": "l", "Everett Sq": "t", "Chelsea": "tr",
             "Milton": "b", "Central Ave": "t", "Valley Rd": "b", "Capen St": "t", "Talbot Ave": "r", "Morton St": "r", "Wellington Hill": "along",
             "Melrose/Cedar Park": "l", "Wellington": "tl", "Cliftondale": "tl", "Northampton": "r", "Lechmere": "x"})
NUDGE.update({"Hawes St": (0.6, -2.0), "Union Sq": (-3, -0.8), "East Somerville": (-0.8, 1.2), "Stadium": (-0.6, 0), "Day Sq": (-1.8, 0.5),
              "Kent St": (-0.7, 0.4), "Newton City Hall": (0.7, -0.6), "Chinatown": (-1.4, 0), "Watertown": (0, -1.3), "Chelsea": (0, 0)})
NUDGE.pop("North Cambridge", None)
TEXT["Saugus Center"] = "Saugus Center"


# Type audit, November 7 (15 reviewers; audit_type/MERGED.md). Later lines win.
SIDE.update({"North Cambridge": "r", "Wellington": "l", "City Square": "r", "Savin Hill": "l", "Shawmut": "l", "Lynn Harbor": "l",
             "Langone Ferryport": "tr", "Hawes St": "b"})
NUDGE.update({"Harvard Ave": (0.3, 1.6), "Hawes St": (-2.2, -0.6), "St. Mary's St": (0.8, 0), "Newton City Hall": (0, -1.2), "Auburndale": (0, 0.9),
              "Boston College": (0, 0.5), "East Somerville": (-1.4, 1.2), "Stadium": (-0.35, -0.2), "Linden Sq": (-0.8, 0), "Davis": (-0.5, 0),
              "North Cambridge": (0.8, 0), "Science Park": (0.4, 0.5), "City Square": (-0.4, -1.4), "Inman Sq": (1.4, 0), "Kendall/MIT": (-0.4, 0),
              "Mass Ave": (-0.4, -0.7), "Day Sq": (-0.9, 0), "Bellingham Sq": (-1, 1.2), "Lynn Harbor": (0, 0.4), "Wood Island": (0.4, 0.4),
              "Savin Hill": (-0.75, 0), "Shawmut": (-0.1, 0), "Chinatown": (-1.3, -1.5), "Four Corners": (-0.5, 2.6), "Mattapan": (-1.0, 0),
              "Weymouth": (0, 0), "West Broadway": (0.6, 0), "Langone Ferryport": (-0.6, -0.9), "Maverick": (-2.8, -1.4), "Mass. Ave": (-1.1, -0.9),
              "West Medford": (-0.6, -0.8)})
TEXT.update({"City Square": "City\nSq", "Charles/MGH": "Charles/\nMGH", "Day Sq": "Day\nSq", "Savin Hill": "Savin\nHill",
             "West Broadway": "West\nBroadway", "St. Mary's St": "St. Mary\u2019s St", "Packard's Corner": "Packard\u2019s Corner",
             "Gov't Center": "Gov\u2019t Center"})
TEXT.pop("Needham Junction", None)  # the full name fits on one line
HALOED |= {"Langone Ferryport", "Museum of Fine Arts"}
A["Allston"] = (43.5, 111)  # off the Worcester Line, so it doesn't read as a rail transfer
A["Maverick"] = (127.5, 117.5)  # down the Blue Line, clear of STATION
A["Mass. Ave"] = (78.5, 62.5)  # its name no longer sits under the Back Bay ring
_ROWS = {"FRAMINGHAM / WORCESTER LINE": 129.0, "HIGH-SPEED RAIL TO ALBANY": 126.4, "VIA WORCESTER, SPRINGFIELD": 123.8,
         "LOWELL LINE": 204.4, "HIGH-SPEED RAIL TO CONCORD NH": 201.8, "VIA LOWELL, NASHUA, MANCHESTER": 199.2}
CR_TEXT = [(s, (xy[0], _ROWS[s]) if s in _ROWS else (xy[0], xy[1] + 0.6) if s in ("NEWBURYPORT / ROCKPORT LINE", "HIGH-SPEED RAIL TO BANGOR", "VIA PORTSMOUTH, PORTLAND, AUGUSTA") else xy, ha)
           for s, xy, ha in CR_TEXT]  # even 2.6 leading; Newburyport rows clear of Middleton
for _p in CR_PATHS:  # lines run under the edge arrowheads, no hairline gap
    for _i in (0, -1):
        if abs(_p[_i][1] - 213.2) < 1e-6:
            _p[_i] = (_p[_i][0], 213.9)

A["Vertex Tower"] = (146.5, 76)  # a new supertall in the Seaport, with its own stop
SIDE["Vertex Tower"] = "t"
SIDE["Wu Sq"] = "tl"  # a hero square in Roslindale, where the mayor lives: a quiet nod to Mayor Wu
NUDGE["Vertex Tower"] = (3.2, 0)  # over open water, clear of the Courthouse dock and Yellow
CAPSULES.append(((59, 84), (61.7, 86.3)))  # David Ortiz commuter stop and Hynes, one transfer station
CAPSULES.append(((110, 182), (114, 182)))
A["Langone Ferryport"] = (118, 114)
CAPSULES.append(((118, 114), (118, 120)))  # Langone Ferryport joins North Station as one complex (Max: "it also connects to north station")  # Oak Grove: Orange and the Haverhill Line, like Malden Center (Max, November 7)

# Real shoreline points (lon, lat) and where each sits on the diagram. The real coast and islands are bent through these.
SHORE = {(-71.0475, 42.3595): (120.4, 106), (-71.0505, 42.3665): (120.6, 116), (-71.0600, 42.3725): (121, 124), (-71.0480, 42.3750): (127, 130), (-71.0390, 42.3690): (126.6, 119),
         (-71.0290, 42.3590): (129, 106), (-71.0100, 42.3540): (146, 92), (-70.9950, 42.3650): (162, 106), (-70.9600, 42.3620): (170, 113), (-70.9610, 42.3760): (177, 121),
         (-70.9750, 42.3830): (171, 133), (-70.9900, 42.3910): (160, 137), (-70.9900, 42.3970): (161, 146), (-70.9850, 42.4170): (167, 152), (-70.9650, 42.4440): (183, 168),
         (-70.9450, 42.4560): (193, 177), (-70.9320, 42.4640): (200, 183), (-70.8950, 42.4640): (205, 187.5), (-70.8610, 42.4830): (212, 188.5), (-70.8530, 42.4960): (213.5, 192), (-70.8370, 42.4880): (219.5, 187.5), (-70.8320, 42.5040): (220.5, 194), (-70.8500, 42.5140): (215.5, 198), (-70.8700, 42.5180): (213.5, 200.5), (-70.8700, 42.5350): (218.5, 208), (-70.8200, 42.5200): (228, 204), (-70.9100, 42.5000): (214, 196), (-70.9350, 42.4320): (205, 166), (-70.9020, 42.4220): (220, 160),
         (-71.0420, 42.3540): (122, 84.5), (-71.0300, 42.3500): (137, 82), (-71.0230, 42.3460): (150, 80), (-71.0115, 42.3380): (160, 68), (-71.0250, 42.3310): (156, 62.5), (-71.0450, 42.3270): (140, 60),
         (-71.0370, 42.3140): (145, 50), (-71.0360, 42.2990): (141, 43), (-71.0080, 42.3090): (150, 36), (-71.0090, 42.2740): (144, 24), (-70.9610, 42.2730): (155, 12), (-70.9700, 42.2420): (145, 2),
         (-70.8950, 42.2520): (178, -6), (-70.9180, 42.3060): (189, 60), (-70.8700, 42.2700): (235, 46), (-71.0080, 42.3170): (151, 51), (-70.9670, 42.3270): (166, 66), (-70.9290, 42.3200): (178, 72),
         (-70.9330, 42.2970): (176, 58), (-70.9290, 42.3310): (192, 77), (-71.2, 42.5): (20, 220), (-71.3, 42.2): (-60, 0), (-70.6, 42.3): (300, 70), (-71.05, 42.0): (130, -120)}
GEORGES = (-70.9290, 42.3200)


def real_water(ax, pts):
    """The real coast and islands (Census towns), bent to the diagram through hand-matched shoreline points."""
    global SEA, WARP
    src = gpd.GeoSeries([Point(k) for k in SHORE], crs=4326).to_crs(26919)
    WARP = RBFInterpolator(np.array([(q.x, q.y) for q in src]), np.array(list(SHORE.values()), float), kernel="thin_plate_spline", smoothing=30)
    frame = box(-71.25, 42.0, -70.55, 42.62)
    towns = gpd.read_file(REPO / "data/shared/ne_towns.gpkg").to_crs(4326)
    land = towns[towns.intersects(frame)].geometry.union_all().buffer(0)
    sea = gpd.GeoSeries([frame.difference(land)], crs=4326).to_crs(26919).simplify(15).iloc[0]
    bent = []
    for poly in getattr(sea, "geoms", [sea]):
        if poly.area < 6e5:
            continue
        d = poly.segmentize(250)
        holes = [WARP(np.array(r.segmentize(250).coords)[:, :2]) for r in d.interiors if ShapelyPolygon(r).area > 6e4]
        bent.append(ShapelyPolygon(WARP(np.array(d.exterior.coords)[:, :2]), holes).buffer(0))
    SEA = unary_union(bent).buffer(0.35).buffer(-0.7).buffer(0.35)
    for g in getattr(SEA, "geoms", [SEA]):
        ax.add_patch(Polygon(np.array(g.exterior.coords), fc=WATER, ec=COAST, lw=0.45, zorder=1))
        for r in g.interiors:
            ax.add_patch(Polygon(np.array(r.coords), fc=PAPER, ec=COAST, lw=0.45, zorder=1.1))


RIVERS = {"charles": [(-16, 128), (30, 128), (50, 125), (59, 118), (63, 108), (68, 98), (76, 99), (85, 105), (92, 118), (100, 127), (110, 128), (118, 127), (127, 123)],
          # The Mystic runs up past Navy Yard, under the Yellow Line beside Stadium, to the Encore dock, then on upriver
          "mystic": [(127, 123), (129.2, 130), (129.4, 136.5), (128.6, 141.5), (126.0, 146.2), (122.6, 149.4), (120.6, 151.8), (117.6, 154.6), (112, 161), (96, 174), (84, 186)],
          # Chelsea Creek runs level between the Day Sq and Bellingham Sq names, then up to Suffolk Downs, so its loop has water
          "chelsea": [(129.4, 135.1), (133.5, 135.25), (135.0, 135.3), (136.6, 135.6), (137.5, 135.85), (139.6, 135.9), (141.0, 136.25),
                      (142.5, 136.55), (144.6, 136.95), (145.9, 137.9), (146.6, 139.0), (147.6, 140.6), (149.0, 142.4), (150.2, 144.2), (151.0, 146.0)],
          "belle isle": [(168.4, 146.5), (163.6, 146.6), (159.8, 146.8)],  # Belle Isle Inlet, up to Suffolk Downs
          "neponset": [(141, 43), (118, 47), (108, 37), (99, 27), (97, 4), (100, -22)]}
WIDTH = {"charles": 13, "mystic": 14, "chelsea": 10, "belle isle": 8, "neponset": 7}  # wide enough for a river loop's two tracks
CHARLES_WEST = [(-15.0, 128.1), (-16.6, 130.0), (-18.0, 131.9), (-21.0, 132.6), (-30.0, 132.7), (-38.0, 132.4), (-47.5, 132.1)]  # between the caption blocks
BASIN = [(120, 127), (110, 128), (100, 127), (92, 118), (85, 105), (76, 99), (66, 97.5)]
BASIN_PT = 27  # line width in points, about 5.6 diagram units


def river_mouths(ax):
    """Hand-drawn so each stop is on its true bank: Harvard and MIT north of the Charles, Allston and BU south;
    Assembly and Sullivan west of the Mystic, Encore and the stadium east; Ashmont branch north of the Neponset."""
    for n, xy in RIVERS.items():
        ax.plot(*smooth_open(xy, 2).T, color=WATER, lw=WIDTH[n], zorder=0.95, solid_capstyle="round", solid_joinstyle="round")
    ax.plot(*smooth_open(BASIN, 2).T, color=WATER, lw=BASIN_PT, zorder=0.95, solid_capstyle="round", solid_joinstyle="round")
    # The Charles goes on past the boats' turn toward Waltham, narrowing to a third of its width at the edge of the sheet
    w = smooth_open(CHARLES_WEST, 3)
    run = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(w, axis=0).T))])
    for k in range(len(w) - 1):
        ax.plot(*w[k:k + 2].T, color=WATER, lw=WIDTH["charles"] * (1 - 0.66 * run[k] / run[-1]), zorder=0.95, solid_capstyle="round")


FERRY = "#00796d"  # Harbor West teal, the default ferry pill color on the line posters
# The whole ferry network, route for route as on the Ferry Map poster (make_ferry_network.py, November 7). Colors come in families:
# purple river loops, teal harbor boats, brown South Boston and Quincy boats, olive and lime North Shore, oxblood South Shore.
# River boats run two-bank loops. The North Shore and South Shore Express boats are high-speed streaks; this map shows them to
# Beverly and Hingham, and the Ferry Map carries them on. title is the rider name the line posters use. Every stop gets a small dot;
# only docks that link to a station get a square, a walking link and a name (Max, November 7).
FERRY_ROUTES = [
    {"key": "charles", "title": "Charles River", "color": "#9e00ff", "loop": True,
     "stops": ["Langone Ferryport", "Lovejoy Wharf", "Nashua St", "Gronk", "Hatch Shell", "Esplanade", "Gloucester St", "BU Docks", "BU Bridge", "Agganis", "Western Ave",
               "John W. Weeks", "Newell", "Cumnock", "Herter", "Northeastern", "Arsenal St",  # Boston bank, upstream
               "Belmont Hill", "Winsor", "Eliot", "Weld", "Riverside", "Magazine Beach", "DeWolfe", "Resch", "Ames St", "Broad Canal", "Poormans",
               "Charlesgate", "Museum of Science", "North Point", "Duck Tours", "Paul Revere Park", "Navy Yard"]},  # Cambridge bank, inbound
    {"key": "mystic", "title": "Mystic River", "color": "#cf8bff", "loop": True,
     "stops": ["Langone Ferryport", "Menino", "Navy Yard", "Little Mystic", "Medford St", "Alford St", "Assembly", "Encore", "Stadium", "Admirals Hill", "Pearl St"]},
    {"key": "chelsea", "title": "Chelsea Creek", "color": "#c74ae6", "loop": True,
     "stops": ["Langone Ferryport", "Quigley", "Chelsea St", "Eastern Ave", "Suffolk Downs", "Addison St", "Condor St", "Boston Bay"]},
    {"key": "hw", "title": "Harbor West", "color": "#00796d",
     "stops": ["Langone Ferryport", "Lovejoy Wharf", "Battery Wharf", "Sargent's Wharf", "Long Wharf", "Central Wharf", "Rowes Wharf", "Dorchester Ave"]},
    {"key": "express", "title": "Fast Ferry", "color": "#003d36", "stops": ["Navy Yard", "Langone Ferryport", "Long Wharf"]},  # nonstop between them, at all times
    {"key": "eb", "title": "East Boston", "color": "#26a69a", "stops": ["Langone Ferryport", "White St", "Bennington St", "Piers Park", "Porzio", "Logan Dock"]},
    {"key": "hi", "title": "Harbor Islands", "color": "#005f73", "stops": ["Langone Ferryport", "Long Island", "Georges Island", "Spectacle Island", "Deer Island"]},
    {"key": "seaport", "title": "Seaport", "color": "#8a4b1c", "stops": ["Langone Ferryport", "Martins Park", "Fan Pier", "Seaport", "Pavilion"]},
    {"key": "ssi", "title": "South Shore", "color": "#b5652a",
     "stops": ["Langone Ferryport", "First St", "Castle Island", "M St", "Carson Beach", "Dorchester Shores", "Old Harbor", "UMass Boston", "Fox Point", "Finigan"]},
    {"key": "qb", "title": "Quincy Bay", "color": "#4a2a14",
     "stops": ["Langone Ferryport", "Squantum Point", "Nickerson", "Thompson Island", "Moon Island", "Squantum", "Wollaston Beach", "Hough's Neck", "Nut Island"]},
    {"key": "fore", "title": "Fore River", "color": "#a07a52", "stops": ["Langone Ferryport", "Bay Pointe", "King's Cove", "Wessagusset", "Hingham", "Nantasket", "Hull"]},
    {"key": "nse", "title": "North Shore", "color": "#9eb000", "fast": True,
     "express_stops": ["Langone Ferryport", "Lynn Harbor", "Salem Wharf", "Gloucester", "Rockport", "Newburyport", "Salisbury"],  # high-speed trips
     "stops": ["Langone Ferryport", "Winthrop Landing", "Winthrop Beach", "Highlands Beach", "Suffolk Downs", "Beachmont", "Revere Beach", "Wonderland",
               "Lynn Harbor", "Nahant Harbor", "Swampscott", "Clifton", "Marblehead", "Salem Wharf", "Beverly"]},
    {"key": "sse", "title": "South Shore", "color": "#611824", "fast": True,
     "stops": ["Langone Ferryport", "Carson Beach", "UMass Boston", "Squantum Point", "Quincy", "Quincy Point", "Hingham"]},
]
ROUTE_COLOR = {r["key"]: r["color"] for r in FERRY_ROUTES}
ROUTE_COLOR.update({"inner-harbor": ROUTE_COLOR["hw"], "north-shore": ROUTE_COLOR["nse"], "south-shore": ROUTE_COLOR["sse"],
                    "harbor-islands": ROUTE_COLOR["hi"]})  # older names, still read by the T stripes and the line posters
# Rough spot for every stop off the river loops. Docks snap to the nearest shore unless listed in AS_DRAWN.
FERRY_SPOTS = {
    "Lovejoy Wharf": (120.2, 125.5), "Langone Ferryport": (120.9, 113.0), "Wonderland": (180.6, 166.6), "Battery Wharf": (122.6, 109.1), "Sargent's Wharf": (120.75, 107.75),
    "Long Wharf": (121.0, 103.0), "Central Wharf": (120.3, 100.3), "Rowes Wharf": (120.3, 96.6), "Dorchester Ave": (120.9, 88.3),
    "White St": (124.9, 122.4), "Bennington St": (124.15, 118.8), "Piers Park": (128.5, 108.0), "Porzio": (133.4, 103.0), "Logan Dock": (139.6, 95.0),
    "Martins Park": (123.0, 91.0), "Fan Pier": (139.5, 82.5), "Seaport": (143.6, 81.3), "Pavilion": (150.4, 81.4),
    "First St": (155.4, 79.3), "Castle Island": (162.6, 64.6), "M St": (158.6, 62.0), "Carson Beach": (146.5, 60.5),
    "Dorchester Shores": (141.0, 59.0), "Old Harbor": (143.4, 55.6), "UMass Boston": (149.4, 53.2), "Fox Point": (142.0, 46.8), "Finigan": (138.4, 43.0),
    "Squantum Point": (146.0, 44.5), "Nickerson": (148.8, 41.0), "Thompson Island": (152.6, 47.4), "Moon Island": (154.2, 41.2), "Squantum": (151.0, 34.4),
    "Wollaston Beach": (150.0, 28.4), "Hough's Neck": (152.4, 17.6), "Nut Island": (155.0, 21.4),
    "Quincy": (143.8, 28.5), "Quincy Point": (148.0, 25.5), "Bay Pointe": (144.6, 27.4), "King's Cove": (150.4, 21.0), "Wessagusset": (152.6, 12.0),
    "Hingham": (150.0, 9.0), "Nantasket": (185.2, 61.8), "Hull": (190.6, 61.4),
    "Long Island": (171.0, 69.6), "Georges Island": (178.0, 72.0), "Spectacle Island": (169.0, 76.0), "Deer Island": (175.6, 114.6),
    "Winthrop Beach": (180.4, 123.6), "Highlands Beach": (172.6, 134.6), "Revere Beach": (174.6, 159.8), "Beachmont": (165.2, 147.3),
    "Winthrop Landing": (172.0, 118.0), "Lynn Harbor": (190.0, 174.0), "Nahant Harbor": (208.0, 155.0), "Swampscott": (207.0, 187.0), "Clifton": (215.6, 186.4),
    "Marblehead": (217.6, 195.2), "Salem Wharf": (219.5, 205.6), "Beverly": (218.7, 212.8),  # Glover Wharf, bent from (-70.879, 42.544)
}
AS_DRAWN = {"Battery Wharf", "Sargent's Wharf", "Central Wharf", "Rowes Wharf", "White St", "Bennington St", "Porzio", "Martins Park", "Seaport",
            "Pavilion", "First St", "Castle Island", "M St", "Spectacle Island", "Deer Island", "Wonderland", "Clifton", "Winthrop Beach", "Revere Beach", "Beachmont", "Nantasket", "Hull",
            "Nickerson", "Thompson Island", "Moon Island", "Squantum", "Wollaston Beach", "Hough's Neck", "Nut Island", "Bay Pointe", "King's Cove",
            "Wessagusset", "Dorchester Shores", "Old Harbor", "UMass Boston", "Fox Point", "Finigan"}
# River-loop stops: a rough spot, put on the stop's own bank. Stops in LOOP_ENDS sit on the loop's turn instead.
LOOP_SPOTS = {
    "charles": {"Nashua St": (112.4, 126.6), "Gronk": (105.5, 126.6), "Hatch Shell": (90.3, 113.8), "Esplanade": (87.6, 107.0),
                "Gloucester St": (83.4, 103.4), "BU Docks": (79.6, 99.4), "BU Bridge": (66.4, 100.6), "Agganis": (62.0, 108.6),
                "Western Ave": (59.0, 116.6), "John W. Weeks": (53.0, 122.6), "Newell": (45.0, 126.0), "Cumnock": (36.0, 127.4),
                "Herter": (27.0, 128.0), "Northeastern": (10.0, 128.0), "Arsenal St": (-12.5, 128.0),
                "Belmont Hill": (-14.8, 128.0), "Winsor": (2.0, 128.0), "Eliot": (17.0, 128.0), "Weld": (58.8, 119.6), "Riverside": (62.4, 112.6),
                "Magazine Beach": (70.6, 99.4), "DeWolfe": (73.4, 99.5), "Resch": (76.2, 100.0), "Ames St": (85.6, 110.2), "Broad Canal": (88.6, 112.8),
                "Poormans": (91.0, 116.0), "Charlesgate": (93.6, 120.6), "Museum of Science": (96.9, 124.1), "North Point": (106.8, 127.4),
                "Duck Tours": (115.6, 127.5), "Paul Revere Park": (123.8, 125.9)},
    "mystic": {"Menino": (128.8, 131.4), "Little Mystic": (128.9, 138.0), "Medford St": (128.6, 140.8), "Alford St": (127.8, 143.0),
               "Encore": (121.6, 152.2), "Stadium": (128.0, 144.3), "Admirals Hill": (129.4, 141.6), "Pearl St": (129.8, 133.2)},
    "chelsea": {"Quigley": (132.4, 135.6), "Chelsea St": (142.6, 136.9), "Eastern Ave": (148.6, 141.9), "Addison St": (147.2, 139.8),
                "Condor St": (141.6, 136.0), "Boston Bay": (132.6, 134.8)},
}
LOOP_ENDS = {"mystic": {"Assembly": (119.55, 152.8)}, "chelsea": {"Suffolk Downs": (151.0, 145.4)}}
# Docks that link to a station: (spot, station, label side, gap, label text); spots come from FERRY_SPOTS and the river loops.
# They get a square, a fine dotted walking link and a name. side None: the station's own name labels the dock.
DOCKS = {
    "Lovejoy Wharf": (None, "North Station", None, 0, None), "Navy Yard": (None, "Navy Yard", None, 0, None),
    "Weld": (None, "Harvard", "r", 1.5, None), "BU Bridge": (None, "BU Bridge", None, 0, None), "Ames St": (None, "Kendall/MIT", "r", 2.4, None),
    "Encore": (None, "Encore", None, 0, None), "Stadium": (None, "Stadium", None, 0, None), "Suffolk Downs": (None, "Suffolk Downs", None, 0, None),
    "Langone Ferryport": (None, "Langone Ferryport", None, 0, None), "Long Wharf": (None, "Aquarium", "r", 1.6, None),
    "Wonderland": (None, "Wonderland", None, 0, None), "Dorchester Ave": (None, "South Station", "r", 1.5, None),
    "Piers Park": (None, "Maverick", "tr", 1.6, None), "Logan Dock": (None, None, "b", 2.0, None), "Fan Pier": (None, "Courthouse", "tl", 1.8, None),
    "Carson Beach": (None, "L Street", "tr", 1.2, None),
    "Revere Beach": (None, "Revere Beach", None, 0, None), "Beachmont": (None, "Beachmont", None, 0, None), "Lynn Harbor": (None, "Lynn Harbor", None, 0, None),
    "Swampscott": (None, "Swampscott", None, 0, None), "Marblehead": (None, "Marblehead", None, 0, None),  # named by the commuter stops they link to
    "Salem Wharf": (None, "Salem", None, 0, None), "Beverly": (None, "Beverly", None, 0, None),
}
NSE_SUFFOLK = (160.6, 146.8)  # the North Shore boats' Suffolk Downs landing, at the head of Belle Isle Inlet
LINK_AT = {"North Station": (117.8, 121.4), "South Station": (117.6, 80.0)}  # the pill ends nearest the dock
LABEL_AT = {"Lovejoy Wharf": ((119.3, 122.4), "r", "Lovejoy Wharf")}  # in NORTH STATION's old spot, right of its pill
HUB_DOCKS = {"Langone Ferryport"}  # every major ferry route starts and ends here (Max, November 7)
# Best-known Charles docks with room for a name, though no station is beside them: (side, gap)
STOP_LABELS = {"Hatch Shell": ("r", 1.5), "Esplanade": ("r", 1.5), "Herter": ("b", 1.4), "Arsenal St": ("b", 1.4), "Northeastern": ("t", 2.0),
               "Eliot": ("t", 1.2)}
# Built from FERRY_ROUTES for make_ferry_poster.py
FERRY_LEGS = [{"key": r["key"], "title": r["title"], "kind": "strip", "outline": r["color"], "hub": r["stops"][0],
               "hubs": [s for s in r["stops"] if s in ("Long Wharf", "Lovejoy Wharf")] or [r["stops"][0]],
               "stops": r["stops"], "pills": r.get("pills", {}), "note": r.get("note"), "poster": True} for r in FERRY_ROUTES]


# Boats stay out of these boxes: the Key, the BOSTON CENTRAL and SOUTH STATION names, City Point and Vertex Tower.
KEEP_OUT = [(156.2, 222, -20, 60.6), (121.5, 138.2, 93.3, 101.8), (120.0, 137.5, 80.6, 86.4), (152.5, 166.0, 68.6, 72.2), (145.6, 154.0, 77.0, 80.4),
            (192.6, 230.0, 79.4, 145.0)]  # last one is the BIGGER Dig panel
LOOP_LW, LOOP_GAP = 2.4, 0.42
WATERMARKS = [(184.5, 95.0), (188.5, 110.0), (213.0, 75.0), (186.0, 84.5), (225.5, 76.0)]  # river loops: two rows of small dots, 2 x 0.42 units apart


def ferry_track(ax, xy, color, lw=3.4, z=2.6, phase=0.0, casing=True, fast=False):
    """Round dots in the route color on a white wake, so ferries never read as subway.
    High-speed coast boats draw as streaks instead of dots."""
    xy = np.asarray(xy, float)
    if casing:
        ax.plot(*xy.T, color=WHITE, lw=lw + 2.6, solid_capstyle="round", solid_joinstyle="round", zorder=z)
    ax.plot(*xy.T, color=color, lw=lw, ls=(phase, (1.5, 1.6) if fast else (0.01, 1.9)), dash_capstyle="round", zorder=z + 0.1, gid="ferry")


def ferry_stop(ax, xy, z=7.25):
    """A small dot for a ferry stop with no station beside it. Its name is on the Ferry Map."""
    ax.scatter(*xy, s=15, color=WHITE, edgecolor=INK, lw=0.6, zorder=z)


def walk(ax, a, b, cut=None):
    """Walking link from a dock to its station: fine black dots, no text. cut: a box the dots skip (a label)."""
    seg = LineString([a, b])
    parts = [seg] if cut is None else [g for g in getattr(seg.difference(cut), "geoms", [seg.difference(cut)]) if not g.is_empty]
    for g in parts:
        xs, ys = g.xy
        ax.plot(xs, ys, color=INK, lw=1.0, ls=(0, (0.01, 1.6)), dash_capstyle="round", zorder=6.4)


def u_turn(a, b, toward, n=12):
    """Half circle from a to b, bulging toward a point: the end of a river loop."""
    a, b, toward = (np.asarray(v, float) for v in (a, b, toward))
    m, r = (a + b) / 2, np.hypot(*(b - a)) / 2
    t0 = np.arctan2(a[1] - m[1], a[0] - m[0])
    sgn = 1 if np.dot([np.cos(t0 + np.pi / 2), np.sin(t0 + np.pi / 2)], toward - m) > 0 else -1
    ts = t0 + sgn * np.linspace(0, np.pi, n)
    return m + r * np.column_stack([np.cos(ts), np.sin(ts)])


def twin_rows(center, h):
    """The two rows of a river loop: h either side of the middle line (h may vary along it, as a function of x, y)."""
    line = LineString(center)
    p = np.array([line.interpolate(t).coords[0] for t in np.linspace(0, line.length, max(3, int(line.length / 0.25)))])
    t = np.gradient(p, axis=0)
    t /= np.hypot(t[:, 0], t[:, 1])[:, None]
    n = np.column_stack([-t[:, 1], t[:, 0]])
    hh = np.array([h(x, y) for x, y in p]) if callable(h) else np.full(len(p), h)
    return p + n * hh[:, None], p - n * hh[:, None]


def ferries(ax):
    """Every ferry route through the water: shortest path on a grid of open water, kept toward mid-channel; river loops and the
    inner harbor channels by hand, so routes that share a channel share one path."""
    step = 0.5
    px = 4.84  # points per diagram unit
    wet = SEA.buffer(0)
    for n, xy in RIVERS.items():
        wet = wet.union(LineString(smooth_open(xy, 2)).buffer(WIDTH[n] / px / 2))
    wet = wet.union(LineString(smooth_open(BASIN, 2)).buffer(BASIN_PT / px / 2))
    xs = np.arange(50, XLIM[1], step)
    ys = np.arange(2, YLIM[1], step)
    gx, gy = np.meshgrid(xs, ys)
    inside = shapely.contains_xy(wet.buffer(-0.2), gx, gy)
    for x0, x1, y0, y1 in KEEP_OUT:
        inside &= ~((gx >= x0) & (gx <= x1) & (gy >= y0) & (gy <= y1))
    depth = distance_transform_edt(inside)
    idx = -np.ones(inside.shape, int)
    idx[inside] = np.arange(inside.sum())
    r, c, w = [], [], []
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        a = inside[max(0, -dy):inside.shape[0] - max(0, dy), max(0, -dx):inside.shape[1] - max(0, dx)]
        b = inside[max(0, dy):, max(0, dx):inside.shape[1] + min(0, dx) or None]
        A = idx[max(0, -dy):inside.shape[0] - max(0, dy), max(0, -dx):inside.shape[1] - max(0, dx)]
        B = idx[max(0, dy):, max(0, dx):inside.shape[1] + min(0, dx) or None]
        dA = depth[max(0, -dy):inside.shape[0] - max(0, dy), max(0, -dx):inside.shape[1] - max(0, dx)]
        dB = depth[max(0, dy):, max(0, dx):inside.shape[1] + min(0, dx) or None]
        ok = a & b
        L = np.hypot(dx, dy)
        r.append(A[ok]); c.append(B[ok]); w.append(L * (1 + 3 / (np.minimum(dA[ok], dB[ok]) + 0.5)))
    N = int(inside.sum())
    G = csr_matrix((np.concatenate(w), (np.concatenate(r), np.concatenate(c))), shape=(N, N))
    nodes = np.column_stack([gx[inside], gy[inside]])
    tree = cKDTree(nodes)

    def route(pts_):
        out = []
        for a, b in zip(pts_, pts_[1:]):
            ia, ib = tree.query(a)[1], tree.query(b)[1]
            if ia == ib:
                continue
            _, pred = dijkstra(G, directed=False, indices=ia, return_predecessors=True)
            if pred[ib] < 0:
                print("  no water path between", [round(v, 1) for v in a], "and", [round(v, 1) for v in b])
            path, k = [], ib
            while k != ia and k >= 0:
                path.append(k)
                k = pred[k]
            path.append(ia)
            xy = nodes[path[::-1]]
            xy = xy[::4] if len(xy) > 8 else xy
            out.append(smooth_open(np.vstack([nodes[ia], xy, nodes[ib]]), 3))
        return out

    def by_hand(*legs):
        """A path through hand-set points, rounded at its corners."""
        pts_ = [q for leg in legs for q in leg]
        keep = [pts_[0]] + [q for p_, q in zip(pts_, pts_[1:]) if np.hypot(q[0] - p_[0], q[1] - p_[1]) > 1e-6]
        return [smooth_open(np.array(keep, float), 3)]

    edge = wet.boundary

    def dock(q):
        d = edge.interpolate(edge.project(Point(q)))
        return (d.x, d.y)

    at = {n: (q if n in AS_DRAWN else dock(q)) for n, q in FERRY_SPOTS.items()}
    global LOGAN
    LOGAN = at["Logan Dock"]

    # Inner harbor channels by hand. NY: Navy Yard down the Mystic mouth to J, the junction off Lovejoy Wharf. CH: J down the
    # channel past North End (east of its name) to K, under the Blue Line off Long Wharf.
    at["Navy Yard"] = (128.55, 134.9)  # Charles, Mystic and the Express all call here: one dock
    J, J2, K = (123.9, 124.9), (125.3, 125.4), (123.1, 109.6)
    NY = [(128.2, 134.4), (128.05, 132.4), (128.0, 129.6), (127.75, 127.9), (127.3, 126.5), (126.5, 125.65), J2, J]
    CH = [J, (124.85, 123.4), (124.95, 122.0), (124.75, 121.0), (124.25, 119.0), (123.95, 118.0), (123.68, 117.0), (123.66, 115.0), (123.75, 113.5),
          (123.3, 112.0), (123.0, 111.0), K]  # hugs the East Boston bank, east of the North End and Lovejoy Wharf names
    to_lw = [K, (121.7, 108.6), at["Sargent's Wharf"], (119.95, 105.7), at["Long Wharf"]]
    LJ = [at["Lovejoy Wharf"], (121.9, 124.55), J]

    # River loops: two rows, one per bank, joined at each end. Stops sit on their own bank's row.
    h = LOOP_GAP
    charles = LineString(smooth_open(RIVERS["charles"], 2))
    cmain = np.array(substring(charles, 0, charles.project(Point(99.0, 125.8))).coords)
    cc = np.vstack([cmain, smooth_open([(99.0, 125.8), (102.0, 126.75), (106.0, 127.0), (112.0, 127.05), (116.5, 127.1), (120.2, 127.3)], 2)[1:]])
    ch_l, ch_r = twin_rows(cc, h)  # left: Cambridge bank, right: Boston bank
    # Cambridge row on to Navy Yard, joining the Navy Yard channel; Boston row down to Lovejoy Wharf; Lovejoy back out to the junction.
    ch_l = np.vstack([ch_l, smooth_open([ch_l[-1], (121.9, 126.9), (123.4, 125.9), J2] + NY[:6][::-1], 2)[1:]])
    rr = LineString(ch_r)
    ch_r = np.array(substring(rr, 0, rr.project(Point(118.6, 126.8))).coords)
    ch_r = np.vstack([smooth_open([at["Lovejoy Wharf"], (119.75, 125.7), ch_r[-1]], 2), ch_r[::-1][1:]])
    charles_path = [np.vstack([ch_r, u_turn(ch_r[-1], ch_l[0], (-20, 128)), ch_l]), smooth_open([J2, J, LJ[1], LJ[0]], 2)]
    mystic = LineString(smooth_open(RIVERS["mystic"], 2))
    m0, m1 = mystic.project(Point(129.3, 130.6)), mystic.project(Point(119.95, 152.45))
    my_c = np.array(substring(mystic, m1, m0).coords) if m1 < m0 else np.array(substring(mystic, m0, m1).coords)[::-1]  # upstream to downstream
    my_l, my_r = twin_rows(my_c, h)  # left: east bank (Encore to Pearl St), right: west bank (Menino to Assembly)
    mystic_path = np.vstack([my_l, u_turn(my_l[-1], my_r[-1], (129, 126)), my_r[::-1], u_turn(my_r[0], my_l[0], (118, 155))])
    ce_c = smooth_open(RIVERS["chelsea"], 3)
    ce_c = np.array(substring(LineString(ce_c), 1.4, LineString(ce_c).length - 0.5).coords)
    squeeze = lambda x, y: min(0.2 + 0.22 * np.clip((abs(x - 138.3) - 1.8) / 1.2, 0, 1),
                               0.2 + 0.22 * np.clip((abs(x - 146.0) - 0.8) / 1.0, 0, 1))  # thin between the Day Sq and Bellingham Sq names
    ce_l, ce_r = twin_rows(ce_c, squeeze)  # left: Chelsea bank, right: East Boston bank
    chelsea_path = np.vstack([ce_l, u_turn(ce_l[-1], ce_r[-1], (153, 149)), ce_r[::-1], u_turn(ce_r[0], ce_l[0], (126, 135))])
    rows = {"charles": (ch_l, ch_r), "mystic": (my_l, my_r), "chelsea": (ce_l, ce_r)}
    loop_paths = {"charles": charles_path, "mystic": [mystic_path], "chelsea": [chelsea_path]}
    left_bank = {"charles": set(FERRY_ROUTES[0]["stops"][FERRY_ROUTES[0]["stops"].index("Belmont Hill"):]), "mystic": {"Encore", "Stadium", "Admirals Hill", "Pearl St"},
                 "chelsea": {"Quigley", "Chelsea St", "Eastern Ave"}}
    for key, spots in LOOP_SPOTS.items():
        lrow, rrow = (LineString(v) for v in rows[key])
        for n, q in spots.items():
            row = lrow if n in left_bank[key] else rrow
            p = row.interpolate(row.project(Point(q)))
            at[n] = (p.x, p.y)
    for key, spots in LOOP_ENDS.items():
        whole = LineString(np.vstack(loop_paths[key]))
        for n, q in spots.items():
            p = whole.interpolate(whole.project(Point(q)))
            at[n] = (p.x, p.y)

    trunk = [(121.0, 98.0), (121.2, 92.6), (123.6, 91.2), (134.0, 91.0)]  # down the waterfront from Long Wharf, then east past South Station
    out_east = [(141.0, 87.6), (150.0, 84.4)]
    sb = [(163.0, 77.0), (167.0, 72.5), (166.2, 67.4), at["Castle Island"], (160.4, 63.4), (159.6, 62.7), at["M St"]]  # round South Boston
    sb_tail = by_hand([at["M St"], (157.3, 61.3), (156.0, 60.6), (151.5, 60.35), (149.0, 59.9), (147.6, 60.0), at["Carson Beach"]])  # under the Carson Beach name
    LF = at["Langone Ferryport"]
    up = [LF, (122.6, 114.2)] + CH[7::-1]  # hub up the channel to the junction off Lovejoy Wharf
    down = [LF, (121.7, 111.6), (122.4, 109.8), (121.7, 108.6), at["Sargent's Wharf"], (119.95, 105.7), at["Long Wharf"]]  # hub to Long Wharf
    out = lambda *legs: by_hand(down) + route([at["Long Wharf"]] + trunk + out_east + [q for leg in legs for q in leg])
    paths = {
        "charles": charles_path + by_hand(up), "mystic": [mystic_path] + by_hand([at["Navy Yard"]], NY, up[::-1]),
        "chelsea": [chelsea_path] + by_hand([(130.8, 135.2), (129.7, 135.0), at["Navy Yard"]], NY, up[::-1]),
        "hw": by_hand(up, LJ[::-1][1:]) + by_hand([LF, (121.7, 111.6), at["Battery Wharf"], (121.7, 108.6), at["Sargent's Wharf"],
                                                   (119.95, 105.7), at["Long Wharf"], at["Central Wharf"], at["Rowes Wharf"], (120.9, 92.0), at["Dorchester Ave"]]),
        "express": by_hand([at["Navy Yard"]], NY, up[::-1]) + by_hand(down),
        "eb": by_hand(up[:5], [at["Bennington St"], (124.75, 121.0), at["White St"]]) + by_hand([LF, (122.6, 111.4), K, (124.6, 109.3), (126.6, 109.0), at["Piers Park"]])
              + route([at["Piers Park"], (131.4, 104.4), at["Porzio"], (138.6, 102.4), (139.6, 98.6), at["Logan Dock"]]),
        "hi": out([(160.0, 79.0), at["Long Island"]]) + route([at["Long Island"], at["Georges Island"], at["Spectacle Island"], (172.0, 84.0), (175.0, 100.0), at["Deer Island"]]),
        "seaport": by_hand(down) + route([at["Long Wharf"], (121.0, 98.0), (121.2, 92.6), at["Martins Park"], (134.0, 91.0), (139.6, 88.0), at["Fan Pier"], at["Seaport"], at["Pavilion"]]),
        "ssi": out([at["First St"]]) + route([at["First St"]] + sb) + sb_tail + route([at["Carson Beach"], at["Dorchester Shores"], at["Old Harbor"], at["UMass Boston"], (148.0, 49.5), (144.0, 47.6), at["Fox Point"], at["Finigan"]]),
        "qb": out(sb) + sb_tail + route([at["Carson Beach"], at["UMass Boston"], at["Squantum Point"], at["Nickerson"], at["Thompson Island"], at["Moon Island"], at["Squantum"], at["Wollaston Beach"],
                     at["Hough's Neck"], at["Nut Island"]]),
        "fore": out(sb) + sb_tail + route([at["Carson Beach"], at["UMass Boston"], at["Squantum Point"], at["Quincy"], at["Bay Pointe"], at["King's Cove"], at["Wessagusset"], at["Hingham"], (155.4, 13.0), (155.6, 40.0), (155.4, 56.0),
                       (156.4, 61.6), (159.6, 62.7), (162.4, 62.7)])  # up the bay, past the Key, through the Castle Island gap
                + by_hand([(162.4, 62.7), (168.0, 62.1), (174.5, 62.8), (180.0, 62.5), at["Nantasket"], at["Hull"]]),  # along Hull's shore
        "nse": out([(162, 80), at["Winthrop Landing"], (176, 116), at["Winthrop Beach"], (180.0, 127.4), (177.6, 130.4), at["Highlands Beach"],
                    (177.6, 140.6), (171.0, 146.4), NSE_SUFFOLK, at["Beachmont"], (176.4, 147.4), (181.0, 150.0), (181.6, 156.6), at["Revere Beach"], (178.8, 162.6), at["Wonderland"], (186.0, 170.0), at["Lynn Harbor"],
                      at["Nahant Harbor"], at["Swampscott"], (212, 186.8), at["Clifton"], (218.5, 185.8), (221.6, 189), (221.6, 195.5), at["Marblehead"],
                      at["Salem Wharf"], at["Beverly"], (224.5, 210.5)]),
        "sse": out(sb) + sb_tail + route([at["Carson Beach"], at["UMass Boston"], at["Squantum Point"], at["Quincy"], at["Quincy Point"], at["Hingham"]]),
    }
    GLOUCESTER_OUT = (224.5, 210.5)  # out of Beverly Harbor, heading up the coast toward Cape Ann
    land, by_route = 0.0, {}
    for rt in FERRY_ROUTES:  # all wakes first, then all dots, so shared channels show alternating colors
        for xy in paths[rt["key"]]:
            ax.plot(*np.asarray(xy).T, color=WHITE, lw=(LOOP_LW + 2.2) if rt.get("loop") else 6.0, solid_capstyle="round", solid_joinstyle="round", zorder=2.6)
            off = LineString(xy).difference(wet).length
            land += off
            by_route[rt["key"]] = by_route.get(rt["key"], 0.0) + off
    if land > 0.3:
        print("  over land by route:", {k: round(v, 2) for k, v in by_route.items() if v > 0.02})
    for k, rt in enumerate(FERRY_ROUTES):
        for xy in paths[rt["key"]]:
            if rt.get("loop"):
                ax.plot(*np.asarray(xy).T, color=rt["color"], lw=LOOP_LW, ls=(0, (0.01, 2.0)), dash_capstyle="round", zorder=2.62, gid="ferry")
            else:
                ferry_track(ax, xy, rt["color"], z=2.62, casing=False, fast=rt.get("fast", False), phase=0.64 * (k % 3))
    print(f"ferry track over land: {land:.2f} units")
    cy = LineString(rounded([(140, 76), (149, 76), (152, 73), (152, 67), (149, 64), (122, 64)], 3))
    print(f"cyan southie in water: {cy.intersection(SEA.buffer(0)).length:.2f} units")

    # Stops: a small dot each. Docks that link to a station: white square, dot in the route color (black where routes meet), walking link.
    near = {**{n: xy for n, xy, *_ in CR_STOPS if n}, **PTS, **LINK_AT}  # docks can link to commuter stops too
    serves = {}
    for rt in FERRY_ROUTES:
        for n in rt["stops"]:
            serves.setdefault(n, []).append(rt["color"])
    for n, cols in serves.items():
        q = at[n]
        if n not in DOCKS:
            ferry_stop(ax, q)
            continue
        station = DOCKS[n][1]
        if station:
            if station in near:
                walk(ax, q, near[station], cut=box(115.0, 153.3, 123.2, 156.0) if station == "Encore" else None)
            else:
                print("dock station missing:", n, station)
        ax.scatter(*q, s=86 if n in HUB_DOCKS else 52, marker="s", color=WHITE, edgecolor=INK, lw=1.3 if n in HUB_DOCKS else 1.0, zorder=7.2)
        ax.scatter(*q, s=9, color=INK if len(set(cols)) > 1 else cols[0], zorder=7.3)
    ax.scatter(*NSE_SUFFOLK, s=52, marker="s", color=WHITE, edgecolor=INK, lw=1.0, zorder=7.2)
    ax.scatter(*NSE_SUFFOLK, s=9, color=ROUTE_COLOR["nse"], zorder=7.3)
    walk(ax, NSE_SUFFOLK, PTS["Suffolk Downs"])
    # The hub's name, beside its ring and dock, left of the Blue Line
    label(ax, (119.35, 119.3), "Langone\nFerryport", "r", gap=0, fs=7.4, weight="bold")
    for n, (_, _, side, gap, text) in DOCKS.items():
        if n in LABEL_AT:
            xy_, side_, text_ = LABEL_AT[n]
            label(ax, xy_, text_, side_, gap=0, fs=7.4, color=INK, halo=True)
        elif side:
            label(ax, at[n], text or n, side, gap=gap, fs=7.8 if n in HUB_DOCKS else 7.4, color=INK, halo=True,
                  weight="bold" if n in HUB_DOCKS else "normal")

    for n, (side, gap) in STOP_LABELS.items():
        label(ax, at[n], n, side, gap=gap, fs=7.4, color=INK, halo=True)

    def title(x, y, text, color, ha="right"):
        ax.text(x, y, text, fontsize=7.0, fontweight="bold", color=color, ha=ha, va="bottom", zorder=6.6,
                path_effects=[pe.withStroke(linewidth=2.4, foreground=WHITE)])

    title(188.0, 149.7, "NORTH SHORE FAST FERRY", "#6f7c00", ha="left")  # open water east of the route
    title(188.0, 147.5, "TO SALISBURY VIA GLOUCESTER, NEWBURYPORT", "#6f7c00", ha="left")
    title(188.0, 145.3, "HIGH-SPEED TRIPS: LANGONE, LYNN, SALEM", "#6f7c00", ha="left")
    title(147.0, 21.5, "SOUTH SHORE FAST FERRY", ROUTE_COLOR["sse"])
    title(147.0, 19.3, "ON TO CAPE COD & THE ISLANDS", ROUTE_COLOR["sse"])  # the full run is on the Ferry Map
    title(184, 77.6, "HARBOR ISLANDS FERRY", ROUTE_COLOR["hi"], ha="left")
    ferry_track(ax, [GLOUCESTER_OUT, (227.6, 212.2)], ROUTE_COLOR["nse"], z=2.62, casing=True, fast=True)
    ax.annotate("", xy=(229.2, 213.1), xytext=(227.3, 212.05),
                arrowprops=dict(arrowstyle="-|>,head_width=0.35,head_length=0.6", color=ROUTE_COLOR["nse"], lw=1.4), zorder=6.6)
    ax.text(228.8, 213.6, "TO SALISBURY", fontsize=7.0, fontweight="bold", color="#6f7c00", ha="right", va="bottom",
            zorder=6.6, path_effects=[pe.withStroke(linewidth=2.4, foreground=WHITE)])  # along the top edge, clear of the Salem docks
    for x_, y_ in WATERMARKS:  # Max's handle, very light, in open water
        ax.text(x_, y_, "@mapzimus", fontsize=6.0, color=WATERMARK, ha="center", va="center", zorder=1.5)
    ax.text(198, 67, "The Fast Ferry from Navy Yard follows\na crossing chartered in 1631", fontsize=7.4, color=ROUTE_COLOR["express"],
            ha="left", va="bottom", zorder=3)


def main():
    w = 18.0 * (XLIM[1] - XLIM[0]) / 268  # same scale as the 18-inch Day 8 sheet
    h = w * (YLIM[1] - YLIM[0]) / (XLIM[1] - XLIM[0])
    fig = plt.figure(figsize=(w, h), facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_facecolor(PAPER)
    ax.set_axis_off()
    for path in CR_PATHS:
        stroke(ax, rounded(path, 3), PURPLE, 3.1, "solid", z=3)
    # Peabody-Danvers line: leaves the Rockport line at South Salem and runs on to the Haverhill line at Lawrence.
    CR_LS = "-" if BUILT else (0, (2.2, 1.1))
    ax.plot(*rounded([(208.5, 198.5), (176, 198.5), (160, 214.5)], 3).T, color=PURPLE, lw=3.1, ls=CR_LS, dash_capstyle="butt", zorder=3)
    for spur in ([(208.5, 198.5), (214.5, 198.5)], [(-21, 143), (-24, 140), (-40, 140)],
                 [(50, -7), (78, -7)], [(34, -16), (46, -16)]):
        ax.plot(*rounded(spur, 3).T, color=PURPLE, lw=3.1, ls=CR_LS, dash_capstyle="butt", zorder=3)
    for (x0, y0), (x1, y1) in (((53, 211.2), (53, 215.2)), ((162.8, 211.7), (159.4, 215.1)), ((-41.2, 163.2), (-44, 166)), ((-40, 122), (-44, 122)), ((46, -17.6), (46, -19.8)), ((31.8, -15.2), (29, -18)),
                               ((121.6, -14), (121.6, -18)), ((143.2, -13.6), (146, -16.4)), ((114, 211.2), (114, 215.2)), ((212, 211.2), (212, 215.2))):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>,head_width=0.45,head_length=0.8", color=PURPLE, lw=0, shrinkA=0, shrinkB=0), zorder=3.3)
    label(ax, (207.6, 199.5), "South Salem", "tl", gap=0, fs=7.8, color=CR_TEXT_COLOR)  # above its stop
    label(ax, (215.6, 197.0), "Marblehead", "bl", gap=0, fs=7.8, color=CR_TEXT_COLOR)
    label(ax, (212.7, 199.5), "Clifton", "tr", gap=0, fs=7.8, color=CR_TEXT_COLOR)  # Max's stop, a Marblehead neighborhood  # under its stop, above the ferry dock
    for name, xy, side, st in CR_STOPS:
        ax.scatter(*xy, s=46, marker="s", color=PURPLE if st == "solid" or BUILT else WHITE, edgecolor=PURPLE, lw=1.4, zorder=6)
        if side:
            label(ax, xy, name, side, gap=2.2, fs=7.8, color=CR_TEXT_COLOR)
    ax.plot(*rounded([(53, 212.6), (53, 175), (88, 175), (114, 149), (114, 72), (108, 66), (76, 66), (46, 36), (46, -19.0)], 3).T, color=HSR, lw=1.3, zorder=3.2)
    ax.plot(*rounded([(114, 76), (114, 72), (108, 66), (82, 66), (26, 122), (-43.2, 122)], 3).T, color=HSR, lw=1.3, zorder=3.2)
    ax.plot(*rounded([(-43.4, 165.4), (-10, 132), (88, 132), (100, 120), (114, 120)], 3).T, color=HSR, lw=1.3, zorder=3.2)
    ax.plot(*rounded([(114, 139), (121, 146), (139, 146), (178, 185), (195, 185), (212, 202), (212, 212.6)], 3).T, color=HSR, lw=1.3, zorder=3.2)
    label(ax, (152.4, -8.9), "Greenbush", "b", gap=0, fs=7.8, color=CR_TEXT_COLOR)
    label(ax, (187.5, 198.5), "Danversport", "b", gap=1.6, fs=7.8, color=CR_TEXT_COLOR)
    label(ax, (212, 211.6), "Beverly", "br", gap=1.6, fs=7.8, color=CR_TEXT_COLOR)  # tucked by its stop, clear of the Salem dock
    label(ax, (131.3, 7.0), "East\nWeymouth", "br", gap=0, fs=7.8, color=CR_TEXT_COLOR)  # clear of the Kingston line
    label(ax, (45, -13.9), "Mansfield", "l", gap=0, fs=7.8, color=CR_TEXT_COLOR)
    label(ax, (35.4, -17.6), "Foxboro", "r", gap=0, fs=7.8, color=CR_TEXT_COLOR)
    label(ax, (47.6, -8.6), "Stoughton", "br", gap=0, fs=7.8, color=CR_TEXT_COLOR)
    label(ax, (212, 203.3), "Salem", "r", gap=2.2, fs=7.8, color=CR_TEXT_COLOR)  # a step down, clear of the Salem Wharf walking link
    global PTS
    pts = PTS = {}
    drawn = set(RINGS)

    def under_capsule(q):
        q = np.array(q, float)
        for a, b in CAPSULES:
            a, b = np.array(a, float), np.array(b, float)
            t = np.clip(np.dot(q - a, b - a) / np.dot(b - a, b - a), 0, 1)
            if np.hypot(*(q - (a + t * (b - a)))) < 1.7:
                return True
        return False
    for col, style, path, stops in lines():
        xy = rounded(path, 7 if "Terminals" in stops else CR)
        if BUILT:
            wide, style = (LW if col in (GREEN, YELLOW, CYAN) else LW * 1.14), "solid"
        else:
            wide = LW * 1.14 if style == "solid" and col != GREEN else (LW if style == "solid" or col in (YELLOW, CYAN) else LW * 0.8)
        stroke(ax, xy, col, wide, style, z=4.5 if col == YELLOW else 5)
        for s, p in place(xy, stops, {**A, **EXTRA}).items():
            if s in EXTRA:
                continue
            if s[-1] != "*":
                pts.setdefault(s, p)
            if s in drawn or under_capsule(p):
                continue
            drawn.add(s)
            ax.scatter(*p, s=(LW * 0.62) ** 2, color=WHITE, edgecolor=INK, lw=0.5, zorder=8)  # fine black edge on every dot
    for s, c in ENDS.items():
        if not under_capsule(pts[s]):
            stop(ax, pts[s], LW, True, edge=c)
    for s in RINGS:
        transfer(ax, pts[s], lw=LW)
    # The BIGGER Dig: heavy black bar with white dashes, stopping at the three stations.
    def four_tracks(x0, y0, x1, y1, z):
        """Black casing with four tracks: white local pair outside, gold express pair inside."""
        ax.plot([x0, x1], [y0, y1], color=INK, lw=LW * 1.8, zorder=z, solid_capstyle="round")
        vx, vy = (y1 - y0), -(x1 - x0)
        n = np.hypot(vx, vy)
        for off, col in ((-1.2, WHITE), (-0.42, HSR), (0.42, HSR), (1.2, WHITE)):
            dx, dy = vx / n * off, vy / n * off
            ax.plot([x0 + dx, x1 + dx], [y0 + dy, y1 + dy], color=col, lw=1.15, zorder=z + 0.1, solid_capstyle="butt")
    four_tracks(114, 120, 114, 76, 7)
    for a, b in CAPSULES:
        transfer(ax, a, b, lw=LW * (1.25 if a in BIG_CAPSULES else 1.05))
    ax.scatter(*pts["Airport"], s=(LW * 2.0) ** 2, color=WHITE, edgecolor=INK, lw=LW * 0.32, zorder=10)
    label(ax, (137.0, 121.6), "AIRPORT", "r", gap=0, fs=11.6, weight="bold")
    ax.scatter(*pts["West Station"], s=(LW * 2.0) ** 2, color=WHITE, edgecolor=INK, lw=LW * 0.32, zorder=10)
    label(ax, (62, 90), "WEST\nSTATION", "r", gap=0, fs=11.6, weight="bold")
    ax.scatter(*pts["Back Bay"], s=(LW * 2.0) ** 2, color=WHITE, edgecolor=INK, lw=LW * 0.32, zorder=10)
    label(ax, (pts["Back Bay"][0], pts["Back Bay"][1] + 7.5), "BACK BAY", "t", gap=0, fs=11.6, weight="bold")  # level, like WEST STATION, in the gap between the rail lines
    ax.scatter([114], [100], s=(LW * 2.8) ** 2, color=WHITE, edgecolor=INK, lw=LW * 0.36, zorder=9.8)
    ax.scatter([114], [100], s=(LW * 1.8) ** 2, color=RED, edgecolor=WHITE, lw=LW * 0.32, zorder=10)
    real_water(ax, pts)
    river_mouths(ax)
    ferries(ax)
    # Silver Line: a short airport shuttle, one line running both ways, from Logan Dock past every terminal to Airport
    stroke(ax, rounded([LOGAN, pts["Terminals"], (155.3, 111.3), (155.3, 116.7), (147, 125), (135, 125)], 2.4), SILVER, LW * 0.72, "solid" if BUILT else "dash", z=4.4)
    silver = [("A", (143.8, 99.8), -1.6, 1.8), ("B", (154.4, 117.6), 1.4, 2.0), ("C", (152.5, 119.5), 1.8, 1.8), ("D", (150.6, 121.4), 1.8, 1.8),
              ("E", (148.7, 123.3), 1.8, 1.8), ("F", (146.8, 124.6), 1.9, 1.9)]  # real order A, B, C, E; D came back and F is a joke
    for q in [LOGAN, (141.6, 97.7), (142.4, 125), (152, 108)] + [v[1] for v in silver]:
        ax.scatter(*q, s=(LW * 0.62) ** 2, color=WHITE, edgecolor=INK, lw=0.5, zorder=8)
    label(ax, (143.4, 125), "Rental Cars", "t", gap=1.3, fs=7.2)
    label(ax, (152, 108), "Parking", "tl", gap=1.5, fs=7.2)
    label(ax, (142.9, 96.7), "Office\nCenter", "r", gap=0, fs=7.2)
    for t, q, dx, dy in silver:
        ax.text(q[0] + dx, q[1] + dy, t, fontsize=8.8, fontweight="bold", color=INK, ha="center", va="center", zorder=11)
    for n, p in pts.items():
        s = SIDE.get(n, "r")
        if n in HIDE or s == "x":
            continue
        big = n in ENDS
        if big:
            t = n.upper().replace(" ", "\n", 1) if len(n) > 9 or n == "Hyde Park" else n.upper()
            label(ax, (p[0] + NUDGE.get(n, (0, 0))[0], p[1] + NUDGE.get(n, (0, 0))[1]), t, s, fs=10.4, weight="bold", gap=3.6)
        else:
            q = (p[0] + NUDGE.get(n, (0, 0))[0], p[1] + NUDGE.get(n, (0, 0))[1])
            label(ax, q, TEXT.get(n, n), s, fs=9.4, gap=2.3, halo=n in HALOED)
    for t, xy, ha in CR_TEXT:
        ax.text(*xy, t, fontsize=7.4, fontweight="bold", color=CR_TEXT_COLOR, ha=ha, va="bottom", zorder=12)
    # Downtown names sit by hand around the capsules.
    label(ax, (99.9, 86.2), "Downtown\nCrossing", "l", gap=0, fs=8.4, halo=True)  # no room for 9.4 between Green and Orange
    label(ax, (122, 98.2), "BOSTON\nCENTRAL", "r", gap=0, fs=16.5, weight="bold")
    label(ax, (110.6, 121.5), "NORTH\nSTATION", "t", gap=0, fs=11.6, weight="bold")  # above its pill, over the Orange Line (Max, November 7)
    label(ax, (120.6, 83.5), "SOUTH\nSTATION", "r", gap=0, fs=11.6, weight="bold")
    label(ax, (82.6, 57.4), "Nubian", "tl", gap=0, fs=9.4)  # above its own ring
    label(ax, (85.2, 51.8), "Mass & Cass\nTreatment\nCenter", "r", gap=0, fs=8.6, halo=True)  # Max's name for the Melnea Cass stop
    label(ax, (40.7, 27.0), "Forest Hills", "l", gap=0, fs=9.4)
    label(ax, (73.6, 54.6), "Ruggles", "br", gap=0, fs=9.4)  # level, right under its own ring
    label(ax, (104.2, 112), "Haymarket", "l", gap=0, fs=9.4)
    label(ax, (101.5, 96.6), "Gov\u2019t\nCenter", "r", gap=0, fs=9.4)
    label(ax, (60.0, 59.5), "Longwood\nMedical", "l", gap=0, fs=9.4)
    label(ax, (108.4, 152), "Sullivan Sq", "tl", gap=0, fs=9.4)
    label(ax, (88.9, 136.2), "Lechmere", "bl", gap=0, fs=8.8)  # clear of the Inman dash and the Yellow pair
    bullet(ax, -35.8, 175.2, "RL", RED)
    bullet(ax, 120, 202, "OL", ORANGE)
    bullet(ax, 182.5, 188.8, "BL", BLUE)
    bullet(ax, 153.0, 88, "YL", YELLOW, fg=INK)
    bullet(ax, 150.5, 113.6, "SL", SILVER)
    glpill(ax, 44.6, 176.4, "E")  # beside West Medford, off the Lowell Line
    bullet(ax, 116, 163.5, "CL", CYAN)
    label(ax, (115.3, 154.5), "Encore", "r", gap=0, fs=9.4, halo=True)  # halfway between the station and its dock
    bullet(ax, 66.5, 2.0, "IL", INDIGO)
    glpill(ax, -39.2, 53, "B")
    glpill(ax, -22.2, 43, "C")
    glpill(ax, -22.2, 10.4, "D")  # under WELLESLEY HILLS (two lines)
    bullet(ax, -30.6, 10.4, "CR", CR_TEXT_COLOR)  # Wellesley Hills is a Worcester Line station (Max, November 7)
    bullet(ax, -24.3, 58.0, "CR", CR_TEXT_COLOR)  # Auburndale is a Worcester Line station too (MBTA stop data); across the line from its name
    glpill(ax, -28, 111.5, "A")  # Watertown: the real A branch, closed 1969
    glpill(ax, 71, 136, "D")  # Union Sq: real D service today
    glpill(ax, 18.5, 12.6, "N")  # Needham: invented letter
    glpill(ax, 23.5, 36.6, "E")  # Forest Hills leg of the E, level with Heath St where the leg starts (Max, November 7)
    # Title.
    UP = 5.4  # title block sits higher on the wider sheet, leaving room for the NERTA mark
    tx, ty, tr = -36, 198.4 + UP, 7.6  # roundel: heavy ring, NERTA's three-layer T (Max, November 7)
    ax.add_patch(Circle((tx, ty), tr, fc=WHITE, ec=INK, lw=4.5, zorder=12))
    NERTA_COLORS = (RED, ORANGE, YELLOW, BLUE, ROUTE_COLOR["inner-harbor"], CYAN, SILVER, HSR, INDIGO, CR_TEXT_COLOR, GREEN)
    draw_t(ax, tx, ty, tr, NERTA_COLORS)  # Max's order: Red, Orange, Yellow, Blue, ferry teal, Cyan, Silver, high-speed gold, Indigo, commuter rail purple, tram (Green)
    ro = tr + 4.5 / 4.836 / 2  # outer edge of the ring
    nb = draw_nerta(ax, tx, ty - ro - 1.0, 2 * ro, "B", colors=NERTA_COLORS)  # NERTA wordmark, slotted under the T
    if WEB:
        ax.text(tx, nb - 1.0, "Maxwell Howe", fontsize=11, color=INK, ha="center", va="top", zorder=12)
        ax.text(205, 124, "@mapzimus", fontsize=13, fontweight="bold", color=COAST, ha="center", va="center", zorder=2.9)  # watermark, open water east of Deer Island
    # Title block, matched to Max's Illustrator layout
    ax.text(-25.5, 200.87 + UP, "Boston\u2019s", fontsize=34, fontweight="bold", color=INK, va="baseline", zorder=12)
    bold = FontProperties(family="Arial", weight="bold")
    tw = TextPath((0, 0), "Rapid T", size=34, prop=bold).get_extents().x1 / 4.836
    ax.text(-25.5, 192.43 + UP, "Rapid T", fontsize=34, fontweight="bold", color=INK, va="baseline", zorder=12)
    ax.text(-25.5 + tw - 0.054 * 34 / 4.836 + 0.15, 192.43 + UP, "ransit", fontsize=34, fontweight="bold", color=INK, va="baseline", zorder=12)
    for t, y in () if WEB else (("Map: Maxwell Howe", 188.04), ("#30DayMapChallenge", 185.17), ("Day 8 \u2022 Utopia", 182.3)):  # tag kept for the release (Max)
        ax.text(-43.72, y, t, fontsize=11, color=INK, va="baseline", zorder=12)
    narrow = FontProperties(fname=r"C:\Windows\Fonts\ARIALNI.TTF")
    narrow_bold = FontProperties(fname=r"C:\Windows\Fonts\ARIALNBI.TTF")
    for k, t in enumerate(() if WEB else ("This is a futuristic concept map", "and is not affiliated with the MBTA", "in any way. MOST of the map decisions",
                           "are grounded in real data & studies,", "proposals made, or projections for", "future projects or development.")):
        yk, x = 188.5 + UP - k * 2.978, -18.75
        for part in t.replace("MOST", "|MOST|").split("|"):  # MOST in bold (Max, November 7)
            fp = narrow_bold if part == "MOST" else narrow
            ax.text(x, yk, part, fontproperties=fp, fontsize=12, color="#000000", va="baseline", zorder=12)
            x += TextPath((0, 0), part, size=12, prop=fp).get_extents().x1 / 4.836  # ink end of this part
            if part.endswith(" "):  # the ink width leaves out the trailing space, so add one space's advance (12 pt Arial Narrow)
                x += 0.62
    # Callout in the harbor, and the Key: one type system. Headings 11 bold, body 9.6, captions 7.6.
    DX, DY = 193.6, 144.0  # the Dig panel's top left, in open sea east of the harbor (Max: moved northeast, November 7)
    for x0, y0, w_, h_ in ((DX, DY - 64.0, 35.4, 64.0), (157, -15.2, 62, 75.0)):  # Key grew 6 units up for the ferry rows
        ax.add_patch(FancyBboxPatch((x0, y0), w_, h_, boxstyle="round,pad=0,rounding_size=1.2", fc=WHITE, ec=INK, lw=1.0, zorder=11))
    tx_ = DX + 2.2
    ax.text(tx_, DY - 2.0, "The BIGGER Dig", fontsize=17, fontweight="bold", color=RED, zorder=12, va="top")
    ax.text(tx_, DY - 6.8, chr(10).join(("Four tracks under Atlantic Ave join", "North and South Stations through", "Boston Central. Every commuter rail",
                                          "line runs straight through: Lowell to", "Providence is one seat. Underground",
                                          "walkways reach Downtown Crossing", "and Park St.")), fontsize=7.4, color=INK, zorder=12, va="top", linespacing=1.2)
    ax.plot([tx_, DX + 33.2], [DY - 19.0, DY - 19.0], color=INK, lw=0.7, zorder=12)
    rapid = len({c for c, *_ in lines()}) + 1  # the Silver Line is drawn on its own
    cr_lines = sum(" LINE" in t for t, *_ in CR_TEXT)
    for k, (big, small) in enumerate(((str(rapid), "Rapid transit lines"), ("224", "T stops"), (str(cr_lines), "Commuter rail lines"),
                                      (str(len(FERRY_ROUTES)), "Ferry routes"), ("5×", "The Big Dig's cost"), ("~140", "New miles"))):
        x_, y_ = tx_ + (k % 2) * 15.6, DY - 20.0 - (k // 2) * 5.8
        ax.text(x_, y_, big, fontsize=12.0, fontweight="bold", color=INK, zorder=12, va="top")
        ax.text(x_, y_ - 3.2, small, fontsize=7.4, color=INK, zorder=12, va="top")
    ax.plot([tx_, DX + 33.2], [DY - 38.0, DY - 38.0], color=INK, lw=0.7, zorder=12)
    # Cost, all in 2026 dollars. One scale: 30.6 diagram units = $125B.
    ax.text(tx_, DY - 39.0, "~$125B", fontsize=15, fontweight="bold", color=RED, zorder=12, va="top")
    ax.text(tx_ + 14.0, DY - 41.0, "Whole map, rough estimate", fontsize=7.0, color=INK, zorder=12, va="top")
    u = 30.6 / 125
    x_ = tx_
    for k, (wide_, c_, t_) in enumerate(((20, INK, "Tunnel $20B"), (38, CR_TEXT_COLOR, "Regional rail $38B"), (67, RED, "New subway lines $67B"))):
        ax.add_patch(FancyBboxPatch((x_, DY - 45.6), wide_ * u - 0.25, 2.3, boxstyle="square,pad=0", fc=c_, ec="none", zorder=12))
        ax.add_patch(FancyBboxPatch((tx_, DY - 48.6 - k * 2.4), 1.6, 1.6, boxstyle="square,pad=0", fc=c_, ec="none", zorder=12))
        ax.text(tx_ + 2.4, DY - 47.8 - k * 2.4, t_, fontsize=7.2, color=INK, zorder=12, va="center")
        x_ += wide_ * u
    ax.add_patch(FancyBboxPatch((tx_, DY - 56.6), 24 * u, 1.6, boxstyle="square,pad=0", fc="#9a9a9e", ec="none", zorder=12))
    ax.text(tx_ + 24 * u + 0.8, DY - 55.8, "Original Big Dig, $24B", fontsize=7.2, color=INK, zorder=12, va="center")
    ax.text(tx_, DY - 59.0, "All figures in 2026 dollars.", fontsize=7.2, color=INK, zorder=12, va="center")
    ax.text(tx_, DY - 61.6, "Driverless maglev, 24 hours a day.", fontsize=7.4, fontweight="bold", color=INK, zorder=12, va="center")
    # Key, for riders, like a transit authority's: lines, regional rail and ferries, stations.
    lx, tx, ly, step = 160.5, 174.5, 56.0, 3.0
    y = ly
    ax.text(lx, y, "Key", fontsize=11, fontweight="bold", color=INK, va="center", zorder=12)

    def row(text, y_):
        ax.text(tx, y_, text, fontsize=9.6, va="center", color=INK, zorder=12)

    def heading(text, y_):
        ax.text(lx, y_, text, fontsize=9.6, fontweight="bold", color=INK, va="center", zorder=12)

    y -= 3.8
    heading("Lines", y)
    y -= step
    for pair in (((RED, "RL", "Red Line"), (ORANGE, "OL", "Orange Line")), ((BLUE, "BL", "Blue Line"), (GREEN, "GL", "Green Line")),
                 ((YELLOW, "YL", "Yellow Line"), (CYAN, "CL", "Cyan Line")), ((INDIGO, "IL", "Indigo Line"), (SILVER, "SL", "Silver Line"))):
        for k, (c_, code, t_) in enumerate(pair):
            x_ = lx + k * 27.0
            ax.add_patch(FancyBboxPatch((x_ + 1.2, y - 1.0), 6.6, 2.0, boxstyle="round,pad=0,rounding_size=1.0", fc=c_, ec="none", zorder=12))
            ax.text(x_ + 4.5, y - 0.05, code, fontsize=8.4, fontweight="bold", color=INK if c_ == YELLOW else WHITE, ha="center", va="center", zorder=12.1)
            ax.text(x_ + 9.4, y, t_, fontsize=9.6, va="center", color=INK, zorder=12)
        y -= step
    y -= 0.8
    heading("Regional rail and ferries", y)
    y -= step
    stroke(ax, [(lx, y), (lx + 11, y)], PURPLE, 3.1, "solid", z=12)
    row("Commuter Rail", y)
    y -= step
    stroke(ax, [(lx, y), (lx + 11, y)], PURPLE, 3.1, "solid", z=12)
    ax.plot([lx, lx + 11], [y, y], color=HSR, lw=1.3, zorder=12.2)
    row("High-Speed Rail, major stations only", y)
    y -= step
    four_tracks(lx + 0.6, y, lx + 10.4, y, 12)
    row("North-South Rail Link, four tracks", y)
    y -= step
    # Ferries by family, drawn as on the map: purple river loops, harbor and bay boats, express streaks (Max, November 7)
    fam = {r["key"]: r["color"] for r in FERRY_ROUTES}
    for k, key in enumerate(("charles", "mystic", "chelsea")):
        x0_, x1_ = lx + 0.6 + k * 3.7, lx + 2.9 + k * 3.7
        loop_ = np.vstack([[(x0_, y + LOOP_GAP), (x1_, y + LOOP_GAP)], u_turn((x1_, y + LOOP_GAP), (x1_, y - LOOP_GAP), (x1_ + 1, y)),
                           [(x1_, y - LOOP_GAP), (x0_, y - LOOP_GAP)], u_turn((x0_, y - LOOP_GAP), (x0_, y + LOOP_GAP), (x0_ - 1, y))])
        ax.plot(*loop_.T, color=fam[key], lw=LOOP_LW, ls=(0, (0.01, 2.0)), dash_capstyle="round", zorder=12)
    row("River ferry, loops along both banks", y)
    y -= step
    for k, key in enumerate(("hw", "hi", "ssi")):
        ferry_track(ax, [(lx + 0.3 + k * 4.0, y), (lx + 1.75 + k * 4.0, y)], fam[key], z=12, casing=False)
    row("Harbor and bay ferry", y)
    y -= step
    for k, key in enumerate(("nse", "sse")):
        ferry_track(ax, [(lx + k * 6.0, y), (lx + 4.6 + k * 6.0, y)], fam[key], z=12, casing=False, fast=True)
    row("Fast Ferry (FF): North and South Shore", y)
    y -= step
    ferry_track(ax, [(lx + 0.3, y), (lx + 10.4, y)], fam["hw"], z=12, casing=False)
    ferry_stop(ax, (lx + 5.4, y), z=12.2)
    row("Ferry stop. Names on the Ferry Map", y)
    y -= step
    ax.scatter([lx + 2.0], [y], s=52, marker="s", color=WHITE, edgecolor=INK, lw=1.0, zorder=12.1)
    ax.scatter([lx + 2.0], [y], s=9, color=INK, zorder=12.2)
    ax.plot([lx + 2.9, lx + 9.5], [y, y], color=INK, lw=1.0, ls=(0, (0.01, 1.6)), dash_capstyle="round", zorder=12)
    ax.scatter([lx + 9.8], [y], s=(LW * 0.62) ** 2, color=WHITE, edgecolor=INK, lw=0.5, zorder=12.1)
    row("Ferry dock, short walk to station", y)
    y -= step
    y -= 0.8
    heading("Stations", y)
    y -= step + 0.3
    ax.scatter([lx + 5.5], [y], s=(LW * 1.5) ** 2, color=WHITE, edgecolor=INK, lw=2.4, zorder=12)
    ax.scatter([lx + 5.5], [y], s=(LW * 0.85) ** 2, color=RED, zorder=12.1)
    row("Boston Central, the hub", y)
    y -= step + 0.2
    ax.scatter([lx + 5.5], [y], s=(LW * 1.2) ** 2, color=WHITE, edgecolor=INK, lw=2.2, zorder=12)
    row("Major station", y)
    y -= step
    stroke(ax, [(lx + 0.3, y), (lx + 10.7, y)], RED, LW * 0.8, "solid", z=12)
    ax.scatter([lx + 3.0], [y], s=(LW * 0.62) ** 2, color=WHITE, edgecolor=INK, lw=0.5, zorder=12.1)
    transfer(ax, (lx + 8.0, y), lw=LW, z=12.1)
    row("Station, transfer station", y)
    y -= step
    ax.scatter([lx + 5.5], [y], s=46, marker="s", color=PURPLE, zorder=12)
    row("Commuter Rail station", y)
    y -= step
    icon(ax, lx + 5.5, y)
    row("Every station is accessible", y)
    y -= 2.6
    ax.text(tx, y, "Driverless maglev, 24 hours a day", fontsize=7.6, va="center", color=INK, zorder=12)
    y -= 2.6
    ax.text(tx, y, "Replacement shuttle buses: none", fontsize=7.6, va="center", color=INK, zorder=12)
    ax.text(219, -17.8, "Map not to scale. Pods on demand at every station." if WEB else "Map not to scale. Pods on demand at every station. Map data: MBTA. Coastline: US Census.",
            fontsize=7.2, color=INK, ha="right", va="top", zorder=12)
    (DAY / "output").mkdir(exist_ok=True)
    fig.savefig(DAY / "output/t_map.png", dpi=200, facecolor=PAPER)
    fig.savefig(DAY / "output/t_map.pdf", facecolor=PAPER)
    print("written")


if __name__ == "__main__":
    main()
