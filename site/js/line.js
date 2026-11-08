/* One subway line: status, made-up numbers, every leg exactly as on its poster, the poster, headways and the busiest stops. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA, d = await N.network();
  const k = N.ORDER.includes(N.qs("l")) ? N.qs("l") : "red";
  const L = N.LINES[k];
  const name = id => d.byId[id].name;
  const ends = L.terminals.map(name);
  document.title = `${L.name} | NERTA`;
  const head = document.getElementById("head");
  head.style.background = L.color;
  if (k === "yellow") head.querySelectorAll("*").forEach(e => e.style.color = "#16161a");
  if (k === "yellow") head.style.color = "#16161a";
  document.getElementById("roundel").src = `/assets/logo/t_${k}.svg`;
  document.getElementById("title").textContent = L.name;
  document.getElementById("title").insertAdjacentHTML("beforeend", N.freeTag(k));
  document.getElementById("crumb").textContent = L.name;
  document.getElementById("blurb").textContent = ends.length ? `To ${ends.slice(0, -1).join(", ")}${ends.length > 1 ? " and " : ""}${ends[ends.length - 1]}.` : "A ring line.";

  const s = N.lineStatus(k);
  const st = document.getElementById("status");
  st.classList.add(k);
  st.innerHTML = `<span class="tag ${s.level}">${s.label}</span><h3>${s.level === "ok" ? "Trains are running on schedule" : N.esc(s.detail)}</h3><p>Updated ${new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}. <a href="/alerts.html">All alerts</a></p>`;

  const ids = [...new Set(L.legs.flat())];
  const stops = ids.map(id => d.byId[id]);
  const riders = stops.reduce((a, x) => a + N.ridership(x) / Math.max(1, N.servedBy(x).length), 0);
  const r = N.rng("line:" + k);
  document.getElementById("stats").innerHTML = [
    ["Stations", stops.length, ends.length + " terminals"],
    ["Weekday riders", N.fmt(Math.round(riders / 100) * 100), (r() > 0.3 ? "+" : "-") + (1 + r() * 5).toFixed(1) + "% from last year"],
    ["On-time", (90 + r() * 8).toFixed(1) + "%", "Last 30 days"],
    ["Peak frequency", "Every " + L.headway + " min", "Every " + Math.round(L.headway * 1.5) + " min off-peak"]
  ].map(([a, b, c]) => `<div class="stat"><div class="k">${a}</div><div class="v" style="font-size:1.6rem">${b}</div><div class="d muted">${c}</div></div>`).join("");

  // Each leg as the poster draws it, headed by where it runs from and to.
  const term = new Set(L.terminals);
  document.getElementById("strip").innerHTML = L.legs.map(leg => {
    const headline = L.legs.length > 1 ? `<li class="branch-head">${N.esc(name(leg[0]))} to ${N.esc(name(leg[leg.length - 1]))}</li>` : "";
    return `<ul class="strip-map ${k}">${headline}${leg.map(id => {
      const x = d.byId[id];
      const other = N.servedBy(x).filter(l => l !== k);
      const subway = other.filter(l => N.ORDER.includes(l)).map(l => N.bullet(l)).join("");
      const rest = (other.some(l => N.LINES[l].mode === "rail" || N.LINES[l].mode === "hsr") || x.lines.includes("rail") ? N.bullet("rail") : "") + (x.dock || x.ferry ? N.bullet("ferry") : "");
      return `<li class="${term.has(id) ? "end" : ""}"><a class="stop" href="${N.stopLink(x)}">${N.esc(x.name)}</a>${subway}${rest}</li>`;
    }).join("")}</ul>`;
  }).join("");

  const p = document.getElementById("poster");
  p.href = `/assets/maps/line_${k}.webp`; p.dataset.title = L.name;
  document.getElementById("poster-img").src = `/assets/maps/line_${k}_thumb.webp`;
  document.getElementById("poster-img").alt = `${L.name} map`;

  const h = L.headway;
  document.getElementById("headways").innerHTML = [
    ["Early morning, 4 to 6:30 AM", h * 2, h * 2.5], ["Morning peak, 6:30 to 9:30 AM", h, h * 1.5], ["Midday, 9:30 AM to 3:30 PM", h * 1.5, h * 1.5],
    ["Evening peak, 3:30 to 6:30 PM", h, h * 1.5], ["Evening, 6:30 PM to midnight", h * 1.5, h * 2], ["Overnight, midnight to 4 AM", 15, 15]
  ].map(([t, a, b]) => `<tr><td>${t}</td><td class="num">${Math.round(a)} min</td><td class="num">${Math.round(b)} min</td></tr>`).join("");

  const top = stops.map(x => [x, N.ridership(x)]).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const max = top[0][1];
  document.getElementById("busy").innerHTML = top.map(([x, n]) =>
    `<div class="bar ${k}"><a href="${N.stopLink(x)}">${N.esc(x.name)}</a><div class="track"><div class="fill" style="width:${n / max * 100}%"></div></div><span class="n">${N.fmt(n)}</span></div>`).join("");

  // Crowding by time of day, on a typical weekday.
  const crowd = N.lineCrowding(k);
  document.getElementById("busy").closest(".card").insertAdjacentHTML("afterend",
    `<div class="card" style="margin-top:20px"><h2>Crowding by time of day</h2><p class="small muted" style="margin-top:-4px">How full trains usually get at the busier stations, on a weekday</p>
    <div class="crowd-row" style="--c:${L.color}">${crowd.map(c => `<div class="col" title="${c.text}"><i style="height:${14 + c.level * 22}px"></i><b>${c.label}</b>${c.text}</div>`).join("")}</div></div>`);
});
