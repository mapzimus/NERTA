/* Home page: trip planner, line status, line cards, headline numbers. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA;
  const d = await N.network();

  // Line status
  const st = document.getElementById("status");
  st.innerHTML = N.ORDER.map(k => {
    const s = N.lineStatus(k);
    return `<li>${N.bullet(k)}<a class="name" href="/line.html?l=${k}">${N.LINES[k].name}</a><span class="state"><i class="dot ${s.level}"></i>${s.label}</span></li>`;
  }).join("") + [["rail", "/rail.html", "Regional Rail"], ["ferry", "/ferry.html", "Ferry"]].map(([k, href, name]) => {
    const bad = ["rail-wor", "rail-fra", "rail-pro", "rail-low", "ferry-hw", "ferry-nse"].map(x => N.lineStatus(x)).filter(s => s.level !== "ok").length;
    const b = k === "rail" ? '<span class="bullet rail">RR</span>' : '<span class="bullet ferry">F</span>';
    return `<li>${b}<a class="name" href="${href}">${name}</a><span class="state"><i class="dot ${bad ? "warn" : "ok"}"></i>${bad ? "Some delays" : "Normal service"}</span></li>`;
  }).join("");
  document.getElementById("status-time").textContent = "Updated " + new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });

  // Charlie Points tile: show the balance if this browser has one
  try {
    const cp = JSON.parse(window.localStorage.getItem("nerta-charlie") || "null");
    if (cp && typeof cp.balance === "number") document.getElementById("cp-home").textContent = `Balance: ${N.fmt(cp.balance)} Charlie Points`;
  } catch (e) { /* storage blocked: keep the default text */ }

  // Line cards
  document.getElementById("line-cards").innerHTML = N.ORDER.slice(0, 4).map(k =>
    `<a class="map-card" href="/line.html?l=${k}"><div class="thumb"><img src="/assets/maps/line_${k}_thumb.webp" alt="${N.LINES[k].name} map" loading="lazy"></div><div class="body"><b>${N.LINES[k].name}</b></div></a>`).join("");

  // Headline numbers
  const subway = d.stops.filter(s => N.servedBy(s).some(l => N.ORDER.includes(l)));
  const total = subway.reduce((a, s) => a + N.ridership(s), 0);
  const ot = 92 + N.rng("ontime:" + new Date().toDateString())() * 5;
  document.getElementById("stats").innerHTML = [
    ["Weekday riders", N.fmt(Math.round(total / 1000) * 1000), "+3.8% from last year", "up"],
    ["On-time today", ot.toFixed(1) + "%", "Goal: 90%", "up"],
    ["Stations", N.fmt(d.stops.filter(s => s.kind === "station").length), "Every one step-free", ""],
    ["Trains in service", N.fmt(Math.round(310 + (N.isPeak() ? 140 : 0) + N.rng("trains" + new Date().getHours())() * 30)), N.isPeak() ? "Peak service" : "Off-peak service", ""]
  ].map(([k, v, dd, c]) => `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div><div class="d ${c}">${dd}</div></div>`).join("");

  // Trip planner
  const from = document.getElementById("from"), to = document.getElementById("to");
  // Each end has its own stop-type filter: trams are almost half of all stops, so a long list is easy to narrow
  const KINDS = [["all", "All stops", () => true], ["subway", "Subway", m => m.has("subway")], ["rail", "Regional Rail", m => m.has("rail") || m.has("hsr")],
                 ["ferry", "Ferry docks", m => m.has("ferry")], ["tram", "Tram stops", m => m.has("tram")]];
  const modes = s => new Set(s.lines.map(k => d.lines[k] && d.lines[k].mode).filter(Boolean));
  const fill = (sel, kind) => {
    const keep = sel.value, test = KINDS.find(k => k[0] === kind)[2];
    sel.innerHTML = d.stops.filter(s => test(modes(s))).map(s => `<option value="${s.id}">${N.esc(s.name)}${s.kind === "dock" ? " (ferry dock)" : ""}</option>`).join("");
    if ([...sel.options].some(o => o.value === keep)) sel.value = keep;
  };
  [[from, "from-mode"], [to, "to-mode"]].forEach(([sel, id]) => {
    const m = document.getElementById(id);
    m.innerHTML = KINDS.map(([k, label]) => `<option value="${k}">${label}</option>`).join("");
    m.onchange = () => fill(sel, m.value);
    fill(sel, "all");
  });
  from.value = "harvard"; to.value = "airport";
  document.getElementById("swap").onclick = () => {
    const fm = document.getElementById("from-mode"), tm = document.getElementById("to-mode"), a = from.value, b = to.value, k = fm.value;
    fm.value = tm.value; tm.value = k; fill(from, fm.value); fill(to, tm.value); from.value = b; to.value = a;
  };
  document.getElementById("trip-form").addEventListener("submit", e => {
    e.preventDefault();
    const out = document.getElementById("trip-result");
    const trip = N.planTrip(d, from.value, to.value);
    if (trip && trip.closed) { out.innerHTML = `<p class="muted">${N.esc(trip.detail)}</p>`; return; }
    if (!trip) { out.innerHTML = `<p class="muted">${from.value === to.value ? "Pick two different stations." : "No route between those two."}</p>`; return; }
    const arrive = new Date(Date.now() + trip.minutes * 60000).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    const rides = trip.legs.filter(l => l.line !== "walk");
    const changes = rides.length - 1;
    const fare = N.tripFare(trip.legs);
    const fareText = fare ? `${N.coin()} ${fare} Charlie Points` : `<span class="free-tag">FREE</span> no Charlie Points needed`;
    let html = `<p style="margin:0 0 6px"><b style="font-size:1.3rem">${trip.minutes} min</b> &middot; arrive about ${arrive} &middot; ${changes <= 0 ? "no changes" : changes + (changes === 1 ? " change" : " changes")} &middot; ${fareText}</p>`;
    trip.legs.forEach((leg, i) => {
      if (leg.line === "walk") { html += `<div class="walk">Walk to ${N.esc(d.byId[leg.to].name)}${d.byId[leg.to].kind === "dock" ? " ferry dock" : ""}, about ${Math.round(leg.mins)} min</div>`; return; }
      if (i && trip.legs[i - 1].line !== "walk") html += `<div class="walk">Change at ${N.esc(d.byId[leg.from].name)}, about 5 min</div>`;
      const L = N.LINES[leg.line];
      html += `<div class="leg ${leg.line}"><div class="legline">${N.bullet(leg.line)}<i></i></div><div>
        <b>${(hs => /^(Ring|Loop) via /.test(hs) ? `${L.name}, ${hs[0].toLowerCase()}${N.esc(hs.slice(1))}` : `${L.name} toward ${N.esc(hs)}`)(N.headsign(d, leg.line, leg.from, leg.next))}</b>
        <span class="small muted">Board at <a href="${N.stopLink(d.byId[leg.from])}">${N.esc(d.byId[leg.from].name)}</a>, ride ${leg.stops} ${leg.stops === 1 ? "stop" : "stops"} (${Math.round(leg.mins)} min) to <a href="${N.stopLink(d.byId[leg.to])}">${N.esc(d.byId[leg.to].name)}</a></span></div></div>`;
    });
    out.innerHTML = html;
  });
});
