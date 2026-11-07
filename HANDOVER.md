# Handover

Last updated November 6, 2026. This assumes you've never seen the project.

## What this is

NERTA is a personal fantasy transit project by Max Howe, a GIS analyst in Massachusetts. It imagines a future Boston subway and regional rail network, drawn in the style of the MBTA's station wall posters.

It began as Day 8 (theme: Utopia) of the 2026 #30DayMapChallenge, a yearly online map-making event. The map outgrew one day, so it moved into this repo.

It is a fan work. It is **not a real MBTA map**, and nothing here is an actual plan.

**The finished pieces:**

1. One main map, "Boston's Rapid Transit".
2. Eight line posters: Red, Orange, Blue, Green, Yellow, Cyan, Indigo and Silver.

**The main idea on the map:** "The BIGGER Dig", a four-track tunnel joining North Station and South Station at a new station called Boston Central. Around it are extended T lines, four new or rethought lines, all 13 commuter rail routes, high-speed rail and ferries.

| Term | Meaning |
|---|---|
| The T | Boston's subway. MBTA is the agency that runs it |
| The BIGGER Dig | Our North-South Rail Link tunnel, named after the Big Dig highway project |
| Pill | The small colored capsule on a poster that shows a transfer, like `OL` or `CR` |
| Solid, striped, dashed | Running today, a real proposal, imagined |
| CR, HSR, F | Commuter rail, high-speed rail, ferry |

## Where it stands

**Done and checked:**

- The main map and all eight posters are final unless Max changes something.
- Every stop on the main map is on its line's poster, and no poster has an extra stop. `boston-map/tools/poster_audit.py` checks this and every shared-stop pill. The map shows 215 T stops.
- The label overlap checks pass. `labels.py` always flags "Rapid T | ransit", which is deliberate: the title is drawn in two pieces to tighten the T. `marks.py` always flags "Lynn Harbor" against its own dot.
- High-resolution files are in `boston-map/output/`. The posting set is the `day08-*` files there.

**Not done:**

- **The Day 8 post hasn't gone out. It's due Sunday, November 8, 2026.** Draft text is in `docs/history/day08_social_posts.md`. Max needs to review it first.

## What to do next, in order

1. Post Day 8.
2. Choose a fix for the crowded top right corner. Options are in `docs/IDEAS.md`.
3. Build the regional commuter rail map. The main map only shows commuter rail lightly, so this one carries the detail.
4. Add buses: on the regional map, very faintly on the main map, and on the posters.
5. Move to other New England cities, using the stations-first method in `docs/IDEAS.md`.

## Open questions for Max

1. **Green Line letters.** The proposal is A for Watertown and F or N for Needham. The A branch history is from memory, so check it with 2 sources first.
2. **Shoreline and Charles River.** Marblehead, the Neck and Salem Harbor are done. The rest could be improved.
3. **Langone Park nod.** Max said to add it if it checks out. Sources weren't clear, so it isn't on the map.
4. **Smaller calls:** the North End ferry label, a darker purple so gold reads better, renaming Seaver St for White Stadium, a second sports name (Pierce or Bergeron), and striping Orange to Reading.

## Known problems

1. **Cost figure:** the $125B is rough. Three inflation inputs need checking against BLS, and the mileage is hand estimated. See `boston-map/data/SOURCES.md`.
2. **Ferry track:** it runs slightly over land near Georges Island.
3. **Dashed corners:** dash ends look clipped on tight curves when zoomed in, most on Yellow's sharp corner.
4. **Top right corner:** crowded, though nothing overlaps.
5. **Unfinished message:** Max once wrote "And I really want to I haven't" and it was cut off. Worth asking about.

Facts resting on one source are marked in `boston-map/data/line_audit.md`.

## Where things are

| Need | Go to |
|---|---|
| Map and poster code | `boston-map/src/make_tmap.py`, `make_line_poster.py`, `station_kit.py` |
| Finished images | `boston-map/output/`. `docs/VERSIONS.md` says which files are current |
| What's been decided or rejected | `docs/DECISIONS.md` |
| Evidence for every line and stop | `boston-map/data/line_audit.md`, `boston-map/data/SOURCES.md` |
| Software, plugins, skills, setup | `docs/TOOLS.md` |
| Reference material | `reference/README.md` |
| Future ideas | `docs/IDEAS.md` |
| Research notes | `research/` |
| Pass-by-pass history | `docs/history/decision_log_all_passes.md` |
| Rules for working on this | `CLAUDE.md` |

## How to rebuild everything

Setup is in `docs/TOOLS.md`. This takes about 5 minutes.

1. Render the main map and run its checks:

   ```bash
   cd boston-map/tools
   python marks.py
   python labels.py make_tmap
   python audit.py
   ```

2. Render the posters at 600 dpi, then check them against the map:

   ```bash
   cd ../src
   python make_line_poster.py
   cd ../tools
   python poster_audit.py
   ```

3. In Illustrator, open `boston-map/output/t_map.pdf` and save it as `day08_rapid_transit.ai`.
4. Export the artboard at 200 dpi as `day08_rapid_transit.png` and at 600 dpi as `day08_rapid_transit_hires.png`, both in `boston-map/output/`.
5. Copy the results to the posting set in `boston-map/output/`:
   - `day08_rapid_transit.png`, `.ai` and `t_map.pdf` become `day08-utopia-boston.png`, `.ai` and `.pdf`.
   - `day08_rapid_transit_hires.png` becomes `day08-utopia-boston-hires.png`.
   - Each `line_<name>.png` becomes `day08-line-<name>.png`.

Copy nothing to `Desktop\30daymap\` until Max says the work is completely finished.

**Things that can bite you:**

- **Hand edits vanish.** Any edit made only in Illustrator is lost at the next rebuild. Move it into the code.
- **Font path.** The disclaimer loads Arial Narrow Italic from `C:\Windows\Fonts\ARIALNI.TTF`. Change the path on another machine.
- **Stop count.** The panel's 215 is typed by hand. It's `audit.py`'s count plus the 10 stops only the Logan Silver Line uses. Update it when stops change.
- **Hidden second stops.** Fenway appears twice in `lines()`, once as `Fenway+`. That's the same station where two lines run side by side.

## Reference material

Links to the official MBTA maps and data are in `reference/README.md`.

Three reference images, including an official MBTA poster and a station photo, are kept private at `D:/REPOS/NERTA/reference/private/` on Max's machine. Max decided to keep them out of git because this repo is public and the MBTA owns the poster. A fresh clone won't have them, so ask Max if you need them. `reference/README.md` lists each file.

## Outside this repo

- **Old Day 8 working copy:** `D:\REPOS\30dmc-day08`, branch `day-08-utopia`. It's out of date, so don't work there.
- **Full session transcript:** `C:\Users\mhowe\.claude\projects\D--REPOS-30-day-map-challenge-2026\6191c34a-246f-4fb5-a839-115daa477823.jsonl`.
- **Recovered Illustrator file:** `boston-map/output/day08_rapid_transit [Recovered]1111.ai` is an old crash recovery on Max's machine. It has no hand edits worth keeping and isn't in git.

## Starting a new Claude session

> Read HANDOVER.md, CLAUDE.md and docs/DECISIONS.md in this repo. Then tell me where the map stands and what you need from me first.
