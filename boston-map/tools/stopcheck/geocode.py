import json, time, urllib.parse, urllib.request
Q = {
"East Arlington":"Capitol Theatre, Massachusetts Avenue, Arlington, MA","Arlington Ctr":"Arlington Center, Arlington, MA","Arlington Heights":"Arlington Heights, Arlington, MA",
"Lexington Ctr":"Lexington Center, Lexington, MA","Lexington Route 128":"Hartwell Avenue, Lexington, MA","Trapelo Rd":"Trapelo Road, Waltham, MA","Waltham":"Waltham station, Waltham, MA","Waverley Sq":"Waverley Square, Belmont, MA","Belmont Ctr":"Belmont Center, Belmont, MA",
"North Cambridge":"Rindge Avenue, Cambridge, MA","Wyoming Hill":"Wyoming Hill, Melrose, MA","Melrose Highlands":"Melrose Highlands, Melrose, MA","Greenwood":"Greenwood, Wakefield, MA","Wakefield":"Wakefield, MA","Reading":"Reading, MA",
"Linden Sq":"Linden Square, Malden, MA","Cliftondale":"Cliftondale Square, Saugus, MA","Saugus Center":"Saugus Center, Saugus, MA","East Saugus":"East Saugus, Saugus, MA",
"Dover":"East Berkeley Street, Boston, MA","Northampton":"Northampton Street, Boston, MA","Grove Hall":"Grove Hall, Boston, MA","Franklin Park":"Franklin Park, Boston, MA","Wellington Hill":"Wellington Hill, Mattapan, Boston, MA",
"Roslindale Village":"Roslindale Village, Boston, MA","Bellevue":"Bellevue, West Roxbury, Boston, MA","Highland":"Highland, West Roxbury, Boston, MA","West Roxbury":"West Roxbury, Boston, MA","VFW Parkway":"Spring Street, West Roxbury, Boston, MA","Hyde Park":"Hyde Park station, Boston, MA",
"Lynn Harbor":"Lynnway, Lynn, MA","Lynn":"Lynn, MA","Winthrop Center":"Winthrop Center, Winthrop, MA","Mass Ave (MIT)":"Massachusetts Institute of Technology, Cambridge, MA","West Station":"Beacon Park Yard, Allston, Boston, MA",
"Medford Hillside":"Medford Hillside, Medford, MA","West Medford":"West Medford, Medford, MA","Inman Sq":"Inman Square, Cambridge, MA","Allston":"Union Square, Allston, Boston, MA","Brighton Center":"Brighton Center, Boston, MA","Oak Sq":"Oak Square, Brighton, Boston, MA","Newton Corner":"Newton Corner, Newton, MA","Watertown":"Watertown Square, Watertown, MA",
"Hyde Sq":"Hyde Square, Jamaica Plain, Boston, MA","Needham Heights":"Needham Heights, Needham, MA","Needham Junction":"Needham Junction, Needham, MA","Hersey":"Hersey, Needham, MA",
"Logan Terminals":"Terminal B, Logan Airport, Boston, MA","Bellingham Sq":"Bellingham Square, Chelsea, MA","Everett Sq":"Everett Square, Everett, MA","Stadium":"Mystic Generating Station, Everett, MA","Encore":"Encore Boston Harbor, Everett, MA","Inner Belt":"Inner Belt Road, Somerville, MA","Binney":"Binney Street, Cambridge, MA","BU Bridge":"Boston University Bridge, Boston, MA","Landmark Center":"Landmark Center, Boston, MA","Mass & Cass":"Melnea Cass Boulevard, Boston, MA","Boston Medical":"Boston Medical Center, Boston, MA",
"Charlestown":"Bunker Hill Community College, Charlestown, Boston, MA","Navy Yard":"Charlestown Navy Yard, Boston, MA","City Square":"City Square, Charlestown, Boston, MA","North End":"Paul Revere Mall, North End, Boston, MA","Fort Point":"Fort Point, Boston, MA","Seaport":"Seaport Boulevard, Boston, MA","Convention Center":"Boston Convention and Exhibition Center, Boston, MA","City Point":"City Point, South Boston, MA","L Street":"L Street, South Boston, MA","West Broadway":"West Broadway, South Boston, MA",
"Fort Independence":"Fort Independence, Boston, MA",
}
out = {}
for k, q in Q.items():
    u = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "json", "limit": 1, "countrycodes": "us"})
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "30daymap-stop-check"}), timeout=20)
        d = json.load(r)
        out[k] = [float(d[0]["lat"]), float(d[0]["lon"]), d[0]["display_name"][:70]] if d else None
    except Exception as e:
        out[k] = None; print("fail", k, e)
    time.sleep(1.1)
json.dump(out, open("geo.json", "w"), indent=0)
print(sum(v is not None for v in out.values()), "of", len(out))
print("missing:", [k for k, v in out.items() if v is None])
