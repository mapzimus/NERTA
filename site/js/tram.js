/* Trams: the overview list of every route, and one page per route with its stops, transfers, next trams and a timetable.
   Routes, stops and their order come from /data/network.json. Rider numbers are made up. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA, d = await N.network();
  const name = id => d.byId[id].name;
  const trams = Object.values(d.lines).filter(l => l.mode === "tram");
  const stopsOf = l => [...new Set(l.legs.flat())];
  const byNumber = (a, b) => (parseInt(a.number, 10) - parseInt(b.number, 10)) || String(a.number).localeCompare(String(b.number));
  const now = () => new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });

  /* ---------- overview ---------- */
  const box = document.getElementById("tram-lines");
  if (box) {
    document.getElementById("tram-lede").textContent = d.tramService || "";
    const rows = trams.map(l => {
      const ids = stopsOf(l);
      return { l, n: ids.length, text: [l.number, l.name, l.title, l.via, ...ids.map(name)].join(" ").toLowerCase() };
    });
    const q = document.getElementById("tram-q"), sort = document.getElementById("tram-sort");
    const draw = () => {
      const t = q.value.trim().toLowerCase();
      const how = sort.value;
      const hits = rows.filter(r => !t || t.split(/\s+/).every(w => r.text.includes(w))).sort((a, b) =>
        how === "name" ? a.l.title.localeCompare(b.l.title) || byNumber(a.l, b.l)
          : how === "stops" ? b.n - a.n || byNumber(a.l, b.l) : byNumber(a.l, b.l));
      document.getElementById("tram-count").textContent = hits.length === rows.length ? `${rows.length} routes` : `${hits.length} of ${rows.length} routes`;
      box.innerHTML = hits.length ? hits.map(({ l, n }) => {
        const s = N.lineStatus(l.key);
        return `<li>${N.bullet(l.key, true)}<div style="flex:1;min-width:0"><a class="name" href="/tram-line.html?l=${l.key}">${N.esc(l.name)}</a>
          <div class="small muted">${N.esc(l.via)}</div></div><span class="small muted" style="white-space:nowrap">${n} stops</span>
          <span class="state" style="margin-left:0;white-space:nowrap"><i class="dot ${s.level}"></i>${s.level === "ok" ? "On schedule" : s.label}</span></li>`;
      }).join("") : `<li class="muted">No routes match. Try a route number like 66, or a stop name.</li>`;
    };
    q.addEventListener("input", draw);
    sort.addEventListener("change", draw);
    if (N.qs("q")) q.value = N.qs("q");
    draw();
    return;
  }

  /* ---------- one route ---------- */
  const l = d.lines[N.qs("l")] && d.lines[N.qs("l")].mode === "tram" ? d.lines[N.qs("l")] : trams.slice().sort(byNumber)[0];
  const key = l.key, leg = l.legs[0], ids = stopsOf(l);
  const a = leg[0], b = leg[leg.length - 1];
  document.title = `${l.name} | NERTA`;
  document.getElementById("title").textContent = l.name;
  document.getElementById("title").insertAdjacentHTML("beforeend", N.freeTag(l.key));
  document.getElementById("crumb").textContent = l.name;
  document.getElementById("head").style.background = l.color;
  document.getElementById("head-bullet").innerHTML = N.bullet(key, true);
  document.getElementById("blurb").textContent = l.via + ".";
  document.getElementById("street-map").href = `/explore.html?line=${encodeURIComponent(key)}`;

  const st = N.lineStatus(key);
  const note = st.level === "ok" ? "Trams are running on schedule" : st.label === "Shuttle pods" ? "Shuttle pods replace trams on a short stretch this weekend" : N.esc(st.detail).replace(/train/g, "tram");
  document.getElementById("status").innerHTML = `<span class="tag ${st.level}">${st.level === "ok" ? "On schedule" : st.label}</span><h3>${note}</h3><p>Updated ${now()}. <a href="/alerts.html">All alerts</a></p>`;

  const head = 8;
  const rr = N.rng("tram:" + key);
  document.getElementById("stats").innerHTML = [
    ["Stops", ids.length, `${name(a)} to ${name(b)}`],
    ["Weekday riders", N.fmt(Math.round((1500 + rr() * 9000) / 10) * 10), "Average, last month"],
    ["On-time", (88 + rr() * 11).toFixed(1) + "%", "Last 30 days"],
    ["Frequency", `Every ${head} min`, "24 hours a day"]
  ].map(([k, v, c]) => `<div class="stat"><div class="k">${k}</div><div class="v" style="font-size:1.6rem">${v}</div><div class="d muted">${N.esc(c)}</div></div>`).join("");

  // Strip map: every stop in order, with subway, rail and ferry marks and the other tram routes that stop there.
  const ends = new Set(l.terminals);
  const marks = x => N.badges(Object.assign({}, x, { lines: x.lines.filter(k => k !== "tram") }));
  const others = x => x.lines.filter(k => k !== key && k.startsWith("tram-") && d.lines[k])
    .map(k => d.lines[k]).sort(byNumber).map(o => `<a href="/tram-line.html?l=${o.key}" style="text-decoration:none">${N.bullet(o.key)}</a>`).join("");
  document.getElementById("strip").innerHTML = `<ul class="strip-map" style="--c:${l.color}">${leg.map(id => {
    const x = d.byId[id];
    return `<li id="${id}" class="${ends.has(id) ? "end" : ""}"><a class="stop" href="${N.stopLink(x)}">${N.esc(x.name)}</a>${marks(x)}${others(x)}</li>`;
  }).join("")}</ul>`;
  if (location.hash) { const el = document.getElementById(location.hash.slice(1)); if (el) { el.scrollIntoView({ block: "center" }); el.style.background = "#fff4d6"; } }

  // Next trams: one row each way, leaving from each end of the route.
  const rows = [a, b].map(from => {
    const dir = N.directions(d, d.byId[from]).filter(x => x.line === key);
    return dir.length ? { from, to: dir[0].to } : null;
  }).filter(Boolean);
  const board = () => {
    document.getElementById("board").innerHTML = `<div class="head"><span>Next trams</span><span>${now()}</span></div>` +
      rows.map(r => { const m = N.departures(r.from, key, r.to, 3); return `<div class="dir">${N.bullet(key)}<div class="to">To ${N.esc(r.to)}<small>From ${N.esc(name(r.from))}</small>${N.crowdNote(r.from, key, m, r.to)}</div><div class="mins">${m.map(v => N.crowdTime(r.from, key, v, r.to)).join("")}</div></div>`; }).join("");
  };
  board(); setInterval(board, 20000);

  // Timetable from the clock: a tram every 8 minutes, 2 to 3 minutes between stops. Running times are made up.
  let dir = "out";
  document.getElementById("dir-out").textContent = "To " + name(b);
  document.getElementById("dir-in").textContent = "To " + name(a);
  const fmtT = m => { const h = Math.floor(m / 60) % 24, mm = m % 60; return `${h % 12 || 12}:${String(mm).padStart(2, "0")}${h < 12 ? "a" : "p"}`; };
  const draw = () => {
    const order = dir === "out" ? leg : [...leg].reverse();
    const t = new Date(), mins = t.getHours() * 60 + t.getMinutes();
    const offset = Math.floor(N.rng("tt:" + key + dir)() * head);
    const first = Math.ceil((mins - offset) / head) * head + offset;
    const trips = [...Array(6)].map((_, n) => first + n * head);
    let cum = 0;
    const body = order.map((id, i) => {
      if (i) cum += 2 + Math.floor(N.rng("gap:" + key + [order[i - 1], id].sort().join())() * 2);
      const c = cum;
      return `<tr><td><a href="${N.stopLink(d.byId[id])}">${N.esc(name(id))}</a></td>${trips.map(x => `<td class="num">${fmtT(x + c)}</td>`).join("")}</tr>`;
    });
    document.getElementById("timetable").innerHTML = `<thead><tr><th>Stop</th>${trips.map((x, n) => `<th class="num">Tram ${n + 1}</th>`).join("")}</tr></thead><tbody>${body.join("")}</tbody>`;
    document.getElementById("tt-note").textContent = `Toward ${name(order[order.length - 1])}. Trams every ${head} minutes, about ${cum} minutes end to end.`;
    document.getElementById("dir-out").classList.toggle("ghost", dir !== "out");
    document.getElementById("dir-in").classList.toggle("ghost", dir !== "in");
  };
  document.getElementById("dir-out").onclick = () => { dir = "out"; draw(); };
  document.getElementById("dir-in").onclick = () => { dir = "in"; draw(); };
  draw();
});
