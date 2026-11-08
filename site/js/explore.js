/* Street map: the whole network drawn on real geography. Subway lines run stop to stop, Regional Rail and High-Speed Rail
   follow their real track, ferries run dashed between docks. Tap a stop for departures. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA;
  const [d, rail, tram] = await Promise.all([N.network(), fetch("/data/geo/cr_lines.geojson").then(r => r.json()),
    fetch("/data/geo/tram_lines.geojson").then(r => r.ok ? r.json() : { features: [] }).catch(() => ({ features: [] }))]);
  const LL = s => [s.geo.lat, s.geo.lon];

  const map = L.map("map", { zoomSnap: 0.5, minZoom: 7, maxZoom: 18, preferCanvas: true });
  L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
    maxZoom: 18, maxNativeZoom: 16, attribution: "Esri, HERE, Garmin, OpenStreetMap contributors"
  }).addTo(map);
  map.setView([42.36, -71.06], 11);
  map.setMaxBounds([[40.2, -74.5], [44.6, -68.6]]);

  // Draw order, bottom to top: rail, ferry, tram, subway, stops. Each pane gets its own canvas.
  [["rail", 410], ["ferry", 420], ["tram", 425], ["subway", 430], ["stops", 440]].forEach(([p, z]) => { map.createPane(p).style.zIndex = z; });
  const R = {}; ["rail", "ferry", "tram", "subway", "stops"].forEach(p => { R[p] = L.canvas({ pane: p, padding: 0.3 }); });

  const MODES = [["subway", "Subway"], ["rail", "Regional Rail"], ["hsr", "High-Speed Rail"], ["ferry", "Ferry"], ["tram", "Trams"]];
  const groups = {}; MODES.forEach(([m]) => { groups[m] = L.layerGroup().addTo(map); });
  const shapes = [];  // { line, layer, base } for dimming

  const add = (line, layer, base) => { shapes.push({ line, layer, base }); groups[N.LINES[line].mode].addLayer(layer); };

  // Regional Rail and High-Speed Rail: real track, purple with a thin outline in the line's color (gold for HSR).
  const HSR = { hmon: "hsr-montreal", hmai: "hsr-bangor", halb: "hsr-albany", hnyc: "hsr-new-york" };
  const railKey = p => {
    if (p.kind === "hsr") return HSR[p.line] || (d.railLines.find(l => l.mode === "hsr" && l.name.split(/[ ,]/)[3] === p.name.split(/[ ,]/)[3]) || {}).key;
    return d.lines["rail-" + p.line] ? "rail-" + p.line : (d.railLines.find(l => l.name.replace(/\s/g, "") === p.name.replace(/\s/g, "")) || {}).key;
  };
  rail.features.forEach(f => {
    const key = railKey(f.properties);
    if (!key || !N.LINES[key]) return;
    const pts = f.geometry.coordinates.map(([x, y]) => [y, x]);
    const edge = f.properties.kind === "hsr" ? "#ffd23f" : (f.properties.edge || N.LINES[key].hue || "#80276c");
    const under = L.polyline(pts, { renderer: R.rail, color: edge, weight: 6.5, opacity: 1, interactive: false });
    const over = L.polyline(pts, { renderer: R.rail, color: "#80276c", weight: 4, opacity: 1, interactive: false });
    add(key, under, { opacity: 1 }); add(key, over, { opacity: 1 });
  });

  // Ferry: dashed, stop to stop. River loops close back to their start.
  d.ferryLines.forEach(l => l.legs.forEach(leg => {
    const ids = leg.slice();
    if (l.loop && ids[0] !== ids[ids.length - 1]) ids.push(ids[0]);
    const pts = ids.map(id => d.byId[id]).filter(s => s && s.geo).map(LL);
    if (pts.length < 2) return;
    add(l.key, L.polyline(pts, { renderer: R.ferry, color: l.color, weight: 3, opacity: 0.95, dashArray: "7 6", interactive: false }), { opacity: 0.95 });
  }));

  // Trams: real street paths, pink, under the subway.
  tram.features.forEach(f => {
    const key = f.properties.line;
    if (!N.LINES[key] || N.LINES[key].mode !== "tram") return;
    const lines = f.geometry.type === "MultiLineString" ? f.geometry.coordinates : [f.geometry.coordinates];
    lines.forEach(c => add(key, L.polyline(c.map(([x, y]) => [y, x]), { renderer: R.tram, color: "#e0457b", weight: 3, opacity: 0.9, lineJoin: "round", interactive: false }), { opacity: 0.9 }));
  });

  // Subway: each leg through its stops, in the line color, on top.
  N.ORDER.forEach(k => (d.lines[k] ? d.lines[k].legs : []).forEach(leg => {
    const pts = leg.map(id => d.byId[id]).filter(s => s && s.geo).map(LL);
    if (pts.length < 2) return;
    add(k, L.polyline(pts, { renderer: R.subway, color: N.LINES[k].color, weight: 5, opacity: 1, lineCap: "round", lineJoin: "round", interactive: false }), { opacity: 1 });
  }));

  // Stops: white dots with a dark ring. Docks are smaller with a teal ring, tram stops smaller still with a pink ring.
  const ring = s => s.kind === "dock" ? "#00796d" : s.kind === "tram" ? "#e0457b" : "#16161a";
  const modesOf = s => [...new Set(N.servedBy(s).map(l => N.LINES[l].mode))];
  const markers = {};
  const radius = (s, z) => (s.kind === "dock" ? 0.75 : s.kind === "tram" ? 0.6 : 1) * (z >= 14 ? 6 : z >= 12 ? 4.5 : z >= 10 ? 3.5 : 2.5);
  d.stops.forEach(s => {
    if (!s.geo) return;
    const m = L.circleMarker(LL(s), {
      renderer: R.stops, radius: radius(s, map.getZoom()), color: ring(s),
      weight: 2, fillColor: "#fff", fillOpacity: 1, opacity: 1
    });
    m.bindTooltip(s.name + (s.kind === "dock" ? " (ferry dock)" : s.kind === "tram" ? " (tram)" : ""), { className: "stop-tip", direction: "top", offset: [0, -6] });
    m.on("click", () => select(s.id, false));
    markers[s.id] = { m, s, modes: modesOf(s) };
  });
  const stopLayer = L.layerGroup().addTo(map);

  // State: which modes are on, which line is picked, which stop is open.
  const on = new Set(MODES.map(([m]) => m));
  let picked = "", selected = null;

  function refresh() {
    MODES.forEach(([m]) => { if (on.has(m)) map.addLayer(groups[m]); else map.removeLayer(groups[m]); });
    shapes.forEach(({ line, layer, base }) => layer.setStyle({ opacity: !picked || line === picked ? base.opacity : 0.12 }));
    if (picked) {
      const g = groups[N.LINES[picked].mode];
      shapes.forEach(({ line, layer }) => { if (line === picked && g.hasLayer(layer)) layer.bringToFront(); });
    }
    const z = map.getZoom();
    Object.values(markers).forEach(({ m, s, modes }) => {
      const show = modes.length ? modes.some(x => on.has(x)) : true;
      if (!show && s.id !== selected) { stopLayer.removeLayer(m); return; }
      stopLayer.addLayer(m);
      const lit = !picked || s.lines.includes(picked);
      m.setRadius(radius(s, z) + (s.id === selected ? 2.5 : 0));
      m.setStyle({ opacity: lit ? 1 : 0.2, fillOpacity: lit ? 1 : 0.2, weight: s.id === selected ? 3.5 : s.kind === "tram" ? 1.5 : 2,
        color: s.id === selected ? "#00a9c9" : ring(s) });
    });
    if (selected && markers[selected]) markers[selected].m.bringToFront();
  }
  map.on("zoomend", refresh);

  // Mode toggles
  const modesEl = document.getElementById("modes");
  const swatch = { subway: N.bullet("red"), rail: N.bullet("rail"), hsr: N.bullet("hsr-albany"), ferry: N.bullet("ferry"), tram: N.bullet("tram") };
  modesEl.innerHTML = MODES.map(([m, t]) => `<label><input type="checkbox" value="${m}" checked>${swatch[m]} ${t}</label>`).join("");
  modesEl.addEventListener("change", e => { e.target.checked ? on.add(e.target.value) : on.delete(e.target.value); refresh(); });

  // Line picker: everything else dims.
  const pick = document.getElementById("pick");
  const byMode = m => Object.values(d.lines).filter(l => l.mode === m)
    .sort((a, b) => m === "tram" ? (parseInt(a.number, 10) || 0) - (parseInt(b.number, 10) || 0) : 0);
  const subwayKeys = N.ORDER.filter(k => d.lines[k]);
  pick.innerHTML = `<option value="">All lines</option>` +
    `<optgroup label="Subway">${subwayKeys.map(k => `<option value="${k}">${N.esc(N.LINES[k].name)}</option>`).join("")}</optgroup>` +
    [["rail", "Regional Rail"], ["hsr", "High-Speed Rail"], ["ferry", "Ferry"], ["tram", "Trams"]].map(([m, t]) =>
      `<optgroup label="${t}">${byMode(m).map(l => `<option value="${l.key}">${N.esc(l.name)}</option>`).join("")}</optgroup>`).join("");
  function choose(key, fit) {
    picked = key && N.LINES[key] ? key : "";
    pick.value = picked;
    if (picked && !on.has(N.LINES[picked].mode)) {
      on.add(N.LINES[picked].mode);
      const box = modesEl.querySelector(`input[value="${N.LINES[picked].mode}"]`);
      if (box) box.checked = true;
    }
    refresh();
    if (picked && fit) {
      const pts = d.lines[picked].legs.flat().map(id => d.byId[id]).filter(s => s && s.geo).map(LL);
      if (pts.length) map.flyToBounds(L.latLngBounds(pts).pad(0.12), { duration: 0.6, maxZoom: 14 });
    }
    setUrl();
  }
  pick.addEventListener("change", () => choose(pick.value, true));

  // Stop search: flies to the stop and opens it.
  const find = document.getElementById("find"), list = document.getElementById("find-list");
  let hits = [], active = -1;
  const label = s => s.name + (s.kind === "dock" && d.byId[N.slug(s.name)] ? " (ferry dock)" : s.kind === "tram" ? " (tram)" : "");
  find.addEventListener("input", () => {
    const q = find.value.trim().toLowerCase();
    if (!q) { list.classList.remove("open"); return; }
    hits = d.stops.filter(s => s.geo && s.name.toLowerCase().includes(q))
      .sort((a, b) => a.name.toLowerCase().indexOf(q) - b.name.toLowerCase().indexOf(q) || a.name.localeCompare(b.name)).slice(0, 9);
    active = -1;
    list.innerHTML = hits.length ? hits.map((s, i) => `<button type="button" data-i="${i}">${N.badges(s)} ${N.esc(label(s))}</button>`).join("")
      : '<div class="small muted" style="padding:8px 10px">No stops match.</div>';
    list.classList.add("open");
  });
  const go = s => { list.classList.remove("open"); find.value = label(s); select(s.id, true); };
  list.addEventListener("click", e => { const b = e.target.closest("button"); if (b) go(hits[+b.dataset.i]); });
  find.addEventListener("keydown", e => {
    const btns = list.querySelectorAll("button");
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!btns.length) return;
      e.preventDefault();
      active = (active + (e.key === "ArrowDown" ? 1 : -1) + btns.length) % btns.length;
      btns.forEach((b, i) => b.classList.toggle("active", i === active));
    } else if (e.key === "Enter") { if (hits[Math.max(active, 0)]) go(hits[Math.max(active, 0)]); }
    else if (e.key === "Escape") list.classList.remove("open");
  });
  document.addEventListener("click", e => { if (!e.target.closest(".explore-find")) list.classList.remove("open"); });

  function setUrl() {
    const p = new URLSearchParams();
    if (selected) p.set("stop", selected);
    if (picked) p.set("line", picked);
    const q = p.toString();
    history.replaceState(null, "", location.pathname + (q ? "?" + q : ""));
  }

  function select(id, fly) {
    const s = d.byId[id];
    if (!s || !s.geo) return;
    selected = id;
    refresh();
    if (fly) map.flyTo(LL(s), Math.max(map.getZoom(), 15), { duration: 0.7 });
    setUrl();
    render(s);
  }

  function render(s) {
    const dirs = N.directions(d, s);
    const shown = dirs.filter(x => N.LINES[x.line].mode === "subway").concat(dirs.filter(x => N.LINES[x.line].mode !== "subway")).slice(0, 7);
    const board = shown.map(x => {
      const m = N.departures(s.id, x.line, x.to, 2);
      return `<div class="dir">${N.bullet(x.line)}<div class="to">${N.esc(x.to)}${N.crowdNote(s.id, x.line, m, x.to)}</div><div class="mins">${m.map(v => N.crowdTime(s.id, x.line, v, x.to)).join("")}</div></div>`;
    }).join("");
    const lines = N.servedBy(s);
    document.getElementById("panel").innerHTML = `
      <h2 style="margin:14px 0 6px">${N.esc(s.name)}${s.kind === "dock" ? " Ferry Dock" : s.kind === "tram" ? " Tram Stop" : ""}</h2>
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">${N.badges(s)}</div>
      ${s.geo.verified === false ? `<p class="small muted" style="margin:0 0 10px">Approximate location</p>` : ""}
      ${board ? `<div class="board"><div class="head"><span>Departures</span><span>Live</span></div>${board}</div>` : ""}
      ${dirs.length > shown.length ? `<p class="small muted" style="margin:6px 0 0">${dirs.length - shown.length} more directions on the station page.</p>` : ""}
      <dl class="kv" style="margin-top:14px">
        <dt>Weekday boardings</dt><dd>${N.fmt(N.ridership(s))}</dd>
        <dt>Lines</dt><dd>${lines.map(l => N.esc(N.LINES[l].name)).join(", ") || "None"}</dd>
        <dt>Step-free</dt><dd>Yes</dd>
      </dl>
      <p style="margin-top:14px"><a class="btn small" href="${N.stopLink(s)}">Station details</a></p>`;
  }

  refresh();
  const startLine = N.qs("line"), startStop = N.qs("stop");
  if (startLine && N.LINES[startLine] && d.lines[startLine]) choose(startLine, !startStop);
  if (startStop && d.byId[startStop]) select(startStop, true);
});
