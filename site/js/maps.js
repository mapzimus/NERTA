document.addEventListener("DOMContentLoaded", () => {
  const N = window.NERTA;
  document.getElementById("line-grid").innerHTML = N.ORDER.map(k => `
    <div class="map-card">
      <a class="thumb" href="/assets/maps/line_${k}.webp" data-lightbox data-title="${N.LINES[k].name}"><img src="/assets/maps/line_${k}_thumb.webp" alt="${N.LINES[k].name} map" loading="lazy"></a>
      <div class="body"><b>${N.bullet(k)} ${N.LINES[k].name}</b><span><a href="/downloads/line_${k}.pdf">PDF</a> &middot; <a href="/line.html?l=${k}">Line page</a></span></div>
    </div>`).join("");
  const ferries = [["inner-harbor", "Inner Harbor"], ["charles", "Charles River"], ["north-shore", "North Shore"], ["south-shore", "South Shore"], ["harbor-islands", "Harbor Islands"]];
  document.getElementById("ferry-grid").innerHTML = ferries.map(([k, t]) => `
    <a class="map-card" href="/assets/maps/ferry5_${k}.webp" data-lightbox data-title="${t} ferry">
      <div class="thumb"><img src="/assets/maps/ferry5_${k}_thumb.webp" alt="${t} ferry route map" loading="lazy"></div>
      <div class="body"><b><span class="bullet ferry">F</span> ${t}</b><span>Ferry route</span></div>
    </a>`).join("");
});
