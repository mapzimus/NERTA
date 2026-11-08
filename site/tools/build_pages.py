"""Write the plain content pages (alerts, fares, accessibility, about, BIGGER Dig, 404) from one template.

    python site/tools/build_pages.py
"""
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | NERTA</title>
<meta name="description" content="{desc}">
<link rel="icon" href="/assets/logo/t.svg" type="image/svg+xml">
<link rel="stylesheet" href="/css/site.css">
<script src="/js/common.js" defer></script>{script}
</head>
<body>
<header class="page-head"><div class="wrap">
  <div class="crumbs"><a href="/">Home</a> / {title}</div>
  <h1>{h1}</h1>
  <p class="lede">{lede}</p>
</div></header>
<main id="main">
{body}
</main>
</body>
</html>
"""

ALERTS_JS = """
<script defer>
document.addEventListener("DOMContentLoaded", () => {
  const N = window.NERTA;
  const live = N.ORDER.map(k => [k, N.lineStatus(k)]).filter(([, s]) => s.level !== "ok");
  document.getElementById("now").innerHTML = live.length ? live.map(([k, s]) =>
    `<div class="alert-item ${k}">${N.bullet(k)} <span class="tag ${s.level}">${s.label}</span><h3>${N.LINES[k].name}: ${s.detail}</h3><p>Updated ${new Date().toLocaleTimeString("en-US", {hour: "numeric", minute: "2-digit"})}. Allow a few extra minutes.</p></div>`).join("")
    : `<div class="alert-item"><span class="tag ok">All clear</span><h3>All lines are running normally</h3><p>No delays reported on any line.</p></div>`;
  document.getElementById("ok").innerHTML = N.ORDER.filter(k => N.lineStatus(k).level === "ok").map(k => `<li>${N.bullet(k)}<a class="name" href="/line.html?l=${k}">${N.LINES[k].name}</a><span class="state"><i class="dot ok"></i>Normal service</span></li>`).join("");
});
</script>"""

PAGES = {
    "alerts": dict(
        title="Service Alerts", h1="Service Alerts", script=ALERTS_JS,
        desc="Current delays and planned work on NERTA lines.",
        lede="Delays, detours and planned work. This page updates on its own.",
        body="""<section class="section"><div class="wrap grid two" style="align-items:start">
  <div><h2>Right now</h2><div id="now"></div>
    <h2 style="margin-top:30px">Planned work</h2>
    <div class="alert-item cyan"><span class="bullet cyan">CL</span> <span class="tag">Weekend</span><h3>Cyan Line: platform tile work at Fort Point</h3><p>Trains run normally. One entrance on Congress St is closed. Use the Summer St entrance.</p></div>
    <div class="alert-item green"><span class="bullet green">GL</span> <span class="tag">Overnight</span><h3>Green Line: rail grinding on the Riverside branch</h3><p>Midnight to 4 AM, trains every 20 minutes between Reservoir and Riverside.</p></div>
    <div class="alert-item rail"><span class="bullet rail">RR</span> <span class="tag">Notice</span><h3>Regional Rail: new High-Speed Rail platforms at Boston Central</h3><p>Montreal, Albany and Bangor trains now board on Level 4.</p></div>
  </div>
  <div class="card"><h2>Running normally</h2><ul class="status-list" id="ok"></ul></div>
</div></section>"""),

    "fares": dict(
        title="Fares", h1="Fares &amp; Passes", script="",
        desc="NERTA fares, passes and reduced fares.",
        lede="One fare goes anywhere on rapid transit, with free transfers for two hours.",
        body="""<section class="section"><div class="wrap">
  <div class="grid three">
    <div class="stat"><div class="k">Rapid transit, any line</div><div class="v">$1.00</div><div class="d muted">Free transfers for 2 hours</div></div>
    <div class="stat"><div class="k">Regional Rail</div><div class="v">$2.00</div><div class="d muted">Any zone, includes transit</div></div>
    <div class="stat"><div class="k">Ferry</div><div class="v">$1.00</div><div class="d muted">Express boats $3.00</div></div>
  </div>
  <div class="grid two" style="margin-top:20px;align-items:start">
    <div class="card"><h2>Passes</h2>
      <table class="data"><thead><tr><th>Pass</th><th class="num">Price</th><th>Covers</th></tr></thead><tbody>
        <tr><td>Day pass</td><td class="num">$3</td><td>Transit and ferry</td></tr>
        <tr><td>7-day pass</td><td class="num">$10</td><td>Transit and ferry</td></tr>
        <tr><td>Monthly pass</td><td class="num">$30</td><td>Transit and ferry</td></tr>
        <tr><td>Monthly Regional pass</td><td class="num">$55</td><td>Everything, including High-Speed Rail to the region's edge</td></tr>
      </tbody></table>
    </div>
    <div class="card"><h2>Ride free</h2>
      <ul><li>Children 12 and under</li><li>Students, with a school ID</li><li>Riders 65 and older</li><li>Riders with disabilities</li><li>Everyone, on New Year's Eve and the day of the Marathon</li></ul>
      <h2 style="margin-top:20px">How to pay</h2>
      <p class="muted" style="margin:0">Tap any contactless card or phone at the gate. Fares cap at the price of a day pass, so you never pay more than $3 in a day.</p>
    </div>
  </div>
</div></section>"""),

    "accessibility": dict(
        title="Accessibility", h1="Accessibility", script="",
        desc="Every NERTA station is step-free.",
        lede="Every station is step-free, from the street to the train.",
        body="""<section class="section"><div class="wrap grid three">
  <div class="card"><h2>Step-free everywhere</h2><p class="muted">All 222 stations have at least two elevators, and platforms are level with the train floor. No ramps, no gaps.</p></div>
  <div class="card"><h2>Elevator status</h2><p class="muted">Every station page lists its elevators. If one is out, a pod takes you to the nearest station with working elevators, free.</p></div>
  <div class="card"><h2>Pods on demand</h2><p class="muted">Pods meet every train at every station, 24 hours a day. Request one at the platform kiosk or on the app.</p></div>
</div></section>"""),

    "about": dict(
        title="About", h1="About this site", script="",
        desc="This is a fan project about an imagined transit system. It is not a real agency.",
        lede="This is a fan project. NERTA is not a real transit agency, and nothing here is real service information.",
        body="""<section class="section"><div class="wrap grid two" style="align-items:start">
  <div class="prose">
    <h2>Just for fun</h2>
    <p>This site imagines what Boston's transit could be: extended lines, four new ones, a rail tunnel joining North Station and South Station, regional rail, high-speed rail and five ferry routes. It is drawn to look and feel like the real thing, because that's the fun of it.</p>
    <p><b>None of it is real.</b> The departures, delays, ridership numbers, fares and news are made up, generated by the site itself. Don't use this site to plan a real trip.</p>
    <p>This site is not affiliated with, endorsed by or connected to any real transit agency or government body.</p>
    <p>Where a line or stop follows a real proposal or plan, the research notes say so. Others are invented.</p>
    <h2 id="credits">Credits</h2>
    <p>Concept, network and map design: <b>Maxwell Howe</b>. Map-drawing and website scripts: Claude Code.</p>
    <p>The project began as Day 8, Utopia, of the 2026 #30DayMapChallenge.</p>
    <p>Coastline: US Census. Today's station order: public transit data.</p>
  </div>
  <div class="card" style="text-align:center"><img src="/assets/logo/nerta.svg" alt="NERTA logo" style="width:180px;margin:10px auto 18px"><p class="muted small" style="margin:0">Map: Maxwell Howe</p></div>
</div></section>"""),

    "bigger-dig": dict(
        title="The BIGGER Dig", h1="The BIGGER Dig", script="",
        desc="A four-track tunnel joining North Station and South Station, with Boston Central at its heart.",
        lede="Four tracks under downtown join North Station and South Station, with a new hub station, Boston Central, halfway between.",
        body="""<section class="section"><div class="wrap grid two" style="align-items:start">
  <div class="prose">
    <h2>One city, one network</h2>
    <p>For a century, trains from the north stopped at North Station and trains from the south stopped at South Station, a mile apart. Riders crossed downtown on the subway to change trains.</p>
    <p>The BIGGER Dig ends that. A four-track tunnel runs under downtown and joins the two stations. Regional Rail trains now run straight through, from the North Shore to the South Shore, from Lowell to Providence.</p>
    <h2>Boston Central</h2>
    <p>Halfway through the tunnel is Boston Central, the new hub. The Orange, Blue and Cyan lines meet here, along with Regional Rail and High-Speed Rail to Montreal, Albany, Concord and Bangor.</p>
    <p><a class="btn" href="/stop.html?id=boston-central">Visit Boston Central</a> <a class="btn ghost" href="/map.html?stop=boston-central">See it on the map</a></p>
  </div>
  <a class="map-card" href="/assets/maps/system_map.webp" data-lightbox data-title="NERTA system map"><div class="thumb" style="aspect-ratio:auto"><img src="/assets/maps/system_map_thumb.webp" alt="System map showing the BIGGER Dig"></div><div class="body"><b>The tunnel on the system map</b><span>The black four-track line through downtown.</span></div></a>
</div></section>"""),

    "404": dict(
        title="Page not found", h1="This stop isn't on the map", script="",
        desc="Page not found.",
        lede="The page you're looking for doesn't exist or has moved.",
        body="""<section class="section"><div class="wrap"><p><a class="btn" href="/">Go home</a> <a class="btn ghost" href="/stops.html">Find a station</a></p></div></section>"""),
}

for slug, p in PAGES.items():
    (SITE / f"{slug}.html").write_text(HEAD.format(**p), encoding="utf-8")
print("wrote", len(PAGES), "pages")
