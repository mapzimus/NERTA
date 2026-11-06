"""Day 8 Boston metro map: the T wall poster, with the extensions and The BIGGER Dig.

python days/08-utopia/src/make_tmap.py
Stop order for today's lines comes from the MBTA V3 data (data/mbta_stops.gpkg). Positions are schematic, set by hand
on a 45-degree grid. Fan map, no official logo. Silver Line and buses left off.
"""
from pathlib import Path
import geopandas as gpd
import csv
import matplotlib.pyplot as plt
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
from shapely.ops import unary_union
from station_kit import INK, WHITE, bullet, label, place, rounded, smooth_closed, smooth_open, stop, stroke, transfer

DAY = Path(__file__).resolve().parents[1]
REPO = DAY.parent
RED, ORANGE, BLUE, GREEN, YELLOW, PURPLE = "#da291c", "#ed8b00", "#003da5", "#00843d", "#f5c400", "#a98aa8"
CR_TEXT_COLOR = "#80276c"
CYAN, INDIGO = "#00a9c9", "#3f3fb5"
PAPER, WATER, COAST = "#fcfcfa", "#c9e3ee", "#7fb2c6"
LW, CR = 9.0, 3.4
HSR = "#ffd23f"
SILVER = "#7c878e"
XLIM, YLIM = (-46, 222), (-20, 208)

# Spots shared between lines, or that fix the shape of a line.
CR_STOPS = [("River Works", (172, 179), "tl", "solid"), ("Swampscott", (204, 194), "br", "solid"), ("Marblehead", (220, 193.5), "l", "dash"), ("Woburn", (66, 201), "t", "dash"), ("Burlington", (80, 201), "r", "dash"),
            ("South Salem", (208.5, 198.5), None, "stripe"), ("Salem", (212, 203.8), "r", "solid"), ("Peabody", (194, 198.5), "b", "dash"), ("Danvers", (181, 198.5), "b", "dash"),
            ("Boston Landing", (15, 122), "t", "solid"), ("David Ortiz", (61.7, 86.3), "r", "solid"),
            
            ("", (46, 14), None, "solid"), ("Walpole", (34, -13), "l", "solid"), ("Foxborough", (34, -16), None, "solid"), ("Stoughton", (50, -7), None, "solid"),
            ("Newtonville", (6, 122), "b", "solid"), ("West Newton", (-3.5, 122), "b", "solid"), ("Wellesley", (-30, 122), "b", "solid"), ("Concord", (-15, 137), "l", "solid"), ("S. Acton", (-21, 143), "r", "solid"), ("Ayer", (-38, 160), "r", "solid"), ("Winchester", (53, 184), "r", "solid"), ("Anderson", (53, 189), "l", "solid"), ("Wilmington", (53, 194), "l", "solid"), ("Endicott", (43.5, -3.5), "l", "solid"), ("Norwood", (39.5, -7.5), "l", "solid"), ("Brockton", (121.6, -2), "r", "solid"), ("Bridgewater", (121.6, -8), "r", "solid"), ("Abington", (127.6, 2), "r", "solid"), ("Hanson", (133, -3.4), "r", "solid"), ("Kingston", (138.4, -8.8), "r", "solid"), ("East Weymouth", (130, 8), "b", "solid"), ("Hingham", (142, 4), "r", "solid"), ("Cohasset", (146.5, -0.5), "r", "solid"), ("Hudson", (-29, 140), "b", "dash"), ("Marlborough", (-40, 140), "b", "dash"), ("Mansfield", (46, -16), None, "dash"), ("North Easton", (57, -7), "b", "dash"), ("Easton Village", (64, -7), "t", "dash"), ("Raynham Place", (71, -7), "b", "dash"), ("Taunton", (78, -7), "t", "dash")]

A = {"Alewife": (44, 146), "Weymouth": (118, -7), "Bellingham Sq": (135, 137), "Wyoma Sq": (188, 192), "East Saugus": (160.5, 174), "Brighton Center": (20, 111), "Allston": (38, 111), "West Medford": (53, 175), "Eliot": (8, 38), "Porter": (58, 132), "Harvard": (66, 124), "Kendall/MIT": (80, 110),
     "Charles/MGH": (90, 100), "Park Street": (96, 94), "Downtown Crossing": (103, 87), "South Station": (114, 76),
     "JFK/UMass": (118, 52), "Ashmont": (94, 26), "Braintree": (118, 8), "Arlington Heights": (20, 170),
     "Inner Belt": (94, 142), "Oak Grove": (110, 182), "Malden Center": (110, 174), "Saugus Center": (152, 174), "Lynn Common": (195, 188), "Reading": (110, 202), "Assembly": (110, 157), "Sullivan Sq": (110, 150), "Community College": (110, 136), "North Station": (110, 120),
     "Haymarket": (110, 112), "State": (110, 100), "Back Bay": (82, 66), "Ruggles": (72, 56), "Broadway": (118, 64), "Andrew": (118, 58), "Forest Hills": (43, 27), "VFW Parkway": (12, -4),
     "Bowdoin": (96, 100), "Gov't Center": (102, 100), "Airport": (135, 125), "Encore": (121, 150), "Mass Ave": (70, 100), "Mattapan": (94, -10), "Dedham": (-2, -16), "Lexington Route 128": (-30, 170), "Waltham": (-30, 146), "Watertown": (-30, 106), "Wonderland": (176, 166), "Lynn Harbor": (188, 178), "Lynn": (195, 185),
     "Medford/Tufts": (63, 165), "Lechmere": (90, 138), "Union Sq": (76, 138), "Boylston": (90, 88), "Arlington": (81, 84),
     "Copley": (75, 84), "Hynes": (59, 84), "Kenmore": (54, 84), "Fenway": (46, 76), "Longwood Medical Area": (59, 56), "Prudential": (69, 75), "Symphony": (69, 69), "Blandford St": (39, 89), "St. Mary's St": (39, 84),
     "Riverside": (-8, 22), "Harvard Ave": (20, 108), "Boston College": (-22, 66), "Norumbega": (-40, 92), "Newton City Hall": (-40, 84), "Cleveland Circle": (-14, 48),
     "Newton Highlands": (12, 42), "Heath St": (40, 37), "Hyde Sq": (40, 32), "Hyde Park": (43, 14), "Nubian": (92, 56), "Tufts Medical Ctr": (92, 76), "Dover": (92, 71), "Northampton": (92, 65.5), "Four Corners": (92, 48), "Grove Hall": (82, 22), "Seaver St": (82, 11), "Wellington Hill": (82, 0), "Melnea Cass": (84, 56), "Inman Sq": (69, 138), "Auburndale": (-20, 10), "BU Bridge": (66, 96), "West Station": (59, 89), "Barrys Corner": (52, 110), "Lansdowne": (59, 89),
     "Terminals": (148, 104), "Newmarket": (100, 56), "Broadway": (118, 64), "Readville": (46, 2), "Winthrop Center": (164, 124), "Orient Heights": (149, 139), "Maverick": (129, 119), "City Point": (152, 70), "Convention Center": (130, 64), "L Street": (145, 64), "West Broadway": (124, 64), "Boston Central": (118, 100), "Aquarium": (118, 108), "North End": (118, 114), "City Square": (122, 132), "Navy Yard": (124, 135), "Thompson Sq": (124, 141), "Stadium": (124, 150), "Encore": (116, 157), "Everett Sq": (130, 150), "Chelsea": (135, 150), "Fort Point": (125, 76), "Uphams Corner": (96, 52), "Bellingham Sq": (135, 141), "Talbot Ave": (79, 35), "Morton St": (71, 27), "Blue Hill Ave": (60, 16), "Fairmount": (50.5, 6.5),  "Mass. Ave": (79.5, 63.5), "Northeastern": (69, 65), "Seaport": (140, 76), "Courthouse": (133, 76)}


def lines():
    """Each entry: color, style, path, stops. Styles: solid today, stripe real proposal, dash imagined."""
    x = []
    x += [(RED, "stripe", [(118, 8), (118, -7)], ["Braintree", "Weymouth"])]
    x += [(RED, "stripe", [(20, 170), (44, 146)], ["Arlington Heights", "Arlington Ctr", "East Arlington", "Alewife"]),
          (RED, "dash", [(-30, 170), (-30, 146)], ["Lexington Route 128", "Trapelo Rd", "Waltham"]),
          (RED, "stripe", [(20, 170), (-30, 170)], ["Arlington Heights", "Lexington Ctr", "Lexington Route 128"]),
          (RED, "stripe", [(44, 146), (-30, 146)], ["Alewife", "Belmont Ctr", "Waverley Sq", "Waltham"]),
          (RED, "solid", [(44, 146), (118, 72), (118, 52)], ["Alewife", "North Cambridge", "Davis", "Porter", "Harvard", "Central", "Kendall/MIT", "Charles/MGH", "Park Street",
                                                             "Downtown Crossing", "South Station", "Broadway", "Andrew", "JFK/UMass"]),
          (RED, "solid", [(118, 52), (94, 28), (94, 26)], ["JFK/UMass", "Savin Hill", "Fields Corner", "Shawmut", "Ashmont"]),
          (RED, "solid", [(118, 52), (118, 8)], ["JFK/UMass", "North Quincy", "Wollaston", "Quincy Center", "Quincy Adams", "Braintree"]),
          (RED, "solid", [(94, 26), (94, -10)], ["Ashmont", "Cedar Grove", "Butler", "Milton", "Central Ave", "Valley Rd", "Capen St", "Mattapan"])]
    x += [(ORANGE, "solid", [(110, 182), (110, 94), (43, 27)],
           ["Oak Grove", "Malden Center", "Wellington", "Assembly", "Sullivan Sq", "Community College", "North Station", "Haymarket", "State",
            "Downtown Crossing", "Chinatown", "Tufts Medical Ctr", "Back Bay", "Mass. Ave", "Ruggles", "Roxbury Crossing", "Jackson Sq",
            "Stony Brook", "Green St", "Forest Hills"]),
          (ORANGE, "dash", [(92, 76), (92, 40), (82, 30), (82, -6), (86, -10), (94, -10)],
           ["Tufts Medical Ctr", "Dover", "Northampton", "Nubian", "Four Corners", "Grove Hall", "Seaver St", "Wellington Hill", "Mattapan"]),
          (ORANGE, "dash", [(110, 202), (110, 182)], ["Reading", "Wakefield", "Greenwood", "Melrose Highlands", "Wyoming Hill", "Oak Grove"]),
          (ORANGE, "dash", [(110, 174), (168, 174), (176, 166)], ["Malden Center", "Linden Sq", "Cliftondale", "Saugus Center", "Wonderland"]),
          (ORANGE, "stripe", [(43, 27), (43, 6), (46, 2)], ["Forest Hills", "Hyde Park", "Readville"]),
          (ORANGE, "stripe", [(43, 27), (12, -4)], ["Forest Hills", "Roslindale Village", "Bellevue", "Highland", "West Roxbury", "VFW Parkway"])]
    x += [(INDIGO, "stripe", [(114, 76), (114, 70), (110, 66), (46, 2)], ["South Station", "Newmarket", "Uphams Corner", "Four Corners", "Talbot Ave", "Morton St", "Blue Hill Ave", "Fairmount", "Readville"])]
    x += [(CYAN, "dash", [(140, 76), (122, 76), (118, 80), (118, 128), (124, 134), (124, 157), (110, 157)],
           ["Seaport", "Courthouse", "Fort Point", "Boston Central", "Aquarium", "North End", "North Station", "City Square", "Navy Yard", "Thompson Sq", "Stadium", "Encore", "Assembly"])]
    x += [(CYAN, "dash", [(140, 76), (149, 76), (152, 73), (152, 67), (149, 64), (122, 64), (118, 64)],
           ["Seaport", "City Point", "L Street", "Convention Center", "West Broadway", "Broadway"])]
    x += [(BLUE, "solid", [(102, 100), (114, 100), (118, 108), (176, 166)], ["Gov't Center", "State", "Aquarium", "Maverick", "Airport", "Wood Island",
                                                                "Orient Heights", "Suffolk Downs", "Beachmont", "Revere Beach", "Wonderland"]),
          (BLUE, "stripe", [(90, 100), (102, 100)], ["Charles/MGH", "Gov't Center"]),
          (BLUE, "dash", [(90, 100), (64, 100), (59, 95), (59, 89)], ["Charles/MGH", "Mass Ave", "West Station"]),
          (BLUE, "dash", [(149, 139), (164, 124)], ["Orient Heights", "Winthrop Center"]),
          (BLUE, "stripe", [(176, 166), (195, 185)], ["Wonderland", "Lynn Harbor", "Lynn"]),
          (BLUE, "dash", [(195, 185), (188, 192)], ["Lynn", "Wyoma Sq"])]
    x += [(GREEN, "solid", [(90, 138), (106, 122), (106, 104), (102, 100), (86, 84), (54, 84)],
           ["Lechmere", "Science Park", "North Station", "Haymarket", "Gov't Center", "Park Street", "Boylston", "Arlington", "Copley", "Hynes", "Kenmore"]),
          (GREEN, "solid", [(63, 165), (90, 138)], ["Medford/Tufts", "Ball Sq", "Magoun Sq", "Gilman Sq", "East Somerville", "Lechmere"]),
          (GREEN, "stripe", [(53, 175), (63, 165)], ["West Medford", "Medford Hillside", "Medford/Tufts"]),
          (GREEN, "solid", [(59, 89), (59, 84)], ["West Station", "Hynes"]),
          (GREEN, "stripe", [(59, 89), (56, 89), (50, 95), (50, 111), (-25, 111), (-30, 106)], ["West Station", "Allston", "Brighton Center", "Oak Sq", "Newton Corner", "Watertown"]),
          (GREEN, "solid", [(76, 138), (90, 138)], ["Union Sq", "Lechmere"]),
          (GREEN, "dash", [(66, 124), (66, 138), (76, 138)], ["Harvard", "Inman Sq", "Union Sq"]),
          (GREEN, "solid", [(54, 84), (44, 84), (20, 108), (-22, 66)],
           ["Kenmore", "Blandford St", "BU East", "BU Central", "Amory St", "Babcock St", "Packard's Corner", "Harvard Ave", "Griggs St", "Allston St",
            "Warren St", "Washington St", "Sutherland Rd", "Chiswick Rd", "Chestnut Hill Ave", "South St", "Boston College"]),
          (GREEN, "solid", [(44, 84), (36, 84), (29, 91), (-14, 48)],
           ["St. Mary's St", "Hawes St", "Kent St", "St. Paul St", "Coolidge Corner", "Summit Ave", "Brandon Hall", "Fairbanks St",
            "Washington Sq", "Tappan St", "Dean Rd", "Englewood Ave", "Cleveland Circle"]),
          (GREEN, "solid", [(54, 84), (-8, 22)], ["Kenmore", "Fenway", "Longwood", "Brookline Village", "Brookline Hills", "Beaconsfield", "Reservoir",
                                                  "Chestnut Hill", "Newton Centre", "Newton Highlands", "Eliot", "Waban", "Woodland", "Riverside"]),
          (GREEN, "solid", [(69, 84), (69, 66), (40, 37)], ["Prudential", "Symphony", "Northeastern", "Museum of Fine Arts", "Longwood Medical Area", "Brigham Circle",
                                                            "Fenwood Rd", "Mission Park", "Riverway", "Back of the Hill", "Heath St"]),
          (GREEN, "stripe", [(40, 37), (40, 32)], ["Heath St", "Hyde Sq"]),
          (GREEN, "stripe", [(40, 32), (40, 30), (43, 27)], ["Hyde Sq", "Forest Hills"]),
          (GREEN, "stripe", [(8, 38), (8, 2), (12, -4)], ["Eliot", "Needham Heights", "Needham Junction", "Hersey", "VFW Parkway"])]
    # Yellow, the Urban Ring. Grand Junction section striped, the rest dashed.
    x += [(YELLOW, "dash", [(148, 104), (148, 105), (135, 118), (135, 137)], ["Terminals", "Airport", "Bellingham Sq"]),
          (YELLOW, "dash", [(135, 137), (135, 150), (102, 150), (90, 138)],
           ["Bellingham Sq", "Chelsea", "Everett Sq", "Stadium", "Sullivan Sq", "Inner Belt", "Lechmere"]),
          (YELLOW, "dash", [(140, 76), (148, 84), (148, 104)], ["Seaport", "Terminals"]),
          (YELLOW, "stripe", [(90, 138), (90, 120), (59, 89)], ["Lechmere", "Binney", "Kendall/MIT", "Mass Ave", "BU Bridge", "West Station"]),
          (YELLOW, "dash", [(59, 89), (54, 84), (50, 80), (50, 56), (114, 56), (118, 52)],
           ["West Station", "Kenmore", "Fenway+", "Longwood Medical Area", "Ruggles", "Melnea Cass", "Nubian", "Newmarket", "Boston Medical", "JFK/UMass"]),
          (YELLOW, "dash", [(118, 52), (140, 74), (140, 76)], ["JFK/UMass", "Convention Center", "Seaport"])]
    return x


EXTRA = {"Sullivan Sq+": (102, 150), "Fenway+": (50, 76), "South Station+": (114, 78.5)}

# Commuter rail, thin purple. All of it now runs through the tunnel, so no line ends downtown.
CR_PATHS = [
    [(114, 120), (114, 149)],                                      # trunk to the Sullivan superstation
    [(-44, 166), (-10, 132), (88, 132), (100, 120), (114, 120)],               # Fitchburg
    [(53, 206), (53, 175), (88, 175), (114, 149)],                 # Lowell and Haverhill, via the Wildcat
    [(114, 139), (121, 146), (139, 146), (178, 185), (195, 185), (212, 202), (212, 208)],  # Newburyport, Rockport
    [(114, 76), (114, 72), (108, 66), (82, 66), (26, 122), (-44, 122)],  # Worcester
    [(82, 66), (76, 66), (46, 36), (46, -19.6)],                     # Providence
    [(46, -1), (34, -13), (29, -18)],                              # Franklin, leaves at Readville
    [(34, -13), (34, -16)],                                        # Foxborough, leaves Franklin at Walpole
    [(114, 72), (120, 72), (121.6, 70.4), (121.6, -18)],                 # Fall River, New Bedford
    [(121.6, 8), (146, -16.4)],                                    # Kingston, Plymouth, Cape Cod
    [(121.6, 8), (138, 8), (152, -6)],                             # Greenbush
    [(46, -3), (50, -7)],                                          # Stoughton
    [(53, 198), (58, 203), (58, 208)],                             # Haverhill
]
CR_TEXT = [("LOWELL LINE", (51, 204.6), "right"), ("HAVERHILL LINE", (59.6, 205.6), "left"), ("HIGH-SPEED RAIL TO CONCORD NH", (51, 201.9), "right"), ("VIA LOWELL, NASHUA, MANCHESTER", (51, 199.2), "right"), ("FITCHBURG LINE TO GREENFIELD, NORTH ADAMS", (-7, 135.8), "left"), ("HIGH-SPEED RAIL TO MONTREAL VIA BURLINGTON VT", (-7, 133.2), "left"),
           ("TO FRAMINGHAM, WORCESTER", (-44, 123.2), "left"), ("HIGH-SPEED RAIL TO ALBANY", (-44, 128.2), "left"), ("VIA WORCESTER, SPRINGFIELD", (-44, 125.7), "left"), ("NEWBURYPORT / ROCKPORT LINE", (209, 206.1), "right"), ("HIGH-SPEED RAIL TO BANGOR", (209, 203.6), "right"), ("VIA PORTSMOUTH, PORTLAND, AUGUSTA", (209, 201.1), "right"), ("TO LAWRENCE", (164, 204.5), "right"), ("PROVIDENCE LINE", (48, -18.6), "left"), ("FRANKLIN LINE", (27.6, -18), "right"), ("HIGH-SPEED RAIL TO NYC", (48, -13.2), "left"), ("VIA PROVIDENCE, NEW HAVEN", (48, -15.9), "left"),
           ("GREENBUSH LINE", (124, 9.4), "left"), ("KINGSTON LINE", (140.4, -12.8), "right"), ("TO PLYMOUTH", (142.8, -15.4), "right"), ("FALL RIVER, NEW BEDFORD, CAPE COD LINES", (120, -18), "right")]

CAPSULES = [((118, 8), (121.6, 8)), ((43, 14), (46, 14)), ((118, 52), (121.6, 52)), ((118, 25.6), (121.6, 25.6)), ((20, 111), (20, 107.4)), ((106, 112), (110, 112)), ((106, 120), (114, 120)), ((110, 100), (118, 100)), ((46, 76), (50, 76)), ((114.2, 77.2), (117.8, 79.8)), ((135, 150), (135, 146))]
RINGS = ["Suffolk Downs", "Gov't Center", "Longwood Medical Area", "Braintree", "Lynn", "VFW Parkway", "Wonderland", "Stadium", "Park Street", "Downtown Crossing", "Kendall/MIT", "Harvard", "Lechmere", "Assembly", "Back Bay", "Ruggles", "Forest Hills", "JFK/UMass",
         "Ashmont", "Airport", "Kenmore", "Seaport", "Porter", "Charles/MGH", "Newmarket", "BU Bridge", "Terminals", "Alewife", "Mattapan", "Four Corners", "Convention Center", "Readville", "Orient Heights", "Aquarium", "Broadway", "Sullivan Sq", "Mass Ave", "Nubian", "Tufts Medical Ctr"]
ENDS = {"Winthrop Center": BLUE, "Weymouth": RED, "Mattapan": RED, "Oak Grove": ORANGE, "Wyoma Sq": BLUE, "West Medford": GREEN, "Boston College": GREEN, "Riverside": GREEN,
        "Cleveland Circle": GREEN, "Reading": ORANGE, "Watertown": GREEN}
NEW_ON_OLD = set()
HIDE = {"Back Bay", "Ruggles", "West Station", "Boston Central", "Nubian", "Melnea Cass", "Lynn Common", "Gov't Center", "State", "North Station", "South Station", "Haymarket", "Longwood Medical Area"}
TEXT = {"Park Street": "Park\nStreet", "Kendall/MIT": "Kendall", "Newton City Hall": "Newton\nCity Hall", "Four Corners": "Four\nCorners", "Melnea Cass": "Melnea\nCass", "Mass Ave": "MIT", "Convention Center": "Convention\nCenter", "Boston Medical": "Boston\nMedical", "Community College": "Community\nCollege", "Science Park": "Science\nPark", "Museum of Fine Arts": "MFA", "Needham Junction": "Needham Jct",
        "Tufts Medical Ctr": "Tufts Medical Ctr", "Downtown Crossing": "Downtown\nCrossing"}
SIDE = {}
for names, s in ((["Porter"], "bl"), (["Davis", "Harvard", "Central", "Kendall/MIT"], "tr"), (["Alewife"], "tr"), (["Arlington Ctr", "East Arlington", "North Cambridge"], "tr"), (["Arlington Heights"], "tr"),
                 (["Broadway", "Andrew", "North Quincy", "Wollaston", "Quincy Center", "Quincy Adams"], "r"), (["Braintree"], "l"),
                 (["Savin Hill", "Fields Corner", "Shawmut"], "bl"), (["Ashmont"], "l"), (["Cedar Grove", "Butler", "Milton", "Central Ave", "Valley Rd", "Capen St"], "r"), (["Mattapan"], "br"),
                 (["Oak Grove", "Malden Center", "Community College"], "l"), (["Wellington", "Assembly"], "r"), (["Chinatown", "Tufts Medical Ctr", "Mass. Ave"], "r"), (["Back Bay"], "up"), (["Bowdoin"], "up"), (["Nubian"], "br"), (["Newmarket"], "se"), (["Melnea Cass"], "b"), (["Boston Medical"], "b"),
                 (["Ruggles"], "l"), (["Roxbury Crossing", "Jackson Sq", "Stony Brook", "Green St", "Forest Hills", "Roslindale Village", "Bellevue", "Highland", "West Roxbury", "VFW Parkway"], "br"), (["Dedham"], "r"), (["Lexington Ctr", "Lexington Route 128", "Belmont Ctr", "Waverley Sq", "Waltham"], "b"), (["Seaver St", "Terminals"], "x2"), (["South Bay"], "l"), (["Uphams Corner", "Four Corners"], "br"), (["Talbot Ave", "Morton St", "Blue Hill Ave", "Fairmount"], "along"), (["Readville"], "r"), (["City Point"], "br"), (["West Broadway"], "t"), (["Convention Center"], "br"), (["Winthrop Center"], "r"), (["Eagle Hill"], "tl"), (["Linden Sq", "Cliftondale", "Saugus Center"], "t"), (["East Saugus"], "tl"),
                 (["Aquarium", "Maverick", "Wood Island", "Orient Heights", "Suffolk Downs", "Beachmont", "Revere Beach", "Wonderland", "Lynn"], "br"),
                 (["Medford/Tufts", "Ball Sq", "Magoun Sq", "Gilman Sq", "East Somerville"], "l"), (["West Medford"], "tr"), (["Lechmere"], "bl"), (["Science Park"], "r"),
                 (["Griggs St", "Allston St", "Warren St", "Washington St", "Sutherland Rd", "Chiswick Rd", "Chestnut Hill Ave", "South St"], "l"), (["Boston College"], "bl"), (["Newton City Hall"], "r"), (["Norumbega"], "r"),
                 (["Kent St", "St. Paul St", "Coolidge Corner", "Summit Ave", "Brandon Hall", "Fairbanks St", "Washington Sq", "Tappan St", "Dean Rd", "Englewood Ave", "Cleveland Circle"], "l"),
                 (["Fenway", "Longwood", "Brookline Village", "Brookline Hills", "Beaconsfield", "Reservoir", "Chestnut Hill", "Newton Centre", "Newton Highlands", "Eliot", "Waban", "Woodland", "Riverside"], "l"),
                 (["Prudential", "Symphony", "Northeastern", "Museum of Fine Arts", "Longwood Medical Area", "Brigham Circle", "Fenwood Rd", "Mission Park", "Riverway", "Back of the Hill", "Heath St", "Hyde Sq"], "l"),
                 (["Blandford St", "BU East", "BU Central", "Amory St", "Babcock St", "Packard's Corner", "Harvard Ave"], "r"),
                 (["St. Mary's St", "Hawes St"], "dn"), (["Copley", "Arlington", "Boylston"], "up"), (["Hynes"], "b"), (["Kenmore"], "tl"),
                 (["Needham Heights"], "r"), (["Needham Junction"], "l"), (["Courthouse"], "b"), (["Seaport"], "r"), (["Mass Ave"], "tl"), (["Inner Belt", ], "r"), (["Bellingham Sq"], "l"), (["Chelsea", "Everett Sq", "Stadium", "Encore"], "up"), (["Binney"], "l"), (["Allston", "Oak Sq"], "t"), (["Brighton Center"], "t"), (["Newton Corner"], "r"), (["Watertown"], "b"), (["Reading", "Wakefield", "Greenwood", "Melrose Highlands", "Wyoming Hill"], "l"),
                 (["West Station"], "tr"), (["Barrys Corner"], "r"), (["BU Bridge"], "r"), (["Lansdowne"], "tr"),
                 (["Charles/MGH"], "bl"), (["Park Street"], "br"),
                 (["Downtown Crossing"], "l"), (["Sullivan Sq"], "x"), (["JFK/UMass"], "br"), (["Airport"], "br")):
    for n in names:
        SIDE[n] = s
NUDGE = {"North End": (2.4, -1.9), "North Cambridge": (1.5, 1.4), "Lechmere": (2.4, 0), "East Somerville": (4.5, 1.6), "Union Sq": (-3, 0), "Four Corners": (-0.5, 2.6), "Uphams Corner": (4, -0.5), "Chinatown": (-1, 0), "Savin Hill": (-1.5, 0), "Fields Corner": (-1.5, 0), "Shawmut": (-1.5, 0), "Park Street": (1.4, 0.8), "Charles/MGH": (-1.5, 0), "Navy Yard": (-0.8, 0), "Airport": (2.5, -1),
         "Brigham Circle": (0, -1.6), "Bellingham Sq": (-1.5, -2), "Lansdowne": (0.6, 0.7)}
HALOED = {"Thompson Sq", "West Broadway", "Assembly", "Lansdowne"}
SIDE.update({"North End": "r", "Dover": "r", "Northampton": "r", "Grove Hall": "r", "Wellington Hill": "l", "Inman Sq": "t", "Davis": "l", "Auburndale": "l", "Riverside": "l", "Union Sq": "b", "Lynn Harbor": "br", "Broadway": "br", "Charles/MGH": "tl", "Kendall/MIT": "l", "Assembly": "tr", "Encore": "b", "Lansdowne": "br", "Ruggles": "bl", "Brigham Circle": "l", "L Street": "t", "Seaport": "br", "Newmarket": "t", "Roslindale Village": "tl", "Hyde Park": "tr", "Heath St": "l", "Newton Corner": "t", "Courthouse": "t", "Hyde Sq": "l", "Forest Hills": "x", "Orient Heights": "r", "Seaver St": "l", "Terminals": "bl", "Roxbury Crossing": "br", "Broadway": "bl", "Thompson Sq": "l", "Navy Yard": "r", "City Square": "r", "Fort Point": "b", "Aquarium": "br", "Convention Center": "br", "City Point": "r", "West Broadway": "t", "Bellingham Sq": "r", "Stadium": "up", "Assembly": "tl", "Encore": "t", "Chelsea": "up", "Everett Sq": "up", "Nubian": "up"})


def water(ax, z=1):
    ax.add_patch(Polygon(smooth_closed([(117, 121), (122, 112), (121, 92), (128, 86), (150, 84), (156, 74), (146, 62), (141, 48), (145, 30), (140, 10), (142, -40),
                                        (260, -40), (260, 240), (222, 240), (196, 164), (172, 136), (154, 116), (138, 110), (127, 118), (129, 133), (121, 134)]),
                         fc=WATER, ec="none", zorder=z))
    for pts, w in (([(-70, 100), (-10, 118), (30, 116), (46, 106), (62, 103), (78, 96), (92, 110), (104, 126), (120, 127)], 11),
                   ([(122, 130), (130, 144), (124, 167), (98, 176), (80, 190)], 7)):
        ax.plot(*smooth_open(pts).T, color=WATER, lw=w * 1.4, zorder=z, solid_capstyle="round")


def glpill(ax, x, y, letter):
    """Green Line pill: GL plus the branch letter in a white circle, as on the poster."""
    bullet(ax, x, y, "GL    ", GREEN, h=3.9, fs=9.4)
    ax.scatter([x + 2.9], [y], s=62, color=WHITE, zorder=12.2)
    ax.text(x + 2.9, y - 0.05, letter, color=GREEN, fontsize=8.6, fontweight="bold", ha="center", va="center", zorder=12.3)


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
SIDE.update({"East Saugus": "b", "Saugus Center": "t", "Lexington Route 128": "l", "Waltham": "l", "Trapelo Rd": "r"})
TEXT["Lexington Route 128"] = "Lexington\nRoute 128"
TEXT["Saugus Center"] = "Saugus\nCenter"
NUDGE["Hyde Park"] = (3.8, 0)
SIDE.update({"Hersey": "l", "Hyde Park": "r", "VFW Parkway": "br", "Needham Junction": "l"})
for n in ("Broadway", "Andrew", "JFK/UMass", "North Quincy", "Wollaston", "Quincy Center", "Quincy Adams"):
    NUDGE[n] = (NUDGE.get(n, (0, 0))[0] + 2.6, NUDGE.get(n, (0, 0))[1])
TEXT["Hyde Park"] = "Hyde\nPark"
SIDE.update({"Andrew": "l", "Fields Corner": "l"})
NUDGE["Andrew"] = (0, 0)
NUDGE["Fields Corner"] = (0, 0)
NUDGE["East Saugus"] = (-1.6, 0)
NUDGE["East Somerville"] = (3, 1.6)
HALOED.update({"Charles/MGH", "Mass. Ave", "Northampton", "Newmarket", "East Saugus", "Broadway", "East Somerville"})
SIDE["Wyoma Sq"] = "l"
SIDE["Terminals"] = "l"
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
SHIFT = {"r": (1, 0), "l": (-1, 0), "tr": (1, 1), "tl": (-1, 1), "br": (1, -1), "bl": (-1, -1)}


# Real shoreline points (lon, lat) and where each sits on the diagram. The real coast and islands are bent through these.
SHORE = {(-71.0475, 42.3595): (120.4, 106), (-71.0505, 42.3665): (120.6, 116), (-71.0600, 42.3725): (121, 124), (-71.0480, 42.3750): (127, 130), (-71.0390, 42.3690): (126.6, 119),
         (-71.0290, 42.3590): (129, 106), (-71.0100, 42.3540): (146, 92), (-70.9950, 42.3650): (162, 106), (-70.9600, 42.3620): (170, 113), (-70.9610, 42.3760): (177, 121),
         (-70.9750, 42.3830): (171, 133), (-70.9900, 42.3910): (160, 137), (-70.9900, 42.3970): (161, 146), (-70.9850, 42.4170): (167, 152), (-70.9650, 42.4440): (183, 168),
         (-70.9450, 42.4560): (193, 177), (-70.9320, 42.4640): (200, 183), (-70.8950, 42.4640): (207, 189), (-70.8400, 42.4950): (240, 192), (-70.8850, 42.5230): (220, 206), (-70.8700, 42.5350): (228, 212), (-70.8800, 42.5000): (224, 198), (-70.9100, 42.5000): (214, 196), (-70.9350, 42.4320): (205, 166), (-70.9020, 42.4220): (220, 160),
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
        ax.add_patch(Polygon(np.array(g.exterior.coords), fc=WATER, ec=COAST, lw=0.6, zorder=1))
        for r in g.interiors:
            ax.add_patch(Polygon(np.array(r.coords), fc=PAPER, ec=COAST, lw=0.6, zorder=1.1))


RIVERS = {"charles": [(-60, 127), (30, 127), (50, 125), (59, 118), (63, 108), (68, 98), (76, 99), (85, 105), (92, 118), (100, 127), (110, 128), (118, 127), (127, 123)],
          "mystic": [(127, 123), (129, 134), (125, 146), (118, 153), (112, 161), (96, 174), (84, 186)],
          "chelsea": [(129, 134), (134, 134), (150, 146)], "neponset": [(141, 43), (118, 47), (108, 37), (99, 27), (97, 4), (100, -22)]}
WIDTH = {"charles": 12, "mystic": 11, "chelsea": 8, "neponset": 7}
BASIN = [(120, 127), (110, 128), (100, 127), (92, 118), (85, 105), (76, 99), (66, 97.5)]
BASIN_PT = 27  # line width in points, about 5.6 diagram units


def river_mouths(ax):
    """Hand-drawn so each stop is on its true bank: Harvard and MIT north of the Charles, Allston and BU south;
    Assembly and Sullivan west of the Mystic, Encore and the stadium east; Ashmont branch north of the Neponset."""
    for n, xy in RIVERS.items():
        ax.plot(*smooth_open(xy, 2).T, color=WATER, lw=WIDTH[n], zorder=0.95, solid_capstyle="round", solid_joinstyle="round")
    ax.plot(*smooth_open(BASIN, 2).T, color=WATER, lw=BASIN_PT, zorder=0.95, solid_capstyle="round", solid_joinstyle="round")


FERRY = "#2b7a9b"
TO_BASIN = [("Long Wharf dock", (121, 103), "Long Wharf"), ("North End", (120.9, 113), ""), ("Lovejoy", (120.2, 125.5), "Lovejoy Wharf")]
FROM_BASIN = [("Mouth", (119, 128.2), ""), ("Thompson Sq", (127, 138.4), ""), ("Mystic", (116.5, 154.5), ""), ("back", (129, 134), ""), ("Chelsea", (146, 143), "Chelsea Creek"), ("back2", (129, 134), ""),
              ("East Boston", (128.5, 108), ""), ("Logan", (139, 95.5), "Logan Dock"), ("Fort", (157, 77), "Fort Independence"), ("Seaport", (143, 82), ""), ("back3", (134, 91), ""), ("Long Wharf dock", (121, 103), "")]
HINGHAM = [(122, 106), (162, 80), (188, 61)]


def ferries(ax):
    """Route every ferry through the water: shortest path on a grid of open water, kept toward mid-channel."""
    step = 0.5
    px = 4.84  # points per diagram unit
    wet = SEA.buffer(0)
    for n, xy in RIVERS.items():
        wet = wet.union(LineString(smooth_open(xy, 2)).buffer(WIDTH[n] / px / 2))
    wet = wet.union(LineString(smooth_open(BASIN, 2)).buffer(BASIN_PT / px / 2))
    xs = np.arange(50, 222, step)
    ys = np.arange(40, 208, step)
    gx, gy = np.meshgrid(xs, ys)
    inside = shapely.contains_xy(wet.buffer(-0.2), gx, gy)
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
            path, k = [], ib
            while k != ia and k >= 0:
                path.append(k)
                k = pred[k]
            path.append(ia)
            xy = nodes[path[::-1]]
            xy = xy[::4] if len(xy) > 8 else xy
            out.append(smooth_open(np.vstack([xy, nodes[ib]]), 3))
        return out

    edge = wet.boundary

    def dock(q):
        d = edge.interpolate(edge.project(Point(q)))
        return (d.x, d.y)

    TRANSIT = ("Mouth", "back", "back2", "back3")
    to_basin = [(n, q if n in TRANSIT else dock(q), t) for n, q, t in TO_BASIN]
    from_basin = [(n, q if n in TRANSIT else dock(q), t) for n, q, t in FROM_BASIN]
    georges = dock((178, 72))
    long_island = dock((166, 66))
    hull = dock((189, 60))
    columbia = dock((148, 47))
    print("columbia dock", [round(v, 1) for v in columbia])
    hingham = [to_basin[0][1], (134, 91), (162, 80), long_island, georges, hull]
    split = (176, 113)
    trunk = (134, 91)
    global LOGAN
    LOGAN = [q for n, q, _ in from_basin if n == "Logan"][0]
    lynn = dock((190, 174))
    north = [to_basin[0][1], trunk, (162, 80), split, (190, 150), lynn]
    salem = [split, (200, 131), (220.5, 147)]
    basin = LineString(smooth_open(BASIN, 2))
    # Boston side is on the right looking upriver from the locks
    up = np.array(basin.offset_curve(-2.2).coords)
    down = np.array(basin.offset_curve(2.2).coords)
    if np.hypot(*(up[0] - np.array(BASIN[0]))) > np.hypot(*(up[-1] - np.array(BASIN[0]))):
        up = up[::-1]
    if np.hypot(*(down[0] - np.array(BASIN[-1]))) > np.hypot(*(down[-1] - np.array(BASIN[-1]))):
        down = down[::-1]
    turn = smooth_open(np.array([up[-1], (BASIN[-1][0] - 1.6, BASIN[-1][1]), down[0]]), 3)
    legs = route([q for _, q, _ in to_basin] + [tuple(up[0])]) + [up, turn, down] + route([tuple(down[-1])] + [q for _, q, _ in from_basin]) + route(hingham) + route(north) + route(salem) + route([long_island, (153, 58), (150.5, 53), columbia])
    land = 0.0
    for xy in legs:
        off = LineString(xy).difference(wet)
        land += off.length
        if off.length > 0.2:
            print("  off water near", [round(v, 1) for v in off.bounds])
        ax.plot(*xy.T, color=FERRY, lw=1.5, ls=(0, (1, 1.4)), zorder=2.5)
    print(f"ferry track over land: {land:.2f} units")
    cy = LineString(rounded([(140, 76), (149, 76), (152, 73), (152, 67), (149, 64), (122, 64)], 3))
    print(f"cyan southie in water: {cy.intersection(SEA.buffer(0)).length:.2f} units")
    ax.scatter(*columbia, s=26, color=WHITE, edgecolor=INK, lw=1.2, zorder=3.2)
    label(ax, columbia, "Columbia Point", "b", gap=1.8, fs=7.6, color=FERRY)
    for n, q, t in to_basin + from_basin[:-1]:
        if n in TRANSIT:
            continue
        ax.scatter(*q, s=26, color=WHITE, edgecolor=INK, lw=1.2, zorder=3.2)
        if t:
            side = {"Lovejoy Wharf": "r", "Chelsea Creek": "t", "Logan Dock": "b", "Long Wharf": "r", "Fort Independence": "r"}[t]
            label(ax, (q[0] + (3 if t == "Logan Dock" else 0), q[1] + (1.5 if t == "Lovejoy Wharf" else 0)), t, side, gap=1.8, fs=7.6, color=FERRY)
    # Stops along each bank, with names lying in the wider water
    ls_up, ls_down = LineString(up), LineString(down)
    for ls, f in ((ls_up, 0.30), (ls_up, 0.56), (ls_up, 0.82), (ls_down, 0.20), (ls_down, 0.46), (ls_down, 0.72)):
        q = ls.interpolate(f, normalized=True)
        q = dock((q.x, q.y))
        ax.scatter(*q, s=22, color=WHITE, edgecolor=INK, lw=1.1, zorder=3.2)
    for t, (x, y), rot, ha_ in (("Esplanade", (90.5, 110.6), 56, "right"), ("Duck Boats", (89.2, 117.6), 54, "left")):
        ax.text(x, y, t, fontsize=6.8, color=FERRY, rotation=rot, rotation_mode="anchor", ha=ha_, va="center", zorder=3.4)
    ax.scatter(*lynn, s=26, color=WHITE, edgecolor=INK, lw=1.2, zorder=3.2)
    for q in (long_island, georges, hull):
        ax.scatter(*q, s=26, color=WHITE, edgecolor=INK, lw=1.2, zorder=3.2)
    label(ax, georges, "Georges Island", "r", gap=1.8, fs=7.6, color=FERRY)
    label(ax, hull, "Hull", "r", gap=1.8, fs=7.6, color=FERRY)
    label(ax, long_island, "Long Island\nRecovery Campus", "b", gap=1.6, fs=7.6, color=FERRY)
    ax.annotate("", xy=(221.8, 148.6), xytext=(220, 146.6), arrowprops=dict(arrowstyle="-|>,head_width=0.3,head_length=0.5", color=FERRY, lw=1.2), zorder=3)
    ax.text(191.5, 152, "LYNN FERRY", fontsize=6.8, fontweight="bold", color=FERRY, ha="right", va="bottom", zorder=3)
    ax.text(220.5, 138.5, "TO SALEM FERRY", fontsize=6.8, fontweight="bold", color=FERRY, ha="right", va="bottom", zorder=3)
    ax.text(198, 67, "The Harbor Loop follows\na ferry chartered in 1631", fontsize=7.4, style="italic", color=FERRY, ha="left", va="bottom", zorder=3)
    ax.text(188, 57.5, "HINGHAM / HULL FERRY", fontsize=6.8, fontweight="bold", color=FERRY, ha="right", va="bottom", zorder=3)
    ax.text(175, 100, "HARBOR LOOP FERRY", fontsize=6.8, fontweight="bold", color=FERRY, ha="right", va="bottom", zorder=3) if False else None


def main():
    w = 18.0
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
    ax.plot(*rounded([(208.5, 198.5), (176, 198.5), (167, 207.5)], 3).T, color=PURPLE, lw=3.1, ls=(0, (2.2, 1.1)), dash_capstyle="butt", zorder=3)
    for spur in ([(208.5, 198.5), (215, 198.5), (220, 193.5)], [(53, 188), (66, 201), (80, 201)], [(-21, 143), (-24, 140), (-40, 140)],
                 [(50, -7), (78, -7)], [(34, -16), (46, -16)]):
        ax.plot(*rounded(spur, 3).T, color=PURPLE, lw=3.1, ls=(0, (2.2, 1.1)), dash_capstyle="butt", zorder=3)
    for (x0, y0), (x1, y1) in (((53, 202), (53, 206)), ((170, 204.5), (166.5, 208)), ((-41.2, 163.2), (-44, 166)), ((-40, 122), (-44, 122)), ((46, -17.6), (46, -19.8)), ((31.8, -15.2), (29, -18)),
                               ((121.6, -14), (121.6, -18)), ((143.2, -13.6), (146, -16.4)), ((149.2, -3.2), (152, -6)), ((58, 204), (58, 208)), ((212, 205.6), (212, 207.8))):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>,head_width=0.45,head_length=0.8", color=PURPLE, lw=0), zorder=3)
    label(ax, (207.5, 196.7), "South Salem", "r", gap=0, fs=6.9, color=CR_TEXT_COLOR)
    for name, xy, side, st in CR_STOPS:
        ax.scatter(*xy, s=46, marker="s", color=PURPLE if st == "solid" else WHITE, edgecolor=PURPLE, lw=1.4, zorder=6)
        if side:
            label(ax, xy, name, side, gap=2.2, fs=7.8, color=CR_TEXT_COLOR)
    ax.plot(*rounded([(53, 206), (53, 175), (88, 175), (114, 149), (114, 72), (108, 66), (76, 66), (46, 36), (46, -19.6)], 3).T, color=HSR, lw=1.3, zorder=3.2)
    ax.plot(*rounded([(114, 76), (114, 72), (108, 66), (82, 66), (26, 122), (-44, 122)], 3).T, color=HSR, lw=1.3, zorder=3.2)
    ax.plot(*rounded([(-44, 166), (-10, 132), (88, 132), (100, 120), (114, 120)], 3).T, color=HSR, lw=1.3, zorder=3.2)
    ax.plot(*rounded([(114, 139), (121, 146), (139, 146), (178, 185), (195, 185), (212, 202), (212, 208)], 3).T, color=HSR, lw=1.3, zorder=3.2)
    label(ax, (45, -14.3), "Mansfield", "l", gap=0, fs=7.8, color=CR_TEXT_COLOR)
    label(ax, (35.4, -18.2), "Foxborough", "r", gap=0, fs=7.8, color=CR_TEXT_COLOR)
    label(ax, (51, -5.2), "Stoughton", "r", gap=0, fs=7.8, color=CR_TEXT_COLOR)
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
        transfer(ax, a, b, lw=LW * 1.05)
    transfer(ax, (118, 120), lw=LW * 1.05)
    ax.scatter(*pts["West Station"], s=(LW * 1.7) ** 2, color=WHITE, edgecolor=INK, lw=LW * 0.28, zorder=10)
    label(ax, (62, 90), "WEST\nSTATION", "r", gap=0, fs=11.6, weight="bold")
    ax.scatter(*pts["Back Bay"], s=(LW * 1.7) ** 2, color=WHITE, edgecolor=INK, lw=LW * 0.28, zorder=10)
    label(ax, pts["Back Bay"], "BACK BAY", "up", gap=2.6, fs=11.6, weight="bold")
    ax.scatter([114], [100], s=(LW * 2.3) ** 2, color=WHITE, edgecolor=INK, lw=LW * 0.3, zorder=9.8)
    ax.scatter([114], [100], s=(LW * 1.5) ** 2, color=RED, edgecolor=WHITE, lw=LW * 0.3, zorder=10)
    real_water(ax, pts)
    river_mouths(ax)
    ferries(ax)
    # Silver Line: a short airport shuttle, one line running both ways, from Logan Dock past every terminal to Airport
    stroke(ax, rounded([LOGAN, pts["Terminals"], (156, 112), (143, 125), (135, 125)], 2.4), SILVER, LW * 0.72, "dash", z=4.4)
    silver = [("A", (143.8, 99.8), -1.6, 1.8), ("B", (152, 116), 1.8, 1.8), ("C", (148.5, 119.5), 1.8, 1.8), ("E", (145, 123), 1.8, 1.8)]
    for q in [LOGAN, (139.5, 125), (152, 108)] + [v[1] for v in silver]:
        ax.scatter(*q, s=(LW * 0.62) ** 2, color=WHITE, edgecolor=INK, lw=0.5, zorder=8)
    label(ax, (143.5, 125), "Rental Cars", "t", gap=1.5, fs=7.6)
    label(ax, (152, 108), "Parking", "tl", gap=1.5, fs=7.6)
    for t, q, dx, dy in silver:
        ax.text(q[0] + dx, q[1] + dy, t, fontsize=8.8, fontweight="bold", color=INK, ha="center", va="center", zorder=11)
    barred = not_accessible()
    for n, p in pts.items():
        s = SIDE.get(n, "r")
        if n in HIDE or s == "x":
            continue
        if n not in barred and s in SHIFT:  # icon sits between the stop and its name
            sx, sy = SHIFT[s]
            flip = n in ("Thompson Sq",)  # name fills the gap beside the stop, so the icon goes on the far side
            if flip:
                icon(ax, p[0] - sx * 3.1, p[1])
            g = 2.9 if sx and sy else 3.1
            None if flip else icon(ax, p[0] + NUDGE.get(n, (0, 0))[0] + sx * g, p[1] + NUDGE.get(n, (0, 0))[1] + sy * (2.5 if sy else 0))
            p = p if flip else (p[0] + sx * 2.0, p[1])
        big = n in ENDS
        if big:
            t = n.upper().replace(" ", "\n", 1) if len(n) > 9 or n == "Hyde Park" else n.upper()
            label(ax, (p[0] + NUDGE.get(n, (0, 0))[0], p[1] + NUDGE.get(n, (0, 0))[1]), t, s, fs=10.4, weight="bold", gap=3.6)
        else:
            q = (p[0] + NUDGE.get(n, (0, 0))[0], p[1] + NUDGE.get(n, (0, 0))[1])
            label(ax, q, TEXT.get(n, n), s, fs=9.4, gap=2.3, style="italic" if n in NEW_ON_OLD else "normal", halo=n in HALOED)
    for t, xy, ha in CR_TEXT:
        ax.text(*xy, t, fontsize=7.4, fontweight="bold", color=CR_TEXT_COLOR, ha=ha, va="bottom", zorder=12)
    # Downtown names sit by hand around the capsules.
    label(ax, (122, 98.2), "BOSTON\nCENTRAL", "r", gap=0, fs=16.5, weight="bold")
    label(ax, (122.2, 121.6), "NORTH\nSTATION", "r", gap=0, fs=11.6, weight="bold")
    label(ax, (120.6, 88), "SOUTH\nSTATION", "r", gap=0, fs=11.6, weight="bold")
    label(ax, (90.4, 54.6), "Nubian", "bl", gap=0, fs=9.4)
    label(ax, (84, 57.8), "Mass & Cass\nTreatment Center", "t", gap=0, fs=8.8)
    label(ax, (48.5, 27.6), "Forest Hills", "r", gap=0, fs=9.4)
    label(ax, (69.5, 56), "Ruggles", "dn", gap=0.8, fs=9.4)
    label(ax, (104.2, 112), "Haymarket", "l", gap=0, fs=9.2)
    label(ax, (101.5, 96.6), "Gov't\nCenter", "r", gap=0, fs=9.2)
    label(ax, (58.8, 59.6), "Longwood\nMedical", "l", gap=0, fs=9.2)
    label(ax, (108.4, 152), "Sullivan Sq", "tl", gap=0, fs=9.2)
    bullet(ax, -30, 176, "RL", RED)
    bullet(ax, 120, 202, "OL", ORANGE)
    bullet(ax, 182.5, 188.8, "BL", BLUE)
    bullet(ax, 153.5, 88, "YL", YELLOW, fg=INK)
    bullet(ax, 154, 122.5, "SL", SILVER)
    glpill(ax, 40, 181, "E")
    bullet(ax, 116, 163, "CL", CYAN)
    label(ax, (116, 156.2), "Encore", "b", gap=0)
    bullet(ax, 61, -1, "IL", INDIGO)
    glpill(ax, -36.5, 53, "B")
    glpill(ax, -25, 42, "C")
    glpill(ax, -33, 22, "D")
    # Title.
    tx, ty, tr = -36, 198.4, 7.6  # roundel: heavy ring, wide block T
    ax.add_patch(Circle((tx, ty), tr, fc=WHITE, ec=INK, lw=4.5, zorder=12))
    ax.add_patch(Polygon([(tx - 5.1, ty + 4.3), (tx + 5.1, ty + 4.3), (tx + 5.1, ty + 2.0), (tx + 1.35, ty + 2.0), (tx + 1.35, ty - 5.2), (tx - 1.35, ty - 5.2),
                          (tx - 1.35, ty + 2.0), (tx - 5.1, ty + 2.0)], closed=True, fc=INK, ec="none", zorder=12.1))
    # Title block, matched to Max's Illustrator layout
    ax.text(-25.5, 200.87, "Boston\u2019s", fontsize=34, fontweight="bold", color=INK, va="baseline", zorder=12)
    bold = FontProperties(family="Arial", weight="bold")
    tw = TextPath((0, 0), "Rapid T", size=34, prop=bold).get_extents().x1 / 4.836
    ax.text(-25.5, 192.43, "Rapid T", fontsize=34, fontweight="bold", color=INK, va="baseline", zorder=12)
    ax.text(-25.5 + tw - 0.054 * 34 / 4.836 + 0.15, 192.43, "ransit", fontsize=34, fontweight="bold", color=INK, va="baseline", zorder=12)
    for t, y in (("Map: Maxwell Howe", 188.04), ("#30DayMapChallenge", 185.07), ("Day 8 \u2022 Utopia", 182.3)):
        ax.text(-43.72, y, t, fontsize=11, color=INK, va="baseline", zorder=12)
    narrow = FontProperties(fname=r"C:\Windows\Fonts\ARIALNI.TTF")
    for k, t in enumerate(("This is a futuristic concept map", "and is not affiliated with the MBTA", "in any way. Most of the map decisions",
                           "are grounded in real studies conducted,", "proposals made, or projections for", "future projects or development.")):
        ax.text(-18.75, 188.5 - k * 2.978, t, fontproperties=narrow, fontsize=12, color="#000000", va="baseline", zorder=12)
    # Callout in the harbor, and the Key: one type system. Headings 11 bold, body 9.6, captions 7.6.
    for x0, y0, w_, h_ in ((157, 80, 62, 33), (157, -13.6, 62, 68.6)):
        ax.add_patch(FancyBboxPatch((x0, y0), w_, h_, boxstyle="square,pad=0", fc=WHITE, ec=INK, lw=1.4, zorder=11))
    ax.text(160.5, 110.6, "The BIGGER Dig", fontsize=22, fontweight="bold", color=RED, zorder=12, va="top")
    ax.text(160.5, 103.4, "Four tracks under downtown join North and South Stations at\nBoston Central, under Atlantic Avenue. Walkways reach\nDowntown Crossing and Park.",
            fontsize=9.6, color=INK, zorder=12, va="top", linespacing=1.22)
    ax.plot([160.5, 215.5], [92.6, 92.6], color=INK, lw=0.7, zorder=12)
    for x, big, small in ((160.5, "$21.5B", "The tunnel, MassDOT\nfour-track estimate"), (180.5, "$15B", "The original\nBig Dig"), (197.5, "~$125B", "Everything on this\nmap, rough estimate")):
        ax.text(x, 91.4, big, fontsize=16, fontweight="bold", color=RED, zorder=12, va="top")
        ax.text(x, 86.4, small, fontsize=7.6, color=INK, zorder=12, va="top", linespacing=1.15)
    lx, tx, ly = 160.5, 174.5, 51.2
    ax.text(lx, ly, "Key", fontsize=11, fontweight="bold", color=INK, va="center", zorder=12)
    rows = [("solid", RED, LW, "Running today"), ("stripe", RED, LW, "New: real proposal or strong case"), ("dash", RED, LW, "New: imagined"),
            ("solid", PURPLE, 3.1, "Commuter rail, running through"), ("hsr", PURPLE, 3.1, "High-speed rail"), ("ferry", "#2b7a9b", 1.5, "Ferries, including the Harbor Loop"), ("dig", INK, 0, "The BIGGER Dig, four tracks"), ("none", INK, 0, "Replacement shuttle buses: none")]
    for i, (st, c, wd, t) in enumerate(rows):
        y = ly - 4.4 - i * 3.4
        if st == "none":
            pass
        elif st == "dig":
            four_tracks(lx + 0.6, y, lx + 10.4, y, 12)
        elif st == "ferry":
            ax.plot([lx, lx + 11], [y, y], color=c, lw=wd, ls=(0, (1, 1.4)), zorder=12)
        else:
            stroke(ax, [(lx, y), (lx + 11, y)], c, wd, "solid" if st == "hsr" else st, z=12)
        if st == "hsr":
            ax.plot([lx, lx + 11], [y, y], color=HSR, lw=1.3, zorder=12.2)
        ax.text(tx, y, t, fontsize=9.6, va="center", color=INK, zorder=12)
    y = ly - 4.4 - 8 * 3.4
    for i, (c, t) in enumerate(((YELLOW, "Yellow: the ring around the core"), (CYAN, "Cyan: Assembly to Southie"), (INDIGO, "Indigo: the Fairmount corridor"), (SILVER, "Silver: Logan Dock to Airport, all terminals"))):
        ax.scatter([lx + 5.5], [y - i * 3.4], s=58, color=c, zorder=12)
        ax.text(tx, y - i * 3.4, t, fontsize=9.6, va="center", color=INK, zorder=12)
    ax.text(lx, y - 14.4, "Stations", fontsize=11, fontweight="bold", color=INK, va="center", zorder=12)
    y0 = y - 18.2
    ax.scatter([lx + 5.5], [y0], s=(LW * 1.6) ** 2, color=WHITE, edgecolor=INK, lw=2.2, zorder=12)
    ax.scatter([lx + 5.5], [y0], s=(LW * 0.9) ** 2, color=RED, zorder=12.1)
    ax.scatter([lx + 5.5], [y0 - 3.4], s=(LW * 1.3) ** 2, color=WHITE, edgecolor=INK, lw=2.2, zorder=12)
    ax.scatter([lx + 5.5], [y0 - 6.8], s=(LW * 0.9) ** 2, color=WHITE, edgecolor=INK, lw=1.6, zorder=12)
    ax.scatter([lx + 5.5], [y0 - 10.2], s=46, marker="s", color=PURPLE, zorder=12)
    for i, t in enumerate(("Tier 1: Boston Central", "Tier 2: North, South, West, Back Bay", "Tier 3: subway stations", "Tier 4: small commuter rail stops")):
        ax.text(tx, y0 - i * 3.4, t, fontsize=9.6, va="center", color=INK, zorder=12)
    ax.text(219, -16.4, "Layout schematic, not to scale. Buses not shown. Data: MBTA V3 API. Coast: US Census TIGER/Line.",
            fontsize=7.2, color=INK, ha="right", va="top", zorder=12)
    (DAY / "output").mkdir(exist_ok=True)
    fig.savefig(DAY / "output/t_map.png", dpi=200, facecolor=PAPER)
    fig.savefig(DAY / "output/t_map.pdf", facecolor=PAPER)
    print("written")


if __name__ == "__main__":
    main()
