# Tools

Everything used to make the map, and how to set it up again.

## Software

| Tool | Used for | Version |
|---|---|---|
| Python | All drawing and checks | 3.14.3 |
| Adobe Illustrator | Final `.ai` and PNG exports | Desktop app, Max's license |
| Git and GitHub | This repo, `mapzimus/NERTA` | |
| Claude Code | Scripts and research, in the desktop app | |

Python packages are pinned in `boston-map/requirements.txt`:

```bash
pip install -r boston-map/requirements.txt
```

**Fonts:** Arial for almost everything, and Arial Narrow Italic for the disclaimer. Both are standard on Windows.

**Python on Max's machine:** it isn't always on PATH. The full path is `C:\Users\mhowe\AppData\Local\Python\bin\python.exe`.

## Claude Code plugins and connections

| Name | Used for | Setup |
|---|---|---|
| Illustrator MCP server | Lets Claude open the PDF, save the `.ai` and export PNGs | `npx illustrator-mcp-server`, added as a stdio MCP server named `illustrator-mcp`. No keys needed. Illustrator must be open |
| Web search and Firecrawl | Research on proposals, stations and costs | Built in, and the Firecrawl plugin. Firecrawl's free tier has a daily limit |

The separate `adobe-for-creativity` plugin is installed but wasn't used for this map. All Adobe work went through the Illustrator MCP server.

RustGIS and QGIS were used on other challenge days, not on this map. Their notes are kept in `docs/claude-memory/` in case they're needed.

**Illustrator freezes:** a long export can leave Illustrator not responding. Don't force-quit straight away. Check for a hidden dialog first, then close without saving and rebuild from `t_map.pdf`. Illustrator can leave `[Recovered]` files behind, which are safe to ignore once checked.

## Skills

| Skill | Where | Used for |
|---|---|---|
| `mbta-style` | `skills/mbta-style/` | The house style for these maps. Written for this project |
| `geospatial-mapmaker` | `skills/geospatial-mapmaker/` | Max's general map-making guide |
| `dataviz` | Comes with Claude Code | The cost bar in the BIGGER Dig panel |
| `skill-creator` | Official Claude Code plugin | Building `mbta-style` |

To install a repo skill, copy its folder to `~/.claude/skills/`. Max's machine has `mbta-style` installed there, so update both copies together.

## Claude's working notes

`docs/claude-memory/` holds copies of the notes Claude kept between sessions. They cover Illustrator quirks, Max's layout preferences, the credit line and the data rule. They're snapshots from November 6, 2026.

## Data

| Data | Source | Script or location |
|---|---|---|
| Today's stops and lines | MBTA V3 API, checked against OpenStreetMap | `boston-map/src/fetch_mbta.py` |
| Wheelchair access | MBTA V3 API | `boston-map/src/fetch_access.py` |
| Coast and towns | US Census TIGER/Line | `data/shared/` |
| Stop scoring | Census population and jobs data | `boston-map/tools/stopcheck/` |

Full citations are in `boston-map/data/SOURCES.md`.

## Check scripts

All are in `boston-map/tools/`.

| Script | Checks |
|---|---|
| `labels.py make_tmap` | Text overlapping text |
| `marks.py` | Dots touching dots, dots under pills, text over dots. Also redraws the map |
| `audit.py` | Counts the stops in `lines()` |
| `routing.py` | Line routing |
| `poster_audit.py` | Every map stop is on its poster, and shared stops have pills both ways |

These don't replace looking at a zoomed crop of whatever changed.
