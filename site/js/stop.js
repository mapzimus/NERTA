/* One station: live departures, a crop of the system map, hourly and monthly ridership, facts and neighbors. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA, d = await N.network();
  const s = d.byId[N.qs("id")] || d.byId["boston-central"];
  document.title = `${s.name} | NERTA`;
  document.getElementById("title").textContent = s.name;
  document.getElementById("crumb").textContent = s.name;
  document.getElementById("bullets").innerHTML = s.lines.map(l => N.bullet(l, true)).join("");
  const names = s.lines.map(l => N.LINES[l].name);
  document.getElementById("sub").textContent = names.length > 1 ? `Change here between the ${names.slice(0, -1).join(", ")} and ${names.slice(-1)}.` : `A ${names[0]} station.`;

  // Departures, one row per direction, refreshed every 20 seconds.
  const dirs = [];
  d.segments.forEach(seg => {
    if (!seg.stops.includes(s.id)) return;
    [seg.stops[0], seg.stops[seg.stops.length - 1]].forEach(end => {
      if (end !== s.id && !dirs.some(x => x.line === seg.line && x.to === end)) dirs.push({ line: seg.line, to: end });
    });
  });
  const board = () => {
    document.getElementById("board").innerHTML = `<div class="head"><span>Departures</span><span>${new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}</span></div>` +
      dirs.map(x => {
        const m = N.departures(s.id, x.line, x.to, 3);
        const via = x.line === "green" ? "Light rail" : x.line === "rail" ? "Regional Rail" : N.LINES[x.line].name;
        return `<div class="dir">${N.bullet(x.line)}<div class="to">${N.esc(d.byId[x.to].name)}<small>${via}</small></div><div class="mins">${m.map(v => `<span>${v === 0 ? "Now" : v + "<em>min</em>"}</span>`).join("")}</div></div>`;
      }).join("");
  };
  board(); setInterval(board, 20000);
  document.getElementById("board-note").textContent = N.isPeak() ? "Peak service. Trains are close together." : "Off-peak service.";

  // Map crop centered on the station.
  const area = document.getElementById("area"), link = document.getElementById("area-link");
  const href = `/map.html?stop=${s.id}`;
  area.href = href; link.href = href;
  if (!s.offmap) {
    const W = d.image.width, H = d.image.height, [x0, x1] = d.extent.x, [y0, y1] = d.extent.y;
    const scale = 0.55;
    const px = (s.x - x0) / (x1 - x0) * W * scale, py = (y1 - s.y) / (y1 - y0) * H * scale;
    area.style.backgroundImage = "url(/assets/maps/system_map.webp)";
    area.style.backgroundSize = `${W * scale}px ${H * scale}px`;
    const place = () => { area.style.backgroundPosition = `${area.clientWidth / 2 - px}px ${area.clientHeight / 2 - py}px`; };
    place(); addEventListener("resize", place);
  } else {
    area.style.cssText += ";display:grid;place-items:center;background:url(/assets/maps/line_silver_thumb.webp) center/contain no-repeat #fff";
    link.textContent = "See the Silver Line map"; link.href = "/line.html?l=silver"; area.href = "/line.html?l=silver";
  }

  // Hourly profile: two commuter peaks, shaped by how central the station is.
  const total = N.ridership(s);
  const r = N.rng("hourly:" + s.id);
  const central = Math.exp(-N.coreDistance(s) / 40);
  const shape = [...Array(24)].map((_, h) => {
    const am = Math.exp(-((h - 8) ** 2) / 2.2) * (1.4 - central * 0.6);
    const pm = Math.exp(-((h - 17.3) ** 2) / 2.6) * (0.8 + central * 0.7);
    const mid = h >= 6 && h <= 22 ? 0.28 : 0.05;
    return (am + pm + mid) * (0.9 + r() * 0.2);
  });
  const sum = shape.reduce((a, b) => a + b, 0);
  const hours = shape.map(v => Math.round(v / sum * total));
  const now = new Date().getHours();
  const hmax = Math.max(...hours);
  const bw = 26, gh = 150;
  document.getElementById("hourly").innerHTML = `<svg class="chart" viewBox="0 0 ${24 * bw + 40} ${gh + 30}" role="img" aria-label="Boardings by hour of the day">
    ${[0, 0.5, 1].map(f => `<line x1="40" x2="${24 * bw + 40}" y1="${gh - f * gh + 4}" y2="${gh - f * gh + 4}" stroke="#e2e2dd"/><text x="34" y="${gh - f * gh + 8}" text-anchor="end">${N.fmt(Math.round(hmax * f / 10) * 10)}</text>`).join("")}
    ${hours.map((v, h) => `<rect x="${40 + h * bw + 3}" y="${gh - v / hmax * gh + 4}" width="${bw - 6}" height="${v / hmax * gh}" rx="3" fill="${h === now ? "#00a9c9" : "#16161a"}"><title>${h % 12 || 12} ${h < 12 ? "AM" : "PM"}: ${N.fmt(v)}</title></rect>`).join("")}
    ${[0, 6, 12, 18, 23].map(h => `<text x="${40 + h * bw + bw / 2}" y="${gh + 24}" text-anchor="middle">${h % 12 || 12}${h < 12 ? "a" : "p"}</text>`).join("")}
  </svg><p class="small muted" style="margin:6px 0 0"><span class="dot" style="background:#00a9c9"></span> This hour</p>`;

  // Monthly trend: last 12 months.
  const months = [...Array(12)].map((_, i) => { const dt = new Date(); dt.setDate(1); dt.setMonth(dt.getMonth() - 11 + i); return dt; });
  const season = [0.86, 0.9, 0.97, 1.0, 1.02, 0.95, 0.88, 0.9, 1.04, 1.06, 1.02, 0.93];
  const vals = months.map((m, i) => Math.round(total * 21 * season[m.getMonth()] * (0.97 + i * 0.006) * (0.97 + r() * 0.06)));
  const vmax = Math.max(...vals) * 1.05, vmin = Math.min(...vals) * 0.9;
  const pts = vals.map((v, i) => [40 + i * 52, 140 - (v - vmin) / (vmax - vmin) * 120]);
  document.getElementById("monthly").innerHTML = `<svg class="chart" viewBox="0 0 640 170" role="img" aria-label="Boardings per month">
    <polyline fill="none" stroke="#16161a" stroke-width="3" points="${pts.map(p => p.join(",")).join(" ")}"/>
    ${pts.map((p, i) => `<circle cx="${p[0]}" cy="${p[1]}" r="4.5" fill="#fff" stroke="#16161a" stroke-width="2"><title>${months[i].toLocaleString("en-US", { month: "long", year: "numeric" })}: ${N.fmt(vals[i])}</title></circle>`).join("")}
    ${pts.map((p, i) => i % 2 ? "" : `<text x="${p[0]}" y="164" text-anchor="middle">${months[i].toLocaleString("en-US", { month: "short" })}</text>`).join("")}
  </svg><p class="small" style="margin:6px 0 0">Last month: <b>${N.fmt(vals[11])}</b> boardings</p>`;

  // Facts
  const f = N.rng("facts:" + s.id);
  const lines = s.lines.length;
  document.getElementById("facts").innerHTML = [
    ["Weekday boardings", N.fmt(total)],
    ["Saturday", N.fmt(Math.round(total * (0.52 + f() * 0.15) / 10) * 10)],
    ["Sunday", N.fmt(Math.round(total * (0.38 + f() * 0.12) / 10) * 10)],
    ["Rank", "#" + (d.stops.map(x => N.ridership(x)).sort((a, b) => b - a).indexOf(total) + 1) + " of " + d.stops.length],
    ["Elevators", `${1 + lines + Math.floor(f() * 2)}, all in service`],
    ["Platforms", lines > 1 ? `${lines} levels` : f() > 0.5 ? "Island" : "Side"],
    ["Bike parking", `${Math.round(20 + f() * 80)} spaces`],
    ["Pods", "On demand, 24 hours"],
    ...(s.hsr ? [["High-Speed Rail", "Yes, at this station"]] : []),
    ...(s.ferry ? [["Ferry", s.ferry === s.name ? "Dock at this station" : `${N.esc(s.ferry)} dock, short walk`]] : []),
    ["Opened", String(s.status === "solid" ? 1897 + Math.floor(f() * 90) : 2026 - Math.floor(f() * 3))]
  ].map(([a, b]) => `<dt>${a}</dt><dd>${b}</dd>`).join("");

  // Nearby, by distance on the diagram.
  const near = d.stops.filter(x => x.id !== s.id && !x.offmap).map(x => [x, Math.hypot(x.x - s.x, x.y - s.y)]).sort((a, b) => a[1] - b[1]).slice(0, 5);
  document.getElementById("nearby").innerHTML = near.map(([x]) => `<li>${x.lines.map(l => N.bullet(l)).join("")}<a class="name" href="${N.stopLink(x)}">${N.esc(x.name)}</a></li>`).join("");
});
