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
# Max added these 19 (November 7) from the ranked candidates: busy routes meeting the subway or commuter rail, mostly new ground.
# Names are drafts; the stop-naming pass polishes them.
EXTRA = [
    ("216", "Houghs Neck", "Quincy Center to Houghs Neck via Germantown"),
    ("101", "Medford Sq", "Malden Center to Sullivan Sq via Medford Sq"),
    ("34", "Dedham", "Forest Hills to Dedham Mall via Washington St"),
    ("34E", "Walpole", "Forest Hills to Walpole Center via Washington St, Dedham and Norwood"),
    ("225", "Weymouth Landing", "Quincy Center to Weymouth Landing"),
    ("100", "Fellsway", "Wellington to Elm St, Medford, via the Fellsway"),
    ("222", "East Weymouth", "Quincy Center to East Weymouth"),
    ("64", "Oak Sq", "Oak Sq to Kendall via Allston and Central Sq"),
    ("240", "Randolph", "Ashmont to Avon Sq via Randolph"),
    ("220", "Hingham", "Quincy Center to Hingham Depot"),
    ("455", "Lynn and Salem", "Wonderland to Salem via Lynn and Swampscott"),
    ("215", "West Quincy", "Ashmont to Quincy Center via West Quincy"),
    ("95", "Mystic Ave", "Sullivan Sq to West Medford via Mystic Ave"),
    ("75", "Huron Ave", "Harvard to Belmont Center via Huron Ave"),
    ("712", "Winthrop", "Orient Heights to Point Shirley via Winthrop"),
    ("78", "Arlmont", "Harvard to Arlmont Village via Park Circle"),
    ("106", "Lebanon St", "Wellington to Lebanon St via Malden Center"),
    ("60", "Route 9", "Kenmore to Chestnut Hill via Brookline Village"),
    ("38", "Centre St, West Roxbury", "Forest Hills to Wren St via Centre St"),
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


def build_draft(stations, buses, bstops, spec=None):
    routes = []
    for rid, title, via in (spec or DRAFT):
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


def rank_candidates(stations, trams):
    """More trams (Max, November 7): major routes that meet the subway, and ones that meet commuter rail.
    Every bus route not already a tram, ranked by weekday trips, with how much of it NERTA rail or a tram already covers."""
    from shapely.ops import unary_union
    import geopandas as gpd
    path = TD / "bus_all.geojson"
    if not path.exists():
        return []
    taken = {r["bus_route"] for r in trams} | {"73"}   # the 73 overlaps the rejected Trapelo Rd stop
    pos = {s["properties"]["name"]: s for s in stations}
    rapid = [(n, to_m(shape(s["geometry"]))) for n, s in pos.items() if any(c != M.CR_TEXT_COLOR for c in s["properties"]["colors"])]
    mb = gpd.read_file(DAY / "data/mbta_stops.gpkg")
    cr = {r["name"]: Point(xy(r.geometry.x, r.geometry.y)) for _, r in mb.iterrows() if "CR-" in r["routes"]}
    for n, s in pos.items():
        if M.CR_TEXT_COLOR in s["properties"]["colors"]:
            cr.setdefault(n, to_m(shape(s["geometry"])))
    links = []
    for color, _style, _path, stops in M.lines():
        pts = [to_m(shape(pos[n.rstrip("+")]["geometry"])).coords[0] for n in stops if n.rstrip("+") in pos]
        if len(pts) > 1:
            links.append(LineString(pts))
    rail = unary_union(links).buffer(350)
    tramzone = unary_union([LineString([xy(*c) for c in r["path"]]) for r in trams]).buffer(150)
    out = []
    for f in json.loads(path.read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        if p["route"] in taken or p["route"].startswith("SL") or p["description"] == "Supplemental Bus":
            continue
        line = to_m(shape(f["geometry"]))
        if line.length < 1500:
            continue
        subway = [n for n, q in rapid if line.distance(q) <= XFER_M]
        # commuter rail stops with no subway there (Salem, Walpole, Hingham...), so combined stations don't count twice
        crs = sorted({n for n, q in cr.items() if line.distance(q) <= XFER_M and all(q.distance(r) > 150 for _, r in rapid)})
        if not subway and not crs:
            continue
        group = "both" if subway and crs else "subway" if subway else "cr"
        under_rail = line.intersection(rail).length / line.length
        under_tram = line.intersection(tramzone).length / line.length
        new_km = line.length * max(0.0, 1 - under_rail - under_tram) / 1000
        out.append(dict(route=p["route"], name=p["long_name"], kind=p["description"], trips=p["weekday_trips"],
                        group=group, subway=subway, cr=crs, under_rail=round(under_rail, 2),
                        under_tram=round(under_tram, 2), new_km=round(new_km, 1), km=round(line.length / 1000, 1),
                        path=[lonlat(*c) for c in line.simplify(6).coords]))
    out.sort(key=lambda c: -c["trips"])
    # Picks: busy, mostly new ground, and not on top of a pick already made.
    picked = []
    for c in out:
        line = LineString([xy(*q) for q in c["path"]])
        if c["trips"] < 60 or c["new_km"] < 2.0 or c["under_rail"] > 0.5 or c["under_tram"] > 0.5 or c["kind"] == "Commuter Bus":
            continue
        if any(line.intersection(o.buffer(150)).length / line.length > 0.5 for o in picked):
            continue
        c["pick"] = True
        picked.append(line)
    print(len(out), "candidates;", sum(1 for c in out if c.get("pick")), "picks:",
          ", ".join(f"{c['route']} ({c['trips']})" for c in out if c.get("pick")))
    return out


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
<title>NERTA Real Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
        integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
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
  <h1>NERTA Real Map</h1>
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
const ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/';
L.tileLayer(ESRI + 'World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {maxZoom:19, maxNativeZoom:16,
  attribution:'Esri, HERE, Garmin, &copy; OpenStreetMap contributors'}).addTo(map);
map.createPane('labels'); map.getPane('labels').style.zIndex = 450; map.getPane('labels').style.pointerEvents = 'none';
L.tileLayer(ESRI + 'World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {maxZoom:19, maxNativeZoom:16, pane:'labels'}).addTo(map);
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
  el.onclick = () => map.fitBounds(line.getBounds(), {paddingTopLeft:[200,40], paddingBottomRight:[350,40]});
  document.getElementById('routes').appendChild(el);
});
// Commuter rail and high-speed rail, written by the rail poster session (data/rail_regional/), when present.
const gCR = L.layerGroup(), gHSR = L.layerGroup();
const rp = (f, k, d) => (f.properties && f.properties[k] !== undefined) ? f.properties[k] : d;
DATA.rail.lines.forEach(f => {
  const hsr = String(rp(f, 'kind', '')).toLowerCase().includes('hsr') || String(rp(f, 'kind', '')).toLowerCase().includes('high');
  const g = f.geometry.type === 'MultiLineString' ? f.geometry.coordinates : [f.geometry.coordinates];
  g.forEach(part => {
    const ll = part.map(c => [c[1], c[0]]);
    if (hsr) {
      L.polyline(ll, {color:'#80276c', weight:7, opacity:0.9}).addTo(gHSR);
      L.polyline(ll, {color:'#ffd23f', weight:3, opacity:1}).bindTooltip(`<b>${rp(f, 'name', 'High-speed rail')}</b>`, {sticky:true}).addTo(gHSR);
    } else {
      L.polyline(ll, {color: rp(f, 'edge', '#80276c'), weight:6, opacity:0.55}).addTo(gCR);
      L.polyline(ll, {color: rp(f, 'color', '#80276c'), weight:3, opacity:0.95}).bindTooltip(`<b>${rp(f, 'name', 'Commuter rail')}</b>`, {sticky:true}).addTo(gCR);
    }
  });
});
DATA.rail.stations.forEach(f => {
  const c = f.geometry.coordinates;
  L.circleMarker([c[1], c[0]], {radius:4, color:'#80276c', weight:2, fillColor: rp(f, 'hsr', false) ? '#ffd23f' : '#fff', fillOpacity:1})
    .bindTooltip(`<b>${rp(f, 'name', '')}</b><br>${[].concat(rp(f, 'lines', [])).join(', ')}`).addTo(gCR);
});
if (DATA.rail.lines.length) { gCR.addTo(map); gHSR.addTo(map); }
// Lore layers (data/lore/): ferries, the BIGGER Dig, the London boat, landmarks.
const gFerry = L.layerGroup(), gDig = L.layerGroup(), gLore = L.layerGroup();
const lines_ = (f, fn) => (f.geometry.type === 'MultiLineString' ? f.geometry.coordinates : [f.geometry.coordinates]).forEach(p => fn(p.map(c => [c[1], c[0]])));
(DATA.lore.ferry_routes || []).forEach(f => lines_(f, ll => {
  L.polyline(ll, {color:'#fff', weight:7, opacity:0.8}).addTo(gFerry);
  L.polyline(ll, {color: rp(f, 'color', '#00796d'), weight:4, dashArray: rp(f, 'fast', false) ? '10 6' : '1 7', lineCap:'round'})
    .bindTooltip(`<b>Ferry: ${rp(f, 'name', '')}</b>${rp(f, 'fast', false) ? '<br>high-speed' : ''}`, {sticky:true}).addTo(gFerry);
}));
(DATA.lore.ferry_docks || []).forEach(f => { const c = f.geometry.coordinates;
  L.circleMarker([c[1], c[0]], {radius: rp(f, 'major', false) ? 5 : 3.5, color:'#00796d', weight:2, fillColor:'#fff', fillOpacity:1,
    dashArray: rp(f, 'invented', false) ? '2 2' : null})
   .bindTooltip(`<b>${rp(f, 'name', '')}</b> (ferry dock)${rp(f, 'invented', false) ? '<br>invented' : ''}`).addTo(gFerry); });
(DATA.lore.dig || []).forEach(f => {
  if (f.geometry.type === 'Point') { const c = f.geometry.coordinates;
    L.circleMarker([c[1], c[0]], {radius:7, color:'#16161a', weight:3, fillColor:'#fff', fillOpacity:1}).bindTooltip(`<b>${rp(f, 'name', '')}</b>`).addTo(gDig);
  } else lines_(f, ll => {
    L.polyline(ll, {color:'#16161a', weight:9, opacity:0.9}).addTo(gDig);
    L.polyline(ll, {color:'#ffd23f', weight:2, dashArray:'6 5'}).bindTooltip(`<b>${rp(f, 'name', 'The BIGGER Dig')}</b>`, {sticky:true}).addTo(gDig);
  });
});
(DATA.lore.london_ferry || []).forEach(f => {
  if (f.geometry.type === 'Point') { const c = f.geometry.coordinates;
    L.circleMarker([c[1], c[0]], {radius:6, color:'#0b2a5b', weight:3, fillColor:'#fff', fillOpacity:1}).bindTooltip(`<b>${rp(f, 'name', '')}</b>`).addTo(gLore);
  } else lines_(f, ll => L.polyline(ll, {color:'#0b2a5b', weight:4, dashArray:'12 8'}).bindTooltip(`<b>${rp(f, 'name', 'Atlantic Clipper')}</b><br>to London`, {sticky:true}).addTo(gLore));
});
(DATA.lore.landmarks || []).forEach(f => { const c = f.geometry.coordinates;
  L.marker([c[1], c[0]], {icon: L.divIcon({className:'', html:'<div style="font-size:18px;color:#0b2a5b;line-height:18px">&#9733;</div>', iconSize:[18,18], iconAnchor:[9,9]})})
   .bindTooltip(`<b>${rp(f, 'name', '')}</b>${rp(f, 'note', '') ? '<br>' + rp(f, 'note', '') : ''}`).addTo(gLore); });
const hasLore = Object.values(DATA.lore).some(a => a.length);
if (hasLore) { gFerry.addTo(map); gDig.addTo(map); gLore.addTo(map); }
const gCand = L.layerGroup().addTo(map);
if (DATA.cands.length) {
  const side = document.getElementById('side');
  const head = document.createElement('div');
  const shown = DATA.cands.filter(c => c.pick || (c.trips >= 40 && c.new_km >= 1.0));
  head.innerHTML = `<h1 style="margin-top:12px">More trams to choose from</h1><p class="sub">Today's busier bus routes that meet the subway or
    commuter rail, busiest first (weekday trips, both ways). Dashed pink on the map. Starred: my picks (60+ trips, 2+ km of new ground,
    under half its length on NERTA rail or another tram). Tick any route to show it. ${DATA.cands.length - shown.length} more are left
    off the list: under 40 trips, or almost all on NERTA rail or a tram already.</p>`;
  side.appendChild(head);
  const btn = document.createElement('div');
  btn.innerHTML = `<button id="copyticks" style="font:bold 13px Arial;background:%(TRAM)s;color:#fff;border:0;border-radius:14px;padding:6px 12px;cursor:pointer">
    Copy my ticks</button> <span id="ticked" style="font-size:12px;color:var(--mute)"></span>`;
  side.appendChild(btn);
  btn.querySelector('button').onclick = () => {
    const ids = [...side.querySelectorAll('label.route input:checked')].map(i => i.dataset.route);
    const t = `Add these trams: ${ids.join(', ')}`;
    document.getElementById('ticked').textContent = t + '  (copied, paste it in chat)';
    try { navigator.clipboard.writeText(t); } catch (e) {}
  };
  [['both', 'Meets the subway and commuter rail'], ['subway', 'Meets the subway'], ['cr', 'Meets commuter rail only']].forEach(([g, title]) => {
    const rows = shown.filter(c => c.group === g);
    if (!rows.length) return;
    const h = document.createElement('div');
    h.innerHTML = `<b style="display:block;margin:10px 0 2px">${title} (${rows.length})</b>`;
    side.appendChild(h);
    rows.forEach(c => {
      const ll = c.path.map(q => [q[1], q[0]]);
      const ln = L.polyline(ll, {color:'%(TRAM)s', weight:4, opacity:0.85, dashArray:'7 6'})
        .bindTooltip(`<b>${c.route}</b> ${c.name}<br>${c.trips} weekday trips`, {sticky:true});
      if (c.pick) ln.addTo(gCand);
      const meets = [...new Set(c.subway.concat(c.cr))].slice(0, 6).join(', ');
      const row = document.createElement('label');
      row.className = 'route';
      row.innerHTML = `<input type="checkbox" data-route="${c.route}" ${c.pick ? 'checked' : ''} style="margin-top:4px">
        <span class="badge" style="background:#fff;color:%(TRAM)s;border:2px solid %(TRAM)s">${c.route}</span>
        <div><b>${c.pick ? '&#9733; ' : ''}${c.name}</b><small>${c.trips} trips a weekday. Meets ${meets}.
        ${Math.round(c.under_rail*100)}%% under NERTA rail, ${Math.round(c.under_tram*100)}%% under a tram, ${c.new_km} km new.</small></div>`;
      row.querySelector('input').onchange = e => e.target.checked ? ln.addTo(gCand) : gCand.removeLayer(ln);
      row.querySelector('div').onclick = ev => { ev.preventDefault(); if (!gCand.hasLayer(ln)) { ln.addTo(gCand); row.querySelector('input').checked = true; }
        map.fitBounds(ln.getBounds(), {paddingTopLeft:[200,40], paddingBottomRight:[350,40]}); };
      side.appendChild(row);
    });
  });
}
const over = {'Draft trams': gTram, 'More trams to choose from': gCand, 'Frequent buses today': gBus, 'NERTA lines': gNerta, 'NERTA stations': gSta};
if (DATA.rail.lines.length) { over['Commuter rail'] = gCR; over['High-speed rail'] = gHSR; }
if (hasLore) { over['Ferries'] = gFerry; over['The BIGGER Dig'] = gDig; over['London boat and landmarks'] = gLore; }
L.control.layers(null, over, {position:'topleft', collapsed:false}).addTo(map);
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
    # The 19 Max added. Built once into tram_extra.json; the stop-naming pass merges them into tram_draft.json.
    epath = TD / "tram_extra.json"
    if not epath.exists() and (TD / "bus_all.geojson").exists() and (TD / "bus_stops_extra.geojson").exists():
        allb = json.loads((TD / "bus_all.geojson").read_text(encoding="utf-8"))["features"]
        estops = json.loads((TD / "bus_stops_extra.geojson").read_text(encoding="utf-8"))["features"]
        extra = build_draft(stations, allb, estops, EXTRA)
        for r in extra:
            r["added"] = "Max, November 7, from the ranked candidates"
        epath.write_text(json.dumps({"color": TRAM, "routes": extra}, indent=1), encoding="utf-8")
        print("wrote", epath)
    if epath.exists():
        have = {r["id"] for r in trams}
        trams = trams + [r for r in json.loads(epath.read_text(encoding="utf-8"))["routes"] if r["id"] not in have]
    v = 1
    while (OUT / f"tram_realmap_v{v}.html").exists():
        v += 1
    cands = rank_candidates(stations, trams)
    (TD / "tram_candidates.json").write_text(json.dumps(cands, indent=1), encoding="utf-8")
    rail = {"lines": [], "stations": []}   # the rail poster session's layer, read only
    for k, fn in (("lines", "cr_lines.geojson"), ("stations", "cr_stations.geojson")):
        p = DAY / "data" / "rail_regional" / fn
        if p.exists():
            rail[k] = json.loads(p.read_text(encoding="utf-8"))["features"]
    print("rail layer:", len(rail["lines"]), "lines,", len(rail["stations"]), "stations")
    lore = {}
    for k in ("ferry_routes", "ferry_docks", "dig", "london_ferry", "landmarks"):
        p = DAY / "data" / "lore" / f"{k}.geojson"
        lore[k] = json.loads(p.read_text(encoding="utf-8"))["features"] if p.exists() else []
    print("lore:", {k: len(v) for k, v in lore.items()})
    data = {"stations": stations, "buses": buses, "trams": trams, "nerta": nerta_links(stations), "code": CODE, "cands": cands, "rail": rail, "lore": lore}
    pill = {"RL": M.RED, "OL": M.ORANGE, "BL": M.BLUE, "GL": M.GREEN, "YL": M.YELLOW, "CL": M.CYAN, "IL": M.INDIGO, "SL": M.SILVER, "CR": M.CR_TEXT_COLOR}
    html = PAGE % {"TRAM": TRAM, "V": v, "DATE": "November 7, 2026", "DATA": json.dumps(data), "PILL": json.dumps(pill)}
    out = OUT / f"tram_realmap_v{v}.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
