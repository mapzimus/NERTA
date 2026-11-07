# NERTA

New England Regional Transit Authority: a futuristic fantasy transit map project for Boston and New England, made for fun.

It started as Day 8 (Utopia) of the 2026 #30DayMapChallenge: a dream Boston T map in the style of the station wall posters, titled **Boston's Rapid Transit**. It grew into something bigger than one day.

This is a personal fantasy map. It is **not a real MBTA map** and has no connection to the MBTA.

## Start here

| If you want to... | Read |
|---|---|
| Pick up the work, with no prior context | [HANDOVER.md](HANDOVER.md) |
| Set up the software, plugins and skills | [docs/TOOLS.md](docs/TOOLS.md) |
| Find the MBTA reference material | [reference/README.md](reference/README.md) |
| See what's been decided, and what was rejected | [docs/DECISIONS.md](docs/DECISIONS.md) |
| See every version of the map and which is current | [docs/VERSIONS.md](docs/VERSIONS.md) |
| Think about what comes next | [docs/IDEAS.md](docs/IDEAS.md) |
| Check a line or stop against its source | [boston-map/data/line_audit.md](boston-map/data/line_audit.md) and [boston-map/data/SOURCES.md](boston-map/data/SOURCES.md) |
| Read the full pass-by-pass history | [docs/history/decision_log_all_passes.md](docs/history/decision_log_all_passes.md) |

## What's in the repo

- `boston-map/src/`: the code that draws everything. `make_tmap.py` is the main map, `make_line_poster.py` is the line posters, and `station_kit.py` holds the shared drawing parts.
- `boston-map/data/`: MBTA lines and stops, OpenStreetMap checks, wheelchair access, the line audit and the sources list.
- `boston-map/output/`: every rendered map, including the Illustrator files.
- `boston-map/tools/`: checks for overlaps, dots under pills, stops in water and routing, plus the stop scoring work.
- `data/shared/`: New England towns, rivers and rail layers.
- `research/`: notes on Massachusetts, NH and Maine, CT, RI and western MA, Vermont and gateway cities, the Boston subway, and historic track.
- `docs/`: decisions, versions, ideas, tools, history and Claude's working notes.
- `reference/`: links to the MBTA maps and data used for comparison.
- `skills/`: `mbta-style`, the reusable style guide for making more maps like this, and `geospatial-mapmaker`, Max's general map guide.

## Rebuild the map

```bash
cd boston-map/src
python make_tmap.py
python make_line_poster.py
```

This writes `t_map.png`, `t_map.pdf` and a 600 dpi PNG and vector PDF for each line poster to `boston-map/output/`. Hand edits made in Illustrator are not in the code, so see the warning in [HANDOVER.md](HANDOVER.md).

Needs Python and the Arial font. Install packages with `pip install -r boston-map/requirements.txt`. The full setup is in [docs/TOOLS.md](docs/TOOLS.md).

## Credits and data

Map: Maxwell Howe. Concept and design by Max, scripts by Claude Code.

Data: MBTA V3 API, OpenStreetMap contributors, US Census TIGER/Line, Natural Earth. The T roundel belongs to the MBTA and appears here on a non-commercial fan map. See [docs/IDEAS.md](docs/IDEAS.md) for the open question about it.
