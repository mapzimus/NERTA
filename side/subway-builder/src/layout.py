"""Schematic stop positions, read off Spencer's own game diagram (PDF page 9).

Each entry is (tile row, tile col, x, y) in the 0.55-scale tiles used while
transcribing. pos() turns them into full-resolution diagram pixels, then into
map units (y up).
"""

T = {
    # row 0
    "North Lexington": (0, 0, 229, 580), "Lexington": (0, 0, 350, 612),
    "East Lexington": (0, 0, 555, 612), "Arlington Heights": (0, 0, 1031, 771),
    "Arlington": (0, 0, 1265, 1005),
    "Winchester Center": (0, 1, 128, 745), "Wedgemere": (0, 1, 145, 778),
    "West Medford": (0, 1, 362, 1003), "North Medford": (0, 1, 1028, 886),
    "Fellsway": (0, 1, 1395, 1005),
    "Malden Center": (0, 2, 260, 993), "Oak Grove": (0, 2, 375, 760),
    "Melrose Center": (0, 2, 395, 608), "Greenwood": (0, 2, 393, 532),
    "Crystal": (0, 2, 400, 492), "Wakefield": (0, 2, 415, 422),
    "Faulkner": (0, 2, 648, 877), "Linden": (0, 2, 1050, 870),
    "Woodlawn Cemetery": (0, 2, 903, 1003), "Franklin Park": (0, 2, 1227, 686),
    "Square One Mall": (0, 2, 1287, 615), "Squire Mall": (0, 2, 1460, 915),
    "Revere Street": (0, 3, 250, 1100), "Wonderland": (0, 3, 415, 1150),
    "Oak Island": (0, 3, 570, 972), "Point of Pines": (0, 3, 730, 812),
    "Lynn Interrim": (0, 3, 925, 612), "Lynn Center": (0, 3, 935, 485),
    "Wyoma": (0, 3, 923, 456), "Mt Hermon": (0, 3, 923, 393),
    "Peabody": (0, 3, 923, 355), "Danvers Central": (0, 3, 1015, 167),
    "South Salem": (0, 3, 1182, 350), "Central Salem": (0, 3, 1200, 331),
    "North Salem": (0, 3, 1218, 313), "Beverly": (0, 3, 1270, 233),
    "Marblehead": (0, 3, 1377, 421),
    # row 1
    "Liberty Heights": (1, 0, 474, 25), "Belmont Hill": (1, 0, 638, 244),
    "Belmont": (1, 0, 783, 474), "Kensington": (1, 0, 992, 477),
    "Orvis": (1, 0, 1157, 477), "Bentley University": (1, 0, 345, 553),
    "Waverley Square": (1, 0, 562, 803), "Cushing Square": (1, 0, 845, 985),
    "Strawberry": (1, 0, 1124, 985),
    "Dilboy": (1, 1, 117, 215), "Alewife": (1, 1, 115, 475),
    "Teele": (1, 1, 277, 478), "Davis": (1, 1, 528, 485),
    "Central Sommerville": (1, 1, 687, 481), "Cambridge Highlands": (1, 1, 113, 605),
    "Avon Hill": (1, 1, 318, 603), "Porter Sq": (1, 1, 626, 601),
    "Tufts University": (1, 1, 643, 233), "Ball Sq": (1, 1, 797, 385),
    "Magoun Sq": (1, 1, 890, 471), "Mystic Valley Pkwy Connector": (1, 1, 1057, 243),
    "Ten Hills": (1, 1, 1278, 473), "Foss Park": (1, 1, 1283, 638),
    "Sommerville": (1, 1, 1133, 722), "Spring Hill": (1, 1, 819, 790),
    "Coolidge Hill": (1, 1, 112, 989), "Harvard University": (1, 1, 628, 995),
    "Union Square": (1, 1, 1036, 993), "Brickbottom": (1, 1, 1278, 980),
    "Medford": (1, 1, 1018, 82),
    "Wellington": (1, 2, 260, 95), "Supercollider": (1, 2, 264, 295),
    "Assembly": (1, 2, 264, 543), "East Sommerville": (1, 2, 270, 858),
    "Casino": (1, 2, 614, 519), "Everett": (1, 2, 778, 212),
    "Washington Park": (1, 2, 880, 318), "Orange - Addison": (1, 2, 1030, 463),
    "Park Square": (1, 2, 1098, 660), "Bellingham Square": (1, 2, 1158, 665),
    "Eagle Hill": (1, 2, 1170, 1000), "Chelsea Mall": (1, 2, 1237, 260),
    "Bunker Hill College": (1, 2, 400, 995), "Charlestown Yard": (1, 2, 775, 982),
    "East Boston": (1, 2, 1278, 1118), "Wood Island": (1, 2, 1425, 993),
    "Mill Hill": (1, 3, 77, 212), "Revere Center": (1, 3, 260, 205),
    "Beachmont Square": (1, 3, 420, 511), "Belle Isle Marsh": (1, 3, 378, 640),
    "Constitution Beach": (1, 3, 225, 793),
    # row 2
    "Cedarwood": (2, 0, 187, 115), "Waltham": (2, 0, 232, 88),
    "Brandeis University": (2, 0, 110, 447), "Bleachery": (2, 0, 337, 179),
    "Southside Waltham": (2, 0, 234, 332), "Watertown": (2, 0, 603, 444),
    "Fessenden": (2, 0, 413, 503), "Newton Corner": (2, 0, 603, 693),
    "Watertown Mall": (2, 0, 1124, 713), "Market St": (2, 0, 1333, 711),
    "Oak Square": (2, 0, 908, 835), "Brighton": (2, 0, 1276, 836),
    "Lasell": (2, 0, 193, 857), "Auburndale": (2, 0, 333, 953),
    "Newton North": (2, 0, 438, 1057), "Newtonville": (2, 0, 480, 1100),
    "Ward Park": (2, 0, 741, 1105), "Boston College North": (2, 0, 1004, 1100),
    "Aberdeen": (2, 0, 1290, 1070),
    "Allston": (2, 1, 245, 490), "West Station": (2, 1, 240, 717),
    "Riverside": (2, 1, 723, 344), "Cambridge Square": (2, 1, 1030, 345),
    "Kendall Square": (2, 1, 1378, 455), "Massachusetts Institute of Technology": (2, 1, 1215, 545),
    "Boston University West": (2, 1, 590, 708), "Boston University East": (2, 1, 908, 708),
    "Fenway": (2, 1, 1160, 830), "Warren St": (2, 1, 84, 882),
    "Corey Hill": (2, 1, 253, 940), "Storrow": (2, 1, 1385, 712),
    "Hynes": (2, 1, 1405, 848), "Christian Plaza": (2, 1, 1397, 975),
    "Northeastern University": (2, 1, 1268, 975), "Coolidge Corner": (2, 1, 512, 985),
    "Inman Square": (2, 1, 1048, 121), "Wellington Harrington": (2, 1, 1400, 222),
    "Lechemere": (2, 2, 262, 90), "Science Park": (2, 2, 480, 305),
    "North Station": (2, 2, 655, 325), "North End": (2, 2, 782, 330),
    "Haymarket": (2, 2, 645, 420), "Government Center": (2, 2, 628, 470),
    "West End": (2, 2, 357, 460), "Bowdoin": (2, 2, 522, 455),
    "Waterfront": (2, 2, 772, 470), "Downtown": (2, 2, 647, 570),
    "Boston Common": (2, 2, 505, 605), "Esplanade": (2, 2, 155, 715),
    "Beacon Hill": (2, 2, 262, 730), "Public Garden": (2, 2, 362, 852),
    "Copley": (2, 2, 217, 848), "Prudential": (2, 2, 132, 965),
    "Back Bay": (2, 2, 264, 975), "Chinatown": (2, 2, 530, 733),
    "South Station": (2, 2, 650, 720), "Fort Point": (2, 2, 850, 718),
    "Seaport": (2, 2, 1030, 855), "Convention Center": (2, 2, 868, 1010),
    "Essex": (2, 2, 537, 870), "Peters": (2, 2, 465, 1048),
    "Foundry": (2, 2, 645, 995), "Maverick": (2, 2, 1020, 352),
    "Logan Airport": (2, 2, 1418, 322),
    "Point Shirley": (2, 3, 725, 567),
    # row 3
    "Boston College South": (3, 0, 1114, 188), "Cleveland Circle": (3, 0, 1260, 195),
    "Chestnut Hill": (3, 0, 1178, 325), "Reservoir": (3, 0, 1408, 330),
    "Newton Centre": (3, 0, 720, 471), "Chestnut Hill Mall": (3, 0, 795, 530),
    "Highlands": (3, 0, 530, 661), "Oak Hill": (3, 0, 512, 812),
    "Upper Falls": (3, 0, 355, 867), "Highland Ave": (3, 0, 255, 1068),
    "Needham Heights": (3, 0, 236, 1087), "Needham Junction": (3, 0, 295, 1090),
    "Needham Center": (3, 0, 264, 1090), "Millenium Park": (3, 0, 818, 1090),
    "South Brookline": (3, 0, 1236, 1090),
    "Washington Square": (3, 1, 175, 195), "Brookline": (3, 1, 381, 320),
    "Brookline Village": (3, 1, 645, 186), "Longwood": (3, 1, 762, 67),
    "Mission Hill": (3, 1, 895, 193), "Riverway": (3, 1, 814, 262),
    "Ohlmsted Park": (3, 1, 700, 378), "Jamaica Plain": (3, 1, 633, 573),
    "Jamaica Pond": (3, 1, 575, 759), "Arborway": (3, 1, 505, 836),
    "Stony Brook": (3, 1, 1020, 698), "Egleston Sq": (3, 1, 1133, 820),
    "Jackson Sq": (3, 1, 1160, 568), "Green St": (3, 1, 883, 840),
    "Roxbury Crossing": (3, 1, 1280, 190), "Centennial": (3, 1, 1278, 117),
    "Beacon St": (3, 1, 375, 62), "Museums": (3, 1, 1130, 70),
    "South End": (3, 2, 268, 193), "Lucas E. Pequegnot": (3, 2, 340, 192),
    "South Boston": (3, 2, 655, 180), "Broadway": (3, 2, 903, 188),
    "Honor Park": (3, 2, 1155, 192), "City Point": (3, 2, 1307, 187),
    "Nubian Square": (3, 2, 143, 323), "Andrew": (3, 2, 648, 305),
    "Uphams Corner": (3, 2, 396, 578), "Columbia": (3, 2, 645, 575),
    "JFK Library": (3, 2, 905, 575), "Roxbury": (3, 2, 140, 632),
    "Savin Hill": (3, 2, 653, 855), "Franklin Zoo": (3, 2, 140, 955),
    "Meeting Hill": (3, 2, 387, 955), "Dorchester": (3, 2, 390, 1045),
    # row 4
    "Bellevue": (4, 0, 1247, 313), "Highland": (4, 0, 1138, 422),
    "West Roxbury": (4, 0, 1043, 519), "Germantown": (4, 0, 1003, 559),
    "East Dedham": (4, 0, 960, 604), "Dedham": (4, 0, 895, 756),
    "Forest Hills": (4, 1, 757, 60), "Roslindale Village": (4, 1, 280, 178),
    "Roslindale": (4, 1, 507, 312), "Clarendon Hill": (4, 1, 375, 443),
    "Hyde Park": (4, 1, 251, 746), "Readville": (4, 1, 251, 797),
    "Harambe": (4, 1, 1275, 240), "Blue Hill": (4, 1, 1279, 433),
    "Mattapan": (4, 1, 1273, 624), "Upper Mills": (4, 1, 1235, 730),
    "Fields Corner": (4, 2, 654, 50), "Shawmut": (4, 2, 654, 200),
    "Peabody Sq": (4, 2, 559, 404), "Ashmont": (4, 2, 396, 571),
    "Neponset": (4, 2, 1063, 212), "North Quincy": (4, 2, 1282, 429),
    "Wollaston": (4, 2, 1446, 591), "Talbot": (4, 2, 253, 186),
    "Quincy Center": (4, 3, 286, 705), "South Quincy": (4, 3, 285, 826),
    "Braintree": (4, 3, 287, 868), "Braintree South": (4, 3, 310, 931),
    "Whitmans Pond": (4, 3, 956, 931),
}


def full(name):
    r, c, x, y = T[name]
    return 200 + c * 2536 - 150 + x / 0.55, 3700 + r * 1890 - 150 + y / 0.55


def pos(name, unit=10.0):
    """Map units: 1 unit = 10 full-res diagram pixels, y up."""
    fx, fy = full(name)
    return fx / unit, -fy / unit


# Bend points for long links, in the same tile coordinates (no stop there).
VIA = {
    ("Lexington", "Winchester Center"): [(0, 0, 465, 487), (0, 0, 890, 487), (0, 0, 1150, 742)],
    ("Waltham", "Lexington"): [(0, 0, 230, 735)],
    ("Winchester Center", "Melrose Center"): [(0, 1, 880, 742), (0, 1, 1010, 612)],
    ("Winchester Center", "North Medford"): [(0, 1, 880, 742)],
    ("North Medford", "Malden Center"): [(0, 1, 1140, 995)],
    ("Woodlawn Cemetery", "Revere Center"): [(0, 2, 1420, 1000)],
    ("Revere Center", "Beachmont Square"): [(1, 3, 400, 340)],
    ("Beachmont Square", "Point Shirley"): [(1, 3, 658, 770), (2, 3, 658, 450)],
    ("Square One Mall", "Lynn Center"): [(0, 3, 912, 610)],
    ("Lynn Center", "Marblehead"): [(0, 3, 1290, 490)],
    ("Blue Hill", "Ashmont"): [(4, 2, 230, 443)],
    ("Ashmont", "Quincy Center"): [(4, 2, 525, 700)],
    ("Quincy Center", "Whitmans Pond"): [(4, 3, 660, 700), (4, 3, 900, 930)],
}


def tile_to_units(r, c, x, y, unit=10.0):
    fx, fy = 200 + c * 2536 - 150 + x / 0.55, 3700 + r * 1890 - 150 + y / 0.55
    return fx / unit, -fy / unit


def snapped(names, edges, rounds=6, tol_deg=7):
    """Positions with near-straight links made exactly 0, 45 or 90 degrees."""
    import math
    import numpy as np
    P = {n: np.array(pos(n), float) for n in names}
    for _ in range(rounds):
        for kind in ("h", "v", "d1", "d2"):
            parent = {n: n for n in P}
            def find(a):
                while parent[a] != a:
                    parent[a] = parent[parent[a]]
                    a = parent[a]
                return a
            for a, b in edges:
                if a not in P or b not in P:
                    continue
                d = P[b] - P[a]
                ang = math.degrees(math.atan2(d[1], d[0])) % 180
                want = {"h": 0, "v": 90, "d1": 45, "d2": 135}[kind]
                diff = min(abs(ang - want), 180 - abs(ang - want))
                if diff < tol_deg and np.hypot(*d) > 0.5:
                    parent[find(a)] = find(b)
            groups = {}
            for n in P:
                groups.setdefault(find(n), []).append(n)
            for g in groups.values():
                if len(g) < 2:
                    continue
                if kind == "h":
                    m = np.mean([P[n][1] for n in g])
                    for n in g: P[n][1] = m
                elif kind == "v":
                    m = np.mean([P[n][0] for n in g])
                    for n in g: P[n][0] = m
                elif kind == "d1":  # y - x constant
                    m = np.mean([P[n][1] - P[n][0] for n in g])
                    for n in g:
                        k = P[n][1] - P[n][0] - m
                        P[n][0] += k / 2; P[n][1] -= k / 2
                else:  # y + x constant
                    m = np.mean([P[n][1] + P[n][0] for n in g])
                    for n in g:
                        k = P[n][1] + P[n][0] - m
                        P[n][0] -= k / 2; P[n][1] -= k / 2
    return P
