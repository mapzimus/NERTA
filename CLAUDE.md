# NERTA project instructions

Read `HANDOVER.md` first. It says where the work stands and what's next.

## Working with Max

- Plain English, American spelling (color, gray, center) on maps and in replies.
- Answer first, short numbered steps, lists of 5 or fewer, one question at a time.
- Commit or push only when Max asks.
- Max sends many short messages while you work. A stopped tool call usually means he's adding something, not that he's upset. Read the next message and adjust.
- When Max rejects something, it stays rejected. Check `docs/DECISIONS.md` before suggesting it again.

## Style

The house style lives in `skills/mbta-style/SKILL.md`. Use it for any new map or poster.

## Data rule

Any assembled data needs 2 named sources before it's called accurate. Say where they agree or differ. With 1 source, label it unverified. Ask for an override IN ALL CAPS. An override covers one dataset only, and only Max can grant it.

## Map rules

- Reference maps are for comparison only. Never copy one.
- Credit reads "Map: Maxwell Howe", no handle.
- Anything using the T roundel must say it isn't affiliated with the MBTA. The main map uses Max's disclaimer paragraph. Posters use "NOT A REAL MBTA MAP".
- Don't name the Patriots or Tom Brady.
- New stops and offshoots must be grounded in a real proposal or real plan. Label invented ones as invented in `boston-map/data/line_audit.md`.
- Posts get the split credit: Max's concept and design, Claude Code's scripts.
- Label style: "X LINE" first, then high-speed rows, with "TO" inline where it fits. Stop names use Center, St, Sq, Ave and Rd.
- Crisp at high zoom, nothing overlapping. Run the checks before calling a map done.

## Checking a map

```bash
cd boston-map/tools
python labels.py make_tmap
python marks.py
python audit.py
python routing.py
```

`labels.py` finds text overlaps. `marks.py` finds dots touching dots, dots under pills and text over dots, and it redraws the map. Rendering and checks are not enough on their own: look at a crop of whatever changed.

## Code notes

- Patch scripts: write them with the Write tool. Bash heredocs mangle `\n` in Python strings.
- `lines()` in `make_tmap.py` is the single source for stops and line styles: solid is running today, stripe is a real proposal, dash is imagined.
- Station labels become outlines in Illustrator. Only headings, the Key and the Dig box stay live text.
- Illustrator route: open `t_map.pdf`, save as `.ai`, export PNG. Fix things in Python and rebuild where possible.
