---
name: rustgis-mcp-quirks
description: "What the RustGIS MCP server can and can't do for map-making (learned building Day 2, 2026-10-31)"
metadata:
  node_type: memory
  type: project
  originSessionId: 5d3634ef-d77e-46e4-b6e1-5e9d12579346
  modified: 2026-10-31T17:17:28.422Z
---

RustGIS MCP (used for Day 2 rivers map, 2026-10-31):
- `run_command` needs the key `command` (not `id`). Layers are addressed by name or id.
- No DuckDB on BRONTOSAURUS, so `layer.addSql` fails. Do derived layers in Python (system Python has shapely + sqlite3; no geopandas, Miniforge path is broken) and load GeoJSON with `layer.addData`.
- No width-by-field: split lines into separate layers per width band and set `layer.outline` width on each.
- Unique Values assigns a qualitative ramp's stops to the layer's *present* classes in sorted order. Every layer sharing a ramp must contain the same class set, or colours shift: pad with zero-length dummy features.
- Layout elements have no z-order command; a rectangle added after the map frame covers it. Blank basemap exports white, not paper.
- Built-in "paper" basemap uses coarse world coastline; use `map.basemap blank` + the shared towns layer for land.
- `layout.export` does PNG (dpi) and vector PDF. Save with `project.saveAs` (*.rgis embeds data).

**Why:** Avoid re-discovering these on later challenge days that use RustGIS.
**How to apply:** Reuse `days/02-lines/src/prep_rustgis.py` pattern (bands + padding) for any multi-layer categorical map in RustGIS.
