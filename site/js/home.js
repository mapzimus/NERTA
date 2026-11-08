/* Home page: trip planner, line status, line cards, headline numbers. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA;
  const d = await N.network();

  // Line status
  const st = document.getElementById("status");
  st.innerHTML = N.ORDER.map(k => {
    const s = N.lineStatus(k);
    return `<li>${N.bullet(k)}<a class="name" href="/line.html?l=${k}">${N.LINES[k].name}</a><span class="state"><i class="dot ${s.level}"></i>${s.label}</span></li>`;
  }).join("");
  document.getElementById("status-time").textContent = "Updated " + new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });

  // Line cards
  document.getElementById("line-cards").innerHTML = N.ORDER.slice(0, 4).map(k =>
    `<a class="map-card" href="/line.html?l=${k}"><div class="thumb"><img src="/assets/maps/line_${k}_thumb.webp" alt="${N.LINES[k].name} map" loading="lazy"></div><div class="body"><b>${N.LINES[k].name}</b></div></a>`).join("");

  // Headline numbers
  const subway = d.stops.filter(s => s.lines.some(l => l !== "rail"));
  const total = subway.reduce((a, s) => a + N.ridership(s), 0);
  const ot = 92 + N.rng("ontime:" + new Date().toDateString())() * 5;
  document.getElementById("stats").innerHTML = [
    ["Weekday riders", N.fmt(Math.round(total / 1000) * 1000), "+3.8% vs. last October", "up"],
    ["On-time today", ot.toFixed(1) + "%", "Goal: 90%", "up"],
    ["Stations", "222", "Every one step-free", ""],
    ["Trains in service", N.fmt(Math.round(310 + (N.isPeak() ? 140 : 0) + N.rng("trains" + new Date().getHours())() * 30)), N.isPeak() ? "Peak service" : "Off-peak service", ""]
  ].map(([k, v, dd, c]) => `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div><div class="d ${c}">${dd}</div></div>`).join("");

  // Trip planner
  const from = document.getElementById("from"), to = document.getElementById("to");
  const opts = subway.filter(s => !s.offmap).map(s => `<option value="${s.id}">${N.esc(s.name)}</option>`).join("");
  from.innerHTML = opts; to.innerHTML = opts;
  from.value = "harvard"; to.value = "airport";
  document.getElementById("swap").onclick = () => { const a = from.value; from.value = to.value; to.value = a; };
  document.getElementById("trip-form").addEventListener("submit", e => {
    e.preventDefault();
    const out = document.getElementById("trip-result");
    const trip = N.planTrip(d, from.value, to.value);
    if (!trip) { out.innerHTML = `<p class="muted">Pick two different stations.</p>`; return; }
    const arrive = new Date(Date.now() + trip.minutes * 60000).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    const changes = trip.legs.length - 1;
    let html = `<p style="margin:0 0 6px"><b style="font-size:1.3rem">${trip.minutes} min</b> &middot; arrive about ${arrive} &middot; ${changes === 0 ? "no changes" : changes + (changes === 1 ? " change" : " changes")}</p>`;
    trip.legs.forEach((leg, i) => {
      if (i) html += `<div class="walk">Change at ${N.esc(d.byId[leg.from].name)}, about 5 min</div>`;
      const L = N.LINES[leg.line];
      html += `<div class="leg ${leg.line}"><div class="legline">${N.bullet(leg.line)}<i></i></div><div>
        <b>${L.name} toward ${N.esc(N.headsign(d, leg.line, leg.from, leg.to))}</b>
        <span class="small muted">Board at <a href="${N.stopLink(d.byId[leg.from])}">${N.esc(d.byId[leg.from].name)}</a>, ride ${leg.stops} ${leg.stops === 1 ? "stop" : "stops"} (${Math.round(leg.mins)} min) to <a href="${N.stopLink(d.byId[leg.to])}">${N.esc(d.byId[leg.to].name)}</a></span></div></div>`;
    });
    out.innerHTML = html;
  });
});
