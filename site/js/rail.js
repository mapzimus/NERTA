/* Regional Rail and High-Speed Rail: the overview page and one page per line, with a timetable generated from the clock.
   Lines, stop order, branches and ends come from the rail poster. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA, d = await N.network();
  const GOLD = "#ffd23f";
  const name = id => d.byId[id].name;
  const DOWNTOWN = ["north-station", "boston-central", "south-station"];
  // Where a line goes, in plain words: its outer ends, plus where it runs on to past the map.
  const reach = l => {
    const outer = l.terminals.filter(t => !DOWNTOWN.includes(t) && (through(l) || t !== l.legs[0][0])).map(name);
    if (l.beyond) outer.unshift(DOWNTOWN.includes(l.beyond.at) ? l.beyond.to : `${name(l.beyond.at)} (continuing to ${l.beyond.to})`);
    return outer;
  };
  const list = (xs) => xs.length > 1 ? xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1] : xs[0] || "";
  const through = l => l.legs[0].slice(0, 3).every(id => DOWNTOWN.includes(id));

  /* ---------- overview ---------- */
  const box = document.getElementById("rail-lines");
  if (box) {
    box.innerHTML = d.railLines.filter(l => l.mode === "rail").map(l => {
      const s = N.lineStatus(l.key);
      const n = new Set(l.legs.flat()).size;
      return `<a class="card" href="/rail-line.html?l=${l.key}" style="text-decoration:none;color:inherit;border-left:8px solid ${l.hue};display:flex;gap:14px;align-items:flex-start">
        ${N.bullet(l.key, true)}<div><h3 style="margin:0 0 4px">${N.esc(l.name)}</h3>
        <p class="small muted" style="margin:0 0 8px">${through(l) ? "Boston Central" : N.esc(name(l.legs[0][0]))} to ${N.esc(list(reach(l)))}</p>
        <span class="small"><b>${n}</b> stations &middot; <span class="tag ${s.level}">${s.label}</span></span></div></a>`;
    }).join("");
    document.getElementById("hsr").innerHTML = d.railLines.filter(l => l.mode === "hsr").map(l =>
      `<a class="stat" href="/rail-line.html?l=${l.key}" style="text-decoration:none;color:inherit;border-top:6px solid ${GOLD}">
        <div class="k">High-Speed Rail</div><div class="v" style="font-size:1.35rem">${N.esc(l.beyond ? l.beyond.to : l.name)}</div>
        <div class="d muted">${l.beyond && l.beyond.via ? "Via " + N.esc(l.beyond.via) + ". " : ""}Boards at ${N.esc(list([...new Set(l.legs.flat())].map(name)))}</div></a>`).join("");
    return;
  }

  /* ---------- one line ---------- */
  const l = d.lines[N.qs("l")] && d.railLines.includes(d.lines[N.qs("l")]) ? d.lines[N.qs("l")] : d.lines["rail-wor"];
  const key = l.key;
  document.title = `${l.name} | NERTA`;
  document.getElementById("title").textContent = l.name;
  document.getElementById("crumb").textContent = l.name;
  document.getElementById("head").style.boxShadow = `inset 0 -8px 0 ${l.hue}`;
  document.getElementById("blurb").textContent = l.mode === "hsr"
    ? `Fast trains to ${l.beyond.to}${l.beyond.via ? ", via " + l.beyond.via : ""}. They stop only at the stations below.`
    : through(l) ? `Through trains from ${l.legs[0].slice(0, 3).map(name).join(", ")} to ${list(reach(l))}.`
      : `Crosstown trains from ${name(l.legs[0][0])} to ${list(reach(l))}.`;

  if (l.poster) {
    const card = document.getElementById("poster");
    card.style.display = ""; card.href = `/assets/maps/${l.poster}.webp`; card.dataset.title = l.name;
    document.getElementById("poster-img").src = `/assets/maps/${l.poster}_thumb.webp`;
    document.getElementById("poster-img").alt = `${l.name} map`;
  }
  const st = N.lineStatus(key);
  document.getElementById("status").innerHTML = `<span class="tag ${st.level}">${st.label}</span><h3>${st.level === "ok" ? "Trains are running on schedule" : N.esc(st.detail)}</h3><p>Updated ${new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}. <a href="/alerts.html">All alerts</a></p>`;

  const head = l.mode === "hsr" ? 60 : N.isPeak() ? 20 : 30;
  const all = [...new Set(l.legs.flat())];
  const rr = N.rng("rail:" + key);
  document.getElementById("stats").innerHTML = [
    ["Stations", all.length, l.legs.length > 1 ? `${l.legs.length - 1} branch${l.legs.length > 2 ? "es" : ""}` : "One line"],
    ["Weekday riders", N.fmt(Math.round((l.mode === "hsr" ? 9000 : 5000 + all.length * 900) * (0.7 + rr() * 0.6) / 100) * 100), "Average, last month"],
    ["On-time", (90 + rr() * 8).toFixed(1) + "%", "Last 30 days"],
    ["Trains", "Every " + head + " min", l.mode === "hsr" ? "All day" : N.isPeak() ? "Peak service" : "Off-peak service"]
  ].map(([a, b, c]) => `<div class="stat"><div class="k">${a}</div><div class="v" style="font-size:1.6rem">${b}</div><div class="d muted">${c}</div></div>`).join("");

  // Strip maps: main line, then each branch from its junction.
  const ends = new Set(l.terminals);
  const marks = x => N.servedBy(x).filter(m => N.ORDER.includes(m)).map(m => N.bullet(m)).join("") + (x.dock || x.ferry ? N.bullet("ferry") : "");
  const strip = document.getElementById("strip");
  strip.outerHTML = `<div id="strip">${l.legs.map((leg, i) => `${l.legs.length > 1 ? `<p class="eyebrow" style="margin-top:${i ? 16 : 0}px">${i ? "Branch from " + N.esc(name(leg[0])) : "Main line"}</p>` : ""}
    <ul class="strip-map" style="--c:${l.mode === "hsr" ? GOLD : "#80276c"}">${leg.map((id, j) => {
      const x = d.byId[id];
      const runOn = l.beyond && l.beyond.at === id ? ` <span class="tag">Continues to ${N.esc(l.beyond.to)}</span>` : "";
      return `<li id="${id}" class="${ends.has(id) || runOn ? "end" : ""}"><a class="stop" href="${N.stopLink(x)}">${N.esc(x.name)}</a>${marks(x)}${runOn}</li>`;
    }).join("")}</ul>`).join("")}</div>`;
  if (location.hash) { const el = document.getElementById(location.hash.slice(1)); if (el) { el.scrollIntoView({ block: "center" }); el.style.background = "#fff4d6"; } }

  // Timetable: pick the main line or a branch (main line to the junction, then the branch). Running time is made up.
  const routes = l.legs.map((leg, i) => {
    if (i === 0) return { label: `${name(leg[0])} to ${name(leg[leg.length - 1])}`, ids: leg };
    const main = l.legs[0], j = main.indexOf(leg[0]);
    return { label: `${name(main[0])} to ${name(leg[leg.length - 1])}`, ids: (j > -1 ? main.slice(0, j) : []).concat(leg) };
  });
  const pick = document.getElementById("route");
  pick.innerHTML = routes.map((r, i) => `<option value="${i}">${N.esc(r.label)}</option>`).join("");
  pick.parentElement.style.display = routes.length > 1 ? "" : "none";
  let dir = "out";
  const draw = () => {
    const route = routes[+pick.value || 0];
    const ids = dir === "out" ? route.ids : [...route.ids].reverse();
    const now = new Date();
    const mins = now.getHours() * 60 + now.getMinutes();
    const offset = Math.floor(N.rng("tt:" + key + dir)() * head);
    const first = Math.ceil((mins - offset) / head) * head + offset;
    const trips = [...Array(6)].map((_, n) => first + n * head);
    const fmtT = m => { const h = Math.floor(m / 60) % 24, mm = m % 60; return `${h % 12 || 12}:${String(mm).padStart(2, "0")}${h < 12 ? "a" : "p"}`; };
    let cum = 0;
    const rows = ids.map((id, i) => {
      if (i) cum += (l.mode === "hsr" ? 9 : 3) + Math.floor(N.rng("gap:" + key + [ids[i - 1], id].sort().join())() * 3);
      const c = cum;
      return `<tr><td><a href="${N.stopLink(d.byId[id])}">${N.esc(name(id))}</a></td>${trips.map(t => `<td class="num">${fmtT(t + c)}</td>`).join("")}</tr>`;
    });
    const base = (N.hash(key) % 40) * 20 + 100;
    document.getElementById("timetable").innerHTML = `<thead><tr><th>Station</th>${trips.map(t => `<th class="num">Train ${base + Math.floor(t / head) * 2 + (dir === "in" ? 1 : 0)}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody>`;
    const to = dir === "out" && l.beyond && route.ids[route.ids.length - 1] === l.beyond.at ? l.beyond.to : name(ids[ids.length - 1]);
    document.getElementById("tt-note").textContent = `Toward ${to}. Trains every ${head} minutes.`;
    document.getElementById("dir-out").classList.toggle("ghost", dir !== "out");
    document.getElementById("dir-in").classList.toggle("ghost", dir !== "in");
  };
  document.getElementById("dir-out").onclick = () => { dir = "out"; draw(); };
  document.getElementById("dir-in").onclick = () => { dir = "in"; draw(); };
  pick.onchange = draw;
  draw();
});
