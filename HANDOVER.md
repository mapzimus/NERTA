# Handover

Last updated November 6, 2026.

## Where it stands

- **Main map:** `boston-map/src/make_tmap.py` draws the current map, titled "Boston's Rapid Transit". The checks pass. (`labels.py` flags "Rapid T | ransit". That's deliberate: the title is drawn in two pieces to tighten the T.)
- **Line posters:** all eight are done: Red, Orange, Blue, Green, Yellow, Cyan, Indigo, Silver. Each shows transfers, including ferry (F) and high-speed rail (HSR) pills. Bus connections aren't on them yet.
- **Master files:** `Desktop\30daymap\` holds the main map as `day08-utopia-boston*` and the posters as `day08-line-*.png`. Overwrite them after any rebuild.
- **Day 8 deadline:** Sunday, November 8, 2026. The post hasn't gone out. Draft text is in `docs/history/day08_social_posts.md`.
- **Project name:** NERTA stays a brainstorm. **Do not put it on the map yet.** The T stays, with no new logo.
- **Style skill:** `skills/mbta-style/` is installed at `~/.claude/skills/mbta-style/`. Update both copies together.

## Read this before you rebuild

Any hand edit in Illustrator must be moved into the code, or the next rebuild loses it. Max's earlier edits are already in. His file is kept as `boston-map/output/day08_rapid_transit_max_edits.ai`.

The disclaimer uses Arial Narrow Italic, loaded from `C:\Windows\Fonts\ARIALNI.TTF`, so a machine without that font needs the path changed.

Rebuild order: render with `tools/marks.py`, open `t_map.pdf` in Illustrator, save as `day08_rapid_transit.ai`, export PNG at 200 dpi to `output/` and 600 dpi to the Desktop, then copy the `.png`, `.ai` and `.pdf` to the Desktop names.

## Next steps, in order

1. Post Day 8. Max should review the draft text first.
2. Choose a fix for the top right corner. Options are in `docs/IDEAS.md`.
3. Build the regional commuter rail map.
4. Work out buses: on the regional map, very faint on the main map, and on line posters.
5. Then move to other New England cities, using the stations-first method in `docs/IDEAS.md`.

## Open items

Waiting on Max:
1. **Green Line letters.** Proposed A for Watertown and F (or N) for Needham, with no letters on any other line. The A branch history is from memory, so verify it with 2 sources first.
2. **Shoreline and Charles River.** Marblehead, the Neck and Salem Harbor are done, using new anchor points in `SHORE`. The rest of the shoreline and the Charles are not started.
3. **Langone Park nod.** Max said to add it if it checks out. Sources weren't clear on the details, so it was never added.
4. **Smaller calls left open:** North End ferry label (529 Commercial St or none), darker purple so gold reads better, renaming Seaver St for White Stadium, a second sports name (Pierce or Bergeron), striping Orange to Reading.

Known problems:
1. **Cost inputs:** three CPI values need checking against BLS, and the mileage is hand estimated. See `boston-map/data/SOURCES.md`.
2. **Poster pills:** the F and HSR pills were set by hand. The Red poster was checked closely against the main map, and the rest were only looked over once. Check them when the map changes.
3. **Ferry track** runs 0.25 units over land near Georges Island.
4. **Top right corner** is still crowded, though nothing overlaps.
5. **Unfinished message:** Max once wrote "And I really want to I haven't" and it was cut off. Worth asking.

Facts still on one source are marked in `boston-map/data/line_audit.md`.

## Where things live outside this repo

- **Day 8 working copy:** `D:\REPOS\30dmc-day08`, branch `day-08-utopia`, in `days/08-utopia/`. Its last commit is `fffb29b`. All later work there is uncommitted and the branch was never pushed, so this repo is the safe copy.
- **Reference images:** Max's photos of old T maps and the official Red Line poster were left out of this public repo on purpose.
- **Full session transcript:** `C:\Users\mhowe\.claude\projects\D--REPOS-30-day-map-challenge-2026\6191c34a-246f-4fb5-a839-115daa477823.jsonl`.

## Prompt for a new session

> Read HANDOVER.md, CLAUDE.md and docs/DECISIONS.md in this repo. Then tell me where the map stands and what you need from me first.
