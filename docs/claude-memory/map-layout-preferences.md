---
name: map-layout-preferences
description: "Max's layout and style preferences for the 30 Day Map Challenge pages, learned while finishing Day 2 (2026-10-31)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 5d3634ef-d77e-46e4-b6e1-5e9d12579346
  modified: 2026-11-01T22:11:10.140Z
---

How Max wants a challenge page laid out (settled on Day 2, confirmed step by step):
- Work around the shape of the subject. New England runs SW–NE, so the empty corners carry the furniture: title block top-left (Québec), chart bottom-right in the ocean ("the ocean isn't the focus so who cares"), scale bar centred under Martha's Vineyard, north arrow beside it.
- Crop tight. Trim empty ocean and neighbouring land; he would rather have slack on the ocean side than a blank strip of New York on the left. Zoom in so the subject fills the page.
- Text over the basemap needs a translucent paper card or pill behind it (title card, state-name pills, chart panel), not glyph halos. Day 1 look: serif title, Source Sans labels, tracked small-caps place names, italic water names.
- Keep the river colours and line widths from the first RustGIS pass; he liked those. Small "other" streams tinted pale slate blue (#a0b5c5) rather than grey so nothing looks unfinished.
- Show where water goes beyond the region as faded continuations (Natural Earth centerlines) with a short italic "to the …" label, not arrows.
- No tan land: off-white land, very light hillshade and grain, flat grey neighbours.
- He flags overlapping labels quickly; do a collision pass on every preview before saving. He sometimes nudges text in Illustrator himself mid-session; read current bounds before adding pills or moving things.

- Each day should look like its own map, not a re-skin of the last one (said after Day 3 came out too close to Day 2). Vary the basemap and the type pair per day: Day 2 = terrain hillshade + sea depth tint, Source Serif + Source Sans; Day 3 = flat water #c3d4df, flat neighbours #dbd4c8, no bathymetry, Rockwell / Rockwell-Bold title with Franklin Gothic Book/Demi labels (Book Italic for water names). Keep the shared grammar (corners for furniture, paper cards, tight crop) but change the skin. Day 4 = NOAA chart depth tints + chart-buff land, Bodoni MT title/italic water names, Gill Sans MT labels. Day 5 = Sentinel-2 imagery, flat slate water #23394a, neighbors muted to paper, Garamond title/italic names, Century Gothic labels.
- Max likes "how it was made" stats on the map itself (Day 5: scene/pass/chunk counts + a pass-date inset in the ocean panel).
- Scale bar + north arrow go bottom-centre under Martha's Vineyard on EVERY day, never inside the legend (re-flagged on Day 4, 2026-11-01).
- Title and subtitle text must be plain and literal, e.g. "Shipwrecks off the MA Coast" — not clever ("Where the Wrecks Gather") or AI-sounding. Subtitle = the numbers in short sentences. Counts must match what is inside the frame, not the whole dataset.

**Why:** these took a dozen rounds to converge on; later days should start from them.
**How to apply:** for the next day's page, start from this layout logic and the Day 2 scripts (`days/02-lines/src/export_svg.py`, `terrain.py`), then preview and fix collisions before showing him.
