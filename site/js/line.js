/* One line: status, numbers, a strip map of every station by branch, the poster, headways and the busiest stops. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA, d = await N.network();
  const k = N.LINES[N.qs("l")] && N.qs("l") !== "rail" ? N.qs("l") : "red";
  const L = N.LINES[k];
  document.title = `${L.name} | NERTA`;
  document.getElementById("head").style.background = L.color;
  if (k === "yellow") document.getElementById("head").style.color = "#16161a";
  document.getElementById("head").classList.toggle("dark-text", k === "yellow");
  document.getElementById("roundel").src = `/assets/logo/t_${k}.svg`;
  document.getElementById("title").textContent = L.name;
  document.getElementById("crumb").textContent = L.name;
  document.getElementById("blurb").textContent = N.BLURB[k];
  if (k === "yellow") document.querySelectorAll("#head .crumbs, #head .crumbs a, #head .lede").forEach(e => e.style.color = "#16161a");

  const s = N.lineStatus(k);
  const st = document.getElementById("status");
  st.classList.add(k);
  st.innerHTML = `<span class="tag ${s.level}">${s.label}</span><h3>${s.level === "ok" ? "Trains are running on schedule" : N.esc(s.detail)}</h3><p>Updated ${new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}. <a href="/alerts.html">All alerts</a></p>`;

  // Segments: longest first so the trunk leads, branches after.
  const segs = d.segments.filter(x => x.line === k).sort((a, b) => b.stops.length - a.stops.length);
  const stops = [...new Set(segs.flatMap(x => x.stops))].map(id => d.byId[id]);
  const riders = stops.reduce((a, x) => a + N.ridership(x), 0);
  const r = N.rng("line:" + k);
  const ends = new Set(); segs.forEach(x => { ends.add(x.stops[0]); ends.add(x.stops[x.stops.length - 1]); });
  const termini = [...ends].filter(id => segs.filter(x => x.stops.includes(id)).length === 1);
  document.getElementById("stats").innerHTML = [
    ["Stations", stops.length, termini.length + " terminals"],
    ["Weekday riders", N.fmt(Math.round(riders / 100) * 100), (r() > 0.3 ? "+" : "-") + (1 + r() * 5).toFixed(1) + "% from last year"],
    ["On-time", (90 + r() * 8).toFixed(1) + "%", "Last 30 days"],
    ["Peak frequency", "Every " + L.headway + " min", "Every " + Math.round(L.headway * 1.5) + " min off-peak"]
  ].map(([a, b, c]) => `<div class="stat"><div class="k">${a}</div><div class="v" style="font-size:1.6rem">${b}</div><div class="d muted">${c}</div></div>`).join("");

  // Strip map
  document.getElementById("strip").innerHTML = segs.map((seg, i) => {
    const a = d.byId[seg.stops[0]].name, b = d.byId[seg.stops[seg.stops.length - 1]].name;
    const head = segs.length > 1 ? `<li class="branch-head">${i === 0 ? "Main line" : "Branch"}: ${N.esc(a)} to ${N.esc(b)}</li>` : "";
    return `<ul class="strip-map ${k}">${head}${seg.stops.map((id, j) => {
      const x = d.byId[id];
      const other = x.lines.filter(l => l !== k);
      const end = (j === 0 || j === seg.stops.length - 1) && termini.includes(id);
      return `<li class="${end ? "end" : ""}"><a class="stop" href="${N.stopLink(x)}">${N.esc(x.name)}</a>${other.map(l => N.bullet(l)).join("")}</li>`;
    }).join("")}</ul>`;
  }).join("");

  // Poster
  const p = document.getElementById("poster");
  p.href = `/assets/maps/line_${k}.webp`; p.dataset.title = L.name;
  document.getElementById("poster-img").src = `/assets/maps/line_${k}_thumb.webp`;
  document.getElementById("poster-img").alt = `${L.name} map`;
  document.getElementById("pdf").href = `/downloads/line_${k}.pdf`;
  document.getElementById("pdf").addEventListener("click", e => e.stopPropagation());

  // Headways
  const h = L.headway;
  document.getElementById("headways").innerHTML = [
    ["Early morning, 4 to 6:30 AM", h * 2, h * 2.5], ["Morning peak, 6:30 to 9:30 AM", h, h * 1.5], ["Midday, 9:30 AM to 3:30 PM", h * 1.5, h * 1.5],
    ["Evening peak, 3:30 to 6:30 PM", h, h * 1.5], ["Evening, 6:30 PM to midnight", h * 1.5, h * 2], ["Overnight, midnight to 4 AM", 15, 15]
  ].map(([t, a, b]) => `<tr><td>${t}</td><td class="num">${Math.round(a)} min</td><td class="num">${Math.round(b)} min</td></tr>`).join("");

  // Busiest
  const top = stops.map(x => [x, N.ridership(x)]).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const max = top[0][1];
  document.getElementById("busy").innerHTML = top.map(([x, n]) =>
    `<div class="bar ${k}"><a href="${N.stopLink(x)}">${N.esc(x.name)}</a><div class="track"><div class="fill" style="width:${n / max * 100}%"></div></div><span class="n">${N.fmt(n)}</span></div>`).join("");
});
