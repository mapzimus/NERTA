# Day 8 — Utopia

Sun Nov 8, 2026

**Idea:** A fantasy Boston T map in the style of the station wall posters, with The BIGGER Dig tunnel under downtown and a full ring. Mostly imagined, with some nods to real proposals. No date on the map.

**Data:** MBTA V3 API (today's stops, lines and accessibility). The coast and islands are real Census shapes bent to fit the layout. Stop lists for new lines are judgment. Details in [data/SOURCES.md](data/SOURCES.md), evidence by line in [data/line_audit.md](data/line_audit.md), plan history in [research/](research/), and all decisions in [PROPOSAL.md](PROPOSAL.md).

**Tool(s):** Python (matplotlib, geopandas, shapely, scipy), finished in Illustrator (`output/day08_rapid_transit.ai`).

**AI use:** Claude Code did the research and wrote the Python scripts. Max set the concept and made the network and design decisions, including the Cyan Line.

## Notes

- `src/make_tmap.py` draws the map; `src/station_kit.py` is the drawing kit.
- The layout is schematic, set by hand on a 45-degree grid. Solid lines run today, striped lines are real proposals, dashed lines are imagined.
- Ferries are routed through the water by computer, so no track crosses land.
- Fan map, not an official MBTA map, and marked that way on the map. The T roundel is included at Max's request.
- `src/make_regional.py`, `src/make_map.py` and their outputs are dropped earlier versions, kept for reference.

## Output

![Rapid Transit](output/day08_rapid_transit.png)

## Post text

See [social_posts.md](social_posts.md).
