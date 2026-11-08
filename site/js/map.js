/* Interactive map: the finished system map as a zoomable image, with a clickable spot on every station. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA;
  const d = await N.network();
  const W = d.image.width, H = d.image.height;
  const [x0, x1] = d.extent.x, [y0, y1] = d.extent.y;
  const toLL = s => [-(y1 - s.y) / (y1 - y0) * H, (s.x - x0) / (x1 - x0) * W];

  const map = L.map("map", { crs: L.CRS.Simple, minZoom: -4, maxZoom: 1, zoomSnap: 0.25, attributionControl: false });
  const bounds = [[-H, 0], [0, W]];
  L.imageOverlay("/assets/maps/system_map.webp", bounds).addTo(map);
  map.fitBounds(bounds);
  map.setMaxBounds(L.latLngBounds(bounds).pad(0.15));

  const markers = {};
  let selected = null;
  d.stops.filter(s => !s.offmap).forEach(s => {
    const m = L.circleMarker(toLL(s), { radius: 10, color: "#00a9c9", weight: 0, fillOpacity: 0, opacity: 1 }).addTo(map);
    m.bindTooltip(s.name, { className: "stop-tip", direction: "top", offset: [0, -8] });
    m.on("mouseover", () => m.setStyle({ weight: 4 }));
    m.on("mouseout", () => { if (selected !== s.id && !m.lit) m.setStyle({ weight: 0 }); });
    m.on("click", () => select(s.id, false));
    markers[s.id] = m;
  });

  // Line filter
  const keys = [...N.ORDER.filter(k => k !== "silver"), "rail"];
  const filters = document.getElementById("filters");
  filters.innerHTML = keys.map(k => `<label><input type="radio" name="line" value="${k}">${N.bullet(k)} ${N.LINES[k].name.replace(" Line", "")}</label>`).join("") +
    `<label><input type="radio" name="line" value="" checked> None</label>`;
  filters.addEventListener("change", e => {
    const k = e.target.value;
    Object.entries(markers).forEach(([id, m]) => {
      const on = k && d.byId[id].lines.includes(k);
      m.lit = on;
      m.setStyle(on ? { weight: 4, color: N.LINES[k].color, fillOpacity: 0 } : { weight: id === selected ? 4 : 0, color: "#00a9c9" });
    });
  });

  function select(id, fly) {
    const s = d.byId[id];
    if (!s) return;
    if (selected && markers[selected] && !markers[selected].lit) markers[selected].setStyle({ weight: 0 });
    selected = id;
    if (markers[id]) {
      markers[id].setStyle({ weight: 4 });
      if (fly) map.flyTo(toLL(s), 0, { duration: 0.6 });
    }
    history.replaceState(null, "", "?stop=" + id);
    render(s);
  }

  function render(s) {
    const transit = s.lines.filter(l => l !== "rail");
    const dirs = [];
    d.segments.forEach(seg => {
      if (!seg.stops.includes(s.id)) return;
      [seg.stops[0], seg.stops[seg.stops.length - 1]].forEach(end => {
        if (end !== s.id && !dirs.some(x => x.line === seg.line && x.to === end)) dirs.push({ line: seg.line, to: end });
      });
    });
    const board = dirs.slice(0, 6).map(x => {
      const m = N.departures(s.id, x.line, x.to, 2);
      return `<div class="dir">${N.bullet(x.line)}<div class="to">${N.esc(d.byId[x.to].name)}</div><div class="mins">${m.map(v => `<span>${v === 0 ? "Now" : v}${v ? "<em>min</em>" : ""}</span>`).join("")}</div></div>`;
    }).join("");
    document.getElementById("panel").innerHTML = `
      <h2 style="margin:6px 0 6px">${N.esc(s.name)}</h2>
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">${s.lines.map(l => N.bullet(l)).join("")}</div>
      ${board ? `<div class="board"><div class="head"><span>Departures</span><span>Live</span></div>${board}</div>` : ""}
      <dl class="kv" style="margin-top:14px">
        <dt>Weekday boardings</dt><dd>${N.fmt(N.ridership(s))}</dd>
        <dt>Lines</dt><dd>${s.lines.map(l => N.LINES[l].name).join(", ")}</dd>
        <dt>Step-free</dt><dd>Yes</dd>
      </dl>
      <p style="margin-top:14px"><a class="btn small" href="${N.stopLink(s)}">Station details</a></p>`;
  }

  const start = N.qs("stop");
  if (start && d.byId[start]) select(start, true);
});
