/* Shared NERTA site code: header, footer, network data, the fake-data engine and the trip planner. */
(function () {
  "use strict";

  /* Service settings. Names, colors, legs and terminals come from /data/network.json, built from the maps and posters. */
  const LINES = {
    red:    { name: "Red Line",    short: "RL", color: "#da291c", headway: 6, speed: 2.2 },
    orange: { name: "Orange Line", short: "OL", color: "#ed8b00", headway: 6, speed: 2.1 },
    blue:   { name: "Blue Line",   short: "BL", color: "#003da5", headway: 5, speed: 2.0 },
    green:  { name: "Green Line",  short: "GL", color: "#00843d", headway: 7, speed: 2.6 },
    yellow: { name: "Yellow Line", short: "YL", color: "#f5c400", headway: 5, speed: 2.0 },
    cyan:   { name: "Cyan Line",   short: "CL", color: "#00a9c9", headway: 4, speed: 1.8 },
    indigo: { name: "Indigo Line", short: "IL", color: "#3f3fb5", headway: 8, speed: 2.4 },
    silver: { name: "Silver Line", short: "SL", color: "#7c878e", headway: 4, speed: 1.6 },
    rail:   { name: "Regional Rail", short: "RR", color: "#80276c", headway: 20, mode: "generic" },
    walk:   { name: "Walk", short: "", color: "#62626d", headway: 0, mode: "walk" },
    ferry:  { name: "Ferry", short: "F", color: "#00796d", headway: 15, mode: "generic" },
    tram:   { name: "Tram", short: "T", color: "#e0457b", headway: 8, mode: "generic" }
  };
  const ORDER = ["red", "orange", "blue", "green", "yellow", "cyan", "indigo", "silver"];
  const CODE = { RL: "red", OL: "orange", BL: "blue", GL: "green", YL: "yellow", CL: "cyan", IL: "indigo", SL: "silver", CR: "rail" };
  const HOP = { rail: 4, hsr: 12, ferry: 6, tram: 2 };  // minutes between stops where the system map gives no distance

  /* ---------- seeded randomness: the made-up numbers stay the same between visits ---------- */
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
  function ferryHeadway(l) { return l.key === "ferry-express" ? 6 : l.loop ? 10 : l.style === "streak" ? 30 : l.family === "The Islands" ? 45 : 15; }
  async function network() {
    if (NET) return NET;
    const d = await (await fetch("/data/network.json")).json();
    d.byId = {};
    d.stops.forEach(s => { d.byId[s.id] = s; });
    d.nbr = {};
    Object.values(d.lines).forEach(l => {
      const base = l.mode === "subway" ? LINES[l.key] : { headway: l.mode === "hsr" ? 60 : l.mode === "rail" ? 20 : l.mode === "tram" ? 8 : ferryHeadway(l) };
      LINES[l.key] = Object.assign({}, base, l);
      const nb = d.nbr[l.key] = {};
      l.legs.forEach(leg => leg.forEach((id, i) => {
        nb[id] = nb[id] || new Set();
        if (i > 0 && leg[i - 1] !== id) nb[id].add(leg[i - 1]);
        if (i < leg.length - 1 && leg[i + 1] !== id) nb[id].add(leg[i + 1]);
      }));
    });
    d.railLines = Object.values(d.lines).filter(l => l.mode === "rail" || l.mode === "hsr");
    d.ferryLines = Object.values(d.lines).filter(l => l.mode === "ferry");
    NET = d;
    return d;
  }
  function slug(n) { return n.toLowerCase().replace(/'/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }
  /* The lines that really stop here, without the generic rail and ferry marks. */
  function servedBy(s) { return s.lines.filter(l => LINES[l] && LINES[l].mode !== "generic"); }
  function kindName(s) { return s.kind === "dock" ? "ferry dock" : "station"; }

  /* Which way a train or boat is heading, from `from` toward its neighbor `next`: every end of track it can reach that way.
     A line that runs on past the map's edge names where it goes. A closed loop has no end, so it names the next stop. */
  function headsign(d, line, from, next) {
    const L = LINES[line], nb = d.nbr[line], ends = new Set(L.terminals || []);
    const seen = new Set([from]), queue = [next], hit = [];
    while (queue.length) {
      const id = queue.shift();
      if (seen.has(id)) continue;
      seen.add(id);
      if (L.beyond && L.beyond.at === id) hit.push(L.beyond.to);
      else if (ends.has(id)) hit.push(d.byId[id].name);
      (nb[id] || []).forEach(n => { if (!seen.has(n)) queue.push(n); });
    }
    if (!hit.length) return (L.mode === "ferry" ? "Loop via " : "Ring via ") + d.byId[next].name;
    return hit.length > 3 ? hit.slice(0, 3).join(" / ") + " and more" : hit.join(" / ");
  }
  /* Every way out of a stop: one row per line and direction. */
  function directions(d, s) {
    const out = [];
    servedBy(s).forEach(line => {
      [...(d.nbr[line][s.id] || [])].forEach(next => {
        const to = headsign(d, line, s.id, next);
        if (!out.some(x => x.line === line && x.to === to)) out.push({ line, next, to });
      });
    });
    return out;
  }

  /* Distance from Boston Central, for the made-up ridership numbers: the core is busiest. */
  function coreDistance(s) {
    if (s.x !== undefined) return Math.hypot(s.x - 110, s.y - 100);
    if (s.geo) return Math.hypot((s.geo.lat - 42.3590) * 111, (s.geo.lon + 71.0525) * 82) * 4;
    return 90;
  }
  /* Made-up boardings per average weekday: random, but bigger where more lines meet and nearer downtown. */
  function ridership(s) {
    const r = rng("boardings:" + s.id);
    const n = servedBy(s).length;
    const base = s.kind === "dock" ? 300 : servedBy(s).some(l => ORDER.includes(l)) ? 2600 : 900;
    const core = 1 + 3.2 * Math.exp(-coreDistance(s) / 32);
    return Math.round(base * (1 + 0.8 * Math.max(0, n - 1)) * core * (0.6 + r() * 0.9) / 10) * 10;
  }

  /* Line status. Most lines run fine; now and then one has trouble, and it changes every few hours. It's the future:
     maglev guideways, pods instead of buses, drones overhead, pod clustering on the streets. {a} and {b} are neighboring stops. */
  const REASONS = {
    subway: [
      ["warn", "Minor delays", "Delays of about {n} minutes while crews recalibrate the guideway between {a} and {b}."],
      ["warn", "Minor delays", "Delays of about {n} minutes while a train-sync update rolls out across the line."],
      ["warn", "Minor delays", "Delays of about {n} minutes while a drone delivery swarm holds over the line near {a}."],
      ["warn", "Minor delays", "Delays of about {n} minutes while platform doors reset at {a}."],
      ["warn", "Minor delays", "Delays of about {n} minutes after a solar storm scrambled train-to-train sync."],
      ["warn", "Slow zone", "Trains slow to half speed between {a} and {b} while crews level a guideway seam."],
      ["bad", "Shuttle pods", "Shuttle pods replace trains between {a} and {b} while crews swap a levitation coil."],
      ["bad", "Shuttle pods", "Shuttle pods replace trains between {a} and {b} while a stalled car is towed clear."]
    ],
    rail: [
      ["warn", "Minor delays", "Delays of about {n} minutes after a tree came down on the guideway near {a}."],
      ["warn", "Minor delays", "Delays of about {n} minutes while a heat wave stretches the guideway near {a}."],
      ["warn", "Minor delays", "Delays of about {n} minutes while a freight convoy clears the junction at {a}."],
      ["warn", "Slow zone", "Trains slow between {a} and {b} while crews check the guideway after high winds."],
      ["bad", "Shuttle pods", "Shuttle pods replace trains between {a} and {b} while crews swap a guideway switch."]
    ],
    ferry: [
      ["warn", "Minor delays", "Boats running about {n} minutes late in fog near {a}."],
      ["warn", "Minor delays", "Boats holding for the high tide at {a}. Allow about {n} extra minutes."],
      ["warn", "Minor delays", "Boats slowing near {a} for a whale sighting. Allow about {n} extra minutes."],
      ["warn", "Minor delays", "Delays of about {n} minutes while dock sensors reset at {a}."],
      ["bad", "Shuttle pods", "Pods replace boats between {a} and {b} while rough water clears."]
    ],
    tram: [
      ["warn", "Minor delays", "Delays of about {n} minutes from pod clustering near {a}."],
      ["warn", "Minor delays", "Delays of about {n} minutes from heavy pod clustering between {a} and {b}."],
      ["warn", "Minor delays", "Trams running about {n} minutes apart because of pod clustering near {a}."],
      ["warn", "Minor delays", "Delays of about {n} minutes around a street festival near {a}."],
      ["warn", "Minor delays", "Delays of about {n} minutes while crews patch the guide strip near {a}."],
      ["bad", "Shuttle pods", "Shuttle pods replace trams between {a} and {b} while crews resurface the street."]
    ]
  };
  // Very rarely, a whole line stops.
  const SUSPENSIONS = {
    subway: ["a guideway power fault", "a line-wide sync outage", "an emergency inspection of the levitation system"],
    rail: ["a guideway power fault", "a signal outage along the corridor", "an emergency guideway inspection"],
    ferry: ["a small craft warning", "dense fog across the harbor"],
    tram: ["a citywide guide-strip fault", "a power fault along the route"]
  };
  const NOUN = { subway: "trains", rail: "trains", ferry: "boats", tram: "trams" };
  const block3h = () => Math.floor(Date.now() / (3 * 3600 * 1000));
  const modeOf = L => L.mode === "hsr" ? "rail" : REASONS[L.mode] ? L.mode : "subway";
  function lineStatus(key) {
    const L = LINES[key] || {};
    const mode = modeOf(L);
    if (rng("suspend:" + key + ":" + block3h())() < 0.0002) {
      const why = SUSPENSIONS[mode][Math.floor(rng("why:" + key + block3h())() * SUSPENSIONS[mode].length)];
      return { level: "bad", label: "Suspended", suspended: true,
               detail: `No ${NOUN[mode]} on the whole line because of ${why}. ${mode === "ferry" ? "Pods are running between the docks by road." : "Shuttle pods are running between every stop."}` };
    }
    const r = rng("status:" + key + ":" + block3h());
    if (r() < 0.86) return { level: "ok", label: "Normal service", detail: "Running on schedule." };
    const pick = REASONS[mode][Math.floor(r() * REASONS[mode].length)];
    let a = "one stop", b = "the next";
    if (NET && NET.lines[key]) {
      const legs = NET.lines[key].legs.filter(l => l.length > 1);
      const leg = legs[Math.floor(r() * legs.length)];
      const i = Math.floor(r() * (leg.length - 1));
      a = NET.byId[leg[i]].name; b = NET.byId[leg[i + 1]].name;
    }
    const n = 4 + Math.floor(r() * 9);
    return { level: pick[0], label: pick[1], detail: pick[2].replace("{a}", a).replace("{b}", b).replace("{n}", n) };
  }
  // Very, very rarely, a whole station closes. Trains run through without stopping.
  const CLOSURES = ["a platform door fault", "a fire system test", "flooding from a king tide", "an elevator swap on every level",
                    "a suspicious package check", "a power fault in the station"];
  function stationStatus(stopId) {
    const r = rng("closed:" + stopId + ":" + block3h());
    if (r() >= 0.00005) return { closed: false };
    const s = NET && NET.byId[stopId];
    const why = CLOSURES[Math.floor(r() * CLOSURES.length)];
    const what = s && s.kind === "dock" ? "Boats pass by without stopping" : s && s.kind === "tram" ? "Trams pass without stopping" : "Trains pass through without stopping";
    return { closed: true, detail: `${s ? s.name : "This station"} is closed because of ${why}. ${what}; pods run to the next stop.` };
  }
  /* Special events. Now and then (about one 3-hour window in four) something is on: extra service, crowds nearby. */
  const EVENTS = [
    { at: "stadium", text: "New England Revolution match at Stadium. Extra Cyan and Yellow Line trains, and extra boats to the Stadium dock, before and after the game. Expect crowds at Stadium and Assembly." },
    { at: "stadium", text: "Concert at Stadium tonight. Extra trains after the show; expect crowds at Stadium, Assembly and Encore." },
    { at: "stadium", text: "New England Revolution match at Stadium. Platforms will be busy for an hour after the final whistle; extra trains are standing by." },
    { at: "fenway", text: "Baseball at Fenway. Extra Green Line trains; expect crowds at Kenmore and Fenway after the last out." },
    { at: "dock-hatch-shell", text: "Free concert at the Hatch Shell. Extra Charles River boats; expect crowds at Charles/MGH and the Esplanade docks." },
    { at: "dock-pavilion", text: "Concert at the Seaport Pavilion. Extra Seaport boats and Cyan Line trains; expect crowds at Seaport." },
    { at: "dock-agganis", text: "Game at Agganis Arena. Extra boats to the Agganis dock and Green Line trains at BU Central." },
    { at: "north-station", text: "Game at the arena over North Station. Expect crowds on every platform after the final buzzer." },
    { at: "encore", text: "Show at Encore tonight. Extra Cyan Line trains and boats to the Encore dock after the show." },
    { at: "boston-central", text: "Night market at Boston Central. The main hall is busy; allow extra time to reach the platforms." }
  ];
  function eventNow() {
    const r = rng("event:" + block3h());
    if (r() > 0.25) return null;
    const e = EVENTS[Math.floor(r() * EVENTS.length)];
    return NET && !NET.byId[e.at] ? null : e;
  }

  /* The strip at the top of every page. Changes every 45 minutes; dismissable. A suspended line or closed station always
     shows; otherwise, sometimes one delay, and now and then two or three at once. */
  function currentIssues(d) {
    const lines = Object.keys(d.lines).map(k => ({ key: k, st: lineStatus(k) })).filter(x => x.st.level !== "ok");
    const closed = d.stops.filter(s => s.kind === "station").map(s => ({ stop: s, st: stationStatus(s.id) })).filter(x => x.st.closed);
    return { lines, closed };
  }
  async function alertBar() {
    const d = await network();
    const block = Math.floor(Date.now() / (45 * 60 * 1000));
    const r = rng("alertbar:" + block);
    const { lines, closed } = currentIssues(d);
    const major = lines.filter(x => x.st.suspended);
    const minor = lines.filter(x => !x.st.suspended);
    const show = [...major.map(x => ({ line: x })), ...closed.map(x => ({ stop: x }))];
    if (r() < 0.6 && minor.length) {
      const subway = minor.filter(x => ORDER.includes(x.key));
      const many = r() < 0.3 ? 2 + Math.floor(r() * 2) : 1;
      const pool = (subway.length && r() < 0.6 ? subway : minor).slice();
      for (let i = 0; i < many && pool.length; i++) show.push({ line: pool.splice(Math.floor(r() * pool.length), 1)[0] });
    }
    const ev = eventNow();
    if (ev) show.push({ event: ev });
    const crowd = crowdAlerts(d)[0];
    if (crowd) show.push({ crowd });
    if (!show.length) return;
    const id = show.map(x => x.line ? x.line.key : x.stop ? x.stop.stop.id : x.crowd ? "crowd" : "event").join(",") + block;
    try { if (sessionStorage.getItem("nerta-alert") === id) return; } catch (e) { /* storage blocked */ }
    const bad = major.length || closed.length || show.some(x => x.line && x.line.st.level === "bad");
    const onlyEvent = show.every(x => x.event || x.crowd);
    const rows = show.map(x => {
      if (x.event) return `<li><span class="tag event">EVENT</span> <span><b><a href="${stopLink(d.byId[x.event.at])}">${esc(d.byId[x.event.at].name)}</a>:</b> ${esc(x.event.text)}</span></li>`;
      if (x.crowd) {
        const c = x.crowd, where = c.stop ? `<a href="${stopLink(c.stop)}">${esc(c.stop.name)}</a>` : `<a href="/line.html?l=${c.line}">${esc(LINES[c.line].name)}</a>`;
        return `<li><span class="tag event">CROWDING</span>${c.line ? bullet(c.line) : ""}<span><b>${where}:</b> ${esc(c.text)}</span></li>`;
      }
      if (x.stop) return `<li><span class="tag">STATION CLOSED</span> <span><b><a href="${stopLink(x.stop.stop)}">${esc(x.stop.stop.name)}</a>:</b> ${esc(x.stop.st.detail)}</span></li>`;
      const L = LINES[x.line.key], st = x.line.st;
      const tag = st.suspended ? "LINE SUSPENDED" : st.level === "bad" ? "SERVICE CHANGE" : "DELAY";
      return `<li><span class="tag">${tag}</span>${bullet(x.line.key)}<span><b>${esc(L.name)}:</b> ${esc(st.detail)}</span></li>`;
    }).join("");
    const bar = document.createElement("div");
    bar.className = "alertbar " + (bad ? "bad" : onlyEvent ? "info" : "warn");
    bar.setAttribute("role", "status");
    bar.innerHTML = `<div class="wrap"><ul>${rows}</ul><a class="all" href="/alerts.html">All alerts</a><button type="button" aria-label="Dismiss alerts">&times;</button></div>`;
    bar.querySelector("button").onclick = () => { bar.remove(); try { sessionStorage.setItem("nerta-alert", id); } catch (e) { /* ignore */ } };
    const head = document.querySelector(".masthead");
    if (head) head.after(bar);
  }

  /* Upcoming departures for one direction, in minutes, moving with the clock. */
  function departures(stopId, line, towards, count = 3) {
    if ((LINES[line] && LINES[line].mode !== "generic" && lineStatus(line).suspended) || stationStatus(stopId).closed) return [];
    const L = LINES[line] || LINES.rail;
    const now = Date.now() / 60000;
    const head = L.headway * (isPeak() || L.mode === "hsr" || L.mode === "tram" ? 1 : 1.5);
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
  function isPeak(dt = new Date()) {
    const h = dt.getHours() + dt.getMinutes() / 60, wd = dt.getDay() % 6 !== 0;
    return wd && ((h >= 6.5 && h < 9.5) || (h >= 15.5 && h < 18.5));
  }

  /* ---------- crowding: how full each train is, made up but plausible ----------
     Busiest in the weekday rushes (7:30 to 9 and 4:30 to 6:30), near downtown, at big stations and around special events.
     Trams and subway fill up most; boats least. Each train gets its own seeded wobble and a least crowded car (or deck). */
  const CROWD = ["Not crowded", "Some crowding", "Crowded", "Very crowded"];
  const CROWD_MODE = { subway: 1, tram: 1.12, rail: 0.72, hsr: 0.62, ferry: 0.6 };
  const DECKS = ["Upper deck has room", "Lower deck has room", "Open deck has room", "Upper deck has room"];
  /* 0 to 1: how busy this time of day is. */
  function crowdHour(dt) {
    const h = dt.getHours() + dt.getMinutes() / 60, wd = dt.getDay() % 6 !== 0;
    if (!wd) return h >= 11 && h < 19 ? 0.5 : h >= 8 && h < 23 ? 0.32 : 0.1;
    if ((h >= 7.5 && h < 9) || (h >= 16.5 && h < 18.5)) return 1;
    const gap = Math.min(...[7.5, 9, 16.5, 18.5].map(e => Math.abs(h - e)));
    const base = h >= 6 && h < 22 ? (h >= 11.5 && h < 13.5 ? 0.42 : 0.34) : 0.1;
    return Math.max(base, Math.exp(-(gap * gap) / 0.5));
  }
  function crowdPeak(dt = new Date(Date.now())) {
    const h = dt.getHours() + dt.getMinutes() / 60;
    return dt.getDay() % 6 !== 0 && ((h >= 7.5 && h < 9) || (h >= 16.5 && h < 18.5));
  }
  /* Extra riders from a special event: most at its stop, some one stop away or anywhere on a line that serves it. */
  function eventBoost(stopId, line) {
    const ev = eventNow();
    if (!ev || !NET) return 0;
    if (ev.at === stopId) return 0.5;
    const at = NET.byId[ev.at];
    if (!at) return 0;
    const near = Object.keys(NET.nbr).some(k => NET.nbr[k][ev.at] && NET.nbr[k][ev.at].has(stopId));
    if (near) return 0.3;
    return at.lines.includes(line) ? 0.12 : 0;
  }
  function crowdBase(s, line, dt) {
    const L = LINES[line] || {};
    const riders = ridership(s);
    const rf = Math.min(1, Math.max(0, (Math.log10(Math.max(riders, 1)) - (L.mode === "ferry" ? 2.2 : 2.7)) / 1.8));
    return (CROWD_MODE[L.mode] || 1) * (0.1 + 0.9 * crowdHour(dt)) * (0.2 + 0.85 * rf);
  }
  const crowdLevel = score => score < 0.38 ? 0 : score < 0.6 ? 1 : score < 0.85 ? 2 : 3;
  /* One train (or boat or tram) leaving stopId on line in minutesAway minutes.
     Returns { level: 0-3, label: "Not crowded" ... "Very crowded", room: "Car 4 least crowded" or "Upper deck has room" }. */
  function crowding(stopId, line, minutesAway = 0, towards = "") {
    const s = NET && NET.byId[stopId];
    const L = LINES[line] || {};
    const when = Date.now() + minutesAway * 60000;
    const train = Math.round(when / 180000);  // the same train keeps its numbers as it counts down
    const r = rng("crowd:" + stopId + ":" + line + ":" + towards + ":" + train);
    const score = s ? crowdBase(s, line, new Date(when)) + eventBoost(stopId, line) + (r() - 0.5) * 0.3 : 0.3;
    const level = crowdLevel(score);
    const cars = L.mode === "tram" ? 3 : L.mode === "rail" || L.mode === "hsr" ? 8 : 6;
    const room = L.mode === "ferry" ? DECKS[Math.floor(r() * DECKS.length)] : `Car ${1 + Math.floor(r() * cars)} least crowded`;
    return { level, label: CROWD[level], room };
  }
  /* How busy a whole station is right now, compared with a usual day at this hour. */
  function stationCrowding(stopId) {
    const s = NET && NET.byId[stopId];
    if (!s) return null;
    const now = new Date(Date.now());
    const lines = servedBy(s);
    const usual = lines.length ? Math.max(...lines.map(l => crowdBase(s, l, now))) : 0.2;
    const wobble = (rng("busy:" + stopId + ":" + Math.floor(Date.now() / 900000))() - 0.5) * 0.24;
    const extra = Math.max(0, ...lines.map(l => eventBoost(stopId, l)));
    const score = usual + wobble + extra;
    const diff = score - usual;
    const level = crowdLevel(score);
    return { level, label: CROWD[level], compare: diff > 0.06 ? "Busier than usual for this hour" : diff < -0.06 ? "Quieter than usual for this hour" : "About as busy as usual for this hour" };
  }
  /* A typical weekday on one line: how full trains get in the morning, midday, evening and night, from its busier stations. */
  function lineCrowding(key) {
    const ids = [...new Set((LINES[key].legs || []).flat())].filter(id => NET.byId[id]);
    const day = new Date(); day.setDate(day.getDate() + ((3 - day.getDay() + 7) % 7));  // the next Wednesday
    return [["Morning", 8.25], ["Midday", 12.5], ["Evening", 17.5], ["Night", 22.5]].map(([label, h]) => {
      const dt = new Date(day); dt.setHours(Math.floor(h), Math.round((h % 1) * 60), 0, 0);
      const scores = ids.map(id => crowdBase(NET.byId[id], key, dt)).sort((x, y) => y - x);
      const top = scores.slice(0, Math.max(1, Math.ceil(scores.length / 3)));
      const score = top.reduce((x, y) => x + y, 0) / top.length;
      const level = crowdLevel(score);
      return { label, level, text: CROWD[level], score };
    });
  }
  /* A tiny icon: 1 to 3 filled people. Very crowded fills all three in red. */
  function crowdIcon(c) {
    const on = Math.max(1, Math.min(3, c.level || 1));
    const ppl = [3, 9, 15].map((x, i) => `<g class="${i < on ? "on" : ""}"><circle cx="${x}" cy="2.2" r="1.9"/><rect x="${x - 2.3}" y="4.8" width="4.6" height="5.2" rx="2"/></g>`).join("");
    return `<svg class="crowd c${c.level}" viewBox="0 0 18 10" width="18" height="10" role="img" aria-label="${c.label}"><title>${c.label}</title>${ppl}</svg>`;
  }
  /* Board HTML for one departure: the minutes with a crowding icon under them. */
  function crowdTime(stopId, line, v, towards) {
    const c = crowding(stopId, line, v, towards);
    return `<span title="${c.label}"><b>${v === 0 ? "Now" : v + "<em>min</em>"}</b>${crowdIcon(c)}</span>`;
  }
  /* A short line for the first departure: which car, or which deck, has room. Empty when nothing is coming. */
  function crowdNote(stopId, line, mins, towards) {
    return mins.length ? `<small class="crowd-note">${crowding(stopId, line, mins[0], towards).room}</small>` : "";
  }

  /* Crowding alerts. Mostly in the rush and around events; now and then otherwise. They change every 45 minutes. */
  const EVENT_CROWD = { stadium: "after the game", fenway: "after the game", "north-station": "after the game", encore: "after the show",
                        "boston-central": "around the night market", "dock-hatch-shell": "after the concert", "dock-pavilion": "after the concert", "dock-agganis": "after the game" };
  function crowdAlerts(d) {
    const out = [];
    const block = Math.floor(Date.now() / (45 * 60 * 1000));
    const r = rng("crowdalert:" + block);
    const now = new Date(Date.now());
    const ev = eventNow();
    if (ev && d.byId[ev.at] && r() < 0.85) {
      const s = d.byId[ev.at];
      const why = /Revolution match/.test(ev.text) ? "after the New England Revolution match" : /Concert/.test(ev.text) ? "after the concert" : EVENT_CROWD[ev.at] || "after the event";
      const what = s.kind === "dock" ? "docks" : "platforms";
      const extra = s.kind === "dock" ? "Extra boats are running; wait for the next one, it's right behind." : "Extra trains are running; wait for the next one, it's right behind.";
      out.push({ stop: s, level: 2, text: `Crowded ${what} at ${s.name} ${why}. ${extra}` });
    }
    const peak = crowdPeak(now);
    const chance = peak ? 0.8 : isPeak(now) ? 0.35 : 0.07;
    if (r() < chance) {
      const many = peak && r() < 0.35 ? 2 : 1;
      const pool = ORDER.filter(k => d.lines[k] && !lineStatus(k).suspended);
      for (let i = 0; i < many && pool.length; i++) {
        const key = pool.splice(Math.floor(r() * pool.length), 1)[0];
        const legs = d.lines[key].legs.filter(l => l.length > 4);
        if (!legs.length) continue;
        const leg = legs[Math.floor(r() * legs.length)];
        // The busy end is the leg's biggest station; the other end is a few stops out.
        let hub = 0;
        leg.forEach((id, j) => { if (ridership(d.byId[id]) > ridership(d.byId[leg[hub]])) hub = j; });
        const span = 3 + Math.floor(r() * 4);
        const far = hub + span < leg.length ? hub + span : Math.max(0, hub - span);
        const morning = now.getHours() < 12;
        const [a, b] = morning ? [leg[far], leg[hub]] : [leg[hub], leg[far]];
        const level = peak && r() < 0.55 ? "Very crowded" : "Crowded";
        const car = 1 + Math.floor(r() * 6);
        const when = peak || isPeak(now) ? (morning ? "during the morning rush" : "during the evening rush") : now.getHours() >= 21 || now.getHours() < 5 ? "tonight" : "right now";
        out.push({ line: key, level: level === "Very crowded" ? 3 : 2,
                   text: `${level} trains between ${d.byId[a].name} and ${d.byId[b].name} ${when}. Car ${car} usually has room.` });
      }
    }
    return out;
  }

  /* ---------- trip planner: fewest minutes, with a cost for each change ---------- */
  function buildGraph(d) {
    const g = {};
    Object.values(d.lines).filter(l => !lineStatus(l.key).suspended).forEach(l => {
      const L = LINES[l.key];
      Object.entries(d.nbr[l.key]).forEach(([a, set]) => set.forEach(b => {
        const A = d.byId[a], B = d.byId[b];
        const mins = l.mode === "subway" && A.x !== undefined && B.x !== undefined
          ? Math.max(1.5, Math.hypot(A.x - B.x, A.y - B.y) / 4 * L.speed * 0.6 + 0.6) : HOP[l.mode] || 3;
        (g[a] = g[a] || []).push({ to: b, line: l.key, mins });
      }));
    });
    // Short walks between a station and its ferry dock, as the posters mark them ("F via Lovejoy Wharf").
    const walk = (a, b) => { (g[a] = g[a] || []).push({ to: b, line: "walk", mins: 4 }); (g[b] = g[b] || []).push({ to: a, line: "walk", mins: 4 }); };
    d.stops.forEach(s => {
      if (s.kind === "station" && s.dock && d.byId[s.dock]) walk(s.id, s.dock);
      if (s.kind === "dock" && s.transfers && d.byId[s.id.slice(5)] && d.byId[s.id.slice(5)].dock !== s.id) walk(s.id, s.id.slice(5));
    });
    return g;
  }
  function planTrip(d, from, to) {
    if (from === to) return null;
    for (const id of [from, to]) {
      const st = stationStatus(id);
      if (st.closed) return { closed: id, detail: st.detail };
    }
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
        const steps = [];
        let k = cur.k;
        while (prev[k]) { steps.unshift(prev[k].edge); k = prev[k].k; }
        return { minutes: Math.round(cur.c), legs: groupLegs(steps) };
      }
      (g[cur.s] || []).forEach(e => {
        const boarding = e.line !== "walk" && cur.l !== e.line;
        if (boarding && cur.l && stationStatus(cur.s).closed) return;  // no changing trains at a closed station
        const c = cur.c + e.mins + (boarding && cur.l && cur.l !== "walk" ? CHANGE : 0) + (boarding ? LINES[e.line].headway / 2 : 0);
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
      else legs.push({ line: e.line, from: e.from, next: e.to, to: e.to, stops: 1, mins: e.mins });
    });
    return legs;
  }

  /* ---------- small helpers ---------- */
  const fmt = n => n.toLocaleString("en-US");
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  function bullet(key, lg) {
    const L = LINES[key] || LINES.rail;
    const cls = `bullet${lg ? " lg" : ""}`;
    if (L.mode === "rail") return `<span class="${cls}" title="${esc(L.name)}" style="background:#80276c;box-shadow:inset 0 0 0 3px ${L.hue}">RR</span>`;
    if (L.mode === "hsr") return `<span class="${cls}" title="${esc(L.name)}" style="background:#ffd23f;color:#16161a;box-shadow:inset 0 0 0 3px #80276c">HSR</span>`;
    if (L.mode === "ferry") return `<span class="${cls}" title="${esc(L.name)}" style="background:${L.color}">F</span>`;
    if (L.mode === "tram") return `<span class="${cls}" title="${esc(L.name)}" style="background:#fff;color:${L.color};box-shadow:inset 0 0 0 2.5px ${L.color}">${esc(L.short)}</span>`;
    return `<span class="${cls} ${key}" title="${esc(L.name)}">${L.short}</span>`;
  }
  /* The white FREE tag, for free rides (Max, November 8). */
  function freeTag(key) { return LINES[key] && LINES[key].free ? ` <span class="free-tag">FREE</span>` : ""; }
  const coin = (h = 16) => `<img src="/assets/logo/cp.svg" alt="" width="${h}" height="${h}" style="vertical-align:-3px">`;
  /* What a trip costs in Charlie Points: rapid transit (subway and tram) once, with free transfers; each ferry, Regional
     Rail or High-Speed Rail ride on its own; free rides cost nothing; never more than a day pass. */
  const FARE = { subway: 25, tram: 25, rail: 50, hsr: 150, ferry: 25, fast: 75, dayPass: 75 };
  function tripFare(legs) {
    let rapid = false, total = 0;
    legs.forEach(leg => {
      const L = LINES[leg.line];
      if (!L || L.mode === "walk" || L.free) return;
      if (L.mode === "subway" || L.mode === "tram") { if (!rapid) { total += FARE.subway; rapid = true; } return; }
      total += L.mode === "hsr" ? FARE.hsr : L.mode === "rail" ? FARE.rail : L.style === "streak" ? FARE.fast : FARE.ferry;
    });
    return Math.min(total, FARE.dayPass);
  }
  /* Compact marks for a stop: each subway line, then one RR and one F if any rail or ferry stops here. */
  function badges(s) {
    return servedBy(s).filter(l => ORDER.includes(l)).map(l => bullet(l)).join("") +
      (s.lines.includes("rail") ? bullet("rail") : "") + (s.lines.includes("ferry") ? bullet("ferry") : "") + (s.lines.includes("tram") ? bullet("tram") : "");
  }
  function stopLink(s) { return `/stop.html?id=${encodeURIComponent(s.id)}`; }
  function qs(name) { return new URLSearchParams(location.search).get(name); }

  /* ---------- header and footer ---------- */
  const NAV = [
    ["/maps.html", "Maps"],
    ["/lines.html", "Subway"],
    ["/rail.html", "Regional Rail"],
    ["/ferry.html", "Ferry"],
    ["/trams.html", "Trams"],
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
  <a href="/charlie.html" class="cp-link"><img class="cp-i" src="/assets/logo/cp.svg" alt="" aria-hidden="true"><b>My Charlie Points</b></a>
  <a href="/accessibility.html" class="hide-sm">Accessibility</a>
  <a href="/alerts.html">Service Alerts</a>
  <a href="/about.html">About</a>
</div></div>
<header class="masthead"><div class="wrap">
  <a class="brand" href="/"><img src="/assets/logo/${Math.random() < 0.15 ? "nerta_37" : "nerta"}.svg" alt="NERTA home" width="46" height="60"><span class="word"><b>NERTA</b><span>Rapid Transit &middot; Regional Rail &middot; Ferry</span></span></a>
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
  /* One searchable list: every station and ferry dock. */
  async function everyPlace() {
    const d = await network();
    return d.stops.map(s => ({ name: s.name + (s.kind === "dock" && d.byId[slug(s.name)] ? " (ferry dock)" : ""), href: stopLink(s), badges: badges(s) }));
  }

  function footer() {
    const f = document.createElement("footer");
    f.className = "foot";
    f.innerHTML = `<div class="wrap"><div class="cols">
  <div><span class="logo-chip"><img src="/assets/logo/nerta.svg" alt="" width="49" height="64"></span>
    <p>Rapid transit, Regional Rail and ferries across Greater Boston, every hour of every day.</p></div>
  <div><h4>Ride</h4><ul><li><a href="/maps.html">Maps</a></li><li><a href="/map.html">Interactive map</a></li><li><a href="/explore.html">Street map</a></li><li><a href="/lines.html">Subway</a></li><li><a href="/rail.html">Regional Rail</a></li><li><a href="/ferry.html">Ferry</a></li><li><a href="/trams.html">Trams</a></li><li><a href="/stops.html">Stations</a></li></ul></div>
  <div><h4>Plan</h4><ul><li><a href="/#planner">Trip planner</a></li><li><a href="/alerts.html">Service alerts</a></li><li><a href="/fares.html">Fares &amp; passes</a></li><li><a href="/accessibility.html">Accessibility</a></li></ul></div>
  <div><h4>Data</h4><ul><li><a href="/data.html">Ridership dashboard</a></li><li><a href="/data.html#downloads">Open data</a></li><li><a href="/data.html#performance">Performance</a></li></ul></div>
  <div><h4>About</h4><ul><li><a href="/about.html">About this site</a></li><li><a href="/about.html#credits">Credits</a></li></ul></div>
</div>
<div class="fine"><span>&copy; NERTA. Maps: Maxwell Howe.</span><span><a href="/about.html">A fan project, not a real transit agency.</a></span></div></div>`;
    document.body.append(f);
  }

  /* ---------- lightbox for map images ---------- */
  function lightbox() {
    const lb = document.createElement("div");
    lb.className = "lightbox";
    lb.innerHTML = `<div class="bar-top"><b id="lb-title"></b><span><button class="btn small" id="lb-x">Close</button></span></div><div class="stage" id="lb-stage"><img id="lb-img" alt=""></div>`;
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
      lb.classList.add("open");
    });
  }

  window.NERTA = { LINES, ORDER, CODE, network, everyPlace, servedBy, kindName, directions, headsign, ridership, lineStatus, stationStatus, currentIssues, eventNow, departures, isPeak, crowding, stationCrowding, crowdTime, crowdNote, crowdIcon, crowdAlerts, crowdPeak, lineCrowding, planTrip, rng, hash, fmt, esc, bullet, badges, freeTag, coin, tripFare, stopLink, qs, slug, coreDistance };
  /* Map images Max hasn't released yet stay off the page (network.json "released"; set in site/tools/build_assets.py). */
  function unreleased() {
    network().then(d => document.querySelectorAll("[data-release]").forEach(el => {
      if (!(d.released || {})[el.dataset.release]) el.remove();
      else el.querySelectorAll("img[data-src]").forEach(img => { img.src = img.dataset.src; });
    }));
  }
  document.addEventListener("DOMContentLoaded", () => { header(); footer(); lightbox(); unreleased(); alertBar(); });
})();
