/* One station or ferry dock: live departures (direction names worked out from the line's real ends), a crop of the system
   map where the stop is drawn on it, made-up ridership numbers, every line that stops here, and its neighbors. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA, d = await N.network();
  const s = d.byId[N.qs("id")] || d.byId["boston-central"];
  const served = N.servedBy(s);
  document.title = `${s.name}${s.kind === "dock" ? " Ferry Dock" : ""} | NERTA`;
  document.getElementById("title").textContent = s.name + (s.kind === "dock" ? " Ferry Dock" : "");
  document.getElementById("crumb").textContent = s.name;
  document.getElementById("bullets").innerHTML = N.badges(s);
  const names = served.map(l => N.LINES[l].name);
  document.getElementById("sub").textContent = names.length > 1
    ? `Served by the ${names.slice(0, -1).join(", ")} and ${names.slice(-1)}.` : names.length ? `Served by the ${names[0]}.` : "";

  // Departures: one row per line and direction, refreshed every 20 seconds. Downtown, rail rows are capped so the board stays readable.
  let dirs = N.directions(d, s);
  const subwayDirs = dirs.filter(x => N.LINES[x.line].mode === "subway");
  const otherDirs = dirs.filter(x => N.LINES[x.line].mode !== "subway");
  dirs = subwayDirs.concat(otherDirs.slice(0, 10));
  const more = otherDirs.length - 10;
  const via = x => { const L = N.LINES[x.line]; return L.mode === "subway" ? L.name : L.name; };
  const board = () => {
    document.getElementById("board").innerHTML = `<div class="head"><span>Departures</span><span>${new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}</span></div>` +
      (dirs.length ? dirs.map(x => {
        const m = N.departures(s.id, x.line, x.to, 3);
        return `<div class="dir">${N.bullet(x.line)}<div class="to">${N.esc(x.to)}<small>${N.esc(via(x))}${N.freeTag(x.line)}</small>${N.crowdNote(s.id, x.line, m, x.to)}</div><div class="mins">${m.map(v => N.crowdTime(s.id, x.line, v, x.to)).join("")}</div></div>`;
      }).join("") : `<div class="dir"><span></span><div class="to">No scheduled service</div><div></div></div>`) +
      (more > 0 ? `<div class="head"><span>${more} more rail, ferry and tram directions</span><span><a href="/rail.html" style="color:inherit">Regional Rail</a></span></div>` : "");
  };
  board(); setInterval(board, 20000);
  const closed = N.stationStatus(s.id), ev = N.eventNow();
  const note = closed.closed ? `<div class="alert-item" style="border-left-color:#b0151a;margin-bottom:14px"><span class="tag bad">Station closed</span><p style="margin-top:6px">${N.esc(closed.detail)}</p></div>`
    : ev && ev.at === s.id ? `<div class="alert-item" style="border-left-color:#1f5fae;margin-bottom:14px"><span class="tag">Event</span><p style="margin-top:6px">${N.esc(ev.text)}</p></div>` : "";
  if (note) document.getElementById("board").insertAdjacentHTML("beforebegin", note);
  document.getElementById("board-note").textContent = N.isPeak() ? "Peak service." : "Off-peak service.";

  // Map crop, where the stop is drawn on the system map.
  const area = document.getElementById("area"), link = document.getElementById("area-link");
  if (s.x !== undefined) {
    const href = `/map.html?stop=${s.id}`;
    area.href = href; link.href = href;
    const W = d.image.width, H = d.image.height, [x0, x1] = d.extent.x, [y0, y1] = d.extent.y;
    const scale = 0.55;
    const px = (s.x - x0) / (x1 - x0) * W * scale, py = (y1 - s.y) / (y1 - y0) * H * scale;
    area.style.backgroundImage = "url(/assets/maps/system_map.webp)";
    area.style.backgroundSize = `${W * scale}px ${H * scale}px`;
    const place = () => { area.style.backgroundPosition = `${area.clientWidth / 2 - px}px ${area.clientHeight / 2 - py}px`; };
    place(); addEventListener("resize", place);
  } else {
    const first = served[0];
    const L = first && N.LINES[first];
    const href = L ? (L.mode === "ferry" ? `/ferry-route.html?r=${first}` : L.mode === "tram" ? `/tram-line.html?l=${first}` : L.mode === "subway" ? `/line.html?l=${first}` : `/rail-line.html?l=${first}`) : "/maps.html";
    const img = L && L.mode === "ferry" && (d.released || {}).ferry ? "ferry_network_thumb" : L && L.mode === "subway" ? `line_${first}_thumb` : "system_map_thumb";
    area.href = href; link.href = href;
    area.style.cssText += `;background:url(/assets/maps/${img}.webp) center/contain no-repeat #fff`;
    link.textContent = L ? `See the ${L.name} map` : "See the maps";
  }

  // Made-up ridership: hourly profile with two peaks, and a 12-month trend.
  const total = N.ridership(s);
  const r = N.rng("hourly:" + s.id);
  const central = Math.exp(-N.coreDistance(s) / 40);
  const shape = [...Array(24)].map((_, h) => {
    const am = Math.exp(-((h - 8) ** 2) / 2.2) * (1.4 - central * 0.6);
    const pm = Math.exp(-((h - 17.3) ** 2) / 2.6) * (0.8 + central * 0.7);
    return (am + pm + (h >= 6 && h <= 22 ? 0.28 : 0.05)) * (0.9 + r() * 0.2);
  });
  const sum = shape.reduce((a, b) => a + b, 0);
  const hours = shape.map(v => Math.round(v / sum * total));
  const now = new Date().getHours(), hmax = Math.max(...hours), bw = 26, gh = 150;
  document.getElementById("hourly").innerHTML = `<svg class="chart" viewBox="0 0 ${24 * bw + 40} ${gh + 30}" role="img" aria-label="Boardings by hour of the day">
    ${[0, 0.5, 1].map(f => `<line x1="40" x2="${24 * bw + 40}" y1="${gh - f * gh + 4}" y2="${gh - f * gh + 4}" stroke="#e2e2dd"/><text x="34" y="${gh - f * gh + 8}" text-anchor="end">${N.fmt(Math.round(hmax * f / 10) * 10)}</text>`).join("")}
    ${hours.map((v, h) => `<rect x="${40 + h * bw + 3}" y="${gh - v / hmax * gh + 4}" width="${bw - 6}" height="${v / hmax * gh}" rx="3" fill="${h === now ? "#00a9c9" : "#16161a"}"><title>${h % 12 || 12} ${h < 12 ? "AM" : "PM"}: ${N.fmt(v)}</title></rect>`).join("")}
    ${[0, 6, 12, 18, 23].map(h => `<text x="${40 + h * bw + bw / 2}" y="${gh + 24}" text-anchor="middle">${h % 12 || 12}${h < 12 ? "a" : "p"}</text>`).join("")}
  </svg><p class="small muted" style="margin:6px 0 0"><span class="dot" style="background:#00a9c9"></span> This hour</p>`;
  // How busy right now, against the usual for this hour, and the hours that are usually busiest (from the chart above).
  const busy = N.stationCrowding(s.id);
  const hr = h => `${h % 12 || 12}${h < 12 ? " AM" : " PM"}`;
  const span = h => `${h % 12 || 12} to ${hr((h + 1) % 24)}`;
  const amTop = hours.slice(0, 12).indexOf(Math.max(...hours.slice(0, 12)));
  const pmTop = 12 + hours.slice(12).indexOf(Math.max(...hours.slice(12)));
  const peaks = [amTop, pmTop].sort((a, b) => hours[b] - hours[a]);
  if (busy && !closed.closed) document.getElementById("hourly").insertAdjacentHTML("beforebegin",
    `<div class="busy-now"><span class="eyebrow" style="margin:0">How busy right now</span>${N.crowdIcon(busy)}<span class="lvl">${busy.label}</span><span class="small">${busy.compare}.</span>` +
    `<span class="small muted" style="flex-basis:100%">Usually busiest ${span(peaks[0])} and ${span(peaks[1])}.</span></div>`);
  const vals = [...Array(12)].map((_, i) => Math.round(total * 21 * (0.85 + r() * 0.3) * (0.97 + i * 0.006)));
  const vmax = Math.max(...vals) * 1.05, vmin = Math.min(...vals) * 0.9;
  const pts = vals.map((v, i) => [40 + i * 52, 140 - (v - vmin) / (vmax - vmin) * 120]);
  document.getElementById("monthly").innerHTML = `<svg class="chart" viewBox="0 0 640 170" role="img" aria-label="Boardings per month">
    <polyline fill="none" stroke="#16161a" stroke-width="3" points="${pts.map(p => p.join(",")).join(" ")}"/>
    ${pts.map((p, i) => `<circle cx="${p[0]}" cy="${p[1]}" r="4.5" fill="#fff" stroke="#16161a" stroke-width="2"><title>${11 - i ? 11 - i + (i === 10 ? " month" : " months") + " ago" : "Last month"}: ${N.fmt(vals[i])}</title></circle>`).join("")}
    <text x="${pts[0][0]}" y="164" text-anchor="start">12 months ago</text><text x="${pts[11][0]}" y="164" text-anchor="end">Last month</text>
  </svg><p class="small" style="margin:6px 0 0">Last month: <b>${N.fmt(vals[11])}</b> boardings</p>`;

  // Facts: made-up ridership, plus what the maps say (every stop is step-free; pods everywhere).
  const f = N.rng("facts:" + s.id);
  const lineLink = l => { const L = N.LINES[l]; const href = L.mode === "ferry" ? `/ferry-route.html?r=${l}` : L.mode === "tram" ? `/tram-line.html?l=${l}` : L.mode === "subway" ? `/line.html?l=${l}` : `/rail-line.html?l=${l}`; return `<a href="${href}">${N.esc(L.name)}</a>`; };
  const dock = s.dock && d.byId[s.dock];
  const station = s.kind === "dock" && d.byId[N.slug(s.name)];
  document.getElementById("facts").innerHTML = [
    ["Weekday boardings", N.fmt(total)],
    ["Saturday", N.fmt(Math.round(total * (0.5 + f() * 0.2) / 10) * 10)],
    ["Sunday", N.fmt(Math.round(total * (0.35 + f() * 0.15) / 10) * 10)],
    ["Lines", served.map(lineLink).join(", ") || "None"],
    ...(s.hsr ? [["High-Speed Rail", "Stops here"]] : []),
    ...(dock ? [["Ferry", `<a href="${N.stopLink(dock)}">${N.esc(dock.name)} dock</a>, short walk`]] : s.ferry ? [["Ferry", `${N.esc(s.ferry)} dock, short walk`]] : []),
    ...(station ? [["Station", `<a href="${N.stopLink(station)}">${N.esc(station.name)}</a>`]] : []),
    ...(s.major ? [["Port", "Major port: express boats stop here"]] : []),
    ...(s.parking ? [["Parking", "Public garage or lot"]] : []),
    ...(s.geo ? [["Street map", `<a href="/explore.html?stop=${encodeURIComponent(s.id)}">Show on the street map</a>`]] : []),
    ["Step-free", "Yes"],
    ["Pods", "At the door, 24 hours"]
  ].map(([a, b]) => `<dt>${a}</dt><dd>${b}</dd>`).join("");

  // Neighbors along each line.
  const near = new Map();
  served.forEach(l => (d.nbr[l][s.id] || []).forEach(n => near.set(n, d.byId[n])));
  document.getElementById("nearby-title").textContent = s.kind === "dock" ? "Next docks" : "Next stops";
  document.getElementById("nearby").innerHTML = [...near.values()].map(x => `<li>${N.badges(x)}<a class="name" href="${N.stopLink(x)}">${N.esc(x.name)}</a></li>`).join("");
});
