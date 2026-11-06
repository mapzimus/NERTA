# Handover

Last updated November 6, 2026.

## Where it stands

- **Main map:** `boston-map/src/make_tmap.py` draws the current map. It renders here pixel-for-pixel the same as the Day 8 working copy, and the overlap checks pass.
- **Day 8 deadline:** Sunday, November 8, 2026. The challenge post still has to go out.
- **Red Line poster:** a sample exists at `boston-map/output/line_red.png`. Max said to do this one sample and **hold the rest until the main map's structure is locked in**.
- **Project name:** NERTA stays a brainstorm. **Do not put it on the map yet.**

## Read this before you rebuild

**Max made hand edits in Illustrator that are not in the code.** They're saved in `boston-map/output/day08_rapid_transit_max_edits.ai`. Nobody has compared that file to the code yet, so what he changed is unknown.

Running `make_tmap.py` does not touch that file, but any new `.ai` built from `t_map.pdf` will not include those edits.

**Do this first:** ask Max what he changed, or compare the file against `t_map.pdf`, then move those changes into the code.

## Next steps, in order

1. Find Max's Illustrator edits and move them into the code.
2. Finish the map structure with the open items below.
3. Export the final Day 8 files and post them.
4. Make the remaining line posters once the structure is locked.

## Open items on the map

Waiting on Max:
1. **Green Line letters.** Proposed A for Watertown and F (or N) for Needham, with no letters on any other line. The A branch history is from memory, so verify it with 2 sources first.
2. **Columbia Point ferry stop.** Max likes it and the sources support it (WBUR, the UMass Boston study, Boston Harbor Now). Not on the map yet.
3. **Shoreline and Charles River.** Max wants to explore doing these better. Not started.
4. **Commuter rail map.** Max is thinking about bringing back a separate one. See `docs/IDEAS.md`.
5. **Smaller calls left open:** North End ferry label (529 Commercial St or none), darker purple so gold reads better, renaming Seaver St for White Stadium, a second sports name (Pierce or Bergeron), striping Orange to Reading.

Known problems:
1. **~$125B total** doesn't include the commuter branches added in the last passes. Decide whether to update it.
2. **Ferry track** runs 0.26 units over land near Georges Island.
3. **Red Line poster key:** it was rearranged because text collided at bottom right, but the fix was never checked by eye. Look at it before trusting it.
4. **Transfer data on the poster:** pills come from shared stop names plus a short manual list, so a transfer can be missed if names differ. Check every pill by hand against the main map before making more posters.
5. **Unfinished message:** Max once wrote "And I really want to I haven't" and it was cut off. Worth asking.

Facts still on one source are marked in `boston-map/data/line_audit.md`.

## Where things live outside this repo

- **Day 8 working copy:** `D:\REPOS\30dmc-day08`, branch `day-08-utopia`, in `days/08-utopia/`. Its last commit is `fffb29b`. **All later work there is uncommitted and the branch was never pushed**, so this repo is the safe copy.
- **Desktop finals:** `Desktop\30daymap\day08-utopia-boston*`. These are older than this repo: they have the 13-route commuter work but not the Suffolk Downs ring, the South Salem label fix or Max's hand edits.
- **Reference images:** Max's photos of old T maps and the official Red Line poster were left out of this public repo on purpose.
- **Full session transcript:** `C:\Users\mhowe\.claude\projects\D--REPOS-30-day-map-challenge-2026\6191c34a-246f-4fb5-a839-115daa477823.jsonl`.

## Prompt for a new session

> Read HANDOVER.md, CLAUDE.md and docs/DECISIONS.md in this repo. Then tell me where the map stands and what you need from me first.
