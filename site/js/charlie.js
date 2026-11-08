/* My Charlie Points: balance, trips, top-ups, passes and settings. Kept in this browser only. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA;
  const KEY = "nerta-charlie";
  const DAY = 86400000;
  const FARE = { subway: 25, tram: 25, rail: 50, hsr: 150, ferry: 25, fast: 75 };
  const PACKS = [
    { pts: 100, bonus: 0, credits: 100 },
    { pts: 250, bonus: 0, credits: 250 },
    { pts: 500, bonus: 25, credits: 500 },
    { pts: 1000, bonus: 75, credits: 1000 },
    { pts: 2500, bonus: 250, credits: 2500 }
  ];
  const PASSES = {
    day: { name: "Day pass", cost: 75, days: 1, covers: "Subway, tram and ferry" },
    week: { name: "7-day pass", cost: 250, days: 7, covers: "Subway, tram and ferry" },
    month: { name: "Monthly pass", cost: 900, days: 30, covers: "Subway, tram and ferry" }
  };
  const AUTO_AT = 50, AUTO_ADD = 250;

  /* ---------- storage: everything under one key, memory if storage is blocked ---------- */
  function load() {
    try { const raw = window.localStorage.getItem(KEY); return raw ? JSON.parse(raw) : null; } catch (e) { return null; }
  }
  function save() {
    try { window.localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* storage blocked: keep it in memory */ }
  }
  function wipe() {
    try { window.localStorage.removeItem(KEY); } catch (e) { /* nothing stored */ }
  }

  const d = await N.network();
  let S = load();
  if (!S || S.v !== 1 || typeof S.balance !== "number" || !Array.isArray(S.log)) { S = fresh(d); save(); }

  /* ---------- a first-visit history: real stops, the fare taken for each ---------- */
  function fareFor(line) {
    if (line.free) return 0;
    if (line.mode === "hsr") return FARE.hsr;
    if (line.mode === "rail") return FARE.rail;
    if (line.mode === "tram") return FARE.tram;
    if (line.mode === "ferry") return /fast ferry/i.test(line.name) ? FARE.fast : FARE.ferry;
    return FARE.subway;
  }
  function fresh(d) {
    const seed = (Math.random() * 4294967296) >>> 0;
    const r = N.rng(seed);
    const pick = a => a[Math.floor(r() * a.length)];
    const lines = Object.values(d.lines);
    const byMode = m => lines.filter(l => l.mode === m);
    const plan = ["subway", "subway", "subway", "subway", "tram", "tram", "rail", "ferry", "subway", "tram", "ferry", "subway"];
    if (r() < 0.35) plan[6] = "hsr";
    const count = 8 + Math.floor(r() * 5);
    const now = Date.now();
    const log = [];
    let spent = 0;
    for (let i = 0; i < count; i++) {
      const pool = byMode(plan[i]).filter(l => l.legs.some(g => g.length > 2));
      if (!pool.length) continue;
      const line = pick(pool);
      const leg = pick(line.legs.filter(g => g.length > 2));
      let a = Math.floor(r() * leg.length), b = Math.floor(r() * leg.length);
      if (a === b) b = (a + 1 + Math.floor(r() * (leg.length - 1))) % leg.length;
      const from = d.byId[leg[a]], to = d.byId[leg[b]];
      if (!from || !to || from.name === to.name) continue;
      const cp = fareFor(line);
      spent += cp;
      // spread trips over the last week, newest first, at plausible hours
      const ago = Math.floor(i * 0.75) * DAY;
      const hour = [7, 8, 8, 9, 12, 17, 17, 18, 19, 21][Math.floor(r() * 10)];
      const t = new Date(now - ago); t.setHours(hour, Math.floor(r() * 60), 0, 0);
      log.push({ kind: "trip", ts: Math.min(t.getTime(), now - (i + 1) * 600000), line: line.key, from: from.id, to: to.id, cp: -cp });
    }
    log.sort((x, y) => y.ts - x.ts);
    const pack = [500, 1000, 2500].find(p => p >= spent + 150) || 2500;
    const oldest = log.length ? log[log.length - 1].ts : now;
    log.push({ kind: "add", ts: oldest - (2 * DAY + 3 * 3600000), cp: pack, note: "Pod wallet" });
    const card = String(1000 + Math.floor(r() * 9000));
    return { v: 1, seed, card, balance: pack - spent, log, auto: false, podShow: true, pass: null };
  }

  /* ---------- formatting, with no calendar dates ---------- */
  const cp = n => N.fmt(n);
  function when(ts) {
    const t = new Date(ts), today = new Date(); today.setHours(0, 0, 0, 0);
    const days = Math.round((today - new Date(t).setHours(0, 0, 0, 0)) / DAY);
    const clock = t.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    if (days <= 0) return "Today, " + clock;
    if (days === 1) return "Yesterday, " + clock;
    return days + " days ago, " + clock;
  }
  function passLeft() {
    if (!S.pass || !PASSES[S.pass.kind]) { S.pass = null; return 0; }
    const left = S.pass.expires - Date.now();
    if (left <= 0) { S.pass = null; save(); return 0; }
    return Math.ceil(left / DAY);
  }
  const daysText = n => `Valid for ${n} more ${n === 1 ? "day" : "days"}`;

  /* ---------- drawing ---------- */
  function drawCard() {
    document.getElementById("cp-balance").textContent = cp(S.balance);
    document.getElementById("cp-number").textContent = "•••• " + S.card;
    const n = passLeft();
    document.getElementById("cp-pass-chip").innerHTML = n ? `<span class="cp-pass-tag">${N.esc(PASSES[S.pass.kind].name)}</span>` : "";
  }
  function row(e) {
    if (e.kind === "trip") {
      const L = N.LINES[e.line] || {}, a = d.byId[e.from], b = d.byId[e.to];
      const where = a && b ? `${N.esc(a.name)} to ${N.esc(b.name)}` : "Trip";
      const fare = e.cp === 0 ? `<span class="cp-amt">Pass</span>` : `<span class="cp-amt neg">&minus;${cp(-e.cp)}</span>`;
      return `<li>${N.bullet(e.line)}<div class="cp-what"><b>${where}</b><span class="small muted">${N.esc(L.name || "")} &middot; ${when(e.ts)}</span></div>${fare}</li>`;
    }
    if (e.kind === "add") {
      return `<li><span class="cp-ico plus" aria-hidden="true">+</span><div class="cp-what"><b>${e.auto ? "Points added, auto-reload" : "Points added"}</b><span class="small muted">${N.esc(e.note || "Pod wallet")} &middot; ${when(e.ts)}</span></div><span class="cp-amt pos">+${cp(e.cp)}</span></li>`;
    }
    if (e.kind === "pass") {
      return `<li><span class="cp-ico" aria-hidden="true">P</span><div class="cp-what"><b>${N.esc(e.name)} bought</b><span class="small muted">Paid with Charlie Points &middot; ${when(e.ts)}</span></div><span class="cp-amt neg">&minus;${cp(-e.cp)}</span></li>`;
    }
    return "";
  }
  function drawActivity() {
    const shown = S.log.slice(0, 30);
    document.getElementById("cp-activity").innerHTML = shown.map(row).join("");
    const trips = S.log.filter(e => e.kind === "trip").length;
    document.getElementById("cp-count").textContent = `${trips} recent ${trips === 1 ? "trip" : "trips"}`;
  }
  function drawPacks() {
    document.getElementById("cp-packs").innerHTML = PACKS.map((p, i) => `
      <button type="button" class="cp-pack" data-pack="${i}">
        <span class="cp-pts">${cp(p.pts)}<small>points</small></span>
        <span class="cp-price">${cp(p.credits)} wallet credits</span>
        ${p.bonus ? `<span class="tag ok">+${cp(p.bonus)} bonus</span>` : `<span class="small muted">${Math.floor(p.pts / FARE.subway)} subway rides</span>`}
      </button>`).join("");
  }
  function drawPass() {
    const n = passLeft();
    document.getElementById("cp-pass-now").innerHTML = n
      ? `<div class="cp-active"><span class="tag ok">Active</span> <b>${N.esc(PASSES[S.pass.kind].name)}</b><span class="small muted">${daysText(n)}. ${N.esc(PASSES[S.pass.kind].covers)}: no points taken at the gate.</span></div>`
      : `<p class="small muted" style="margin-top:-4px">No pass right now. Fares come out of your points, capped at a day pass a day.</p>`;
    document.getElementById("cp-pass-list").innerHTML = Object.entries(PASSES).map(([k, p]) => `
      <div class="cp-pass-row"><div><b>${p.name}</b><span class="small muted">${p.covers}, ${p.days === 1 ? "1 day" : p.days + " days"}</span></div>
      <button type="button" class="btn small" data-pass="${k}"><img class="cp-i" src="/assets/logo/cp.svg" alt=""> ${cp(p.cost)} CP</button></div>`).join("");
  }
  function drawSettings() {
    document.getElementById("cp-auto").setAttribute("aria-checked", String(!!S.auto));
    document.getElementById("cp-podshow").setAttribute("aria-checked", String(!!S.podShow));
  }
  function draw() { drawCard(); drawActivity(); drawPass(); drawSettings(); }

  /* ---------- actions ---------- */
  function autoReload() {
    if (!S.auto || S.balance >= AUTO_AT) return false;
    S.balance += AUTO_ADD;
    S.log.unshift({ kind: "add", ts: Date.now(), cp: AUTO_ADD, auto: true, note: "Pod wallet" });
    return true;
  }
  const confirmBox = document.getElementById("cp-confirm");
  const packsBox = document.getElementById("cp-packs");
  function showConfirm(i) {
    const p = PACKS[i];
    packsBox.hidden = true;
    confirmBox.hidden = false;
    confirmBox.innerHTML = `
      <p class="eyebrow">Confirm</p>
      <p class="cp-big">${cp(p.pts + p.bonus)} Charlie Points</p>
      <dl class="kv" style="margin:8px 0 16px"><dt>Pack</dt><dd>${cp(p.pts)} points${p.bonus ? ` + ${cp(p.bonus)} bonus` : ""}</dd><dt>Price</dt><dd>${cp(p.credits)} wallet credits</dd><dt>Card</dt><dd>•••• ${N.esc(S.card)}</dd><dt>New balance</dt><dd>${cp(S.balance + p.pts + p.bonus)}</dd></dl>
      <div class="row" style="flex-wrap:wrap"><button type="button" class="btn" id="cp-pay">Pay with pod wallet</button><button type="button" class="btn ghost" id="cp-cancel">Cancel</button></div>`;
    document.getElementById("cp-pay").onclick = () => {
      const added = p.pts + p.bonus;
      S.balance += added;
      S.log.unshift({ kind: "add", ts: Date.now(), cp: added, note: "Pod wallet" });
      save(); draw();
      confirmBox.innerHTML = `<div class="cp-done" role="status"><span class="cp-ico plus" aria-hidden="true">&#10003;</span><div><b>${cp(added)} points added</b><span class="small muted">New balance: ${cp(S.balance)} Charlie Points</span></div></div>
        <button type="button" class="btn ghost small" id="cp-again" style="margin-top:14px">Done</button>`;
      document.getElementById("cp-again").onclick = hideConfirm;
    };
    document.getElementById("cp-cancel").onclick = hideConfirm;
    document.getElementById("cp-pay").focus();
  }
  function hideConfirm() { confirmBox.hidden = true; confirmBox.innerHTML = ""; packsBox.hidden = false; }
  packsBox.addEventListener("click", e => { const b = e.target.closest("[data-pack]"); if (b) showConfirm(+b.dataset.pack); });

  document.getElementById("cp-pass-list").addEventListener("click", e => {
    const b = e.target.closest("[data-pass]");
    if (!b) return;
    const k = b.dataset.pass, p = PASSES[k], msg = document.getElementById("cp-pass-msg");
    if (S.balance < p.cost) { msg.innerHTML = `You need ${cp(p.cost - S.balance)} more points for a ${p.name.toLowerCase()}. <a href="#add">Add Charlie Points</a>`; return; }
    S.balance -= p.cost;
    const start = S.pass && S.pass.expires > Date.now() ? S.pass.expires : Date.now();
    const expires = start + p.days * DAY;
    const keep = S.pass && passLeft() > p.days ? S.pass.kind : k;
    S.pass = { kind: keep, expires };
    S.log.unshift({ kind: "pass", ts: Date.now(), cp: -p.cost, name: p.name });
    const topped = autoReload();
    save(); draw();
    msg.textContent = `${p.name} bought. Your pass is ${daysText(passLeft()).toLowerCase()}.` + (topped ? ` Auto-reload added ${AUTO_ADD} points.` : "");
  });

  function toggle(id, field) {
    document.getElementById(id).addEventListener("click", () => {
      S[field] = !S[field];
      const topped = field === "auto" && autoReload();
      save(); topped ? draw() : drawSettings();
    });
  }
  toggle("cp-auto", "auto");
  toggle("cp-podshow", "podShow");

  document.getElementById("cp-reset").addEventListener("click", e => {
    e.preventDefault();
    wipe();
    S = fresh(d); save(); hideConfirm(); draw();
    document.getElementById("cp-pass-msg").textContent = "";
    window.scrollTo(0, 0);
  });

  drawPacks();
  draw();
  if (location.hash) { const t = document.querySelector(location.hash); if (t) t.scrollIntoView(); }
});
