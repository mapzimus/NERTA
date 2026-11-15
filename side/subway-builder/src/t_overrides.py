"""Hand adjustments to the automatic T-style layout. Units are map units."""

# exact spots for the downtown core
PLACE = {
    "West End": (116, -212), "Bowdoin": (141, -212), "Government Center": (165, -212),
    "Waterfront": (190, -212), "Science Park": (141, -184), "North Station": (165, -184),
    "North End": (190, -184), "Downtown": (165, -232), "South Station": (165, -252),
    "Chinatown": (145, -252), "Public Garden": (130, -258), "Copley": (112, -258),
    "Hynes": (96, -258), "Fenway": (80, -258), "Storrow": (96, -240),
    "Beacon Hill": (116, -240), "Back Bay": (121, -276), "Christian Plaza": (96, -276),
}
MOVE = {
    "Cambridge Highlands": (0, -9), "Porter Sq": (0, -9),
    "Needham Heights": (-8, 0),
}
# branch ends: terminal -> list of (angle, steps); one step is one stop spacing
RAYS = {
    "Liberty Heights": [(135, 4)],
    "Belmont": [(180, 2.4)],
    "Bentley University": [(225, 4)],
    "Lasell": [(180, 1), (135, 4)],
    "Upper Falls": [(225, 3)],
    "Dedham": [(225, 7)],
    "Readville": [(270, 4)],
    "Braintree South": [(270, 3)],
    "Whitmans Pond": [(0, 2.4)],
    "Point Shirley": [(-45, 1.8)],
    "Danvers Central": [(90, 4)],
    "Beverly": [(45, 4)],
    "Marblehead": [(0, 2.4)],
    "Wakefield": [(90, 3)],
    "North Lexington": [(180, 1.6)],
}
BENDS = {
    ("Chinatown", "Waterfront"): "last",
}
VIA = {}
