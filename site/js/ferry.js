/* Ferry: the overview grouped by family, and one page per route with docks, transfers and next boats. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA;
  const [f, d] = await Promise.all([N.ferry(), N.network()]);
  const swatch = rt => `<span class="bullet" style="background:${rt.color};min-width:26px">F</span>`;
  const pills = (rt, n) => (rt.pills[n] || []).map(c => N.CODE[c] ? N.bullet(N.CODE[c]) : "").join("");
  const label = (rt, n) => rt.labels[n] || n;
  const every = rt => rt.key === "express" ? 6 : rt.loop ? 10 : rt.style === "streak" ? 30 : rt.family === "The Islands" ? 45 : 15;

  /* ---------- overview ---------- */
  const fam = document.getElementById("families");
  if (fam) {
    fam.innerHTML = `<h2>Routes</h2>` + f.families.map(g => `<p class="eyebrow" style="margin-top:14px">${N.esc(g.name)}</p><ul class="status-list">` +
      g.routes.map(k => f.byKey[k]).map(rt => {
        const s = N.lineStatus("ferry-" + rt.key);
        return `<li>${swatch(rt)}<a class="name" href="/ferry-route.html?r=${rt.key}">${N.esc(rt.name)}</a><span class="small muted">${rt.all.length} docks</span><span class="state"><i class="dot ${s.level}"></i>${s.level === "ok" ? "On schedule" : s.label}</span></li>`;
      }).join("") + `</ul>`).join("");
    return;
  }

  /* ---------- one route ---------- */
  const rt = f.byKey[N.qs("r")] || f.byKey["hw"];
  document.title = `${rt.name} Ferry | NERTA`;
  document.getElementById("title").textContent = rt.name;
  document.getElementById("crumb").textContent = rt.name;
  document.getElementById("head").style.background = rt.color;
  document.getElementById("blurb").textContent = `${rt.family}. ${rt.all.length} docks, boats every ${every(rt)} minutes${rt.style === "streak" ? ", express trips stop only at major ports" : ""}.`;

  const s = N.lineStatus("ferry-" + rt.key);
  const ferryNote = s.level === "ok" ? "Boats are running on schedule" : s.label === "Shuttle pods" ? "Pods replace boats at one dock this weekend" : "Boats running a few minutes late due to harbor traffic";
  document.getElementById("status").innerHTML = `<span class="tag ${s.level}">${s.level === "ok" ? "On schedule" : s.label}</span><h3>${ferryNote}</h3><p>Updated ${new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}.</p>`;

  const sections = rt.stops ? { "": rt.stops } : {};
  Object.assign(sections, rt.banks || {}, rt.branches || {});
  document.getElementById("docks").innerHTML = Object.entries(sections).map(([title, docks]) =>
    `${title ? `<p class="eyebrow" style="margin-top:12px">${N.esc(title)}</p>` : ""}<ul class="strip-map" style="--c:${rt.color}">` +
    docks.map((n, i) => {
      const sub = d.byId[N.slug(n)];
      const major = rt.major_ports.includes(n);
      const name = sub ? `<a class="stop" href="${N.stopLink(sub)}">${N.esc(label(rt, n))}</a>` : `<span class="stop" style="font-weight:${major ? 700 : 400}">${N.esc(label(rt, n))}</span>`;
      return `<li id="${N.slug(n)}" class="${i === 0 || i === docks.length - 1 ? "end" : ""}">${name}${pills(rt, n)}${major ? ' <span class="tag">Major port</span>' : ""}</li>`;
    }).join("") + `</ul>`).join("");
  if (location.hash) { const el = document.getElementById(location.hash.slice(1)); if (el) { el.scrollIntoView({ block: "center" }); el.style.background = "#fff4d6"; } }

  const first = rt.all[0], last = rt.all[rt.all.length - 1];
  const dirs = rt.loop ? [["Clockwise", "clockwise"], ["Counterclockwise", "counter"], ["Zigzag, bank to bank", "zigzag"]] : [[`To ${label(rt, last)}`, "out"], [`To ${label(rt, first)}`, "in"]];
  const board = () => {
    document.getElementById("board").innerHTML = `<div class="head"><span>Next boats from ${N.esc(label(rt, first))}</span><span>${new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}</span></div>` +
      dirs.map(([t, k]) => {
        const now = Date.now() / 60000, h = every(rt), off = N.rng("boat:" + rt.key + k)() * h;
        const m = [0, 1, 2].map(i => Math.round(Math.ceil((now - off) / h) * h + off + i * h - now));
        return `<div class="dir">${swatch(rt)}<div class="to">${N.esc(t)}</div><div class="mins">${m.map(v => `<span>${v === 0 ? "Now" : v + "<em>min</em>"}</span>`).join("")}</div></div>`;
      }).join("");
  };
  board(); setInterval(board, 20000);

  const r = N.rng("ferryfacts:" + rt.key);
  document.getElementById("facts").innerHTML = [
    ["Boats", `Every ${every(rt)} min, 24 hours`],
    ["Weekday riders", N.fmt(Math.round((rt.all.length * 260 + 800) * (0.8 + r() * 0.5) / 10) * 10)],
    ["On-time", (93 + r() * 6).toFixed(1) + "%"],
    ["Fare", rt.style === "streak" || rt.family === "The Islands" ? "$3.00 express" : "$1.00"],
    ["Major ports", rt.major_ports.length ? rt.major_ports.map(N.esc).join(", ") : "None"]
  ].map(([a, b]) => `<dt>${a}</dt><dd>${b}</dd>`).join("");
  document.getElementById("services").innerHTML = (rt.services || []).map(x => `<li>${N.esc(x[0].toUpperCase() + x.slice(1))}</li>`).join("") + (rt.note ? `<li>${N.esc(rt.note)}</li>` : "");
});
