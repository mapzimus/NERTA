"""Spencer's Subway Builder network, transcribed from his game export.

Sources: bostonstations.geojson (stop positions) and BosNewTransit.pdf
(page 9 game diagram for stop order, page 2 and page 7 for transfer lists,
page 8 for the Orange Line A stop list). Both files are his, from the same
game save, so this is one source: his game. Treat it as the authority.

Stop names are the geojson names. DISPLAY fixes spelling and applies the
house abbreviations; the fixes are listed in data/name_fixes.md so Max can
check them with Spencer.
"""

ROUTES = {
    # code: (display name, color key, [stops in order])
    "RL-A": ("Red Line A", "red", [
        "North Lexington", "Lexington", "East Lexington", "Arlington Heights",
        "Arlington", "Dilboy", "Davis", "Porter Sq", "Harvard University",
        "Cambridge Square", "Kendall Square", "West End", "Bowdoin",
        "Government Center", "Downtown", "South Station", "Foundry",
        "South Boston", "Andrew", "Columbia", "Savin Hill", "Fields Corner",
        "Shawmut", "Peabody Sq", "Ashmont"]),
    "RL-B": ("Red Line B", "red", [
        "Belmont", "Cambridge Highlands", "Harvard University",
        "Cambridge Square", "Kendall Square", "West End", "Bowdoin",
        "Government Center", "Downtown", "South Station", "Foundry",
        "South Boston", "Andrew", "Columbia", "Savin Hill", "Neponset",
        "North Quincy", "Wollaston", "Quincy Center", "South Quincy",
        "Braintree", "Braintree South"]),
    "OL-A": ("Orange Line A", "orange", [
        "Dedham", "East Dedham", "Germantown", "West Roxbury", "Highland",
        "Bellevue", "Roslindale Village", "Forest Hills", "Green St",
        "Stony Brook", "Jackson Sq", "Roxbury Crossing", "Centennial",
        "Christian Plaza", "Back Bay", "Chinatown", "Downtown",
        "Government Center", "Haymarket", "North Station",
        "Bunker Hill College", "East Sommerville", "Assembly", "Supercollider",
        "Wellington", "Malden Center", "Oak Grove", "Melrose Center",
        "Greenwood", "Crystal", "Wakefield"]),
    "OL-B": ("Orange Line B", "orange", [
        "Readville", "Hyde Park", "Clarendon Hill", "Roslindale",
        "Forest Hills", "Green St", "Stony Brook", "Jackson Sq",
        "Roxbury Crossing", "Centennial", "Christian Plaza", "Back Bay",
        "Chinatown", "Waterfront", "North End", "North Station",
        "Bunker Hill College", "East Sommerville", "Casino", "Everett",
        "Woodlawn Cemetery", "Linden", "Franklin Park", "Square One Mall"]),
    "BL-A": ("Blue Line A", "blue", [
        "Fenway", "Storrow", "Esplanade", "Beacon Hill", "West End", "Bowdoin",
        "Government Center", "Waterfront", "Maverick", "Logan Airport",
        "Wood Island", "Constitution Beach", "Belle Isle Marsh",
        "Beachmont Square", "Wonderland", "Oak Island", "Point of Pines",
        "Lynn Interrim", "Lynn Center", "South Salem", "Central Salem", "North Salem",
        "Beverly"]),
    "BL-B": ("Blue Line B", "blue", [
        "Cambridge Square", "Kendall Square", "West End", "Bowdoin",
        "Government Center", "Waterfront", "Maverick", "East Boston",
        "Wood Island", "Constitution Beach", "Belle Isle Marsh",
        "Beachmont Square", "Wonderland", "Oak Island", "Point of Pines",
        "Lynn Interrim", "Lynn Center", "Wyoma", "Mt Hermon", "Peabody",
        "Danvers Central"]),
    "GL-A": ("Green Line A", "green", [
        "Brandeis University", "Cedarwood", "Waltham", "Bleachery",
        "Watertown", "Watertown Mall", "Market St", "West Station",
        "Boston University West", "Boston University East", "Fenway",
        "Storrow", "Esplanade", "Beacon Hill", "Bowdoin", "Science Park",
        "Lechemere", "Brickbottom", "Foss Park", "Ten Hills",
        "Mystic Valley Pkwy Connector", "Medford", "North Medford"]),
    "GL-B": ("Green Line B", "green", [
        "Southside Waltham", "Fessenden", "Newton Corner", "Oak Square",
        "Brighton", "West Station", "Boston University West",
        "Boston University East", "Fenway", "Storrow", "Esplanade",
        "Beacon Hill", "Bowdoin", "Science Park", "Lechemere", "Brickbottom",
        "Sommerville", "Magoun Sq", "Ball Sq", "Tufts University",
        "West Medford", "Wedgemere", "Winchester Center"]),
    "GL-C": ("Green Line C", "green", [
        "Lasell", "Auburndale", "Newton North", "Newtonville", "Ward Park",
        "Boston College North", "Aberdeen", "Warren St", "West Station",
        "Boston University West", "Boston University East", "Fenway",
        "Storrow", "Esplanade", "Beacon Hill", "Bowdoin", "Science Park",
        "Lechemere", "Brickbottom", "Sommerville", "Central Sommerville",
        "Davis", "Teele", "Alewife", "Orvis", "Kensington", "Belmont Hill",
        "Liberty Heights"]),
    "GL-D": ("Green Line D", "green", [
        "Upper Falls", "Highlands", "Newton Centre", "Boston College South",
        "Cleveland Circle", "Washington Square", "Coolidge Corner", "Fenway",
        "Hynes", "Copley", "Public Garden", "Boston Common",
        "Government Center", "Haymarket", "North Station", "Science Park",
        "Lechemere", "Union Square", "Spring Hill", "Porter Sq", "Avon Hill",
        "Cambridge Highlands"]),
    "GL-E": ("Green Line E", "green", [
        "Needham Heights", "Highland Ave", "Oak Hill", "Chestnut Hill Mall",
        "Chestnut Hill", "Reservoir", "Brookline", "Brookline Village",
        "Longwood", "Fenway", "Hynes", "Copley", "Public Garden",
        "Boston Common", "Government Center", "Haymarket", "North Station",
        "Science Park", "Lechemere", "Wellington Harrington", "Inman Square",
        "Harvard University", "Coolidge Hill", "Strawberry", "Cushing Square",
        "Waverley Square", "Bentley University"]),
    "GL-F": ("Green Line F", "green", [
        "Needham Heights", "Needham Center", "Needham Junction", "Millenium Park",
        "South Brookline", "Arborway", "Jamaica Pond", "Jamaica Plain",
        "Ohlmsted Park", "Riverway", "Mission Hill", "Museums",
        "Northeastern University", "Christian Plaza", "Prudential", "Copley",
        "Public Garden", "Boston Common", "Government Center", "North End"]),
    "YL": ("Yellow Line", "yellow", [
        "Back Bay", "Public Garden", "Beacon Hill", "West End", "Science Park",
        "North Station", "North End", "Waterfront", "Chinatown", "Essex",
        "Peters", "South End", "Nubian Square", "Roxbury", "Franklin Zoo",
        "Harambe", "Blue Hill", "Mattapan", "Upper Mills"]),
    "SL": ("Silver Line", "silver", [
        "Medford", "Fellsway", "Malden Center", "Faulkner", "Linden",
        "Squire Mall", "Revere Street", "Revere Center", "Mill Hill",
        "Chelsea Mall", "Orange - Addison", "Park Square", "Charlestown Yard",
        "Bunker Hill College", "Lechemere", "West End", "Beacon Hill",
        "Public Garden", "Chinatown", "South Station", "Fort Point",
        "Seaport", "Honor Park", "JFK Library"]),
    "TL": ("Teal Line", "teal", [
        "Logan Airport", "East Boston", "Eagle Hill", "Bellingham Square",
        "Orange - Addison", "Washington Park", "Everett", "Wellington",
        "Medford", "West Medford", "Dilboy", "Alewife", "Cambridge Highlands",
        "Coolidge Hill", "Allston", "West Station", "Brighton",
        "Boston College North", "Boston College South", "Reservoir",
        "Arborway", "Forest Hills", "Blue Hill", "Talbot", "Dorchester",
        "Meeting Hill", "Uphams Corner", "South Boston", "Convention Center",
        "Seaport"]),
    # Loops: the last stop connects back to the first.
    "VL": ("Violet Loop", "violet", [
        "Allston", "Riverside", "Cambridge Square",
        "Massachusetts Institute of Technology", "Storrow", "Hynes",
        "Christian Plaza", "South End", "Lucas E. Pequegnot", "South Boston",
        "Broadway", "Honor Park", "City Point", "JFK Library", "Savin Hill",
        "Meeting Hill", "Franklin Zoo", "Egleston Sq", "Stony Brook",
        "Jamaica Plain", "Brookline", "Beacon St", "Corey Hill",
        "West Station"]),
    "PL": ("Pink Loop", "pink", [
        "Harvard University", "Union Square", "East Sommerville",
        "Charlestown Yard", "Eagle Hill", "East Boston", "Logan Airport",
        "Honor Park", "JFK Library", "Columbia", "Uphams Corner",
        "Nubian Square", "Roxbury Crossing", "Mission Hill", "Longwood",
        "Coolidge Corner", "West Station", "Allston"]),
    # Brown Line North branches east of Winchester Center: one arm to
    # Marblehead via Melrose, one to Point Shirley via Malden. The game lists
    # both Malden and Melrose as Brown Line N, so it is drawn as one
    # branched route. Ask Spencer how it really runs.
    "BRN": ("Brown Line North", "brown", [
        "Southside Waltham", "Waltham", "Lexington", "Winchester Center",
        "North Medford", "Malden Center", "Woodlawn Cemetery",
        "Revere Center", "Beachmont Square", "Point Shirley"]),
    "BRN2": ("Brown Line North", "brown", [
        "Winchester Center", "Melrose Center", "Square One Mall",
        "Lynn Center", "Marblehead"]),
    "BRS": ("Brown Line South", "brown", [
        "Blue Hill", "Ashmont", "Quincy Center", "Whitmans Pond"]),
}

LOOPS = {"VL", "PL"}

# Regional rail. Reconstructed, NOT read from a game stop list: outer stops
# are the export points that sit on each purple line in his page 5 map, and
# the downtown stops come from the numbered pills on pages 2 and 7. Line
# numbers are matched to names by which downtown stops they share. Confirm
# with Spencer before calling these final.
REGIONAL = {
    "CR1": ("Worcester / Fitchburg Line", [
        "Worchester Central", "North Worchester", "Shrewsberry", "Northborough",
        "Florence St", "Southborough", "Ashland", "Framingham", "Natick",
        "Wellesley Central", "Wellesley Hill", "Newton", "West Station",
        "Back Bay", "Cambridge Square", "Concord", "Kelly Corner",
        "Leominster", "Fitchminster", "Fitchburg"]),
    "CR2": ("Manchester / Plymouth Line", [
        "Lowell", "Billerica", "Wilmington", "Woburn", "North Station",
        "Government Center", "South Station", "South Boston", "Savin Hill",
        "Quincy Center", "Weymouth", "Hingham", "Cohasset", "Scituate"]),
    "CR3": ("Haverhill / Cape Cod Line", [
        "Haverhill", "Lawrence", "Andover", "Reading", "Stoneham",
        "East Sommerville", "North Station", "Government Center",
        "South Station", "South Boston", "Savin Hill", "Milton", "Randolph",
        "Avon", "Brockton", "Bridgewater"]),
    "CR4": ("Portsmouth / New Bedford Line", [
        "Newburyport", "Topsfield", "Melrose Center", "Malden Center",
        "East Sommerville", "North Station", "Government Center",
        "South Station", "Back Bay", "Forest Hills", "Canton", "Stoughton",
        "Easton"]),
    "CR5": ("Rockport / Providence Line", [
        "Rockport", "Glouchester", "Manchester", "North Station",
        "Government Center", "South Station", "Back Bay", "Forest Hills",
        "Norwood", "Walpole", "Patriot Stadium", "Foxborough", "Mansfield"]),
}

# The export calls this stop Central Square; the game now calls it
# Cambridge Square.
GEO_ALIAS = {"Cambridge Square": "Central Square"}

DISPLAY = {
    "Lechemere": "Lechmere",
    "Sommerville": "Somerville",
    "Central Sommerville": "Central Somerville",
    "East Sommerville": "East Somerville",
    "Ohlmsted Park": "Olmsted Park",
    "Millenium Park": "Millennium Park",
    "Lynn Interrim": "Lynn Interim",
    "Jamacia Plain": "Jamaica Plain",
    "Glouchester": "Gloucester",
    "Worchester Central": "Worcester Center",
    "North Worchester": "North Worcester",
    "Shrewsberry": "Shrewsbury",
    "Patriot Stadium": "Foxborough Stadium",
    "Massachusetts Institute of Technology": "MIT",
    "Orange - Addison": "Orange-Addison",
    "Revere Street": "Revere St",
    "Cambridge Square": "Cambridge Sq",
    "Kendall Square": "Kendall Sq",
    "Union Square": "Union Sq",
    "Inman Square": "Inman Sq",
    "Washington Square": "Washington Sq",
    "Nubian Square": "Nubian Sq",
    "Beachmont Square": "Beachmont Sq",
    "Bellingham Square": "Bellingham Sq",
    "Park Square": "Park Sq",
    "Oak Square": "Oak Sq",
    "Cushing Square": "Cushing Sq",
    "Waverley Square": "Waverley Sq",
    "Square One Mall": "Square One Mall",
}


def display(name):
    return DISPLAY.get(name, name.strip())
