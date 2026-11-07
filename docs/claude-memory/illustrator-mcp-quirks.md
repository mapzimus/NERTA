---
name: illustrator-mcp-quirks
description: "Illustrator MCP argument shapes, path quirks and the layer-swap recipe learned on Days 2 and 3 (2026-10-31); read before driving Illustrator for a challenge page"
metadata:
  node_type: memory
  type: reference
  originSessionId: 5d3634ef-d77e-46e4-b6e1-5e9d12579346
  modified: 2026-11-01T01:58:27.584Z
---

Quirks of the Illustrator MCP server (verified 2026-10-31 while finishing Days 2 and 3):
- `create_line` takes `x1,y1,x2,y2` (not start/end objects). `stroke.color` must be a typed object: `{"type":"rgb","r":43,"g":43,"b":43}`; a hex string is rejected.
- `create_text_frame` wants `font_name` and `font_size`. A stray `size` key is accepted silently and the frame comes out at 12 pt.
- `save_document` ignores `path`: it saves the open document under its own name (an SVG opened from `output/map_vector_notext.svg` saves as `output/map_vector_notext.ai`). Copy the file afterwards to the committed name, e.g. `day03_towns.ai`.
- `export` also ignores the file name in `path` and writes `<docname>.png`, `<docname>_2.png`, … next to the document. Rename after export.
- `find_objects` with `bounds_within` does not filter; it returns every object of that type, so scan the bounds yourself. `get_document_structure` is the reliable map of groups and z-order (parse the saved JSON).
- `modify_object` `position` is the bounds top-left in `artboard-web`. `create_text_frame` `x,y` is the baseline anchor. For a 22 px frame the top of bounds is about 18 px above the baseline. `modify_object` with `contents` rewrites a frame's text in place.
- Stacked two-line labels: one point-text frame with `\n` in contents and `leading` set (24 for 22 px) works and moves as a unit.
- `set_z_order` only steps or sends to back/front. To interleave, call `send_to_back` on the objects front-to-back in the order you want them to end up (last call ends at the very back); parallel calls to this server run in the order sent.
- `import_svg_as_editable` takes `file_path`. A 650 KB SVG took about 4 minutes on a RAM-starved machine and the call timed out at 60 s while Illustrator kept working; calls queued behind it were dropped, so check state before retrying. The import lands as one group at the top of the topmost layer, and nested SVG groups arrive both inside their parent and as flattened duplicates at the group's top level: move the parent's named sub-groups out with `move_to_layer`, then delete the parent group to clear the duplicates.
- `close_document` after a successful save still reports unsaved changes once an export has run; `close_document(save: true)` is fine.
- Every call acts on Illustrator's ACTIVE document, and another Claude session using Illustrator at the same time can switch it between calls (on 2026-10-31 an `export` and a `close_document(save: true)` meant for Day 3 hit a Day 4 file another session had just opened, overwriting its PNG). Before `export`, `save_document` or `close_document`, call `get_document_info` and check `fileName`; re-`open_document` your file to re-activate it. Under RAM pressure Illustrator may also reopen the file as `<name> [Recovered].ai`; `save_document(mode: "save_as", path, overwrite: true)` puts it back on the real path.
- `modify_object` `rotation` with `rotation_mode: "absolute"` over-rotated a text frame (about 18° for a requested 9°) and shrank its font; use `delta` and re-set `font_size`, then check the bounds height.

Layer-swap recipe (Day 3): keep palette-dependent layers (`towns`, `state_lines`, `bars`, `swatches`) in their own `<g id>` in the exporter, lift them with `src/patch_layers.py` into `patch.svg`, import, move the four groups into Layer 1, fix z-order, delete the old groups. Text frames are untouched.

**How to apply:** build each day's text pass with these shapes from the start; rename exports and copy the .ai to its committed name as the last step. Related: [[illustrator-mcp-svg-fonts]], [[map-layout-preferences]].
