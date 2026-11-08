/* Ferry: the overview grouped by family as on the ferry map, and one page per route with every dock, transfers and next boats.
   Routes, docks and their order come from the ferry network map's own route list. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA, d = await N.network();
  const name = id => d.byId[id].label || d.byId[id].name;

  /* ---------- overview ---------- */
  const fam = document.getElementById("families");
  if (fam) {
    fam.innerHTML = `<h2>Routes</h2>` + d.families.map(g => `<p class="eyebrow" style="margin-top:14px">${N.esc(g.name)}</p><ul class="status-list">` +
      g.routes.map(k => d.lines[k]).map(rt => {
        const s = N.lineStatus(rt.key);
        return `<li>${N.bullet(rt.key)}<a class="name" href="/ferry-route.html?r=${rt.key}">${N.esc(rt.name)}</a><span class="small muted">${new Set(rt.legs.flat()).size} docks</span><span class="state"><i class="dot ${s.level}"></i>${s.level === "ok" ? "On schedule" : s.label}</span></li>`;
      }).join("") + `</ul>`).join("");
    return;
  }

  /* ---------- one route ---------- */
  const rt = d.lines[N.qs("r")] && d.lines[N.qs("r")].mode === "ferry" ? d.lines[N.qs("r")] : d.ferryLines[0];
  const L = N.LINES[rt.key];
  const docks = [...new Set(rt.legs.flat())];
  document.title = `${rt.name}${/ferry$/i.test(rt.name) ? "" : " Ferry"} | NERTA`;
  if (rt.poster) {
    const card = document.getElementById("poster");
    card.style.display = ""; card.href = `/assets/maps/${rt.poster}.webp`; card.dataset.title = `${rt.name} ferry`;
    document.getElementById("poster-img").src = `/assets/maps/${rt.poster}_thumb.webp`;
    document.getElementById("poster-img").alt = `${rt.name} ferry route map`;
  }
  document.getElementById("title").textContent = rt.name;
  document.getElementById("title").insertAdjacentHTML("beforeend", N.freeTag(rt.key));
  document.getElementById("crumb").textContent = rt.name;
  document.getElementById("head").style.background = rt.color;
  document.getElementById("blurb").textContent = `${rt.family}. ${docks.length} docks, boats every ${L.headway} minutes${rt.style === "streak" ? ". Express trips stop only at major ports" : ""}.`;

  const s = N.lineStatus(rt.key);
  const note = s.level === "ok" ? "Boats are running on schedule" : s.detail;
  document.getElementById("status").innerHTML = `<span class="tag ${s.level}">${s.level === "ok" ? "On schedule" : s.label}</span><h3>${note}</h3><p>Updated ${new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}.</p>`;

  // Every dock, leg by leg, with the transfers the ferry map shows.
  const ends = new Set(rt.terminals);
  const pills = x => (x.transfers || []).map(c => N.CODE[c] ? N.bullet(N.CODE[c]) : "").join("");
  document.getElementById("docks").innerHTML = rt.legs.map((leg, i) =>
    `${rt.legs.length > 1 ? `<p class="eyebrow" style="margin-top:${i ? 14 : 0}px">${i ? "Branch from " + N.esc(name(leg[0])) : "Main route"}</p>` : rt.loop ? `<p class="eyebrow">Loop: up one bank, round the end, back down the other</p>` : ""}
    <ul class="strip-map" style="--c:${rt.color}">` + leg.map((id, j) => {
      const x = d.byId[id];
      const last = rt.loop && j === leg.length - 1;
      return `<li id="${id}" class="${ends.has(id) ? "end" : ""}"><a class="stop" href="${N.stopLink(x)}" style="font-weight:${x.major ? 700 : 400}">${N.esc(name(id))}${last ? " (loop complete)" : ""}</a>${pills(x)}${x.major && !last ? ' <span class="tag">Major port</span>' : ""}</li>`;
    }).join("") + `</ul>`).join("");
  if (location.hash) { const el = document.getElementById(location.hash.slice(1)); if (el) { el.scrollIntoView({ block: "center" }); el.style.background = "#fff4d6"; } }

  // Next boats from the first dock.
  const first = rt.legs[0][0];
  const dirs = rt.loop ? (rt.services.length ? rt.services : ["clockwise loop", "counterclockwise loop"]).map(t => t[0].toUpperCase() + t.slice(1))
    : N.directions(d, d.byId[first]).filter(x => x.line === rt.key).map(x => "To " + x.to);
  const board = () => {
    document.getElementById("board").innerHTML = `<div class="head"><span>Next boats from ${N.esc(name(first))}</span><span>${new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}</span></div>` +
      dirs.map(t => { const m = N.departures(first, rt.key, t, 3); return `<div class="dir">${N.bullet(rt.key)}<div class="to">${N.esc(t)}${/zigzag/i.test(t) ? ` <span class="free-tag">FREE</span>` : ""}${N.crowdNote(first, rt.key, m, t)}</div><div class="mins">${m.map(v => N.crowdTime(first, rt.key, v, t)).join("")}</div></div>`; }).join("");
  };
  board(); setInterval(board, 20000);

  const r = N.rng("ferryfacts:" + rt.key);
  const majors = docks.filter(id => d.byId[id].major).map(name);
  document.getElementById("facts").innerHTML = [
    ["Boats", `Every ${L.headway} min, 24 hours`],
    ["Weekday riders", N.fmt(Math.round((docks.length * 260 + 800) * (0.7 + r() * 0.6) / 10) * 10)],
    ["On-time", (92 + r() * 7).toFixed(1) + "%"],
    ["Major ports", majors.length ? majors.map(N.esc).join(", ") : "None"]
  ].map(([a, b]) => `<dt>${a}</dt><dd>${b}</dd>`).join("");
  document.getElementById("services").innerHTML = rt.note && /[.!]$/.test(rt.note.trim()) ? `<li>${N.esc(rt.note)}</li>` : "";
});
