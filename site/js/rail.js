/* Regional Rail: the overview page and one page per line, with a timetable generated from the clock. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA;
  const [r, d] = await Promise.all([N.rail(), N.network()]);
  const PURPLE = "#80276c", GOLD = "#ffd23f";
  const rim = l => l.hsr ? `background:${PURPLE};box-shadow:inset 0 0 0 3px ${PURPLE}, inset 0 0 0 7px ${GOLD}` : `background:${PURPLE};box-shadow:inset 0 0 0 3px ${l.hue}`;
  const chip = l => `<span class="bullet" style="${rim(l)};min-width:38px">${l.hsr ? "HSR" : "RR"}</span>`;
  const subway = n => d.byId[N.slug(n)];
  const transfers = n => {
    const s = subway(n);
    if (!s) return "";
    return s.lines.filter(x => x !== "rail").map(x => N.bullet(x)).join("") + (s.ferry ? `<span class="bullet ferry">F</span>` : "");
  };
  const nameLink = n => subway(n) ? `<a class="stop" href="${N.stopLink(subway(n))}">${N.esc(n)}</a>` : `<span class="stop" style="font-weight:700">${N.esc(n)}</span>`;
  const outer = l => l.stops.filter(n => !["North Station", "Boston Central", "South Station"].includes(n));

  /* ---------- overview ---------- */
  const list = document.getElementById("rail-lines");
  if (list) {
    list.innerHTML = r.lines.filter(l => !l.hsr).map(l => {
      const s = N.lineStatus("rail-" + l.key);
      return `<a class="card" href="/rail-line.html?l=${l.key}" style="text-decoration:none;color:inherit;border-left:8px solid ${l.hue};display:flex;gap:14px;align-items:flex-start">
        ${chip(l)}<div><h3 style="margin:0 0 4px">${N.esc(l.name)}</h3>
        <p class="small muted" style="margin:0 0 8px">Boston Central to ${N.esc(l.terminal)}${l.ends.length > 1 ? " and " + l.ends.slice(0, -1).map(N.esc).join(", ") : ""}</p>
        <span class="small"><b>${outer(l).length}</b> stations &middot; <span class="tag ${s.level}">${s.label}</span></span></div></a>`;
    }).join("");
    document.getElementById("hsr").innerHTML = r.lines.filter(l => l.hsr).map(l =>
      `<a class="stat" href="/rail-line.html?l=${l.key}" style="text-decoration:none;color:inherit;border-top:6px solid ${GOLD}">
        <div class="k">High-Speed Rail</div><div class="v" style="font-size:1.5rem">${N.esc(l.name.replace("High-Speed Rail to ", ""))}</div>
        <div class="d muted">Boards at ${l.stops.filter(n => !["North Station", "South Station"].includes(n)).slice(0, 3).map(N.esc).join(", ")}</div></a>`).join("");
    return;
  }

  /* ---------- one line ---------- */
  const key = r.byKey[N.qs("l")] ? N.qs("l") : "wor";
  const l = r.byKey[key];
  document.title = `${l.name} | NERTA`;
  document.getElementById("title").textContent = l.name;
  document.getElementById("crumb").textContent = l.name;
  document.getElementById("head").style.boxShadow = `inset 0 -8px 0 ${l.hsr ? GOLD : l.hue}`;
  document.getElementById("blurb").textContent = l.hsr
    ? `Fast trains from Boston Central to ${l.name.replace("High-Speed Rail to ", "")}. Boston-area stops are listed below.`
    : `Through trains from ${l.stops.includes("North Station") ? "North Station, Boston Central and South Station" : "Boston Central"} to ${l.terminal}.`;

  const st = N.lineStatus("rail-" + key);
  document.getElementById("status").innerHTML = `<span class="tag ${st.level}">${st.label}</span><h3>${st.level === "ok" ? "Trains are running on schedule" : N.esc(st.detail)}</h3><p>Updated ${new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}. <a href="/alerts.html">All alerts</a></p>`;

  const head = l.hsr ? 60 : N.isPeak() ? 20 : 30;
  const rr = N.rng("rail:" + key);
  document.getElementById("stats").innerHTML = [
    ["Stations", l.stops.length, l.hsr ? "In the Boston area" : "Including the three downtown"],
    ["Weekday riders", N.fmt(Math.round((l.hsr ? 9000 : 6000 + l.stops.length * 900) * (0.8 + rr() * 0.4) / 100) * 100), "Average, last month"],
    ["On-time", (91 + rr() * 7).toFixed(1) + "%", "Last 30 days"],
    ["Trains", "Every " + head + " min", l.hsr ? "All day" : N.isPeak() ? "Peak service" : "Off-peak service"]
  ].map(([a, b, c]) => `<div class="stat"><div class="k">${a}</div><div class="v" style="font-size:1.6rem">${b}</div><div class="d muted">${c}</div></div>`).join("");

  document.getElementById("strip").style.setProperty("--c", l.hsr ? GOLD : PURPLE);
  document.getElementById("strip").innerHTML = l.stops.map((n, i) => {
    const end = l.ends.includes(n) || i === l.stops.length - 1;
    return `<li id="${N.slug(n)}" class="${end ? "end" : ""}">${nameLink(n)}${transfers(n)}</li>`;
  }).join("");
  if (location.hash) { const el = document.getElementById(location.hash.slice(1)); if (el) { el.scrollIntoView({ block: "center" }); el.style.background = "#fff4d6"; } }

  // Timetable: the next six trains, with times at each stop. Running time grows about 3 to 5 minutes per stop.
  const gaps = l.stops.map((n, i) => i === 0 ? 0 : 3 + Math.floor(N.rng("gap:" + key + n)() * 3));
  const draw = dir => {
    const stops = dir === "out" ? l.stops : [...l.stops].reverse();
    const g = dir === "out" ? gaps : [0, ...gaps.slice(1).reverse()];
    const now = new Date(); now.setSeconds(0, 0);
    const offset = Math.floor(N.rng("tt:" + key + dir)() * head);
    const mins = now.getHours() * 60 + now.getMinutes();
    let first = Math.ceil((mins - offset) / head) * head + offset;
    const trips = [...Array(6)].map((_, k) => first + k * head);
    const fmtT = m => { const h = Math.floor(m / 60) % 24, mm = m % 60; return `${h % 12 || 12}:${String(mm).padStart(2, "0")}${h < 12 ? "a" : "p"}`; };
    let cum = 0;
    const rows = stops.map((n, i) => { cum += g[i]; const c = cum; return `<tr><td>${subway(n) ? `<a href="${N.stopLink(subway(n))}">${N.esc(n)}</a>` : N.esc(n)}</td>${trips.map(t => `<td class="num">${fmtT(t + c)}</td>`).join("")}</tr>`; });
    document.getElementById("timetable").innerHTML = `<thead><tr><th>Station</th>${trips.map((t, k) => `<th class="num">Train ${(N.hash(key) % 40) * 20 + 100 + Math.floor(t / head) * 2 + (dir === "in" ? 1 : 0)}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody>`;
    document.getElementById("tt-note").textContent = `${dir === "out" ? "Outbound" : "Inbound"} toward ${stops[stops.length - 1]}. Trains every ${head} minutes. Times are today's.`;
    document.getElementById("dir-out").classList.toggle("ghost", dir !== "out");
    document.getElementById("dir-in").classList.toggle("ghost", dir !== "in");
  };
  document.getElementById("dir-out").onclick = () => draw("out");
  document.getElementById("dir-in").onclick = () => draw("in");
  draw("out");
});
