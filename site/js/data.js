/* Ridership dashboard. Every number comes from NERTA.ridership() and seeded randomness, so it is stable between visits. */
document.addEventListener("DOMContentLoaded", async () => {
  const N = window.NERTA, d = await N.network();
  const last = new Date(); last.setDate(1); last.setMonth(last.getMonth() - 1);
  const monthName = last.toLocaleString("en-US", { month: "long", year: "numeric" });
  document.getElementById("period").textContent = "Data for " + monthName;

  const stops = d.stops.filter(s => s.lines.some(l => l !== "rail"));
  const byLine = N.ORDER.map(k => {
    // A transfer station's riders are shared among its lines.
    const n = stops.filter(s => s.lines.includes(k)).reduce((a, s) => a + N.ridership(s) / s.lines.filter(l => l !== "rail").length, 0);
    return [k, Math.round(n / 100) * 100];
  }).sort((a, b) => b[1] - a[1]);
  const total = byLine.reduce((a, b) => a + b[1], 0);
  const r = N.rng("system:" + monthName);

  document.getElementById("tiles").innerHTML = [
    ["Weekday riders", N.fmt(total), `+${(2 + r() * 3).toFixed(1)}% from last year`, "up"],
    ["Saturday riders", N.fmt(Math.round(total * 0.61 / 100) * 100), `+${(1 + r() * 3).toFixed(1)}% from last year`, "up"],
    ["On-time, all lines", (92 + r() * 4).toFixed(1) + "%", "Goal: 90%", "up"],
    ["Trips run as scheduled", (98.6 + r() * 1.2).toFixed(1) + "%", "Of 41,200 weekly trips", ""]
  ].map(([k, v, dd, c]) => `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div><div class="d ${c}">${dd}</div></div>`).join("");

  const max = byLine[0][1];
  document.getElementById("by-line").innerHTML = byLine.map(([k, n]) =>
    `<div class="bar ${k}"><a href="/line.html?l=${k}">${N.LINES[k].name}</a><div class="track"><div class="fill" style="width:${n / max * 100}%"></div></div><span class="n">${N.fmt(n)}</span></div>`).join("");

  // Trend: 24 months, seasonal, rising.
  const season = [0.86, 0.9, 0.97, 1.0, 1.02, 0.95, 0.88, 0.9, 1.04, 1.06, 1.02, 0.93];
  const months = [...Array(24)].map((_, i) => { const m = new Date(last); m.setMonth(m.getMonth() - 23 + i); return m; });
  const vals = months.map((m, i) => Math.round(total * season[m.getMonth()] * (0.93 + i * 0.0035) * (0.985 + N.rng("t" + i)() * 0.03)));
  const lo = Math.min(...vals) * 0.95, hi = Math.max(...vals) * 1.03;
  const X = i => 60 + i * 24, Y = v => 170 - (v - lo) / (hi - lo) * 150;
  const area = `M${X(0)},170 ` + vals.map((v, i) => `L${X(i)},${Y(v)}`).join(" ") + ` L${X(23)},170 Z`;
  document.getElementById("trend").innerHTML = `<svg class="chart" viewBox="0 0 640 200" role="img" aria-label="Weekday riders per month">
    ${[0, 0.5, 1].map(f => { const v = lo + (hi - lo) * f; return `<line x1="60" x2="620" y1="${Y(v)}" y2="${Y(v)}" stroke="#e2e2dd"/><text x="54" y="${Y(v) + 4}" text-anchor="end">${(v / 1e6).toFixed(2)}M</text>`; }).join("")}
    <path d="${area}" fill="#bfe3e2" opacity=".7"/>
    <polyline fill="none" stroke="#16161a" stroke-width="2.5" points="${vals.map((v, i) => X(i) + "," + Y(v)).join(" ")}"/>
    ${vals.map((v, i) => `<circle cx="${X(i)}" cy="${Y(v)}" r="9" fill="transparent"><title>${months[i].toLocaleString("en-US", { month: "short", year: "numeric" })}: ${N.fmt(v)}</title></circle>`).join("")}
    ${months.map((m, i) => m.getMonth() === 0 ? `<text x="${X(i)}" y="194" text-anchor="middle">Jan ${m.getFullYear()}</text>` : "").join("")}
  </svg>`;

  document.getElementById("otp").innerHTML = N.ORDER.map(k => {
    const q = N.rng("otp:" + k + monthName);
    const a = 88 + q() * 9, b = 88 + q() * 9, c = 89 + q() * 7;
    const tag = a >= 90 ? ["ok", "Meets goal"] : ["warn", "Below goal"];
    return `<tr><td>${N.bullet(k)} <a href="/line.html?l=${k}">${N.LINES[k].name}</a></td><td class="num"><b>${a.toFixed(1)}%</b></td><td class="num">${b.toFixed(1)}%</td><td class="num">${c.toFixed(1)}%</td><td class="num">${N.fmt(Math.round(60 / N.LINES[k].headway * 20 * 2 * 30 * (0.98 + q() * 0.02)))}</td><td><span class="tag ${tag[0]}">${tag[1]}</span></td></tr>`;
  }).join("");

  const top = stops.map(s => [s, N.ridership(s)]).sort((a, b) => b[1] - a[1]).slice(0, 20);
  document.getElementById("top").innerHTML = top.map(([s, n], i) => {
    const ch = (N.rng("yoy:" + s.id)() * 12 - 3);
    return `<tr><td>${i + 1}</td><td><a href="${N.stopLink(s)}"><b>${N.esc(s.name)}</b></a></td><td>${s.lines.map(l => N.bullet(l)).join(" ")}</td><td class="num">${N.fmt(n)}</td><td class="num ${ch >= 0 ? "up" : "down"}">${ch >= 0 ? "+" : ""}${ch.toFixed(1)}%</td></tr>`;
  }).join("");

  document.getElementById("csv").addEventListener("click", () => {
    const rows = [["station_id", "station_name", "lines", "weekday_boardings", "month"]];
    d.stops.forEach(s => rows.push([s.id, `"${s.name.replace(/"/g, '""')}"`, s.lines.join(";"), N.ridership(s), last.toISOString().slice(0, 7)]));
    const blob = new Blob([rows.map(r => r.join(",")).join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = `nerta_station_ridership_${last.toISOString().slice(0, 7)}.csv`; a.click();
  });
});
