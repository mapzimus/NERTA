---
name: day08-direction-two-posters
description: Day 8 pivoted on 2026-11-04 from one New England map to two T wall-poster maps; Max rejected the geographic version as too basic
metadata:
  node_type: memory
  type: project
  originSessionId: 6191c34a-246f-4fb5-a839-115daa477823
  modified: 2026-11-04T12:11:36.030Z
---

Day 8 (due Nov 8, 2026) is one map in the style of the real T station posters: a futuristic Boston T map. Max dropped the regional commuter rail map on 2026-11-04 because he didn't like it; don't revive it unless he asks. Northern and central NH, ME and VT are out. Scripts: `make_tmap.py`, `make_regional.py`, shared `station_kit.py`, in worktree `D:\REPOS\30dmc-day08`. `make_map.py` is the rejected version.

**Why:** Max said the geographic map looked "pretty basic" and sent a photo of a real T poster: "This is the style I want." Buses don't matter. He wants a clear, real coastline, and lines must never run into the ocean.

**How to apply:** Keep octilinear hand-laid lines, white stops, capsule transfers. Real coast is bent to the diagram with a thin-plate spline from station positions. Check research/ before calling a stop invented or real: "Logan West" came from the 2009 Urban Ring fact sheet, and I wrongly told Max I had invented it. See [[day08-mbta-new-england]] and [[two-source-data-rule]].
