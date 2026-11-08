# Handover

Last updated November 7, 2026 (final audit pass). This assumes you've never seen the project.

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
- Every stop on the main map is on its line's poster, and no poster has an extra stop. `boston-map/tools/poster_audit.py` checks this and every shared-stop pill. The map shows 222 T stops.
- The label overlap checks pass. `labels.py` always flags "Rapid T | ransit", which is deliberate: the title is drawn in two pieces to tighten the T. `marks.py` always flags "Lynn Harbor" against its own dot.
- High-resolution files are in `boston-map/output/`. The posting set is the `day08-*` files there.

**Not done:**

- **Publish the existing Day 8 map on Sunday, November 8, 2026.** Use the files already in `boston-map/output/`. Do not redraw them for the post. Draft text is in `docs/history/day08_social_posts.md`. Max needs to review it first.
- After Sunday, the project continues for fun. Buses are part of that later work, not the post.

## November 8, 2026: finals (read this first)

- **Finals are in `boston-map/output/final/`, `Downloads\NERTA-final\` and `Desktop\NERTA-FINAL-Disclaimer\`:** the main map, 8 T posters, the Ferry Map, 14 ferry route posters, 15 rail line posters, the combined rail poster, the regional rail map and the rail network display. `docs/VERSIONS.md` lists what each was made from. `boston-map/tools/finalize.py <slug> <pdf> [<png>]` saves a newly signed-off map; it never overwrites.
- **Release v1.0 (post these):** `Desktop\NERTA-FINAL-Disclaimer\v1.0\<map>\`, with and without the disclaimer, "v1.0" bottom-left. `boston-map/tools/release_v1.py` makes them from the signed-off PDFs; a later change means a new final, then a new version number.
- **Social sizes:** `boston-map/tools/export_social.py` (sources in `research/social-media-sizes-2026-11-07.md`).
- **Label rule (Max):** "id prefer overlapping the color before putting the text confusingly far away." Names sit by their own stop, on a colored line if need be; nothing touches.
- **Orange Line north (Max, November 8):** ends at North Reading; a loop from Greenwood to Market St (Lynnfield) and back in at Reading skips Wakefield. Both invented. 227 T stops. The website, rail and tram sessions were told.
- **Parking:** P at 34 T stations, `make_tmap.PARKING`, sources in `research/parking-and-bleachery-2026-11-08.md`.
- **Still open:** the tram session's three maps are in review (round 2 findings in `research/audit-tram-r2-2026-11-08.json`); the London boat's name is Max's pick.
- **nerta.fun logos:** `site/assets/logo/` has the 12-color T and NERTA mark (stripes rising to the right) and `nerta_37.svg`, the 37-color website-only alternate.

## Late November 7, 2026: newest state (read this first)

- **Release block on every map posted November 8 (Max):** the disclaimer paragraph, "Map: Maxwell Howe", "#30DayMapChallenge" and "Day 8 • Utopia". The main map draws its own. Posters call `draw_release()` from `boston-map/src/release_tag.py`. Web versions leave it out.
- **Finished maps go to `C:\Users\mhowe\Desktop\NERTA-FINAL-Disclaimer\`, sized for social media, only when Max says that map is final.** Maps tie together, so most stay open for a long time.
- **Side sessions:** the rail poster (`make_rail_poster.py`, newest `copies/rail_poster_v7`), the tram poster (`tools/make_tram_realmap.py`, `src/tram_merge.py`), and the nerta.fun site. Each writes its changes for other maps to `research/<name>-changes-for-all-maps.md`; the main-map session applies them to every map.
- **Max wants individual line posters** for the ferry, commuter rail and high-speed networks, as well as the combined posters.
- **London ferry (invented):** Long Wharf becomes an international port with a transatlantic boat to London. Working name "Atlantic Clipper", not final.
- **nerta.fun** (from the site session): a static Cloudflare Worker, source in `site/`, deployed with `npx wrangler deploy` from `site/`. `site/tools/render_web_maps.py` makes web map versions (name under NERTA, @mapzimus in the water, no hashtag, Day 8, disclaimer or MBTA sources) into `boston-map/output/copies/web/` only; then `site/tools/build_assets.py` and `site/tools/build_pages.py`. Site rules: never say MBTA, no dates, the network must match the maps and posters exactly, only rider stats and money figures are made up (seeded random), pods are canon and never explained. In progress there: network data rebuilt from the posters, real lat/lon in `site/data/locations.json`, a geographic map later. Draft renders in `output/copies/` are never committed (673 MB).

## Release pass, November 7, 2026 (branch `ferry-pass`, uncommitted)

- **Post this set:** `boston-map/output/copies/release_2026-11-08/`. It has `current_map.png` (600 dpi), `current_map.pdf` (vector), and the eight `line_*` posters as PNG and PDF. Ferry route posters are held back.
- Done: NERTA wordmark under the T, a new Key, teal water and rounded panels, the commuter rail fixes, ferry label cleanup, and ferry pills on the posters matching the map and colored by route. `docs/DECISIONS.md` lists them all.
- The real-geography pass is done. `docs/DECISIONS.md` lists what moved and what was left schematic on purpose: West Station, the B/C/D fan, Everett Sq, the Worcester row.
- Open for Max: the surface map vehicle, and "Gov't Center" against the naming rule.
- Bus advice and data: `research/bus-plan-draft.md`. Recommendation: no buses on this release.

## Ferry pass, November 7, 2026 (branch `ferry-pass`)

- Cursor's 12 ferry legs are merged into 5 routes with their own colors. `docs/DECISIONS.md` and `boston-map/data/line_audit.md` have the details.
- Newest main map copy: `boston-map/output/copies/ferry5_final_lbl.png`. Posters: `copies/ferry5_<route>.png`. Nothing in `output/` itself was touched.
- Safe render and checks: `safe_run.py` in the session scratchpad saves only to `copies/` under a new name. Copy it into `boston-map/tools/` if it should stay.
- Label check: 62 flags, against 85 on the first five-route render. The only text-on-text flag is the deliberate "Rapid T | ransit". The rest are station names over water and ferry dots in tight channels: Aquarium, Navy Yard, NORTH STATION, MIT and Science Park. North Shore boats pass behind the Dig panel.
- Cursor's state before this pass is backed up in the session scratchpad (`cursor_backup/`).
- The sheet now has half an inch more on the top and right, at the same scale, so it's about 18.5 by 15.8 inches. Beverly is added. Newest copy: `copies/wide_v2_lbl.png`.
- `cost-check` also edits this file. Merging the two branches will need this section kept by hand.

## What to do next, in order

1. Publish Day 8 from the existing files.
2. Choose a fix for the crowded top right corner. Options are in `docs/IDEAS.md`. Any trial is a copy.
3. Build the regional commuter rail map, as a new map. The main map only shows commuter rail lightly, so this one carries the detail.
4. Test buses on a copy: the regional map first, then maybe faintly on the main map and on the posters. This is a later project, after Sunday.
5. Move to other New England cities, using the stations-first method in `docs/IDEAS.md`.

## Open questions for Max

1. **Green Line letters.** Done November 7: A (Watertown), D (also Union Sq) and N (Needham) are on the map with B, C, D and E. Sources are in `line_audit.md`.
2. **Shoreline and Charles River.** Marblehead, the Neck and Salem Harbor are done. The rest could be improved.
3. **Langone.** Max named the North End ferry dock Langone. A ferry there was not found in two sources, so it stays unverified.
4. **Smaller calls:** the North End ferry label, a darker purple so gold reads better, renaming Seaver St for White Stadium, and a second sports name (Pierce or Bergeron). Orange to Reading is striped (done November 7).

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

## Copies only

Max's rule, November 6, 2026: do not overwrite finished maps. Everything already in `boston-map/output/` stays, including the `day08-*` posting set, the Illustrator files, `t_map.pdf`, `t_map.png`, and the `line_*` posters.

New renders go in `boston-map/output/copies/` under a new file name. Do not replace, export over, or copy onto an existing output file. Max decides later whether any old file is deleted.

`marks.py` calls `make_tmap.py`, which saves over `output/t_map.png` and `output/t_map.pdf`. `make_line_poster.py` saves over `output/line_<name>.png` and `.pdf`. The Illustrator steps below save over the current `.ai` and PNG exports. Do not run any of that unless Max names the exact file.

Copy nothing to `Desktop\30daymap\` until Max says the work is completely finished.

## How the current files were built

Setup is in `docs/TOOLS.md`. These steps overwrite the live files. They are frozen. Do not run them unless Max asks.

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
- **Stop count.** The panel's 225 is typed by hand. It's `audit.py`'s count plus the 10 stops only the Logan Silver Line uses. Update it when stops change.
- **Hidden second stops.** Fenway appears twice in `lines()`, once as `Fenway+`. That's the same station where two lines run side by side.

## Reference material

Links to the official MBTA maps and data are in `reference/README.md`.

Three reference images, including an official MBTA poster and a station photo, are kept private at `D:/REPOS/NERTA/reference/private/` on Max's machine. Max decided to keep them out of git because this repo is public and the MBTA owns the poster. A fresh clone won't have them, so ask Max if you need them. `reference/README.md` lists each file.

## Outside this repo

- **Old Day 8 working copy:** `D:\REPOS\30dmc-day08`, branch `day-08-utopia`. It's out of date, so don't work there.
- **Full session transcript:** `C:\Users\mhowe\.claude\projects\D--REPOS-30-day-map-challenge-2026\6191c34a-246f-4fb5-a839-115daa477823.jsonl`.
- **Recovered Illustrator file:** `boston-map/output/archive/day08_rapid_transit [Recovered]1111.ai` is an old crash recovery on Max's machine. It has no hand edits worth keeping and isn't in git.

## Starting a new Claude session

> Read HANDOVER.md, CLAUDE.md and docs/DECISIONS.md in this repo. Then tell me where the map stands and what you need from me first.
