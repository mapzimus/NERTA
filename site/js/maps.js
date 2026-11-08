document.addEventListener("DOMContentLoaded", () => {
  const N = window.NERTA;
  document.getElementById("line-grid").innerHTML = N.ORDER.map(k => `
    <div class="map-card">
      <a class="thumb" href="/assets/maps/line_${k}.webp" data-lightbox data-title="${N.LINES[k].name}"><img src="/assets/maps/line_${k}_thumb.webp" alt="${N.LINES[k].name} map" loading="lazy"></a>
      <div class="body"><b>${N.bullet(k)} ${N.LINES[k].name}</b><span><a href="/line.html?l=${k}">Line page</a></span></div>
    </div>`).join("");
});
