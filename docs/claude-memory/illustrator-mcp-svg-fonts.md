---
name: illustrator-mcp-svg-fonts
description: "Illustrator MCP quirks for SVG import — variable fonts never match, anchors are lost, how the Day 2 pipeline works around it"
metadata:
  node_type: memory
  type: project
  originSessionId: 5d3634ef-d77e-46e4-b6e1-5e9d12579346
  modified: 2026-10-31T18:06:52.397Z
---

Illustrator MCP (learned 2026-10-31 on Day 2):
- `open_document` on a .svg is fast and keeps `<g id>` groups as named groups. `import_svg_as_editable` of a 2 MB SVG timed out at 60 s.
- Illustrator's SVG importer cannot match the installed variable fonts (Source Sans/Serif Variable) by any name form (family, PostScript, quoted, style attr). Every text frame comes in as Source Code Pro. Fix after import with `modify_object` `font_name` using PostScript names: SourceSansRoman-Regular / -Semibold, SourceSansItalic-Regular, SourceSerifRoman-Regular / -Bold.
- The font change keeps each frame's left edge, so `text-anchor="end"`/`"middle"` alignment is lost. Re-align with `modify_object` `position` using the returned bounds width: x = anchor − width (end) or anchor − width/2 (middle). `src/export_svg.py` prints the anchors; parse the SVG for them.
- Better than fixing fonts after import: open a text-free SVG and build every frame with `create_text_frame` (font, size, justification, tracking, leading, newline for lines). Point text honours right/center justification, so no re-alignment pass. `modify_object` cannot change a frame's justification once set; delete and recreate.
- `export` with scale 1 at 72 dpi gives a PNG at the page's pixel size; `raster_options.dpi` is per-export.
- RustGIS `layout.export` PDF is a raster inside a clip path, not vector. For vector in Illustrator, generate the SVG in Python.

**Why:** avoids an hour of trial and error on later challenge days that finish in Illustrator.
**How to apply:** reuse the Day 2 pattern: Python writes a text-free SVG + text_spec.json → open the SVG in Illustrator → one batch of create_text_frame calls → save .ai → export.
