"""A working web map in real geography for deciding the NERTA tram network (Max, November 7).

python make_tram_realmap.py            -> output/copies/tram_realmap_vN.html (never overwrites)

Layers: NERTA stations at their real spots (data/tram/stations_real.geojson) linked station to station in line colors,
today's frequent buses (data/tram/bus_routes.geojson), and the draft tram routes in hot pink.
The draft lives in data/tram/tram_draft.json. If that file is missing, a first draft is built from the bus shapes:
each tram runs its bus corridor, with stops at every NERTA station it passes and about every 650 m between them.
Edit the json by hand after review; this script only redraws it.
"""
import json
import math
import re
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, mapping, shape

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import make_tmap as M  # noqa: E402  (read only)

DAY = Path(__file__).resolve().parents[1]
TD = DAY / "data" / "tram"
OUT = DAY / "output" / "copies"
TRAM = "#e0457b"   # hot pink (Max, November 7). CIEDE2000 20.5 or more from every NERTA color.
CODE = {M.RED: "RL", M.ORANGE: "OL", M.BLUE: "BL", M.GREEN: "GL", M.YELLOW: "YL", M.CYAN: "CL", M.INDIGO: "IL", M.SILVER: "SL",
        M.CR_TEXT_COLOR: "CR"}

# First draft: the gap corridors in research/bus-exploration-2026-11-07.md, sections 2b and 4. The 73 is left off
# (it overlaps the rejected Trapelo Rd stop); the 70 and 16 are added (planned frequent routes on gap corridors).
DRAFT = [
    ("66", "Harvard St", "Harvard to Nubian via Allston, Coolidge Corner and Brookline Village"),
    ("1", "Mass Ave", "Harvard to Nubian via MIT, Back Bay and the South End"),
    ("70", "Western Ave and Arsenal St", "Central to Waltham via Watertown Sq"),
    ("71", "Mt Auburn St", "Watertown Sq to Harvard"),
    ("16", "Columbia Rd", "Andrew to Forest Hills via Uphams Corner, Grove Hall and Franklin Park"),
    ("15", "Dudley St", "Fields Corner to Ruggles via Uphams Corner and Nubian"),
    ("22", "Talbot Ave and Columbus Ave", "Ashmont to Ruggles via Codman Sq and Jackson Sq"),
    ("23", "Washington St, Dorchester", "Ashmont to Ruggles via Codman Sq, Grove Hall and Nubian"),
    ("31", "Morton St", "Mattapan to Forest Hills"),
    ("9", "Broadway", "City Point to Copley via the South End"),
    ("111", "Chelsea", "Woodlawn to Haymarket over the Tobin Bridge"),
    ("116", "Inland Revere", "Wonderland to Maverick via Revere and Chelsea"),
    ("110", "Revere and Everett", "Wonderland to Wellington via Everett Sq"),
]
SPACING = 650   # meters between tram stops, roughly
XFER_M = 250    # a NERTA station this close to the line becomes a tram stop


def xy(lon, lat):
    """Meters on a local plane around Boston."""
    return ((lon + 71.06) * 111320 * math.cos(math.radians(42.36)), (lat - 42.36) * 110540)


def lonlat(x, y):
    return (x / (111320 * math.cos(math.radians(42.36))) - 71.06, y / 110540 + 42.36)


def to_m(geom):
    if geom.geom_type == "Point":
        return Point(xy(geom.x, geom.y))
    return LineString([xy(*c) for c in geom.coords])


def tidy(name):
    """'Massachusetts Ave @ Sidney St' -> 'Sidney St'."""
    for sep in (" @ ", " opp ", " before ", " after ", " at "):
        if sep in name:
            name = name.split(sep)[-1]
            break
    for a, b in ((" Street", " St"), (" Square", " Sq"), (" Avenue", " Ave"), (" Road", " Rd"), ("Massachusetts", "Mass")):
        name = name.replace(a, b)
    return re.sub(r"\s+", " ", name.replace(" Station", "")).strip()


def build_draft(stations, buses, bstops):
    routes = []
    for rid, title, via in DRAFT:
        shapes = [f for f in buses if f["properties"]["route"] == rid]
        if not shapes:
            print("no bus shape for", rid)
            continue
        line = max((to_m(shape(f["geometry"])) for f in shapes), key=lambda g: g.length)
        stops = []
        for s in stations:
            p = to_m(shape(s["geometry"]))
            if line.distance(p) <= XFER_M:
                codes = sorted({CODE.get(c, "?") for c in s["properties"]["colors"]}, key=list(CODE.values()).index)
                stops.append(dict(name=s["properties"]["name"], at=line.project(p), nerta=True, pills=codes,
                                  lonlat=lonlat(*line.interpolate(line.project(p)).coords[0])))
        cands = []
        for b in bstops:
            if rid not in b["properties"]["routes"]:
                continue
            p = to_m(shape(b["geometry"]))
            if line.distance(p) <= 60:
                cands.append(dict(name=tidy(b["properties"]["name"]), at=line.project(p), nerta=False, pills=[],
                                  lonlat=(b["geometry"]["coordinates"][0], b["geometry"]["coordinates"][1]), bus_name=b["properties"]["name"]))
        cands.sort(key=lambda c: c["at"])
        for end in (cands[:1], cands[-1:]):
            for c in end:
                if all(abs(c["at"] - s["at"]) > 300 for s in stops):
                    stops.append(c)
        for c in cands:
            if all(abs(c["at"] - s["at"]) >= SPACING for s in stops):
                stops.append(c)
        stops.sort(key=lambda s: s["at"])
        routes.append(dict(id=rid, name=title, via=via, bus_route=rid, status="draft",
                           path=[lonlat(*c) for c in line.simplify(4).coords],
                           stops=[{k: v for k, v in s.items() if k != "at"} for s in stops]))
        print(f"tram {rid:4s} {title:30s} {line.length / 1000:5.1f} km  {len(stops)} stops")
    return routes


def nerta_links(stations):
    """Each NERTA line as straight links between its stations at their real spots."""
    pos = {s["properties"]["name"]: s["geometry"]["coordinates"] for s in stations}
    out = []
    for color, style, _path, stops in M.lines():
        pts = [pos[n.rstrip("+")] for n in stops if n.rstrip("+") in pos]
        if len(pts) > 1:
            out.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": pts}, "properties": {"color": color, "style": style}})
    return out


PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NERTA Trams, Real Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root { --ink:#16161a; --paper:#fcfcfa; --pink:%(TRAM)s; --mute:#5b616b; --panel:#ffffffee; }
html,body { margin:0; height:100%%; background:var(--paper); font-family: Arial, Helvetica, sans-serif; color:var(--ink); }
#map { position:absolute; inset:0; }
.panel { position:absolute; z-index:1000; background:var(--panel); border:1px solid #c9d3d3; border-radius:10px; padding:10px 12px;
         box-shadow:0 2px 8px #0002; font-size:13px; }
#side { top:10px; right:10px; width:310px; max-height:calc(100%% - 40px); overflow:auto; }
#side h1 { font-size:17px; margin:0 0 2px; } #side .sub { color:var(--mute); margin:0 0 8px; font-size:12px; }
.route { display:flex; gap:8px; align-items:flex-start; padding:5px 0; border-top:1px solid #eee; cursor:pointer; }
.route:hover { background:#fff0f5; }
.badge { flex:none; min-width:34px; text-align:center; background:var(--pink); color:#fff; font-weight:bold; border-radius:12px; padding:2px 6px; }
.route small { color:var(--mute); display:block; }
.legend div { display:flex; gap:8px; align-items:center; margin:3px 0; }
.sw { width:28px; height:0; border-top:5px solid var(--pink); } .sw.bus { border-top:2px solid #6b7280; }
.sw.nerta { border-top:4px solid #da291c99; } .dot { width:10px; height:10px; border-radius:50%%; border:2px solid var(--ink); background:#fff; }
.dot.hand { border-color:#e67e00; border-style:dashed; } .dot.tram { border-color:var(--pink); }
#spot { left:10px; bottom:22px; max-width:420px; } #spot code { font-size:12px; }
.pill { display:inline-block; font-size:10px; font-weight:bold; color:#fff; border-radius:7px; padding:0 5px; margin-left:2px; }
.leaflet-tooltip.stopname { font-size:11px; padding:1px 4px; }
</style></head><body>
<div id="map"></div>
<div class="panel" id="side">
  <h1>NERTA Trams, Real Map</h1>
  <p class="sub">Draft v%(V)s, %(DATE)s. Working map, not for posting. Click a route to zoom to it; click any spot on the map to get its coordinates.</p>
  <div class="legend">
    <div><span class="sw"></span>Draft tram route (hot pink)</div>
    <div><span class="dot tram"></span>Draft tram stop</div>
    <div><span class="sw bus"></span>Today's frequent bus</div>
    <div><span class="sw nerta"></span>NERTA line, station to station</div>
    <div><span class="dot"></span>NERTA station, two sources</div>
    <div><span class="dot hand"></span>NERTA station placed by hand or one source</div>
  </div>
  <div id="routes"></div>
</div>
<div class="panel" id="spot">Click the map to get a spot.</div>
<script>
const DATA = %(DATA)s;
const PILL = %(PILL)s;
const map = L.map('map', {zoomControl:true, preferCanvas:false}).setView([42.355, -71.07], 12);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {maxZoom:19, subdomains:'abcd',
  attribution:'&copy; OpenStreetMap contributors &copy; CARTO'}).addTo(map);
const gNerta = L.layerGroup().addTo(map), gBus = L.layerGroup().addTo(map), gTram = L.layerGroup().addTo(map), gSta = L.layerGroup().addTo(map);
const pills = codes => codes.map(c => `<span class="pill" style="background:${PILL[c]||'#888'};${c==='YL'?'color:#16161a':''}">${c}</span>`).join('');
DATA.nerta.forEach(f => L.polyline(f.geometry.coordinates.map(c => [c[1], c[0]]), {color:f.properties.color, weight:4, opacity:0.45,
  dashArray: f.properties.style==='dash' ? '8 6' : null}).addTo(gNerta));
DATA.buses.forEach(f => L.polyline(f.geometry.coordinates.map(c => [c[1], c[0]]), {color:'#6b7280', weight:2, opacity:0.7})
  .bindTooltip(`Bus ${f.properties.route}: ${f.properties.long_name}`, {sticky:true}).addTo(gBus));
DATA.stations.forEach(f => {
  const p = f.properties, two = p.verified;
  L.circleMarker([f.geometry.coordinates[1], f.geometry.coordinates[0]], {radius:5, color: two ? '#16161a' : '#e67e00', weight:2,
    dashArray: two ? null : '3 2', fillColor:'#fff', fillOpacity:1})
   .bindTooltip(`<b>${p.name}</b> ${pills(p.colors.map(c => DATA.code[c]||'?'))}<br>${p.sources.join(' + ')}${p.note ? '<br>'+p.note : ''}`)
   .addTo(gSta);
});
const routeLayers = {};
DATA.trams.forEach(r => {
  const ll = r.path.map(c => [c[1], c[0]]);
  const casing = L.polyline(ll, {color:'#fff', weight:10, opacity:0.9}).addTo(gTram);
  const line = L.polyline(ll, {color:'%(TRAM)s', weight:6, opacity:0.95}).bindTooltip(`<b>${r.id} ${r.name}</b><br>${r.via}`, {sticky:true}).addTo(gTram);
  routeLayers[r.id] = line;
  r.stops.forEach(s => L.circleMarker([s.lonlat[1], s.lonlat[0]], {radius: s.nerta ? 6 : 4, color: s.nerta ? '#16161a' : '%(TRAM)s', weight:2,
      fillColor:'#fff', fillOpacity:1})
    .bindTooltip(`<b>${s.name}</b> ${pills(s.pills)}<br>Tram ${r.id}${s.bus_name ? '<br>bus stop: '+s.bus_name : ''}`, {className:'stopname'}).addTo(gTram));
  const el = document.createElement('div');
  el.className = 'route';
  el.innerHTML = `<span class="badge">${r.id}</span><div><b>${r.name}</b><small>${r.via}. ${r.stops.length} stops</small></div>`;
  el.onclick = () => map.fitBounds(line.getBounds(), {padding:[40,40]});
  document.getElementById('routes').appendChild(el);
});
L.control.layers(null, {'Draft trams': gTram, 'Frequent buses today': gBus, 'NERTA lines': gNerta, 'NERTA stations': gSta},
  {position:'topleft', collapsed:false}).addTo(map);
map.on('click', e => {
  const t = `${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}`;
  document.getElementById('spot').innerHTML = `Spot: <code>${t}</code> (copy this into chat to point at a place)`;
});
</script></body></html>
"""


def main():
    stations = json.loads((TD / "stations_real.geojson").read_text(encoding="utf-8"))["features"]
    buses = json.loads((TD / "bus_routes.geojson").read_text(encoding="utf-8"))["features"]
    bstops = json.loads((TD / "bus_stops.geojson").read_text(encoding="utf-8"))["features"]
    dpath = TD / "tram_draft.json"
    if dpath.exists():
        trams = json.loads(dpath.read_text(encoding="utf-8"))["routes"]
    else:
        trams = build_draft(stations, buses, bstops)
        dpath.write_text(json.dumps({"color": TRAM, "routes": trams}, indent=1), encoding="utf-8")
        print("wrote", dpath)
    v = 1
    while (OUT / f"tram_realmap_v{v}.html").exists():
        v += 1
    data = {"stations": stations, "buses": buses, "trams": trams, "nerta": nerta_links(stations), "code": CODE}
    pill = {"RL": M.RED, "OL": M.ORANGE, "BL": M.BLUE, "GL": M.GREEN, "YL": M.YELLOW, "CL": M.CYAN, "IL": M.INDIGO, "SL": M.SILVER, "CR": M.CR_TEXT_COLOR}
    html = PAGE % {"TRAM": TRAM, "V": v, "DATE": "November 7, 2026", "DATA": json.dumps(data), "PILL": json.dumps(pill)}
    out = OUT / f"tram_realmap_v{v}.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
