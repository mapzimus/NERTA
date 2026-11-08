/* Shared NERTA site code: header, footer, network data, the fake-data engine and the trip planner. */
(function () {
  "use strict";

  const LINES = {
    red:    { name: "Red Line",    short: "RL", color: "#da291c", headway: 6,  speed: 2.2, poster: "line_red" },
    orange: { name: "Orange Line", short: "OL", color: "#ed8b00", headway: 6,  speed: 2.1, poster: "line_orange" },
    blue:   { name: "Blue Line",   short: "BL", color: "#003da5", headway: 5,  speed: 2.0, poster: "line_blue" },
    green:  { name: "Green Line",  short: "GL", color: "#00843d", headway: 7,  speed: 2.6, poster: "line_green" },
    yellow: { name: "Yellow Line", short: "YL", color: "#f5c400", headway: 5,  speed: 2.0, poster: "line_yellow" },
    cyan:   { name: "Cyan Line",   short: "CL", color: "#00a9c9", headway: 4,  speed: 1.8, poster: "line_cyan" },
    indigo: { name: "Indigo Line", short: "IL", color: "#3f3fb5", headway: 8,  speed: 2.4, poster: "line_indigo" },
    silver: { name: "Silver Line", short: "SL", color: "#7c878e", headway: 4,  speed: 1.6, poster: "line_silver" },
    rail:   { name: "Regional Rail", short: "RR", color: "#80276c", headway: 20, speed: 4.0, poster: null }
  };
  const ORDER = ["red", "orange", "blue", "green", "yellow", "cyan", "indigo", "silver"];
  const BLURB = {
    red: "Alewife and the Arlington and Waltham branches to Ashmont, Mattapan and Braintree, through Harvard, Kendall and downtown.",
    orange: "Reading and Oak Grove through North Station and downtown to Forest Hills, with branches to Saugus, Mattapan and the Southwest.",
    blue: "From Charles/MGH and West Station under the harbor to the Airport, Revere and Lynn.",
    green: "Light rail from Medford and Union Sq through the Central Subway to Boston College, Cleveland Circle, Riverside, Heath St and Needham.",
    yellow: "The ring line: a full circle around the core, linking every radial line without going downtown.",
    cyan: "Seaport and South Boston through Boston Central and the North End to Charlestown and Assembly.",
    indigo: "South Station through Dorchester and Mattapan to Readville.",
    silver: "The airport line: every terminal, rental cars and the Logan ferry dock."
  };
  const SILVER_STOPS = ["Airport", "Rental Cars", "Terminal F", "Terminal E", "Terminal D", "Terminal C", "Terminal B", "Parking", "Terminals", "Terminal A", "Office Center", "Logan Dock"];

  /* ---------- seeded randomness: same numbers every visit ---------- */
  function hash(str) {
    let h = 2166136261;
    for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function rng(seed) {
    let a = typeof seed === "string" ? hash(seed) : seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* ---------- network data ---------- */
  let NET = null;
  async function network() {
    if (NET) return NET;
    const res = await fetch("/data/network.json");
    const d = await res.json();
    d.byId = {};
    d.stops.forEach(s => { d.byId[s.id] = s; });
    // Silver Line stops are poster-only; add the ones the map doesn't carry so its page works.
    d.silver = SILVER_STOPS.map(n => {
      const id = slug(n);
      if (!d.byId[id]) {
        const near = d.byId["terminals"] || d.byId["airport"];
        d.byId[id] = { id, name: n, x: near.x, y: near.y, lines: [], mode: "subway", offmap: true };
        d.stops.push(d.byId[id]);
      }
      if (!d.byId[id].lines.includes("silver")) d.byId[id].lines.push("silver");
      return id;
    });
    d.segments.push({ line: "silver", stops: d.silver });
    d.stops.sort((a, b) => a.name.localeCompare(b.name));
    NET = d;
    return d;
  }
  /* Regional Rail and ferry: loaded on the pages that need them. */
  let RAIL = null, FERRY = null;
  async function rail() {
    if (RAIL) return RAIL;
    RAIL = await (await fetch("/data/rail.json")).json();
    RAIL.byKey = {};
    const MAIN_END = { fit: "Wachusett", pro: "Wickford Junction" };  // the poster lists their branches last
    RAIL.lines.forEach(l => { RAIL.byKey[l.key] = l; l.terminal = MAIN_END[l.key] || (l.ends.length ? l.ends[l.ends.length - 1] : l.stops[l.stops.length - 1]); });
    return RAIL;
  }
  async function ferry() {
    if (FERRY) return FERRY;
    FERRY = await (await fetch("/data/ferry.json")).json();
    FERRY.byKey = {};
    FERRY.routes.forEach(r => {
      FERRY.byKey[r.key] = r;
      const parts = [r.stops || [], ...Object.values(r.banks || {}), ...Object.values(r.branches || {})];
      r.all = [...new Set(parts.flat())];
    });
    return FERRY;
  }
  /* Transfer codes used on the maps, to site line keys. */
  const CODE = { RL: "red", OL: "orange", BL: "blue", GL: "green", YL: "yellow", CL: "cyan", IL: "indigo", SL: "silver", CR: "rail" };

  function slug(n) { return n.toLowerCase().replace(/'/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }

  /* Distance from Boston Central in map units: the core is busiest. */
  function coreDistance(s) { return Math.hypot(s.x - 118, s.y - 100); }

  /* How many people board here on an average weekday. Deterministic per stop.
     Busy if: many lines, close to downtown, a terminal, or a named hub. */
  function ridership(s) {
    const r = rng("boardings:" + s.id);
    const transit = s.lines.filter(l => l !== "rail").length;
    const base = s.mode === "rail" && !transit ? 900 : 2600;
    const lineBoost = 1 + 0.9 * Math.max(0, transit - 1);
    const core = 1 + 3.2 * Math.exp(-coreDistance(s) / 32);
    const hubs = { "boston-central": 4.2, "south-station": 3.0, "north-station": 2.8, "park-street": 2.2, "downtown-crossing": 2.0, "harvard": 1.7, "kendall-mit": 1.6, "back-bay": 1.5, "airport": 1.5, "jfk-umass": 1.3 };
    const hub = hubs[s.id] || 1;
    const noise = 0.75 + r() * 0.6;
    return Math.round(base * lineBoost * core * hub * noise / 10) * 10;
  }

  /* Line status. Most lines run fine; one or two get a believable delay that changes every few hours. */
  const ISSUES = [
    ["warn", "Minor delays", "Delays of about 5 minutes due to a disabled train"],
    ["warn", "Minor delays", "Trains running about 8 minutes apart due to a signal problem"],
    ["warn", "Slow zone", "Speed restriction between two stops while crews finish rail work"],
    ["bad", "Shuttle pods", "Shuttle pods replace trains on a short stretch this weekend for track work"]
  ];
  function lineStatus(key) {
    const block = Math.floor(Date.now() / (3 * 3600 * 1000));
    const r = rng("status:" + key + ":" + block);
    const roll = r();
    if (roll < 0.78) return { level: "ok", label: "Normal service", detail: "Trains running on schedule." };
    const i = ISSUES[Math.floor(r() * ISSUES.length)];
    return { level: i[0], label: i[1], detail: i[2] };
  }

  /* Upcoming departures for one direction, in minutes, moving with the clock. */
  function departures(stopId, line, towards, count = 3) {
    const L = LINES[line];
    const now = Date.now() / 60000;
    const head = L.headway * (isPeak() ? 1 : 1.5);
    const offset = rng("dep:" + stopId + line + towards)() * head;
    const out = [];
    let t = Math.ceil((now - offset) / head) * head + offset;
    while (out.length < count) {
      const m = Math.round(t - now);
      if (m >= 0) out.push(m);
      t += head * (0.85 + rng("j" + Math.round(t))() * 0.3);
    }
    return out;
  }
  function isPeak(d = new Date()) {
    const h = d.getHours() + d.getMinutes() / 60, wd = d.getDay() % 6 !== 0;
    return wd && ((h >= 6.5 && h < 9.5) || (h >= 15.5 && h < 18.5));
  }

  /* ---------- trip planner: fewest minutes, with a cost for each change ---------- */
  function buildGraph(d) {
    const g = {};
    const add = (a, b, line, mins) => { (g[a] = g[a] || []).push({ to: b, line, mins }); };
    d.segments.forEach(seg => {
      const L = LINES[seg.line];
      for (let i = 0; i < seg.stops.length - 1; i++) {
        const a = d.byId[seg.stops[i]], b = d.byId[seg.stops[i + 1]];
        if (!a || !b || a.id === b.id) continue;
        const dist = Math.hypot(a.x - b.x, a.y - b.y);
        const mins = Math.max(1.5, dist / 4 * L.speed * 0.6 + 0.6);
        add(a.id, b.id, seg.line, mins); add(b.id, a.id, seg.line, mins);
      }
    });
    return g;
  }
  function planTrip(d, from, to) {
    if (from === to) return null;
    const g = d.graph || (d.graph = buildGraph(d));
    const CHANGE = 5;
    const key = (s, l) => s + "|" + l;
    const dist = {}, prev = {}, seen = new Set();
    const queue = [{ k: key(from, ""), s: from, l: "", c: 0 }];
    dist[key(from, "")] = 0;
    while (queue.length) {
      queue.sort((a, b) => a.c - b.c);
      const cur = queue.shift();
      if (seen.has(cur.k)) continue;
      seen.add(cur.k);
      if (cur.s === to) {
        const legs = [];
        let k = cur.k;
        while (prev[k]) { legs.unshift(prev[k].edge); k = prev[k].k; }
        return { minutes: Math.round(cur.c), legs: groupLegs(legs) };
      }
      (g[cur.s] || []).forEach(e => {
        const c = cur.c + e.mins + (cur.l && cur.l !== e.line ? CHANGE : 0) + (!cur.l ? LINES[e.line].headway / 2 : 0);
        const nk = key(e.to, e.line);
        if (dist[nk] === undefined || c < dist[nk]) {
          dist[nk] = c; prev[nk] = { k: cur.k, edge: { from: cur.s, to: e.to, line: e.line, mins: e.mins } };
          queue.push({ k: nk, s: e.to, l: e.line, c });
        }
      });
    }
    return null;
  }
  function groupLegs(edges) {
    const legs = [];
    edges.forEach(e => {
      const last = legs[legs.length - 1];
      if (last && last.line === e.line) { last.to = e.to; last.stops++; last.mins += e.mins; }
      else legs.push({ line: e.line, from: e.from, to: e.to, stops: 1, mins: e.mins });
    });
    return legs;
  }
  /* Which way a train is heading: the far end of the segment in that direction. */
  function headsign(d, line, from, to) {
    for (const seg of d.segments) {
      if (seg.line !== line) continue;
      const i = seg.stops.indexOf(from), j = seg.stops.indexOf(to);
      if (i > -1 && j > -1) return d.byId[j > i ? seg.stops[seg.stops.length - 1] : seg.stops[0]].name;
    }
    return d.byId[to].name;
  }

  /* ---------- small helpers ---------- */
  const fmt = n => n.toLocaleString("en-US");
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  function bullet(key, lg) {
    const L = LINES[key];
    return `<span class="bullet ${key}${lg ? " lg" : ""}" title="${esc(L.name)}">${L.short}</span>`;
  }
  function stopLink(s) { return `/stop.html?id=${encodeURIComponent(s.id)}`; }
  function qs(name) { return new URLSearchParams(location.search).get(name); }

  /* ---------- header and footer ---------- */
  const NAV = [
    ["/maps.html", "Maps"],
    ["/lines.html", "Subway"],
    ["/rail.html", "Regional Rail"],
    ["/ferry.html", "Ferry"],
    ["/stops.html", "Stations"],
    ["/alerts.html", "Alerts"],
    ["/data.html", "Data"],
    ["/fares.html", "Fares"]
  ];
  function header() {
    const norm = p => p.replace(/\.html$/, "").replace(/\/$/, "/index");
    const here = norm(location.pathname);
    const links = NAV.map(([href, t]) => `<a href="${href}"${here === norm(href) ? ' aria-current="page"' : ""}>${t}</a>`).join("");
    const el = document.createElement("div");
    el.innerHTML = `
<a class="skip" href="#main">Skip to content</a>
<div class="utility"><div class="wrap">
  <span class="clock" id="clock"></span>
  <a href="/accessibility.html" class="hide-sm">Accessibility</a>
  <a href="/alerts.html">Service Alerts</a>
  <a href="/about.html">About</a>
</div></div>
<header class="masthead"><div class="wrap">
  <a class="brand" href="/"><img src="/assets/logo/nerta.svg" alt="NERTA home" width="46" height="60"><span class="word"><b>NERTA</b><span>Rapid Transit &middot; Regional Rail &middot; Ferry</span></span></a>
  <button class="menu-btn" aria-expanded="false" aria-controls="nav">Menu</button>
  <nav class="nav" id="nav" aria-label="Main">${links}
    <div class="search" role="search">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/></svg>
      <label class="sr" for="q">Find a station</label>
      <input id="q" type="search" placeholder="Find a station" autocomplete="off">
      <div class="suggest" id="suggest"></div>
    </div>
  </nav>
</div><div class="stripe" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></header>`;
    document.body.prepend(...el.childNodes);
    const btn = document.querySelector(".menu-btn"), nav = document.getElementById("nav");
    btn.addEventListener("click", () => { const o = nav.classList.toggle("open"); btn.setAttribute("aria-expanded", o); });
    tick(); setInterval(tick, 15000);
    searchBox();
  }
  function tick() {
    const c = document.getElementById("clock");
    if (c) c.textContent = new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  }
  async function searchBox() {
    const input = document.getElementById("q"), box = document.getElementById("suggest");
    let active = -1, items = [];
    input.addEventListener("input", async () => {
      const all = await everyPlace();
      const q = input.value.trim().toLowerCase();
      if (!q) { box.classList.remove("open"); return; }
      items = all.filter(s => s.name.toLowerCase().includes(q)).sort((a, b) => a.name.toLowerCase().indexOf(q) - b.name.toLowerCase().indexOf(q)).slice(0, 9);
      active = -1;
      box.innerHTML = items.length ? items.map(s => `<a href="${s.href}">${s.badges} ${esc(s.name)}</a>`).join("") : '<div class="small muted" style="padding:8px 10px">No stations match.</div>';
      box.classList.add("open");
    });
    input.addEventListener("keydown", e => {
      const links = box.querySelectorAll("a");
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        active = (active + (e.key === "ArrowDown" ? 1 : -1) + links.length) % links.length;
        links.forEach((a, i) => a.classList.toggle("active", i === active));
      } else if (e.key === "Enter") {
        const a = links[active] || links[0];
        if (a) location.href = a.href;
      } else if (e.key === "Escape") box.classList.remove("open");
    });
    document.addEventListener("click", e => { if (!e.target.closest(".search")) box.classList.remove("open"); });
  }
  /* One searchable list: subway stations, Regional Rail stations and ferry docks, each linking to the best page. */
  let PLACES = null;
  async function everyPlace() {
    if (PLACES) return PLACES;
    const [d, r, f] = await Promise.all([network(), rail(), ferry()]);
    const seen = new Set();
    PLACES = d.stops.map(s => { seen.add(s.id); return { name: s.name, href: stopLink(s), badges: s.lines.map(l => bullet(l)).join("") }; });
    r.lines.forEach(l => l.stops.forEach(n => {
      const id = slug(n);
      if (seen.has(id)) return;
      seen.add(id);
      PLACES.push({ name: n, href: `/rail-line.html?l=${l.key}#${id}`, badges: bullet("rail") });
    }));
    f.routes.forEach(rt => rt.all.forEach(n => {
      const id = slug(n);
      if (seen.has(id)) return;
      seen.add(id);
      PLACES.push({ name: n, href: `/ferry-route.html?r=${rt.key}#${id}`, badges: `<span class="bullet ferry">F</span>` });
    }));
    PLACES.sort((a, b) => a.name.localeCompare(b.name));
    return PLACES;
  }

  function footer() {
    const f = document.createElement("footer");
    f.className = "foot";
    f.innerHTML = `<div class="wrap"><div class="cols">
  <div><span class="logo-chip"><img src="/assets/logo/nerta.svg" alt="" width="49" height="64"></span>
    <p>Serving 222 rapid transit stations across Greater Boston, every hour of every day.</p></div>
  <div><h4>Ride</h4><ul><li><a href="/maps.html">Maps</a></li><li><a href="/map.html">Interactive map</a></li><li><a href="/lines.html">Subway</a></li><li><a href="/rail.html">Regional Rail</a></li><li><a href="/ferry.html">Ferry</a></li><li><a href="/stops.html">Stations</a></li></ul></div>
  <div><h4>Plan</h4><ul><li><a href="/#planner">Trip planner</a></li><li><a href="/alerts.html">Service alerts</a></li><li><a href="/fares.html">Fares &amp; passes</a></li><li><a href="/accessibility.html">Accessibility</a></li></ul></div>
  <div><h4>Data</h4><ul><li><a href="/data.html">Ridership dashboard</a></li><li><a href="/data.html#downloads">Open data</a></li><li><a href="/data.html#performance">Performance</a></li></ul></div>
  <div><h4>About</h4><ul><li><a href="/about.html">About this site</a></li><li><a href="/about.html#credits">Credits</a></li><li><a href="/bigger-dig.html">The BIGGER Dig</a></li></ul></div>
</div>
<div class="fine"><span>&copy; NERTA. Maps: Maxwell Howe.</span><span><a href="/about.html">A fan project, not a real transit agency.</a></span></div></div>`;
    document.body.append(f);
  }

  /* ---------- lightbox for map images ---------- */
  function lightbox() {
    const lb = document.createElement("div");
    lb.className = "lightbox";
    lb.innerHTML = `<div class="bar-top"><b id="lb-title"></b><span><a class="btn small" id="lb-dl" download>Download</a> <button class="btn small" id="lb-x">Close</button></span></div><div class="stage" id="lb-stage"><img id="lb-img" alt=""></div>`;
    document.body.append(lb);
    const stage = lb.querySelector("#lb-stage"), img = lb.querySelector("#lb-img");
    const close = () => { lb.classList.remove("open"); stage.classList.remove("zoomed"); };
    lb.querySelector("#lb-x").onclick = close;
    document.addEventListener("keydown", e => { if (e.key === "Escape") close(); });
    stage.addEventListener("click", () => stage.classList.toggle("zoomed"));
    document.addEventListener("click", e => {
      const a = e.target.closest("[data-lightbox]");
      if (!a) return;
      e.preventDefault();
      img.src = a.getAttribute("href"); img.alt = a.dataset.title || "";
      lb.querySelector("#lb-title").textContent = a.dataset.title || "";
      lb.querySelector("#lb-dl").href = a.getAttribute("href");
      lb.classList.add("open");
    });
  }

  window.NERTA = { LINES, ORDER, BLURB, network, rail, ferry, everyPlace, CODE, ridership, lineStatus, departures, isPeak, planTrip, headsign, rng, hash, fmt, esc, bullet, stopLink, qs, slug, coreDistance };
  document.addEventListener("DOMContentLoaded", () => { header(); footer(); lightbox(); });
})();
